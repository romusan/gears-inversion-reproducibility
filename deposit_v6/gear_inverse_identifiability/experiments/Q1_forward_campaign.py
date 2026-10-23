"""Prespecified physical ablations; never fit compliance to benchmark targets."""
import sys,json,time
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator
from mechanics.transmission_error import TransmissionError
from geometry.microgeometry import TipRelief
from V06_korta_mundo_reproduction import build_pair,rt_to_sa,SOLUTIONS,TORQUES,REFERENCE_PP,REFERENCE_SOURCE
from campaign_provenance import provenance

OUT=Path(__file__).resolve().parents[1]/'results'/'q1_revision_2026-10-12'
OUT.mkdir(exist_ok=True)

def main():
    rows=[];equivalence=[]
    for variant in ['legacy','shear-G','projected-energy','centerline-energy']:
        pair=build_pair();micro=TipRelief(p=1)
        model=GearContactModel(pair,micro,micro,compliance_variant=variant)
        cases={'unmodified':None,**{name:np.array([s['d_um']*.001,rt_to_sa(s['rt_mm'],pair.g1),0,.5]) for name,s in SOLUTIONS.items()}}
        for torque in TORQUES:
            op=BatchedGapOperator(model,torque,240)
            for name,theta in cases.items():
                result=op.evaluate(theta,theta)
                pp=float(np.ptp(result['prediction'])*1000);ref=REFERENCE_PP[(name,torque)]
                rows.append(dict(variant=variant,case=name,torque_Nm=torque,model_pp_um=pp,reference_fe_pp_um=ref,
                                 absolute_difference_um=pp-ref,difference_percent=100*(pp-ref)/ref,
                                 unmodified_normalized_percent=100*(pp-ref)/REFERENCE_PP[('unmodified',torque)],
                                 force_residual_N=result['force_residual_N'],monotonicity_margin_mm_N=op.monotonicity_margin))
                print(variant,name,torque,round(pp,6),round(100*(pp-ref)/ref,3),flush=True)
        # All geometries same in this benchmark, including both-relief operation.
        original=TransmissionError(model).compute_cycle(500,120,theta1=cases['Sol2'],theta2=cases['Sol2'])
        fast=BatchedGapOperator(model,500,120).evaluate(cases['Sol2'],cases['Sol2'])
        equivalence.append(dict(variant=variant,max_TE_difference_mm=float(np.max(np.abs(original['TE_lin_fluct']-fast['prediction'])))))
    report=dict(provenance=provenance(),source_url=REFERENCE_SOURCE,n_positions=240,
                criterion_note='5% is an internal research target, not a journal or ISO requirement.',
                geometry=dict(alpha_deg=20,alpha_w_deg=float(np.rad2deg(pair.alpha_w)),contact_ratio=float(pair.eps_alpha),
                              profile_shift=0,pitch_thickness_mm=3.78,center_distance_mm=150,
                              note='Explicit tip diameter and circular thickness; zero stored profile shift is not a manufacturing reconstruction.'),
                ablation_sources=['https://www.mdpi.com/2076-3417/11/11/4960'],
                results=rows,equivalence=equivalence)
    (OUT/'forward_ablation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for variant in ['legacy','shear-G','projected-energy','centerline-energy']:
        rr=[r for r in rows if r['variant']==variant];x=np.arange(12)
        axes[0].plot(x,[r['difference_percent'] for r in rr],'.-',label=variant)
        axes[1].plot(x,[r['absolute_difference_um'] for r in rr],'.-',label=variant)
    axes[0].axhspan(-5,5,color='gray',alpha=.15);axes[0].set_ylabel('Difference / case FE peak-to-peak (%)')
    axes[1].set_ylabel('Signed peak-to-peak difference (µm)')
    for ax in axes:
        ax.set_xticks(x,[f"{r['case']}\n{r['torque_Nm']:.0f}" for r in rr],rotation=70,fontsize=7)
        ax.set_xlabel('Geometry and torque (Nm)');ax.grid(alpha=.2)
    axes[0].legend(fontsize=8);fig.tight_layout();fig.savefig(OUT/'forward_ablation.png',dpi=160);plt.close(fig)
    print('Equivalence',equivalence,flush=True)

if __name__=='__main__':main()
