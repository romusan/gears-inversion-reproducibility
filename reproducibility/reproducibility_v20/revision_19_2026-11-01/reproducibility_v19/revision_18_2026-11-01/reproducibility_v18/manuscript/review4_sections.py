import json
from pathlib import Path
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm,Pt
from review3_sections import add_section as previous
from review2_sections import tab,ROOT
from word_math import node,seq,sup,sub,frac
BASE=ROOT/'revision_4_2026-10-12'
def read():return json.loads((BASE/'numerical_review4.json').read_text())
def add_section(doc,marker,paragraph,table,figure):
    original_paragraph=paragraph
    def clean_paragraph(d,text):
        for a,b in [('p_i','pᵢ'),('w_i','wᵢ'),('Δg_i','Δgᵢ'),('K_i','Kᵢ'),('b_i','bᵢ'),('w′_H','w′ₕ')]:text=text.replace(a,b)
        return original_paragraph(d,text)
    paragraph=clean_paragraph
    if marker=='Q1_COUPLED_OBSERVATION':
        paragraph(doc,'Observation on coupled flexibility. In a fixed-geometry linear contact model, diagonal compliance is unnecessary for relief invisibility. Let H be symmetric positive definite and let p≥0 satisfy 1ᵀp=F>0. Contact uniquely minimizes the strictly convex potential below; its KKT conditions are w=Hp+g−δ1≥0 and p_i w_i=0. A positive force component fixes δ uniquely.')
        p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p._p.append(node('oMath',seq('Ψ(p) = ',frac('1','2'),sup('p','T'),'H p + ',sup('g','T'),'p;   p ≥ 0, ',sup('1','T'),'p = F')))
        paragraph(doc,'If Δg≥0 and Δg_i=0 wherever p_i>0, the same p and δ satisfy the modified KKT conditions. Uniqueness proves unchanged approach, including cross-pair elastic coupling. For two imposed approaches the variational inequalities give the following bound. It makes total force strictly increasing whenever a solution has positive force; individual contact forces need not increase monotonically.')
        p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p._p.append(node('oMath',seq(sup('(p₂ − p₁)','T'),'H(p₂ − p₁) ≤ (δ₂ − δ₁)(F₂ − F₁)')))
        paragraph(doc,'For an additional nonlinear Hertz term, strict convexity requires positive definiteness of H+diag(w′_H) over the force domain. For the clipped law used here, λ_min(H)>2 max K_i, with K_i=1/(πE*b_i), is a sufficient uniform condition. Positive definiteness of H alone does not certify the composite law. The exploratory FE contact below contains no added Hertz spring. The observation assumes fixed H, geometry, contact stations and observation operator; material removal or changes in normals are outside its hypotheses.')
        return
    if marker=='Q1_FE_APPENDIX':
        r=read()
        paragraph(doc,'The exploratory FE calculation uses two complete 57-tooth plane-strain bodies with linear triangular elements, E=210000 MPa, ν=0.30 and width 23 mm. Involute flanks use the benchmark dimensions. Both circular bores are clamped relative to rigid hub motion; nominal bore radius is 25 mm. A quadratic root blend with a 0.4 mm trim approximates the missing manufactured fillet. These are assumed supports and contours, not a reconstruction of the reference CAD. No stiffness multiplier is fitted.')
        paragraph(doc,'Gmsh generates the meshes and scikit-fem assembles elasticity. Condensing both bodies gives H=P₁ᵀK₁⁻¹P₁+P₂ᵀK₂⁻¹P₂. Matched tangent stations use projected involute gaps and fixed line-of-action normals. Nonnegative nodal forces minimize the contact potential under total force 9334.893 N. Equilibrium, complementarity and finite perturbations of force verify the selected solutions. Two nominal FE matrices have positive minimum eigenvalues. Constant-strain energy and rigid-rotation checks pass; source, matrices, meshes and numerical records accompany the reproducibility materials.')
        tab(doc,12,'FE and baseline at identical sampled phases. Approach is µm; k/b is incremental stiffness per width, N/(mm·µm). Edge denotes load reaching a clipped flank endpoint.',
            ['Cycle fraction','Pairs','FE approach','Baseline approach','FE k/b','Baseline k/b','Edge'],
            [[f"{x['phase_fraction']:.6f}",x['nominal_pairs'],f"{x['fe_approach_um']:.3f}",f"{x['baseline_approach_um']:.3f}",f"{x['fe_k_per_width']:.3f}",f"{x['baseline_k_per_width']:.3f}",'Yes' if x['edge_loaded'] else 'No'] for x in r['matched_phases']],
            [2.5,1.1,2.7,3.1,2.2,3.0,1.6],paragraph,table)
        paragraph(doc,'Only nominal contact windows are included. Close to entry and exit, interface patches are clipped at the end of the involute; two sampled phases load that endpoint. Pre-engagement corner contact and changing surface normals are omitted. Excluding contacts outside nominal windows can introduce an artificial jump, so these records do not define a validated continuous FE cycle.')
        paragraph(doc,f"The eight-phase FE range is {r['fe_sampled_range_um']:.3f} µm, versus {r['baseline_sampled_range_um']:.3f} µm for the same baseline phases and {r['baseline_full_pp_um']:.3f} µm over 1920 baseline positions. Its descriptive difference from the published 10.527 µm amplitude is {r['fe_sampled_range_difference_percent']:+.1f}%. A sampled range and a full-cycle peak-to-peak target are not equivalent validation statistics. Refining one edge-bearing phase from h=0.25 to 0.18 mm changes k by {100*r['clipped_edge_refinement_k_change']:.3f}% and approach by {100*r['clipped_edge_refinement_approach_change']:.3f}%, without resolving the missing corner mechanics.")
        rows=[]
        for c in r['convergence']:
            for x in c['levels']:rows.append([c['phase_fraction'],x['h_mm'],x['contact_step_mm'],x['triangles'],f"{x['k_N_um']:.4f}",f"{x['approach_um']:.4f}"])
        tab(doc,13,'Three mesh levels at interior phases. h controls bulk/root resolution; requested contact step controls stations. Triangles count both bodies. k is N/µm and approach is µm.',
            ['Fraction','h mm','Contact mm','Triangles','k','Approach'],rows,[2,2,2.8,3,3.2,3.2],paragraph,table)
        paragraph(doc,f"A three-point fit k(h)=k∞+Chᵖ gives effective orders {r['convergence'][0]['three_point_effective_order']:.2f} and {r['convergence'][1]['three_point_effective_order']:.2f}. Bulk and contact meshes change together and station counts are rounded; these estimates do not demonstrate an asymptotic order or certify extrapolation error. Doubling contour resolution and enlarging the candidate contact patch change interior stiffness by less than 0.13%.")
        tab(doc,14,'Interior two-phase contrast under three bore assumptions. The incremental proxy F(1/k₁−1/k₂) differs from the actual phase difference. Both are µm.',
            ['Bore radius mm','Incremental proxy','Actual phase difference','Baseline k₁ excess %','Baseline k₂ excess %'],
            [[x['bore_radius_mm'],f"{x['incremental_proxy_um']:.5f}",f"{x['actual_phase_difference_um']:.5f}",f"{x['baseline_stiffer_percent'][0]:.2f}",f"{x['baseline_stiffer_percent'][1]:.2f}"] for x in r['common_flexibility']],
            [2.8,3.4,3.8,3.2,3.0],paragraph,table)
        paragraph(doc,f"The actual two-phase difference varies by {100*r['actual_two_phase_dispersion_relative']:.3f}% over these bores, despite appreciable absolute-stiffness changes. This supports approximately common compliance for these two phases, not universal independence of centred TE from hub support. Removing only cross-pair FE flexibility blocks raises k₂ from 327.06 to 408.13 N/µm. This controlled counterfactual shows a coupling effect in the assumed FE geometry; it does not establish compensation of errors in the analytical baseline.")
        tab(doc,15,'Local engagement-onset coordinate for nominal G0, zero dedendum depth. Bisection starts from the 960-position support and uses force >10⁻⁸ N. This is a local numerical onset estimate, not a continuous-domain certificate.',
            ['Compliance variant','ξ onset at 50 Nm','ξ onset at 300 Nm'],
            [[label,*[f"{next(x['onset_xi'] for x in r['support_edge'] if x['variant']==v and x['torque_Nm']==T):.9f}" for T in [50,300]]] for v,label in {'legacy':'Baseline','shear-G':'G shear','projected-energy':'Radial energy','centerline-energy':'Centre-line'}.items()],
            [6.2,5.0,5.0],paragraph,table)
        paragraph(doc,'At equal load and grid, all four variants give the same sampled ξ_min at 120 and 960 positions; local bisection reveals small mechanically dependent shifts hidden by those grids. Variant spread is about 0.000038 at 50 Nm and 0.000228 at 300 Nm. The sd=0.25 start remains above every tested onset, but the support diagnostic is conditional on compliance, load and phase resolution. The current FE is for the 57/57 benchmark and cannot certify support for G0=(24,48); its coupling matrix is not transplanted between geometries.')
        return
    previous(doc,marker,paragraph,table,figure)
    if marker=='Q1_ANGULAR':
        r=read();paragraph(doc,f"An independent exploratory continuum/contact calculation contrasts single- and double-pair interior phases at 650 Nm (Appendix A). Assuming a 25 mm clamped bore and an approximate root, it gives k₁=239.18 and k₂=327.06 N/µm, versus 346.51 and 535.49 N/µm for the baseline at the same phases. Varying the bore from 20 to 35 mm changes absolute stiffness while the two-phase approach difference varies by only {100*r['actual_two_phase_dispersion_relative']:.3f}%. Approximately common deformation can therefore cancel between these phases, consistent with the role of mean removal in the observable. This finite comparison is not a proof of support-independent centred TE. Additional transition phases reveal clipped edge loading and do not validate the published peak-to-peak amplitude.")
