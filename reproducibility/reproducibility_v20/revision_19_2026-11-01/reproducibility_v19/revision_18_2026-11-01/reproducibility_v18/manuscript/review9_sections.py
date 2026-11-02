"""Ninth build: correct the null-space interpretation (the tenth null
direction is the additive constant over the loaded nodes, a consequence of
the mean-removed observable, not load transfer), add a per-direction and
per-node precision analysis, and close the minor points raised in review:
cross-operator dedendum wording, addendum precision in absolute terms,
xi_min of the 57/57 pair, seed disambiguation of the 0.394/0.369 medians,
and the ±0.9 pp solver note on the recalculated benchmark ranges.
"""
import json
import review8_sections as v8sec
import review5_sections as v5
from review2_sections import ROOT

RES = ROOT / 'deposit_v6' / 'results' / 'independent_validation'


def rep(t, old, new):
    assert old in t, 'text drifted: ' + old[:80]
    return t.replace(old, new, 1)


def add_section(doc, marker, paragraph, table, figure):
    if marker == 'Q1_RESOLUTION':
        res = json.loads((RES / '07_resolution.json').read_text(encoding='utf-8'))
        cor = json.loads((RES / '09_resolution_corrections.json').read_text(encoding='utf-8'))
        c25 = res['cases']['0.25']
        ref = res['refinement']
        ns = cor['null_structure']
        prec = cor['precision']
        assert ns['rank_equals_loaded_minus_one']
        n_below = prec['directions_with_std_below_um']
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
            "ξ≤0.20 and approximately 0.97 for ξ≥0.225, so the transition is bracketed between "
            "the last unloaded node and the first loaded node; this is consistent with the contact "
            "onset 0.2346 at 300 Nm of Table 11, which the uniform 0.025 grid does not resolve. "
            "The support-screening rule of Section 3.1 is therefore not an empirical heuristic: "
            "it coincides with the exact resolution boundary of the discrete operator, and the "
            "null space below the support boundary is spanned by the nodal values of that "
            "region, the discrete counterpart of the invisibility condition. The trace of R is "
            f"{c25['trace']:.1f}, equal to the number of loaded nodes minus one, stable over two "
            f"decades of damping, and reaches {ref['240_81']['numerical_rank']} of "
            f"{ref['240_81']['n_nodes']} nodes under simultaneous refinement of the flank grid "
            "and the angular sampling. The approach waveform thus resolves 31 independent relief "
            "combinations wherever contact loads the flank.")
        paragraph(doc,
            "The null space is ten-dimensional, and its content is fully accounted for. Nine "
            "directions are the nodal values below the support boundary. The tenth is the "
            f"constant over the {ns['n_loaded']} loaded nodes: the hat functions sum to one, so a "
            "constant relief shift moves every gap and approach reading by the same amount and "
            "is erased by the cycle mean (Section 2.3). Correspondingly the whitened operator "
            "satisfies J_h 1=0 identically (‖J_h 1‖/s₁≈10⁻¹⁵), its rank is n_loaded−1, and "
            "R_jj=1−1/n_loaded≈0.969 on the loaded part. The relief is therefore identified up "
            "to this additive constant — a structural property of the mean-removed observable, "
            "not a limitation of any particular inversion method.")
        paragraph(doc,
            "Resolution does not by itself quantify precision. With σ=0.1 µm the standard "
            "deviation of the amplitude of each resolved direction is 1/s_k: "
            f"{n_below['0.5']} of the {ns['rank']} resolved directions lie below 0.5 µm, "
            f"{n_below['1.0']} below 1 µm and {n_below['5.0']} below 5 µm, while the two "
            "least-resolved directions (5.3 and 14.7 µm) remain estimable but poorly "
            "conditioned. Projected onto nodes, the standard deviation of the resolved part is "
            "about 0.10 µm near ξ≈0.6, rises to about 4.8 µm in the mid-flank region "
            "ξ≈0.375–0.475, and stays below 5 µm at every loaded node; the nodes below the "
            "support boundary carry no relief information at all. The precision boundary "
            "therefore coincides with the support boundary.")
        paragraph(doc,
            "A direct null-space shuttle confirms the dichotomy (Figure 7c). Perturbing the "
            "relief by 5 µm along a null direction, the amplitude of the dedendum relief studied "
            "above, leaves transmission error unchanged to 10⁻¹⁵ µm, while the same perturbation "
            "along the principal resolved direction changes it by "
            f"{c25['demo']['range_first']['rms_um']:.2f} µm, seventeen times the noise floor. For "
            "measurement practice, the resolution map states what a transmission-error-based "
            "identification can support: the relief over the loaded part of the flank, up to an "
            "additive constant, across the intended operating range.")
        figure(doc, 'fig_resolution.png',
               'Figure 7 Resolution of the non-parametric relief at 300 Nm and σ=0.1 µm. '
               '(a) Diagonal of the resolution matrix along the flank: exact null region below '
               'the support boundary, near-unit resolution above it. (b) Whitened spectrum of '
               'J_h; singular values beyond index 31 (≈10⁻¹²) span the null space. (c) '
               'Null-space shuttle: RMS change of transmission error for 5 µm relief '
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
                    'the remaining null dimension counts the additive constant over the loaded '
                    'nodes, which the mean-removed observable annihilates. The smallest resolved '
                    'singular value grows with refinement.',
            headers=['Positions', 'Nodes', 'Zero columns', 'Rank', 'Null dimension',
                     'Smallest resolved s'],
            rows=rows, widths=[2.2, 1.8, 2.6, 1.6, 2.6, 3.4]))
    elif marker == 'Q1_CROSS_INVERSE':
        # prose() runs once per paragraph, so apply each (old, new) pair only
        # when its anchor is present, and verify at the end that all landed.
        fixes = [
            ("This is an independent mechanical confirmation of the sufficient invisibility "
             "condition, obtained with a contact operator different from the analytical model.",
             "This is an independent mechanical confirmation of the sufficient invisibility "
             "condition, obtained with a contact operator different from the analytical model. "
             "The minimum loaded coordinate over the nineteen interior phases is 0.6953, far "
             "above both dedendum starts (0.30 and 0.45), so the invisibility of both "
             "dedendum cases is the prediction of the support condition rather than a new "
             "empirical finding."),
            ("The addendum depth is recovered within 5% of its scale with both compliance "
             "formulations (0.0175 mm legacy and 0.0206 mm projected-energy, true 0.020 mm), "
             "with 0.109–0.151 µm transmission-error residual at the observed phases.",
             "The addendum depth is recovered to 0.0025 mm (legacy) and 0.0006 mm "
             "(projected-energy) of the true 0.020 mm, with 0.109–0.151 µm "
             "transmission-error residual at the observed phases."),
            ("The estimated dedendum depth is spurious, 0.01–0.02 mm against true values of "
             "0–0.005 mm: it is the degree of freedom that absorbs the discrepancy between "
             "the two mechanical operators. Small estimated dedendum depths therefore cannot "
             "be interpreted literally,",
             "The estimated dedendum depth is 0.01–0.02 mm against true values of 0–0.005 "
             "mm, but the dedendum block did not move from its initialization: the estimated "
             "dedendum start equals the starting value in both formulations, so the reported "
             "dedendum values carry no relief information and only mark the degree of freedom "
             "left available to the fit. Small estimated dedendum depths therefore cannot be "
             "interpreted literally,"),
            ("The external discrepancy is structural rather than a defect of the shear term "
             "alone.",
             "The external discrepancy is structural rather than a defect of the shear term "
             "alone. The roughly ±0.9 pp shift from the original campaign's 8.9–37.2% range "
             "reflects solver discretization settings in this independent recalculation; the "
             "case × torque pairs and the FE references are identical."),
            ("The contact-support conclusions are invariant to the compliance formulation.",
             "The contact-support conclusions are invariant to the compliance formulation. "
             "The legacy medians quoted here come from a repetition with a disjoint seed base "
             "(20261022); a bootstrap comparison with the original campaign (median 0.394, "
             "95% CI [0.310, 0.433] against 0.369, CI [0.291, 0.435]) leaves the two "
             "statistically indistinguishable."),
        ]
        landed = [False] * len(fixes)

        def prose(d, text):
            for i, (old, new) in enumerate(fixes):
                if old in text:
                    text = text.replace(old, new, 1)
                    landed[i] = True
            return paragraph(d, text)

        v8sec.add_section(doc, marker, prose, table, figure)
        missing = [i for i, ok in enumerate(landed) if not ok]
        assert not missing, 'cross-inverse fixes not applied: %s' % missing
        for item in v5.SUPPLEMENT:
            if item['number'] == 'S10':
                item['caption'] = item['caption'].replace(
                    'Spurious dedendum estimates absorb operator discrepancy; they are not '
                    'physical relief measurements.',
                    'Estimated dedendum blocks remain at their initialization and carry no '
                    'relief information.')
    else:
        v8sec.add_section(doc, marker, paragraph, table, figure)
