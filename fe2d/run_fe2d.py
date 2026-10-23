"""Exploratory 2D gear continuum and frictionless condensed nodal contact.

No analytical beam or Hertz compliance is imported. Geometry and hub support
are idealizations, explicitly independent of the unavailable reference CAD.
Units: mm, N, MPa. Contact forces are total forces over the 23 mm width.
"""
import argparse,json,sys,time,hashlib
from pathlib import Path
# Permit the existing scientific runtime to load only the three new FE packages
# from this isolated environment; no global package installation is required.
sys.path.append(str(Path(__file__).resolve().parent/'.venv/Lib/site-packages'))
import numpy as np
import gmsh,meshio
from scipy.sparse.linalg import splu
from scipy.spatial import cKDTree
from scipy.optimize import minimize,brentq
from skfem import MeshTri,Basis,ElementVector,ElementTriP1,ElementTriP2,asm
from skfem.models.elasticity import linear_elasticity
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parent/'results';OUT.mkdir(exist_ok=True)
Z=57;MODULE=2.6;RP=Z*MODULE/2;RB=RP*np.cos(np.deg2rad(20))
RF=141.70/2;RA=154.50/2;WIDTH=23.;E=210000.;NU=.3;CENTER=150.
AW=np.arccos(2*RB/CENTER);PB=np.pi*MODULE*np.cos(np.deg2rad(20))
UF=np.sqrt((RF/RB)**2-1);UA=np.sqrt((RA/RB)**2-1)
INV=np.tan(np.deg2rad(20))-np.deg2rad(20);HALF=3.78/(2*RP)

def configure_24_24():
    """Symmetric 24/24 pair, module 3 mm (same module and pressure angle as
    the nominal study) for the observable-dedendum FE validation (phase 11).
    Standard proportions: addendum 1m, dedendum 1.25m, thickness pi*m/2."""
    global Z,MODULE,RP,RB,RF,RA,WIDTH,E,NU,CENTER,AW,PB,UF,UA,INV,HALF
    Z=24;MODULE=3.;RP=Z*MODULE/2;RB=RP*np.cos(np.deg2rad(20))
    RF=RP-1.25*MODULE;RA=RP+MODULE;WIDTH=20.;E=210000.;NU=.3;CENTER=2*RP
    AW=np.arccos(2*RB/CENTER);PB=np.pi*MODULE*np.cos(np.deg2rad(20))
    # Standard dedendum puts the root circle at or below the base circle;
    # the involute flank then starts at the base circle itself (UF=0).
    UF=0.0 if RF<=RB else float(np.sqrt((RF/RB)**2-1));UA=float(np.sqrt((RA/RB)**2-1))
    INV=np.tan(np.deg2rad(20))-np.deg2rad(20);HALF=np.pi/(2*Z)

def point(u,tooth=0,side=1):
    r=RB*np.sqrt(1+u*u);beta=HALF+INV-(u-np.arctan(u))
    angle=tooth*2*np.pi/Z+side*beta
    return np.array([r*np.cos(angle),r*np.sin(angle)])

def inward(u,tooth=0):
    # Analytical derivative of upper involute flank, expressed in local body axes.
    eps=1e-6;t=point(u+eps,tooth)-point(u-eps,tooth);t/=np.linalg.norm(t)
    return np.array([t[1],-t[0]])

def rotation(angle):
    return np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])

def flank_root(function):
    """Preserve exact flank endpoints despite station roundoff at clipped tips."""
    if abs(function(UF))<=1e-11:return UF
    if abs(function(UA))<=1e-11:return UA
    return brentq(function,UF,UA)

