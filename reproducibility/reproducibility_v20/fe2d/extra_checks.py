import json
from run_fe2d import run,OUT
records=[]
for phase in [0,.5]:
    records.append(run(phase,.25,.01,25,.4,geometry_factor=2))
    records.append(run(phase,.25,.01,25,.4,patch=.5))
(OUT/'geometry_patch_checks.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print('Geometry and contact-domain checks complete',flush=True)
