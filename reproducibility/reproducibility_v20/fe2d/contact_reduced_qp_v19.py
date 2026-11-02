"""Exact constraint generation for the condensed convex contact QP.
Omitted dual forces are zero; all omitted primal gaps are checked after every
subproblem. This changes linear algebra, not the contact model or constraints.
"""
import numpy as np
from scipy.sparse import csc_matrix
import updated_surface_contact as mc


def sparse_matvec(C,v):
    """Exact product, visiting only exactly nonzero load entries."""
    idx=np.flatnonzero(v)
    return C[:,idx]@v[idx]


def sparse_columns(C,P):
    """Exact C@P without SciPy copying the entire dense C for each product."""
    return np.add.reduceat(C[:,P.indices]*P.data[None,:],P.indptr[:-1],axis=1)


def load_map_loop(rows,indices,R,which):
    lookup={int(v):i for i,v in enumerate(indices)};rr=[];cc=[];vv=[]
    for k,c in enumerate(rows):
        slave=which==(2 if c.get('reverse',False) else 1)
        count=mc.N1 if c.get('reverse',False) else mc.N2
        points=[(c['i'],1.)] if slave else [(c['j'],1-c['t']),((c['j']+1)%count,c['t'])]
        n=R.T@c['normal']*(-1 if which==1 else 1)
        for j,w in points:
            if j not in lookup:raise RuntimeError('Candidate escaped condensed patch')
            for d in [0,1]:rr.append(2*lookup[j]+d);cc.append(k);vv.append(float(w*n[d]))
    return csc_matrix((vv,(rr,cc)),shape=(2*len(indices),len(rows)))


def load_map(rows,indices,R,which):
    n=len(rows);reverse=np.array([c.get('reverse',False) for c in rows]);slave=reverse if which==2 else ~reverse
    i=np.array([c['i'] for c in rows]);j=np.array([c['j'] for c in rows]);t=np.array([c['t'] for c in rows])
    pts=np.column_stack([np.where(slave,i,j),np.where(slave,i,(j+1)%np.where(reverse,mc.N1,mc.N2))])
    loc=np.searchsorted(indices,pts)
    if np.any(loc>=len(indices)) or not np.array_equal(indices[loc],pts):raise RuntimeError('Candidate escaped condensed patch')
    weights=np.column_stack([np.where(slave,1.,1-t),np.where(slave,0.,t)])
    normals=np.array([c['normal'] for c in rows])@R*(-1 if which==1 else 1)
    rr=(2*loc[:,:,None]+np.arange(2)[None,None,:]).ravel();cc=np.broadcast_to(np.arange(n)[:,None,None],(n,2,2)).ravel()
    values=(weights[:,:,None]*normals[:,None,:]).ravel()
    return csc_matrix((values,(rr,cc)),shape=(2*len(indices),n))


def diagonal(C,P):
    out=np.zeros(P[0].shape[1])
    for c,p in zip(C,P):
        counts=np.diff(p.indptr);cols=np.repeat(np.arange(p.shape[1]),counts);offset=np.arange(len(p.data))-np.repeat(p.indptr[:-1],counts)
        idx=np.zeros((p.shape[1],int(max(counts))),int);v=np.zeros(idx.shape)
        idx[cols,offset]=p.indices;v[cols,offset]=p.data
        out+=np.einsum('ij,ijk,ik->i',v,c[idx[:,:,None],idx[:,None,:]],v)
    return out


def solve(C,P,g,a,torque,initial,geometric_gap):
    diag=diagonal(C,P);s=float(np.median(diag));eps=s*1e-8
    b=a/mc.fe.RB;F=torque/mc.fe.RB;n=len(g)
    candidates=np.where(b>.1)[0]
    score=np.full(n,np.inf);score[candidates]=g[candidates]/b[candidates]+F*diag[candidates]/(2*b[candidates]**2)
    active=np.unique(np.r_[np.where(initial>1e-6)[0],np.where(geometric_gap<.001)[0],np.argsort(score)[:min(12,len(candidates))]])
    tolerance=max(1e-13,F*s*1e-10);loops=0
    while True:
        pp=[p[:,active] for p in P];v=[sparse_columns(c,p) for c,p in zip(C,pp)]
        H=sum(p.T@u for p,u in zip(pp,v));H=(H+H.T)/2
        f,delta,_=mc.solve_qp(H+np.eye(len(active))*eps,g[active],a[active],torque,initial=initial[active])
        force=np.zeros(n);force[active]=f;disp=[u@f for u in v]
        w=sum(p.T@u for p,u in zip(P,disp))+g-delta*b+eps*force
        bad=np.where(w < -tolerance)[0];missing=np.setdiff1d(bad,active)
        if not len(missing):
            assert w.min()>-max(tolerance*20,1e-10)
            assert abs(a@force/torque-1)<1e-9
            return force,delta,disp,eps,dict(subproblems=loops+1,variables=len(active),all_variables=n,minimum_gap_mm=float(w.min()))
        active=np.unique(np.r_[active,missing]);loops+=1
        if loops>8:active=np.arange(n)
