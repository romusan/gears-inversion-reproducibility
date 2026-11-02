"""Reproject saved solutions and recompute equilibrium, energy and FE residual.
This is a saved-state audit of the implemented model, not another solver.
"""
import sys,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'fe2d'))
import reduced_cycle_contact_v19 as c
from contact_reduced_qp_v19 import sparse_matvec
from shapely.geometry import Polygon
OUT=ROOT/'revision_19_2026-11-01';EXP=OUT/'experiments'

def main():
    results=[]
    for step,h in [(.04,.5),(.02,.35)]:
        rr=[json.loads(x) for x in (EXP/f'cycle_s{step:g}_h{h:g}.jsonl').read_text().splitlines()]
        c.fe.configure_24_24()
        b2=np.load(EXP/'body_cache'/f'nominal_s{step:g}_h{h:g}.npz');C2=b2['C'];poly2=b2['poly'];idx2=b2['indices']
        for case in ['nominal','addendum','combined']:
            ss=[r for r in rr if r['case']==case];tag=ss[0]['body_tags'][0]
            b1=np.load(EXP/'body_cache'/(tag+'.npz'));C1=C2 if case=='nominal' else b1['C'];poly1=b1['poly'];idx1=b1['indices'];c.mc.N1,c.mc.N2=len(poly1),len(poly2)
            for r in ss:
                z=np.load(EXP/'cycle_states'/r['state_file']);u=[z['u1'],z['u2']];angle=float(z['angle']);R1,R2=c.pose(r['phase'])
                x,y,Q2=c.mc.geometry([poly1,poly2],[idx1,idx2],u,R1,R2,angle)
                rows=c.mc.contacts(x,y,two_pass=True);forces={(bool(d),int(i)):float(p) for d,i,p in zip(z['directions'],z['slave_indices'],z['force'])}
                keys={(a['reverse'],a['i']) for a in rows};assert all(k in keys or p<1e-5 for k,p in forces.items())
                f=np.array([forces.get((a['reverse'],a['i']),0.) for a in rows]);active=f>1e-5
                P=[c.mc.load_map(rows,idx1,R1,1),c.mc.load_map(rows,idx2,Q2,2)];loads=[p@f for p in P]
                residual=max(float(np.linalg.norm(v-sparse_matvec(C,l))/max(np.linalg.norm(v),1e-15)) for v,C,l in zip(u,[C1,C2],loads))
                torque=sum(-c.mc.old.cross2(a['point2']-[c.fe.CENTER,0],a['normal'])*p for a,p in zip(rows,f))
                force_balance=np.linalg.norm(R1@loads[0].reshape(-1,2).sum(0)+Q2@loads[1].reshape(-1,2).sum(0))/max(f.sum(),1)
                gaps=np.array([a['gap'] for a in rows])*1000;overlap=Polygon(x).intersection(Polygon(y)).area
                energy=float(sum(.5*v@l for v,l in zip(u,loads)))
                a=dict(step=step,case=case,phase=r['phase'],minimum_gap_um=float(gaps.min()),active_gap_um=float(max(abs(gaps[active]))),torque_relative_error=float(abs(torque/300000-1)),force_balance_relative=float(force_balance),elastic_relative_error=residual,strain_energy_Nmm=energy,overlap_area_mm2=float(overlap))
                assert a['minimum_gap_um']>-.001 and a['active_gap_um']<.001 and a['torque_relative_error']<2e-6 and residual<2e-5 and force_balance<1e-10 and energy>0 and overlap<1e-8,a
                results.append(a)
            print('AUDITED',step,case,len(results),flush=True)
            del C1
        del C2
    assert len(results)==726
    (OUT/'audit_cycle_v19.json').write_text(json.dumps(dict(states=726,results=results,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2))
if __name__=='__main__':main()
