"""Six extra phases: restricted nominal-window contact, explicit edge flags."""
import json
import numpy as np
from run_fe2d import run,OUT,RA,RB,AW,PB
span=np.sqrt(RA*RA-RB*RB)-RB*np.tan(AW)
entry=1-span/PB;exit=span/PB
phases=[entry-.025,entry+.025,entry+.06,exit-.06,exit-.025,exit+.025]
rows=[]
for phase in phases:
    rows.append(run(float(phase),.25,.01,25,.4,allow_clipped=True))
    (OUT/'transition_partial.json').write_text(json.dumps(rows,indent=2))
# An edge-bearing case needs its own refinement check.
edge=next(r for r in rows if r['tooth_edge_loaded'])
refined=run(edge['phase_fraction'],.18,.0075,25,.4,allow_clipped=True)
report=dict(entry_phase_fraction=float(entry),exit_phase_fraction=float(exit),records=rows,
    edge_refinement=refined,
    sampled_range_um=float(np.ptp([r['approach_um'] for r in rows])),
    warning='Nominal contact windows only, fixed normals, clipped flank patches. Does not resolve pre-engagement corner contact or prove full-cycle peak-to-peak amplitude. Edge-load refinement is required and a restricted-model range is not the published FE benchmark.')
(OUT/'transition_checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('Transition phases complete',report['sampled_range_um'],flush=True)
