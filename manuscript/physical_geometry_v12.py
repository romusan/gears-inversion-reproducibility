"""Actual material-removal control using harmonic mesh morphing and new FE K.

Hidden pinion relief lies below every candidate contact station. Therefore
loaded coordinates and normals are provably unchanged; the contour, volume,
elastic stiffness and condensed compliance are recalculated. No relief gap
is added. This tests the fixed-compliance hypothesis, not full-cycle recovery.
"""
import sys,json,time,gc
from pathlib import Path
import numpy as np
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent;OUT=ROOT/'revision_12_2026-10-23'
sys.path[:0]=[str(ROOT/'fe2d'),str(ROOT/'deposit_v6/gear_inverse_identifiability/src')]
import run_fe2d as fe
from scipy.spatial import cKDTree
from scipy.sparse.linalg import splu
from skfem import MeshTri,Basis,ElementTriP1,ElementTriP2,ElementVector,asm
from skfem.models.poisson import laplace
from skfem.models.elasticity import linear_elasticity
fe.configure_24_24()
ROOT_TRIM=.1;FACTOR=2;SD=.25
archive=[json.loads(x) for x in (ROOT/'deposit_v6/results/independent_validation/11_fe_cycle_24_24.jsonl').read_text().splitlines()]
interior=sorted({r['phase_fraction'] for r in archive if not r['restricted_nominal_window']})
eligible=[p for p in interior if min(float(np.min(c['v1']/fe.UA)) for c in fe.contacts(p,.35,.02,False))>SD+.001]
PHASES=np.array(eligible)[np.round(np.linspace(0,len(eligible)-1,8)).astype(int)].tolist()
(OUT/'physical_phase_selection.json').write_text(json.dumps(dict(interior_count=len(interior),eligible_count=len(eligible),criterion='All candidate pinion contact coordinates exceed relief start by 0.001',phases=PHASES),indent=2))

def shifted_point(u,tooth,side,depth):
    p=fe.point(u,tooth,side)
    if side!=1 or u/fe.UA>=SD:return p
    angle=np.arctan2(p[1],p[0]);er=np.array([np.cos(angle),np.sin(angle)]);et=np.array([-er[1],er[0]])
    tangent=(er-u*et)/np.sqrt(1+u*u);normal=np.array([tangent[1],-tangent[0]])
    return p+depth*((SD-u/fe.UA)/SD)**2*normal

def contour(contact,depth):
    """The exact polygon used by mesh_body, with changed upper-flank points."""
    pts=[];geometry_vs={};point=lambda u,t,s:shifted_point(u,t,s,depth)
    for index,c in enumerate(contact):
        R=c['R1'];base=R@fe.point(c['u1'],c['tooth1']);tangent=np.array([np.cos(fe.AW),-np.sin(fe.AW)])
        fixed_x=np.linspace(c['x'][0],c['x'][-1],71)
        geometry_vs[index]=np.array([fe.flank_root(lambda u:(R@fe.point(u,c['tooth1'])-base)@tangent-x) for x in fixed_x])
    ustart=np.sqrt(fe.UF**2+2*ROOT_TRIM/fe.RB);beta_f=fe.HALF+fe.INV-(fe.UF-np.arctan(fe.UF))
    for tooth in range(fe.Z):
        for side,ascending in [(-1,True),(1,False)]:
            regular=np.linspace(ustart,fe.UA,18*FACTOR)
            match=next((j for j,c in enumerate(contact) if c['tooth1']==tooth),None)
            vv=geometry_vs[match] if match is not None and side==1 else np.array([])
            u=np.unique(np.r_[regular,vv]);u=u if ascending else u[::-1]
            if ascending:
                a=tooth*2*np.pi/fe.Z-side*(-beta_f-ROOT_TRIM/fe.RF)
                p0=np.array([fe.RF*np.cos(a),fe.RF*np.sin(a)]);p1=point(fe.UF,tooth,side);p2=point(ustart,tooth,side)
                for t in np.linspace(0,1,6*FACTOR+1)[:-1]:pts.append((1-t)**2*p0+2*t*(1-t)*p1+t*t*p2)
            for v in u:pts.append(point(v,tooth,side))
            if not ascending:
                a=tooth*2*np.pi/fe.Z+beta_f+ROOT_TRIM/fe.RF
                p0=point(ustart,tooth,side);p1=point(fe.UF,tooth,side);p2=np.array([fe.RF*np.cos(a),fe.RF*np.sin(a)])
                for t in np.linspace(0,1,6*FACTOR+1)[1:]:pts.append((1-t)**2*p0+2*t*(1-t)*p1+t*t*p2)
            if side==-1:
                beta=fe.HALF+fe.INV-(fe.UA-np.arctan(fe.UA));a0=tooth*2*np.pi/fe.Z
                for a in np.linspace(a0-beta,a0+beta,4*FACTOR+1)[1:-1]:pts.append([fe.RA*np.cos(a),fe.RA*np.sin(a)])
        a0=tooth*2*np.pi/fe.Z+beta_f+ROOT_TRIM/fe.RF;a1=(tooth+1)*2*np.pi/fe.Z-beta_f-ROOT_TRIM/fe.RF
        for a in np.linspace(a0,a1,8*FACTOR+1)[1:-1]:pts.append([fe.RF*np.cos(a),fe.RF*np.sin(a)])
    return np.array(pts)

