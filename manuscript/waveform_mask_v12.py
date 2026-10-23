"""Common-mask full-waveform and mask-sensitivity audit; no unresolved FE phases used."""
import sys,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from audit_v11 import GearPair,InvoluteGear,GearContactModel,TipRelief,BatchedGapOperator,fit,SCALE,BOUNDS
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent;OUT=ROOT/'revision_12_2026-10-23';OLD=ROOT/'revision_11_2026-10-23'
rms=lambda x:float(np.sqrt(np.mean(np.array(x)**2)))
arch=[json.loads(x) for x in (ROOT/'deposit_v6/results/independent_validation/11_fe_cycle_24_24.jsonl').read_text().splitlines()]
interior=sorted({r['phase_fraction'] for r in arch if not r['restricted_nominal_window']})
indices=np.round(np.array(interior)*120).astype(int);valid=set(indices);truth=np.array([.02,.75,.01,.5])
pair=GearPair(InvoluteGear(24,3,20,20),InvoluteGear(24,3,20,20));micro=TipRelief()
def operator(ph):return BatchedGapOperator(GearContactModel(pair,micro1=micro,compliance_variant='projected-energy'),300,phi_positions=np.array(ph)*2*np.pi/24)
curves={};wave=[];meshes=json.loads((OLD/'mesh_convergence.json').read_text())['rows']
plt.rcParams.update({'font.size':18});fig,axes=plt.subplots(2,2,figsize=(13,8))
for h in [.5,.35,.25]:
 records=arch if h==.5 else [json.loads(x) for x in (OLD/f'fe24_h{h:g}.jsonl').read_text().splitlines()]
 cc={}
 for case in ['unmodified','addendum','dedendum']:
  look={r['phase_fraction']:r['approach_um'] for r in records if r['case']==case};a=np.array([look[p] for p in interior]);cc[case]=a-a.mean()
 curves[h]=cc;est=next(m['estimate'] for m in meshes if m['h_mm']==h);pred=1000*operator(interior).evaluate(np.array(est))['prediction'];res=pred-cc['dedendum']
 wave.append(dict(h_mm=h,combined_rms_um=rms(cc['dedendum']),residual_rms_um=rms(res),combined_centered_um=cc['dedendum'].tolist(),residual_um=res.tolist()))
 axes[0,0].plot(interior,cc['dedendum'],label=f'h={h} mm');axes[0,1].plot(interior,cc['dedendum']-cc['addendum'],label=f'h={h} mm');axes[1,1].plot(interior,res,label=f'h={h} mm')
 if h!=.5:
  d=cc['dedendum']-curves[.5]['dedendum'];axes[1,0].plot(interior,d,label=f'{h} − 0.50 mm')
  wave[-1].update(combined_change_from_coarsest_rms_um=rms(d),combined_correlation_with_coarsest=float(np.corrcoef(cc['dedendum'],curves[.5]['dedendum'])[0,1]),isolated_change_from_coarsest_rms_um=rms(cc['dedendum']-cc['addendum']-(curves[.5]['dedendum']-curves[.5]['addendum'])))
for a,title in zip(axes.flat,['Combined-relief TE','Isolated dedendum response','Bulk mesh change','Analytical fit residual']):a.set(title=title,xlabel='Mesh-cycle fraction',ylabel='Response (µm)');a.grid(alpha=.2);a.legend(fontsize=16)
fig.tight_layout();fig.savefig(BASE/'assets/fig_waveforms_v12.png',dpi=210);plt.close(fig)
starts=[np.array([.03,.65,.01,.35]),np.array([.015,.85,.02,.45])];rng=np.random.default_rng(20261025)
starts += [BOUNDS[:,0]+rng.random(4)*(BOUNDS[:,1]-BOUNDS[:,0]) for _ in range(6)]
rows=[]
for guard in [-1,0,1,2,3]:
 ids=list(range(120)) if guard==-1 else [i for i in indices if all((i+j)%120 in valid for j in range(-guard,guard+1))]
 ph=np.array(ids)/120;op=operator(ph);out=op.evaluate(truth,jacobian=True);sv=np.linalg.svd(out['jacobian']*SCALE/.0001,compute_uv=False);z=truth.copy();z[2]=0
 row=dict(mask='full_analytical_only' if guard==-1 else f'interior_guard_{guard}',n=len(ids),indices=[int(i) for i in ids],rank=int(sum(sv>sv[0]*1e-7)),singular_values=sv.tolist(),budget_normalized_smin=float(sv[-1]*np.sqrt(120/len(ids))),isolated_analytical_rms_um=1000*rms(out['prediction']-op.evaluate(z)['prediction']))
 if guard>=0:
  positions=[list(indices).index(i) for i in ids];y=curves[.5]['dedendum'][positions]*.001;y-=y.mean()
  attempts=[fit([op],y,.0001,s,max_nfev=1600) for s in starts];nulls=[fit([op],y,.0001,s,fixed={2:0.,3:.5},max_nfev=1600) for s in starts]
  best=min(attempts,key=lambda r:r['chi2']);null=min(nulls,key=lambda r:r['chi2']);row.update(best=best,restricted=null,delta_chi2_no_dedendum=null['chi2']-best['chi2'])
 rows.append(row)
(OUT/'waveform_mask_audit.json').write_text(json.dumps(dict(scope='P1 full-waveform comparisons on 102 common phases; cyclic guard erosion; 120-phase analysis is analytical only',phases=interior,waveforms=wave,masks=rows),indent=2));print([(r['mask'],r['n'],r.get('delta_chi2_no_dedendum')) for r in rows])
