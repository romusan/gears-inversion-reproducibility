"""Seventh review: cross-operator inversion and formulation robustness."""
import json
from pathlib import Path
import review6_sections as v6sec
import review5_sections as v5
from review2_sections import ROOT, tab

DEP = ROOT / 'deposit_v6'
RES = DEP / 'results' / 'independent_validation'


def load(name):
    return json.loads((RES / name).read_text(encoding='utf-8'))


def add_section(doc, marker, paragraph, table, figure):
    if marker == 'Q1_CROSS_INVERSE':
        cross = load('03_cross_inverse.json')
        mc = load('04_mc_summary.json')
        bench = load('03_benchmark_reproduction.json')

        paragraph(doc,
            "An independent two-dimensional finite-element model (plane strain, linear triangular "
            "elements, frictionless unilateral contact, fixed line-of-action normals, rigid bore of "
            "assumed 25 mm radius and an approximated root transition) generated full-cycle approach "
            "curves for the benchmark 57/57 pair at 650 Nm with pinion relief exponent p=2. Four relief "
            "configurations share the geometry: unmodified, addendum relief of 0.020 mm from s=0.75, and "
            "dedendum relief of 0.005 mm from s=0.30 and from s=0.45. Six of the twenty-five phases are "
            "restricted by the nominal contact-patch window and are excluded; the inversion uses the "
            "nineteen interior phases only.")

        paragraph(doc,
            "The dedendum cases are numerically identical to the addendum case at all twenty-five "
            "phases: the finite-element generator contains no dedendum signal outside loaded support. "
            "This is an independent mechanical confirmation of the sufficient invisibility condition, "
            "obtained with a contact operator different from the analytical model.")

        rows = []
        for r in cross['rows']:
            est = r['estimate']
            rows.append([r['variant'], r['case'],
                         f"{est[0]:.4f}", f"{est[1]:.4f}",
                         f"{est[2]:.4f}", f"{est[3]:.2f}",
                         f"{r['rmse_TE_at_observed_phases_um']:.3f}",
                         f"{r['pp_pred_um']:.2f} / {r['pp_fe_um']:.2f}"])
        tab(doc, 9,
            'Cross-operator inversion: analytical operator fitted to interior finite-element phases '
            '(650 Nm, benchmark 57/57). Estimated relief parameters; TE RMSE at observed phases and '
            'predicted versus finite-element peak-to-peak are in µm. The identical dedendum rows '
            'reflect the absence of dedendum signal in the generator, not a property of the inverse.',
            ['Compliance', 'Case', 'C_a est mm', 's_a est', 'C_d est mm', 's_d est',
             'TE RMSE µm', 'p-p pred/FE µm'],
            rows, [2.2, 2.2, 1.7, 1.5, 1.7, 1.4, 1.6, 2.8], paragraph, table)

        paragraph(doc,
            "The addendum depth is recovered within 5% of its scale with both compliance formulations "
            "(0.0175 mm legacy and 0.0206 mm projected-energy, true 0.020 mm), with 0.109–0.151 µm "
            "transmission-error residual at the observed phases. The estimated dedendum depth is "
            "spurious, 0.01–0.02 mm against true values of 0–0.005 mm: it is the degree of freedom that "
            "absorbs the discrepancy between the two mechanical operators. Small estimated dedendum "
            "depths therefore cannot be interpreted literally, and the residual between independent "
            "operators bounds practical precision at about 0.1 µm of transmission error.")

        legacy = [r for r in bench if r['variant'] == 'legacy']
        proj = [r for r in bench if r['variant'] == 'projected-energy']
        paragraph(doc,
            f"Recalculating the twelve external peak-to-peak targets with both formulations gives "
            f"{min(r['relative_error_percent'] for r in legacy):.1f}–{max(r['relative_error_percent'] for r in legacy):.1f}% "
            f"error for the legacy baseline and "
            f"{min(r['relative_error_percent'] for r in proj):.1f}–{max(r['relative_error_percent'] for r in proj):.1f}% "
            f"for the energy-projected variant; none of the 24 comparisons meets the adopted 5% target. "
            f"The external discrepancy is structural rather than a defect of the shear term alone.")

        s_legacy = next(r for r in mc['summary'] if r['variant'] == 'legacy' and r['sd_true'] == 0.25)
        s_proj = next(r for r in mc['summary'] if r['variant'] == 'projected-energy' and r['sd_true'] == 0.25)
        d_legacy = next(r for r in mc['summary'] if r['variant'] == 'legacy' and r['sd_true'] == 0.40)
        d_proj = next(r for r in mc['summary'] if r['variant'] == 'projected-energy' and r['sd_true'] == 0.40)
        paragraph(doc,
            f"Monte Carlo repetition of the nominal cells under the energy-projected formulation "
            f"(100 seeds each at σ=0.1 µm) changes the median dedendum scaled error from "
            f"{s_legacy['dedendum_scaled_error']['median']:.3f} to {s_proj['dedendum_scaled_error']['median']:.3f} "
            f"at s_d=0.25 and from {d_legacy['dedendum_scaled_error']['median']:.3f} to "
            f"{d_proj['dedendum_scaled_error']['median']:.3f} at s_d=0.40, with addendum medians of "
            f"{s_proj['addendum_scaled_error']['median']:.3f} in all four cells. The support transition "
            f"occurs at the same relief start in both formulations, just above the common minimum "
            f"loaded coordinate 0.2356. The contact-support conclusions are invariant to the "
            f"compliance formulation.")

        v5.SUPPLEMENT.append(dict(
            number='S10',
            caption='Supplementary Table S10 Cross-operator inversion records. Generator: '
                    'two-dimensional finite element (plane strain, linear elements, frictionless '
                    'contact, bore radius assumed 25 mm). Inverse: analytical beam–Hertz operator, '
                    '650 Nm, nineteen interior phases of 25. Spurious dedendum estimates absorb '
                    'operator discrepancy; they are not physical relief measurements.',
            headers=['Compliance', 'Case', 'C_a true', 'C_a est', 's_a est', 'C_d est', 's_d est',
                     'TE RMSE µm', 'p-p pred µm', 'p-p FE µm'],
            rows=[[r['variant'], r['case'],
                   {'addendum': '0.0200', 'dedendum': '0.0200', 'dedendum-deep': '0.0200'}[r['case']],
                   f"{r['estimate'][0]:.4f}", f"{r['estimate'][1]:.4f}",
                   f"{r['estimate'][2]:.4f}", f"{r['estimate'][3]:.2f}",
                   f"{r['rmse_TE_at_observed_phases_um']:.3f}",
                   f"{r['pp_pred_um']:.2f}", f"{r['pp_fe_um']:.2f}"] for r in cross['rows']],
            widths=[2.1, 2.1, 1.5, 1.5, 1.4, 1.5, 1.3, 1.6, 1.6, 1.7]))
        v5.SUPPLEMENT.append(dict(
            number='S11',
            caption='Supplementary Table S11 Formulation robustness of noise recovery. G0, 300 Nm, '
                    '120 observations, σ=0.1 µm, 100 seeds per cell, seed base 20261022. Scaled '
                    'errors |Δθ|/s; profile RMSE on 1001 flank coordinates.',
            headers=['Compliance', 'True s_d', 'Addendum med', 'Addendum p90',
                     'Dedendum med', 'Dedendum p90', 'Profile RMSE med µm', 'χ² median'],
            rows=[[r['variant'], f"{r['sd_true']:.2f}",
                   f"{r['addendum_scaled_error']['median']:.3f}",
                   f"{r['addendum_scaled_error']['p90']:.3f}",
                   f"{r['dedendum_scaled_error']['median']:.3f}",
                   f"{r['dedendum_scaled_error']['p90']:.3f}",
                   f"{r['full_profile_rmse_um']['median']:.3f}",
                   f"{r['chi2']['median']:.0f}"] for r in mc['summary']],
            widths=[2.4, 1.5, 1.9, 1.9, 1.9, 1.9, 2.7, 2.0]))
    else:
        # v7 renumbering: the new Section 4.5 table takes number 9; the two
        # appendix tables shift from 9,10 to 10,11. Strings arrive already
        # relabelled by the review5 layer (review4 source numbers 12 and 15).
        def renumber(d, text):
            for old, new in [
                ('Table 9 Quadratic-element weak-contact FE', 'Table 10 Quadratic-element weak-contact FE'),
                ('Table 9 compares the same phases', 'Table 10 compares the same phases'),
                ('the eight-phase subset in Table 9 spans', 'the eight-phase subset in Table 10 spans'),
                ('Table 10 Local engagement-onset', 'Table 11 Local engagement-onset'),
            ]:
                if old in text:
                    text = text.replace(old, new)
            return paragraph(d, text)
        v6sec.add_section(doc, marker, renumber, table, figure)
