"""Vectorized version of the equivalence-tested midpoint search."""
from spatial_projection_v19 import np,cKDTree,fe

def search(x,y,dmax=.1,normal_sign=1):
    e=np.roll(y,-1,axis=0)-y;l2=np.sum(e*e,axis=1)
    nm=np.column_stack([e[:,1],-e[:,0]])/np.sqrt(l2)[:,None]
    es=np.roll(x,-1,axis=0)-x;ns=np.column_stack([es[:,1],-es[:,0]])/np.linalg.norm(es,axis=1)[:,None]
    ns+=np.roll(ns,1,axis=0);ns/=np.linalg.norm(ns,axis=1)[:,None]
    normal=normal_sign*np.array([np.sin(fe.AW),np.cos(fe.AW)])
    end=np.roll(y,-1,axis=0);lo=np.minimum(y,end);hi=np.maximum(y,end)
    keep=(nm@normal<=-.3)&(lo[:,0]<fe.CENTER/2+5+dmax)&(hi[:,0]>fe.CENTER/2-5-dmax)&(lo[:,1]<12+dmax)&(hi[:,1]>-12-dmax)
    ids=np.where(keep)[0];ym=y[ids];em=e[ids];lm=l2[ids];nmm=nm[ids]
    slave=np.where((abs(x[:,0]-fe.CENTER/2)<5)&(abs(x[:,1])<12)&(ns@normal>.45))[0]
    radius=dmax+.5*np.max(np.sqrt(lm))+1e-12
    hood=cKDTree(ym+.5*em).query_ball_point(x[slave],radius,return_sorted=True)
    counts=np.array([len(a) for a in hood]);good=counts>0;slave=slave[good];counts=counts[good]
    if not len(slave):raise RuntimeError('No contact candidates')
    use=np.concatenate([a for a in hood if len(a)]).astype(int);si=np.repeat(slave,counts)
    t=np.clip(np.sum((x[si]-ym[use])*em[use],axis=1)/lm[use],0,1)
    q=ym[use]+t[:,None]*em[use];dist=np.linalg.norm(q-x[si],axis=1)
    starts=np.r_[0,np.cumsum(counts)[:-1]];mins=np.minimum.reduceat(dist,starts)
    chosen=np.minimum.reduceat(np.where(dist==np.repeat(mins,counts),np.arange(len(dist)),len(dist)),starts)
    t=t[chosen];q=q[chosen];dist=dist[chosen];use=use[chosen];j=ids[use];n=-nmm[use];g=np.sum((q-x[slave])*n,axis=1)
    edge=((t<1e-9)|(t>1-1e-9))&(g>1e-10)
    n[edge]=(q[edge]-x[slave[edge]])/dist[edge,None];g[edge]=dist[edge]
    good=(dist<=dmax)&(n@normal>=.4)&(np.sum(ns[slave]*n,axis=1)>=.4)
    rows=[dict(i=int(i),j=int(jj),t=float(tt),normal=nn,gap=float(gg),q=qq) for i,jj,tt,nn,gg,qq in zip(slave[good],j[good],t[good],n[good],g[good],q[good])]
    if not rows:raise RuntimeError('No contact candidates')
    return rows
