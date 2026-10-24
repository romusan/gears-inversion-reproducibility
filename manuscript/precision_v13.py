"""Targeted numerical controls for the eight-phase physical-removal contrast.

Alternative sparse LU ordering and residual corrections test elastic algebra.
80-digit contact polishing tests condensed-system algebra, not 80-digit FE.
Weighted harmonic morphing preserves the same boundary polygon. A halved
pressure spacing tests interface sensitivity on exactly the same phase set.
No difference between these controls is a rigorous continuum error bound.
"""
import json,time,gc
from pathlib import Path
import numpy as np
import physical_geometry_v12 as phys
from scipy.sparse.linalg import splu
from skfem import MeshTri,Basis,ElementTriP2,ElementTriP1,ElementVector,asm,BilinearForm
from skfem.helpers import dot,grad
from skfem.models.elasticity import linear_elasticity
import mpmath as mp
fe=phys.fe;ROOT=phys.ROOT;OUT=ROOT/'revision_13_2026-10-23';OUT.mkdir(exist_ok=True)
mp.mp.dps=80

def condense(K,P,D,enhanced=False):
    free=np.setdiff1d(np.arange(K.shape[0]),D);A=K[free][:,free].tocsc();B=P[free]
    lu=splu(A,permc_spec='MMD_AT_PLUS_A' if enhanced else 'COLAMD');U=lu.solve(B)
    before=float(np.linalg.norm(B-A@U)/np.linalg.norm(B))
    if enhanced:
        for _ in range(4):U+=lu.solve(B-A@U)
    after=float(np.linalg.norm(B-A@U)/np.linalg.norm(B));H=B.T@U
    return (H+H.T)/2,dict(relative_elastic_residual_before=before,relative_elastic_residual_after=after)

def matrix(body,field,depth):
    xyz=body['xyz']+field*(depth/.05)
    ratios=phys.areas(xyz,body['tri'])/phys.areas(body['xyz'],body['tri']);assert ratios.min()>0
    basis=Basis(MeshTri(xyz.T,body['tri'].T),ElementVector(ElementTriP2()))
    lam=fe.E*fe.NU/((1+fe.NU)*(1-2*fe.NU));mu=fe.E/(2*(1+fe.NU))
    return fe.WIDTH*asm(linear_elasticity(lam,mu),basis)

def weighted_field(body,original):
    boundary=body['mesh'].boundary_nodes();free=np.setdiff1d(np.arange(len(body['xyz'])),boundary)
    @BilinearForm
    def form(u,v,w):return (1+(w.x[0]**2+w.x[1]**2)/fe.RB**2)*dot(grad(u),grad(v))
    L=asm(form,Basis(body['mesh'],ElementTriP1()));field=original.copy()
    field[free]=splu(L[free][:,free].tocsc()).solve(-(L[free][:,boundary]@field[boundary]))
    assert np.array_equal(field[boundary],original[boundary])
    return field

def approach(H,g,F,enhanced=False):
    sol=fe.solve_contact(H,g,F)
    if not enhanced:return float(sol['delta'])
    ids=np.flatnonzero(sol['active']);n=len(ids);A=mp.matrix(n+1);rhs=mp.matrix(n+1,1)
    for j,i in enumerate(ids):
        for k,l in enumerate(ids):A[j,k]=mp.mpf(float(H[i,l]))
        A[j,n]=-1;A[n,j]=1;rhs[j]=-mp.mpf(float(g[i]))
    rhs[n]=mp.mpf(float(F));z=mp.lu_solve(A,rhs)
    assert min(z[i] for i in range(n))>=0
    p=np.zeros(len(g));p[ids]=[float(z[i]) for i in range(n)]
    assert np.min(H@p+g-float(z[n]))>-1e-10
    return float(z[n])

