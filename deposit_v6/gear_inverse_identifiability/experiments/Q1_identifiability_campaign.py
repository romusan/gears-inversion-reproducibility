"""Support transition, analytic local spectra, profile likelihood and 100-seed MC.

The legacy operator is retained to isolate the review's identifiability question.
It is a same-model synthetic experiment (inverse crime), not physical validation.
"""
import sys,json,argparse,time
from pathlib import Path
import concurrent.futures as cf
import numpy as np
from scipy.optimize import least_squares
import matplotlib.pyplot as plt
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from geometry.involute import InvoluteGear,GearPair
from geometry.microgeometry import TipRelief
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator
from campaign_provenance import provenance

OUT=Path(__file__).resolve().parents[1]/'results'/'q1_revision_2026-10-12'
OUT.mkdir(exist_ok=True)
SCALE=np.array([.05,1,.01,1]);BOUNDS=np.array([[0,.1],[.3,.95],[0,.05],[.05,.5]])
STARTS=[np.array([.03,.65,.01,.35]),np.array([.015,.85,.02,.45])]
DESIGNS={'single300':[(300,120)],'multi50_300':[(50,60),(300,60)]}

def operators(design,variant='legacy'):
    pair=GearPair(InvoluteGear(24,3,20,20),InvoluteGear(48,3,20,20))
    model=GearContactModel(pair,TipRelief(),compliance_variant=variant)
    # The completed statistical campaign used the iterative force inversion.
    # Keep that policy explicit even though the equivalent Lambert-W engine
    # is now available for subsequent forward evaluations.
    return [BatchedGapOperator(model,T,n,force_engine='iterative') for T,n in design]

def predict(ops,theta):
    return np.concatenate([op.evaluate(theta)['prediction'] for op in ops])

def fit(ops,y,sigma,start,fixed=None,max_nfev=400):
    fixed=fixed or {};free=[j for j in range(4) if j not in fixed]
    cache={}
    def evaluate(q):
        if 'q' not in cache or not np.array_equal(q,cache['q']):
            theta=np.array(start,dtype=float);theta[free]=q*SCALE[free]
            for j,value in fixed.items():theta[j]=value
            rr=[op.evaluate(theta,jacobian=True) for op in ops]
            cache.update(q=q.copy(),theta=theta,
                         y=np.concatenate([r['prediction'] for r in rr]),
                         J=np.vstack([r['jacobian'] for r in rr])[:,free]*SCALE[free]/sigma)
        return cache
    sol=least_squares(lambda q:(evaluate(q)['y']-y)/sigma,
                      start[free]/SCALE[free],jac=lambda q:evaluate(q)['J'],
                      bounds=(BOUNDS[free,0]/SCALE[free],BOUNDS[free,1]/SCALE[free]),
                      ftol=1e-9,gtol=1e-8,xtol=1e-10,max_nfev=max_nfev)
    cc=evaluate(sol.x)
    return dict(theta=cc['theta'].tolist(),chi2=float(2*sol.cost),success=bool(sol.success),
                nfev=int(sol.nfev),optimality=float(sol.optimality),fit_rmse_um=float(np.sqrt(np.mean((cc['y']-y)**2))*1000))

def bestfit(ops,y,sigma,fixed=None,starts=STARTS):
    results=[fit(ops,y,sigma,s,fixed) for s in starts]
    best=min(results,key=lambda r:r['chi2']);best['start_chi2']=[r['chi2'] for r in results]
    best['all_starts_success']=all(r['success'] for r in results)
    return best

