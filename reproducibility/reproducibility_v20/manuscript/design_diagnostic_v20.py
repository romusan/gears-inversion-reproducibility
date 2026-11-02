"""Declared local diagnostics, separating nuisance projection and discrepancy.
Finite-difference tangents are descriptive and not physical uncertainty bounds.
"""
import json,time,hashlib
from pathlib import Path
import numpy as np
from inverse_moving_v19 import ROOT,FastOperator,INTERIOR,DESIGN,SCALE,DH,SIGMA,full,target
OUT=ROOT/'revision_20_2026-11-01/experiments';OUT.mkdir(parents=True,exist_ok=True)
def rms(x):return float(np.sqrt(np.mean(np.asarray(x)**2)))
def project(A,B):return B-A@np.linalg.lstsq(A,B,rcond=1e-12)[0]

def main():
    op=FastOperator(.04,.5,reference=True);theta=full.TRUTH;phases=np.arange(120)/120;raw=OUT/'local_forward_v20.json'
    runs=json.loads(raw.read_text()) if raw.exists() else []
    def predict(th):
        saved=next((r for r in runs if r['theta']==list(th)),None)
        if saved:return np.array(saved['prediction_um'])
        pred,diag=op.predict(np.array(th),phases,tol=.00001)
        runs.append(dict(theta=list(th),prediction_um=pred.tolist(),diagnostics=diag));raw.write_text(json.dumps(runs,indent=2));print('TANGENT',len(runs),list(th),flush=True);return pred
    base=predict(theta);y=target();results=[]
    for factor in [1.,.5]:
        J=[]
        for j in range(4):
            h=DH[j]*factor;tp=theta.copy();tm=theta.copy();tp[j]+=h;tm[j]-=h
            J.append((predict(tp)-predict(tm))/(2*h)*SCALE[j]/SIGMA)
        J=np.column_stack(J)
        for label,idx in [('interior',INTERIOR),('with_transitions',DESIGN)]:
            jj=J[idx];delta=(base-y)[idx]/SIGMA
            for offset in [True,False]:
                A=np.column_stack([jj[:,:2],np.ones(len(idx))]) if offset else jj[:,:2]
                D=project(A,jj[:,2:]);e=project(A,delta);sv=np.linalg.svd(D,compute_uv=False);bias=np.linalg.lstsq(D,-e,rcond=1e-12)[0]
                gram=D.T@D;sign,ldet=np.linalg.slogdet(gram)
                results.append(dict(design=label,step_factor=factor,offset_estimated=offset,projected_dedendum_singular_values=sv.tolist(),logdet_dedendum_information=float(ldet) if sign>0 else None,linear_scaled_dedendum_bias=bias.tolist(),linear_dedendum_point=(theta[2:]+SCALE[2:]*bias).tolist(),projected_discrepancy_RMS_um=rms(e)*SIGMA,linear_residual_RMS_um=rms(e+D@bias)*SIGMA,addendum_tangent_fraction=float(np.linalg.norm(jj[:,:2])**2/np.linalg.norm(jj)**2)))
        np.savez_compressed(OUT/f'local_tangent_factor{factor:g}.npz',J_scaled_whitened=J,theta=theta,DH=DH*factor,SCALE=SCALE,SIGMA=SIGMA,reference_prediction_um=base,target_um=y)
    # Exact full-geometry generator contrasts on each observation design.
    rr=[json.loads(x) for x in (ROOT/'revision_19_2026-11-01/experiments/cycle_s0.02_h0.35.jsonl').read_text().splitlines()]
    curves={case:np.array([r['approach_um'] for r in sorted(rr,key=lambda r:r['phase']) if r['case']==case and r['phase']<1]) for case in ['nominal','addendum','combined']}
    contrasts=[]
    for label,idx in [('interior',INTERIOR),('with_transitions',DESIGN)]:
        for case,A,B in [('addendum',curves['addendum'],curves['nominal']),('dedendum',curves['combined'],curves['addendum'])]:
            d=A-B;contrasts.append(dict(design=label,component=case,design_centered_RMS_um=rms(d[idx]-np.mean(d[idx])),global_centered_subset_RMS_um=rms((d-d.mean())[idx]),mean_raw_difference_um=float(np.mean(d[idx]))))
    out=dict(results=results,generator_contrasts=contrasts,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Local central tangents at known truth, two finite-difference steps, unchanged nominal FE elasticity; no noisy refitting or coverage calibration.')
    (OUT/'design_diagnostic_v20.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
