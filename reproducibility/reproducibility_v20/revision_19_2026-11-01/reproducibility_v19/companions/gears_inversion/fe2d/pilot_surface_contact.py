"""Separate exploratory 24/24 full-contour contact pilot (mm, N, MPa).

Small-strain, plane-strain FE, one-pass node-to-segment contact. Candidate
locations/normals are recomputed on the complete rigid contour at each phase,
including tip segments and vertices. Normals are frozen during each elastic
solve: this is NOT a finite-deformation contact solver. Sharp tips and assumed
quadratic root blends are not certified manufacturing geometry.
"""
import argparse, hashlib, json, time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.spatial import cKDTree
from scipy.sparse.linalg import splu
import run_fe2d as fe

OUT=Path(__file__).resolve().parent/'pilot_surface_2026-11-01'
OUT.mkdir(exist_ok=True)


def cross2(a,b):
    return a[...,0]*b[...,1]-a[...,1]*b[...,0]


def contour(step):
    """Same nominal involute/proportions and quadratic root blend as baseline.
    Refine the complete possible contact zone, not only nominal contact pairs.
    """
    pts=[]; labels=[]; trim=.4
    uf=fe.UF; ua=fe.UA; us=np.sqrt(uf*uf+2*trim/fe.RB)
    bf=fe.HALF+fe.INV-(uf-np.arctan(uf))
    def add(p,label):
        if not pts or np.linalg.norm(p-pts[-1])>1e-10:
            pts.append(np.asarray(p));labels.append(label)
    for tooth in range(fe.Z):
        a0=tooth*2*np.pi/fe.Z
        local_step=step if tooth in [0,1,2,fe.Z-1,fe.Z-2] else .35
        for side,ascending in [(-1,True),(1,False)]:
            af=a0+side*(bf+trim/fe.RF)
            root=fe.RF*np.array([np.cos(af),np.sin(af)])
            p0=root if ascending else fe.point(us,tooth,side)
            p1=fe.point(uf,tooth,side)
            p2=fe.point(us,tooth,side) if ascending else root
            if ascending:
                for t in np.linspace(0,1,12,endpoint=False):
                    add((1-t)**2*p0+2*t*(1-t)*p1+t*t*p2,'root')
            # Arc length of involute is RB/2 (u^2-us^2).
            nn=int(np.ceil(fe.RB*(ua*ua-us*us)/(2*local_step)))+1
            vv=np.sqrt(np.linspace(us*us,ua*ua,nn))
            if not ascending:vv=vv[::-1]
            for u in vv:add(fe.point(u,tooth,side),'flank')
            if not ascending:
                for t in np.linspace(0,1,13)[1:]:
                    add((1-t)**2*p0+2*t*(1-t)*p1+t*t*p2,'root')
            if ascending:
                b=fe.HALF+fe.INV-(ua-np.arctan(ua))
                nt=int(np.ceil(2*fe.RA*b/local_step))+1
                for a in np.linspace(a0-b,a0+b,nt)[1:]:
                    add(fe.RA*np.array([np.cos(a),np.sin(a)]),'tip')
        aa=a0+bf+trim/fe.RF;bb=a0+2*np.pi/fe.Z-bf-trim/fe.RF
        for a in np.linspace(aa,bb,12)[1:-1]:
            add(fe.RF*np.array([np.cos(a),np.sin(a)]),'root')
    xy=np.array(pts)
    assert .5*np.sum(cross2(xy,np.roll(xy,-1,axis=0)))>0
    return xy,np.array(labels)