def contacts(fraction,patch,step,allow_clipped=False):
    span=np.sqrt(RA*RA-RB*RB)-RB*np.tan(AW)
    s=fraction*PB+np.arange(-2,2)*PB
    s=s[np.abs(s)<span-1e-7]
    us1=(RB*np.tan(AW)+s)/RB;us2=(RB*np.tan(AW)-s)/RB
    n=int(np.ceil(patch/step));full_xs=np.linspace(-patch,patch,2*n+1)
    result=[]
    for j,(u1,u2) in enumerate(zip(us1,us2)):
        ss=float(s[j]);normal=np.array([np.sin(AW),np.cos(AW)])
        tangent=np.array([np.cos(AW),-np.sin(AW)])
        centerpoint=np.array([CENTER/2,0])+ss*normal
        # Neighbouring mating teeth run in opposite index order.
        t1=j;t2=(-j)%Z
        angle1=np.arctan2(centerpoint[1],centerpoint[0])-np.arctan2(point(u1,t1)[1],point(u1,t1)[0])
        q2=centerpoint-np.array([CENTER,0])
        angle2=np.arctan2(q2[1],q2[0])-np.arctan2(point(u2,t2)[1],point(u2,t2)[0])
        R1=rotation(angle1);R2=rotation(angle2)
        assert np.linalg.norm(R1@inward(u1,t1)+normal)<1e-7
        assert np.linalg.norm(R2@inward(u2,t2)-normal)<1e-7
        def station(u,R,tooth,center):return (R@point(u,tooth)+center-centerpoint)@tangent
        ends1=sorted([station(v,R1,t1,np.zeros(2)) for v in [UF,UA]])
        ends2=sorted([station(v,R2,t2,np.array([CENTER,0])) for v in [UF,UA]])
        lower=max(-patch,ends1[0],ends2[0]);upper=min(patch,ends1[1],ends2[1])
        truncated=lower>-patch+1e-9 or upper<patch-1e-9
        if truncated and not allow_clipped:raise ValueError('Patch reaches a tooth edge; allow_clipped is a restricted transition model, not corner-contact validation.')
        xs=np.unique(np.r_[lower,full_xs[(full_xs>lower+1e-10)&(full_xs<upper-1e-10)],upper])
        v1=np.array([flank_root(lambda u:station(u,R1,t1,np.zeros(2))-x) for x in xs])
        v2=np.array([flank_root(lambda u:station(u,R2,t2,np.array([CENTER,0]))-x) for x in xs])
        if not allow_clipped and (min(v1.min(),v2.min())<=UF or max(v1.max(),v2.max())>=UA):
            raise ValueError('Contact patch intersects a root blend or tip; use interior phases.')
        Q1=np.array([R1@point(v,t1) for v in v1]);Q2=np.array([R2@point(v,t2)+np.array([CENTER,0]) for v in v2])
        gap=(Q2-Q1)@normal
        assert gap.min()>-1e-10
        result.append(dict(tooth1=t1,tooth2=t2,u1=u1,u2=u2,v1=v1,v2=v2,x=xs,
            gap=np.maximum(gap,0),normal1=inward(u1,t1),normal2=inward(u2,t2),R1=R1,R2=R2,truncated=truncated))
    # The same rigid rotation must place every contacting tooth of one gear.
    assert all(np.linalg.norm(c['R1']-result[0]['R1'])<1e-10 and np.linalg.norm(c['R2']-result[0]['R2'])<1e-10 for c in result)
    return result

