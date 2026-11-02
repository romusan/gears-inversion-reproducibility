"""Tenth build: add the observable-dedendum FE cross-operator test (phase 11)
as a second, complementary validation in Section 4.5, qualify the exact
null-space statement of Section 4.6 as a property of the linearized
discretized operator, and close the remaining review points: convergence
robustness of the 65 flagged fits (phase 12), two inverse-analysis
references, abstract length, scoped FE claims, AI declaration and the
seed-base note in the supplement.
"""
import json
import review9_sections as v9sec
import review5_sections as v5
from review2_sections import ROOT

RES = ROOT / 'deposit_v6' / 'results' / 'independent_validation'


def fmt(theta, unit=False):
    return (f"({theta[0]:.4f}, {theta[1]:.4f}, {theta[2]:.4f}, {theta[3]:.4f})")


def add_section(doc, marker, paragraph, table, figure):
    if marker == 'Q1_CROSS_INVERSE':
        v9sec.add_section(doc, marker, paragraph, table, figure)
        fe = json.loads((RES / '11_fe_observable_dedendum.json').read_text(encoding='utf-8'))
        truth = fe['truth']
        legacy, proj = fe['rows']
        t = tuple(truth)
        fe_dd = legacy['fe_signal_dedendum_rms_um']
        fe_ad = legacy['fe_signal_addendum_rms_um']
        an_dd = proj['analytic_signal_rms_um']
        ratio = fe_dd / an_dd
        n_int = fe['n_interior_phases']
        n_res = fe['n_restricted']
        p = proj['noiseless']
        paragraph(doc,
            "A second finite-element test closes the gap left by the nominal cross-operator "
            "experiment, in which the dedendum never entered the loaded region: the minimum "
            "loaded coordinate 0.6953 over its nineteen interior phases lies far above both "
            "dedendum starts, so invisibility there is the prediction of the support condition, "
            "not an independent recovery result. A symmetric 24/24 pair with module 3 mm at "
            "300 Nm has an analytic minimum loaded coordinate "
            f"{legacy['analytic_min_loaded_xi']:.4f}, so a dedendum relief starting at "
            f"{t[3]:.2f} penetrates the loaded flank throughout the cycle. The truth is "
            f"C_a={t[0]:.3f} mm, s_a={t[1]:.2f}, C_d={t[2]:.3f} mm and s_d={t[3]:.2f}. The "
            f"dedendum signal of the FE generator, {fe_dd:.2f} µm RMS between C_d="
            f"{t[2]:.3f} mm and C_d=0, is of the same order as its addendum signal "
            f"({fe_ad:.2f} µm) and about {ratio:.0f} times the analytical operator's dedendum "
            "response at the same truth: a direct amplitude measure of the inter-operator "
            "discrepancy, consistent with the structural discrepancy account of Section 5 "
            "rather than evidence against it.")
        paragraph(doc,
            f"Inverting the {n_int} interior-phase FE responses ({n_res} restricted phases "
            "excluded) with the energy-projected compliance, noise-free, recovers "
            f"C_a={p['estimate'][0]:.4f} mm, s_a={p['estimate'][1]:.4f}, "
            f"C_d={p['estimate'][2]:.4f} mm and s_d={p['estimate'][3]:.4f}: the dedendum "
            f"depth to {abs(p['estimate'][2]-t[2])*1000:.1f} µm of its true {t[2]*1000:.0f} µm, "
            "but its start only coarsely (true "
            f"{t[3]:.2f}), and the fit residual of {p['fit_rmse_um']:.2f} µm exceeds the "
            "0.1 µm noise floor used in the Monte Carlo campaigns. Across "
            f"{proj['mc']['seeds']} noise realizations at 0.1 µm the median scaled errors are "
            f"{proj['mc']['scaled_error_median'][0]:.3f} (C_a), "
            f"{proj['mc']['scaled_error_median'][1]:.3f} (s_a), "
            f"{proj['mc']['scaled_error_median'][2]:.3f} (C_d) and "
            f"{proj['mc']['scaled_error_median'][3]:.3f} (s_d), with a 90th percentile of "
            f"{proj['mc']['scaled_error_p90'][2]:.3f} on the dedendum depth. The depth of a "
            "loaded dedendum relief is therefore recoverable through cross-operator inversion, "
            "its start only grossly, and even the noise-free recovery is limited by the "
            "operator discrepancy rather than by the inversion. This test, not the nominal "
            "one, is the cross-operator evidence for dedendum observability; it is restricted "
            "to the sampled interior phases of a single geometry and load.")
        rows = []
        for r in fe['rows']:
            nl, mc = r['noiseless'], r['mc']
            rows.append([
                r['variant'],
                fmt(nl['estimate']),
                fmt(nl['scaled_error']),
                fmt(mc['scaled_error_median']),
                f"{mc['scaled_error_p90'][2]:.3f}",
                f"{mc['fit_rmse_median_um']:.3f}",
            ])
        v5.SUPPLEMENT.append(dict(
            number='S13',
            caption='Supplementary Table S13 Observable-dedendum cross-operator inversion on '
                    'the symmetric 24/24 pair at 300 Nm (truth C_a=0.020 mm, s_a=0.75, '
                    'C_d=0.010 mm, s_d=0.50; 102 interior phases, 18 restricted phases '
                    'excluded; FE dedendum signal 1.768 µm RMS against 0.197 µm for the '
                    'analytical operator at the same truth). Noiseless and Monte Carlo '
                    '(50 seeds, 0.1 µm) scaled errors; the last column is the median fit '
                    'residual. The dedendum depth is recovered by the projected-energy '
                    'variant, its start only coarsely; the legacy variant absorbs part of '
                    'the inter-operator discrepancy into the dedendum block.',
            headers=['Variant', 'Noiseless estimate (C_a, s_a, C_d, s_d)',
                     'Noiseless scaled error', 'MC median scaled error',
                     'MC p90 err. C_d', 'Fit RMSE µm'],
            rows=rows, widths=[2.2, 3.8, 3.2, 3.4, 1.8, 1.8]))
    elif marker == 'Q1_RESOLUTION':
        v9sec.add_section(doc, marker, paragraph, table, figure)
        paragraph(doc,
            "Two qualifications bound these resolution statements. The null space, the "
            "near-unit diagonal and the per-direction standard deviations are exact "
            "properties of the linearized, discretized operator at the fitted point; they "
            "describe the first-order sensitivity map, not a guarantee that arbitrary "
            "nonlinear profiles are reconstructible from transmission error. A global "
            "reconstruction claim would additionally require control of the higher-order "
            "terms of the contact map, in particular the validity of the linearization away "
            "from contact switches and over the amplitude range of the relief, and control "
            "of the flank-grid discretization error. The Monte Carlo experiments of Section "
            "4.3 supply that nonlinear evidence within the four-parameter relief family, "
            "while the present analysis certifies the linearized sensitivity structure "
            "exactly.")
    else:
        v9sec.add_section(doc, marker, paragraph, table, figure)
