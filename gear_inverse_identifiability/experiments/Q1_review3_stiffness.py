"""Internal stiffness scales for a qualified comparison with ISO assumptions."""
import json
import numpy as np
from Q1_forward_campaign import build_pair,TipRelief,GearContactModel,BatchedGapOperator
from Q1_review3_grid_control import OUT
from campaign_provenance import provenance

pair=build_pair(); model=GearContactModel(pair,TipRelief(p=1))
op=BatchedGapOperator(model,650,1920); r=op.evaluate()
active=(r['forces']>1e-8)&op.valid; count=active.sum(axis=1)
_,tangent=op.elastic(r['forces'])
k=np.where(active,1/tangent,0).sum(axis=1)/1000
rows=[]
for n in [1,2]:
    v=k[count==n]; d=r['delta'][count==n]*1000
    rows.append(dict(loaded_pairs=n,incremental_k_min_N_um=float(v.min()),
        incremental_k_max_N_um=float(v.max()),incremental_k_median_N_um=float(np.median(v)),
        per_width_min_N_mm_um=float(v.min()/23),per_width_max_N_mm_um=float(v.max()/23),
        median_approach_um=float(np.median(d))))
report=dict(provenance=provenance(),torque_Nm=650,width_mm=23,
    normal_force_N=float(r['forces'].sum(axis=1).mean()),rows=rows,
    iso_context='ISO 6336-1:2019 clause 6.4.3, Method C simplified assumption cprime=14 N/(mm micrometre); not a universal stiffness range.',
    interpretation='Incremental fixed-phase contact tangent per face width is an order-of-magnitude comparison, not the ISO single-stiffness calculation or independent validation.')
(OUT/'stiffness_scale.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report['rows'],indent=2))
