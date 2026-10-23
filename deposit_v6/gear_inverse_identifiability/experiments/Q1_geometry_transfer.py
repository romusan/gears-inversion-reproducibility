"""Ideal involute portability with no undercut case; standardized bounds."""
import json
import numpy as np
from Q1_identifiability_campaign import OUT,InvoluteGear,GearPair,GearContactModel,TipRelief,BatchedGapOperator,fit,predict,provenance

def main():
    rows=[]
    for name,z1,z2,m,b in [('G0',24,48,3.,20.),('G1',20,60,2.5,15.),('G2',30,45,4.,25.),('G3',18,64,2.,12.)]:
        pair=GearPair(InvoluteGear(z1,m,20,b),InvoluteGear(z2,m,20,b));model=GearContactModel(pair,TipRelief())
        for sd in [.25,.4]:
            theta=np.array([.02*m/3,.75,.005*m/3,sd])
            for design in [[(300,120)],[(50,60),(300,60)]]:
                ops=[BatchedGapOperator(model,T,n) for T,n in design]
                # Normalize depths to m=3 for reuse of the declared bounds:
                # here use actual physical depths, safely contained in global
                # bounds, and retain the same bounds across all geometries.
                y=predict(ops,theta)
                starts=[np.array([.03,.65,.01,.35]),np.array([.015,.85,.02,.45])]
                fits=[fit(ops,y,.0001,start) for start in starts];result=min(fits,key=lambda r:r['chi2'])
                rows.append(dict(geometry=name,z1=z1,z2=z2,module_mm=m,width_mm=b,alpha_deg=20.,
                                 theoretical_min_teeth=2/np.sin(np.deg2rad(20))**2,
                                 contact_ratio=float(pair.eps_alpha),sd_true=sd,torques_Nm=[T for T,n in design],
                                 theta_true=theta.tolist(),**result))
                print(name,sd,rows[-1]['torques_Nm'],result['fit_rmse_um'],flush=True)
    (OUT/'geometry_transfer.json').write_text(json.dumps(dict(provenance=provenance(),bounds_note='Common physical bounds, Ca<=0.100 mm Cd<=0.050 mm; relief truth depths scaled with module.',records=rows),indent=2),encoding='utf-8')
if __name__=='__main__':main()
