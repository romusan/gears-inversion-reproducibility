"""Noiseless cross-operator inverse checks on an explicit common phase design.

Inverse: moving bilateral geometry, nominal/reference FE elasticity.
Generator: independently remeshed modified geometry and FE elasticity.
No confidence coverage or global optimization certificate is asserted.
"""
import argparse,hashlib,json,sys,time
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'fe2d'))
import cycle_contact_v19 as full
from reduced_cycle_contact_v19 import ReducedOperator as FastOperator

OUT=ROOT/'revision_19_2026-11-01'/'experiments'
SCALE=np.array([.02,.2,.01,.3]);LO=np.array([.005,.55,0.,.15]);HI=np.array([.04,.9,.025,.7])
DH=np.array([.0001,.001,.0001,.001]);SIGMA=.1
EXCLUDED=list(range(24,33))+list(range(88,97))
ANCHORS=[0,10,20,36,44,52,60,68,76,84,100,110]
ELIGIBLE=np.array([i for i in range(120) if i not in EXCLUDED])
INTERIOR=ELIGIBLE[np.linspace(0,len(ELIGIBLE)-1,30,dtype=int)].tolist()
DESIGN=sorted(EXCLUDED+ANCHORS)


def target():
    path=OUT/'cycle_s0.02_h0.35.jsonl'
    rr=[json.loads(s) for s in path.read_text().splitlines() if s.strip()]
    d={int(round(r['phase']*120)):r for r in rr if r['case']=='combined' and r['phase']<1}
    assert len(d)==120,'Complete generating cycle before inversion'
    return np.array([d[i]['approach_um'] for i in range(120)])


def prepare(step):
    op=FastOperator(step,.5,reference=True);theta=full.TRUTH
    op.set_parameters(theta)
    reports=[]
    for phase in [.174048546,.5,.825951454]:
        slow,s=full.Operator.phase(op,phase,tol=.00001)
        fast,t=op.phase(phase,tol=.00001)
        delta=abs(slow['approach_um']-fast['approach_um']);assert delta<.0001
        reports.append(dict(phase=phase,difference_um=delta,fast_iterations=fast['iterations'],damped_iterations=slow['iterations']))
    (OUT/f'fast_iteration_check_s{step:g}.json').write_text(json.dumps(reports,indent=2));return op


class Problem:
    def __init__(self,op,indices,y,restricted=False):
        self.op=op;self.indices=indices;self.phases=np.array(indices)/120;self.y=y[indices]-np.mean(y[indices]);self.restricted=restricted
        self.cache={};self.calls=0;self.forward_records=[];self.errors=[]
    def theta(self,z):
        if self.restricted:return np.array([z[0]*SCALE[0],z[1]*SCALE[1],0.,.5])
        return z*SCALE
    def residual(self,z):
        th=self.theta(z);key=tuple(th)
        if key not in self.cache:
            try:pred,records=self.op.predict(th,self.phases,tol=.00001)
            except Exception as e:
                self.errors.append(dict(theta=th.tolist(),error=repr(e)));raise
            self.calls+=1;self.forward_records.append(dict(theta=th.tolist(),maximum_iterations=max(r['iterations'] for r in records),fallbacks=sum(r.get('damped_fallback',False) for r in records),full_qp_fallbacks=sum(r.get('full_qp_fallback',False) for r in records),maximum_gap_um=max(r['gap_error_um'] for r in records),maximum_penetration_um=max(r['penetration_um'] for r in records),maximum_torque_relative_error=max(r['torque_relative_error'] for r in records),maximum_elastic_relative_error=max(r['elastic_relative_error'] for r in records),maximum_overlap_area_mm2=max(r['overlap_area_mm2'] for r in records)))
            if self.calls%10==0:print('FORWARD',self.op.step,len(self.indices),self.restricted,self.calls,th.tolist(),flush=True)
            self.cache[key]=(pred-pred.mean()-self.y)/SIGMA
        return self.cache[key]
    def jac(self,z):
        base=self.residual(z);J=[]
        for j in range(len(z)):
            h=DH[j]/SCALE[j]
            if z[j]+h>HI[j]/SCALE[j]:h=-h
            zz=z.copy();zz[j]+=h;J.append((self.residual(zz)-base)/h)
        return np.column_stack(J)


def run(step,maxn=25):
    y=target();op=FastOperator(step,.5,reference=True)
    coarse_path=OUT/'inverse_reference_s0.08.json'
    prior=json.loads(coarse_path.read_text()) if coarse_path.exists() else []
    records=[];starts=[np.array([.018,.72,.008,.45]),np.array([.025,.82,.014,.60])]
    for label,indices in [('interior',INTERIOR),('with_transitions',DESIGN)]:
        if step==.04 and prior:
            best=min([r for r in prior if r['design']==label and not r['restricted']],key=lambda r:r['cost'])
            candidates=[np.array(best['theta'])]
        else:candidates=starts
        for restricted in [False,True]:
            use=candidates if not restricted else [candidates[0]]
            for start in use:
                p=Problem(op,indices,y,restricted);z0=start/SCALE
                if restricted:z0=z0[:2]
                t=time.time()
                try:
                    opt=least_squares(p.residual,z0,jac=p.jac,bounds=(LO[:len(z0)]/SCALE[:len(z0)],HI[:len(z0)]/SCALE[:len(z0)]),
                        max_nfev=maxn,ftol=1e-6,xtol=1e-6,gtol=1e-5)
                    theta=p.theta(opt.x);res=p.residual(opt.x)*SIGMA
                    sv=np.linalg.svd(opt.jac,compute_uv=False)
                    r=dict(design=label,indices=indices,restricted=restricted,start=start.tolist(),theta=theta.tolist(),success=bool(opt.success),status=int(opt.status),message=opt.message,
                        cost=float(opt.cost),residual_RMS_um=float(np.sqrt(np.mean(res*res))),nfev=int(opt.nfev),forward_calls=p.calls,
                        scaled_jacobian_singular_values=sv.tolist(),seconds=time.time()-t,
                        scaled_parameter_error=float(np.linalg.norm((theta-full.TRUTH)/SCALE)),
                        forward_records=p.forward_records,errors=p.errors,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
                except Exception as e:r=dict(design=label,indices=indices,restricted=restricted,start=start.tolist(),error=repr(e),forward_calls=p.calls,errors=p.errors,seconds=time.time()-t)
                records.append(r);(OUT/f'inverse_reference_s{step:g}.json').write_text(json.dumps(records,indent=2));print('INVERSE',step,label,restricted,r.get('theta'),r.get('success'),r.get('error'),flush=True)
    # Assess complete-cycle prediction at the selected fits, not fit samples only.
    for label in ['interior','with_transitions']:
        choices=[r for r in records if r['design']==label and not r['restricted'] and 'cost' in r]
        if not choices:continue
        best=min(choices,key=lambda r:r['cost']);pred,diag=op.predict(np.array(best['theta']),np.arange(120)/120,tol=.00001)
        delta=(pred-pred.mean())-(y-y.mean())
        best['full_cycle_prediction_RMS_um']=float(np.sqrt(np.mean(delta*delta)))
        best['full_cycle_prediction_um']=(pred-pred.mean()).tolist()
        best['full_cycle_diagnostics']=diag
        (OUT/f'inverse_reference_s{step:g}.json').write_text(json.dumps(records,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--step',type=float,default=.08);ap.add_argument('--prepare',action='store_true');ap.add_argument('--max-nfev',type=int,default=25)
    a=ap.parse_args();prepare(a.step) if a.prepare else run(a.step,a.max_nfev)
