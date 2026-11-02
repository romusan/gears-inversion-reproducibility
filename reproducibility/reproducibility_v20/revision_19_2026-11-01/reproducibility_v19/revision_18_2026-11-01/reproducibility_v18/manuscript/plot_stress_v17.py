"""Publication-size rendering of saved stress results; no simulation or fitting."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=Path(__file__).resolve().parent.parent/'revision_17_final_2026-11-01'
def main():
    rows=[json.loads(x) for x in (OUT/'stress_records.jsonl').read_text().splitlines()];assert len(rows)==500
    scenarios=['iid','correlated_iid_fit','correlated_gls_fit','gain5_iid_fit','operator_iid_fit']
    plt.rcParams.update({'font.size':14})
    fig,axes=plt.subplots(1,2,figsize=(10,4.8));labels=['IID','AR / IID fit','AR / GLS fit','Gain +5%','Operator change']
    for ax,sd in zip(axes,[.25,.4]):
        for i,c in enumerate(scenarios):
            rr=sorted([r for r in rows if r['sd_true']==sd and r['scenario']==c],key=lambda r:r['seed'])
            for kind,marker,color in [('interior','o','#2469a1'),('bound','x','#d04b29'),('failed','+','black')]:
                ss=[r for r in rr if ('failed' if not r['success'] else ('bound' if r['dedendum_bound'] else 'interior'))==kind]
                ax.scatter([i+((r['seed']%9)-4)*.017 for r in ss],[r['dedendum_scaled_error'] for r in ss],s=20,marker=marker,c=color,label=kind if i==0 else None,alpha=.75)
            med=np.median([r['dedendum_scaled_error'] for r in rr]);ax.plot([i-.22,i+.22],[med,med],'k-',lw=2)
        ax.set_xticks(range(5),labels,rotation=33,ha='right');ax.set_title(f'True dedendum start {sd}');ax.set_ylabel('Maximum scaled dedendum error');ax.grid(axis='y',alpha=.2)
    handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',ncol=3,frameon=False)
    fig.tight_layout(rect=(0,0,1,.88));fig.savefig(OUT/'stress_v17.png',dpi=300);plt.close(fig)
    (OUT/'plot_provenance_v17.json').write_text(json.dumps({'records_sha256':hashlib.sha256((OUT/'stress_records.jsonl').read_bytes()).hexdigest(),'plot_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'image_sha256':hashlib.sha256((OUT/'stress_v17.png').read_bytes()).hexdigest(),'data_unchanged':True,'font_points_at_16cm_width':14*16/2.54/10},indent=2))
if __name__=='__main__':main()
