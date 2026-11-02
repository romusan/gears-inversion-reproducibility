"""Distance from a synthetic relief response to the addendum-only response set.

New deterministic same-operator controls, not FE/experimental validation or a
calibrated hypothesis test. Every attempted fit and source hash is retained.
"""
import sys,json,hashlib,time,platform
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
import scipy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
BASE=Path(__file__).resolve().parent; ROOT=BASE.parent
SRC=ROOT/'deposit_v6/gear_inverse_identifiability/src'
sys.path.insert(0,str(SRC))
from geometry.involute import InvoluteGear,GearPair
from geometry.microgeometry import TipRelief
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator
OUT=ROOT/'revision_14_2026-11-01'; OUT.mkdir(exist_ok=True)
SCALE=np.array([.05,1,.01,1]); SIGMA=.0001
def rms(x):return float(np.sqrt(np.mean(np.asarray(x)**2)))
def main():
    t0=time.time();rows=[]
    rng=np.random.default_rng(20261101)
    starts=[np.array([.02,.75]),np.array([.03,.65]),np.array([.015,.85])]
    starts += [np.array([rng.uniform(.001,.09),rng.uniform(.31,.94)]) for _ in range(3)]
    for variant in ['legacy','shear-G','projected-energy','centerline-energy']:
        model=GearContactModel(GearPair(InvoluteGear(24,3,20,20),InvoluteGear(48,3,20,20)),micro1=TipRelief(),compliance_variant=variant)
        dense=BatchedGapOperator(model,300,n_positions=960)
        for sd in [.25,.4]:
            truth=np.array([.02,.75,.005,sd]);zero=truth.copy();zero[2]=0
            for n,offset in [(120,0),(120,.5),(240,0),(480,0)]:
                phases=(np.arange(n)+offset)/n*2*np.pi/24
                op=BatchedGapOperator(model,300,phi_positions=phases)
                result=op.evaluate(truth,jacobian=True);y=result['prediction']
                signal=y-op.evaluate(zero)['prediction']; attempts=[]
                for start in starts:
                    cache={}
                    def ev(q):
                        if 'q' not in cache or not np.array_equal(q,cache['q']):
                            theta=np.array([*(q*SCALE[:2]),0.,.5]);r=op.evaluate(theta,jacobian=True)
                            cache.update(q=q.copy(),theta=theta,pred=r['prediction'],J=r['jacobian'][:,:2]*SCALE[:2]/SIGMA)
                        return cache
                    sol=least_squares(lambda q:(ev(q)['pred']-y)/SIGMA,start/SCALE[:2],jac=lambda q:ev(q)['J'],bounds=(np.array([0,.3])/SCALE[:2],np.array([.1,.95])/SCALE[:2]),max_nfev=1200,ftol=1e-11,xtol=1e-12,gtol=1e-9)
                    r=ev(sol.x)
                    attempts.append(dict(start=start.tolist(),theta=r['theta'].tolist(),chi2=float(2*sol.cost),success=bool(sol.success),nfev=int(sol.nfev),optimality=float(sol.optimality)))
                best=min(attempts,key=lambda x:x['chi2']);est=np.array(best['theta'])
                residual=y-op.evaluate(est)['prediction']
                # Local addendum tangent projection of the isolated signal.
                J0=op.evaluate(zero,jacobian=True)['jacobian'][:,:2]*SCALE[:2]
                projected=signal-J0@np.linalg.lstsq(J0,signal,rcond=1e-12)[0]
                reference=dense.evaluate(truth)['prediction']
                held=dense.evaluate(est)['prediction']
                # Independent force engine and finite-difference tangent checks.
                check=BatchedGapOperator(model,300,phi_positions=phases,force_engine='iterative')
                engine_error=1000*rms(check.evaluate(truth)['prediction']-y)
                steps=[1e-7,1e-6,1e-7,1e-6];fd_errors=[]
                for j,h in enumerate(steps):
                    plus=truth.copy();minus=truth.copy();plus[j]+=h;minus[j]-=h
                    fd=(op.evaluate(plus)['prediction']-op.evaluate(minus)['prediction'])/(2*h)
                    fd_errors.append(float(np.linalg.norm(fd-result['jacobian'][:,j])/max(np.linalg.norm(fd),1e-14)))
                row=dict(variant=variant,truth=truth.tolist(),n=n,phase_offset_steps=offset,torque_Nm=300,sigma_um=.1,isolated_signal_rms_um=1000*rms(signal),restricted_residual_rms_um=1000*rms(residual),local_projected_signal_rms_um=1000*rms(projected),normalized_distance_120=120*(rms(residual)/SIGMA)**2,heldout_960_residual_rms_um=1000*rms(reference-held),best=best,attempts=attempts,force_residual_N=result['force_residual_N'],engine_difference_rms_um=engine_error,jacobian_relative_errors=fd_errors)
                assert row['restricted_residual_rms_um']<=row['isolated_signal_rms_um']+1e-8
                rows.append(row)
                (OUT/'restricted_distance_records.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
                print(variant,sd,n,offset,'signal',row['isolated_signal_rms_um'],'distance',row['restricted_residual_rms_um'],flush=True)
    report=dict(scope='Same-operator noiseless analytical controls. Distance at fixed 120-observation normalization is descriptive, not a significance test. Six bounded local starts including truth addendum; no global minimum certificate.',python=sys.version,platform=platform.platform(),numpy=np.__version__,scipy=scipy.__version__,seed=20261101,source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),SRC/'mechanics/batched_operator.py',SRC/'mechanics/compliance.py',SRC/'geometry/microgeometry.py']},cells=len(rows),attempts=sum(len(r['attempts']) for r in rows),failed_attempts=sum(not a['success'] for r in rows for a in r['attempts']),max_force_residual_N=max(r['force_residual_N'] for r in rows),max_engine_difference_rms_um=max(r['engine_difference_rms_um'] for r in rows),max_jacobian_relative_error=max(max(r['jacobian_relative_errors']) for r in rows),elapsed_seconds=time.time()-t0)
    (OUT/'restricted_distance_summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    plt.rcParams.update({'font.size':11})
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    labels=['Baseline','Shear G','Radial energy','Centre line']
    for ax,sd in zip(axes,[.25,.4]):
        rr=[r for r in rows if r['truth'][3]==sd and r['n']==120 and r['phase_offset_steps']==0]
        x=np.arange(4)
        ax.bar(x-.18,[r['isolated_signal_rms_um'] for r in rr],.36,label='Isolated signal')
        ax.bar(x+.18,[r['restricted_residual_rms_um'] for r in rr],.36,label='After addendum refit')
        ax.set_xticks(x,labels,rotation=23);ax.set_ylabel('Centred response RMS (µm)');ax.set_title(f'Dedendum start {sd:.2f}');ax.grid(axis='y',alpha=.2)
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',ncol=2,fontsize=10,frameon=False)
    fig.tight_layout(rect=(0,0,1,.9));fig.savefig(BASE/'assets/fig_restricted_distance_v14.png',dpi=240);plt.close(fig)
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
