"""Publication labels and consistent quantile colors; no numerical reruns."""
import json
import numpy as np
import matplotlib.pyplot as plt
from Q1_identifiability_campaign import OUT

def main():
    labels={'single300':'300 Nm','multi50_300':'50/300 Nm'}
    colors={'single300':'tab:blue','multi50_300':'tab:orange'}
    rows=json.loads((OUT/'monte_carlo_summary.json').read_text())['summary']
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for ax,sd in zip(axes,[.25,.4]):
        for name in labels:
            g=[r for r in rows if r['sd_true']==sd and r['design']==name]
            ax.plot([r['sigma_um'] for r in g],[r['dedendum_scaled_error']['median'] for r in g],'o-',color=colors[name],label=labels[name])
            ax.plot([r['sigma_um'] for r in g],[r['dedendum_scaled_error']['p90'] for r in g],':',color=colors[name])
        ax.set_xlabel('Noise σ (µm)');ax.set_ylabel('Scaled dedendum error');ax.set_title(f'True $s_d$ = {sd}');ax.legend(fontsize=8);ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(OUT/'monte_carlo.png',dpi=160);plt.close(fig)
    records=json.loads((OUT/'profile_likelihood.json').read_text())['records']
    fig,axes=plt.subplots(2,2,figsize=(11,7))
    for i,sd in enumerate([.25,.4]):
        for j,param in enumerate(['sd','Cd']):
            ax=axes[i,j]
            for r in records:
                if r['sd_true']==sd and r['parameter']==param:
                    factor=1000 if param=='Cd' else 1
                    ax.plot([t['value']*factor for t in r['rows']],[t['delta_chi2'] for t in r['rows']],label=labels[r['design']],color=colors[r['design']])
            ax.axhline(3.841,color='k',ls='--');ax.set_ylim(0,15);ax.set_xlabel('$s_d$' if param=='sd' else '$C_d$ (µm)')
            ax.set_ylabel('Profile Δχ²');ax.set_title(f'True $s_d$ = {sd}');ax.legend(fontsize=8);ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(OUT/'profile_likelihood.png',dpi=160);plt.close(fig)

if __name__=='__main__':main()