def make_body(poly,h,near):
    gm=fe.gmsh;gm.initialize();gm.option.setNumber('General.Terminal',0)
    try:
        gm.model.add('surface_pilot');geo=gm.model.geo
        ids=[geo.addPoint(float(x),float(y),0,h if not flag else h/3)
             for (x,y),flag in zip(poly,near)]
        lines=[geo.addLine(ids[i],ids[(i+1)%len(ids)]) for i in range(len(ids))]
        outer=geo.addCurveLoop(lines)
        bi=[geo.addPoint(12*np.cos(a),12*np.sin(a),0,2*h)
            for a in np.linspace(0,2*np.pi,96,endpoint=False)]
        bl=[geo.addLine(bi[i],bi[(i+1)%len(bi)]) for i in range(len(bi))]
        geo.addPlaneSurface([outer,geo.addCurveLoop(bl)]);geo.synchronize()
        gm.option.setNumber('Mesh.MeshSizeExtendFromBoundary',0)
        field=gm.model.mesh.field
        df=field.add('Distance');field.setNumbers(df,'PointsList',[ids[i] for i in np.where(near)[0]])
        tf=field.add('Threshold');field.setNumber(tf,'InField',df)
        for key,value in [('SizeMin',h/3),('SizeMax',3*h),('DistMin',.3),('DistMax',4.)]:
            field.setNumber(tf,key,value)
        field.setAsBackgroundMesh(tf)
        gm.option.setNumber('Mesh.Algorithm',6)
        gm.option.setNumber('Mesh.MeshSizeMax',3*h)
        gm.model.mesh.generate(2)
        tags,xx,_=gm.model.mesh.getNodes();xy=np.array(xx).reshape(-1,3)[:,:2]
        _,en=gm.model.mesh.getElementsByType(2)
        mapping={int(t):i for i,t in enumerate(tags)}
        tri=np.array([mapping[int(t)] for t in en]).reshape(-1,3)
    finally:gm.finalize()
    dist,nodes=cKDTree(xy).query(poly);assert dist.max()<1e-8
    m=fe.MeshTri(xy.T,tri.T);basis=fe.Basis(m,fe.ElementVector(fe.ElementTriP1()))
    lam=fe.E*fe.NU/((1+fe.NU)*(1-2*fe.NU));mu=fe.E/(2*(1+fe.NU))
    K=fe.WIDTH*fe.asm(fe.linear_elasticity(lam,mu),basis)
    fixed=basis.nodal_dofs[:,np.linalg.norm(xy,axis=1)<12+1e-7].ravel()
    free=np.setdiff1d(np.arange(basis.N),fixed)
    return dict(xy=xy,nodes=nodes,basis=basis,K=K,free=free,
                solver=splu(K[free][:,free].tocsc()),elements=len(tri))


def candidates(p1,p2,l1,l2,dmax=.10):
    """One-pass closest projection, including endpoint normal cones.
    Candidate nodes are selected over the entire meshing zone. No LOA window.
    """
    seg=np.roll(p2,-1,axis=0)-p2;ll=np.sum(seg*seg,axis=1)
    normal=np.column_stack([seg[:,1],-seg[:,0]])/np.sqrt(ll)[:,None]
    s1=np.roll(p1,-1,axis=0)-p1
    sn=np.column_stack([s1[:,1],-s1[:,0]])/np.linalg.norm(s1,axis=1)[:,None]
    vn=sn+np.roll(sn,1,axis=0);vn/=np.linalg.norm(vn,axis=1)[:,None]
    nominal=np.array([np.sin(fe.AW),np.cos(fe.AW)])
    rows=[]
    for i in np.where((p1[:,0]>fe.CENTER/2-5)&(abs(p1[:,1])<12)&(vn@nominal>.5))[0]:
        t=np.clip(np.sum((p1[i]-p2)*seg,axis=1)/ll,0,1)
        q=p2+t[:,None]*seg;dist=np.linalg.norm(q-p1[i],axis=1)
        # Ignore the opposite flank: master outward normal opposes loaded side.
        dist[normal@nominal>-.35]=np.inf
        j=int(np.argmin(dist));g=float(dist[j])
        if g>dmax:continue
        endpoint=t[j]<1e-9 or t[j]>1-1e-9
        n=(q[j]-p1[i])/g if endpoint and g>1e-10 else -normal[j]
        # Surface must face the gap. A negative projected gap indicates overlap.
        signed=float((q[j]-p1[i])@(-normal[j]))
        if signed < -1e-8:raise RuntimeError('Initial polygon overlap')
        if n@nominal<.5 or vn[i]@n<.5:continue
        lever=-float(cross2(q[j]-np.array([fe.CENTER,0]),n))
        if lever<=0:continue
        # A segment starting at the tip/flank junction is not itself a tip
        # segment. Classify by BOTH endpoints, avoiding a nodal-label ambiguity.
        radii=np.linalg.norm(p2[[j,(j+1)%len(p2)]]-np.array([fe.CENTER,0]),axis=1)
        tip_segment=bool(np.max(abs(radii-fe.RA))<1e-8)
        vertex=j if t[j]<.5 else (j+1)%len(p2)
        at_tip_vertex=abs(np.linalg.norm(p2[vertex]-np.array([fe.CENTER,0]))-fe.RA)<1e-8
        rows.append(dict(i=int(i),j=j,t=float(t[j]),normal=n,gap=g,
                         lever=lever,corner=bool(endpoint and at_tip_vertex),
                         surface1=str(l1[i]),surface2='tip' if tip_segment else 'flank'))
    if not rows:raise RuntimeError('No candidates')
    return rows


