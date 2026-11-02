"""Post-analysis of stored fits; support, Fisher and contact-transition audits.

No Monte Carlo trajectory is recomputed or overwritten.
"""
import sys,json,csv
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from Q1_identifiability_campaign import OUT as OLD,STARTS,SCALE,BOUNDS,DESIGNS,operators,bestfit,predict
from Q1_forward_campaign import build_pair,TipRelief,GearContactModel,BatchedGapOperator,SOLUTIONS,rt_to_sa
from campaign_provenance import provenance
OUT=OLD.parent/'q1_review2_2026-10-12';OUT.mkdir(exist_ok=True)

def stats():
    fits=[json.loads(s) for s in (OLD/'monte_carlo_records.jsonl').read_text().splitlines() if s.strip()]
    rows=[];fisher=[];baselines=[]
    for sd in [.25,.4]:
        truth=np.array([.02,.75,.005,sd])
        for i,start in enumerate(STARTS,1):
            e=np.abs(start-truth)/SCALE
            baselines.append(dict(sd_true=sd,start=i,theta=start.tolist(),addendum_scaled_error=float(e[:2].max()),dedendum_scaled_error=float(e[2:].max())))
        for name,design in DESIGNS.items():
            ops=operators(design)
            J=np.vstack([op.evaluate(truth,jacobian=True)['jacobian'] for op in ops])*SCALE/.0001
            _,s,V=np.linalg.svd(J,full_matrices=False)
            for sig in [.1,.5,1]:
                group=[r for r in fits if r['sd_true']==sd and r['design']==name and r['sigma_um']==sig]
                est=np.array([r['theta'] for r in group]);eps=np.minimum(est-BOUNDS[:,0],BOUNDS[:,1]-est)/(BOUNDS[:,1]-BOUNDS[:,0])
                bound=eps<=1e-6
                upper_cd=(BOUNDS[2,1]-est[:,2])/(BOUNDS[2,1]-BOUNDS[2,0])<=1e-6
                selected=np.argmin(np.array([r['start_chi2'] for r in group]),axis=1)
                selected_starts=np.array(STARTS)[selected]
                start_distance=np.max(np.abs(est[:,2:]-selected_starts[:,2:])/SCALE[2:],axis=1)
                rows.append(dict(sd_true=sd,design=name,sigma_um=sig,n=len(group),any_bound_fraction=float(bound.any(axis=1).mean()),
                    dedendum_bound_fraction=float(bound[:,2:].any(axis=1).mean()),cd_upper_fraction=float(upper_cd.mean()),
                    sd_any_bound_fraction=float(bound[:,3].mean()),selected_first_start_fraction=float(np.mean(selected==0)),
                    median_distance_from_selected_start_dedendum=float(np.median(start_distance))))
                if sig==.1:
                    qerr=(est-truth)/SCALE
                    projected=qerr@V[-1]
                    cov=(V.T/s**2)@V
                    # Max of the two correlated dedendum absolute errors is a
                    # different statistic from one weakest-direction coordinate.
                    rng=np.random.default_rng(20261013)
                    gaussian=rng.standard_normal((100000,4))@np.diag(1/s)@V
                    fisher.append(dict(sd_true=sd,design=name,sigma_um=sig,singular_values=s.tolist(),weak_vector=V[-1].tolist(),
                        weakest_direction_sd=1/float(s[-1]),gaussian_abs_median=float(norm.ppf(.75)/s[-1]),
                        mc_projected_abs_median=float(np.median(np.abs(projected))),mc_projected_mean=float(projected.mean()),
                        mc_projected_sd=float(projected.std(ddof=1)),
                        mc_dedendum_max_median=float(np.median(np.max(np.abs(qerr[:,2:]),axis=1))),
                        gaussian_dedendum_max_median=float(np.median(np.max(np.abs(gaussian[:,2:]),axis=1))),
                        covariance_q=cov.tolist()))
    report=dict(provenance=provenance(),bound_tolerance='distance to a bound divided by box width <= 1e-6',
                baseline_errors=baselines,fit_bound_statistics=rows,fisher_comparison=fisher,
                note='Gaussian comparison is an unconstrained local approximation at truth; no calibration to Monte Carlo medians.')
    (OUT/'fit_diagnostics.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    with (OUT/'fit_bound_statistics.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print('Fisher',[(r['sd_true'],r['design'],r['gaussian_abs_median'],r['mc_projected_abs_median'],r['gaussian_dedendum_max_median'],r['mc_dedendum_max_median']) for r in fisher],flush=True)

def geometries():
    old=json.loads((OLD/'geometry_transfer.json').read_text())['records'];rows=[]
    for r in old:
        g1=__import__('geometry.involute',fromlist=['InvoluteGear']).InvoluteGear(r['z1'],r['module_mm'],20,r['width_mm'])
        geo=__import__('geometry.involute',fromlist=['InvoluteGear','GearPair']);g2=geo.InvoluteGear(r['z2'],r['module_mm'],20,r['width_mm'])
        pair=geo.GearPair(g1,g2);model=GearContactModel(pair,TipRelief())
        design=[(T,120 if len(r['torques_Nm'])==1 else 60) for T in r['torques_Nm']]
        rr=[];mins=[];count=0
        for T,n in design:
            op=BatchedGapOperator(model,T,n);res=op.evaluate(np.array(r['theta_true']),jacobian=True)
            loaded=(res['forces']>1e-8)&op.valid
            mins.append(float(op.xi1[loaded].min()));count+=int(np.sum(op.xi1[loaded]<r['sd_true']))
            rr.append(res['jacobian'])
        J=np.vstack(rr)*SCALE/.0001;s=np.linalg.svd(J,compute_uv=False)
        err=np.abs(np.array(r['theta'])-r['theta_true'])/SCALE
        rows.append(dict(geometry=r['geometry'],sd_true=r['sd_true'],torques_Nm=r['torques_Nm'],min_loaded_xi=min(mins),
                         loaded_relief_contacts=count,smallest_singular_value=float(s[-1]),rank=int(np.sum(s>s[0]*1e-7)),
                         dedendum_scaled_error=float(err[2:].max())))
    (OUT/'geometry_support.json').write_text(json.dumps(dict(provenance=provenance(),sigma_um=.1,rows=rows),indent=2),encoding='utf-8')
    print('Geometry support rows',len(rows),flush=True)

def flat_profiles():
    profiles=json.loads((OLD/'profile_likelihood.json').read_text())['records'];rows=[]
    for sd in [.25,.4]:
        truth=np.array([.02,.75,.005,sd])
        for name,design in DESIGNS.items():
            ops=operators(design);sigma=.0001
            y=predict(ops,truth)+np.random.default_rng(20261012).normal(0,sigma,120)
            p=[r for r in profiles if r['sd_true']==sd and r['design']==name]
            starts=[*STARTS,*[np.array(r['baseline']['theta']) for r in p],
                    *[np.array(t['theta']) for r in p if r['parameter']=='Cd' for t in r['rows'] if t['value']==0]]
            invisible=bestfit(ops,y,sigma,fixed={2:0,3:.05},starts=starts)
            best=min([r['baseline']['chi2'] for r in p]+[t['chi2'] for r in p for t in r['rows']])
            theta=np.array(invisible['theta']);zero=theta.copy();zero[2]=0
            contacts=[op.evaluate(zero) for op in ops]
            lower=min(float(op.xi1[(r['forces']>1e-8)&op.valid].min()) for op,r in zip(ops,contacts))
            candidate=theta.copy();candidate[2]=.05
            invariant=float(np.max(np.abs(predict(ops,candidate)-predict(ops,theta))))
            rows.append(dict(sd_true=sd,design=name,invisible_fit=invisible,best_profile_chi2=best,
                invisible_delta_chi2=invisible['chi2']-best,min_loaded_xi_invisible_fit=lower,
                response_change_at_Cd_50um_sd_005_mm=invariant,
                nominal_zero_dedendum_response_rms_um=float(np.sqrt(np.mean((predict(ops,truth)-predict(ops,np.array([.02,.75,0,sd])))**2))*1000)))
    (OUT/'flat_profile_diagnostics.json').write_text(json.dumps(dict(provenance=provenance(),rows=rows,
        interpretation='Exact invariant parameter subsets can be visited during profiling; finite-noise profile flatness at a nonzero-sensitivity truth is not a proof of structural nonidentifiability at that truth.'),indent=2),encoding='utf-8')
    print('Invisible profile costs',[(r['sd_true'],r['design'],r['invisible_delta_chi2']) for r in rows],flush=True)

def waveforms():
    rows=[];curves=[];refinement=[]
    for variant in ['legacy','shear-G','projected-energy','centerline-energy']:
        pair=build_pair();micro=TipRelief(p=1);model=GearContactModel(pair,micro,micro,compliance_variant=variant)
        sol=SOLUTIONS['Sol2'];theta=np.array([sol['d_um']*.001,rt_to_sa(sol['rt_mm'],pair.g1),0,.5])
        for name,t in [('unmodified',None),('Sol2',theta)]:
            op=BatchedGapOperator(model,650,1920);res=op.evaluate(t,t);delta=res['delta'];phi=np.rad2deg(op.phi)
            _,tangent=op.elastic(res['forces']);active=(res['forces']>1e-8)&op.valid
            stiffness=np.sum(np.where(active,1/tangent,0),axis=1)/1000 # N/µm
            counts=active.sum(axis=1)
            jumps=np.abs(np.diff(np.r_[delta,delta[0]]))*1000
            rows.append(dict(variant=variant,case=name,torque_Nm=650,n_positions=1920,
                mean_approach_um=float(delta.mean()*1000),peak_to_peak_um=float(np.ptp(delta)*1000),
                waveform_rms_um=float(np.std(delta)*1000),max_adjacent_change_um=float(jumps.max()),
                median_single_pair_approach_um=float(np.median(delta[counts==1])*1000) if np.any(counts==1) else None,
                median_two_pair_approach_um=float(np.median(delta[counts==2])*1000) if np.any(counts==2) else None,
                mesh_stiffness_min_N_um=float(stiffness.min()),mesh_stiffness_max_N_um=float(stiffness.max())))
            if name=='unmodified':curves.append(dict(variant=variant,phi=phi,delta=delta*1000,stiffness=stiffness))
            if variant=='legacy' and name=='unmodified':
                centre=op.phi[np.argmax(jumps[:-1])]+(op.phi[1]-op.phi[0])/2
                half=np.deg2rad(.03)
                for n in [65,257,1025,4097]:
                    localphi=np.linspace(centre-half,centre+half,n)
                    local=BatchedGapOperator(model,650,phi_positions=localphi);l=local.evaluate()
                    refinement.append(dict(n_positions=n,step_deg=float(np.rad2deg(localphi[1]-localphi[0])),
                        max_adjacent_change_um=float(np.abs(np.diff(l['delta'])).max()*1000),
                        local_range_um=float(np.ptp(l['delta'])*1000)))
    labels={'legacy':'Baseline','shear-G':'G shear','projected-energy':'Radial energy','centerline-energy':'Centre-line'}
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for c in curves:
        axes[0].plot(c['phi'],c['delta'],label=labels[c['variant']]);axes[1].plot(c['phi'],c['stiffness'],label=labels[c['variant']])
    axes[0].set_ylabel('Total approach (µm)');axes[1].set_ylabel('Incremental mesh stiffness (N/µm)')
    for ax in axes:ax.set_xlabel('Rotation (deg)');ax.grid(alpha=.2)
    axes[0].legend(fontsize=8);fig.tight_layout();fig.savefig(OUT/'plateau_stiffness.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(5,3.4));ax.loglog([r['step_deg'] for r in refinement],[r['max_adjacent_change_um'] for r in refinement],'o-')
    ax.set_xlabel('Local angular step (deg)');ax.set_ylabel('Largest adjacent approach change (µm)');ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(OUT/'transition_resolution.png',dpi=160);plt.close(fig)
    report=dict(provenance=provenance(),rows=rows,transition_refinement=refinement,
                stiffness_definition='d(sum pair forces)/d(delta) at fixed gaps, not force/delta secant stiffness',
                external_comparison='External plateau, waveform and stiffness data are unavailable; these are internal diagnostics only.')
    (OUT/'waveform_diagnostics.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Transition',refinement,flush=True)

if __name__=='__main__':stats();geometries();flat_profiles();waveforms()
