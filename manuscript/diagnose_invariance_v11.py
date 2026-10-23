"""Confirm whether the fitted dedendum is inside or outside loaded support."""
import sys,json
from pathlib import Path
import numpy as np
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent;DEP=ROOT/'deposit_v6';OUT=ROOT/'revision_11_2026-10-23'
sys.path.insert(0,str(DEP/'gear_inverse_identifiability/src'))
from geometry.involute import InvoluteGear,GearPair
from geometry.microgeometry import TipRelief
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator
audit=json.loads((OUT/'audit_inverse.json').read_text());old=json.loads((DEP/'results/independent_validation/11_fe_observable_dedendum.json').read_text())
phases=np.array(old['interior_phases'])*2*np.pi/24;pair=GearPair(InvoluteGear(24,3,20,20),InvoluteGear(24,3,20,20))
rows=[]
for r in audit['variants']:
    op=BatchedGapOperator(GearContactModel(pair,micro1=TipRelief(),compliance_variant=r['variant']),300,phi_positions=phases)
    for label,theta in [('broad_start',r['best']['theta']),('archived_two_start',next(x for x in old['rows'] if x['variant']==r['variant'])['noiseless']['estimate'])]:
        a=np.array(theta);p=op.evaluate(a,jacobian=True);z=a.copy();z[2]=0
        loaded=op.xi1[(p['forces']>1e-8)&op.valid]
        rows.append(dict(variant=r['variant'],fit=label,estimate=a.tolist(),min_loaded_coordinate=float(loaded.min()),
                         relief_start=float(a[3]),loaded_points_in_dedendum=int((loaded<a[3]).sum()),
                         deletion_of_fitted_dedendum_rms_um=float(1000*np.sqrt(np.mean((p['prediction']-op.evaluate(z)['prediction'])**2))),
                         dedendum_jacobian_column_norms=np.linalg.norm(p['jacobian'][:,2:],axis=0).tolist()))
(OUT/'audit_fit_invariance.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
