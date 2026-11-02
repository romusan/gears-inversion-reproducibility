"""Audit every added attempt and repeat selected full predictions from cold states."""
import json,hashlib
from pathlib import Path
import numpy as np
from inverse_moving_v19 import ROOT,FastOperator,target,INTERIOR,DESIGN,LO,HI
OUT=ROOT/'revision_20_2026-11-01';EXP=OUT/'experiments'
def main():
    y=target();source=hashlib.sha256((ROOT/'manuscript/starts_v20.py').read_bytes()).hexdigest();count=0;reports=[]
    old=json.loads((ROOT/'revision_19_2026-11-01/experiments/inverse_reference_s0.04.json').read_text())
    for design in ['interior','with_transitions']:
        rr=json.loads((EXP/f'starts_{design}.json').read_text());assert len(rr)==6 and len({r['attempt_id'] for r in rr})==6
        for r in rr:
            count+=1;assert r['source_sha256']==source
            if 'theta' not in r:continue
            th=np.array(r['theta']);assert np.all(th>=LO-1e-10) and np.all(th<=HI+1e-10)
            assert abs(r['cost']-.5*30*(r['residual_RMS_um']/.1)**2)<1e-8*max(r['cost'],1)
            for q in r['forward_records']:
                assert q['maximum_gap_um']<.000011 and q['maximum_penetration_um']<.000011 and q['maximum_torque_relative_error']<1e-6 and q['maximum_elastic_relative_error']<1e-5 and q['maximum_overlap_area_mm2']<1e-8
        pool=[r for r in old+rr if r['design']==design and not r['restricted'] and 'cost' in r];b=min(pool,key=lambda r:r['cost'])
        cached=np.array(b.get('prediction_um',b.get('full_cycle_prediction_um')));idx=INTERIOR if design=='interior' else DESIGN
        op=FastOperator(.04,.5,reference=True);pred,diag=op.predict(np.array(b['theta']),np.arange(120)/120,tol=.00001)
        error=(pred-pred.mean())-(cached-cached.mean());maximum=float(max(abs(error)));assert maximum<.0002,(design,maximum)
        reports.append(dict(design=design,theta=b['theta'],cold_vs_saved_centered_max_um=maximum,cold_vs_saved_centered_RMS_um=float(np.sqrt(np.mean(error**2))),cold_prediction_um=pred.tolist(),diagnostics=diag))
    assert count==12
    (OUT/'audit_starts_v20.json').write_text(json.dumps(dict(additional_attempts=12,all_objectives_consistent=True,selected_cold_checks=reports),indent=2));print('Audited',count,'additional attempts and two cold cycles')
if __name__=='__main__':main()
