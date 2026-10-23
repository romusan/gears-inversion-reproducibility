"""Third-review controls, with prior numerical records preserved."""
import json
from review2_sections import add_section as previous,tab,pic,ROOT
NEW=ROOT/'gear_inverse_identifiability/results/q1_review3_2026-10-12'

def add_section(doc,marker,paragraph,table,figure):
    def corrected(d,text):
        text=text.replace('is retained as a counterexample to a universal ambiguity claim','demonstrates that ambiguity is conditional on contact support')
        text=text.replace('This monotone ranking mainly rewards the highest torque within the tested range.', 'This is a local ranking of the addendum block on the original grids, rather than a complete profile-recovery design criterion.')
        text=text.replace('a lower-sensitivity load', 'a load with lower addendum sensitivity')
        text=text.replace('Table 9 connects geometry','Table 11 connects geometry')
        text=text.replace('Table 9 Support and sensitivity','Table 11 Support and sensitivity')
        if text.startswith('All six intervals contain zero'):
            text='All six bootstrap intervals contain zero, and five of six paired medians favour a single 300 Nm load. At s_d=0.40, the tested allocation has no demonstrable recovery advantage. At s_d=0.25, that comparison is confounded by the different angular grids and cannot isolate load allocation. Neither result proves equivalence or excludes loads that change contact support more effectively.'
        return paragraph(d,text)
    previous(doc,marker,corrected,table,figure)
    if marker=='Q1_ANGULAR':
        r=json.loads((NEW/'stiffness_scale.json').read_text(encoding='utf-8'))['rows'][0]
        paragraph(doc,f"The baseline single-pair incremental stiffness per width is {r['per_width_min_N_mm_um']:.2f}–{r['per_width_max_N_mm_um']:.2f} N/(mm·µm). ISO 6336-1:2019, clause 6.4.3, assumes c′=14 N/(mm·µm) for spur gears in simplified Method C [29]. That assumption concerns steel solid-disc gears and is not a universal stiffness range. The present incremental tangent is not a calculation of ISO c′; proximity in magnitude supplies no independent validation. It nevertheless motivates testing the two-pair/one-pair stiffness ratio and engagement transition alongside absolute compliance. Compensating approximation errors remain a hypothesis, not a demonstrated cause of the better baseline amplitude.")
    elif marker=='Q1_SPECTRA':
        r=json.loads((NEW/'grid_control.json').read_text(encoding='utf-8'))
        paragraph(doc,'The original equal-count comparison assigns 120 angular positions to 300 Nm and 60 positions to each of 50 and 300 Nm. This changes phase coverage as well as torque allocation. Two controls separate these effects: shared dense grids with information normalized to the same budget, and actual 120-observation designs with complementary phases. Each sampled cycle retains its own removed mean.')
        rows=[[x['sd_true'],x['n_phase_nodes'],f"{x['single300']['sigma4']:.5g}",f"{x['pair50_300']['sigma4']:.5g}",f"{x['psd_margin']:.3g}"] for x in r['common_grid']]
        tab(doc,9,'Common-grid local information at σ=0.1 µm. Single-load information uses weight 120/n; each paired load uses 60/n. Dense grids are quadrature controls normalized to a 120-observation budget, not new 120-observation Monte Carlo datasets. PSD margin is λ_min(I_pair)−[λ_min(I_50)+λ_min(I_300)]/2.',
            ['True s_d','Nodes n','300 σ₄','50/300 σ₄','PSD margin'],rows,[2.3,2.3,3.4,3.4,4.8],paragraph,table)
        paragraph(doc,'Both loads share 240 positions in the first dense control, extended to 480 and 960 to assess phase refinement. At s_d=0.25, the 240-node normalized σ₄ values are 0.03317 and 0.03003 for 300 and 50/300 Nm. At 960 nodes they are 0.03309 and 0.03149. All controls satisfy the positive-semidefinite lower bound for the weighted information sum. This bound does not imply that allocating half the budget to a lower torque must improve on allocating the entire budget to 300 Nm.')
        # A compact wide comparison avoids sixteen repeated design rows.
        names={'single300_120':'300, 120 phases','pair_original60':'50/300, original 60','repeat300_original60':'300/300, original 60','pair_same60':'50/300, even 60','repeat300_same60':'300/300, even 60','pair_interleaved_A':'50 even, 300 odd','pair_interleaved_B':'50 odd, 300 even','repeat300_interleaved':'300 even, 300 odd'}
        rows=[]
        for key,label in names.items():
            rr=[next(x for x in r['actual_designs'] if x['sd_true']==sd and x['design']==key) for sd in [.25,.4]]
            rows.append([label,*[f"{x['sigma4']:.5g}" for x in rr]])
        tab(doc,10,'Actual designs with 120 observations, σ=0.1 µm. Original 60 denotes the original uniform cycle grid. Even and odd denote complementary index subsets of the 120-position grid, with its existing endpoint convention; they differ from the original 60-position grid.',
            ['Phase and torque assignment','σ₄ at s_d=0.25','σ₄ at s_d=0.40'],rows,[8.4,3.9,3.9],paragraph,table)
        paragraph(doc,'At marginal support, repeating 300 Nm on the original 60-position grid gives σ₄=0.01501, close to 0.01524 for 50/300 Nm: most of the original information loss survives without changing torque. Complementary phases give 0.03607 and 0.03621, close to the 120-position single-load value 0.03581. The marginal allocation result is therefore sampling dependent. At deeper support, complementary-load σ₄ values 6.157 and 6.106 remain below the single-load value 6.368; dense common-grid controls give the same ordering. This supports the local ordering in that regime, without replacing a controlled nonlinear Monte Carlo comparison or claiming exact convergence of marginal information.')
    elif marker=='Q1_GEOMETRIES':
        paragraph(doc,'Geometry is part of the observability diagnosis. At s_d=0.25 and 300 Nm, G1 and G3 have ξ_min≈0.138 and 0.079 with σ₄≈6.7 and 23.4, whereas G0 has only marginal penetration and G2 has no loaded dedendum support. Before fitting, compare nominal loaded ξ_min over the intended loads with the expected s_d range, refining phases near engagement. A range entirely below ξ_min flags an invisible candidate region under the stated support condition; overlap calls for sensitivity and profile analysis rather than a guarantee of recovery. This makes the diagnostic specific to geometry, load and angular sampling.')
