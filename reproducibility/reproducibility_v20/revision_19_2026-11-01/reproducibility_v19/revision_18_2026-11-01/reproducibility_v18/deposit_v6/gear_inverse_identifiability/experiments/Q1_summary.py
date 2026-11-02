"""Final paired summaries and reproducibility checks for the new campaign."""
import json,csv
from pathlib import Path
import numpy as np
from Q1_identifiability_campaign import OUT,provenance

def main():
    rr=[json.loads(s) for s in (OUT/'monte_carlo_records.jsonl').read_text().splitlines() if s.strip()]
    keys=[(r['sd_true'],r['design'],r['sigma_um'],r['seed']) for r in rr]
    assert len(keys)==len(set(keys))==1200,'Incomplete or duplicate Monte Carlo records'
    paired=[];rng=np.random.default_rng(10312026)
    for sd in [.25,.4]:
        for sigma in [.1,.5,1]:
            by_design={name:{r['seed']:r for r in rr if r['sd_true']==sd and r['sigma_um']==sigma and r['design']==name}
                       for name in ['single300','multi50_300']}
            assert all(len(v)==100 for v in by_design.values())
            indices=rng.integers(0,100,size=(5000,100))
            record=dict(sd_true=sd,sigma_um=sigma,n_pairs=100,bootstrap_replicates=5000)
            for metric in ['addendum_scaled_error','dedendum_scaled_error','full_profile_rmse_um','heldout200_rmse_um']:
                d=np.array([by_design['multi50_300'][seed][metric]-by_design['single300'][seed][metric] for seed in range(100)])
                boot=np.median(d[indices],axis=1)
                record[metric]=dict(median_paired_difference=float(np.median(d)),bootstrap_percentile_95=np.quantile(boot,[.025,.975]).tolist(),
                                    fraction_multi_lower=float(np.mean(d<0)))
            paired.append(record)
    meta=json.loads((OUT/'support_transition.json').read_text())['provenance']
    (OUT/'paired_comparison.json').write_text(json.dumps(dict(provenance=provenance(),operator_campaign_provenance=meta,
                  sign_convention='multi minus single; negative favors paired loads',
                  note='Bootstrap uncertainty for a 100-seed paired simulation statistic; not coverage of physical parameters.',records=paired),indent=2),encoding='utf-8')
    fields=['sd_true','design','sigma_um','seed','success','all_starts_success','nfev','optimality','fit_rmse_um',
            'addendum_scaled_error','dedendum_scaled_error','full_profile_rmse_um','heldout200_rmse_um']
    with (OUT/'monte_carlo_metrics.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        writer.writerows({key:r[key] for key in fields} for r in rr)
    print('Confirmed 1200 unique reconstructions; six paired 100-seed comparisons',flush=True)
if __name__=='__main__':main()
