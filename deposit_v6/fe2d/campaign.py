"""Mesh and boundary-assumption checks for the exploratory two-plateau test."""
import json,time,hashlib,platform,importlib.metadata as metadata
import numpy as np
from pathlib import Path
from run_fe2d import run,OUT,E,NU,WIDTH,MeshTri,Basis,ElementVector,ElementTriP1,asm,linear_elasticity

def patch_test():
    m=MeshTri.init_tensor(np.linspace(0,2,9),np.linspace(0,3,11))
    b=Basis(m,ElementVector(ElementTriP1()));lam=E*NU/((1+NU)*(1-2*NU));mu=E/(2*(1+NU))
    K=WIDTH*asm(linear_elasticity(lam,mu),b)
    A=np.array([[1e-4,3e-5],[3e-5,-2e-5]]);disp=A@m.p;u=np.zeros(b.N);u[b.nodal_dofs]=disp
    numerical=float(.5*u@(K@u));expected=float(.5*WIDTH*6*(lam*np.trace(A)**2+2*mu*np.sum(A*A)))
    interior=np.setdiff1d(np.arange(b.N),b.get_dofs().all());r=K@u
    rigid=np.zeros(b.N);rigid[b.nodal_dofs]=np.vstack([-m.p[1],m.p[0]])
    report=dict(strain_energy_relative_error=abs(numerical/expected-1),
        constant_strain_interior_residual=float(np.linalg.norm(r[interior])/np.linalg.norm(r)),
        rigid_rotation_relative_residual=float(np.linalg.norm(K@rigid)/(np.linalg.norm(K.data)*np.linalg.norm(rigid))))
    assert report['strain_energy_relative_error']<1e-10 and report['constant_strain_interior_residual']<1e-10
    assert report['rigid_rotation_relative_residual']<1e-10
    return report

def main():
    patch=patch_test();records=[]
    for h,step in [(.5,.02),(.35,.014),(.25,.01)]:
        for phase in [0,.5]:records.append(run(phase,h,step,25,.4,save=h==.25))
        (OUT/'campaign_partial.json').write_text(json.dumps(records,indent=2))
    convergences=[]
    for phase in [0,.5]:
        rr=[r for r in records if r['phase_fraction']==phase]
        change=abs(rr[-1]['k_incremental_N_um']/rr[-2]['k_incremental_N_um']-1)
        if change>.01:
            records.append(run(phase,.18,.0075,25,.4,save=True))
            rr.append(records[-1]);change=abs(rr[-1]['k_incremental_N_um']/rr[-2]['k_incremental_N_um']-1)
        convergences.append(dict(phase_fraction=phase,last_k_change=change,within_one_percent=change<=.01))
    # Resolve bore and root blend assumptions on the same refined mesh.
    for bore,trim in [(20,.4),(35,.4),(25,0),(25,.8)]:
        for phase in [0,.5]:records.append(run(phase,.25,.01,bore,trim))
        (OUT/'campaign_partial.json').write_text(json.dumps(records,indent=2))
    sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')}
    report=dict(patch_test=patch,records=records,mesh_convergence=convergences,
        source_hashes=sources,python=platform.python_version(),
        versions={n:metadata.version(n) for n in ['numpy','scipy','matplotlib','gmsh','scikit-fem','meshio']},
        status='Exploratory assumed geometry and supports; not an exact reproduction of the published FE benchmark.',
        contact_model='Full gear 2D continuum; fixed-normal, matched-tangent-station frictionless contact with exact projected involute gaps; no analytical beam/Hertz compliance.',
        excluded='Exact trochoidal fillet, reference hub/rim support, 3D effects, corner engagement transition and full TE cycle.')
    (OUT/'campaign.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('CAMPAIGN COMPLETE',json.dumps(convergences),flush=True)

if __name__=='__main__':main()
