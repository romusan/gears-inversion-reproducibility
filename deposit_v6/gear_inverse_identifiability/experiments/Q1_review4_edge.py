"""Local bisection resolves onset hidden by a sampled xi_min tie."""
import json
import numpy as np
from Q1_review3_grid_control import InvoluteGear,GearPair,TipRelief,GearContactModel,BatchedGapOperator
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]/'results/q1_review4_2026-10-12'
rows=[]
for variant in ['legacy','shear-G','projected-energy','centerline-energy']:
    pair=GearPair(InvoluteGear(24,3,20,20),InvoluteGear(48,3,20,20));model=GearContactModel(pair,TipRelief(),compliance_variant=variant)
    for T in [50,300]:
        theta=np.array([.02,.75,0,.25]);op=BatchedGapOperator(model,T,960);r=op.evaluate(theta)
        loaded=(r['forces']>1e-8)&op.valid;candidate=np.where(loaded,op.xi1,np.inf);i,k=np.unravel_index(np.argmin(candidate),candidate.shape)
        centre=op.phi[i];target=float(op.xi1[i,k]);step=op.phi[1]-op.phi[0]
        def evaluate(phi):
            q=BatchedGapOperator(model,T,phi_positions=np.array([phi]));v=q.evaluate(theta)
            j=int(np.argmin(abs(q.xi1[0]-target)))
            return float(v['forces'][0,j]),float(q.xi1[0,j])
        lo=centre-2*step;hi=centre
        assert evaluate(lo)[0]<=1e-8 and evaluate(hi)[0]>1e-8
        for _ in range(32):
            mid=(lo+hi)/2
            if evaluate(mid)[0]>1e-8:hi=mid
            else:lo=mid
        force,xi=evaluate(hi)
        rows.append(dict(variant=variant,torque_Nm=T,sampled_min_xi=target,onset_xi=xi,
            onset_phi_rad=hi,bracket_width_rad=hi-lo,force_threshold_N=1e-8,sd_minus_onset=.25-xi))
(OUT/'support_edge_bisection.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps(rows,indent=2))
