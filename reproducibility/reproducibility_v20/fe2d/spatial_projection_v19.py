"""Exact midpoint-ball broad phase for the declared node-to-segment search.
Any segment within dmax has its midpoint within dmax+length/2. Sorting
candidate indices preserves the original tie-breaking convention.
"""
import numpy as np
from scipy.spatial import cKDTree
import updated_surface_contact as original
fe=original.fe

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
    slave=np.where((abs(x[:,0]-fe.CENTER/2)<5)&(abs(x[:,1])<12)&(ns@normal>.45))[0]
    radius=dmax+.5*np.max(np.sqrt(lm))+1e-12
    neighborhoods=cKDTree(ym+.5*em).query_ball_point(x[slave],radius,return_sorted=True)
    for i,neighbors in zip(slave,neighborhoods):
        if not neighbors:continue
        use=np.asarray(neighbors,dtype=int)
        t=np.clip(np.sum((x[i]-ym[use])*em[use],axis=1)/lm[use],0,1)
        q=ym[use]+t[:,None]*em[use];dist=np.linalg.norm(q-x[i],axis=1)
        k=int(np.argmin(dist));j=int(ids[use[k]])
        if dist[k]>dmax:continue
        n=-nmm[use[k]];g=float((q[k]-x[i])@n)
        if (t[k]<1e-9 or t[k]>1-1e-9) and g>1e-10:
            n=(q[k]-x[i])/dist[k];g=float(dist[k])
        if n@normal<.4 or ns[i]@n<.4:continue
        rows.append(dict(i=int(i),j=j,t=float(t[k]),normal=n,gap=g,q=q[k]))
    if not rows:raise RuntimeError('No contact candidates')
    return rows
