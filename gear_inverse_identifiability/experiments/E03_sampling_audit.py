"""Separate coarse observation ambiguity from dense-grid weak sensitivity.
Fresh nonlinear model; seeded starts; dense validation held out from fitting.
"""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from E04_noise_bias import build_model,THETA_TRUE,BOUNDS,SCALE
from inverse.reconstruction import InverseReconstructor
from identifiability.fisher_optimal_loads import FisherLoadSelector
from campaign_provenance import provenance
from E05_fixed_budget import OUT,clean

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    te=build_model()
    selector=FisherLoadSelector(te,THETA_TRUE,parameter_scale=SCALE,sigma_mm=1e-4)
    no_root=THETA_TRUE.copy();no_root[3]=0.15
    dense_truth=te.compute_cycle(100,240,THETA_TRUE)['TE_lin_fluct']
    rng=np.random.default_rng(20261012)
    initials=[THETA_TRUE*np.array([1.3,0.9,2,1.2])]+[rng.uniform(BOUNDS[:,0],BOUNDS[:,1]) for _ in range(3)]
    audits=[]
    for n in [20,30,60,120,240]:
        truth=te.compute_cycle(100,n,THETA_TRUE)['TE_lin_fluct']
        candidate=te.compute_cycle(100,n,no_root)['TE_lin_fluct']
        info=selector.diagnostics([100],total_observations=n)
        audits.append(dict(n_positions=n,rank=info['rank'],singular_values=info['singular_values'],
                           root_change_rmse_um=float(np.sqrt(np.mean((truth-candidate)**2))*1e3)))
        print('sampling',n,audits[-1],flush=True)
    records=[]
    record_path=OUT/'E03_sampling_records.jsonl'
    done=set()
    if record_path.exists():
        records=[json.loads(l) for l in record_path.read_text().splitlines() if l.strip()]
        done={(r['n_positions'],r['start_id']) for r in records}
    stamp=provenance()
    for n in [30,60,120]:
        truth=te.compute_cycle(100,n,THETA_TRUE)['TE_lin_fluct']
        recon=InverseReconstructor(te,[100],BOUNDS,theta_scale=SCALE,n_positions_forward=n)
        for sid,initial in enumerate(initials):
            if (n,sid) in done:continue
            result=recon.reconstruct(truth,theta0=initial,max_nfev=200)
            dense_est=te.compute_cycle(100,240,result['theta'])['TE_lin_fluct']
            row=dict(n_positions=n,start_id=sid,theta0=initial,theta_est=result['theta'],
                     success=bool(result['success']),nfev=int(result['nfev']),
                     fit_rmse_um=result['rmse']*1e3,
                     heldout_dense_rmse_um=float(np.sqrt(np.mean((dense_est-dense_truth)**2))*1e3),
                     error_scaled=(result['theta']-THETA_TRUE)/SCALE,provenance=stamp)
            row=clean(row);records.append(row)
            with record_path.open('a',encoding='utf-8') as out:out.write(json.dumps(row,allow_nan=False)+'\n')
            print('recovery',n,sid,row['fit_rmse_um'],row['heldout_dense_rmse_um'],flush=True)
    (OUT/'E03_sampling_audit.json').write_text(json.dumps(clean(dict(provenance=stamp,grids=audits,records=records,
        description='Four seeded starts per grid; 240-point held-out validation; does not prove global uniqueness.')),indent=2,allow_nan=False),encoding='utf-8')

if __name__=='__main__':main()