def mesh_body(contact,which,h,bore,root_trim,tag,geometry_factor=1,traction='nodal',local_h=None,degree=1):
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
    gmsh.model.add(tag);geo=gmsh.model.geo
    pts=[];patch_points=[]
    geometry_vs={}
    if traction=='weak_hat':
        # Fixed geometric boundary vertices independent of pressure spacing.
        for index,c in enumerate(contact):
            R=c['R'+str(which)];center=np.array([0 if which==1 else CENTER,0])
            base=R@point(c['u'+str(which)],c['tooth'+str(which)])+center
            tangent=np.array([np.cos(AW),-np.sin(AW)])
            fixed_x=np.linspace(c['x'][0],c['x'][-1],71)
            geometry_vs[index]=np.array([flank_root(lambda u:(R@point(u,c['tooth'+str(which)])+center-base)@tangent-x) for x in fixed_x])
    # Sharp root or quadratic tangent-like blend, controlled by trim length.
    ustart=np.sqrt(UF*UF+2*root_trim/RB) if root_trim else UF
    beta_f=HALF+INV-(UF-np.arctan(UF))
    for tooth in range(Z):
        for side,ascending in [(-1,True),(1,False)]:
            regular=np.linspace(ustart,UA,18*geometry_factor)
            match_index=next((j for j,c in enumerate(contact) if c['tooth'+str(which)]==tooth),None)
            matching=contact[match_index] if match_index is not None else None
            vv=(geometry_vs[match_index] if traction=='weak_hat' else matching['v'+str(which)]) if matching is not None and side==1 else np.array([])
            u=np.unique(np.r_[regular,vv]);u=u if ascending else u[::-1]
            if root_trim and ascending:
                a=tooth*2*np.pi/Z-side*(-beta_f-root_trim/RF)
                p0=np.array([RF*np.cos(a),RF*np.sin(a)])
                p1=point(UF,tooth,side);p2=point(ustart,tooth,side)
                for t in np.linspace(0,1,6*geometry_factor+1)[:-1]:pts.append((1-t)**2*p0+2*t*(1-t)*p1+t*t*p2)
            for v in u:pts.append(point(v,tooth,side))
            if root_trim and not ascending:
                a=tooth*2*np.pi/Z+beta_f+root_trim/RF
                p0=point(ustart,tooth,side);p1=point(UF,tooth,side)
                p2=np.array([RF*np.cos(a),RF*np.sin(a)])
                for t in np.linspace(0,1,6*geometry_factor+1)[1:]:pts.append((1-t)**2*p0+2*t*(1-t)*p1+t*t*p2)
            if side==-1:
                b=HALF+INV-(UA-np.arctan(UA));a0=tooth*2*np.pi/Z
                for a in np.linspace(a0-b,a0+b,4*geometry_factor+1)[1:-1]:pts.append([RA*np.cos(a),RA*np.sin(a)])
        a0=tooth*2*np.pi/Z+beta_f+root_trim/RF
        a1=(tooth+1)*2*np.pi/Z-beta_f-root_trim/RF
        for a in np.linspace(a0,a1,8*geometry_factor+1)[1:-1]:pts.append([RF*np.cos(a),RF*np.sin(a)])
    pts=np.array(pts)
    # Exact interface coordinates appear as boundary vertices; small surrounding
    # triangles resolve local contact deformation without a Hertz spring.
    targets=np.vstack([np.array([point(v,c['tooth'+str(which)]) for v in c['v'+str(which)]]) for c in contact])
    geometry_targets=np.vstack([np.array([point(v,c['tooth'+str(which)]) for v in geometry_vs[j]]) for j,c in enumerate(contact)]) if traction=='weak_hat' else targets
    kd=cKDTree(geometry_targets);distance=kd.query(pts)[0]
    contact_spacing=min(float(np.median(np.diff(c['x']))) for c in contact)
    contact_mesh_size=contact_spacing if local_h is None else local_h
    sizes=np.where(distance<.8,np.minimum(h,contact_mesh_size),h)
    ids=[geo.addPoint(x,y,0,float(size)) for (x,y),size in zip(pts,sizes)]
    lines=[geo.addLine(ids[i],ids[(i+1)%len(ids)]) for i in range(len(ids))]
    outer=geo.addCurveLoop(lines)
    innerids=[geo.addPoint(bore*np.cos(a),bore*np.sin(a),0,2.0) for a in np.linspace(0,2*np.pi,96,endpoint=False)]
    innerlines=[geo.addLine(innerids[i],innerids[(i+1)%96]) for i in range(96)]
    inner=geo.addCurveLoop(innerlines);geo.addPlaneSurface([outer,inner]);geo.synchronize()
    # Explicit grading prevents the contact size from spreading through the
    # entire disk; both near-contact and root/bulk resolution are controlled.
    field=gmsh.model.mesh.field
    contact_ids=[ids[i] for i in np.where(distance<1e-8)[0]]
    df=field.add('Distance');field.setNumbers(df,'PointsList',contact_ids)
    tf=field.add('Threshold');field.setNumber(tf,'InField',df)
    for name,value in [('SizeMin',contact_mesh_size),('SizeMax',4*h),('DistMin',.1),('DistMax',1.2)]:field.setNumber(tf,name,value)
    db=field.add('Distance');field.setNumbers(db,'PointsList',ids)
    tb=field.add('Threshold');field.setNumber(tb,'InField',db)
    for name,value in [('SizeMin',h),('SizeMax',4*h),('DistMin',.5),('DistMax',4.)]:field.setNumber(tb,name,value)
    mf=field.add('Min');field.setNumbers(mf,'FieldsList',[tf,tb]);field.setAsBackgroundMesh(mf)
    gmsh.option.setNumber('Mesh.MeshSizeExtendFromBoundary',0)
    gmsh.option.setNumber('Mesh.Algorithm',6)
    gmsh.option.setNumber('Mesh.MeshSizeMax',4*h)
    gmsh.option.setNumber('Mesh.MeshSizeMin',min(h,contact_mesh_size,.01))
    gmsh.model.mesh.generate(2)
    tags,xyz,_=gmsh.model.mesh.getNodes();xyz=np.array(xyz).reshape(-1,3)[:,:2]
    eltags,enodes=gmsh.model.mesh.getElementsByType(2)
    order={int(t):i for i,t in enumerate(tags)}
    tri=np.array([order[int(t)] for t in enodes]).reshape(-1,3)
    gmsh.finalize()
    boundarynodes=cKDTree(xyz);dist,node=boundarynodes.query(targets)
    if traction=='nodal' and dist.max()>1e-7:raise RuntimeError('Contact vertex missing in mesh')
    m=MeshTri(xyz.T,tri.T)
    basis=Basis(m,ElementVector(ElementTriP1() if degree==1 else ElementTriP2()))
    lam=E*NU/((1+NU)*(1-2*NU));mu=E/(2*(1+NU))
    K=WIDTH*asm(linear_elasticity(lam,mu),basis)
    fixednodes=np.where(np.linalg.norm(xyz,axis=1)<bore+1e-6)[0]
    D=basis.nodal_dofs[:,fixednodes].ravel()
    if degree==2:
        bore_facets=np.all(np.isin(m.facets,fixednodes),axis=0)
        D=np.r_[D,basis.facet_dofs[:,bore_facets].ravel()]
    free=np.setdiff1d(np.arange(basis.N),D)
    P=np.zeros((basis.N,len(node)));offset=0
    for c in contact:
        n=len(c['x']);norm=c['normal'+str(which)]
        for j,ind in enumerate(node[offset:offset+n]):P[basis.nodal_dofs[:,ind],offset+j]=norm
        offset+=n
    if traction=='weak_hat':
        # Consistent normalized pressure hats: integrate against the actual
        # piecewise-linear FE boundary trace rather than apply point forces.
        P[:]=0;offset=0;boundary=m.boundary_nodes()
        facet_map={tuple(sorted(v)):j for j,v in enumerate(m.facets.T)} if degree==2 else {}
        for c in contact:
            angle=c['tooth'+str(which)]*2*np.pi/Z
            local=xyz[boundary]@rotation(-angle).T
            radius=np.linalg.norm(local,axis=1);u=np.sqrt(np.maximum((radius/RB)**2-1,0))
            beta=HALF+INV-(u-np.arctan(u))
            angular=np.arctan2(local[:,1],local[:,0])
            mask=(u>=ustart-1e-8)&(u<=UA+1e-8)&(abs(angular-beta)<5e-5)
            bn=boundary[mask]
            R=c['R'+str(which)];world=xyz[bn]@R.T
            center=np.array([0 if which==1 else CENTER,0]);world+=center
            base=R@point(c['u'+str(which)],c['tooth'+str(which)])+center
            tangent=np.array([np.cos(AW),-np.sin(AW)])
            xx=(world-base)@tangent;order=np.argsort(xx);xx=xx[order];bn=bn[order]
            stations=c['x'];norm=c['normal'+str(which)]
            assert xx[0]<=stations[0]+1e-7 and xx[-1]>=stations[-1]-1e-7
            for j,xj in enumerate(stations):
                left=stations[max(j-1,0)];right=stations[min(j+1,len(stations)-1)]
                area=(right-left)/2
                cuts=np.unique(np.r_[left,xj,right,xx[(xx>left)&(xx<right)]])
                for lo,hi in zip(cuts[:-1],cuts[1:]):
                    if hi-lo<1e-12:continue
                    centerq=(hi+lo)/2;half=(hi-lo)/2
                    for xi,quadweight in zip([-np.sqrt(3/5),0,np.sqrt(3/5)],[5/9,8/9,5/9]):
                        q=centerq+half*xi
                        hat=(q-left)/(xj-left) if q<xj and xj>left else (right-q)/(right-xj) if right>xj else 0
                        k=np.clip(np.searchsorted(xx,q)-1,0,len(xx)-2);ratio=(q-xx[k])/(xx[k+1]-xx[k])
                        if degree==1:
                            for nn,weight in [(bn[k],1-ratio),(bn[k+1],ratio)]:P[basis.nodal_dofs[:,nn],offset+j]+=norm*weight*hat*half*quadweight/area
                        else:
                            for nn,weight in [(bn[k],(1-ratio)*(1-2*ratio)),(bn[k+1],ratio*(2*ratio-1))]:P[basis.nodal_dofs[:,nn],offset+j]+=norm*weight*hat*half*quadweight/area
                            facet=facet_map[tuple(sorted([bn[k],bn[k+1]]))]
                            P[basis.facet_dofs[:,facet],offset+j]+=norm*4*ratio*(1-ratio)*hat*half*quadweight/area
            offset+=len(stations)
        assert np.max(abs(np.linalg.norm(np.vstack([P[0::2].sum(axis=0),P[1::2].sum(axis=0)]),axis=0)-1))<1e-8
    solver=splu(K[free][:,free].tocsc());U=np.zeros_like(P);U[free]=solver.solve(P[free])
    H=P.T@U
    sym=float(np.linalg.norm(H-H.T)/np.linalg.norm(H))
    assert sym<1e-9
    return dict(mesh=m,xyz=xyz,tri=tri,basis=basis,K=K,P=P,U=U,H=(H+H.T)/2,D=D,
        nodes=len(xyz),elements=len(tri),symmetry=sym)

