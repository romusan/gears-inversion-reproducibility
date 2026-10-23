"""Regenerate sensitivity, profile and resolution plots with readable labels."""
import json,shutil
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent
OLD=ROOT/'gear_inverse_identifiability/results/q1_revision_2026-10-12'
RES=ROOT/'deposit_v6/results/independent_validation';AUD=ROOT/'revision_11_2026-10-23'
DEST=BASE/'assets';DEST.mkdir(exist_ok=True)
plt.rcParams.update({'font.size':13,'axes.labelsize':14,'axes.titlesize':14,'legend.fontsize':11,'xtick.labelsize':11,'ytick.labelsize':11})
def load(name):return json.loads((OLD/name).read_text())
def finish(fig,name):
    for ax in fig.axes:ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(DEST/name,dpi=240,bbox_inches='tight');plt.close(fig)

rr=load('support_transition.json')['rows'];x=[r['sd_true'] for r in rr]
fig,aa=plt.subplots(3,1,figsize=(7,8),sharex=True)
aa[0].semilogy(x,[max(r['dedendum_signal_rms_um'],1e-12) for r in rr],'o-');aa[0].axhline(.1,color='k',ls='--');aa[0].set_ylabel('Isolated TE RMS (µm)')
aa[0].lines[-1].set_label('Noise scale 0.1 µm');aa[0].legend()
aa[1].plot(x,[r['numerical_rank'] for r in rr],'o-');aa[1].set_ylabel('Numerical rank');aa[1].set_yticks([2,3,4])
aa[2].semilogy(x,[max(r['dedendum_scaled_error'],1e-12) for r in rr],'o-');aa[2].set_ylabel('Scaled dedendum error');aa[2].set_xlabel('True dedendum start $s_d$')
finish(fig,'fig_transition_v11.png')

fig,aa=plt.subplots(2,2,figsize=(10,7))
for i,sd in enumerate([.25,.4]):
    for j,param in enumerate(['sd','Cd']):
        ax=aa[i,j]
        for r in load('profile_likelihood.json')['records']:
            if r['sd_true']==sd and r['parameter']==param:
                factor=1000 if param=='Cd' else 1
                ax.plot([p['value']*factor for p in r['rows']],[p['delta_chi2'] for p in r['rows']],label='300 Nm' if r['design']=='single300' else '50/300 Nm')
        ax.axhline(3.841,color='k',ls='--');ax.set_ylim(0,15);ax.set_title(f'True $s_d={sd}$');ax.set_ylabel('Profile Δχ²');ax.set_xlabel('Start $s_d$' if param=='sd' else 'Depth $C_d$ (µm)');ax.legend()
finish(fig,'fig_profiles_v11.png')

fig,aa=plt.subplots(1,2,figsize=(9,4.5))
for ax,sd in zip(aa,[.25,.4]):
    for name,label in [('single300','300 Nm'),('multi50_300','50/300 Nm')]:
        g=[r for r in load('monte_carlo_summary.json')['summary'] if r['sd_true']==sd and r['design']==name]
        l=ax.plot([r['sigma_um'] for r in g],[r['dedendum_scaled_error']['median'] for r in g],'o-',label=label)[0]
        ax.plot([r['sigma_um'] for r in g],[r['dedendum_scaled_error']['p90'] for r in g],':',color=l.get_color())
    ax.set_xlabel('Noise σ (µm)');ax.set_ylabel('Scaled dedendum error');ax.set_title(f'True $s_d={sd}$');ax.legend()
finish(fig,'fig_monte_v11.png')

fig,aa=plt.subplots(1,2,figsize=(9,4.5))
for ax,sd in zip(aa,[.25,.4]):
    for r in load('support_transition.json')['spectra']:
        if r['sd_true']==sd:ax.semilogy(range(1,5),r['singular_values'],'o-',label=f"{r['torque_Nm']:.0f} Nm")
    ax.set_xticks(range(1,5));ax.set_xlabel('Singular index');ax.set_ylabel('Scaled whitened singular value');ax.set_title(f'True $s_d={sd}$');ax.legend()
finish(fig,'fig_spectra_v11.png')

a=json.loads((AUD/'audit_structure.json').read_text())['null_space'];r=json.loads((RES/'07_resolution.json').read_text())['cases']['0.25']
fig,aa=plt.subplots(3,1,figsize=(7.5,8))
aa[0].plot(np.linspace(0,1,41),r['rdiag'],'o-');aa[0].axvline(a['minimum_loaded_coordinate'],ls='--',color='k',label='First loaded contact');aa[0].set_xlabel('Nodal coordinate ξ');aa[0].set_ylabel('Resolution diagonal');aa[0].legend()
aa[1].semilogy(np.arange(1,42),r['singular_values'],'o');aa[1].axvline(31.5,ls='--',color='k');aa[1].set_ylabel('Whitened singular value');aa[1].set_xlabel('Singular index')
aa[2].semilogy(np.arange(1,32),a['direction_std_um'],'o-');aa[2].axhline(1,color='k',ls='--');aa[2].set_ylabel('Conditional mode SD (µm)');aa[2].set_xlabel('Resolved singular index')
finish(fig,'fig_resolution_v11.png')

