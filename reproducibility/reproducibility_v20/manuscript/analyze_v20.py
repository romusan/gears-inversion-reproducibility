"""Common metrics for the original and additional fine-reference attempts."""
from pathlib import Path
import json,csv
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT/'revision_19_2026-11-01';OUT=ROOT/'revision_20_2026-11-01';EXP=OUT/'experiments'
TRUTH=np.array([.02,.75,.01,.5]);SCALE=np.array([.02,.2,.01,.3])
def rms(x):return float(np.sqrt(np.mean(np.asarray(x)**2)))
def relief(th):
    x=np.linspace(0,1,1001);ca,sa,cd,sd=th
    return ca*(np.maximum(x-sa,0)/(1-sa))**2+cd*(np.maximum(sd-x,0)/sd)**2
def main():
    old=json.loads((OLD/'analysis_v19.json').read_text());rr=[json.loads(s) for s in (OLD/'experiments/cycle_s0.02_h0.35.jsonl').read_text().splitlines()];y=np.array([r['approach_um'] for r in sorted(rr,key=lambda r:r['phase']) if r['case']=='combined' and r['phase']<1])
    original=json.loads((OLD/'experiments/inverse_reference_s0.04.json').read_text());attempts=[]
    for r in original:
        q={k:v for k,v in r.items() if k not in ['forward_records','full_cycle_diagnostics']};q.update(origin='v19',start_id='R0' if r['restricted'] else 'P')
        if 'full_cycle_prediction_um' in r:q['prediction_um']=r['full_cycle_prediction_um']
        attempts.append(q)
    for design in ['interior','with_transitions']:
        raw=json.loads((EXP/f'starts_{design}.json').read_text());assert len(raw)==6
        for r in raw:
            q={k:v for k,v in r.items() if k not in ['forward_records','prediction_diagnostics']};q.update(origin='v20',start_id=('R' if r['restricted'] else 'S')+str(r['attempt_id']+1));q['indices']=next(s['indices'] for s in original if s['design']==design)
            attempts.append(q)
    selected=[]
    for r in attempts:
        if 'theta' not in r:continue
        r['normal_relief_RMS_um']=1000*rms(relief(r['theta'])-relief(TRUTH));r['scaled_parameter_error']=float(np.linalg.norm((np.array(r['theta'])-TRUTH)/SCALE))
        if 'prediction_um' in r:
            pred=np.array(r['prediction_um']);idx=r['indices'];delta=pred-pred[idx].mean()-(y-y[idx].mean());held=[i for i in range(120) if i not in idx]
            r['full_cycle_prediction_RMS_um']=rms((pred-pred.mean())-(y-y.mean()));r['unseen_stations_RMS_um']=rms(delta[held])
            assert abs(r['residual_RMS_um']-rms(delta[idx]))<.0002
    for design in ['interior','with_transitions']:
        for restricted in [False,True]:
            best=min([r for r in attempts if r['design']==design and r['restricted']==restricted and 'cost' in r],key=lambda r:r['cost']);selected.append({k:v for k,v in best.items() if k not in ['prediction_um','full_cycle_prediction_um']})
    diagnostic=json.loads((EXP/'design_diagnostic_v20.json').read_text());ccx=json.loads((OUT/'audit_ccx_v20.json').read_text())
    summary=dict(fine_attempts=attempts,fine_selected=selected,additional_attempts=12,total_cycle_inverse_attempts=30,failed_additional=sum(not r.get('success',False) for r in attempts if r['origin']=='v20'),local_design=diagnostic,calculix=ccx,original_cycle_summary={k:v for k,v in old.items() if k!='inverse'})
    (OUT/'analysis_v20.json').write_text(json.dumps(summary,indent=2))
    keys=['design','restricted','start_id','origin','theta','success','nfev','cost','residual_RMS_um','normal_relief_RMS_um','unseen_stations_RMS_um']
    with (OUT/'fine_starts_v20.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(attempts)
    print('Fine attempts',len(attempts),'Additional failed flags',summary['failed_additional']);print([(r['design'],r['restricted'],r['theta'],r['residual_RMS_um']) for r in selected])
if __name__=='__main__':main()
