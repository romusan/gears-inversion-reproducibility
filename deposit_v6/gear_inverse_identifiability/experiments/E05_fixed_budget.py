"""Fixed total sampling budget, a repeated-load control and step/grid audits.
Outputs are separate from the historical E05 figures.
"""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from E04_noise_bias import build_model, THETA_TRUE, SCALE
from identifiability.fisher_optimal_loads import FisherLoadSelector
from campaign_provenance import provenance

OUT=Path(__file__).resolve().parents[1]/'results'/'corrections_2026-10-12'
def clean(x):
    if isinstance(x,np.ndarray):return clean(x.tolist())
    if isinstance(x,(np.floating,np.integer)):return clean(x.item())
    if isinstance(x,float) and not np.isfinite(x):return None
    if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
    if isinstance(x,list):return [clean(v) for v in x]
    return x

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    selector=FisherLoadSelector(build_model(),THETA_TRUE,parameter_scale=SCALE,
                               sigma_mm=0.0001,h_rel=1e-4,rank_rtol=1e-7)
    torques=[50.,100.,200.,300.]
    # Common addendum coordinate subspace; this is conditional on nuisance
    # parameters being fixed, not marginal uncertainty of the full model.
    B=np.eye(4)[:,:2]
    designs=[]
    for loads in [[t] for t in torques]+[[50,100],[50,200],[50,300],[100,200],[100,300],[200,300],[100,100]]:
        full=selector.diagnostics(loads,total_observations=120)
        reduced=selector.diagnostics(loads,total_observations=120,subspace=B)
        designs.append(dict(torques=loads,full=full,conditional_addendum=reduced))
        print('design',loads,'rank',full['rank'],'conditional logdet',reduced['logdet'],flush=True)
    sweeps=[]
    for n in [20,60,120,240]:
        mats=[]
        for h in [1e-3,1e-4,1e-5]:
            J=selector._compute_jacobian(100,h_rel=h,n_positions=n)
            mats.append(J)
            sv=np.linalg.svd(J,compute_uv=False)
            sweeps.append(dict(n_positions=n,h_rel=h,singular_values=sv,
                               column_norms=np.linalg.norm(J,axis=0)))
        for k in [1,2]:
            sweeps[-3+k]['column_relative_change']=np.linalg.norm(mats[k]-mats[k-1],axis=0)/np.maximum(np.linalg.norm(mats[k-1],axis=0),1e-30)
        print('grid completed',n,flush=True)
    active=[]
    te=selector.te_model
    u_tip=np.sqrt((te.pair.g1.ra/te.pair.g1.rb)**2-1)
    for t in torques:
        cycle=te.compute_cycle(torque_Nm=t,n_positions=240,theta1=THETA_TRUE)
        sactive=[]
        for state,forces in zip(cycle['states'],cycle['forces']):
            s=np.clip(state['u1']/u_tip,0,1)
            sactive.extend(s[np.asarray(forces)>1e-6].tolist())
        active.append(dict(torque=t,min_active_profile_coordinate=min(sactive),
                           dedendum_start=float(THETA_TRUE[3]),
                           dedendum_active_samples=sum(s<THETA_TRUE[3] for s in sactive)))
    report=dict(provenance=provenance(),theta_nominal=THETA_TRUE,scale=SCALE,sigma_mm=0.0001,
                budget=120,rank_rtol=selector.rank_rtol,designs=designs,derivative_audit=sweeps,
                active_contact_audit=active,
                interpretation='Addendum scores are conditional on fixed dedendum; full rank is numerical, not a structural proof.')
    (OUT/'E05_fixed_budget.json').write_text(json.dumps(clean(report),indent=2,allow_nan=False),encoding='utf-8')
    fig,ax=plt.subplots(1,2,figsize=(12,4.5))
    labels=[','.join(str(int(t)) for t in d['torques']) for d in designs]
    ax[0].bar(np.arange(len(designs)),[d['conditional_addendum']['logdet'] for d in designs])
    ax[0].set_xticks(np.arange(len(designs)),labels,rotation=60)
    ax[0].set_ylabel('Conditional addendum log det F')
    ax[0].set_title('120 observations for every design')
    for d in designs:
        if len(d['torques'])==1:
            ax[1].semilogy(range(1,5),np.maximum(d['full']['singular_values'],1e-30),'o-',label=labels[designs.index(d)] if False else str(d['torques']))
    ax[1].set_xlabel('Singular value index');ax[1].set_ylabel('Scaled whitened singular value');ax[1].legend()
    fig.tight_layout();fig.savefig(OUT/'E05_fixed_budget.png',dpi=180);plt.close(fig)
    print('saved',OUT,flush=True)

if __name__=='__main__':main()
