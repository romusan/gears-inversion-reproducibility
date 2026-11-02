"""Publication figure of saved stress errors; logarithmic scale, explicit n."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=Path(__file__).resolve().parent.parent/'revision_18_2026-11-01'
def main():
    rows=[json.loads(x) for x in (OUT/'derived_records.jsonl').read_text().splitlines()];assert len(rows)==1100 and all(r['dedendum_error']>0 for r in rows)
    scenarios=['iid','correlated_iid_fit','correlated_gls_fit','correlated_fgls_fit','gain5_iid_fit','operator_iid_fit','rotation_harmonics','tooth_harmonic']
    labels=['IID','AR / IID','AR / GLS','AR / FGLS','Gain +5%','Operator','1× + 2× rot.','Tooth pass']
    plt.rcParams.update({'font.size':14});fig,axes=plt.subplots(1,2,figsize=(11,5.5))
    for ax,sd in zip(axes,[.25,.4]):
        ticklabels=[]
        for i,c in enumerate(scenarios):
            rr=sorted([r for r in rows if r['sd_true']==sd and r['scenario']==c],key=lambda r:r['seed']);ticklabels.append(labels[i]+f' ({len(rr)})')
            for kind,marker,color in [('interior','o','#2469a1'),('bound','x','#d04b29'),('failed','+','black')]:
                ss=[r for r in rr if ('failed' if not r['success'] else ('bound' if r['dedendum_bound'] else 'interior'))==kind]
                ax.scatter([i+((r['seed']%11)-5)*.023 for r in ss],[r['dedendum_error'] for r in ss],s=13,marker=marker,c=color,label=kind if i==0 else None,alpha=.7)
            m=np.median([r['dedendum_error'] for r in rr]);ax.plot([i-.3,i+.3],[m,m],'k-',lw=2)
        ax.set_yscale('log');ax.set_xticks(range(8),ticklabels,rotation=53,ha='right');ax.set_title(f'True dedendum start {sd}');ax.set_ylabel('Maximum scaled dedendum error');ax.grid(axis='y',alpha=.2,which='both')
    h,l=axes[0].get_legend_handles_labels();fig.legend(h,l,loc='upper center',ncol=3,frameon=False);fig.tight_layout(rect=(0,0,1,.88));fig.savefig(OUT/'stress_v18.png',dpi=300);plt.close(fig)
    (OUT/'plot_provenance_v18.json').write_text(json.dumps({'records_sha256':hashlib.sha256((OUT/'derived_records.jsonl').read_bytes()).hexdigest(),'plot_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'image_sha256':hashlib.sha256((OUT/'stress_v18.png').read_bytes()).hexdigest(),'log_scale':True,'numbers_in_labels':'selected case count'},indent=2))
if __name__=='__main__':main()
