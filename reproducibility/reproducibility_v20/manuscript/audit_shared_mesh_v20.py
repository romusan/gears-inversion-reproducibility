"""Reconstruct sampled 2D compliance columns from the exported CCX mesh.
This verifies transfer/mesh equivalence, independently of CCX contact results.
"""
import json,sys,hashlib
from pathlib import Path
import numpy as np
from scipy.sparse.linalg import splu
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'fe2d'))
import cycle_contact_v19 as c
OUT=ROOT/'revision_20_2026-11-01';FOLDER=OUT/'calculix_cycle_crosscheck'
def read_mesh(path):
    nodes=[];elements=[];mode=None
    for s in path.read_text().splitlines():
        if s.startswith('*'):
            key=s.upper().split(',')[0];mode='node' if key=='*NODE' else ('element' if key=='*ELEMENT' else None);continue
        if not mode or not s.strip():continue
        q=s.split(',')
        if mode=='node':nodes.append(list(map(float,q[1:4])))
        else:elements.append(list(map(int,q[1:7])))
    return np.array(nodes),np.array(elements)
def main():
    c.fe.configure_24_24();results=[];wheel_done=False
    for meta_path in sorted(FOLDER.glob('f0.225*_input.json')):
        m=json.loads(meta_path.read_text());stem=meta_path.name.replace('_input.json','');path=FOLDER/(stem+'.inp');xyz,elem=read_mesh(path);bound=json.loads((FOLDER/(stem+'_boundary.json')).read_text());offset=0;eo=0;R=c.pose(.225)
        for k in [0,1]:
            n=m['mesh'][k]['nodes_2d'];nt=m['mesh'][k]['triangles']
            if k==1 and wheel_done:offset+=2*n;eo+=nt;continue
            th=np.array(m['theta']);tag=('profile_'+hashlib.sha256(th.tobytes()).hexdigest()[:12]) if k==0 else 'nominal';tag+=f"_s{m['step']:g}_h{m['h']:g}"
            z=np.load(ROOT/'revision_19_2026-11-01/experiments/body_cache'/(tag+'.npz'));C=z['C'];idx=z['indices'];poly=z['poly']
            world=xyz[offset:offset+n,:2];center=np.array([0 if k==0 else c.fe.CENTER,0]);xy=(world-center)@R[k];tri=elem[eo:eo+nt,:3]-offset-1
            mesh=c.fe.MeshTri(xy.T,tri.T);basis=c.fe.Basis(mesh,c.fe.ElementVector(c.fe.ElementTriP1()));lam=c.fe.E*c.fe.NU/((1+c.fe.NU)*(1-2*c.fe.NU));mu=c.fe.E/(2*(1+c.fe.NU));K=c.fe.WIDTH*c.fe.asm(c.fe.linear_elasticity(lam,mu),basis)
            fixed=basis.nodal_dofs[:,np.linalg.norm(xy,axis=1)<12+1e-7].ravel();free=np.setdiff1d(np.arange(basis.N),fixed);lookup=np.full(basis.N,-1);lookup[free]=np.arange(len(free))
            boundary_ids=np.array(bound[k]['bottom_ids'])-offset-1
            contour_error=float(np.max(abs(xy[boundary_ids]-poly)));assert contour_error<1e-8
            dofs=basis.nodal_dofs[:,boundary_ids[idx]].T.ravel();cols=np.unique(np.linspace(0,len(dofs)-1,8,dtype=int));rhs=np.zeros((len(free),len(cols)));rhs[lookup[dofs[cols]],np.arange(len(cols))]=1
            solution=splu(K[free][:,free].tocsc()).solve(rhs);computed=solution[lookup[dofs]];reference=C[:,cols];relative=float(np.max(abs(computed-reference))/np.max(abs(reference)));assert relative<1e-6,(tag,relative)
            results.append(dict(tag=tag,nodes=n,triangles=nt,sampled_columns=cols.tolist(),contour_coordinate_error_mm=contour_error,compliance_column_relative_error=relative,input_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
            if k==1:wheel_done=True
            offset+=2*n;eo+=nt;del C
    assert len(results)==3
    (OUT/'audit_shared_mesh_v20.json').write_text(json.dumps(dict(results=results,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2));print(results)
if __name__=='__main__':main()
