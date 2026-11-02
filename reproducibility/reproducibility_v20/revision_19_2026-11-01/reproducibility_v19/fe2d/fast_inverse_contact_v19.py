"""Full-step projection iteration with audited damped fallback for inversion.
The inherited operator selects full-profile or nominal/reference elasticity.
"""
from cycle_contact_v19 import *
from spatial_projection_v19 import search as accelerated_search
mc.search=accelerated_search

def fullstep_phase(self,f,torque=300.,warm=None,tol=.0001,maxiter=100,save=False):
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
        disp=newdisp;angle=newangle
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

class FastOperator(Operator):
    def phase(self,f,torque=300.,warm=None,tol=.00001,maxiter=100,save=False):
        try:
            r,s=fullstep_phase(self,f,torque,warm,tol,min(maxiter,24),save)
            r['damped_fallback']=False
        except (RuntimeError,KeyError) as error:
            r,s=Operator.phase(self,f,torque,warm,tol,maxiter,save)
            r['damped_fallback']=True;r['fullstep_failure']=repr(error)
        r['iteration_source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        r['projection_source_sha256']=hashlib.sha256((Path(__file__).parent/'spatial_projection_v19.py').read_bytes()).hexdigest()
        return r,s
