"""Regenerate campaign figures and parameter-block metrics from records."""
import json,csv
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from campaign_provenance import provenance

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from geometry.microgeometry import TipRelief
OUT=ROOT/'results'/'corrections_2026-10-12'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    summaries={};csv_rows=[]
    for name,expected in [('E04',36),('E07',40),('E08',24)]:
        records=[json.loads(l) for l in (ROOT/'results'/f'{name}_records.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
        summaries[name]={'records':len(records),'expected':expected,
                         'optimizer_success':sum(r['success'] for r in records),
                         'versioned':sum('provenance' in r for r in records)}
        for r in records:
            error=np.asarray(r.get('param_norm_err',r['param_rel_err']))
            truth=np.asarray(r.get('theta_true',[0.020,0.75,0.005,0.25]))
            sd_degenerate=bool(truth[2]==0)
            xi=np.linspace(0,1,1001)
            delta_profile=TipRelief(p=2).evaluate(xi,np.asarray(r['theta_est']))-TipRelief(p=2).evaluate(xi,truth)
            csv_rows.append(dict(experiment=name,case=r['case'],generator=r.get('gen',''),inverse=r.get('inv',''),
                                 geometry=r.get('geom',''),modification=r.get('mod',''),sigma_um=r.get('sigma_um',''),
                                 gamma=r.get('gamma',''),seed=r.get('seed',''),success=r['success'],
                                 jacobian_scheme=r.get('jacobian_scheme','not_recorded'),
                                 addendum_max_error=float(max(error[:2])),dedendum_max_error=float(max(error[2:])),
                                 error_metric='normalized' if 'param_norm_err' in r else 'relative',
                                 sd_degenerate_at_truth=sd_degenerate,
                                 max_error_excluding_exact_sd_degeneracy=float(max(error[:3] if sd_degenerate else error)),
                                 full_flank_profile_rms_um=float(np.sqrt(np.mean(delta_profile**2))*1e3),
                                 fit_rmse_um=r['fit_rmse_mm']*1e3,versioned='provenance' in r))
    with (OUT/'parameter_block_metrics.csv').open('w',encoding='utf-8-sig',newline='') as out:
        writer=csv.DictWriter(out,fieldnames=list(csv_rows[0]));writer.writeheader();writer.writerows(csv_rows)
    fig,axes=plt.subplots(1,2,figsize=(11,4.5))
    for name,marker in [('E04','o'),('E07','s')]:
        rr=[r for r in csv_rows if r['experiment']==name]
        for j,key in enumerate(['addendum_max_error','dedendum_max_error']):
            axes[j].scatter([r['fit_rmse_um'] for r in rr],[max(r[key],1e-12) for r in rr],marker=marker,alpha=.65,label=name)
            axes[j].set_xscale('log');axes[j].set_yscale('log')
            axes[j].set_xlabel('Fit RMSE (µm)');axes[j].set_ylabel('Maximum relative error')
            axes[j].set_title(['Addendum Ca, sa','Dedendum Cd, sd'][j]);axes[j].legend()
    fig.tight_layout();fig.savefig(OUT/'parameter_block_errors.png',dpi=180);plt.close(fig)
    path=OUT/'E03_sampling_audit.json'
    if path.exists():
        report=json.loads(path.read_text())
        fig,axes=plt.subplots(1,2,figsize=(11,4.5))
        grids=report['grids'];rr=report['records']
        axes[0].plot([r['n_positions'] for r in grids],[r['rank'] for r in grids],'o-')
        axes[0].set_xlabel('Observation positions');axes[0].set_ylabel('Numerical rank');axes[0].set_ylim(1.5,4.5)
        for n in [30,60,120]:
            selected=[r for r in rr if r['n_positions']==n]
            axes[1].scatter([max(r['fit_rmse_um'],1e-14) for r in selected],
                            [max(r['heldout_dense_rmse_um'],1e-14) for r in selected],label=f'{n} points')
        axes[1].set_xscale('log');axes[1].set_yscale('log');axes[1].set_xlabel('Fit RMSE (µm)')
        axes[1].set_ylabel('240-point held-out RMSE (µm)');axes[1].legend()
        fig.tight_layout();fig.savefig(OUT/'E03_sampling_audit.png',dpi=180);plt.close(fig)
    (OUT/'campaign_summary.json').write_text(json.dumps(dict(provenance=provenance(),experiments=summaries),indent=2),encoding='utf-8')
    print(summaries,flush=True)

if __name__=='__main__':main()
