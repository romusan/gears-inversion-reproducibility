"""Fase 2.4: efecto de la formulacion de compliance sobre la identificabilidad.

Configuraciones: legacy-24 (historico), projected-24, projected-96 (cuadratura refinada).
Casos: G0, 300 Nm, 120 posiciones, sd en {0.25, 0.40}.
Salida: reports/02_identifiability_variants.json
"""
import json, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROJ = ROOT / 'gear_inverse_identifiability'
sys.path.insert(0, str(PROJ / 'src'))
sys.path.insert(0, str(PROJ / 'experiments'))

from geometry.involute import InvoluteGear, GearPair
from geometry.microgeometry import TipRelief
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator
from Q1_identifiability_campaign import bestfit, predict, SCALE

SIGMA = 1e-4


def build(variant, nq):
    pair = GearPair(InvoluteGear(24, 3, 20, 20), InvoluteGear(48, 3, 20, 20))
    model = GearContactModel(pair, TipRelief(), compliance_variant=variant)
    if nq != 24:
        q = np.polynomial.legendre.leggauss(nq)
        model.comp1._quadrature = q
        model.comp2._quadrature = q
    return model


rows = []
for name, variant, nq in [('legacy-24', 'legacy', 24),
                          ('projected-24', 'projected-energy', 24),
                          ('projected-96', 'projected-energy', 96)]:
    op = BatchedGapOperator(build(variant, nq), 300.0, 120)
    for sd in [0.25, 0.40]:
        theta = np.array([.02, .75, .005, sd])
        r = op.evaluate(theta, jacobian=True)
        zero = theta.copy(); zero[2] = 0
        J = r['jacobian'] * SCALE / SIGMA
        _, s, _ = np.linalg.svd(J, full_matrices=False)
        loaded = op.xi1[(r['forces'] > 1e-8) & op.valid]
        rec = bestfit([op], r['prediction'], SIGMA)
        est = np.array(rec['theta']); err = np.abs(est - theta) / SCALE
        rows.append({
            'config': name, 'sd_true': sd,
            'TE_pp_um': float((r['prediction'].max() - r['prediction'].min()) * 1000),
            'TE_rms_um': float(np.sqrt(np.mean(r['prediction'] ** 2)) * 1000),
            'dedendum_signal_rms_um': float(np.sqrt(np.mean((r['prediction'] - predict([op], zero)) ** 2)) * 1000),
            'min_loaded_xi': float(loaded.min()),
            'n_loaded_relief_points': int(np.sum(loaded < sd)),
            'singular_values': s.tolist(),
            'numerical_rank': int(np.sum(s > s[0] * 1e-7)),
            'noise_free_addendum_scaled_error': float(err[:2].max()),
            'noise_free_dedendum_scaled_error': float(err[2:].max()),
            'noise_free_chi2': rec['chi2'], 'noise_free_success': rec['success'],
            'force_residual_N': r['force_residual_N']})
        print(rows[-1]['config'], sd, 'pp=%.3f um' % rows[-1]['TE_pp_um'],
              'rank=%d' % rows[-1]['numerical_rank'],
              'ded_err=%.2e' % rows[-1]['noise_free_dedendum_scaled_error'], flush=True)

# diferencias respecto al historico
base = {(r['sd_true']): r for r in rows if r['config'] == 'legacy-24'}
for r in rows:
    b = base[r['sd_true']]
    r['delta_TE_pp_percent_vs_legacy'] = 100 * (r['TE_pp_um'] - b['TE_pp_um']) / b['TE_pp_um']
    r['sv_ratio_min_vs_legacy'] = float(min(np.array(r['singular_values']) / np.array(b['singular_values'])))

(ROOT / 'reports' / '02_identifiability_variants.json').write_text(json.dumps(rows, indent=1))
print('written reports/02_identifiability_variants.json')
