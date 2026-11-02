"""Repeat paired entry contrasts with a full initial load fraction.
The final torque and model are unchanged; slow interrupted runs are retained.
A same-grid pair controls sensitivity to this continuation change.
"""
import json,hashlib
from pathlib import Path
from crosscheck_relief_fast_v20 import make_deck,execute,OUT
rows=[]
for step,h in [(.02,.35),(.01,.25)]:
    for case in ['addendum','combined']:
        receipt=OUT/(f'fast_mortar_{step:g}_{case}_receipt.json')
        if receipt.exists():rows.append(json.loads(receipt.read_text()));continue
        path=make_deck(.174048546,.00084,step,h,1e9,True,True,case)
        try:r=execute(path)
        except Exception as e:r=dict(error=repr(e),normal_termination=False)
        r.update(case=case,phase=.174048546,step=step,h=h,method='mortar',initial_increment=1.0,input=path.name,runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        receipt.write_text(json.dumps(r,indent=2));rows.append(r);print(r,flush=True)
(OUT/'campaign_fast_v20.json').write_text(json.dumps(rows,indent=2))
