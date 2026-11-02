"""Full-cycle bilateral moving contact with reusable body compliance.

The FE mesh and condensed band are fixed in body coordinates over the cycle.
The full-geometry generator remeshes for each prescribed profile. The inverse
variant explicitly retains nominal elasticity while changing the contact
geometry on a constant material-coordinate grid. These are distinct operators.
"""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from scipy.sparse import csc_matrix
from scipy.optimize import brentq
from shapely.geometry import Polygon
import updated_surface_contact as mc
import relieved_surface_geometry as rg

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'revision_19_2026-11-01'/'experiments';OUT.mkdir(parents=True,exist_ok=True)
fe=mc.fe
TRUTH=np.array([.020,.75,.010,.50])


def pose(f):
    # A continuously extended ideal involute defines the rigid pose even when
    # its theoretical contact point is beyond the physical tip. It is not a
    # restriction on actual contact candidates.
    s=f*fe.PB;v1=np.tan(fe.AW)+s/fe.RB;v2=np.tan(fe.AW)-s/fe.RB
    q=np.array([fe.CENTER/2,0])+s*np.array([np.sin(fe.AW),np.cos(fe.AW)])
    a1=np.arctan2(q[1],q[0])-np.arctan2(fe.point(v1)[1],fe.point(v1)[0])
    q2=q-[fe.CENTER,0]
    a2=np.arctan2(q2[1],q2[0])-np.arctan2(fe.point(v2)[1],fe.point(v2)[0])
    return fe.rotation(a1),fe.rotation(a2)


def fixed_topology(step,theta):
    """Same parameter fractions and vertex counts for every inverse geometry."""
    uf,ua=fe.UF,fe.UA;trim=.4;us=np.sqrt(uf*uf+2*trim/fe.RB)
    bf=fe.HALF+fe.INV-(uf-np.arctan(uf));pts=[]
    end=brentq(lambda u:np.linalg.norm(rg.profile(u,0,theta))-fe.RA,ua,ua+.15) if theta[0]>0 else ua
    def add(p):
        if not pts or np.linalg.norm(p-pts[-1])>1e-10:pts.append(np.asarray(p))
    for tooth in range(fe.Z):
        aa=tooth*2*np.pi/fe.Z;st=step if tooth in [0,1,2,fe.Z-1,fe.Z-2] else .35
        for side,asc in [(-1,True),(1,False)]:
            af=aa+side*(bf+trim/fe.RF);root=fe.RF*np.array([np.cos(af),np.sin(af)])
            fn=(lambda u:fe.point(u,tooth,-1)) if side==-1 else (lambda u:rg.profile(u,tooth,theta))
            c0=root if asc else fn(us);c1=fn(uf);c2=fn(us) if asc else root
            if asc:
                for t in np.linspace(0,1,12,endpoint=False):add((1-t)**2*c0+2*t*(1-t)*c1+t*t*c2)
            n=int(np.ceil(fe.RB*(ua*ua-us*us)/(2*st)))+2
            vv=np.sqrt(np.linspace(us*us,(ua if asc else end)**2,n))
            for u in vv if asc else vv[::-1]:add(fn(u))
            if not asc:
                for t in np.linspace(0,1,13)[1:]:add((1-t)**2*c0+2*t*(1-t)*c1+t*t*c2)
            if asc:
                lo=fe.HALF+fe.INV-(ua-np.arctan(ua));p=rg.profile(end,0,theta);hi=np.arctan2(p[1],p[0])
                nt=int(np.ceil(2*fe.RA*lo/st))+2
                for a in np.linspace(aa-lo,aa+hi,nt)[1:]:add(fe.RA*np.array([np.cos(a),np.sin(a)]))
        for a in np.linspace(aa+bf+trim/fe.RF,aa+2*np.pi/fe.Z-bf-trim/fe.RF,12)[1:-1]:add(fe.RF*np.array([np.cos(a),np.sin(a)]))
    return np.array(pts)


