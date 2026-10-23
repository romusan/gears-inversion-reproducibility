"""Angular peak convergence around contact transitions, distinct from RMS."""
import sys,json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from Q1_forward_campaign import OUT,build_pair,rt_to_sa,SOLUTIONS,TipRelief,GearContactModel,BatchedGapOperator,provenance

def main():
    rows=[];curves={}
    for variant in ['legacy','shear-G','projected-energy']:
        pair=build_pair();micro=TipRelief(p=1);model=GearContactModel(pair,micro,micro,compliance_variant=variant)
        s=SOLUTIONS['Sol2'];modified=np.array([s['d_um']*.001,rt_to_sa(s['rt_mm'],pair.g1),0,.5])
        for name,theta in [('unmodified',None),('Sol2',modified)]:
            last=None
            for n in [30,60,120,240,480,960,1920]:
                op=BatchedGapOperator(model,650,n);r=op.evaluate(theta,theta)
                pp=float(np.ptp(r['prediction'])*1000)
                rows.append(dict(variant=variant,case=name,n_positions=n,peak_to_peak_um=pp,
                                 relative_pp_change=None if last is None else abs(pp-last)/abs(last),
                                 max_force_residual_N=r['force_residual_N']))
                last=pp
                if name=='unmodified' and variant=='legacy' and n in [120,1920]:curves[n]=(op.phi,r['prediction'])
    (OUT/'angular_peak_convergence.json').write_text(json.dumps(dict(provenance=provenance(),torque_Nm=650,rows=rows),indent=2),encoding='utf-8')
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for variant in ['legacy','shear-G','projected-energy']:
        rr=[r for r in rows if r['variant']==variant and r['case']=='unmodified']
        axes[0].plot([r['n_positions'] for r in rr],[r['peak_to_peak_um'] for r in rr],'o-',label=variant)
    axes[0].set_xscale('log',base=2);axes[0].set_xlabel('Angular positions');axes[0].set_ylabel('Peak-to-peak TE (µm)');axes[0].legend(fontsize=8)
    for n,(phi,y) in curves.items():axes[1].plot(np.rad2deg(phi),y*1000,'.-',ms=2,label=f'{n} positions')
    axes[1].set_xlabel('Rotation (deg)');axes[1].set_ylabel('TE fluctuation (µm)');axes[1].legend(fontsize=8)
    for ax in axes:ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(OUT/'angular_peak_convergence.png',dpi=160);plt.close(fig)
    print(json.dumps(rows[-7:],indent=2),flush=True)
if __name__=='__main__':main()
