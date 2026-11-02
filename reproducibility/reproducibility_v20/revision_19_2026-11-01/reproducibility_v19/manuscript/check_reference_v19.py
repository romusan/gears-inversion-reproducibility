"""Archive at-truth predictions independently of the inverse search."""
import json,sys,time
import numpy as np
from inverse_moving_v19 import OUT,FastOperator,full

for step in [.08,.04]:
    path=OUT/f'reference_truth_s{step:g}.json'
    if path.exists():continue
    t=time.time();op=FastOperator(step,.5,reference=True)
    y,rr=op.predict(full.TRUTH,np.arange(120)/120,tol=.00001)
    path.write_text(json.dumps(dict(step=step,theta=full.TRUTH.tolist(),prediction_um=y.tolist(),diagnostics=rr,seconds=time.time()-t),indent=2))
    print('REFERENCE TRUTH',step,time.time()-t,flush=True)
