"""Fase 0: auditoria de linea base (manuscript-v6 congelado).

Verifica, sin modificar el modelo:
  A. Integridad de monte_carlo_summary.json contra los registros jsonl.
  B. Reproduccion de las filas del support sweep para sd=0.25 y sd=0.40
     (100 Nm, 240 posiciones): RMS de senal dedendum, xi_min cargado,
     valores singulares, rango numerico, recuperacion sin ruido (2 inicios).
  C. Chequeo forward nominal G0 a 300 Nm (120 pos): equilibrio de fuerza,
     complementariedad, rango TE, y coherencia ruido/objetivo/Fisher.
  D. Valores publicados del benchmark Korta & Mundo (V06_corrected.json,
     almacenado en la copia de trabajo; reproduccion completa en Fase 3).

Ejecutar desde deposit_v6/reports/:
    python baseline_audit.py
"""
import json, subprocess, sys, platform
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]          # deposit_v6/
PROJ = ROOT / 'gear_inverse_identifiability'
sys.path.insert(0, str(PROJ / 'src'))
sys.path.insert(0, str(PROJ / 'experiments'))

import numpy, scipy, matplotlib
from Q1_identifiability_campaign import (operators, predict, bestfit,
                                         SCALE, OUT)

audit = {'library_versions': {'python': platform.python_version(),
                              'numpy': numpy.__version__,
                              'scipy': scipy.__version__,
                              'matplotlib': matplotlib.__version__},
         'git': subprocess.run(['git', '-C', str(ROOT), 'log', '--oneline', '-1'],
                               capture_output=True, text=True).stdout.strip(),
         'branch': subprocess.run(['git', '-C', str(ROOT), 'branch', '--show-current'],
                                  capture_output=True, text=True).stdout.strip()}

# ---------- A. integridad del resumen Monte Carlo ---------------------------
records = [json.loads(s) for s in (OUT / 'monte_carlo_records.jsonl').read_text().splitlines() if s.strip()]
summary_stored = json.load(open(OUT / 'monte_carlo_summary.json'))['summary']
metrics = ['addendum_scaled_error', 'dedendum_scaled_error', 'full_profile_rmse_um', 'heldout200_rmse_um']
checks_A = []
for row in summary_stored:
    grp = [r for r in records if r['sd_true'] == row['sd_true'] and r['design'] == row['design']
           and r['sigma_um'] == row['sigma_um']]
    ok_n = len(grp) == row['n']
    ok_succ = sum(r['success'] for r in grp) == row['success']
    stat_ok = True
    for m in metrics:
        a = np.array([r[m] for r in grp])
        for q, key in [(0.5, 'median'), (0.9, 'p90'), (0.95, 'p95')]:
            if abs(float(np.quantile(a, q)) - row[m][key]) > 1e-9 * max(1.0, abs(row[m][key])):
                stat_ok = False
    checks_A.append({'cell': [row['sd_true'], row['design'], row['sigma_um']],
                     'n': len(grp), 'n_ok': ok_n, 'success_ok': ok_succ, 'stats_ok': stat_ok})
audit['A_monte_carlo_integrity'] = {
    'n_records': len(records),
    'expected_cells': len(summary_stored),
    'all_ok': all(c['n_ok'] and c['success_ok'] and c['stats_ok'] for c in checks_A),
    'cells': checks_A}

