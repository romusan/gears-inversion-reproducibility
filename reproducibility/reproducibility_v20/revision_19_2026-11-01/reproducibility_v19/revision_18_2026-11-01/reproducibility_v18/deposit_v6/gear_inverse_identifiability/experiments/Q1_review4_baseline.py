import json
import numpy as np
from pathlib import Path
from Q1_forward_campaign import build_pair,TipRelief,GearContactModel,BatchedGapOperator
from campaign_provenance import provenance
OUT=Path(__file__).resolve().parents[1]/'results/q1_review4_2026-10-12'
ROOT=Path(__file__).resolve().parents[2]
fe=json.loads((ROOT/'fe2d/results/transition_checks.json').read_text())
phases=sorted([0,.5]+[r['phase_fraction'] for r in fe['records']])
pair=build_pair();model=GearContactModel(pair,TipRelief(p=1))
op=BatchedGapOperator(model,650,phi_positions=np.array(phases)*2*np.pi/57);r=op.evaluate()
_,t=op.elastic(r['forces']);active=(r['forces']>1e-8)&op.valid;k=np.where(active,1/t,0).sum(axis=1)/1000
rows=[dict(phase_fraction=f,approach_um=float(d*1000),k_N_um=float(kk),k_per_width_N_mm_um=float(kk/23),loaded_pairs=int(n)) for f,d,kk,n in zip(phases,r['delta'],k,active.sum(axis=1))]
dense=BatchedGapOperator(model,650,1920).evaluate()
(OUT/'matched_baseline.json').write_text(json.dumps(dict(provenance=provenance(),records=rows,full_cycle_pp_um=float(np.ptp(dense['delta'])*1000),positions_full_cycle=1920),indent=2))
print('Matched baseline saved')
