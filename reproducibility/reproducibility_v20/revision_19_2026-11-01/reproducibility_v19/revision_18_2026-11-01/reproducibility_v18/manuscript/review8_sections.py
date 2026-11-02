"""Eighth build: integrate the non-parametric resolution analysis (Section 4.6)
and polish the prose into a submission-tone manuscript."""
import json
from pathlib import Path
import review7_sections as v7sec
import review5_sections as v5
from review2_sections import ROOT

RES = ROOT / 'deposit_v6' / 'results' / 'independent_validation'


def add_section(doc, marker, paragraph, table, figure):
    if marker == 'Q1_RESOLUTION':
        res = json.loads((RES / '07_resolution.json').read_text(encoding='utf-8'))
        c25 = res['cases']['0.25']
        ref = res['refinement']
        paragraph(doc,
            "The parametrized experiments above establish what four physical relief parameters "
            "can be recovered. The same implicit contact tangent answers a sharper, non-parametric "
            "question: which parts of the flank can transmission error resolve at all? The relief "
            "is discretized on 41 uniform nodes over the flank coordinate with a linear hat basis, "
            "so the local sensitivity matrix J_h=σ⁻¹∂F/∂h at 300 Nm and 120 positions is 120 by 41. "
            "The associated resolution matrix R=(J_hᵀJ_h+ε²I)⁻¹J_hᵀJ_h, evaluated through the SVD "
            "with relative damping ε=10⁻⁶s₁, gives the resolving power of each flank coordinate "
            "on its diagonal and the number of independent combinations carried by the data in "
            "its trace.")
        paragraph(doc,
            "The diagonal of R is sharply structured (Figure 7a). It is identically zero for "
            "ξ≤0.20 and approximately 0.97 for ξ≥0.225, with the transition located at the minimum "
            "loaded coordinate ξ_min=0.2356. The support-screening rule of Section 3.1 is therefore "
            "not an empirical heuristic: it coincides with the exact resolution boundary of the "
            "discrete operator, and the null space below ξ_min is spanned by the nodal values of "
            "that region, the discrete counterpart of the invisibility condition. The trace of R "
            f"is {c25['trace']:.1f}, stable over two decades of damping, and reaches "
            f"{ref['240_81']['numerical_rank']} of {ref['240_81']['n_nodes']} nodes under "
            "simultaneous refinement of the flank grid and the angular sampling. The approach "
            "waveform thus resolves the relief locally wherever contact loads it, with resolving "
            "power well beyond the four declared parameters.")
        paragraph(doc,
            "The null space is ten-dimensional, and its content is instructive. Nine directions "
            "are the nodal values below ξ_min. The tenth is internal: a weighted combination "
            "concentrated at ξ≈0.25–0.375 and ξ≈0.875–0.90 that persists under angular and grid "
            "refinement (Supplementary Table S12). It corresponds to transferring load between "
            "simultaneously active pairs while keeping the weighted gap sum fixed, and it is "
            "invisible in the approach observable by construction. The support condition is thus "
            "sufficient but not complete: the observable carries one structural null direction "
            "that no inversion method can recover from transmission error alone.")
        paragraph(doc,
            "A direct null-space shuttle confirms the dichotomy (Figure 7c). Perturbing the "
            "relief by 5 µm along a null direction, the amplitude of the dedendum relief studied "
            "above, leaves transmission error unchanged to 10⁻¹⁵ µm, while the same perturbation "
            "along the principal resolved direction changes it by "
            f"{c25['demo']['range_first']['rms_um']:.2f} µm, seventeen times the noise floor. For "
            "measurement practice, the resolution map certifies what a transmission-error-based "
            "identification can support: the relief over the loaded part of the flank across the "
            "intended operating range, with a single load-split combination to be kept in mind "
            "when relief content spans single- and double-pair contact zones.")
        figure(doc, 'fig_resolution.png',
               'Figure 7 Resolution of the non-parametric relief at 300 Nm and σ=0.1 µm. '
               '(a) Diagonal of the resolution matrix along the flank: exact null region below '
               'the minimum loaded coordinate, near-unit resolution above it. (b) Whitened '
               'spectrum of J_h; singular values beyond index 31 (≈10⁻¹²) span the null space. '
               '(c) Null-space shuttle: RMS change of transmission error for 5 µm relief '
               'perturbations along the first null and the principal resolved directions, '
               'against the noise floor.')
        rows = []
        for key in ['120_41', '240_41', '240_81', '480_81']:
            r = ref[key]
            rows.append([r['n_positions'], r['n_nodes'], r['zero_columns'],
                         r['numerical_rank'], r['null_dim'],
                         f"{r['min_range_singular_value']:.3g}"])
        v5.SUPPLEMENT.append(dict(
            number='S12',
            caption='Supplementary Table S12 Refinement of the resolution analysis at the '
                    'marginal-support truth. Zero columns are nodal values whose sensitivity '
                    'column vanishes identically (support below the minimum loaded coordinate); '
                    'the internal null direction is the remainder of the null-space dimension. '
                    'The smallest resolved singular value grows with refinement.',
            headers=['Positions', 'Nodes', 'Zero columns', 'Rank', 'Null dimension',
                     'Smallest resolved s'],
            rows=rows, widths=[2.2, 1.8, 2.6, 1.6, 2.6, 3.4]))
    else:
        v7sec.add_section(doc, marker, paragraph, table, figure)