def solve_contact(H,g,F,initial=None):
    # Convex potential energy, nonnegative nodal normal forces and force budget.
    scale=float(np.median(np.diag(H)));A=H/scale;b=g/(F*scale)
    n=len(g);q=np.ones(n)/n if initial is None else initial/F
    opt=minimize(lambda q:.5*q@A@q+b@q,q,jac=lambda q:A@q+b,
        bounds=[(0,None)]*n,constraints=[{'type':'eq','fun':lambda q:q.sum()-1,'jac':lambda q:np.ones(n)}],
        method='SLSQP',options={'ftol':1e-12,'maxiter':1000})
    if not opt.success:raise RuntimeError(opt.message)
    p=np.maximum(opt.x,0)*F;act=p>F*1e-8
    # Polish contact multipliers on the selected active set.
    for it in range(100):
        i=np.where(act)[0];v=np.linalg.solve(H[np.ix_(i,i)],np.column_stack([np.ones(len(i)),g[i]]))
        delta=(F+v[:,1].sum())/v[:,0].sum();pp=delta*v[:,0]-v[:,1]
        if pp.min()<-1e-7:act[i[np.argmin(pp)]]=False;continue
        p=np.zeros(n);p[i]=pp;w=H@p+g-delta
        if w[~act].min(initial=0)<-1e-10:act[np.argmin(w)]=True;continue
        break
    else:raise RuntimeError('Active-set polishing failed')
    stiffness=float(v[:,0].sum())/1000
    assert p.min()>-1e-7 and abs(p.sum()-F)<1e-6 and w.min()>-1e-9
    return dict(p=p,delta=delta,k_N_um=stiffness,active=act,gap_residual_mm=float(max(abs(w[act]).max(initial=0),-w.min())),
        force_residual_N=float(abs(p.sum()-F)),optimizer_iterations=int(opt.nit))

