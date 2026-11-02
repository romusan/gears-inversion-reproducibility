"""Fast analytical control on the same 30-observation designs and bounds."""
import json,sys
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from inverse_moving_v19 import ROOT,OUT,SCALE,LO,HI,INTERIOR,DESIGN,SIGMA,target
SRC=ROOT/'deposit_v6/gear_inverse_identifiability/src';sys.path.insert(0,str(SRC))
from geometry.involute import InvoluteGear,GearPair
from geometry.microgeometry import TipRelief
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator


def main():
    y=target();pair=GearPair(InvoluteGear(24,3,20,20),InvoluteGear(24,3,20,20));model=GearContactModel(pair,micro1=TipRelief(p=2.),micro2=None,compliance_variant='projected-energy')
    output=[]
    for design,idx in [('interior',INTERIOR),('with_transitions',DESIGN)]:
        op=BatchedGapOperator(model,300.,phi_positions=np.array(idx)*2*np.pi/(24*120));data=y[idx]-y[idx].mean()
        def residual(z,restricted=False):
            theta=np.r_[z*SCALE[:2],0.,.5] if restricted else z*SCALE
            p=op.evaluate(theta)['prediction']*1000
            return (p-p.mean()-data)/SIGMA
        def jac(z):return op.evaluate(z*SCALE,jacobian=True)['jacobian']*1000*SCALE[None,:]/SIGMA
        for restricted in [False,True]:
            for start in [np.array([.018,.72,.008,.45]),np.array([.025,.82,.014,.60])]:
                n=2 if restricted else 4
                r=least_squares(lambda z:residual(z,restricted),start[:n]/SCALE[:n],jac='2-point' if restricted else jac,
                    bounds=(LO[:n]/SCALE[:n],HI[:n]/SCALE[:n]),max_nfev=600,ftol=1e-10,xtol=1e-10,gtol=1e-9)
                theta=np.r_[r.x*SCALE[:2],0.,.5] if restricted else r.x*SCALE
                full=BatchedGapOperator(model,300.,phi_positions=np.arange(120)*2*np.pi/(24*120)).evaluate(theta)['prediction']*1000
                output.append(dict(operator='projected-energy fixed-normal',design=design,indices=idx,restricted=restricted,start=start.tolist(),theta=theta.tolist(),success=bool(r.success),cost=float(r.cost),residual_RMS_um=float(np.sqrt(np.mean(r.fun*r.fun)))*SIGMA,
                    full_cycle_prediction_RMS_um=float(np.sqrt(np.mean((full-full.mean()-(y-y.mean()))**2))),full_cycle_prediction_um=(full-full.mean()).tolist(),nfev=int(r.nfev)))
    (OUT/'inverse_analytic.json').write_text(json.dumps(output,indent=2));print('Analytical common-design fits',len(output))


if __name__=='__main__':main()
