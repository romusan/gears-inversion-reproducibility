"""Saved-fit diagnostics, paired bootstrap and held-out operator transfer."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
import json,hashlib,sys
import numpy as np
from scipy.linalg import solve_triangular
from scipy.stats import chi2
import stress_v17 as v
from stress_v18 import harmonic
ROOT=v.ROOT;OUT=ROOT/'revision_18_2026-11-01'
SCENARIOS=['iid','correlated_iid_fit','correlated_gls_fit','correlated_fgls_fit','gain5_iid_fit','operator_iid_fit','rotation_harmonics','tooth_harmonic']
def med(a):return float(np.median(a)) if len(a) else None
def main():
    old=ROOT/'revision_17_final_2026-11-01/stress_records.jsonl';extra=OUT/'extension_records.jsonl'
    rows=[json.loads(x) for p in [old,extra] for x in p.read_text().splitlines()];assert len(rows)==1100
    assert len({(r['sd_true'],r['scenario'],r['seed']) for r in rows})==1100
    pair=v.GearPair(v.InvoluteGear(24,3,20,20),v.InvoluteGear(48,3,20,20));ops={k:v.BatchedGapOperator(v.GearContactModel(pair,micro1=v.TipRelief(),compliance_variant=k),200,240) for k in ['projected-energy','shear-G']}
    fitop,L=v.operators();fitop=fitop['projected-energy'];cut=float(chi2.ppf(.95,120));derived=[]
    for r in rows:
        est=np.array(r['theta']);truth=np.array(r['truth']);nom=ops['projected-energy'].evaluate(truth)['prediction'];pred=ops['projected-energy'].evaluate(est)['prediction'];g=ops['shear-G'].evaluate(truth)['prediction'] if r['scenario']=='operator_iid_fit' else nom.copy()
        if r['scenario']=='gain5_iid_fit':g*=1.05
        g+=harmonic(r['scenario'],r['seed'],240)
        residual=fitop.evaluate(est)['prediction']-np.array(r['observations_mm']);W=None;sigma=v.SIGMA
        if r['scenario']=='correlated_gls_fit':W=L
        if r['scenario']=='correlated_fgls_fit':
            W=np.linalg.cholesky(r['rho_estimated']**np.abs(np.arange(120)[:,None]-np.arange(120)[None,:]));sigma=r['sigma_estimated_mm']
        wh=(residual if W is None else solve_triangular(W,residual,lower=True))/sigma;score=float(wh@wh);assert np.isclose(score,r['chi2'],rtol=1e-8,atol=1e-8)
        flags=np.minimum(est-v.BOUNDS[:,0],v.BOUNDS[:,1]-est)<=1e-6*np.diff(v.BOUNDS,axis=1).ravel();assert flags.tolist()==r['bound_flags']
        derived.append(dict(sd_true=r['sd_true'],scenario=r['scenario'],seed=r['seed'],success=r['success'],bound_flags=r['bound_flags'],dedendum_bound=r['dedendum_bound'],dedendum_error=r['dedendum_scaled_error'],profile_um=r['full_profile_rmse_um'],residual_um=r['fit_rmse_um'],window_bias_um=r['deterministic_discrepancy_rms_um'],Q=score,Q_per_n=score/120,score_flag=score>cut if r['scenario']!='correlated_fgls_fit' else None,heldout_nominal_um=1000*v.rms(pred-nom),heldout_generator_um=1000*v.rms(pred-g),rho_estimated=r.get('rho_estimated'),sigma_estimated_um=1000*r.get('sigma_estimated_mm',v.SIGMA)))
    local=[]
    for sd in [.25,.4]:
        truth=np.array([.02,.75,.005,sd]);J=fitop.evaluate(truth,jacobian=True)['jacobian']*v.SCALE
        gls=np.linalg.pinv(solve_triangular(L,J,lower=True)/v.SIGMA,rcond=1e-14);ols=np.linalg.pinv(J,rcond=1e-14)@L*v.SIGMA
        local.append(dict(sd=sd,scaled_linear_std_gls=np.sqrt(np.diag(gls@gls.T)).tolist(),scaled_linear_std_ols=np.sqrt(np.diag(ols@ols.T)).tolist(),box_width_scaled=(np.diff(v.BOUNDS,axis=1).ravel()/v.SCALE).tolist(),scope='Unbounded local linear noise propagation under known AR covariance; not coverage or nonlinear performance'))
    cells=[]
    for sd in [.25,.4]:
        for scenario in SCENARIOS:
            rr=[r for r in derived if r['sd_true']==sd and r['scenario']==scenario];assert len(rr)==(200 if sd==.4 and scenario in ['iid','gain5_iid_fit'] else 50)
            cells.append(dict(sd=sd,scenario=scenario,n=len(rr),failed=sum(not r['success'] for r in rr),depth_bound=sum(r['bound_flags'][2] for r in rr),start_bound=sum(r['bound_flags'][3] for r in rr),any_bound=sum(r['dedendum_bound'] for r in rr),score_flags=None if scenario=='correlated_fgls_fit' else sum(r['score_flag'] for r in rr),screen_pass_error_median=med([r['dedendum_error'] for r in rr if r['score_flag'] is False]),**{k:med([r[k] for r in rr]) for k in ['dedendum_error','profile_um','residual_um','window_bias_um','Q_per_n','heldout_nominal_um','heldout_generator_um','rho_estimated','sigma_estimated_um'] if k!='rho_estimated' or scenario=='correlated_fgls_fit'},interior_median=med([r['dedendum_error'] for r in rr if r['success'] and not r['dedendum_bound']])))
    rng=np.random.default_rng(20261118);boot=[];reps=[]
    for sd,a,b,n in [(.25,'gain5_iid_fit','iid',50),(.4,'gain5_iid_fit','iid',50),(.4,'gain5_iid_fit','iid',200),(.25,'correlated_gls_fit','correlated_iid_fit',50),(.4,'correlated_gls_fit','correlated_iid_fit',50),(.25,'correlated_fgls_fit','correlated_iid_fit',50),(.4,'correlated_fgls_fit','correlated_iid_fit',50)]:
        aa={r['seed']:r for r in derived if r['sd_true']==sd and r['scenario']==a and r['seed']<n};bb={r['seed']:r for r in derived if r['sd_true']==sd and r['scenario']==b and r['seed']<n};assert len(aa)==len(bb)==n
        ids=sorted(aa);idx=rng.integers(0,n,size=(10000,n));result=dict(sd=sd,A=a,B=b,n=n,statistic='median(A)-median(B), paired percentile bootstrap',metrics={})
        for key in ['dedendum_error','profile_um','heldout_nominal_um']:
            x=np.array([aa[i][key] for i in ids]);y=np.array([bb[i][key] for i in ids]);dist=np.median(x[idx],axis=1)-np.median(y[idx],axis=1)
            result['metrics'][key]=dict(median_A=med(x),median_B=med(y),difference=med(x)-med(y),lower=float(np.quantile(dist,.025)),upper=float(np.quantile(dist,.975)))
            reps.append(dict(sd=sd,A=a,B=b,n=n,metric=key,replicates=dist.tolist()))
        common=[i for i in ids if aa[i]['success'] and bb[i]['success'] and not aa[i]['dedendum_bound'] and not bb[i]['dedendum_bound']]
        result['joint_converged_interior']=dict(n=len(common),median_A=med([aa[i]['dedendum_error'] for i in common]),median_B=med([bb[i]['dedendum_error'] for i in common]))
        boot.append(result)
    (OUT/'derived_records.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in derived),encoding='utf-8');(OUT/'bootstrap_replicates.json').write_text(json.dumps(reps))
    summary=dict(selected_cases=1100,original_cases=500,new_cases=600,final_attempts=sum(len(r['attempts']) for r in rows),pilot_attempts=sum(len(r.get('pilot_attempts',[])) for r in rows),failed_selected=sum(not r['success'] for r in rows),failed_final_attempts=sum(not a['success'] for r in rows for a in r['attempts']),failed_pilot_attempts=sum(not a['success'] for r in rows for a in r.get('pilot_attempts',[])),cells=cells,local_linear_covariance=local,bootstrap=boot,bootstrap_seed=20261118,bootstrap_samples=10000,score_cutoff=cut,heldout=dict(torque_Nm=200,phases=240,noise_free=True,scope='same-operator transfer, not physical validation'),source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [old,extra,Path(__file__),ROOT/'manuscript/stress_v18.py',ROOT/'manuscript/stress_v17.py']})
    summary['environment']=dict(python=sys.version,numpy=np.__version__,scipy=v.scipy.__version__)
    (OUT/'analysis_v18.json').write_text(json.dumps(summary,indent=2));print(json.dumps({'counts':[summary[k] for k in ['selected_cases','new_cases','final_attempts','pilot_attempts']],'bootstrap_gain':boot[2],'AR_cells':[c for c in cells if c['scenario'].startswith('correlated')]},indent=2))
if __name__=='__main__':main()
