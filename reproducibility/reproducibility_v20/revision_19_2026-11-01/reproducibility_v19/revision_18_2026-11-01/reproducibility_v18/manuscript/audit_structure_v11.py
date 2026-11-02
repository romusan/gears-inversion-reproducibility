"""Recompute the observation null space and all 48 benchmark amplitudes."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent;DEP=ROOT/'deposit_v6'
OUT=ROOT/'revision_11_2026-10-23'
sys.path[:0]=[str(DEP/'gear_inverse_identifiability/src'),str(DEP/'gear_inverse_identifiability/experiments')]
from geometry.microgeometry import TipRelief,GridRelief
from geometry.involute import InvoluteGear,GearPair
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator
from V06_korta_mundo_reproduction import build_pair,SOLUTIONS,REFERENCE_PP,rt_to_sa,TORQUES

grid=GridRelief(41);tip=TipRelief();pair=GearPair(InvoluteGear(24,3,20,20),InvoluteGear(48,3,20,20))
op=BatchedGapOperator(GearContactModel(pair,micro1=grid,compliance_variant='projected-energy'),300,120)
h=tip.evaluate(grid.grid,np.array([.02,.75,.005,.25]));res=op.evaluate(h,jacobian=True)
J=res['jacobian']/.0001;u,s,v=np.linalg.svd(J,full_matrices=False)
rank=int(np.sum(s>s[0]*1e-7));col=np.linalg.norm(J,axis=0);sensitive=col>s[0]*1e-9
ns=dict(rank=rank,n_nodes=41,zero_columns=np.flatnonzero(~sensitive).tolist(),
        first_sensitive_node=float(grid.grid[np.flatnonzero(sensitive)[0]]),
        minimum_loaded_coordinate=float(op.xi1[(res['forces']>1e-8)&op.valid].min()),
        global_constant_relative_residual=float(np.linalg.norm(J@np.ones(41))/s[0]),
        sensitive_constant_relative_residual=float(np.linalg.norm(J@sensitive.astype(float))/s[0]),
        direction_std_um=(1000/s[:rank]).tolist())
# The positive/negative test distinguishes local null directions from finite gap changes.
ns['finite_perturbations']=[]
for name,d in [('global_constant',np.ones(41)),('below_support_node',np.eye(41)[0]),('sensitive_constant',sensitive.astype(float))]:
    ns['finite_perturbations'].append(dict(direction=name,change_rms_um=[float(1000*np.sqrt(np.mean((op.evaluate(h+a*d)['prediction']-res['prediction'])**2))) for a in [-.005,.005]]))
rows=[];bp=build_pair();micro=TipRelief(p=1)
for variant in ['legacy','shear-G','projected-energy','centerline-energy']:
    model=GearContactModel(bp,micro1=micro,micro2=micro,compliance_variant=variant)
    for case in ['unmodified',*SOLUTIONS]:
        theta=None if case=='unmodified' else np.array([SOLUTIONS[case]['d_um']*.001,rt_to_sa(SOLUTIONS[case]['rt_mm'],bp.g1),0,.5])
        for torque in TORQUES:
            operator=BatchedGapOperator(model,torque,240)
            y=operator.evaluate(theta,theta)['prediction']
            pp=float(np.ptp(y)*1000);ref=REFERENCE_PP[case,torque]
            rows.append(dict(variant=variant,case=case,torque_Nm=torque,model_pp_um=pp,reference_pp_um=ref,relative_error_percent=100*(pp-ref)/ref))
out=dict(null_space=ns,benchmark=rows,benchmark_geometry=dict(alpha_w_deg=float(np.rad2deg(bp.alpha_w)),contact_ratio=float(bp.eps_alpha)))
(OUT/'audit_structure.json').write_text(json.dumps(out,indent=2))
print(json.dumps(ns,indent=2))
for variant in ['legacy','shear-G','projected-energy','centerline-energy']:
    a=[r['relative_error_percent'] for r in rows if r['variant']==variant];print(variant,min(a),max(a))
