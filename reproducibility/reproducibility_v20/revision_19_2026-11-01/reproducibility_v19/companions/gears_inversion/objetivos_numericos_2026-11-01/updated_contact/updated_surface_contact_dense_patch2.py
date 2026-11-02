"""Exploratory moving-projection contact with condensed linear elastic bodies.

Finite rigid hub rotation + small-strain body elasticity. External relaxed
projection iteration, NOT a consistent-tangent Newton/mortar implementation.
No evidence is promoted to the manuscript until geometric residuals pass.
"""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
import pilot_surface_contact as old

OUT=Path(__file__).resolve().parents[1]/'objetivos_numericos_2026-11-01'/'updated_contact'
OUT.mkdir(parents=True,exist_ok=True)
fe=old.fe


def search(x,y,dmax=.1,normal_sign=1):
    e=np.roll(y,-1,axis=0)-y;l2=np.sum(e*e,axis=1)
    nm=np.column_stack([e[:,1],-e[:,0]])/np.sqrt(l2)[:,None]
    es=np.roll(x,-1,axis=0)-x
    ns=np.column_stack([es[:,1],-es[:,0]])/np.linalg.norm(es,axis=1)[:,None]
    ns+=np.roll(ns,1,axis=0);ns/=np.linalg.norm(ns,axis=1)[:,None]
    normal=normal_sign*np.array([np.sin(fe.AW),np.cos(fe.AW)]);rows=[]
    # Exact broad-phase rejection: a segment outside the expanded slave search
    # box cannot be within dmax. Preserve original segment indices for assembly.
    end=np.roll(y,-1,axis=0)
    lo=np.minimum(y,end);hi=np.maximum(y,end)
    keep=(nm@normal<=-.3)&(lo[:,0]<fe.CENTER/2+5+dmax)&(hi[:,0]>fe.CENTER/2-5-dmax)&(lo[:,1]<12+dmax)&(hi[:,1]>-12-dmax)
    ids=np.where(keep)[0];ym=y[ids];em=e[ids];lm=l2[ids];nmm=nm[ids]
    for i in np.where((abs(x[:,0]-fe.CENTER/2)<5)&(abs(x[:,1])<12)&(ns@normal>.45))[0]:
        t=np.clip(np.sum((x[i]-ym)*em,axis=1)/lm,0,1)
        q=ym+t[:,None]*em;dist=np.linalg.norm(q-x[i],axis=1)
        k=int(np.argmin(dist));j=int(ids[k])
        if dist[k]>dmax:continue
        n=-nmm[k];g=float((q[k]-x[i])@n)
        if (t[k]<1e-9 or t[k]>1-1e-9) and g>1e-10:
            n=(q[k]-x[i])/dist[k];g=float(dist[k])
        if n@normal<.4 or ns[i]@n<.4:continue
        rows.append(dict(i=int(i),j=j,t=float(t[k]),normal=n,gap=g,q=q[k]))
    if not rows:raise RuntimeError('No contact candidates')
    return rows


def contacts(x,y,reverse=False,dmax=.1):
    rows=search(y,x,dmax,-1) if reverse else search(x,y,dmax)
    for c in rows:
        c['reverse']=reverse
        if reverse:c['normal']=-c['normal'];c['point2']=y[c['i']]
        else:c['point2']=c['q']
    return rows


def condense(poly,indices,h,near,cache):
    if cache.exists():
        z=np.load(cache)
        assert np.array_equal(z['indices'],indices)
        return z['C'],dict(nodes=int(z['nodes']),elements=int(z['elements']),cached=True)
    body=old.make_body(poly,h,near);dofs=body['basis'].nodal_dofs[:,body['nodes'][indices]].T.ravel()
    C=np.zeros((len(dofs),len(dofs)));lookup=np.full(body['basis'].N,-1,dtype=int)
    lookup[body['free']]=np.arange(len(body['free']))
    assert np.all(lookup[dofs]>=0)
    for start in range(0,len(dofs),48):
        dd=dofs[start:start+48];rhs=np.zeros((len(body['free']),len(dd)))
        rhs[lookup[dd],np.arange(len(dd))]=1
        u=body['solver'].solve(rhs);C[:,start:start+len(dd)]=u[lookup[dofs]]
    symmetry=float(np.linalg.norm(C-C.T)/np.linalg.norm(C));assert symmetry<1e-9
    C=(C+C.T)/2
    np.savez_compressed(cache,C=C,indices=indices,nodes=len(body['xy']),elements=body['elements'])
    return C,dict(nodes=len(body['xy']),elements=body['elements'],symmetry=symmetry,cached=False)


