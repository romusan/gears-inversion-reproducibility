"""Paired actual-profile contrasts; common initial rotation for each pair."""
import json,hashlib
from pathlib import Path
from crosscheck_relief_v20 import make_deck,execute,OUT

def main():
    rows=[]
    for method,step,h in [('mortar',.02,.35),('mortar',.01,.25),('penalty',.02,.35)]:
        for case in ['addendum','combined']:
            key=f'{method}_{step:g}_{case}';receipt=OUT/(key+'_receipt.json')
            if receipt.exists():rows.append(json.loads(receipt.read_text()));continue
            path=make_deck(.174048546,.00084,step,h,1e9,True,method=='mortar',case)
            try:r=execute(path)
            except Exception as e:r=dict(error=repr(e),normal_termination=False)
            r.update(case=case,step=step,h=h,method=method,input=path.name,runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
            receipt.write_text(json.dumps(r,indent=2));rows.append(r);print(key,r,flush=True)
    (OUT/'campaign_v20.json').write_text(json.dumps(rows,indent=2))
if __name__=='__main__':main()
