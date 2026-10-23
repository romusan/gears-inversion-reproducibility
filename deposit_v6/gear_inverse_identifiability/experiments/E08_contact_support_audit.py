"""Check the invisibility condition for G2 nominal relief on sampled loads."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from E08_generalization import build_te,GEOMETRIES
from campaign_provenance import provenance

def main():
    geom=next(g for g in GEOMETRIES if g[0]=='G2-coarse')
    te=build_te(geom);rows=[]
    u_tip=np.sqrt((te.pair.g1.ra/te.pair.g1.rb)**2-1)
    for torque in [50,100,300]:
        zero=te.compute_cycle(torque,60,np.array([.02,.75,0,.30]))
        changed=te.compute_cycle(torque,60,np.array([.02,.75,.05,.30]))
        active=[];margins=[];max_support_force=0.
        for state,p,w in zip(zero['states'],zero['forces'],zero['separations']):
            xi=state['u1']/u_tip
            active.extend(xi[p>1e-6].tolist())
            if np.any(xi<.30):
                margins.extend(w[xi<.30].tolist())
                max_support_force=max(max_support_force,float(np.max(p[xi<.30])))
        row=dict(torque_Nm=torque,n_positions=60,min_loaded_xi=min(active),
                 support_end=.30,min_support_separation_mm=min(margins),
                 max_support_force_N=max_support_force,
                 max_response_change_mm=float(np.max(np.abs(zero['TE_lin_fluct']-changed['TE_lin_fluct']))))
        assert row['min_support_separation_mm']>0 and row['max_support_force_N']==0
        rows.append(row);print(row,flush=True)
    path=Path(__file__).resolve().parents[1]/'results'/'corrections_2026-10-12'/'E08_contact_support.json'
    path.write_text(json.dumps(dict(provenance=provenance(),geometry=geom,records=rows,
        limitation='Certificate for the stated discrete observations in a gap-only microgeometry model; no physical stiffness-change sensitivity is represented.'),indent=2),encoding='utf-8')

if __name__=='__main__':main()
