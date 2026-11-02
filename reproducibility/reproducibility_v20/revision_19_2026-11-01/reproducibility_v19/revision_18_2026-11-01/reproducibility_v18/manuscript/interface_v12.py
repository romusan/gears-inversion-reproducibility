"""Separate 24/24 weak-contact interface control on fixed P2 body meshes.

Twenty-four common interior phases. Geometric boundary vertices, local mesh
target and bulk h are held fixed while the pressure-hat spacing changes.
"""
import sys,json,time
from pathlib import Path
import numpy as np
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent;OUT=ROOT/'revision_12_2026-10-23'
sys.path[:0]=[str(ROOT/'fe2d'),str(ROOT/'deposit_v6/gear_inverse_identifiability/src')]
import run_fe2d as fe
from geometry.microgeometry import TipRelief
fe.configure_24_24();micro=TipRelief();truth=np.array([.02,.75,.01,.5]);ad=truth.copy();ad[2]=0
arch=[json.loads(x) for x in (ROOT/'deposit_v6/results/independent_validation/11_fe_cycle_24_24.jsonl').read_text().splitlines()]
interior=sorted({r['phase_fraction'] for r in arch if not r['restricted_nominal_window']})
ustart=np.sqrt(fe.UF**2+2*.4/fe.RB)
eligible=[p for p in interior if all(min(c['v1'].min(),c['v2'].min())>ustart+.0001 for c in fe.contacts(p,.35,.04,False))]
(OUT/'interface_phase_selection.json').write_text(json.dumps(dict(interior_count=len(interior),eligible_count=len(eligible),criterion='Both candidate traces above the root-blend boundary',eligible_phases=eligible),indent=2))
phases=np.array(eligible)[np.round(np.linspace(0,len(eligible)-1,24)).astype(int)].tolist()
def average(c,theta):
    out=[]
    for cc in c:
        x=cc['x'];g=cc['gap'].copy()
        if theta is not None:g+=micro.evaluate(np.asarray(cc['v1'])/fe.UA,theta)
        M=np.zeros((len(x),len(x)))
        for j,d in enumerate(np.diff(x)):M[j:j+2,j:j+2]+=d*np.array([[2,1],[1,2]])/6
        out.extend((M@g)/M.sum(axis=1))
    return np.array(out)
def main():
    dest=OUT/'interface24_verified_records.jsonl';records=[]
    if dest.exists():records=[json.loads(x) for x in dest.read_text().splitlines()]
    done={(r['step_mm'],r['phase_fraction']) for r in records}
    with dest.open('a',encoding='utf-8') as file:
        for step in [.04,.02,.01]:
            for phase in phases:
                if (step,phase) in done:continue
                t=time.time();c=fe.contacts(phase,.35,step,False)
                bodies=[fe.mesh_body(c,i,.35,12.,.4,f'interface12_{step}_{phase}_{i}',1,'weak_hat',.02,2) for i in (1,2)]
                H=sum(b['H'] for b in bodies);F=300000/fe.RB
                approaches={};errors=[]
                for name,theta in [('unmodified',None),('addendum',ad),('combined',truth)]:
                    sol=fe.solve_contact(H,average(c,theta),F);approaches[name]=1000*sol['delta'];errors.append(sol['gap_residual_mm'])
                row=dict(step_mm=step,phase_fraction=phase,h_mm=.35,local_h_mm=.02,degree=2,traction='weak_hat',
                         approaches_um=approaches,nodes=[b['nodes'] for b in bodies],elements=[b['elements'] for b in bodies],
                         max_contact_residual_mm=max(errors),seconds=time.time()-t)
                file.write(json.dumps(row)+'\n');file.flush();records.append(row)
                print('interface',step,phase,'seconds',round(row['seconds'],1),flush=True)
    rows=[]
    for step in [.04,.02,.01]:
        rr=sorted([r for r in records if r['step_mm']==step],key=lambda r:r['phase_fraction'])
        assert len(rr)==24
        combined=np.array([r['approaches_um']['combined'] for r in rr]);add=np.array([r['approaches_um']['addendum'] for r in rr])
        diff=combined-add;diff-=diff.mean()
        rows.append(dict(step_mm=step,isolated_dedendum_rms_um=float(np.sqrt(np.mean(diff**2))),
                         combined_mean_removed_um=(combined-combined.mean()).tolist(),
                         isolated_signal_um=diff.tolist(),nodes=[r['nodes'] for r in rr]))
    # Same phase and body have exactly the same mesh node count at all spacings.
    assert rows[0]['nodes']==rows[1]['nodes']==rows[2]['nodes']
    for previous,current in zip(rows[:-1],rows[1:]):
        current['combined_waveform_change_rms_um']=float(np.sqrt(np.mean((np.array(current['combined_mean_removed_um'])-previous['combined_mean_removed_um'])**2)))
        current['isolated_signal_relative_change_percent']=100*(current['isolated_dedendum_rms_um']/previous['isolated_dedendum_rms_um']-1)
    (OUT/'interface24_summary.json').write_text(json.dumps(dict(phases=phases,scope='24 interior phases; fixed P2 body meshes and fixed normals; averaged gaps and pressure hats',rows=rows),indent=2))
    print(rows,flush=True)
if __name__=='__main__':main()