def load_map(rows,indices,R,which):
    lookup={int(v):i for i,v in enumerate(indices)}
    P=np.zeros((2*len(indices),len(rows)))
    for k,c in enumerate(rows):
        slave=which==(2 if c.get('reverse',False) else 1)
        master_count=N1 if c.get('reverse',False) else N2
        points=[(c['i'],1.)] if slave else [(c['j'],1-c['t']),((c['j']+1)%master_count,c['t'])]
        n=R.T@c['normal']*(-1 if which==1 else 1)
        for j,w in points:
            if j not in lookup:raise RuntimeError('Candidate escaped condensed patch: enlarge initial search')
            P[2*lookup[j]:2*lookup[j]+2,k]+=w*n
    return P


def geometry(polys,indices,displacements,R1,R2,theta):
    u1=np.zeros_like(polys[0]);u2=np.zeros_like(polys[1])
    u1[indices[0]]=displacements[0].reshape(-1,2)
    u2[indices[1]]=displacements[1].reshape(-1,2)
    Q2=R2@fe.rotation(theta)
    return (polys[0]+u1)@R1.T,(polys[1]+u2)@Q2.T+[fe.CENTER,0],Q2


def solve_qp(H,g,a,torque):
    """Feasible active-set convex QP; allows zero/negative radial lever arms."""
    b=a/fe.RB;F=torque/fe.RB;s=float(np.median(np.diag(H)))
    A=H/s;c=g/(F*s)
    n=len(g);r=np.zeros(n);positive=np.where(b>.1)[0]
    first=positive[np.argmin(c[positive]/b[positive]+.5*np.diag(A)[positive]/b[positive]**2)]
    r[first]=1/b[first];active=r>0
    for _ in range(4*n+100):
        idx=np.where(active)[0];m=len(idx)
        K=np.zeros((m+1,m+1));K[:m,:m]=A[np.ix_(idx,idx)];K[:m,m]=-b[idx];K[m,:m]=b[idx]
        z=np.linalg.solve(K,np.r_[-c[idx],1]);star=z[:m]
        if star.min()<-1e-12:
            direction=star-r[idx];mask=direction<-1e-14
            alpha=min(1,float(np.min(-r[idx][mask]/direction[mask])))
            r[idx]+=alpha*direction;r[abs(r)<1e-13]=0;active=r>0
            continue
        r[:]=0;r[idx]=np.maximum(star,0);r/=b@r
        grad=A@r+c-z[-1]*b;grad[active]=np.inf
        if grad.min(initial=0)<-1e-10:
            active[np.argmin(grad)]=True;continue
        force=F*r;delta=F*s*z[-1];res=H@force+g-delta*b
        assert res.min()>-1e-8 and abs(a@force/torque-1)<1e-9
        return force,delta,res
    raise RuntimeError('Feasible active-set QP failed')