def body(poly,step,h,name):
    tag=f'{name}_s{step:g}_h{h:g}';path=OUT/'body_cache'/(tag+'.npz');path.parent.mkdir(exist_ok=True)
    sha=hashlib.sha256(poly.tobytes()).hexdigest()
    tooth=np.rint(np.arctan2(poly[:,1],poly[:,0])*fe.Z/(2*np.pi)).astype(int)%fe.Z
    selected=np.where(np.isin(tooth,[0,1,2,fe.Z-1,fe.Z-2]))[0]
    indices=np.unique(np.concatenate([(selected+i)%len(poly) for i in [-2,-1,0,1,2]]))
    if path.exists():
        z=np.load(path);assert str(z['poly_sha'])==sha and np.array_equal(z['indices'],indices)
        return dict(poly=poly,indices=indices,C=z['C'],tag=tag,nodes=int(z['nodes']),elements=int(z['elements']))
    near=np.zeros(len(poly),dtype=bool);near[indices]=True
    mesh=mc.old.make_body(poly,h,near);dofs=mesh['basis'].nodal_dofs[:,mesh['nodes'][indices]].T.ravel()
    lookup=np.full(mesh['basis'].N,-1);lookup[mesh['free']]=np.arange(len(mesh['free']))
    C=np.empty((len(dofs),len(dofs)))
    for j in range(0,len(dofs),48):
        dd=dofs[j:j+48];rhs=np.zeros((len(mesh['free']),len(dd)));rhs[lookup[dd],np.arange(len(dd))]=1
        U=mesh['solver'].solve(rhs);C[:,j:j+len(dd)]=U[lookup[dofs]]
    symmetry=float(np.linalg.norm(C-C.T)/np.linalg.norm(C));assert symmetry<1e-9;C=(C+C.T)/2
    np.savez_compressed(path,C=C,poly=poly,indices=indices,poly_sha=sha,nodes=len(mesh['xy']),elements=mesh['elements'],symmetry=symmetry)
    print('BODY',tag,len(mesh['xy']),len(indices),flush=True)
    return dict(poly=poly,indices=indices,C=C,tag=tag,nodes=len(mesh['xy']),elements=mesh['elements'])


class Operator:
    def __init__(self,step=.04,h=.5,theta=None,reference=False):
        fe.configure_24_24();self.step=step;self.h=h;self.reference=reference
        nominal=fixed_topology(step,np.array([0.,.75,0.,.5])) if reference else mc.old.contour(step)[0]
        self.b2=body(nominal,step,h,'reference_nominal' if reference else 'nominal')
        if reference or theta is None:self.b1=self.b2
        else:
            poly=rg.contour(step,theta);name='profile_'+hashlib.sha256(np.asarray(theta).tobytes()).hexdigest()[:12]
            self.b1=body(poly,step,h,name)
        self.polys=[self.b1['poly'],self.b2['poly']];self.C=[self.b1['C'],self.b2['C']]
        self.indices=[self.b1['indices'],self.b2['indices']];self.states={};self.last=None

    def set_parameters(self,theta):
        assert self.reference
        poly=fixed_topology(self.step,theta);assert len(poly)==len(self.b1['poly'])
        assert Polygon(poly).is_valid
        self.polys=[poly,self.b2['poly']]

    def phase(self,f,torque=300.,warm=None,tol=.0001,maxiter=100,save=False):
        mc.N1,mc.N2=map(len,self.polys);R1,R2=pose(f)
        if warm is None:disp=[np.zeros(len(c)) for c in self.C];angle=0.;guess={}
        else:disp=[a.copy() for a in warm['u']];angle=warm['angle'];guess=warm['guess'].copy()
        key=lambda c:(c['reverse'],c['i']);converged=False
        for it in range(maxiter):
            x,y,Q2=mc.geometry(self.polys,self.indices,disp,R1,R2,angle);rows=mc.contacts(x,y,two_pass=True)
            P=[mc.load_map(rows,self.indices[0],R1,1),mc.load_map(rows,self.indices[1],Q2,2)]
            V=[c@p for c,p in zip(self.C,P)];H=sum(p.T@v for p,v in zip(P,V));H=(H+H.T)/2
            a=np.array([-mc.old.cross2(c['point2']-[fe.CENTER,0],c['normal']) for c in rows])
            g=np.array([c['gap'] for c in rows])-sum(p.T@u for p,u in zip(P,disp))+a*angle
            eps=float(np.median(np.diag(H)))*1e-8
            force,delta,_=mc.solve_qp(H+np.eye(len(g))*eps,g,a,torque*1000,initial=np.array([guess.get(key(c),0) for c in rows]))
            newdisp=[v@force for v in V];newangle=delta/fe.RB
            xx,yy,QQ=mc.geometry(self.polys,self.indices,newdisp,R1,R2,newangle);newrows=mc.contacts(xx,yy,two_pass=True);by={key(c):c for c in newrows}
            active=force>1e-5;missing=[k for k,c in enumerate(rows) if key(c) not in by and active[k]]
            if missing:raise RuntimeError('Active projection disappeared')
            current=[by.get(key(c),c) for c in rows]
            gap=max(abs(current[k]['gap']) for k in np.where(active)[0])*1000
            penetration=max(0,-min(c['gap'] for c in newrows))*1000
            moment=sum(-mc.old.cross2(c['point2']-[fe.CENTER,0],c['normal'])*p for c,p in zip(current,force))
            terr=abs(moment/(torque*1000)-1)
            newP=[mc.load_map(current,self.indices[0],R1,1),mc.load_map(current,self.indices[1],QQ,2)]
            elast=max(np.linalg.norm(v-c@(p@force))/max(np.linalg.norm(v),1e-15) for v,c,p in zip(newdisp,self.C,newP))
            change=abs(newangle-angle)*fe.RB*1000
            if gap<tol and penetration<tol and terr<1e-6 and elast<1e-5 and change<tol:
                disp=newdisp;angle=newangle;converged=True;break
            disp=[.55*u+.45*v for u,v in zip(disp,newdisp)];angle=.55*angle+.45*newangle
            guess={key(c):float(p) for c,p in zip(rows,force)}
        rec=dict(phase=float(f),torque_Nm=torque,approach_um=float(angle*fe.RB*1000),converged=converged,iterations=it+1,
            gap_error_um=gap,penetration_um=penetration,torque_relative_error=float(terr),elastic_relative_error=float(elast),
            approach_step_um=change,regularization_gap_bound_um=float(eps*force.max()*1000),body_tags=[self.b1['tag'],self.b2['tag']])
        if not converged:raise RuntimeError('Nonconvergence '+json.dumps(rec))
        pg1,pg2=Polygon(xx),Polygon(yy)
        if not pg1.is_valid or not pg2.is_valid:raise RuntimeError('Invalid deformed polygon')
        rec['overlap_area_mm2']=float(pg1.intersection(pg2).area)
        if rec['overlap_area_mm2']>1e-8:raise RuntimeError('Global polygon overlap '+json.dumps(rec))
        state=dict(u=disp,angle=angle,guess={key(c):float(p) for c,p in zip(rows,force)})
        self.last=state
        if save:
            folder=OUT/'cycle_states';folder.mkdir(exist_ok=True)
            name=f"{self.b1['tag']}_f{f:.9f}"
            np.savez_compressed(folder/(name+'.npz'),u1=disp[0],u2=disp[1],angle=angle,force=force,slave_indices=np.array([c['i'] for c in rows]),directions=np.array([c['reverse'] for c in rows]))
            rec['state_file']=name+'.npz'
        return rec,state

    def predict(self,theta,phases,tol=.00001):
        self.set_parameters(theta);pred=[];records=[]
        for f in phases:
            r,s=self.phase(float(f),warm=self.states.get(float(f)),tol=tol)
            self.states[float(f)]=s;pred.append(r['approach_um']);records.append(r)
        return np.array(pred),records


