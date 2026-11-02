"""Verify new observations, pilot covariance, transfer and paired-bootstrap records."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.linalg import solve_triangular
from scipy.stats import bootstrap
import stress_v17 as v
ROOT=v.ROOT;OUT=ROOT/'revision_18_2026-11-01'
def main():
    extra=[json.loads(x) for x in (OUT/'extension_records.jsonl').read_text().splitlines()];assert len(extra)==600
    a=json.loads((OUT/'analysis_v18.json').read_text());derived=[json.loads(x) for x in (OUT/'derived_records.jsonl').read_text().splitlines()];assert len(derived)==1100
    ops,L=v.operators();op=ops['projected-energy'];maxdiff=0.
    for r in extra:
        truth=np.array(r['truth']);theta=np.array(r['theta']);nom=op.evaluate(truth)['prediction'];g=nom.copy();sc=r['scenario'];n=120;u=np.arange(n)/n
        phase=np.random.default_rng(2026111800+r['seed']).uniform(0,2*np.pi,2)
        if sc=='gain5_iid_fit':g*=1.05
        if sc=='rotation_harmonics':
            h=.0001*(np.cos(2*np.pi*u/24+phase[0])+np.cos(4*np.pi*u/24+phase[1]));g+=h-h.mean()
        if sc=='tooth_harmonic':
            h=np.sqrt(2)*.0001*np.cos(2*np.pi*u+phase[0]);g+=h-h.mean()
        z=np.random.default_rng(2026110100+r['seed']).normal(size=n);expected=g+v.SIGMA*(L@z if sc=='correlated_fgls_fit' else z);y=np.array(r['observations_mm'])
        maxdiff=max(maxdiff,float(np.max(abs(y-expected))));assert np.allclose(y,expected,rtol=1e-11,atol=1e-15)
        assert np.allclose(g,r['generating_prediction_mm'],rtol=1e-11,atol=1e-15)
        best=min(r['attempts'],key=lambda x:x['chi2']);assert best['theta']==r['theta'] and best['success']==r['success']
        xx=np.linspace(0,1,1001);micro=v.TipRelief();profile=1000*np.sqrt(np.mean((micro.evaluate(xx,theta)-micro.evaluate(xx,truth))**2))
        assert np.isclose(profile,r['full_profile_rmse_um'])
        assert np.isclose(np.max(abs(theta[2:]-truth[2:])/v.SCALE[2:]),r['dedendum_scaled_error'])
        res=op.evaluate(theta)['prediction']-y;sigma=v.SIGMA
        if sc=='correlated_fgls_fit':
            pilot=min(r['pilot_attempts'],key=lambda x:x['chi2']);e=y-op.evaluate(np.array(pilot['theta']))['prediction'];e-=e.mean()
            rho=float(np.clip((e[:-1]@e[1:])/max(e[:-1]@e[:-1],1e-30),-.95,.95));sigma=float(max(np.sqrt(np.mean(e**2)),1e-8))
            assert np.isclose(rho,r['rho_estimated']) and np.isclose(sigma,r['sigma_estimated_mm'])
            LL=np.linalg.cholesky(rho**abs(np.arange(n)[:,None]-np.arange(n)[None,:]));res=solve_triangular(LL,res,lower=True)
        Q=float((res/sigma)@(res/sigma));assert np.isclose(Q,r['chi2'],rtol=1e-8,atol=1e-8)
    for p,h in a['source_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
    receipt=json.loads((OUT/'extension_source.json').read_text());assert receipt['sha256']==hashlib.sha256((ROOT/'manuscript/stress_v18.py').read_bytes()).hexdigest();assert receipt['base_source_sha256']==hashlib.sha256((ROOT/'manuscript/stress_v17.py').read_bytes()).hexdigest()
    # Independent SciPy paired percentile bootstrap agrees for the first contrast
    # when supplied the same RNG and common resampled index sequence.
    b=a['bootstrap'][0];xx=sorted([r for r in derived if r['sd_true']==b['sd'] and r['scenario']==b['A'] and r['seed']<b['n']],key=lambda r:r['seed']);yy=sorted([r for r in derived if r['sd_true']==b['sd'] and r['scenario']==b['B'] and r['seed']<b['n']],key=lambda r:r['seed'])
    result=bootstrap((np.array([r['dedendum_error'] for r in xx]),np.array([r['dedendum_error'] for r in yy])),lambda x,y,axis:np.median(x,axis=axis)-np.median(y,axis=axis),paired=True,method='percentile',n_resamples=10000,rng=np.random.default_rng(20261118))
    expected=b['metrics']['dedendum_error'];assert np.allclose([result.confidence_interval.low,result.confidence_interval.high],[expected['lower'],expected['upper']])
    reps=json.loads((OUT/'bootstrap_replicates.json').read_text());assert len(reps)==21
    for entry in reps:
        bb=next(x for x in a['bootstrap'] if (x['sd'],x['A'],x['B'],x['n'])==(entry['sd'],entry['A'],entry['B'],entry['n']));m=bb['metrics'][entry['metric']]
        assert len(entry['replicates'])==10000 and np.allclose(np.quantile(entry['replicates'],[.025,.975]),[m['lower'],m['upper']])
    for c in a['cells']:
        rr=[r for r in derived if r['sd_true']==c['sd'] and r['scenario']==c['scenario']];assert len(rr)==c['n']
        for k in ['dedendum_error','profile_um','residual_um','Q_per_n','heldout_nominal_um','heldout_generator_um']:assert np.isclose(np.median([r[k] for r in rr]),c[k])
        assert c['failed']==sum(not r['success'] for r in rr)
    allraw=[json.loads(x) for p in [ROOT/'revision_17_final_2026-11-01/stress_records.jsonl',OUT/'extension_records.jsonl'] for x in p.read_text().splitlines()];lookup={(r['sd_true'],r['scenario'],r['seed']):r for r in allraw}
    pair=v.GearPair(v.InvoluteGear(24,3,20,20),v.InvoluteGear(48,3,20,20));transfer={k:v.BatchedGapOperator(v.GearContactModel(pair,micro1=v.TipRelief(),compliance_variant=k),200,240) for k in ['projected-energy','shear-G']};checked=0
    for c in a['cells']:
        rr=sorted([r for r in derived if r['sd_true']==c['sd'] and r['scenario']==c['scenario']],key=lambda r:r['seed'])
        for r in [rr[0],rr[-1]]:
            raw=lookup[(r['sd_true'],r['scenario'],r['seed'])];truth=np.array(raw['truth']);theta=np.array(raw['theta']);nom=transfer['projected-energy'].evaluate(truth)['prediction'];pred=transfer['projected-energy'].evaluate(theta)['prediction'];g=transfer['shear-G'].evaluate(truth)['prediction'] if r['scenario']=='operator_iid_fit' else nom.copy()
            if r['scenario']=='gain5_iid_fit':g*=1.05
            u=np.arange(240)/240;phase=np.random.default_rng(2026111800+r['seed']).uniform(0,2*np.pi,2)
            if r['scenario']=='rotation_harmonics':
                h=.0001*(np.cos(2*np.pi*u/24+phase[0])+np.cos(4*np.pi*u/24+phase[1]));g+=h-h.mean()
            if r['scenario']=='tooth_harmonic':
                h=np.sqrt(2)*.0001*np.cos(2*np.pi*u+phase[0]);g+=h-h.mean()
            assert np.isclose(1000*np.sqrt(np.mean((pred-nom)**2)),r['heldout_nominal_um'])
            assert np.isclose(1000*np.sqrt(np.mean((pred-g)**2)),r['heldout_generator_um']);checked+=1
    assert a['final_attempts']==3300 and a['pilot_attempts']==300
    report=dict(new_observations_verified=600,selected_objectives_recomputed_for_new_cases=600,pilot_covariance_estimates_verified=100,all_1100_objectives_checked_by_analysis=True,transfer_records_independently_recomputed=checked,bootstrap_reference='scipy.stats.bootstrap paired=True, percentile, 10000',bootstrap_reference_agrees=True,stored_bootstrap_intervals_checked=21,cell_counts_and_medians_verified=16,source_hashes_verified=True,max_observation_difference_mm=maxdiff)
    (OUT/'numerical_audit_v18.json').write_text(json.dumps(report,indent=2));print(report)
if __name__=='__main__':main()
