"""Fase 3.5: validacion inversa cruzada.

Operador generador: FE 2D independiente (run_fe2d, fases interiores verificadas).
Operador inverso: modelo analitico de contacto (GearContactModel + BatchedGapOperator).
Geometria: 57/57 del benchmark (misma para ambos operadores; sin trasladar
matrices de compliance entre geometrias).

Salida: results/independent_validation/03_cross_inverse.json
"""
import json, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROJ = ROOT / 'gear_inverse_identifiability'
sys.path.insert(0, str(PROJ / 'src'))
sys.path.insert(0, str(PROJ / 'experiments'))

from V06_korta_mundo_reproduction import build_pair
from geometry.microgeometry import TipRelief
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator
from Q1_identifiability_campaign import bestfit, SCALE

SIGMA = 1e-4
BOUNDS = np.array([[0, .1], [.3, .95], [0, .05], [.05, .5]])
CASES = {
    'addendum': np.array([0.02, 0.75, 0.0, 0.5]),
    'dedendum': np.array([0.02, 0.75, 0.005, 0.30]),
    'dedendum-deep': np.array([0.02, 0.75, 0.005, 0.45]),
}

# ---------- cargar la curva FE ---------------------------------------------
recs = [json.loads(s) for s in (ROOT / 'results' / 'independent_validation' /
                                '03_fe_cycle_v2.jsonl').read_text().splitlines() if s.strip()]
fractions = sorted({r['phase_fraction'] for r in recs})
interior = [f for f in fractions
            if not any(r['restricted_nominal_window'] for r in recs if r['phase_fraction'] == f)]
print('fases:', len(fractions), 'interiores:', len(interior),
      'excluidas:', sorted(set(fractions) - set(interior)))
phi_fe = np.array([f * 2 * np.pi / 57.0 for f in interior])


def fe_curve(case):
    d = {r['phase_fraction']: r['approach_um'] for r in recs if r['case'] == case}
    y = np.array([d[f] for f in interior]) * 1e-3  # um -> mm
    return y - y.mean()


# ---------- modelo analitico 57/57 ------------------------------------------
pair = build_pair()
micro = TipRelief(p=2.0)
analytic = {v: GearContactModel(pair, micro1=micro, micro2=None,
                                compliance_variant=v)
            for v in ['legacy', 'projected-energy']}
u_tip1 = float(np.sqrt((pair.g1.ra / pair.g1.rb) ** 2 - 1))


def support(model, theta):
    op = BatchedGapOperator(model, 650.0, phi_positions=phi_fe)
    r = op.evaluate(theta, jacobian=False)
    xi = op.xi1[(r['forces'] > 1e-8) & op.valid]
    return float(xi.min()), op, r


rows = []
xi_grid = np.linspace(0, 1, 1001)
for variant, model in analytic.items():
    # soporte analitico para cada caso
    for cname, truth in CASES.items():
        op = BatchedGapOperator(model, 650.0, phi_positions=phi_fe)
        r_true = op.evaluate(truth)
        xi_min, _, _ = support(model, truth)
        y_fe = fe_curve(cname)
        # inverso analitico sobre las mismas fases interiores
        fit = bestfit([op], y_fe, SIGMA)
        est = np.array(fit['theta'])
        err_scaled = np.abs(est - truth) / SCALE
        pred_est = op.evaluate(est)['prediction']
        rmse_te = float(np.sqrt(np.mean((pred_est - y_fe) ** 2)) * 1000)
        pp_pred = float((pred_est.max() - pred_est.min()) * 1000)
        pp_fe = float((y_fe.max() - y_fe.min()) * 1000)
        prof_rmse = float(np.sqrt(np.mean((micro.evaluate(xi_grid, est)
                                           - micro.evaluate(xi_grid, truth)) ** 2)) * 1000)
        # senal: diferencia del caso vs unmodified en cada operador
        base_pred = op.evaluate(np.array([0.0, 0.75, 0.0, 0.5]))['prediction']
        signal_analytic = float(np.sqrt(np.mean((r_true['prediction'] - base_pred) ** 2)) * 1000)
        rows.append(dict(variant=variant, case=cname,
                         truth=truth.tolist(), estimate=est.tolist(),
                         addendum_scaled_error=float(err_scaled[:2].max()),
                         dedendum_scaled_error=float(err_scaled[2:].max()),
                         full_profile_rmse_um=prof_rmse,
                         rmse_TE_at_observed_phases_um=rmse_te,
                         pp_pred_um=pp_pred, pp_fe_um=pp_fe,
                         e_pp_percent=100 * abs(pp_pred - pp_fe) / pp_fe,
                         analytic_min_loaded_xi=xi_min,
                         analytic_signal_rms_um=signal_analytic,
                         chi2=fit['chi2'], fit_rmse_um=fit['fit_rmse_um'],
                         success=fit['success']))
        print(variant, cname, 'est=', np.round(est, 4).tolist(),
              'add_err=%.3f ded_err=%.3f' % (err_scaled[:2].max(), err_scaled[2:].max()),
              'TErmse=%.3f um pp=%.2f/%.2f' % (rmse_te, pp_pred, pp_fe),
              'xi_min=%.3f' % xi_min, 'sig=%.2f um' % signal_analytic, flush=True)

# curvas de referencia unmodified: pp de cada operador vs benchmark 10.527
ref = {}
for variant, model in analytic.items():
    op = BatchedGapOperator(model, 650.0, phi_positions=phi_fe)
    for cname in ['unmodified']:
        pred = op.evaluate(None)['prediction']
        ref[variant] = dict(analytic_pp_interior_um=float((pred.max() - pred.min()) * 1000),
                            fe_pp_interior_um=float((fe_curve(cname).max() - fe_curve(cname).min()) * 1000))

out = ROOT / 'results' / 'independent_validation'
(out / '03_cross_inverse.json').write_text(json.dumps(
    dict(rows=rows, reference_pp_interior=ref,
         interior_phases=interior,
         benchmark_pp_650Nm_um=10.527,
         note='FE phases interior-only; phi = fraction*2*pi/57; pinion relief p=2; '
              'generator=FE2D run_fe2d (bore 25 mm assumed, root_trim 0.4 mm, P1 nodal h=0.5); '
              'inverse=analytical beam+Hertz model (two compliance variants).'), indent=1))
print('reference pp (interior):', json.dumps(ref))
print('written 03_cross_inverse.json')