def morph_field(body,contact):
    nominal=contour(contact,0);changed=contour(contact,.05);following=np.roll(nominal,-1,axis=0)
    boundary=body['mesh'].boundary_nodes();xyz=body['xyz'];displacement=np.zeros_like(xyz)
    outer=boundary[np.linalg.norm(xyz[boundary],axis=1)>13]
    mids=(nominal+following)/2;_,indices=cKDTree(mids).query(xyz[outer],k=64)
    a=nominal[indices];v=following[indices]-a;q=xyz[outer,None,:]
    t=np.clip(np.sum((q-a)*v,axis=2)/np.sum(v*v,axis=2),0,1)
    dist=np.linalg.norm(q-a-t[:,:,None]*v,axis=2);best=np.argmin(dist,axis=1)
    err=dist[np.arange(len(outer)),best];assert err.max()<1e-7,err.max()
    seg=indices[np.arange(len(outer)),best];frac=t[np.arange(len(outer)),best]
    change=changed-nominal;displacement[outer]=(1-frac[:,None])*change[seg]+frac[:,None]*change[(seg+1)%len(nominal)]
    sb=Basis(body['mesh'],ElementTriP1());L=asm(laplace,sb)
    free=np.setdiff1d(np.arange(len(xyz)),boundary)
    displacement[free]=splu(L[free][:,free].tocsc()).solve(-(L[free][:,boundary]@displacement[boundary]))
    return displacement,float(err.max())

def areas(xyz,tri):
    a=xyz[tri[:,1]]-xyz[tri[:,0]];b=xyz[tri[:,2]]-xyz[tri[:,0]]
    return (a[:,0]*b[:,1]-a[:,1]*b[:,0])/2

def morphed_H(body,field,factor):
    xyz=body['xyz']+factor*field;oldareas=areas(body['xyz'],body['tri']);newareas=areas(xyz,body['tri'])
    ratio=newareas/oldareas;assert ratio.min()>0,'Inverted element'
    mesh=MeshTri(xyz.T,body['tri'].T);basis=Basis(mesh,ElementVector(ElementTriP2()))
    assert basis.N==body['basis'].N
    lam=fe.E*fe.NU/((1+fe.NU)*(1-2*fe.NU));mu=fe.E/(2*(1+fe.NU))
    K=fe.WIDTH*asm(linear_elasticity(lam,mu),basis);free=np.setdiff1d(np.arange(basis.N),body['D'])
    P=body['P'];U=splu(K[free][:,free].tocsc()).solve(P[free]);H=P[free].T@U
    symmetry=np.linalg.norm(H-H.T)/np.linalg.norm(H);assert symmetry<1e-9
    removed=float(np.abs(oldareas).sum()-np.abs(newareas).sum());assert removed>0
    return (H+H.T)/2,dict(removed_area_mm2=removed,min_element_area_ratio=float(ratio.min()),symmetry=float(symmetry))

