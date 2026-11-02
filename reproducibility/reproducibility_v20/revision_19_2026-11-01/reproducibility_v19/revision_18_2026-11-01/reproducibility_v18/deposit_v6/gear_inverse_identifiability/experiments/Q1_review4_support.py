"""Contact-support sensitivity to analytical mechanical assumptions."""
import json
import numpy as np
from Q1_review3_grid_control import InvoluteGear,GearPair,TipRelief,GearContactModel,BatchedGapOperator,SCALE,SIGMA
from campaign_provenance import provenance
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]/'results/q1_review4_2026-10-12';OUT.mkdir(exist_ok=True)
rows=[]
for n in [120,960]:
    for variant in ['legacy','shear-G','projected-energy','centerline-energy']:
        pair=GearPair(InvoluteGear(24,3,20,20),InvoluteGear(48,3,20,20))
        model=GearContactModel(pair,TipRelief(),compliance_variant=variant)
        for torque in [50,300]:
            op=BatchedGapOperator(model,torque,n)
            for depth in [0,.005]:
                theta=np.array([.02,.75,depth,.25]);r=op.evaluate(theta,jacobian=True)
                mask=(r['forces']>1e-8)&op.valid;ss=np.linalg.svd(r['jacobian']*SCALE/SIGMA,compute_uv=False)
                rows.append(dict(n_positions=n,variant=variant,torque_Nm=torque,dedendum_depth_mm=depth,
                    min_loaded_xi=float(op.xi1[mask].min()),sd_minus_min_loaded_xi=float(.25-op.xi1[mask].min()),
                    relief_contact_count=int(np.sum(op.xi1[mask]<.25)),sigma4=float(ss[-1]),
                    rank=int(np.sum(ss>ss[0]*1e-7))))
(OUT/'support_variants.json').write_text(json.dumps(dict(provenance=provenance(),rows=rows,
    scope='Nominal G0 geometry; zero-dedendum reference and 5 micrometre truth. FE benchmark uses different geometry and its xi_min cannot replace the G0 result.'),indent=2),encoding='utf-8')
print(json.dumps(rows,indent=2))