def main():
    dest=OUT/'precision_records.jsonl';records=[]
    if dest.exists():records=[json.loads(x) for x in dest.read_text().splitlines()]
    done={(r['phase_fraction'],r['mode']) for r in records}
    archive=[json.loads(x) for x in (ROOT/'revision_12_2026-10-23/physical_geometry_verified_records.jsonl').read_text().splitlines()]
    with dest.open('a',encoding='utf-8') as f:
        for phase in phys.PHASES:
            for step in [.02,.01]:
                modes=['baseline','enhanced_algebra','weighted_morph'] if step==.02 else ['fine_interface']
                if all((phase,m) in done for m in modes):continue
                t=time.time();c=fe.contacts(phase,.35,step,False)
                w=fe.mesh_body(c,2,.35,12.,.1,f'precision_w_{phase}_{step}',2,'weak_hat',.02,2)
                wH=w['H'];wHe,wdiag=condense(w['K'],w['P'],w['D'],True);del w;gc.collect()
                b=fe.mesh_body(c,1,.35,12.,.1,f'precision_p_{phase}_{step}',2,'weak_hat',.02,2)
                field,projection=phys.morph_field(b,c);weighted=weighted_field(b,field) if step==.02 else field
                g=phys.weak_gaps(c);F=300000/fe.RB
                for mode in modes:
                    if (phase,mode) in done:continue
                    enhanced=mode=='enhanced_algebra';chosen=weighted if mode=='weighted_morph' else field
                    deltas=[];diags=[]
                    for depth in [0.,.01,.05]:
                        K=matrix(b,chosen,depth);H,diag=condense(K,b['P'],b['D'],enhanced)
                        delta=approach(H+(wHe if enhanced else wH),g,F,enhanced);deltas.append(delta);diags.append(diag)
                    shifts=[1000*(v-deltas[0]) for v in deltas]
                    original=[r for r in archive if r['h_mm']==.35 and r['phase_fraction']==phase]
                    original=sorted(original,key=lambda r:r['depth_mm'])
                    rec=dict(phase_fraction=phase,h_mm=.35,mode=mode,step_mm=step,depths_mm=[0.,.01,.05],approach_changes_um=shifts,
                             nominal_reassembly_change_um=1000*(deltas[0]-approach(b['H']+wH,g,F)),
                             archive_shift_changes_um=[v-r['approach_change_um'] for v,r in zip(shifts,original)],
                             elastic_residuals=diags,wheel_enhanced_residual=wdiag,boundary_projection_mm=projection,
                             max_interior_morph_difference_mm=float(np.linalg.norm(weighted-field,axis=1).max()),seconds=time.time()-t)
                    f.write(json.dumps(rec)+'\n');f.flush();records.append(rec)
                print('precision',phase,step,round(time.time()-t,1),flush=True);del b;gc.collect()
    assert len(records)==32 and len({(r['phase_fraction'],r['mode']) for r in records})==32
    rows=[]
    for mode in ['baseline','enhanced_algebra','weighted_morph','fine_interface']:
        rr=sorted([r for r in records if r['mode']==mode],key=lambda r:r['phase_fraction'])
        for j,depth in [(1,.01),(2,.05)]:
            signal=np.array([r['approach_changes_um'][j] for r in rr]);signal-=signal.mean()
            base=np.array([r['approach_changes_um'][j] for r in sorted([v for v in records if v['mode']=='baseline'],key=lambda r:r['phase_fraction'])]);base-=base.mean()
            diff=signal-base
            rows.append(dict(mode=mode,depth_um=1000*depth,signal_rms_nm=float(np.sqrt(np.mean(signal**2))*1000),
                             control_change_rms_nm=float(np.sqrt(np.mean(diff**2))*1000),max_phase_control_change_nm=float(np.max(abs(diff))*1000)))
    report=dict(scope='Eight S20 phases, h=0.35 mm; empirical numerical stability, not a rigorous total error bound',phases=phys.PHASES,contact_precision_digits=80,elastic_arithmetic='float64, alternative LU ordering and four residual corrections',rows=rows,
                max_nominal_reassembly_change_nm=max(abs(r['nominal_reassembly_change_um'])*1000 for r in records),
                max_baseline_archive_shift_change_nm=max(max(abs(v) for v in r['archive_shift_changes_um'])*1000 for r in records if r['mode']=='baseline'))
    (OUT/'precision_summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