# ---------- B. reproduccion de filas del support sweep ----------------------
sweep_stored = json.load(open(OUT / 'support_transition.json'))
rows_B = []
for sd in [0.25, 0.40]:
    theta = np.array([.02, .75, .005, sd])
    op = operators([(100, 240)])[0]
    r = op.evaluate(theta, jacobian=True)
    zero = theta.copy(); zero[2] = 0
    J = r['jacobian'] * SCALE / .0001
    _, sing, _ = np.linalg.svd(J, full_matrices=False)
    loaded = op.xi1[(r['forces'] > 1e-8) & op.valid]
    sig_rms = float(np.sqrt(np.mean((r['prediction'] - predict([op], zero)) ** 2)) * 1000)
    rec = bestfit([op], r['prediction'], .0001)
    est = np.array(rec['theta']); err = np.abs(est - theta) / SCALE
    stored = [w for w in sweep_stored['rows'] if abs(w['sd_true'] - sd) < 1e-9][0]
    rows_B.append({
        'sd_true': sd,
        'new': {'dedendum_signal_rms_um': sig_rms,
                'min_loaded_xi': float(loaded.min()),
                'n_loaded_relief_points': int(np.sum(loaded < sd)),
                'numerical_rank': int(np.sum(sing > sing[0] * 1e-7)),
                'singular_values': sing.tolist(),
                'recovery_dedendum_scaled_error': float(err[2:].max()),
                'recovery_addendum_scaled_error': float(err[:2].max()),
                'recovery_chi2': rec['chi2'], 'recovery_success': rec['success']},
        'stored': {k: stored[k] for k in ['dedendum_signal_rms_um', 'min_loaded_xi',
                                          'n_loaded_relief_points', 'numerical_rank',
                                          'addendum_scaled_error', 'dedendum_scaled_error']},
        'stored_singular_values': stored['singular_values'],
        'stored_recovery_chi2': stored['recovery']['chi2'],
        'match': {
            'rms': abs(sig_rms - stored['dedendum_signal_rms_um']) <= 1e-9 * max(1.0, abs(stored['dedendum_signal_rms_um'])),
            'min_loaded_xi': abs(float(loaded.min()) - stored['min_loaded_xi']) < 1e-12,
            'n_points': int(np.sum(loaded < sd)) == stored['n_loaded_relief_points'],
            'rank': int(np.sum(sing > sing[0] * 1e-7)) == stored['numerical_rank'],
            'add_err': abs(float(err[:2].max()) - stored['addendum_scaled_error']) < 1e-9,
            'ded_err': abs(float(err[2:].max()) - stored['dedendum_scaled_error']) < 1e-9,
            'sv_max_rel_diff': float(np.max(np.abs(sing - np.array(stored['singular_values']))
                                            / np.maximum(np.array(stored['singular_values']), 1e-300)))}
    })
audit['B_support_sweep_reproduction'] = rows_B

# ---------- C. chequeo forward nominal G0 a 300 Nm --------------------------
from geometry.involute import InvoluteGear, GearPair
from geometry.microgeometry import TipRelief
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator

pair = GearPair(InvoluteGear(24, 3, 20, 20), InvoluteGear(48, 3, 20, 20))
model = GearContactModel(pair, TipRelief())
phi = pair.rotation_for_mesh(120)[0]
checks_C = []
for sd in [0.25, 0.40]:
    theta = np.array([.02, .75, .005, sd])
    op = BatchedGapOperator(model, 300.0, phi_positions=phi, force_engine='iterative')
    r = op.evaluate(theta, jacobian=True)
    pred = r['prediction']
    comp = float(np.max(np.abs(np.minimum(r['forces'], r['separations']))))
    nonpen = float(np.min(r['separations']))
    checks_C.append({'sd': sd,
                     'TE_pp_um': float((pred.max() - pred.min()) * 1000),
                     'TE_rms_um': float(np.sqrt(np.mean(pred ** 2)) * 1000),
                     'force_residual_N': r['force_residual_N'],
                     'complementarity_max': comp,
                     'min_separation_mm': nonpen,
                     'monotonicity_margin': op.monotonicity_margin,
                     'jacobian_shape': list(r['jacobian'].shape),
                     'n_contact_pairs': int(np.max(np.sum(r['forces'] > 1e-8, axis=1)))})
audit['C_forward_300Nm_G0'] = checks_C

# ---------- D. benchmark externo publicado (referencia almacenada) ---------
v06_path = ROOT.parent / 'gear_inverse_identifiability/results/corrections_2026-10-12/V06_corrected.json'
v06 = json.load(open(v06_path))
errs = [c['difference_percent'] for c in v06['results']]
audit['D_korta_mundo_stored'] = {
    'n_comparisons': len(v06['results']),
    'deviations_percent_min': min(errs), 'deviations_percent_max': max(errs),
    'all_overpredict': all(c['model_pp_um'] > c['reference_fe_pp_um'] for c in v06['results']),
    'passes_5_percent_any': any(c['passes_5_percent'] for c in v06['results']),
    'source': str(v06_path),
    'note': 'Valores almacenados de la campana de correccion; reproduccion completa en Fase 3.'}

out = Path(__file__).resolve().parent / '00_baseline_audit.json'
out.write_text(json.dumps(audit, indent=1), encoding='utf-8')
print(json.dumps({k: (v if not isinstance(v, list) else f'{len(v)} entries') for k, v in audit.items()}, indent=1))
print('OK A:', audit['A_monte_carlo_integrity']['all_ok'])
for r in rows_B:
    print('B sd=%.2f match:' % r['sd_true'], {k: (f"{v:.2e}" if isinstance(v, float) else v) for k, v in r['match'].items()})
