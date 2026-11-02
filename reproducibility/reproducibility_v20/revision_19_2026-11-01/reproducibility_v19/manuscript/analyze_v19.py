"""Full-cycle numerical receipts; no smoothing or forced periodic closure."""
from pathlib import Path
import json,csv,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'revision_19_2026-11-01';EXP=OUT/'experiments'
EXCLUDED=list(range(24,33))+list(range(88,97))
def rms(x):return float(np.sqrt(np.mean(np.asarray(x)**2)))
def center(x):return np.asarray(x)-np.mean(x)

def main():
    summaries=[];curves={};allrows=[]
    for step,h in [(.04,.5),(.02,.35)]:
        path=EXP/f'cycle_s{step:g}_h{h:g}.jsonl';rr=[json.loads(x) for x in path.read_text().splitlines() if x.strip()]
        assert len(rr)==363 and len({(r['case'],r['phase']) for r in rr})==363
        assert all(r['converged'] and r['gap_error_um']<.00011 and r['penetration_um']<.00011 and r['torque_relative_error']<1e-6 and r['elastic_relative_error']<1e-5 and r['overlap_area_mm2']<1e-8 for r in rr)
        cases={}
        for case in ['nominal','addendum','combined']:
            ss=sorted([r for r in rr if r['case']==case],key=lambda r:r['phase']);assert len(ss)==121
            assert np.max(abs(np.array([r['phase'] for r in ss])-np.arange(121)/120))<1e-12
            y=np.array([r['approach_um'] for r in ss]);curves[(step,case)]=y
            cases[case]=dict(centered_RMS_um=rms(center(y[:120])),closure_um=float(y[-1]-y[0]),formerly_excluded_count=18)
            assert all((EXP/'cycle_states'/r['state_file']).exists() for r in ss)
        contrast=center(curves[(step,'combined')][:120]-curves[(step,'addendum')][:120])
        summaries.append(dict(step_mm=step,h_mm=h,states=len(rr),cycle_observations=360,closure_controls=3,cases=cases,dedendum_centered_RMS_um=rms(contrast),dedendum_excluded_RMS_um=rms(contrast[EXCLUDED]),dedendum_interior_RMS_um=rms(contrast[[i for i in range(120) if i not in EXCLUDED]]),
            maximum_gap_error_um=max(r['gap_error_um'] for r in rr),maximum_penetration_um=max(r['penetration_um'] for r in rr),maximum_torque_relative_error=max(r['torque_relative_error'] for r in rr),maximum_elastic_relative_error=max(r['elastic_relative_error'] for r in rr),maximum_overlap_area_mm2=max(r['overlap_area_mm2'] for r in rr),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        allrows.extend(rr)
    differences={case:rms(center(curves[(.02,case)][:120])-center(curves[(.04,case)][:120])) for case in ['nominal','addendum','combined']}
    transition_differences={case:rms((center(curves[(.02,case)][:120])-center(curves[(.04,case)][:120]))[EXCLUDED]) for case in ['nominal','addendum','combined']}
    raw_transition_differences={case:rms((curves[(.02,case)][:120]-curves[(.04,case)][:120])[EXCLUDED]) for case in ['nominal','addendum','combined']}
    contrast_diff=rms(center(curves[(.02,'combined')][:120]-curves[(.02,'addendum')][:120])-center(curves[(.04,'combined')][:120]-curves[(.04,'addendum')][:120]))
    approximation=[]
    for step in [.08,.04]:
        p=EXP/f'reference_truth_s{step:g}.json'
        if not p.exists():continue
        r=json.loads(p.read_text());y=np.array(r['prediction_um'])
        approximation.append(dict(step_mm=step,truth_RMS_against_fine_generator_um=rms(center(y)-center(curves[(.02,'combined')][:120])),truth_RMS_against_coarse_generator_um=rms(center(y)-center(curves[(.04,'combined')][:120]))))
    inverse=[]
    for name in ['inverse_reference_s0.08.json','inverse_reference_s0.04.json','inverse_analytic.json']:
        p=EXP/name
        if p.exists():
            for r in json.loads(p.read_text()):
                q=dict(file=name,**{k:v for k,v in r.items() if k not in ['forward_records','full_cycle_prediction_um','full_cycle_diagnostics']})
                if 'theta' in r:
                    xi=np.linspace(0,1,1001)
                    def relief(th):
                        ca,sa,cd,sd=th
                        return ca*(np.maximum(xi-sa,0)/(1-sa))**2+cd*(np.maximum(sd-xi,0)/sd)**2
                    q['normal_relief_RMS_um']=1000*rms(relief(r['theta'])-relief([.02,.75,.01,.5]))
                    q['scaled_parameter_error']=float(np.linalg.norm((np.array(r['theta'])-[.02,.75,.01,.5])/[.02,.2,.01,.3]))
                if 'full_cycle_prediction_um' in r:
                    idx=r['indices'];held=[i for i in range(120) if i not in idx];pred=np.asarray(r['full_cycle_prediction_um']);y=curves[(.02,'combined')][:120]
                    err=pred-pred[idx].mean()-(y-y[idx].mean())
                    q['unseen_stations_RMS_um']=rms(err[held])
                inverse.append(q)
    a=dict(cycle=summaries,cycle_centered_refinement_RMS_um=differences,transition_centered_refinement_RMS_um=transition_differences,transition_raw_refinement_RMS_um=raw_transition_differences,dedendum_contrast_refinement_RMS_um=contrast_diff,states=726,cycle_observations=720,closure_controls=6,excluded_indices=EXCLUDED,approximation=approximation,inverse=inverse)
    (OUT/'analysis_v19.json').write_text(json.dumps(a,indent=2))
    with (OUT/'cycle_results_v19.csv').open('w',newline='',encoding='utf-8') as f:
        keys=['step_mm','h_mm','case','phase','approach_um','gap_error_um','penetration_um','torque_relative_error','elastic_relative_error','overlap_area_mm2'];w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(allrows)
    plt.rcParams.update({'font.size':11});fig,axes=plt.subplots(2,2,figsize=(10,7));x=np.arange(120)/120
    for step,label,style in [(.04,'0.04 / 0.50 mm','--'),(.02,'0.02 / 0.35 mm','-')]:
        axes[0,0].plot(x,center(curves[(step,'combined')][:120]),style,label=label)
        axes[0,1].plot(x,center(curves[(step,'combined')][:120]-curves[(step,'addendum')][:120]),style,label=label)
    for case in ['nominal','addendum','combined']:axes[1,0].plot(x,center(curves[(.02,case)][:120])-center(curves[(.04,case)][:120]),label=case)
    for a0,b0 in [(24,32),(88,96)]:
        for ax in axes.flat:ax.axvspan(a0/120,b0/120,color='#efb566',alpha=.25)
    ax=axes[1,1]
    for step in [.08,.04]:
        p=EXP/f'reference_truth_s{step:g}.json'
        if p.exists():ax.plot(x,center(json.loads(p.read_text())['prediction_um'])-center(curves[(.02,'combined')][:120]),label=f'Reference {step:g} mm at truth')
    for ax,title in zip(axes.flat,['(a) Modified-profile TE','(b) Isolated dedendum contrast','(c) Fine minus coarse TE','(d) Inverse approximation at truth']):ax.set_title(title);ax.set_xlabel('Canonical tooth-pass fraction');ax.set_ylabel('Mean-removed difference (µm)' if ax!=axes[0,0] else 'Mean-removed TE (µm)');ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.tight_layout();fig.savefig(OUT/'cycle_v19.png',dpi=300);plt.close(fig)
    print(json.dumps({k:v for k,v in a.items() if k!='inverse'},indent=2))
if __name__=='__main__':main()