def run(fraction,h,step,bore,root_trim,patch=.35,save=False,geometry_factor=1,allow_clipped=False,traction='nodal',local_h=None,degree=1):
    c=contacts(fraction,patch,step,allow_clipped);tag=f'f{fraction:g}_h{h:g}_d{step:g}_b{bore:g}_r{root_trim:g}_exactgap'
    if allow_clipped:tag+='_transition'
    if geometry_factor!=1:tag+=f'_geom{geometry_factor}'
    if patch!=.35:tag+=f'_patch{patch:g}'
    if traction!='nodal':tag+='_'+traction
    if local_h is not None:tag+=f'_local{local_h:g}'
    if degree!=1:tag+=f'_P{degree}'
    start=time.time();bodies=[]
    for i in [1,2]:
        print('Meshing and factoring',tag,'body',i,flush=True)
        bodies.append(mesh_body(c,i,h,bore,root_trim,tag+str(i),geometry_factor,traction,local_h,degree))
        print('Body ready',i,bodies[-1]['nodes'],'nodes',flush=True)
    H=sum(b['H'] for b in bodies);gap=np.concatenate([x['gap'] for x in c]);F=650000/RB
    if traction=='weak_hat':
        averaged=[]
        for cc in c:
            x=cc['x'];g=cc['gap'];M=np.zeros((len(x),len(x)))
            for j,d in enumerate(np.diff(x)):
                M[j:j+2,j:j+2]+=d*np.array([[2,1],[1,2]])/6
            averaged.extend((M@g)/M.sum(axis=1))
        gap=np.array(averaged)
    sol=solve_contact(H,gap,F)
    # Independent finite perturbation verifies the tangent including pressure redistribution.
    low=solve_contact(H,gap,F*.999,sol['p']);high=solve_contact(H,gap,F*1.001,sol['p'])
    kfd=(.002*F)/(1000*(high['delta']-low['delta']))
    off=0;loads=[];edge=False;tooth_edge_load=False
    for cc in c:
        pp=sol['p'][off:off+len(cc['x'])];active=pp>F*1e-8
        loads.append(float(pp.sum()))
        if cc['truncated']:tooth_edge_load|=bool(active[0] or active[-1])
        else:edge|=bool(active[0] or active[-1])
        off+=len(pp)
    assert not edge,'Increase contact patch extent'
    residuals=[];energies=[];moments=[]
    for body in bodies:
        u=body['U']@sol['p'];rhs=body['P']@sol['p'];res=body['K']@u-rhs
        free=np.setdiff1d(np.arange(body['basis'].N),body['D']);residuals.append(float(np.linalg.norm(res[free])/np.linalg.norm(rhs)))
        energies.append(float(.5*u@(body['K']@u)))
        # Quadratic edge DOFs carry forces too; use all vector-DOF coordinates.
        ux=np.arange(0,body['basis'].N,2);uy=ux+1
        loc=body['basis'].doflocs[:,ux]
        moments.append(float(np.sum(loc[0]*rhs[uy]-loc[1]*rhs[ux])))
        if save:
            disp=u[body['basis'].nodal_dofs].T
            R=c[0]['R'+str(len(energies))];center=np.array([0 if len(energies)==1 else CENTER,0])
            world=body['xyz']@R.T+center;worlddisp=disp@R.T
            meshio.write(OUT/(tag+f'_body{len(energies)}.vtu'),meshio.Mesh(np.c_[world,np.zeros(body['nodes'])],[('triangle',body['tri'])],point_data={'displacement_mm':np.c_[worlddisp,np.zeros(body['nodes'])]}))
    record=dict(phase_fraction=fraction,nominal_pairs=len(c),mesh_h_mm=h,contact_step_mm=step,
        bore_radius_mm=bore,root_trim_mm=root_trim,patch_halfwidth_mm=patch,geometry_factor=geometry_factor,
        traction_discretization=traction,local_contact_mesh_mm=local_h,element_degree=degree,
        restricted_nominal_window=allow_clipped,tooth_edge_loaded=tooth_edge_load,
        clipped_contact_domains=[bool(cc['truncated']) for cc in c],
        nodes=[b['nodes'] for b in bodies],elements=[b['elements'] for b in bodies],
        approach_um=float(sol['delta']*1000),k_incremental_N_um=sol['k_N_um'],k_fd_N_um=float(kfd),
        tangent_relative_difference=float(abs(kfd/sol['k_N_um']-1)),k_secant_N_um=float(F/(1000*sol['delta'])),
        pair_forces_N=loads,normal_force_N=float(F),force_residual_N=sol['force_residual_N'],
        contact_residual_mm=sol['gap_residual_mm'],elastic_residual_relative=max(residuals),
        strain_energy_N_mm=sum(energies),body_torques_Nmm=moments,
        torque_relative_error=max(abs(abs(v)/650000-1) for v in moments),seconds=time.time()-start)
    np.savez_compressed(OUT/(tag+'_contact.npz'),H_mm_N=H,gap_mm=gap,p_N=sol['p'],x_mm=np.concatenate([x['x'] for x in c]))
    (OUT/(tag+'.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps(record),flush=True)
    if save:
        body=bodies[0];u=body['U']@sol['p'];mag=np.linalg.norm(u[body['basis'].nodal_dofs],axis=0)*1000
        fig,axes=plt.subplots(1,2,figsize=(11,4.7));axes[0].tripcolor(body['xyz'][:,0],body['xyz'][:,1],body['tri'],mag,shading='gouraud');axes[0].set_aspect('equal');axes[0].set_title('Plane strain displacement magnitude (µm)');axes[0].set_xlim(65,79);axes[0].set_ylim(-9,16)
        off=0
        for i,cc in enumerate(c):
            pp=sol['p'][off:off+len(cc['x'])];dx=cc['x'][1]-cc['x'][0]
            axes[1].plot(cc['x'],pp/(WIDTH*dx),label=f'Pair {i+1}');off+=len(pp)
        axes[1].set_xlabel('Tangent coordinate (mm)');axes[1].set_ylabel('Nodal equivalent pressure (MPa)');axes[1].legend();axes[1].grid(alpha=.25)
        fig.suptitle(f'Exploratory FE 2D, 650 Nm, phase {fraction:g}');fig.tight_layout();fig.savefig(OUT/(tag+'.png'),dpi=160);plt.close(fig)
    return record

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--phase',type=float,default=0);p.add_argument('--h',type=float,default=.5);p.add_argument('--step',type=float,default=.02);p.add_argument('--bore',type=float,default=25);p.add_argument('--root-trim',type=float,default=.4);p.add_argument('--patch',type=float,default=.35);p.add_argument('--geometry-factor',type=int,default=1);p.add_argument('--save',action='store_true');p.add_argument('--allow-clipped',action='store_true');a=p.parse_args()
    run(a.phase,a.h,a.step,a.bore,a.root_trim,a.patch,a.save,a.geometry_factor,a.allow_clipped)