def run(phase,step=.04,h=.5,torques=(60.,150.,300.),relax=.45,maxiter=80,tol_um=.001,case='nominal',reverse=False):
    global N1,N2
    fe.configure_24_24();start=time.time();poly,labels=old.contour(step)
    theta_relief={'nominal':None,'addendum':(.020,.75,0.,.50),'combined':(.020,.75,.010,.50)}[case]
    if theta_relief is None:polys=[poly,poly]
    else:
        from relieved_surface_geometry import contour as relieved
        polys=[relieved(step,theta_relief),poly]
    N1,N2=map(len,polys)
    cc=fe.contacts(phase,.05,.025,True);R1=cc[0]['R1'];R2=cc[0]['R2']
    x0=polys[0]@R1.T;y0=polys[1]@R2.T+[fe.CENTER,0]
    # Include nearby nodes even if their initial normal fails the facing test.
    # Under deformation a previously excluded vertex can become a candidate.
    # Nearest-vertex radius includes half the largest opposite segment length.
    indices=[]
    from scipy.spatial import cKDTree
    for x,y in [(x0,y0),(y0,x0)]:
        radius=.5+.5*np.max(np.linalg.norm(np.roll(y,-1,axis=0)-y,axis=1))
        close=cKDTree(y).query(x)[0]<radius
        box=(abs(x[:,0]-fe.CENTER/2)<5+radius)&(abs(x[:,1])<12+radius)
        indices.append(np.where(close&box)[0])
    # Include neighboring vertices needed for updated segment normals.
    indices=[np.unique(np.concatenate([(i+o)%n for o in [-2,-1,0,1,2]])) for i,n in zip(indices,[N1,N2])]
    tag=f'f{phase:.9f}_s{step:g}_h{h:g}'
    if case!='nominal':tag+='_'+case
    if reverse:tag+='_reverse'
    tag+='_patch2'
    C=[];mesh=[]
    for k,w in enumerate([x0,y0]):
        near=(abs(w[:,0]-fe.CENTER/2)<5)&(abs(w[:,1])<12)
        c,m=condense(polys[k],indices[k],h,near,OUT/(tag+f'_body{k+1}.npz'));C.append(c);mesh.append(m)
        print('condensed',k+1,len(indices[k]),m,flush=True)
    u=[np.zeros(len(c)) for c in C];theta=0.;history=[];stages=[]
    for torque in torques:
        converged=False
        for it in range(maxiter):
            x,y,Q2=geometry(polys,indices,u,R1,R2,theta);rows=contacts(x,y,reverse)
            P=[load_map(rows,indices[0],R1,1),load_map(rows,indices[1],Q2,2)]
            H=sum(b.T@c@b for b,c in zip(P,C));H=(H+H.T)/2
            a=np.array([-old.cross2(c['point2']-[fe.CENTER,0],c['normal']) for c in rows])
            gc=np.array([c['gap'] for c in rows]);elastic_gap=sum(b.T@v for b,v in zip(P,u))
            g=gc-elastic_gap+a*theta
            force,delta,res=solve_qp(H,g,a,torque*1000.)
            newu=[c@b@force for c,b in zip(C,P)];newtheta=delta/fe.RB
            # Verify on the newly deformed surfaces, not merely linearized gaps.
            xx,yy,QQ=geometry(polys,indices,newu,R1,R2,newtheta);rr=contacts(xx,yy,reverse)
            by_slave={c['i']:c for c in rr};active=force>1e-5
            gap_error=max(abs(by_slave[c['i']]['gap']) for k,c in enumerate(rows) if active[k])*1000
            penetration=max(0,-min(c['gap'] for c in rr))*1000
            actual_torque=sum(-old.cross2(by_slave[c['i']]['point2']-[fe.CENTER,0],by_slave[c['i']]['normal'])*force[k] for k,c in enumerate(rows))
            torque_error=abs(actual_torque/(torque*1000)-1)
            newP=[load_map([by_slave[c['i']] for c in rows],indices[0],R1,1),load_map([by_slave[c['i']] for c in rows],indices[1],QQ,2)]
            elastic_error=max(np.linalg.norm(v-c@b@force)/max(np.linalg.norm(v),1e-15) for v,c,b in zip(newu,C,newP))
            angular_step=abs(newtheta-theta)*fe.RB*1000
            rec=dict(torque_Nm=torque,iteration=it,approach_um=delta*1000,
                active=int(active.sum()),candidates=len(rows),true_gap_error_um=gap_error,
                penetration_um=penetration,torque_relative_error=float(torque_error),
                elastic_fixed_point_relative_error=float(elastic_error),approach_step_um=angular_step)
            history.append(rec)
            print(json.dumps(rec),flush=True)
            if gap_error<tol_um and penetration<tol_um and torque_error<1e-6 and elastic_error<1e-5 and angular_step<tol_um:
                u=newu;theta=newtheta;converged=True;break
            u=[(1-relax)*v+relax*w for v,w in zip(u,newu)];theta=(1-relax)*theta+relax*newtheta
        stages.append(dict(torque_Nm=torque,converged=converged,last=rec))
        if not converged:break
    result=dict(tag=tag,phase=phase,step_mm=step,h_mm=h,relaxation=relax,case=case,relief_parameters=theta_relief,master_slave_reversed=reverse,stages=stages,
        all_load_stages_converged=all(s['converged'] for s in stages) and len(stages)==len(torques),
        mesh=mesh,history=history,seconds=time.time()-start,
        method='Condensed small-strain continuum, finite rigid hub rotation, updated node/segment projection and normals, relaxed external iteration; not consistent-tangent Newton; assumed sharp-tip/quadratic-root geometry. Relief cases change pinion geometry and FE stiffness.',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (OUT/(tag+'.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
    np.savez_compressed(OUT/(tag+'_state.npz'),u1=u[0],u2=u[1],theta=theta,indices1=indices[0],indices2=indices[1],poly1=polys[0],poly2=polys[1],force=force,slave_indices=np.array([c['i'] for c in rows]))
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--phase',type=float,default=.174048546)
    ap.add_argument('--step',type=float,default=.04);ap.add_argument('--h',type=float,default=.5)
    ap.add_argument('--maxiter',type=int,default=80);ap.add_argument('--relax',type=float,default=.45)
    ap.add_argument('--case',choices=['nominal','addendum','combined'],default='nominal');ap.add_argument('--reverse',action='store_true')
    a=ap.parse_args();run(a.phase,a.step,a.h,relax=a.relax,maxiter=a.maxiter,case=a.case,reverse=a.reverse)
