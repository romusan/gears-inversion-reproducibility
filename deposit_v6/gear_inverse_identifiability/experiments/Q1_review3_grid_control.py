"""Separate phase-grid, centring and load-allocation effects in local information.

Dense common-grid scores are quadrature approximations normalized to a budget
of 120, not Monte Carlo data sets with 120 physical observations.
"""
import sys,json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from geometry.involute import InvoluteGear,GearPair
from geometry.microgeometry import TipRelief
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator
from campaign_provenance import provenance
OUT=Path(__file__).resolve().parents[1]/'results'/'q1_review3_2026-10-12';OUT.mkdir(exist_ok=True)
SCALE=np.array([.05,1,.01,1]);SIGMA=.0001

def score(J):
    s=np.linalg.svd(J,compute_uv=False)
    return dict(singular_values=s.tolist(),sigma4=float(s[-1]),lambda_min=float(s[-1]**2),rank=int(np.sum(s>s[0]*1e-7)))

def main():
    pair=GearPair(InvoluteGear(24,3,20,20),InvoluteGear(48,3,20,20))
    model=GearContactModel(pair,TipRelief());common=[];actual=[]
    for sd in [.25,.4]:
        theta=np.array([.02,.75,.005,sd])
        for n in [60,120,240,480,960]:
            Js={};support={}
            for T in [50,300]:
                op=BatchedGapOperator(model,T,n);res=op.evaluate(theta,jacobian=True)
                Js[T]=res['jacobian']*SCALE/SIGMA
                mask=(res['forces']>1e-8)&op.valid
                support[T]=dict(min_loaded_xi=float(op.xi1[mask].min()),relief_contact_count=int(np.sum(op.xi1[mask]<sd)))
            # One equally sampled cycle per load; divide sums by n and apply
            # explicit allocation weights before SVD.
            single=score(Js[300]*np.sqrt(120/n))
            paired=score(np.vstack([Js[50],Js[300]])*np.sqrt(60/n))
            low=score(Js[50]*np.sqrt(120/n))
            lower=.5*(single['lambda_min']+low['lambda_min'])
            assert paired['lambda_min'] >= lower-1e-10
            common.append(dict(sd_true=sd,n_phase_nodes=n,budget_equivalent=120,
                single300=single,pair50_300=paired,single50=low,psd_lower_bound=lower,
                psd_margin=paired['lambda_min']-lower,support=support))
            print('common',sd,n,single['sigma4'],paired['sigma4'],flush=True)
        # Actual 120-sample designs, including duplicated and complementary phases.
        phi120=pair.rotation_for_mesh(120)[0]
        phi60=pair.rotation_for_mesh(60)[0]
        specs={'single300_120':[(300,phi120)],
               'pair_original60':[(50,phi60),(300,phi60)],
               'repeat300_original60':[(300,phi60),(300,phi60)],
               'pair_same60':[(50,phi120[::2]),(300,phi120[::2])],
               'repeat300_same60':[(300,phi120[::2]),(300,phi120[::2])],
               'pair_interleaved_A':[(50,phi120[::2]),(300,phi120[1::2])],
               'pair_interleaved_B':[(50,phi120[1::2]),(300,phi120[::2])],
               'repeat300_interleaved':[(300,phi120[::2]),(300,phi120[1::2])]}
        for name,spec in specs.items():
            J=[];support=[]
            for T,phi in spec:
                op=BatchedGapOperator(model,T,phi_positions=phi);res=op.evaluate(theta,jacobian=True)
                J.append(res['jacobian']*SCALE/SIGMA);mask=(res['forces']>1e-8)&op.valid
                support.append(dict(torque=T,n=len(phi),min_loaded_xi=float(op.xi1[mask].min()),relief_contact_count=int(np.sum(op.xi1[mask]<sd))))
            actual.append(dict(sd_true=sd,design=name,n_observations=120,**score(np.vstack(J)),support=support))
    report=dict(provenance=provenance(),common_grid=common,actual_designs=actual,
                centring='Each load-cycle Jacobian is centred over its sampled phase grid; repeated cycles have separate means.',
                interpretation='Common-grid normalized scores isolate phase quadrature from allocation; actual complementary grids retain 120 observations but redistribute their phases and their cycle means.')
    (OUT/'grid_control.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,sd in zip(axes,[.25,.4]):
        rr=[r for r in common if r['sd_true']==sd]
        for key,label in [('single300','300 Nm'),('pair50_300','50/300 Nm')]:
            ax.plot([r['n_phase_nodes'] for r in rr],[r[key]['sigma4'] for r in rr],'o-',label=label)
        ax.set_xscale('log',base=2);ax.set_xlabel('Shared phase quadrature nodes');ax.set_ylabel('Budget-normalized σ₄');ax.set_title(f'True $s_d$ = {sd}');ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.tight_layout();fig.savefig(OUT/'common_grid.png',dpi=160);plt.close(fig)
    print('actual',[(r['sd_true'],r['design'],r['sigma4']) for r in actual],flush=True)
if __name__=='__main__':main()