def campaign(step,h):
    fe.configure_24_24();path=OUT/f'cycle_s{step:g}_h{h:g}.jsonl'
    existing=[json.loads(s) for s in path.read_text().splitlines() if s.strip()] if path.exists() else []
    done={(r['case'],r['phase']) for r in existing};failures=[]
    for case,theta in [('nominal',None),('addendum',np.array([.02,.75,0.,.5])),('combined',TRUTH)]:
        op=Operator(step,h,theta);warm=None
        for f in list(np.arange(120)/120)+[1.]:
            if (case,float(f)) in done:continue
            try:
                r,warm=op.phase(float(f),warm=warm,save=True)
            except Exception as e:
                # Retain the failed attempt and retry from unloaded geometry.
                failures.append(dict(case=case,phase=float(f),error=repr(e)))
                (OUT/f'failures_s{step:g}.json').write_text(json.dumps(failures,indent=2))
                try:r,warm=op.phase(float(f),warm=None,maxiter=160,save=True)
                except Exception as e:
                    failures.append(dict(case=case,phase=float(f),retry_error=repr(e)))
                    (OUT/f'failures_s{step:g}.json').write_text(json.dumps(failures,indent=2));raise
            r.update(case=case,step_mm=step,h_mm=h,theta=None if theta is None else theta.tolist(),
                model='Full geometry and FE elasticity; bilateral moving contact; one body mesh per geometry and resolution',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
            with path.open('a',encoding='utf-8') as f_out:f_out.write(json.dumps(r)+'\n')
            print('CYCLE',case,f,r['approach_um'],r['iterations'],flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--step',type=float,default=.04);ap.add_argument('--h',type=float,default=.5)
    a=ap.parse_args();campaign(a.step,a.h)