def weak_gaps(c):
    gaps=[]
    for cc in c:
        x=cc['x'];M=np.zeros((len(x),len(x)))
        for j,d in enumerate(np.diff(x)):M[j:j+2,j:j+2]+=d*np.array([[2,1],[1,2]])/6
        gaps.extend((M@cc['gap'])/M.sum(axis=1))
    return np.array(gaps)

def main():
    dest=OUT/'physical_geometry_verified_records.jsonl';records=[]
    if dest.exists():records=[json.loads(x) for x in dest.read_text().splitlines()]
    done={(r['h_mm'],r['phase_fraction']) for r in records if r['depth_mm']==.05}
    with dest.open('a',encoding='utf-8') as file:
        for h in [.5,.35,.25]:
            for phase in PHASES:
                if (h,phase) in done:continue
                t=time.time();c=fe.contacts(phase,.35,.02,False)
                candidate_min=min(np.min(cc['v1']/fe.UA) for cc in c)
                assert candidate_min>SD,'The proposed hidden relief reaches candidate contact'
                wheel=fe.mesh_body(c,2,h,12.,ROOT_TRIM,f'physical12_w_{h}_{phase}',FACTOR,'weak_hat',.02,2)
                H2=wheel['H'].copy();del wheel;gc.collect()
                pinion=fe.mesh_body(c,1,h,12.,ROOT_TRIM,f'physical12_p_{h}_{phase}',FACTOR,'weak_hat',.02,2)
                field,err=morph_field(pinion,c);g=weak_gaps(c);F=300000/fe.RB
                H0=pinion['H'];base=fe.solve_contact(H0+H2,g,F)
                for depth in [0.,.01,.05]:
                    H,geometry=(H0,{}) if depth==0 else morphed_H(pinion,field,depth/.05)
                    sol=base if depth==0 else fe.solve_contact(H+H2,g,F)
                    row=dict(h_mm=h,phase_fraction=phase,depth_mm=depth,relief_start=SD,root_trim_mm=ROOT_TRIM,
                             geometry_factor=FACTOR,degree=2,step_mm=.02,local_h_mm=.02,
                             candidate_min_xi=float(candidate_min),added_gap_mm=0.,boundary_projection_error_mm=err,
                             H_relative_change=float(np.linalg.norm(H-H0)/np.linalg.norm(H0)),
                             approach_um=1000*sol['delta'],incremental_stiffness_N_um=sol['k_N_um'],
                             approach_change_um=1000*(sol['delta']-base['delta']),
                             force_residual_N=sol['force_residual_N'],contact_residual_mm=sol['gap_residual_mm'],
                             nodes=pinion['nodes'],seconds=time.time()-t,**geometry)
                    file.write(json.dumps(row)+'\n');file.flush();records.append(row)
                print('physical',h,phase,'seconds',round(time.time()-t,1),flush=True)
                del pinion;gc.collect()
    summary=[]
    for h in [.5,.35,.25]:
        for depth in [.01,.05]:
            rr=sorted([r for r in records if r['h_mm']==h and r['depth_mm']==depth],key=lambda r:r['phase_fraction'])
            assert len(rr)==8
            d=np.array([r['approach_change_um'] for r in rr]);centered=d-d.mean()
            summary.append(dict(h_mm=h,depth_mm=depth,centered_TE_difference_rms_um=float(np.sqrt(np.mean(centered**2))),
                                mean_approach_change_um=float(d.mean()),max_H_relative_change=max(r['H_relative_change'] for r in rr),
                                removed_area_mm2=rr[0]['removed_area_mm2'],centered_differences_um=centered.tolist()))
    (OUT/'physical_geometry_summary.json').write_text(json.dumps(dict(scope='Actual boundary-fitted hidden upper-flank/root-blend relief; P2 weak contact; harmonic boundary-fitted mesh morphing; eight common interior phases; zero added gap',phases=PHASES,rows=summary),indent=2))
    print(summary,flush=True)
if __name__=='__main__':main()

