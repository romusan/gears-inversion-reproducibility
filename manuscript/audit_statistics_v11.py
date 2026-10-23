"""Check all archived 1800 statistical records without refitting them."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent;DEP=ROOT/'deposit_v6';OUT=ROOT/'revision_11_2026-10-23'
sys.path.insert(0,str(DEP/'gear_inverse_identifiability/src'))
from geometry.microgeometry import TipRelief
R=DEP/'gear_inverse_identifiability/results';micro=TipRelief();xx=np.linspace(0,1,1001);scale=np.array([.05,1,.01,1])
paths=[R/'q1_revision_2026-10-12/monte_carlo_records.jsonl',R/'q1_review5_2026-10-12/complementary_monte_records.jsonl']
campaigns=[];groups=[]
for path,expected in zip(paths,[1200,600]):
    rr=[json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    assert len(rr)==expected
    keys=[(r['sd_true'],r['design'],r['sigma_um'],r['seed']) for r in rr];assert len(keys)==len(set(keys))
    param_errors=[];profile_errors=[];cost_errors=[]
    for r in rr:
        truth=np.array([.02,.75,.005,r['sd_true']]);est=np.array(r['theta'])
        err=abs(est-truth)/scale
        param_errors.extend([abs(err[:2].max()-r['addendum_scaled_error']),abs(err[2:].max()-r['dedendum_scaled_error'])])
        cost_errors.append(abs(r['chi2']-120*(r['fit_rmse_um']/r['sigma_um'])**2))
        if 'full_profile_rmse_um' in r:
            p=float(1000*np.sqrt(np.mean((micro.evaluate(xx,est)-micro.evaluate(xx,truth))**2)))
            profile_errors.append(abs(p-r['full_profile_rmse_um']))
    for sd,design,sigma in sorted({(r['sd_true'],r['design'],r['sigma_um']) for r in rr}):
        cell=[r for r in rr if (r['sd_true'],r['design'],r['sigma_um'])==(sd,design,sigma)]
        assert len(cell)==100 and {r['seed'] for r in cell}==set(range(100))
        groups.append(dict(campaign=path.parent.name,sd_true=sd,design=design,sigma_um=sigma,n=100,
                           success=sum(r['success'] for r in cell),dedendum_median=float(np.median([r['dedendum_scaled_error'] for r in cell]))))
    campaigns.append(dict(path=str(path.relative_to(DEP)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                          records=len(rr),failed=sum(not r['success'] for r in rr),
                          max_parameter_metric_error=max(param_errors),max_profile_metric_error=max(profile_errors,default=0),
                          max_chi2_rmse_identity_error=max(cost_errors)))
    assert max(param_errors)<1e-10 and max(profile_errors,default=0)<1e-10 and max(cost_errors)<1e-6
out=dict(scope='Independent metric and integrity audit of stored fits; not a rerun of the 1800 optimizations',campaigns=campaigns,cells=groups)
(OUT/'audit_statistics.json').write_text(json.dumps(out,indent=2))
print(json.dumps(campaigns,indent=2))