def sweep():
    rows=[];spectra=[]
    ops=operators([(100,240)])
    for sd in np.linspace(.2,.5,31):
        theta=np.array([.02,.75,.005,sd]);r=ops[0].evaluate(theta,jacobian=True)
        zero=theta.copy();zero[2]=0
        J=r['jacobian']*SCALE/.0001
        _,sing,V=np.linalg.svd(J,full_matrices=False)
        loaded=ops[0].xi1[(r['forces']>1e-8)&ops[0].valid]
        result=bestfit(ops,r['prediction'],.0001)
        est=np.array(result['theta']);err=np.abs(est-theta)/SCALE
        rows.append(dict(sd_true=float(sd),singular_values=sing.tolist(),numerical_rank=int(np.sum(sing>sing[0]*1e-7)),
                         dedendum_signal_rms_um=float(np.sqrt(np.mean((r['prediction']-predict(ops,zero))**2))*1000),
                         min_loaded_xi=float(loaded.min()),n_loaded_relief_points=int(np.sum(loaded<sd)),
                         recovery=result,addendum_scaled_error=float(err[:2].max()),dedendum_scaled_error=float(err[2:].max())))
        print('sweep',round(sd,3),rows[-1]['numerical_rank'],round(rows[-1]['dedendum_signal_rms_um'],6),flush=True)
    for sd in [.25,.4]:
        theta=np.array([.02,.75,.005,sd])
        for T in [50,100,200,300]:
            op=operators([(T,120)])[0];r=op.evaluate(theta,jacobian=True)
            J=r['jacobian']*SCALE/.0001;_,s,V=np.linalg.svd(J,full_matrices=False)
            spectra.append(dict(sd_true=sd,torque_Nm=T,singular_values=s.tolist(),right_singular_vectors=V.tolist(),
                                dedendum_column_norms=np.linalg.norm(J[:,2:],axis=0).tolist(),
                                fisher_condition=float((s[0]/s[-1])**2) if s[-1]>0 else None))
    (OUT/'support_transition.json').write_text(json.dumps(dict(provenance=provenance(),rows=rows,spectra=spectra),indent=2),encoding='utf-8')
    fig,axes=plt.subplots(1,3,figsize=(13,4))
    sd=[r['sd_true'] for r in rows]
    axes[0].semilogy(sd,[max(r['dedendum_signal_rms_um'],1e-12) for r in rows],'.-')
    axes[0].axhline(.1,color='k',ls='--',label='Noise σ = 0.1 µm');axes[0].legend(fontsize=8)
    axes[0].set_ylabel('Dedendum-induced TE RMS (µm)')
    axes[1].plot(sd,[r['numerical_rank'] for r in rows],'.-');axes[1].set_yticks(range(5));axes[1].set_ylabel('Numerical rank')
    axes[2].semilogy(sd,[max(r['dedendum_scaled_error'],1e-12) for r in rows],'.-');axes[2].set_ylabel('Scaled dedendum recovery error')
    for ax in axes:ax.set_xlabel('True dedendum start $s_d$');ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(OUT/'support_transition.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,sd in zip(axes,[.25,.4]):
        for r in spectra:
            if r['sd_true']==sd:ax.semilogy(range(1,5),r['singular_values'],'o-',label=f"{r['torque_Nm']:.0f} Nm")
        ax.set_xticks(range(1,5));ax.set_xlabel('Singular value index');ax.set_ylabel('Scaled, whitened singular value');ax.set_title(f'True $s_d$ = {sd}');ax.legend(fontsize=8);ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(OUT/'analytic_spectra.png',dpi=160);plt.close(fig)

def profiles():
    records=[]
    for sd in [.25,.4]:
        theta=np.array([.02,.75,.005,sd])
        for name,design in DESIGNS.items():
            ops=operators(design);sigma=.0001
            y=predict(ops,theta)+np.random.default_rng(20261012).normal(0,sigma,120)
            base=bestfit(ops,y,sigma)
            for index,grid in [(3,np.linspace(.05,.5,46)),(2,np.linspace(0,.05,41))]:
                rows=[]
                for value in grid:
                    result=bestfit(ops,y,sigma,{index:float(value)},starts=[np.array(base['theta']),*STARTS])
                    rows.append(dict(value=float(value),**result))
                minchi=min(base['chi2'],min(r['chi2'] for r in rows))
                for r in rows:r['delta_chi2']=max(0,r['chi2']-minchi)
                records.append(dict(sd_true=sd,design=name,parameter=['Ca','sa','Cd','sd'][index],sigma_um=.1,
                                    seed=20261012,baseline=base,rows=rows,
                                    threshold_note='3.841 is a nominal Wilks diagnostic; coverage is not certified near bounds/weak directions.'))
                (OUT/'profile_likelihood.json').write_text(json.dumps(dict(provenance=provenance(),records=records),indent=2),encoding='utf-8')
                print('profile',sd,name,index,'range',min(r['delta_chi2'] for r in rows),max(r['delta_chi2'] for r in rows),flush=True)
    fig,axes=plt.subplots(2,2,figsize=(11,7))
    for i,sd in enumerate([.25,.4]):
        for j,param in enumerate(['sd','Cd']):
            ax=axes[i,j]
            for r in records:
                if r['sd_true']==sd and r['parameter']==param:
                    factor=1000 if param=='Cd' else 1
                    ax.plot([t['value']*factor for t in r['rows']],[t['delta_chi2'] for t in r['rows']],label=r['design'])
            ax.axhline(3.841,color='k',ls='--');ax.set_ylim(0,15);ax.set_xlabel('$s_d$' if param=='sd' else '$C_d$ (µm)')
            ax.set_ylabel('Profile Δχ²');ax.set_title(f'True $s_d$ = {sd}');ax.legend(fontsize=8);ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(OUT/'profile_likelihood.png',dpi=160);plt.close(fig)

_WORKER_OPS={}
def monte_one(task):
    sd,name,sigma_um,seed=task
    if name not in _WORKER_OPS:_WORKER_OPS[name]=operators(DESIGNS[name])
    ops=_WORKER_OPS[name];theta=np.array([.02,.75,.005,sd]);sigma=sigma_um*.001
    y=predict(ops,theta)+np.random.default_rng(seed).normal(0,sigma,120)
    result=bestfit(ops,y,sigma);est=np.array(result['theta']);err=np.abs(est-theta)/SCALE
    xi=np.linspace(0,1,1001);micro=TipRelief()
    profile_rmse=float(np.sqrt(np.mean((micro.evaluate(xi,est)-micro.evaluate(xi,theta))**2))*1000)
    held=operators([(200,240)]) if 'held' not in _WORKER_OPS else _WORKER_OPS['held']
    _WORKER_OPS['held']=held
    held_rmse=float(np.sqrt(np.mean((predict(held,est)-predict(held,theta))**2))*1000)
    return dict(sd_true=sd,design=name,sigma_um=sigma_um,seed=seed,**result,
                addendum_scaled_error=float(err[:2].max()),dedendum_scaled_error=float(err[2:].max()),
                full_profile_rmse_um=profile_rmse,heldout200_rmse_um=held_rmse)

def monte_carlo(workers=2,nseeds=100):
    tasks=[(sd,name,sig,seed) for sd in [.25,.4] for name in DESIGNS for sig in [.1,.5,1] for seed in range(nseeds)]
    path=OUT/'monte_carlo_records.jsonl';existing=[]
    if path.exists():existing=[json.loads(s) for s in path.read_text().splitlines() if s.strip()]
    done={(r['sd_true'],r['design'],r['sigma_um'],r['seed']) for r in existing}
    todo=[t for t in tasks if t not in done]
    with path.open('a',encoding='utf-8') as f,cf.ProcessPoolExecutor(max_workers=workers) as pool:
        for i,record in enumerate(pool.map(monte_one,todo,chunksize=1),1):
            f.write(json.dumps(record)+'\n');f.flush()
            if i%20==0:print('MC completed',len(existing)+i,'/',len(tasks),flush=True)
    rr=[json.loads(s) for s in path.read_text().splitlines() if s.strip()];summary=[]
    for sd in [.25,.4]:
        for name in DESIGNS:
            for sig in [.1,.5,1]:
                group=[r for r in rr if r['sd_true']==sd and r['design']==name and r['sigma_um']==sig]
                result=dict(sd_true=sd,design=name,sigma_um=sig,n=len(group),success=sum(r['success'] for r in group),
                            all_starts_success=sum(r['all_starts_success'] for r in group))
                for metric in ['addendum_scaled_error','dedendum_scaled_error','full_profile_rmse_um','heldout200_rmse_um']:
                    a=np.array([r[metric] for r in group]);result[metric]=dict(median=float(np.median(a)),p90=float(np.quantile(a,.9)),p95=float(np.quantile(a,.95)))
                summary.append(result)
    (OUT/'monte_carlo_summary.json').write_text(json.dumps(dict(provenance=provenance(),expected=len(tasks),records=len(rr),
                        design='Two fixed starts independent of true theta; 120 observations in each design; 100 seeds/cell.',summary=summary),indent=2),encoding='utf-8')
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for ax,sd in zip(axes,[.25,.4]):
        for name in DESIGNS:
            g=[r for r in summary if r['sd_true']==sd and r['design']==name]
            ax.plot([r['sigma_um'] for r in g],[r['dedendum_scaled_error']['median'] for r in g],'o-',label=name)
            ax.plot([r['sigma_um'] for r in g],[r['dedendum_scaled_error']['p90'] for r in g],':')
        ax.set_xlabel('Noise σ (µm)');ax.set_ylabel('Scaled dedendum error: median / dotted p90');ax.set_title(f'True $s_d$ = {sd}');ax.legend(fontsize=8);ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(OUT/'monte_carlo.png',dpi=160);plt.close(fig)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['sweep','profiles','mc']);ap.add_argument('--workers',type=int,default=2);ap.add_argument('--seeds',type=int,default=100);a=ap.parse_args()
    {'sweep':sweep,'profiles':profiles,'mc':lambda:monte_carlo(a.workers,a.seeds)}[a.command]()
