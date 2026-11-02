"""Interior paired check after the entry pair releases its solver directory."""
import time,json,hashlib
from pathlib import Path
from crosscheck_cycle_v20 import OUT,make_deck,execute
while not (OUT/'campaign_v20.json').exists():time.sleep(5)
rows=[]
for case in ['addendum','combined']:
    path=make_deck(.5,.00079,.02,.35,1e9,True,True,case)
    try:r=execute(path)
    except Exception as e:r=dict(error=repr(e),normal_termination=False)
    r.update(case=case,phase=.5,step=.02,h=.35,method='mortar',input=path.name,runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (OUT/('interior_'+case+'_receipt.json')).write_text(json.dumps(r,indent=2));rows.append(r)
(OUT/'campaign_interior_v20.json').write_text(json.dumps(rows,indent=2))
