"""Vectorized solution and implicit tangent of the fixed-geometry gap model.

This operator caches only geometry. Forces/active sets are solved anew. It is
restricted to nonlinear Hertz, fixed compliance and positive total force.
"""
import numpy as np
from scipy.special import lambertw


class BatchedGapOperator:
    def __init__(self, model, torque_Nm, n_positions=120, force_engine='lambert',phi_positions=None):
        if force_engine not in ('lambert','iterative'):
            raise ValueError('Unknown force engine')
        self.force_engine=force_engine
        self.model = model
        self.torque = float(torque_Nm)
        self.force = 1000*self.torque/model.pair.g1.rb
        if self.force <= 0 or model.hertz.linearize:
            raise ValueError('Positive torque and nonlinear Hertz required')
        if phi_positions is None:
            self.phi, _ = model.pair.rotation_for_mesh(n_positions)
        else:
            self.phi=np.asarray(phi_positions,dtype=float)
            if self.phi.ndim!=1 or not len(self.phi) or not np.all(np.isfinite(self.phi)):
                raise ValueError('phi_positions must be a finite nonempty vector')
            n_positions=len(self.phi)
        states = [model.get_contact_state(phi) for phi in self.phi]
        width = max(len(s['g']) for s in states)
        self.valid = np.zeros((n_positions,width),bool)
        self.g0 = np.full((n_positions,width),1e6)
        self.c = np.ones((n_positions,width))
        self.r = np.ones((n_positions,width))
        self.xi1 = np.zeros((n_positions,width))
        self.xi2 = np.zeros((n_positions,width))
        for i,s in enumerate(states):
            n=len(s['g']); self.valid[i,:n]=True
            self.g0[i,:n]=s['g'];self.c[i,:n]=s['c_lin'];self.r[i,:n]=s['r_eq']
            for name,gear,u in [('xi1',model.pair.g1,s['u1']),('xi2',model.pair.g2,s['u2'])]:
                getattr(self,name)[i,:n]=u/np.sqrt((gear.ra/gear.rb)**2-1)
        self.K = 1/(np.pi*model.hertz.E_star*model.hertz.b)
        # The unclipped derivative approaches -2K at the clipping boundary;
        # the clipped derivative is -K. This strict
        # condition makes each complete pair approach globally increasing.
        self.monotonicity_margin = float(np.min(self.c[self.valid])-2*self.K)
        if self.monotonicity_margin <= 0:
            raise ValueError('Pair approach not certified globally monotone')

    def elastic(self,p):
        ps=np.maximum(p,1e-300)
        ratio=4*self.r/np.sqrt(4*(ps/self.model.hertz.b)*self.r/(np.pi*self.model.hertz.E_star))
        log=np.log(np.maximum(ratio,1))
        w=self.K*p*(2*log-1)
        tangent=self.c+self.K*np.where(ratio>1,2*log-2,-1)
        return self.c*p+w,tangent

    def evaluate(self,theta1=None,theta2=None, jacobian=False):
        g=self.g0.copy()
        shape=g.shape
        if theta1 is not None and self.model.micro1 is not None:
            g+=self.model.micro1.evaluate(self.xi1.ravel(),theta1).reshape(shape)
        if theta2 is not None and self.model.micro2 is not None:
            g+=self.model.micro2.evaluate(self.xi2.ravel(),theta2).reshape(shape)
        emax,_=self.elastic(np.full(shape,self.force))
        lo=np.min(np.where(self.valid,g,np.inf),axis=1)
        hi=np.min(np.where(self.valid,g+emax,np.inf),axis=1)
        delta=(lo+hi)/2
        p=np.zeros(shape)
        for outer in range(70):
            target=delta[:,None]-g
            active=(target>0)&self.valid
            if self.force_engine=='lambert':
                p=np.zeros(shape)
                C=4*np.pi*self.model.hertz.E_star*self.model.hertz.b*self.r[active]
                t=target[active];c=self.c[active];a=c/self.K
                clipped=t>=C*(c-self.K)
                values=np.empty_like(t)
                values[clipped]=t[clipped]/(c[clipped]-self.K)
                ix=~clipped
                z=-(t[ix]/(self.K*C[ix]))*np.exp(1-a[ix])
                regular=z<0
                vp=np.empty_like(z)
                vp[regular]=-(t[ix][regular]/self.K)/lambertw(z[regular],k=-1).real
                # Stable fallback when exp(1-c/K) underflows. This occurs at
                # very high beam compliance; Newton in p avoids exp(c/K).
                vp[~regular]=t[ix][~regular]/c[ix][~regular]
                for _ in range(5):
                    ii=~regular
                    if not np.any(ii):break
                    pp=vp[ii];cc=c[ix][ii];CC=C[ix][ii];tt=t[ix][ii]
                    log=np.log(CC/pp)
                    vp[ii]=pp-(pp*(cc+self.K*(log-1))-tt)/(cc+self.K*(log-2))
                values[ix]=vp;p[active]=values
            else:
                pl=np.zeros(shape);pu=np.full(shape,self.force)
                p=np.where(active,np.clip(target/self.c,0,self.force),0)
                for inner in range(55):
                    elastic,tangent=self.elastic(p)
                    err=elastic-target
                    done=(~active)|(np.abs(err)<2e-15)
                    if np.all(done):break
                    pl=np.where(active&(err<0),p,pl)
                    pu=np.where(active&(err>=0),p,pu)
                    step=p-err/tangent
                    step=np.where((step>pl)&(step<pu),step,(pl+pu)/2)
                    p=np.where(done,p,step)
            p=np.where(active,p,0)
            elastic,tangent=self.elastic(p)
            balance=p.sum(axis=1)-self.force
            if np.max(np.abs(balance))<2e-8:break
            lo=np.where(balance<0,delta,lo);hi=np.where(balance>=0,delta,hi)
            slope=np.sum(np.where(active,1/tangent,0),axis=1)
            step=delta-balance/np.maximum(slope,1e-300)
            step=np.where((step>lo)&(step<hi),step,(lo+hi)/2)
            converged=np.abs(balance)<2e-8
            delta=np.where(converged,delta,step)
        else:
            raise RuntimeError('Batched equilibrium did not converge')
        separation=g-delta[:,None]+elastic
        result={'prediction':delta-delta.mean(),'delta':delta,'forces':p,
                'gaps':g,'separations':separation,
                'force_residual_N':float(np.max(np.abs(balance)))}
        if jacobian:
            if theta1 is None or self.model.micro1 is None:
                raise ValueError('Pinion relief required for tangent')
            dg=self.model.micro1.jacobian(self.xi1.ravel(),theta1).reshape(*shape,4)
            weights=np.where(active,1/tangent,0)
            J=np.sum(weights[:,:,None]*dg,axis=1)/weights.sum(axis=1)[:,None]
            result['jacobian']=J-J.mean(axis=0)
        return result