def load_matrix(body,rows,R,which):
    P=np.zeros((body['basis'].N,len(rows)));dofs=body['basis'].nodal_dofs
    for k,c in enumerate(rows):
        n=R.T@c['normal']*(-1 if which==1 else 1)
        points=[(c['i'],1)] if which==1 else [(c['j'],1-c['t']),((c['j']+1)%len(body['nodes']),c['t'])]
        for idx,w in points:P[dofs[:,body['nodes'][idx]],k]+=n*w
    U=np.zeros_like(P);U[body['free']]=body['solver'].solve(P[body['free']])
    return P,U,P.T@U


def solve(H,g,a,torque):
    # Normalize lever arms: sum(a/RB * p)=T/RB. Work conjugate multiplier
    # is RB*angular approach; unlike fixed-normal solve this uses actual torque.
    b=a/fe.RB;F=torque/fe.RB;s=float(np.median(np.diag(H)))
    A=H/s;gg=g/(F*s);q=np.ones(len(g));q/=b@q
    opt=minimize(lambda q:.5*q@A@q+gg@q,q,jac=lambda q:A@q+gg,
        bounds=[(0,None)]*len(g),constraints=[dict(type='eq',fun=lambda q:b@q-1,jac=lambda q:b)],
        method='SLSQP',options=dict(ftol=1e-12,maxiter=1500))
    if not opt.success:raise RuntimeError(opt.message)
    active=opt.x>1e-8
    for _ in range(200):
        idx=np.where(active)[0];v=np.linalg.solve(H[np.ix_(idx,idx)],np.column_stack([b[idx],g[idx]]))
        delta=(F+b[idx]@v[:,1])/(b[idx]@v[:,0]);pp=delta*v[:,0]-v[:,1]
        if pp.min()<-1e-7:active[idx[np.argmin(pp)]]=False;continue
        p=np.zeros(len(g));p[idx]=pp;w=H@p+g-delta*b
        if w[~active].min(initial=0)<-1e-9:active[np.argmin(w)]=True;continue
        return p,delta,w
    raise RuntimeError('Active set did not converge')


