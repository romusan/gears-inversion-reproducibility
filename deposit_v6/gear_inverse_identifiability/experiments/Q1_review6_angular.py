"""Angular-offset envelope; exact for the explicitly declared linear interpolant.

The FE interpolation has only eight nodes and is not a direct FE angular sweep.
"""
import json
from pathlib import Path
import numpy as np
from Q1_forward_campaign import build_pair,TipRelief,GearContactModel,BatchedGapOperator
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'revision_6_2026-10-12';OUT.mkdir(exist_ok=True)
PERIOD=360/57;STEP=.21

def envelope(x,y):
    # Fixed global sampling grid cropped to [0, one mesh period).
    # Offset spans the entire [0,step); 30 or 31 samples, with no duplicated endpoint.
    breaks=np.unique(np.r_[0,STEP,PERIOD%STEP,np.mod(x,STEP)])
    breaks=breaks[(breaks>=0)&(breaks<=STEP)]
    a,b=breaks[:-1],breaks[1:];j=np.arange(int(np.ceil(PERIOD/STEP)))
    mid=(a+b)/2;valid=mid[:,None]+STEP*j[None,:]<PERIOD
    def sample(offset):
        return np.interp(offset[:,None]+STEP*j[None,:],np.r_[x,PERIOD],np.r_[y,y[0]])
    Y0=sample(a);Y1=sample(b)
    def ranges(u):
        Y=Y0+(Y1-Y0)*u[:,None]
        return np.max(np.where(valid,Y,-np.inf),axis=1)-np.min(np.where(valid,Y,np.inf),axis=1)
    # Convex range of affine lines on each interval. Ternary search applies even at ties.
    lo=np.zeros(len(a));hi=np.ones(len(a))
    for _ in range(70):
        u=lo+(hi-lo)/3;v=hi-(hi-lo)/3;left=ranges(u)<=ranges(v)
        hi=np.where(left,v,hi);lo=np.where(left,lo,u)
    u=(hi+lo)/2;rmin=ranges(u);rmax=np.maximum(ranges(np.zeros(len(a))),ranges(np.ones(len(a))))
    index=int(np.argmin(rmin))
    return dict(min_pp_um=float(rmin.min()),max_pp_um=float(rmax.max()),
        minimum_offset_deg=float(a[index]+u[index]*(b[index]-a[index])),
        partition_intervals=len(a),sample_counts=sorted(set(valid.sum(axis=1).tolist())),
        method='All offset intervals partitioned at shifted interpolation knots and the sample-count change. Range is convex within each interval; interval maxima occur at endpoints and minima use 70 ternary steps. Bounds apply to this periodic piecewise-linear interpolant, not the unknown exact waveform.')

def main():
    pair=build_pair();model=GearContactModel(pair,TipRelief(p=1))
    reports=[]
    for n in [3840,7680,15360]:
        x=np.linspace(0,PERIOD,n,endpoint=False)
        y=BatchedGapOperator(model,650,phi_positions=np.deg2rad(x)).evaluate()['delta']*1000
        e=envelope(x,y);e.update(model='baseline',nodes=n,dense_pp_um=float(np.ptp(y)))
        reports.append(e)
        np.savez_compressed(OUT/f'baseline_{n}.npz',angle_deg=x,approach_um=y)
        print('Baseline',n,e['min_pp_um'],e['max_pp_um'],flush=True)
        (OUT/'angular_partial.json').write_text(json.dumps(reports,indent=2))
    fe=json.loads((ROOT/'fe2d/results/quadratic_eight_phases.json').read_text())
    x=np.array([r['phase_fraction'] for r in fe['records']])*PERIOD
    y=np.array([r['approach_um'] for r in fe['records']])
    e=envelope(x,y);e.update(model='FE eight-phase linear interpolant',nodes=len(x),sampled_range_um=float(np.ptp(y)))
    reports.append(e)
    (OUT/'angular_offset_control.json').write_text(json.dumps(dict(period_deg=PERIOD,step_deg=STEP,
        sampling='Grid offset in [0,0.21 deg); crop to one fixed mesh cycle, 30 or 31 samples. Cycles do not have an integer number of 0.21-degree steps.',
        results=reports,warning='Baseline envelopes are refined interpolation diagnostics. FE envelope is a sensitivity illustration of an eight-phase interpolant; it cannot measure the unresolved FE transition ramp or attribute the benchmark mismatch to angular sampling.'),indent=2))

if __name__=='__main__':main()
