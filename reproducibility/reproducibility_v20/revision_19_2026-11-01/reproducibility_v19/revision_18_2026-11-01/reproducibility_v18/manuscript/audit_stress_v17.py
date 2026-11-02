"""Independent checks of archived stress observations, objectives and partitions."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
import json,hashlib,sys
import numpy as np
from scipy.linalg import solve_triangular
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'revision_17_final_2026-11-01'
sys.path.insert(0,str(ROOT/'deposit_v6/gear_inverse_identifiability/src'))
from geometry.involute import InvoluteGear,GearPair
from geometry.microgeometry import TipRelief
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator
def main():
    rows=[json.loads(x) for x in (OUT/'stress_records.jsonl').read_text().splitlines()]
    summary=json.loads((OUT/'stress_summary.json').read_text());assert len(rows)==500
    assert len({(r['sd_true'],r['scenario'],r['seed']) for r in rows})==500
    pair=GearPair(InvoluteGear(24,3,20,20),InvoluteGear(48,3,20,20))
    ops={k:BatchedGapOperator(GearContactModel(pair,micro1=TipRelief(),compliance_variant=k),300,120) for k in ['projected-energy','shear-G']}
    C=.8**np.abs(np.arange(120)[:,None]-np.arange(120)[None,:]);L=np.linalg.cholesky(C)
    sigma=.0001;scale=np.array([.05,1,.01,1]);bounds=np.array([[0,.1],[.3,.95],[0,.05],[.05,.5]])
    max_obj=0.;max_signal=0.;allattempts=0
    for r in rows:
        truth=np.array(r['truth']);theta=np.array(r['theta']);y=np.array(r['observations_mm']);g=np.array(r['generating_prediction_mm'])
        nominal=ops['projected-energy'].evaluate(truth)['prediction']
        expected=ops['shear-G'].evaluate(truth)['prediction'] if r['scenario']=='operator_iid_fit' else nominal.copy()
        if r['scenario']=='gain5_iid_fit':expected*=1.05
        max_signal=max(max_signal,float(np.max(abs(g-expected))))
        z=np.random.default_rng(2026110100+r['seed']).normal(size=120)
        assert np.allclose(y-g,sigma*(L@z if r['scenario'].startswith('correlated_') else z),rtol=1e-10,atol=1e-15)
        residual=ops['projected-energy'].evaluate(theta)['prediction']-y
        white=solve_triangular(L,residual,lower=True)/sigma if r['scenario']=='correlated_gls_fit' else residual/sigma
        obj=float(white@white);max_obj=max(max_obj,abs(obj-r['chi2'])/(1+obj))
        assert np.isclose(obj,r['chi2'],rtol=1e-8,atol=1e-8)
        assert np.isclose(1000*np.sqrt(np.mean(residual**2)),r['fit_rmse_um'],rtol=1e-8)
        pred=residual+y
        assert np.isclose(1000*np.sqrt(np.mean((pred-g)**2)),r['prediction_error_vs_generator_um'],rtol=1e-8)
        assert np.isclose(1000*np.sqrt(np.mean((g-nominal)**2)),r['deterministic_discrepancy_rms_um'],rtol=1e-8,atol=1e-12)
        xx=np.linspace(0,1,1001);micro=TipRelief()
        assert np.isclose(1000*np.sqrt(np.mean((micro.evaluate(xx,theta)-micro.evaluate(xx,truth))**2)),r['full_profile_rmse_um'],rtol=1e-8)
        assert np.isclose(np.max(abs(theta[2:]-truth[2:])/scale[2:]),r['dedendum_scaled_error'])
        flags=np.minimum(theta-bounds[:,0],bounds[:,1]-theta)<=1e-6*np.diff(bounds,axis=1).ravel()
        assert flags.tolist()==r['bound_flags'] and bool(any(flags[2:]))==r['dedendum_bound']
        best=min(r['attempts'],key=lambda a:a['chi2']);assert best['theta']==r['theta'] and best['success']==r['success']
        allattempts+=len(r['attempts'])
    assert allattempts==1500 and max_signal<1e-14
    for c in summary['cells']:
        rr=[r for r in rows if r['sd_true']==c['sd_true'] and r['scenario']==c['scenario']];assert len(rr)==50
        st=c['strata'];assert st['converged_interior']['n']+st['converged_bound']['n']+st['failed']['n']==50
        assert np.isclose(st['all']['dedendum']['median'],np.median([r['dedendum_scaled_error'] for r in rr]))
    for path,h in summary['source_sha256'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h
    archived=json.loads((OUT/'archived_status_strata.json').read_text())
    assert sum(c['n'] for c in archived['cells'])==1800
    for c in archived['cells']:assert sum(c['strata'][k]['n'] if c['strata'][k] else 0 for k in ['converged_interior','converged_bound','failed'])==100
    for path,h in archived['source_sha256'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h
    report=dict(cases=500,attempts=allattempts,observation_seed_and_covariance_checked=True,all_selected_objectives_recomputed=True,profile_and_response_errors_recomputed=True,max_relative_objective_difference=max_obj,max_generator_difference_mm=max_signal,per_coordinate_bounds_checked=True,status_partitions_checked=True,unchanged_archived_selections=1800,source_hashes_checked=True)
    (OUT/'numerical_audit_v17.json').write_text(json.dumps(report,indent=2));print(report)
if __name__=='__main__':main()
