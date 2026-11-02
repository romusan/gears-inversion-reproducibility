"""Finite noise/discrepancy stress controls; no external calibration is claimed."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
import sys,json,time,hashlib,platform,concurrent.futures as cf
from pathlib import Path
from functools import lru_cache
import numpy as np
import scipy
from scipy.optimize import least_squares
from scipy.linalg import solve_triangular
ROOT=Path(__file__).resolve().parent.parent;SRC=ROOT/'deposit_v6/gear_inverse_identifiability/src';OUT=ROOT/'revision_17_final_2026-11-01'
sys.path.insert(0,str(SRC))
from geometry.involute import InvoluteGear,GearPair
from geometry.microgeometry import TipRelief
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator
SCALE=np.array([.05,1,.01,1]);BOUNDS=np.array([[0,.1],[.3,.95],[0,.05],[.05,.5]])
STARTS=[np.array(x) for x in [[.03,.65,.01,.35],[.015,.85,.02,.45],[.01,.50,.04,.48]]]
SCENARIOS=['iid','correlated_iid_fit','correlated_gls_fit','gain5_iid_fit','operator_iid_fit']
SIGMA=.0001;RHO=.8;SEEDS=50
def rms(x):return float(np.sqrt(np.mean(np.asarray(x)**2)))
def metric(values):
    if not len(values):return None
    return dict(n=len(values),median=float(np.median(values)),p10=float(np.quantile(values,.1)),p90=float(np.quantile(values,.9)))
@lru_cache(None)
def operators():
    pair=GearPair(InvoluteGear(24,3,20,20),InvoluteGear(48,3,20,20))
    ops={v:BatchedGapOperator(GearContactModel(pair,micro1=TipRelief(),compliance_variant=v),300,120) for v in ['projected-energy','shear-G']}
    L=np.linalg.cholesky(RHO**np.abs(np.arange(120)[:,None]-np.arange(120)[None,:]))
    return ops,L
def run_case(task):
    sd,scenario,seed=task;ops,L=operators();op=ops['projected-energy'];truth=np.array([.02,.75,.005,sd])
    nominal=op.evaluate(truth)['prediction']
    generating=ops['shear-G'].evaluate(truth)['prediction'] if scenario=='operator_iid_fit' else nominal.copy()
    if scenario=='gain5_iid_fit':generating=1.05*generating
    z=np.random.default_rng(2026110100+seed).normal(size=120)
    noise=SIGMA*(L@z if scenario.startswith('correlated_') else z)
    y=generating+noise
    def whiten(x):
        return solve_triangular(L,x,lower=True,check_finite=False)/SIGMA if scenario=='correlated_gls_fit' else x/SIGMA
    attempts=[]
    for start in STARTS:
        cache={}
        def ev(q):
            if 'q' not in cache or not np.array_equal(cache['q'],q):
                r=op.evaluate(q*SCALE,jacobian=True)
                cache.update(q=q.copy(),residual=whiten(r['prediction']-y),J=whiten(r['jacobian']*SCALE))
            return cache
        fit=least_squares(lambda q:ev(q)['residual'],start/SCALE,jac=lambda q:ev(q)['J'],bounds=(BOUNDS[:,0]/SCALE,BOUNDS[:,1]/SCALE),max_nfev=600,ftol=1e-9,xtol=1e-10,gtol=1e-8)
        attempts.append(dict(start=start.tolist(),theta=(fit.x*SCALE).tolist(),chi2=float(2*fit.cost),success=bool(fit.success),status=int(fit.status),nfev=int(fit.nfev),optimality=float(fit.optimality)))
    best=min(attempts,key=lambda r:r['chi2']);est=np.array(best['theta']);pred=op.evaluate(est)['prediction']
    bound=(np.minimum(est-BOUNDS[:,0],BOUNDS[:,1]-est)<=1e-6*np.diff(BOUNDS,axis=1).ravel()).tolist()
    xx=np.linspace(0,1,1001);micro=TipRelief()
    return dict(sd_true=sd,scenario=scenario,seed=seed,truth=truth.tolist(),theta=est.tolist(),success=best['success'],chi2=best['chi2'],attempts=attempts,bound_flags=bound,dedendum_bound=bool(any(bound[2:])),dedendum_scaled_error=float(np.max(np.abs(est[2:]-truth[2:])/SCALE[2:])),full_profile_rmse_um=1000*rms(micro.evaluate(xx,est)-micro.evaluate(xx,truth)),fit_rmse_um=1000*rms(pred-y),prediction_error_vs_generator_um=1000*rms(pred-generating),deterministic_discrepancy_rms_um=1000*rms(generating-nominal),noise_rms_um=1000*rms(noise),observations_mm=y.tolist(),generating_prediction_mm=generating.tolist())
def summarize(rows):
    cells=[]
    for sd in [.25,.4]:
        for scenario in SCENARIOS:
            rr=[r for r in rows if r['sd_true']==sd and r['scenario']==scenario];assert len(rr)==SEEDS
            strata={name:[r for r in rr if predicate(r)] for name,predicate in [('all',lambda r:True),('converged',lambda r:r['success']),('failed',lambda r:not r['success']),('converged_bound',lambda r:r['success'] and r['dedendum_bound']),('converged_interior',lambda r:r['success'] and not r['dedendum_bound'])]}
            cells.append(dict(sd_true=sd,scenario=scenario,n=len(rr),failed=sum(not r['success'] for r in rr),bound_count=sum(r['dedendum_bound'] for r in rr),discrepancy_rms_um=rr[0]['deterministic_discrepancy_rms_um'],strata={k:dict(n=len(v),dedendum=metric([r['dedendum_scaled_error'] for r in v]),profile=metric([r['full_profile_rmse_um'] for r in v]),fit=metric([r['fit_rmse_um'] for r in v])) for k,v in strata.items()}))
    return cells
def archived_status():
    paths=[ROOT/'deposit_v6/gear_inverse_identifiability/results/q1_revision_2026-10-12/monte_carlo_records.jsonl',ROOT/'deposit_v6/gear_inverse_identifiability/results/q1_review5_2026-10-12/complementary_monte_records.jsonl']
    cells=[]
    for path in paths:
        rr=[json.loads(x) for x in path.read_text().splitlines() if x.strip()]
        for sd,design,sigma in sorted({(r['sd_true'],r['design'],r['sigma_um']) for r in rr}):
            group=[r for r in rr if (r['sd_true'],r['design'],r['sigma_um'])==(sd,design,sigma)];assert len(group)==100
            def bound(r):
                a=np.array(r['theta']);return bool(np.any(np.minimum(a[2:]-BOUNDS[2:,0],BOUNDS[2:,1]-a[2:])<=1e-6*np.diff(BOUNDS[2:],axis=1).ravel()))
            strata={k:[r['dedendum_scaled_error'] for r in group if condition(r)] for k,condition in [('all',lambda r:True),('converged',lambda r:r['success']),('failed',lambda r:not r['success']),('converged_bound',lambda r:r['success'] and bound(r)),('converged_interior',lambda r:r['success'] and not bound(r))]}
            cells.append(dict(campaign=path.parent.name,sd_true=sd,design=design,sigma_um=sigma,n=100,failed=sum(not r['success'] for r in group),dedendum_bound_count=sum(bound(r) for r in group),strata={k:metric(v) for k,v in strata.items()}))
    assert sum(r['n'] for r in cells)==1800
    return cells,{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
def main():
    OUT.mkdir(exist_ok=True);start=time.time();rows=[];tasks=[(sd,c,s) for sd in [.25,.4] for c in SCENARIOS for s in range(SEEDS)]
    path=OUT/'stress_records.jsonl'
    # Resume completed keys only when the exact scientific source matches.
    source_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();receipt=OUT/'stress_source.json'
    if path.exists():
        assert json.loads(receipt.read_text())['sha256']==source_hash
        rows=[json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    receipt.write_text(json.dumps(dict(sha256=source_hash)),encoding='utf-8')
    complete={(r['sd_true'],r['scenario'],r['seed']) for r in rows};assert len(complete)==len(rows)
    tasks=[t for t in tasks if t not in complete]
    with path.open('a',encoding='utf-8') as out,cf.ProcessPoolExecutor(max_workers=3) as pool:
        pending=[pool.submit(run_case,t) for t in tasks]
        for future in cf.as_completed(pending):
            r=future.result();rows.append(r);out.write(json.dumps(r)+'\n');out.flush()
            if len(rows)%25==0:print('Completed',len(rows),'/ 500 cases;',round(time.time()-start,1),'s',flush=True)
    assert len(rows)==500
    archive,hashes=archived_status();(OUT/'archived_status_strata.json').write_text(json.dumps(dict(cells=archive,source_sha256=hashes),indent=2),encoding='utf-8')
    summary=dict(scope='Illustrative finite stress controls, not measured-data calibration, global optimization or a coverage study.',seeds=SEEDS,seed_base=2026110100,n_positions=120,torque_Nm=300,sigma_um=.1,rho=RHO,gain=1.05,fit_variant='projected-energy',operator_generator='shear-G',starts=[s.tolist() for s in STARTS],cases=len(rows),attempts=sum(len(r['attempts']) for r in rows),failed_selected=sum(not r['success'] for r in rows),failed_attempts=sum(not a['success'] for r in rows for a in r['attempts']),cells=summarize(rows),python=sys.version,numpy=np.__version__,scipy=scipy.__version__,platform=platform.platform(),elapsed_seconds=time.time()-start,source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),SRC/'mechanics/batched_operator.py',SRC/'mechanics/compliance.py',SRC/'geometry/microgeometry.py']})
    (OUT/'stress_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10})
    fig,axes=plt.subplots(1,2,figsize=(11,4.2));labels=['IID','AR / IID fit','AR / GLS fit','Gain +5%','Operator change']
    for ax,sd in zip(axes,[.25,.4]):
        for i,c in enumerate(SCENARIOS):
            rr=sorted([r for r in rows if r['sd_true']==sd and r['scenario']==c],key=lambda r:r['seed'])
            for kind,marker,color in [('interior','o','#2469a1'),('bound','x','#d04b29'),('failed','+','black')]:
                ss=[r for r in rr if ('failed' if not r['success'] else ('bound' if r['dedendum_bound'] else 'interior'))==kind]
                ax.scatter([i+((r['seed']%9)-4)*.017 for r in ss],[r['dedendum_scaled_error'] for r in ss],s=18,marker=marker,c=color,label=kind if i==0 else None,alpha=.75)
            med=np.median([r['dedendum_scaled_error'] for r in rr]);ax.plot([i-.22,i+.22],[med,med],'k-',lw=2)
        ax.set_xticks(range(5),labels,rotation=23,ha='right');ax.set_title(f'True dedendum start {sd}');ax.set_ylabel('Maximum scaled dedendum error');ax.grid(axis='y',alpha=.2)
    handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',ncol=3,frameon=False);fig.tight_layout(rect=(0,0,1,.9));fig.savefig(OUT/'stress_v17.png',dpi=240);plt.close(fig)
    print('Finished',len(rows),'cases;',summary['attempts'],'attempts',flush=True)
if __name__=='__main__':main()