# External amplitudes: one panel per profile avoids crowded case/torque labels.
bench=json.loads((AUD/'audit_structure.json').read_text())['benchmark']
labels={'legacy':'Baseline','shear-G':'G shear','projected-energy':'Radial energy','centerline-energy':'Centre-line'}
fig,aa=plt.subplots(2,2,figsize=(9,6),sharex=True)
for ax,case in zip(aa.flat,['unmodified','Sol1','Sol2','Sol3']):
    for variant,label in labels.items():
        rr=[r for r in bench if r['case']==case and r['variant']==variant]
        ax.plot([r['torque_Nm'] for r in rr],[r['relative_error_percent'] for r in rr],'o-',label=label)
    ax.axhspan(-5,5,color='grey',alpha=.15);ax.set_title(case.capitalize() if case=='unmodified' else case)
    ax.set_xticks([350,500,650]);ax.set_xlabel('Torque (Nm)');ax.set_ylabel('Amplitude error (%)')
aa[0,0].legend(fontsize=9)
finish(fig,'fig_benchmark_v11.png')

import sys
sys.path[:0]=[str(ROOT/'deposit_v6/gear_inverse_identifiability/src'),str(ROOT/'deposit_v6/gear_inverse_identifiability/experiments')]
from V06_korta_mundo_reproduction import build_pair
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator
fig,aa=plt.subplots(2,1,figsize=(7,6),sharex=True)
for variant,label in labels.items():
    op=BatchedGapOperator(GearContactModel(build_pair(),compliance_variant=variant),650,1920)
    r=op.evaluate();_,tangent=op.elastic(r['forces'])
    stiff=np.sum(np.where((r['forces']>1e-8)&op.valid,1/tangent,0),axis=1)/1000
    aa[0].plot(np.rad2deg(op.phi),r['delta']*1000,label=label)
    aa[1].plot(np.rad2deg(op.phi),stiff,label=label)
aa[0].set_ylabel('Total approach (µm)');aa[1].set_ylabel('Incremental stiffness (N/µm)');aa[1].set_xlabel('Rotation (deg)');aa[0].legend(ncol=2)
finish(fig,'fig_stiffness_v11.png')
if (AUD/'audit_inverse.json').exists():
    import sys
    sys.path.insert(0,str(ROOT/'deposit_v6/gear_inverse_identifiability/src'))
    from geometry.microgeometry import TipRelief
    inverse=json.loads((AUD/'audit_inverse.json').read_text());micro=TipRelief();xx=np.linspace(0,1,1001)
    fig,aa=plt.subplots(2,2,figsize=(9,7.5))
    source=ROOT/'deposit_v6/results/independent_validation/11_fe_cycle_24_24.jsonl'
    records=[json.loads(x) for x in source.read_text().splitlines()]
    interior=sorted({r['phase_fraction'] for r in records if not r['restricted_nominal_window']})
    # Re-evaluate the saved estimates to plot their residuals without refitting.
    from geometry.involute import InvoluteGear,GearPair
    from mechanics.compliance import GearContactModel
    from mechanics.batched_operator import BatchedGapOperator
    d={r['phase_fraction']:r['approach_um'] for r in records if r['case']=='dedendum'}
    y=np.array([d[p] for p in interior]);y-=y.mean()
    for r in inverse['variants']:
        for j,key in enumerate(['Cd','sd']):
            rr=r['profiles'][key];factor=1000 if key=='Cd' else 1
            aa[0,j].plot([p['value']*factor for p in rr],[p['delta_chi2'] for p in rr],label=r['variant'])
        est=np.array(r['best']['theta']);aa[1,0].plot(xx,micro.evaluate(xx,est)*1000,label=r['variant'])
        pair=GearPair(InvoluteGear(24,3,20,20),InvoluteGear(24,3,20,20))
        op=BatchedGapOperator(GearContactModel(pair,micro1=micro,compliance_variant=r['variant']),300,phi_positions=np.array(interior)*2*np.pi/24)
        aa[1,1].scatter(interior,op.evaluate(est)['prediction']*1000-y,s=9,label=r['variant'])
    for j,label in enumerate(['Depth $C_d$ (µm)','Start $s_d$']):
        aa[0,j].axhline(3.841,color='k',ls='--',label='Nominal reference');aa[0,j].set_ylim(-.1,5);aa[0,j].set_xlabel(label);aa[0,j].set_ylabel('Profile Δχ²');aa[0,j].legend(fontsize=10)
    aa[1,0].plot(xx,micro.evaluate(xx,np.array([.02,.75,.01,.5]))*1000,'k--',label='True relief');aa[1,0].set_xlabel('Flank coordinate ξ');aa[1,0].set_ylabel('Relief (µm)');aa[1,0].legend(fontsize=10)
    aa[1,1].set_xlabel('Interior phase fraction');aa[1,1].set_ylabel('TE residual (µm)');aa[1,1].legend(fontsize=10)
    finish(fig,'fig_fe_inverse_v11.png')
print('Regenerated figures 3–8')
