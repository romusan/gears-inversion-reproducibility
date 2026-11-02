"""Extend saved v17 controls; preserve old results; no physical validation."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
import json,hashlib,time,concurrent.futures as cf
import numpy as np
from scipy.optimize import least_squares
from scipy.linalg import solve_triangular
import stress_v17 as v
ROOT=v.ROOT;OUT=ROOT/'revision_18_2026-11-01'
def fit_data(y,op,L=None,sigma=v.SIGMA):
    def white(a):return (a if L is None else solve_triangular(L,a,lower=True,check_finite=False))/sigma
    aa=[]
    for start in v.STARTS:
        cache={}
        def ev(q):
            if 'q' not in cache or not np.array_equal(cache['q'],q):
                r=op.evaluate(q*v.SCALE,jacobian=True);cache.update(q=q.copy(),r=white(r['prediction']-y),J=white(r['jacobian']*v.SCALE))
            return cache
        f=least_squares(lambda q:ev(q)['r'],start/v.SCALE,jac=lambda q:ev(q)['J'],bounds=(v.BOUNDS[:,0]/v.SCALE,v.BOUNDS[:,1]/v.SCALE),max_nfev=600,ftol=1e-9,xtol=1e-10,gtol=1e-8)
        aa.append(dict(start=start.tolist(),theta=(f.x*v.SCALE).tolist(),chi2=float(2*f.cost),success=bool(f.success),status=int(f.status),nfev=int(f.nfev),optimality=float(f.optimality)))
    return aa,min(aa,key=lambda a:a['chi2'])
def harmonic(scenario,seed,n):
    phases=np.random.default_rng(2026111800+seed).uniform(0,2*np.pi,2);u=np.arange(n)/n
    if scenario=='rotation_harmonics':h=.0001*(np.cos(2*np.pi*u/24+phases[0])+np.cos(4*np.pi*u/24+phases[1]))
    elif scenario=='tooth_harmonic':h=np.sqrt(2)*.0001*np.cos(2*np.pi*u+phases[0])
    else:return np.zeros(n)
    return h-h.mean()
def run(task):
    sd,scenario,seed=task
    if scenario in ['iid','gain5_iid_fit']:return v.run_case(task)
    ops,L=v.operators();op=ops['projected-energy'];truth=np.array([.02,.75,.005,sd]);g=op.evaluate(truth)['prediction'];z=np.random.default_rng(2026110100+seed).normal(size=120)
    pilot=[];rho=None;sigma=v.SIGMA;h=harmonic(scenario,seed,120)
    y=g+h+v.SIGMA*(L@z if scenario=='correlated_fgls_fit' else z)
    if scenario=='correlated_fgls_fit':
        pilot,best=fit_data(y,op);res=y-op.evaluate(np.array(best['theta']))['prediction'];res-=res.mean()
        rho=float(np.clip(np.dot(res[:-1],res[1:])/max(np.dot(res[:-1],res[:-1]),1e-30),-.95,.95));sigma=float(max(np.sqrt(np.mean(res**2)),1e-8))
        L=np.linalg.cholesky(rho**np.abs(np.arange(120)[:,None]-np.arange(120)[None,:]))
    aa,best=fit_data(y,op,L if scenario=='correlated_fgls_fit' else None,sigma);est=np.array(best['theta']);pred=op.evaluate(est)['prediction'];flags=np.minimum(est-v.BOUNDS[:,0],v.BOUNDS[:,1]-est)<=1e-6*np.diff(v.BOUNDS,axis=1).ravel();xx=np.linspace(0,1,1001);micro=v.TipRelief()
    return dict(sd_true=sd,scenario=scenario,seed=seed,truth=truth.tolist(),theta=est.tolist(),success=best['success'],chi2=best['chi2'],attempts=aa,pilot_attempts=pilot,rho_estimated=rho,sigma_estimated_mm=sigma,bound_flags=flags.tolist(),dedendum_bound=bool(any(flags[2:])),dedendum_scaled_error=float(np.max(abs(est[2:]-truth[2:])/v.SCALE[2:])),full_profile_rmse_um=1000*v.rms(micro.evaluate(xx,est)-micro.evaluate(xx,truth)),fit_rmse_um=1000*v.rms(pred-y),prediction_error_vs_generator_um=1000*v.rms(pred-g-h),deterministic_discrepancy_rms_um=1000*v.rms(h),noise_rms_um=1000*v.rms(y-g-h),observations_mm=y.tolist(),generating_prediction_mm=(g+h).tolist())
def main():
    OUT.mkdir(exist_ok=True);start=time.time();path=OUT/'extension_records.jsonl';receipt=OUT/'extension_source.json';sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    rows=[]
    if path.exists():
        assert json.loads(receipt.read_text())['sha256']==sha;rows=[json.loads(x) for x in path.read_text().splitlines()]
    receipt.write_text(json.dumps({'sha256':sha,'base_source_sha256':hashlib.sha256(Path(v.__file__).read_bytes()).hexdigest()}))
    tasks=[(.4,c,i) for c in ['iid','gain5_iid_fit'] for i in range(50,200)]+[(sd,c,i) for sd in [.25,.4] for c in ['rotation_harmonics','tooth_harmonic','correlated_fgls_fit'] for i in range(50)]
    done={(r['sd_true'],r['scenario'],r['seed']) for r in rows};assert len(done)==len(rows)
    with path.open('a',encoding='utf-8') as f,cf.ProcessPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(run,t) for t in tasks if t not in done]
        for fu in cf.as_completed(futures):
            r=fu.result();rows.append(r);f.write(json.dumps(r)+'\n');f.flush()
            if len(rows)%25==0:print('Completed',len(rows),'/600;',round(time.time()-start,1),'s',flush=True)
    assert len(rows)==600
    (OUT/'extension_run.json').write_text(json.dumps({'new_cases':len(rows),'final_attempts':sum(len(r['attempts']) for r in rows),'pilot_attempts':sum(len(r.get('pilot_attempts',[])) for r in rows),'seconds':time.time()-start},indent=2))
if __name__=='__main__':main()
