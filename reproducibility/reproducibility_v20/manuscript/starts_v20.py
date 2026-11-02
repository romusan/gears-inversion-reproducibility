"""Additional fixed-start checks at the unchanged 0.04 mm inverse reference.
V19 files and numerical operators remain immutable. No random noise is added.
"""
import argparse,json,hashlib,time
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from inverse_moving_v19 import Problem,FastOperator,target,ROOT,SCALE,LO,HI,INTERIOR,DESIGN,SIGMA,full
OUT=ROOT/'revision_20_2026-11-01'/'experiments';OUT.mkdir(parents=True,exist_ok=True)
STARTS=[np.array(x) for x in [[.018,.72,.008,.45],[.025,.82,.014,.60],[.012,.60,.003,.20],[.032,.86,.020,.65]]]

def main(design):
    source=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();path=OUT/f'starts_{design}.json'
    records=json.loads(path.read_text()) if path.exists() else []
    assert all(r['source_sha256']==source for r in records)
    y=target();idx=INTERIOR if design=='interior' else DESIGN;op=FastOperator(.04,.5,reference=True)
    prior=json.loads((ROOT/'revision_19_2026-11-01/experiments/inverse_reference_s0.04.json').read_text())
    selected=min([r for r in prior if r['design']==design and not r['restricted']],key=lambda r:r['cost'])
    attempts=[(False,i,s) for i,s in enumerate(STARTS)]+[(True,4,np.array(selected['theta'])),(True,5,STARTS[1])]
    for restricted,i,start in attempts:
        if any(r['attempt_id']==i for r in records):continue
        p=Problem(op,idx,y,restricted);z=start/SCALE
        if restricted:z=z[:2]
        t=time.time();r=dict(attempt_id=i,design=design,restricted=restricted,start=start.tolist(),source_sha256=source)
        try:
            fit=least_squares(p.residual,z,jac=p.jac,bounds=(LO[:len(z)]/SCALE[:len(z)],HI[:len(z)]/SCALE[:len(z)]),max_nfev=25,ftol=1e-6,xtol=1e-6,gtol=1e-5)
            theta=p.theta(fit.x);r.update(theta=theta.tolist(),success=bool(fit.success),status=int(fit.status),message=fit.message,cost=float(fit.cost),nfev=int(fit.nfev),residual_RMS_um=float(np.sqrt(np.mean(fit.fun**2)))*SIGMA,scaled_jacobian_singular_values=np.linalg.svd(fit.jac,compute_uv=False).tolist())
            if not restricted:
                pred,diag=op.predict(theta,np.arange(120)/120,tol=.00001);r['prediction_um']=pred.tolist();r['prediction_diagnostics']=diag
                train_delta=pred[idx]-pred[idx].mean()-(y[idx]-y[idx].mean())
                r['fresh_training_RMS_um']=float(np.sqrt(np.mean(train_delta**2)))
                assert abs(r['fresh_training_RMS_um']-r['residual_RMS_um'])<.0002
        except Exception as e:r.update(error=repr(e))
        r.update(seconds=time.time()-t,forward_calls=p.calls,forward_records=p.forward_records,errors=p.errors)
        records.append(r);path.write_text(json.dumps(records,indent=2));print('DONE',design,i,restricted,r.get('theta'),r.get('success'),r.get('error'),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('design',choices=['interior','with_transitions']);main(ap.parse_args().design)
