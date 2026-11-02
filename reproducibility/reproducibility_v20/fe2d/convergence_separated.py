"""Separate bulk FE resolution and interface pressure-station spacing."""
import json
from run_fe2d import run,OUT
rows=[]
# Fixed near-contact mesh size; body and interface are varied independently.
configs=[('bulk',h,.01) for h in [.5,.35,.25]]+[('interface',.25,d) for d in [.02,.005]]
for label,h,d in configs:
    for phase in [0,.5]:
        r=run(phase,h,d,25,.4,traction='weak_hat',local_h=.01,degree=2)
        r['study']=label;rows.append(r)
        (OUT/'separated_convergence_partial.json').write_text(json.dumps(rows,indent=2))
(OUT/'separated_convergence.json').write_text(json.dumps(dict(records=rows,
    formulation='Normalized continuous pressure hats integrated against actual quadratic FE boundary trace; gap constraints averaged with the same hats.',
    fixed_local_mesh_mm=.01,element_degree=2,
    scope='Interior phases; weak contact constraints. Bulk and interface studies vary separate controls; no corner validation.'),indent=2))
print('Separated convergence complete',flush=True)