def run(phase,step,h):
    start=time.time();fe.configure_24_24()
    p,l=contour(step)
    cc=fe.contacts(phase,.05,.025,allow_clipped=True)
    R1=cc[0]['R1'];R2=cc[0]['R2']
    w1=p@R1.T;w2=p@R2.T+np.array([fe.CENTER,0])
    rows=candidates(w1,w2,l,l)
    nominal_pairs={(c['tooth1'],c['tooth2']) for c in cc}
    tooth=np.rint(np.arctan2(p[:,1],p[:,0])*fe.Z/(2*np.pi)).astype(int)%fe.Z
    extra=np.array([(int(tooth[c['i']]),int(tooth[c['j']])) not in nominal_pairs for c in rows])
    bodies=[];Hs=[];mat=[]
    for which,R,w in [(1,R1,w1),(2,R2,w2)]:
        near=(abs(w[:,0]-fe.CENTER/2)<5)&(abs(w[:,1])<12)
        body=make_body(p,h,near);P,U,H=load_matrix(body,rows,R,which)
        print('body',which,'nodes',len(body['xy']),'candidates',len(rows),flush=True)
        bodies.append(body);Hs.append(H);mat.append((P,U))
    H=sum(Hs);g=np.array([c['gap'] for c in rows]);a=np.array([c['lever'] for c in rows])
    force,delta,res=solve(H,g,a,300000.)
    active=force>1e-5;energy=0.;elastic=[];torques=[];boundary_displacements=[]
    for body,(P,U) in zip(bodies,mat):
        u=U@force;f=P@force;rr=body['K']@u-f
        elastic.append(float(np.linalg.norm(rr[body['free']])/np.linalg.norm(f)))
        energy+=.5*u@(body['K']@u)
        xy=body['basis'].doflocs[:,::2]
        torques.append(float(np.sum(xy[0]*f[1::2]-xy[1]*f[0::2])))
        boundary_displacements.append(u[body['basis'].nodal_dofs[:,body['nodes']]].T)
    # A posteriori re-search on the deformed contours: expose the error from
    # frozen normals and rigid-contact locations instead of asserting it away.
    d1=w1+boundary_displacements[0]@R1.T
    d2=(w2-np.array([fe.CENTER,0]))@fe.rotation(delta/fe.RB).T+np.array([fe.CENTER,0])+boundary_displacements[1]@R2.T
    seg2=np.roll(d2,-1,axis=0)-d2;len2=np.sum(seg2*seg2,axis=1)
    normals2=np.column_stack([seg2[:,1],-seg2[:,0]])/np.sqrt(len2)[:,None]
    true_gaps=[]
    for k in np.where(active)[0]:
        c=rows[k];pt=d1[c['i']]
        t=np.clip(np.sum((pt-d2)*seg2,axis=1)/len2,0,1)
        qq=d2+t[:,None]*seg2;dd=np.linalg.norm(qq-pt,axis=1)
        dd[normals2@c['normal']>-.35]=np.inf
        j=int(np.argmin(dd));true_gaps.append(float((qq[j]-pt)@(-normals2[j])))
    result=dict(phase=phase,step_mm=step,bulk_h_mm=h,approach_um=float(delta*1000),
        candidates=len(rows),active=int(active.sum()),nodes=[len(b['xy']) for b in bodies],
        active_tip_or_corner=int(sum(active[k] and (c['corner'] or c['surface1']=='tip' or c['surface2']=='tip') for k,c in enumerate(rows))),
        torque_relative_residual=float(abs(a@force/300000-1)),body_torques_Nmm=torques,
        complementarity_mm=float(np.max(abs(res[active]))),minimum_gap_residual_mm=float(res.min()),
        elastic_residual_relative=max(elastic),symmetry_relative=float(np.linalg.norm(H-H.T)/np.linalg.norm(H)),
        deformed_research_max_active_gap_um=float(np.max(abs(np.array(true_gaps)))*1000),
        deformed_research_max_active_penetration_um=float(max(0,-min(true_gaps))*1000),
        energy_relative_residual=float(abs((2*energy+g@force)/(delta*300000/fe.RB)-1)),
        active_search_boundary=bool(any(active[k] and c['gap']>.08 for k,c in enumerate(rows))),
        seconds=time.time()-start,
        model='P1 plane strain; nominal full contours; one-pass node-to-segment; phase-dependent normals frozen during elastic solve; sharp tips; assumed root blends; no relief yet')
    edge=np.array([c['corner'] or c['surface1']=='tip' or c['surface2']=='tip' for c in rows])
    result['tip_or_corner_force_fraction']=float(force[edge].sum()/force.sum())
    result['force_fraction_outside_nominal_pairs']=float(force[extra].sum()/force.sum())
    result['normal_deviation_deg_max_active']=float(np.rad2deg(np.max(np.arccos(np.clip(
        np.array([c['normal'] for c in rows])[active]@np.array([np.sin(fe.AW),np.cos(fe.AW)]),-1,1)))))
    # Controlled first-order relief-gap comparison, matching archived u/u_tip law.
    # On a tip segment its addendum value is extended constantly. Geometry,
    # normals and FE stiffness remain nominal: this is not a machined-relief CAD.
    xi=np.clip(np.sqrt(np.maximum((np.linalg.norm(p[[c['i'] for c in rows]],axis=1)/fe.RB)**2-1,0))/fe.UA,0,1)
    add=.020*(np.maximum(xi-.75,0)/.25)**2
    ded=.010*(np.maximum(.5-xi,0)/.5)**2
    variants={}
    for name,relief in [('addendum',add),('combined',add+ded)]:
        pp,dd,ww=solve(H,g+relief,a,300000.)
        aa=pp>1e-5
        variants[name]=dict(approach_um=float(dd*1000),
            tip_or_corner_force_fraction=float(pp[edge].sum()/pp.sum()),
            complementarity_mm=float(np.max(abs(ww[aa]))),
            minimum_gap_residual_mm=float(ww.min()),
            torque_relative_residual=float(abs(a@pp/300000-1)))
        assert variants[name]['complementarity_mm']<1e-8 and ww.min()>-1e-8
    result['relief_gap_variants']=variants
    result['isolated_dedendum_approach_difference_um']=variants['combined']['approach_um']-variants['addendum']['approach_um']
    result['relief_gap_caveat']='First-order pinion gap only, nominal geometry/normals/stiffness; u/u_tip p=2 law, constant addendum continuation over tip segments; not a machined modified-tip model.'
    assert result['torque_relative_residual']<1e-8
    assert result['complementarity_mm']<1e-8 and result['minimum_gap_residual_mm']>-1e-8
    assert result['elastic_residual_relative']<1e-7 and result['energy_relative_residual']<1e-7
    tag=f'phase{phase:.6f}_step{step:g}_h{h:g}'
    np.savez_compressed(OUT/(tag+'.npz'),H=H,gap=g,lever=a,force=force,
        normal=np.array([c['normal'] for c in rows]),edge=edge,extra_nominal_pair=extra,xi_pinion=xi,slave=w1[[c['i'] for c in rows]],
        master=np.array([w2[c['j']]*(1-c['t'])+w2[(c['j']+1)%len(p)]*c['t'] for c in rows]))
    (OUT/(tag+'.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--phase',type=float,default=.5)
    parser.add_argument('--step',type=float,default=.08);parser.add_argument('--h',type=float,default=.7)
    args=parser.parse_args();run(args.phase,args.step,args.h)
