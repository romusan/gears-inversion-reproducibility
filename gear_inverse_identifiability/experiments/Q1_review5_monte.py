"""Nonlinear complementary-phase control, same 120-observation budget."""
import json,time,argparse,concurrent.futures as cf
from pathlib import Path
import numpy as np
from Q1_identifiability_campaign import InvoluteGear,GearPair,TipRelief,GearContactModel,BatchedGapOperator,bestfit,predict,SCALE,STARTS
from campaign_provenance import provenance
OUT=Path(__file__).resolve().parents[1]/'results/q1_review5_2026-10-12';OUT.mkdir(exist_ok=True)
OLD=OUT.parent/'q1_revision_2026-10-12';OPS=None

def getops(engine='lambert'):
    pair=GearPair(InvoluteGear(24,3,20,20),InvoluteGear(48,3,20,20));model=GearContactModel(pair,TipRelief())
    phi=pair.rotation_for_mesh(120)[0]
    return [BatchedGapOperator(model,T,phi_positions=p,force_engine=engine) for T,p in [(50,phi[::2]),(300,phi[1::2])]]

def one(task):
    global OPS
    if OPS is None:OPS=getops()
    sd,sig,seed=task;truth=np.array([.02,.75,.005,sd]);noise=np.random.default_rng(seed).normal(0,sig*.001,120)
    # Match random errors to canonical physical phase, not concatenated row number.
    y=predict(OPS,truth)+np.r_[noise[::2],noise[1::2]]
    r=bestfit(OPS,y,sig*.001);err=abs(np.array(r['theta'])-truth)/SCALE
    return dict(sd_true=sd,sigma_um=sig,seed=seed,design='50_even_300_odd',
        addendum_scaled_error=float(err[:2].max()),dedendum_scaled_error=float(err[2:].max()),**r)

def summarize(records):
    baseline=[json.loads(s) for s in (OLD/'monte_carlo_records.jsonl').read_text().splitlines() if s.strip()]
    rows=[];rng=np.random.default_rng(20261012)
    for sd in [.25,.4]:
        for sig in [.1,.5,1]:
            new=sorted([r for r in records if r['sd_true']==sd and r['sigma_um']==sig],key=lambda r:r['seed'])
            old=sorted([r for r in baseline if r['sd_true']==sd and r['sigma_um']==sig and r['design']=='single300'],key=lambda r:r['seed'])
            assert len(new)==len(old)==100
            assert [r['seed'] for r in old]==[r['seed'] for r in new]
            a=np.array([r['dedendum_scaled_error'] for r in old]);b=np.array([r['dedendum_scaled_error'] for r in new]);delta=b-a
            boot=np.median(delta[rng.integers(0,100,(5000,100))],axis=1)
            rows.append(dict(sd_true=sd,sigma_um=sig,n=100,new_success=sum(r['success'] for r in new),
                single300_median=float(np.median(a)),complementary_median=float(np.median(b)),
                complementary_p90=float(np.quantile(b,.9)),median_paired_difference=float(np.median(delta)),
                bootstrap_percentile_95=np.quantile(boot,[.025,.975]).tolist(),fraction_pair_better=float(np.mean(delta<0))))
    return rows

def main(workers):
    # Verify the new faster force engine on truth and both truth-independent starts.
    a=getops();b=getops('iterative');checks=[]
    for theta in [np.array([.02,.75,.005,s]) for s in [.25,.4]]+STARTS:
        for x,z in zip(a,b):
            r=x.evaluate(theta,jacobian=True);v=z.evaluate(theta,jacobian=True)
            checks.append(dict(max_prediction_difference_mm=float(np.max(abs(r['prediction']-v['prediction']))),max_jacobian_difference=float(np.max(abs(r['jacobian']-v['jacobian'])))))
    assert all(r['max_prediction_difference_mm']<1e-11 and r['max_jacobian_difference']<1e-8 for r in checks)
    path=OUT/'complementary_monte_records.jsonl';records=[]
    if path.exists():records=[json.loads(s) for s in path.read_text().splitlines() if s.strip()]
    done={(r['sd_true'],r['sigma_um'],r['seed']) for r in records}
    tasks=[(sd,sig,seed) for sd in [.25,.4] for sig in [.1,.5,1] for seed in range(100) if (sd,sig,seed) not in done]
    start=time.time()
    with path.open('a',encoding='utf-8') as f,cf.ProcessPoolExecutor(max_workers=workers) as pool:
        for r in pool.map(one,tasks,chunksize=1):
            records.append(r);f.write(json.dumps(r)+'\n');f.flush()
            if len(records)%25==0:print('Completed',len(records),'of 600, seconds',round(time.time()-start),flush=True)
    report=dict(provenance=provenance(),records=len(records),summary=summarize(records),engine_equivalence=checks,
        noise_policy='Same independent errors assigned to canonical 120-position phase indices; paired by seed to the stored single300 experiment.',
        design='50 Nm at even indices, 300 Nm at odd indices; 60 observations each, centred separately.',
        optimizer='Same two fixed starts, bounds, scales and fit tolerances as the original campaign; all selected fits including failures retained.',
        force_engine='Lambert W, verified against iterative for truths and starts; old single300 records use iterative.')
    (OUT/'complementary_monte_summary.json').write_text(json.dumps(report,indent=2))
    print('MC complete',json.dumps(report['summary']),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--workers',type=int,default=4);a=p.parse_args();main(a.workers)
