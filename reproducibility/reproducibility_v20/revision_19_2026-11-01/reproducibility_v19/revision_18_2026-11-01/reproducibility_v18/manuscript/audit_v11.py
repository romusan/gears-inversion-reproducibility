"""Independent, deterministic review of the 24/24 cross-operator inverse test.

Reads archived v10 records without overwriting them. Profile objectives are
conditional discrepancy diagnostics, not calibrated confidence intervals.
"""
import sys, json, hashlib, time
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
DEP = ROOT / 'deposit_v6'
OUT = ROOT / 'revision_11_2026-10-23'
OUT.mkdir(exist_ok=True)
PROJ = DEP / 'gear_inverse_identifiability'
sys.path[:0] = [str(PROJ/'src'), str(PROJ/'experiments')]
from geometry.involute import InvoluteGear, GearPair
from geometry.microgeometry import TipRelief, GridRelief
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator
from Q1_identifiability_campaign import fit, SCALE, BOUNDS

def rms(x): return float(np.sqrt(np.mean(np.asarray(x)**2)))

def main():
    t0=time.time()
    src=DEP/'results/independent_validation/11_fe_cycle_24_24.jsonl'
    records=[json.loads(x) for x in src.read_text().splitlines() if x.strip()]
    keys=[(r['case'],r['phase_fraction']) for r in records]
    assert len(keys)==len(set(keys)), 'Duplicate FE case/phase records'
    phases=sorted({r['phase_fraction'] for r in records})
    interior=[p for p in phases if not any(r['restricted_nominal_window'] for r in records if r['phase_fraction']==p)]
    assert len(records)==3*len(phases) and len(interior)==102
    curves={}
    for case in ['unmodified','addendum','dedendum']:
        lookup={r['phase_fraction']:r['approach_um'] for r in records if r['case']==case}
        a=np.array([lookup[p] for p in interior]);curves[case]=(a-a.mean())*.001
    truth=np.array([.02,.75,.01,.5]);micro=TipRelief();xx=np.linspace(0,1,1001)
    report=dict(source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
                n_records=len(records),n_phases=len(phases),n_interior=len(interior),
                excluded_phases=[p for p in phases if p not in interior],
                fe_combined_vs_nominal_rms_um=1000*rms(curves['dedendum']-curves['unmodified']),
                fe_addendum_vs_nominal_rms_um=1000*rms(curves['addendum']-curves['unmodified']),
                fe_isolated_dedendum_rms_um=1000*rms(curves['dedendum']-curves['addendum']),
                max_force_residual_N=max(abs(r['force_residual_N']) for r in records),
                max_contact_residual_mm=max(abs(r['contact_residual_mm']) for r in records),variants=[])
    rng=np.random.default_rng(20261023)
    starts=[np.array([.03,.65,.01,.35]),np.array([.015,.85,.02,.45])]
    starts += [BOUNDS[:,0]+rng.random(4)*(BOUNDS[:,1]-BOUNDS[:,0]) for _ in range(22)]
    # Deliberately include a zero-depth start and a nearly upper-bound start.
    starts += [np.array([.005,.35,0,.08]), np.array([.09,.94,.049,.49])]
    fig,axes=plt.subplots(2,2,figsize=(12,8))
    plt.rcParams.update({'font.size':11})
    for variant in ['legacy','projected-energy']:
        pair=GearPair(InvoluteGear(24,3,20,20),InvoluteGear(24,3,20,20))
        op=BatchedGapOperator(GearContactModel(pair,micro1=micro,compliance_variant=variant),300,phi_positions=np.array(interior)*2*np.pi/24)
        y=curves['dedendum'];sigma=.0001
        attempts=[fit([op],y,sigma,s,max_nfev=1600) for s in starts]
        best=min(attempts,key=lambda r:r['chi2'])
        # C_d=0 makes s_d redundant: fix both, leaving precisely two free coordinates.
        restricted=[fit([op],y,sigma,s,fixed={2:0.,3:.5},max_nfev=1600) for s in starts]
        null=min(restricted,key=lambda r:r['chi2'])
        est=np.array(best['theta']);pred=op.evaluate(est,jacobian=True)
        true=op.evaluate(truth,jacobian=True);z=truth.copy();z[2]=0
        signal=1000*rms(true['prediction']-op.evaluate(z)['prediction'])
        profiles={}
        for j,grid in [(2,np.linspace(0,.05,41)),(3,np.linspace(.05,.5,46))]:
            rr=[];warm=est.copy()
            for value in grid:
                ss=[warm,est,starts[2],starts[8],starts[15]]
                ff=[fit([op],y,sigma,s,{j:float(value)},max_nfev=1000) for s in ss]
                b=min(ff,key=lambda r:r['chi2']);warm=np.array(b['theta'])
                rr.append(dict(value=float(value),**b))
            profiles[['Ca','sa','Cd','sd'][j]]=rr
            print(variant,'profile',j,'done',flush=True)
        base=min([best['chi2']]+[r['chi2'] for rr in profiles.values() for r in rr])
        for rr in profiles.values():
            for r in rr:r['delta_chi2']=r['chi2']-base
        residual=pred['prediction']-y
        J=pred['jacobian']*SCALE/sigma
        sv=np.linalg.svd(J,compute_uv=False)
        r=dict(variant=variant,truth=truth.tolist(),starts=[s.tolist() for s in starts],
               attempts=attempts,best=best,restricted=null,restricted_attempts=restricted,
               delta_chi2_no_dedendum=null['chi2']-best['chi2'],
               best_profile_rmse_um=1000*rms(micro.evaluate(xx,est)-micro.evaluate(xx,truth)),
               restricted_profile_rmse_um=1000*rms(micro.evaluate(xx,np.array(null['theta']))-micro.evaluate(xx,truth)),
               analytic_isolated_signal_rms_um=signal,
               fe_to_analytic_isolated_ratio=report['fe_isolated_dedendum_rms_um']/signal,
               scaled_whitened_singular_values=sv.tolist(),
               residual_mean_um=float(residual.mean()*1000),
               profiles=profiles)
        # Independent central differences, away from the upper bound by using the truth minus a small offset.
        check=truth.copy();check[3]=.48
        tangent=op.evaluate(check,jacobian=True)['jacobian']
        fd=[]
        for j,h in enumerate([1e-7,1e-6,1e-7,1e-6]):
            plus=check.copy();minus=check.copy();plus[j]+=h;minus[j]-=h
            d=(op.evaluate(plus)['prediction']-op.evaluate(minus)['prediction'])/(2*h)
            fd.append(float(np.linalg.norm(d-tangent[:,j])/max(np.linalg.norm(d),1e-15)))
        r['jacobian_relative_errors']=fd
        report['variants'].append(r)
        for j,key in enumerate(['Cd','sd']):
            rr=profiles[key];factor=1000 if key=='Cd' else 1
            axes[0,j].plot([x['value']*factor for x in rr],[x['delta_chi2'] for x in rr],label=variant)
        axes[1,0].plot(xx,micro.evaluate(xx,est)*1000,label=variant)
        axes[1,1].plot(interior,residual*1000,'.',label=variant)
        print(variant,'best',best,'restricted',null,'profile RMS',r['best_profile_rmse_um'],flush=True)
        (OUT/'audit_inverse.json').write_text(json.dumps(report,indent=2))
    for j,label in enumerate(['Dedendum depth (µm)','Dedendum start']):
        axes[0,j].set_xlabel(label);axes[0,j].set_ylabel('Profile objective increase Δχ²')
        axes[0,j].axhline(3.841,color='k',ls='--',label='Nominal reference only')
        axes[0,j].set_ylim(0,25)
    axes[1,0].plot(xx,micro.evaluate(xx,truth)*1000,'k--',label='True relief')
    axes[1,0].set_xlabel('Flank coordinate ξ');axes[1,0].set_ylabel('Relief (µm)')
    axes[1,1].set_xlabel('Interior phase fraction');axes[1,1].set_ylabel('TE fit residual (µm)')
    for ax in axes.flat:ax.legend(fontsize=9);ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(OUT/'audit_inverse.png',dpi=220);plt.close(fig)
    report['elapsed_seconds']=time.time()-t0
    (OUT/'audit_inverse.json').write_text(json.dumps(report,indent=2))

if __name__=='__main__':main()
