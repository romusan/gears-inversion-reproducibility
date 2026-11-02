"""Declared idealized machined-flank geometry for simulation, not measured CAD.

Only the upper (loaded) pinion flank is relieved. Modified involute is extended
until it meets the original tip circle; an assumed quadratic root blend joins
the modified flank to the unmodified root circle. Sharp tip junction retained.
"""
import numpy as np
from scipy.optimize import brentq
import pilot_surface_contact as p


def profile(u,tooth,theta):
    fe=p.fe;xi=np.clip(u/fe.UA,0,1);Ca,sa,Cd,sd=theta
    amount=Ca*(max(xi-sa,0)/(1-sa))**2+Cd*(max(sd-xi,0)/sd)**2
    beta=fe.HALF+fe.INV-(u-np.arctan(u))+tooth*2*np.pi/fe.Z
    normal=np.array([np.sin(beta-np.arctan(u)),-np.cos(beta-np.arctan(u))])
    return fe.point(u,tooth,1)+amount*normal


def contour(step,theta):
    fe=p.fe
    if not any(theta):return p.contour(step)[0]
    uf=fe.UF;ua=fe.UA;trim=.4;us=np.sqrt(uf*uf+2*trim/fe.RB)
    bf=fe.HALF+fe.INV-(uf-np.arctan(uf));pts=[]
    def add(x):
        if not pts or np.linalg.norm(x-pts[-1])>1e-10:pts.append(np.asarray(x))
    uend=brentq(lambda u:np.linalg.norm(profile(u,0,theta))-fe.RA,ua,ua+.1) if theta[0]>0 else ua
    for tooth in range(fe.Z):
        a0=tooth*2*np.pi/fe.Z;st=step if tooth in [0,1,2,fe.Z-1,fe.Z-2] else .35
        for side,ascending in [(-1,True),(1,False)]:
            af=a0+side*(bf+trim/fe.RF);root=fe.RF*np.array([np.cos(af),np.sin(af)])
            fn=(lambda u:fe.point(u,tooth,side)) if side==-1 else (lambda u:profile(u,tooth,theta))
            end=ua if side==-1 else uend
            c0=root if ascending else fn(us);c1=fn(uf);c2=fn(us) if ascending else root
            if ascending:
                for t in np.linspace(0,1,12,endpoint=False):add((1-t)**2*c0+2*t*(1-t)*c1+t*t*c2)
            nn=int(np.ceil(fe.RB*(end*end-us*us)/(2*st)))+1
            vv=np.sqrt(np.linspace(us*us,end*end,nn))
            if not ascending:vv=vv[::-1]
            for u in vv:add(fn(u))
            if not ascending:
                for t in np.linspace(0,1,13)[1:]:add((1-t)**2*c0+2*t*(1-t)*c1+t*t*c2)
            if ascending:
                lo=fe.HALF+fe.INV-(ua-np.arctan(ua))
                endxy=profile(uend,0,theta);hi=np.arctan2(endxy[1],endxy[0])
                nt=int(np.ceil(fe.RA*(lo+hi)/st))+1
                for a in np.linspace(a0-lo,a0+hi,nt)[1:]:add(fe.RA*np.array([np.cos(a),np.sin(a)]))
        aa=a0+bf+trim/fe.RF;bb=a0+2*np.pi/fe.Z-bf-trim/fe.RF
        for a in np.linspace(aa,bb,12)[1:-1]:add(fe.RF*np.array([np.cos(a),np.sin(a)]))
    xy=np.array(pts);assert np.linalg.norm(profile(uend,0,theta))-fe.RA<1e-9
    assert .5*np.sum(p.cross2(xy,np.roll(xy,-1,axis=0)))>0
    return xy
