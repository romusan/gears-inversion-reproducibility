"""Audit cached pilot equilibria; do not promote preliminary outputs to paper."""
import csv,hashlib,json,platform,shutil,zipfile
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pilot_surface_contact as p


def audit():
    p.fe.configure_24_24();out=p.OUT
    raw=json.loads((out/'campaign.json').read_text())
    assert len(raw)==15,'Campaign must finish before analysis'
    baseline=json.loads((out/'nominal_window_baseline.json').read_text())
    # Analytic two-contact convex problem: force ratio 2:1 for compliance 1:2.
    pp,dd,ww=p.solve(np.diag([1e-5,2e-5]),np.zeros(2),np.ones(2)*p.fe.RB,1000.)
    analytic_error=float(np.max(abs(pp/(1000/p.fe.RB)-[2/3,1/3])))
    assert analytic_error<1e-10
    verified=[];fixed=0;kinematic=[]
    for r0 in raw:
        r=json.loads(json.dumps(r0));phase=r['phase'];step=r['step_mm'];h=r['bulk_h_mm']
        tag=f'phase{phase:.6f}_step{step:g}_h{h:g}'
        z=np.load(out/(tag+'.npz'))
        poly,lab=p.contour(step);cc=p.fe.contacts(phase,.05,.025,True)
        w1=poly@cc[0]['R1'].T;w2=poly@cc[0]['R2'].T+[p.fe.CENTER,0]
        rows=p.candidates(w1,w2,lab,lab)
        H=z['H'];g=z['gap'];a=z['lever'];force=z['force']
        assert len(rows)==len(force)
        assert np.max(abs(np.array([c['gap'] for c in rows])-g))<1e-12
        edge=np.array([c['corner'] or c['surface1']=='tip' or c['surface2']=='tip' for c in rows])
        tooth=np.rint(np.arctan2(poly[:,1],poly[:,0])*p.fe.Z/(2*np.pi)).astype(int)%p.fe.Z
        nominal={(c['tooth1'],c['tooth2']) for c in cc}
        extra=np.array([(int(tooth[c['i']]),int(tooth[c['j']])) not in nominal for c in rows])
        corrected=int(np.sum(edge!=z['edge']));fixed+=corrected
        r['corrected_candidate_classifications']=corrected
        r['active_tip_or_corner']=int(np.sum(edge&(force>1e-5)))
        r['tip_or_corner_force_fraction']=float(force[edge].sum()/force.sum())
        r['force_fraction_outside_nominal_pairs']=float(force[extra].sum()/force.sum())
        # Kinematic work conjugacy, independently perturb master rigid angle.
        q=z['master']-[p.fe.CENTER,0];eps=1e-7
        motion=(q@p.fe.rotation(eps).T-q@p.fe.rotation(-eps).T)/(2*eps)
        deriv=-np.sum(motion*z['normal'],axis=1)
        kinematic.append(float(np.max(abs(deriv-a))/p.fe.RB))
        assert kinematic[-1]<1e-7
        xi=z['xi_pinion'];add=.02*(np.maximum(xi-.75,0)/.25)**2
        ded=.01*(np.maximum(.5-xi,0)/.5)**2
        for name,relief in [('unmodified',np.zeros_like(g)),('addendum',add),('combined',add+ded)]:
            f,delta,res=p.solve(H,g+relief,a,300000.)
            assert np.min(f)>-1e-7 and abs(a@f/300000-1)<1e-9
            assert res.min()>-1e-8 and np.max(abs(res[f>1e-5]))<1e-8
            if name=='unmodified':assert abs(delta*1000-r['approach_um'])<1e-7
            else:
                v=r['relief_gap_variants'][name]
                assert abs(delta*1000-v['approach_um'])<1e-7
                v['tip_or_corner_force_fraction']=float(f[edge].sum()/f.sum())
                v['force_fraction_outside_nominal_pairs']=float(f[extra].sum()/f.sum())
        np.savez_compressed(out/('classification_'+tag+'.npz'),edge=edge,extra_nominal_pair=extra)
        verified.append(r)
    convergence=[]
    for phase in sorted({r['phase'] for r in verified}):
        rr=sorted([r for r in verified if r['phase']==phase],key=lambda r:-r['step_mm'])
        mid,fine=rr[-2:];base=next(b for b in baseline if b['phase']==phase)
        convergence.append(dict(phase=phase,approach_fine_um=fine['approach_um'],
            last_approach_change_um=fine['approach_um']-mid['approach_um'],
            last_approach_change_relative=abs(fine['approach_um']/mid['approach_um']-1),
            gap_law_dedendum_difference_fine_um=fine['isolated_dedendum_approach_difference_um'],
            last_dedendum_difference_change_um=fine['isolated_dedendum_approach_difference_um']-mid['isolated_dedendum_approach_difference_um'],
            nominal_window_baseline_um=base['approach_um'],
            difference_vs_nominal_window_um=fine['approach_um']-base['approach_um'],
            difference_vs_nominal_window_relative=fine['approach_um']/base['approach_um']-1,
            extra_pair_force_fraction=fine['force_fraction_outside_nominal_pairs'],
            true_tip_or_corner_force_fraction=fine['tip_or_corner_force_fraction'],
            deformed_contact_gap_error_um=fine['deformed_research_max_active_gap_um']))
    (out/'campaign_verified.json').write_text(json.dumps(verified,indent=2),encoding='utf-8')
    (out/'summary.csv').write_text('',encoding='utf-8')
    with (out/'summary.csv').open('w',encoding='utf-8',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=list(convergence[0]));wr.writeheader();wr.writerows(convergence)
    receipt=dict(status='EXPLORATORY_ONLY_NOT_FOR_MANUSCRIPT_RESULTS',configurations=15,
        equilibria_audited=45,nominal_window_comparisons=5,analytic_force_ratio_error=analytic_error,
        torque_lever_kinematic_relative_error_max=max(kinematic),
        corrected_candidate_classifications=fixed,
        classification_correction='A segment starting at the tip/flank junction is a flank segment unless both endpoints lie on the tip circle. Raw campaign and edge arrays retain pre-audit labels; use campaign_verified.json and classification_*.npz.',
        maximum_elastic_residual=max(r['elastic_residual_relative'] for r in verified),
        maximum_torque_residual=max(r['torque_relative_residual'] for r in verified),
        maximum_energy_residual=max(r['energy_relative_residual'] for r in verified),
        configurations_with_loaded_search_cutoff=sum(r['active_search_boundary'] for r in verified),
        convergence=convergence,python=platform.python_version(),
        assumptions=['24/24 spur, module 3 mm, 20 degree pressure angle, width 20 mm, E210 GPa, nu0.3, plane strain, fixed bore radius12 mm, root trim0.4 mm',
            'sharp tip, assumed quadratic root blend; no measured/CAD geometry',
            'one-pass nominal contour contact; normals and elastic contact points are not iteratively updated during a solve',
            'phase-dependent full-contour candidates in x(center/2 +/-5 mm), abs(y)<12 mm, gap cutoff0.1 mm; facing-normal filters',
            'relief represented only by first-order extra gap on pinion with u/u_tip p=2 law; addendum continued constantly on top; not relief CAD',
            'torque300 Nm imposed on gear2; gear1 held by its hub; actual reaction torque is reported',
            '15 equilibria configurations at five phases do not determine a full-cycle TE or unique inverse recovery'],
        decision='Do not insert numerical pilot results into v18: deformed-contact re-search exposes contact-location error; complete nonlinear contact updates and geometry validation first.')
    (out/'audit.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    fig,ax=plt.subplots(1,3,figsize=(13,3.8))
    for step in [.04,.02,.01]:
        rr=sorted([r for r in verified if r['step_mm']==step],key=lambda r:r['phase'])
        xx=[r['phase'] for r in rr]
        ax[0].plot(xx,[r['approach_um'] for r in rr],'o-',label=f'step {step:g} mm')
        ax[1].plot(xx,[r['isolated_dedendum_approach_difference_um'] for r in rr],'o-')
    ax[0].plot([r['phase'] for r in baseline],[r['approach_um'] for r in baseline],'kx--',label='Nominal windows, fine')
    fine=[r for r in verified if r['step_mm']==.01]
    ax[2].plot([r['phase'] for r in fine],[r['deformed_research_max_active_gap_um'] for r in fine],'rs-',label='Re-search active gap error')
    ax[2].plot([r['phase'] for r in fine],[r['isolated_dedendum_approach_difference_um'] for r in fine],'bo-',label='Gap-law dedendum contrast')
    for aa in ax:aa.set_xlabel('Mesh phase fraction');aa.set_ylabel('micrometres');aa.grid(alpha=.25)
    ax[0].set_title('Nominal angular approach x base radius');ax[1].set_title('Combined minus addendum (uncentred)');ax[2].set_title('Contact-location error vs gap contrast')
    ax[0].legend(fontsize=7);ax[2].legend(fontsize=7)
    fig.suptitle('Exploratory pilot: not validated corner-contact or inverse recovery',fontsize=11)
    fig.tight_layout();fig.savefig(out/'pilot_diagnostics.png',dpi=170);plt.close(fig)
    sources={}
    for name in ['pilot_surface_contact.py','analyze_pilot_surface.py','run_pilot_surface_campaign.py','run_fe2d.py']:
        src=Path(__file__).parent/name;shutil.copy2(src,out/name)
        sources[name]=hashlib.sha256(src.read_bytes()).hexdigest()
    (out/'source_hashes.json').write_text(json.dumps(sources,indent=2))
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':audit()
