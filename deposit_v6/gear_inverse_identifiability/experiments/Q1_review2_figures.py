"""Align model legend labels with the second-review tables."""
import json
import numpy as np
import matplotlib.pyplot as plt
from Q1_review2_diagnostics import OLD,OUT

def main():
    rows=json.loads((OLD/'forward_ablation.json').read_text())['results']
    names={'legacy':'Baseline','shear-G':'G shear','projected-energy':'Radial energy','centerline-energy':'Centre-line'}
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for variant,label in names.items():
        rr=[r for r in rows if r['variant']==variant];x=np.arange(len(rr))
        axes[0].plot(x,[r['difference_percent'] for r in rr],'.-',label=label)
        axes[1].plot(x,[r['absolute_difference_um'] for r in rr],'.-',label=label)
    axes[0].axhspan(-5,5,color='gray',alpha=.15);axes[0].set_ylabel('Difference / case FE peak-to-peak (%)')
    axes[1].set_ylabel('Signed peak-to-peak difference (µm)')
    for ax in axes:
        ax.set_xticks(x,[f"{r['case']}\n{r['torque_Nm']:.0f}" for r in rr],rotation=70,fontsize=7)
        ax.set_xlabel('Case and torque (Nm)');ax.grid(alpha=.2)
    axes[0].legend(fontsize=8);fig.tight_layout();fig.savefig(OUT/'forward_ablation.png',dpi=160);plt.close(fig)
if __name__=='__main__':main()
