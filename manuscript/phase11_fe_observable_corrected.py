"""Corrected signal contrast for the archived 24/24 two-start experiment.

The case named 'dedendum' contains both reliefs. The isolated dedendum
signal subtracts the addendum-only curve, not the nominal curve. This
script optionally reruns the original 50-noise-realization experiment and
writes a new result without modifying the manuscript-v10 archive.

Signal sensitivity of the FE generator does not imply identifiable relief
in the inverse operator. See audit_v11.py for restricted fits and broad
profiles; the archived fitted dedendum lies outside loaded support.

Output: revision_11_2026-10-23/11_fe_observable_dedendum_corrected.json
"""
import json, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1] / 'deposit_v6'
PROJ = ROOT / 'gear_inverse_identifiability'
sys.path.insert(0, str(PROJ / 'src'))
sys.path.insert(0, str(PROJ / 'experiments'))

from geometry.involute import InvoluteGear, GearPair
from geometry.microgeometry import TipRelief
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator
from Q1_identifiability_campaign import bestfit, SCALE

SIGMA = 1e-4
TRUTH = np.array([0.02, 0.75, 0.010, 0.50])
N_SEEDS = 50

recs = [json.loads(s) for s in (ROOT / 'results' / 'independent_validation' /
                                '11_fe_cycle_24_24.jsonl').read_text().splitlines()
        if s.strip()]
fractions = sorted({r['phase_fraction'] for r in recs})
interior = [f for f in fractions
            if not any(r['restricted_nominal_window'] for r in recs
                       if r['phase_fraction'] == f)]
print('fases:', len(fractions), 'interiores:', len(interior),
      'restringidas:', len(fractions) - len(interior), flush=True)
phi = np.array([f * 2 * np.pi / 24.0 for f in interior])


def fe_curve(case):
    d = {r['phase_fraction']: r['approach_um'] for r in recs if r['case'] == case}
    y = np.array([d[f] for f in interior]) * 1e-3
    return y - y.mean()


pair = GearPair(InvoluteGear(24, 3, 20, 20), InvoluteGear(24, 3, 20, 20))
micro = TipRelief(p=2.0)
xi_grid = np.linspace(0, 1, 1001)
rows = []
for variant in ['legacy', 'projected-energy']:
    model = GearContactModel(pair, micro1=micro, micro2=None,
                             compliance_variant=variant)
    op = BatchedGapOperator(model, 300.0, phi_positions=phi)
    # soporte analitico y senal predicha
    r_true = op.evaluate(TRUTH)
    xi = op.xi1[(r_true['forces'] > 1e-8) & op.valid]
    base_pred = op.evaluate(np.array([0.02, 0.75, 0.0, 0.5]))['prediction']
    sig_pred = float(np.sqrt(np.mean((r_true['prediction'] - base_pred) ** 2)) * 1000)
    # Isolated dedendum: combined relief minus addendum-only, means removed
    y_fe = fe_curve('dedendum')
    y_un = fe_curve('unmodified')
    sig_fe = float(np.sqrt(np.mean((y_fe - fe_curve('addendum')) ** 2)) * 1000)
    y_ad = fe_curve('addendum')
    sig_ad_fe = float(np.sqrt(np.mean((y_ad - y_un) ** 2)) * 1000)
    # inversion ruido-libre
    fit0 = bestfit([op], y_fe, SIGMA)
    est0 = np.array(fit0['theta'])
    err0 = np.abs(est0 - TRUTH) / SCALE
    prof0 = float(np.sqrt(np.mean((micro.evaluate(xi_grid, est0)
                                   - micro.evaluate(xi_grid, TRUTH)) ** 2)) * 1000)
    rmse0 = float(np.sqrt(np.mean((op.evaluate(est0)['prediction'] - y_fe) ** 2)) * 1000)
    # MC con ruido sigma=0.1 um
    rng = np.random.default_rng(20261023)
    errs, profiles, rmses = [], [], []
    for k in range(N_SEEDS):
        y = y_fe + SIGMA * rng.standard_normal(y_fe.shape)
        fit = bestfit([op], y, SIGMA)
        est = np.array(fit['theta'])
        errs.append(np.abs(est - TRUTH) / SCALE)
        profiles.append(np.sqrt(np.mean((micro.evaluate(xi_grid, est)
                                         - micro.evaluate(xi_grid, TRUTH)) ** 2)) * 1000)
        rmses.append(np.sqrt(np.mean((op.evaluate(est)['prediction'] - y_fe) ** 2)) * 1000)
    errs = np.array(errs)
    rows.append(dict(
        variant=variant,
        analytic_min_loaded_xi=float(xi.min()),
        analytic_signal_rms_um=sig_pred,
        fe_signal_dedendum_rms_um=sig_fe,
        fe_signal_addendum_rms_um=sig_ad_fe,
        noiseless=dict(estimate=est0.tolist(),
                       scaled_error=err0.tolist(),
                       profile_rmse_um=prof0,
                       fit_rmse_um=rmse0,
                       success=bool(fit0['success'])),
        mc=dict(seeds=N_SEEDS,
                scaled_error_median=np.median(errs, axis=0).tolist(),
                scaled_error_p90=np.percentile(errs, 90, axis=0).tolist(),
                profile_rmse_median_um=float(np.median(profiles)),
                profile_rmse_p90_um=float(np.percentile(profiles, 90)),
                fit_rmse_median_um=float(np.median(rmses)))))
    print(variant, 'xi_min=%.4f sig_pred=%.3f sig_fe=%.3f | noiseless est=%s err=%s prof=%.3f | MC med=%s p90=%s prof_med=%.3f' % (
        xi.min(), sig_pred, sig_fe, np.round(est0, 4).tolist(),
        np.round(err0, 3).tolist(), prof0,
        np.round(np.median(errs, axis=0), 3).tolist(),
        np.round(np.percentile(errs, 90, axis=0), 3).tolist(),
        np.median(profiles)), flush=True)

out = ROOT.parent / 'revision_11_2026-10-23'
(out / '11_fe_observable_dedendum_corrected.json').write_text(json.dumps(dict(
    truth=TRUTH.tolist(), scale=SCALE.tolist(), sigma_um=0.1,
    n_interior_phases=len(interior),
    interior_phases=interior,
    n_restricted=len(fractions) - len(interior),
    torque_Nm=300.0, geometry='24/24 symmetric, m=3 mm, alpha=20 deg, b=20 mm',
    generator='FE2D run_fe2d configure_24_24 (bore 12 mm, root_trim 0.4, P1 nodal h=0.5, 120 phases)',
    inverse='analytical beam+Hertz 24/24 operator on interior phases, mean-removed approach',
    rows=rows), indent=1))
print('written 11_fe_observable_dedendum_corrected.json')
