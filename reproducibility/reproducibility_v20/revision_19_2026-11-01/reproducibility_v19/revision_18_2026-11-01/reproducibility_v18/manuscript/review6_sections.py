"""Sixth review: matched quadratic phases, ties and offset diagnostics."""
import json
from pathlib import Path
import review5_sections as v5
from review2_sections import ROOT,tab
NEW=ROOT/'revision_6_2026-10-12'

def add_section(doc,marker,paragraph,table,figure):
    pending=[]
    fe=json.loads((ROOT/'fe2d/results/quadratic_eight_phases.json').read_text())
    def prose(d,text):
        if text.startswith('Table 9 Linear-element nodal FE'):
            pending.append(text)
            text=text.replace('Linear-element nodal FE','Quadratic-element weak-contact FE')
        if text.startswith('At the original linear nodal resolution,'):
            text=f"With quadratic elements and distributed pressure, the eight-phase FE range is {fe['sampled_range_um']:.3f} µm. Table 9 compares the same phases with the analytical baseline; Supplementary Table S8 preserves the original linear FE values. This finite-phase restricted-model range is not a continuous-cycle peak-to-peak estimate or a certified physical error relative to 10.527 µm. Clipped edge patches, fixed normals and omitted pre-engagement corner contacts retain the main mechanical limitation."
        if text.startswith('The exploratory FE calculation uses'):
            text=text.replace('linear triangular elements','quadratic triangular displacement elements and continuous pressure hats')
        if text.startswith('Gmsh generates the meshes'):
            text=text.replace('Nonnegative nodal forces minimize','Nonnegative pressure-basis coefficients minimize')
            text=text.replace('Two nominal FE matrices have positive minimum eigenvalues.','All eight quadratic FE matrices have positive minimum eigenvalues.')
            text+=' The contact gaps are weak averages against the same normalized pressure basis; pointwise nonpenetration is not certified by this discretization.'
        if text.startswith('An independent exploratory continuum/contact calculation'):
            text=text.replace('An independent exploratory continuum/contact calculation','The original linear-element exploratory continuum/contact calculation')
        if text.startswith('The actual two-phase difference varies by'):
            text='In the original linear-element model, '+text[0].lower()+text[1:]
        if text.startswith('Across 1920 angular positions,'):
            text='Across 1920 angular positions, the baseline single-pair incremental stiffness per width is 14.08–15.07 N/(mm·µm); the eight-phase subset in Table 9 spans 14.22–15.07. ISO 6336-1 [29], Clause 9, distinguishes single-tooth and mesh stiffness. The present incremental tangent is not a calculation of either complete ISO method and provides no independent validation. The two-pair/one-pair ratio and engagement transitions require separate checks; compensation of analytical approximation errors remains a hypothesis.'
        if text.startswith('The convergence follow-up uses'):
            text+=' The interface stiffness sequence is nonmonotonic. Small last-step changes describe observed numerical stability, not established asymptotic convergence, a Richardson order or an exact-error bound.'
        return paragraph(d,text)
    def tables(d,headers,rows,widths):
        if pending:
            caption=pending.pop()
            v5.SUPPLEMENT.append(dict(number='S8',caption=caption.replace('Table 9','Supplementary Table S8'),headers=headers,rows=[row[:] for row in rows],widths=widths))
            byphase={round(r['phase_fraction'],6):r for r in fe['records']}
            rows=[row[:] for row in rows]
            for row in rows:
                r=byphase[round(float(row[0]),6)]
                row[2]=f"{r['approach_um']:.3f}"
                row[4]=f"{r['k_incremental_N_um']/23:.3f}"
                row[-1]='Yes' if r['tooth_edge_loaded'] else 'No'
        return table(d,headers,rows,widths)
    v5.add_section(doc,marker,prose,tables,figure)
    for item in v5.SUPPLEMENT:
        if item['number']=='S7':item['caption']=item['caption'].replace('Separated quadratic-element/distributed-pressure convergence.','Separated quadratic-element bulk and pressure-interface refinement controls. The interface stiffness sequence is nonmonotonic.')
    if marker=='Q1_MONTE_CARLO':
        r=json.loads((ROOT/'gear_inverse_identifiability/results/q1_review5_2026-10-12/complementary_monte_summary.json').read_text())
        percentages=[100*x['fraction_pair_better'] for x in r['summary']]
        prose(doc,'The two-load error is strictly smaller for '+', '.join(f'{p:.0f}%' for p in percentages[:3])+' of seeds at s_d=0.25 and '+', '.join(f'{p:.0f}%' for p in percentages[3:])+ ' at s_d=0.40, in increasing noise order (0.1, 0.5, 1 µm). These fractions include all 100 seeds, including failures. They use the raw floating-point comparison and do not classify small optimization differences as meaningful improvements. Saturation and near ties prevent treating a percentile endpoint at zero as a coverage certificate or an equivalence test.')
    if marker=='Q1_FE_APPENDIX':
        audit=json.loads((NEW/'review6_summary.json').read_text())
        prose(doc,f"The eight quadratic matrices are symmetric positive definite, with force, weak-contact and elastic residual checks retained in the data. In two phases, a ±0.1% force perturbation changes the active set; reducing the perturbation to ±0.01% restores agreement with the local tangent. With fixed normals and the nominal normal-force budget, the largest body-moment deviation from 650 Nm is {audit['maximum_torque_error_percent']:.4f}%; no stiffness or load multiplier is fitted to the reference.")
        r=json.loads((NEW/'angular_offset_control.json').read_text())
        entries=r['results']
        v5.SUPPLEMENT.append(dict(number='S9',caption='Supplementary Table S9 Angular sampling every 0.21° over one fixed mesh period (360/57 degrees). Offset spans [0,0.21°); grids contain 30 or 31 samples. Envelopes apply to the stated periodic piecewise-linear interpolants. FE has only eight nodes and does not resolve transition ramps.',
            headers=['Waveform','Nodes','Minimum p-p µm','Maximum p-p µm'],
            rows=[[x['model'],x['nodes'],f"{x['min_pp_um']:.6f}",f"{x['max_pp_um']:.6f}"] for x in entries],widths=[6.5,2,3.5,3.5]))
        finest=entries[-2];feinterp=entries[-1]
        prose(doc,f"For the baseline, offset envelopes at the published 0.21° increment are {finest['min_pp_um']:.3f}–{finest['max_pp_um']:.3f} µm (Supplementary Table S9); repeating with 3840, 7680 and 15360 interpolation nodes checks the angular representation. This sampling effect alone does not explain 10.527 µm in the analytical model. The eight-phase quadratic FE interpolant gives {feinterp['min_pp_um']:.3f}–{feinterp['max_pp_um']:.3f} µm under the same sampling rule, but that is a coarse interpolation illustration, not a direct FE scan. It cannot measure the unresolved FE ramp or attribute the benchmark discrepancy to angular aliasing.")
