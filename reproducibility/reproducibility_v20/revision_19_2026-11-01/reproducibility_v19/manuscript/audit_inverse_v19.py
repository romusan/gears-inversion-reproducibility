"""Verify objective arithmetic and fresh-cycle predictions at saved best fits."""
import json
import numpy as np
from inverse_moving_v19 import OUT,target,INTERIOR,DESIGN,LO,HI

def main():
    y=target();reports=[];count=0;computed=0
    for name,n in [('inverse_reference_s0.08.json',6),('inverse_reference_s0.04.json',4),('inverse_analytic.json',8)]:
        rr=json.loads((OUT/name).read_text());assert len(rr)==n
        for r in rr:
            count+=1
            assert r['indices']==(INTERIOR if r['design']=='interior' else DESIGN)
            if 'theta' not in r:continue
            computed+=1
            th=np.array(r['theta']);assert np.all(th>=LO-1e-10) and np.all(th<=HI+1e-10)
            if r['restricted']:assert th[2]==0 and th[3]==.5
            expected=.5*len(r['indices'])*(r['residual_RMS_um']/.1)**2
            assert abs(r['cost']-expected)<1e-8*max(expected,1)
            for a in r.get('forward_records',[]):
                assert a['maximum_gap_um']<.000011 and a['maximum_penetration_um']<.000011
                assert a['maximum_torque_relative_error']<1e-6 and a['maximum_elastic_relative_error']<1e-5 and a['maximum_overlap_area_mm2']<1e-8
            if 'full_cycle_prediction_um' in r:
                pred=np.array(r['full_cycle_prediction_um']);idx=r['indices'];res=pred[idx]-pred[idx].mean()-(y[idx]-y[idx].mean());err=float(abs(np.sqrt(np.mean(res**2))-r['residual_RMS_um']))
                assert err<.0002,(name,r['design'],err)
                reports.append(dict(file=name,design=r['design'],restricted=r['restricted'],fresh_cycle_vs_fitted_training_RMS_difference_um=err))
    assert count==18
    (OUT.parent/'audit_inverse_v19.json').write_text(json.dumps(dict(attempts=count,computed_objectives=computed,all_computed_objectives_consistent=True,records=reports),indent=2));print('Verified',count,'inverse attempts',len(reports),'complete-cycle checks')
if __name__=='__main__':main()
