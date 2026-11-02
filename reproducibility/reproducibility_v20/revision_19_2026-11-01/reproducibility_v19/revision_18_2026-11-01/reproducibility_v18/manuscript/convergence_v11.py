"""24/24 bulk mesh study with identical interior phases and fixed interface.

The h=0.5 archive is preserved. New h=0.35 and 0.25 cycles use the same
P1/nodal 0.02 mm interface. This isolates bulk mesh sensitivity; it does not
certify interface, corner contact, or geometrically remeshed relief.
"""
import sys,json,time
from pathlib import Path
import numpy as np
BASE=Path(__file__).resolve().parent
ROOT=BASE.parent;DEP=ROOT/'deposit_v6';OUT=ROOT/'revision_11_2026-10-23'
sys.path[:0]=[str(ROOT/'fe2d'),str(DEP/'gear_inverse_identifiability/src'),str(DEP/'gear_inverse_identifiability/experiments')]
import run_fe2d as fe
from geometry.microgeometry import TipRelief
from geometry.involute import InvoluteGear,GearPair
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator
from Q1_identifiability_campaign import fit,BOUNDS
fe.configure_24_24();micro=TipRelief()
truth=np.array([.02,.75,.01,.5]);ad=truth.copy();ad[2]=0
src=DEP/'results/independent_validation/11_fe_cycle_24_24.jsonl'
arch=[json.loads(s) for s in src.read_text().splitlines() if s.strip()]
phases=sorted({r['phase_fraction'] for r in arch if not r['restricted_nominal_window']})

def generate(h):
    dest=OUT/f'fe24_h{h:g}.jsonl';rr=[]
    if dest.exists():rr=[json.loads(x) for x in dest.read_text().splitlines() if x.strip()]
    done={r['phase_fraction'] for r in rr}
    with dest.open('a',encoding='utf-8') as file:
        for fraction in phases:
            if fraction in done:continue
            t=time.time();contact=fe.contacts(fraction,.35,.02,allow_clipped=False)
            bodies=[fe.mesh_body(contact,i,h,12.,.4,f'v11_{h}_{fraction}_{i}',1,'nodal',None,1) for i in (1,2)]
            H=sum(b['H'] for b in bodies);g0=np.concatenate([c['gap'] for c in contact]);F=300000/fe.RB
            for name,theta in [('unmodified',None),('addendum',ad),('dedendum',truth)]:
                gap=g0.copy()
                if theta is not None:gap+=np.concatenate([micro.evaluate(np.clip(np.asarray(c['v1'])/fe.UA,0,1),theta) for c in contact])
                sol=fe.solve_contact(H,gap,F)
                record=dict(h_mm=h,step_mm=.02,phase_fraction=fraction,case=name,approach_um=float(sol['delta']*1000),
                            nodes=[b['nodes'] for b in bodies],force_residual_N=sol['force_residual_N'],contact_residual_mm=sol['gap_residual_mm'])
                file.write(json.dumps(record)+'\n');rr.append(record)
            file.flush()
            print('h',h,'phase',fraction,'seconds',round(time.time()-t,2),flush=True)
    return rr

def summarize():
    rows=[];rng=np.random.default_rng(20261024)
    starts=[np.array([.03,.65,.01,.35]),np.array([.015,.85,.02,.45])]
    starts += [BOUNDS[:,0]+rng.random(4)*(BOUNDS[:,1]-BOUNDS[:,0]) for _ in range(10)]
    for h in [.5,.35,.25]:
        path=OUT/f'fe24_h{h:g}.jsonl'
        rr=arch if h==.5 else [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
        curves={}
        for case in ['unmodified','addendum','dedendum']:
            d={r['phase_fraction']:r['approach_um'] for r in rr if r['case']==case}
            a=np.array([d[p] for p in phases]);curves[case]=(a-a.mean())*.001
        pair=GearPair(InvoluteGear(24,3,20,20),InvoluteGear(24,3,20,20))
        op=BatchedGapOperator(GearContactModel(pair,micro1=micro,compliance_variant='projected-energy'),300,phi_positions=np.array(phases)*2*np.pi/24)
        attempts=[fit([op],curves['dedendum'],.0001,s,max_nfev=1600) for s in starts]
        best=min(attempts,key=lambda r:r['chi2'])
        rows.append(dict(h_mm=h,step_mm=.02,n_phases=len(phases),
                         isolated_dedendum_rms_um=float(np.sqrt(np.mean((curves['dedendum']-curves['addendum'])**2))*1000),
                         estimate=best['theta'],fit_rmse_um=best['fit_rmse_um'],success=best['success'],
                         profile_rmse_um=float(np.sqrt(np.mean((micro.evaluate(np.linspace(0,1,1001),np.array(best['theta']))-micro.evaluate(np.linspace(0,1,1001),truth))**2))*1000),
                         max_force_residual_N=max(r['force_residual_N'] for r in rr),
                         max_contact_residual_mm=max(r['contact_residual_mm'] for r in rr)))
    (OUT/'mesh_convergence.json').write_text(json.dumps(dict(scope='P1 bulk refinement at fixed nodal interface and fixed nominal geometry; 102 common interior phases',rows=rows),indent=2))
    print(rows,flush=True)

if __name__=='__main__':
    OUT.mkdir(exist_ok=True)
    for h in [.35,.25]:generate(h)
    summarize()
