"""Reproduce pilot and baseline in their separate output folder.
Usage: python run_pilot_surface_campaign.py; then python analyze_pilot_surface.py
The audit preserves original pre-correction labels from the first development
campaign and recomputes correct geometric classification from cached matrices.
"""
import json
import numpy as np
import pilot_surface_contact as p

PHASES=[.174048546,.224048546,.5,.775951454,.825951454]


def baseline():
    fe=p.fe;fe.configure_24_24();rows=[]
    for phase in PHASES:
        c=fe.contacts(phase,.35,.01,True)
        bodies=[fe.mesh_body(c,i,.25,12,.4,'pilot_baseline',1,'nodal',None,1) for i in [1,2]]
        H=sum(b['H'] for b in bodies);g=np.concatenate([x['gap'] for x in c])
        s=fe.solve_contact(H,g,300000/fe.RB)
        rows.append(dict(phase=phase,approach_um=s['delta']*1000,step_mm=.01,h_mm=.25,
            restricted_nominal_window=any(x['truncated'] for x in c),
            contact_residual_mm=s['gap_residual_mm'],nodes=[b['nodes'] for b in bodies]))
    (p.OUT/'nominal_window_baseline.json').write_text(json.dumps(rows,indent=2))


if __name__=='__main__':
    rows=[]
    for phase in PHASES:
        for step,h in [(.04,.5),(.02,.35),(.01,.25)]:
            rows.append(p.run(phase,step,h))
            (p.OUT/'campaign.json').write_text(json.dumps(rows,indent=2))
    baseline()
