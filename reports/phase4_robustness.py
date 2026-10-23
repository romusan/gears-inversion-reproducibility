"""Fase 4: robustez de las conclusiones de identificabilidad frente a la
formulacion de compliance (legacy vs projected-energy).

Pregunta central: sobrevive la conclusion "la identificabilidad depende de la
interseccion del relieve con las regiones cargadas, pero la interseccion no
garantiza precision" al cambiar de formulacion? Y: sigue siendo valida, de
forma matematica, la condicion suficiente de invisibilidad (relieve sin
interseccion con la zona cargada => columna dedendum del Jacobiano nula)?

Diseno: G0 (24/48, m=3, beta=20), 300 Nm, 120 posiciones, sigma = 0.1 um.
Casos: sd en {0.25, 0.40} (marginal vs amplia interseccion; s_min = 0.2356).

Productos:
  1. sweep de transicion (senal dedendum vs sd, ambas variantes, sin ajuste)
  2. metricas forward + espectro + recuperacion sin ruido (consistencia Fase 2)
  3. Monte Carlo con ruido: 100 semillas declaradas por configuracion
     (semilla base 20261022), checkpoint con reanudacion.

Uso:
  python phase4_robustness.py sweep        # productos 1+2
  python phase4_robustness.py mc legacy    # MC de una variante (reanudable)
  python phase4_robustness.py mc all       # MC de ambas variantes
  python phase4_robustness.py summary      # agrega MC -> JSON resumen
"""
import json, sys, argparse
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

SIGMA = 1e-4           # 0.1 um en mm
BASE_SEED = 20261022
N_SEEDS = 100
SD_CASES = [0.25, 0.40]
OUT = ROOT / 'results' / 'independent_validation'
MC_PATH = OUT / '04_mc_records.jsonl'


def build(variant):
    pair = GearPair(InvoluteGear(24, 3, 20, 20), InvoluteGear(48, 3, 20, 20))
    return GearContactModel(pair, TipRelief(), compliance_variant=variant)


def forward_metrics(model, theta):
    op = BatchedGapOperator(model, 300.0, 120)
    r = op.evaluate(theta, jacobian=True)
    J = r['jacobian'] * SCALE / SIGMA
    _, s, _ = np.linalg.svd(J, full_matrices=False)
    loaded = op.xi1[(r['forces'] > 1e-8) & op.valid]
    zero = theta.copy(); zero[2] = 0.0
    return op, r, dict(
        TE_pp_um=float((r['prediction'].max() - r['prediction'].min()) * 1000),
        TE_rms_um=float(np.sqrt(np.mean(r['prediction'] ** 2)) * 1000),
        min_loaded_s=float(loaded.min()),
        n_loaded_relief_points=int(np.sum(loaded < theta[3])),
        singular_values=s.tolist(),
        numerical_rank=int(np.sum(s > s[0] * 1e-7)),
        fisher_condition=float((s[0] / s[-1]) ** 2) if s[-1] > 0 else None,
        dedendum_signal_rms_um=float(
            np.sqrt(np.mean((r['prediction'] - predict([op], zero)) ** 2)) * 1000),
        force_residual_N=r['force_residual_N'])


def sweep():
    rows, cases = [], []
    sd_grid = np.linspace(0.20, 0.50, 61)
    for variant in ['legacy', 'projected-energy']:
        model = build(variant)
        for sd in sd_grid:
            theta = np.array([.02, .75, .005, float(sd)])
            _, _, m = forward_metrics(model, theta)
            m.update(variant=variant, sd_true=float(sd))
            rows.append(m)
        for sd in SD_CASES:
            theta = np.array([.02, .75, .005, sd])
            _, _, m = forward_metrics(model, theta)
            rec = bestfit([BatchedGapOperator(model, 300.0, 120)],
                          predict([BatchedGapOperator(model, 300.0, 120)], theta), SIGMA)
            est = np.array(rec['theta'])
            m.update(variant=variant, sd_true=sd,
                     noise_free_addendum_scaled_error=float((np.abs(est - theta) / SCALE)[:2].max()),
                     noise_free_dedendum_scaled_error=float((np.abs(est - theta) / SCALE)[2:].max()),
                     noise_free_chi2=rec['chi2'])
            cases.append(m)
            print(variant, 'sd=%.2f' % sd, 'pp=%.3f' % m['TE_pp_um'],
                  'n_loaded=%d' % m['n_loaded_relief_points'],
                  'ded_sig=%.4f um' % m['dedendum_signal_rms_um'],
                  'ded_err=%.1e' % m['noise_free_dedendum_scaled_error'], flush=True)
    # umbrales de transicion: primer sd con senal > 1e-6 um y con puntos cargados
    thresholds = {}
    for variant in ['legacy', 'projected-energy']:
        vr = [r for r in rows if r['variant'] == variant]
        vis = [r for r in vr if r['n_loaded_relief_points'] > 0]
        sig = [r for r in vr if r['dedendum_signal_rms_um'] > 1e-6]
        thresholds[variant] = dict(
            first_sd_with_loaded_relief_points=min(r['sd_true'] for r in vis),
            first_sd_with_signal_above_1em6_um=min(r['sd_true'] for r in sig))
    (OUT / '04_support_transition_sweep.json').write_text(json.dumps(
        dict(rows=rows, thresholds=thresholds,
             min_loaded_s_G0_300Nm=0.2356,
             note='s in [0,1] along active profile (0=root,1=tip); dedendum '
                  'relief occupies s<sd; loaded region [s_min,1]; invisibility '
                  'iff sd<=s_min; forward-only sweep (no fitting).'), indent=1))
    (OUT / '04_forward_cases.json').write_text(json.dumps(cases, indent=1))
    print('thresholds:', json.dumps(thresholds))


def mc_one(variant, sd, seed):
    model = build(variant)
    op = BatchedGapOperator(model, 300.0, 120)
    theta = np.array([.02, .75, .005, sd])
    y = predict([op], theta) + np.random.default_rng(seed).normal(0, SIGMA, 120)
    rec = bestfit([op], y, SIGMA)
    est = np.array(rec['theta'])
    micro = TipRelief()
    xi = np.linspace(0, 1, 1001)
    prof = float(np.sqrt(np.mean((micro.evaluate(xi, est)
                                  - micro.evaluate(xi, theta)) ** 2)) * 1000)
    return dict(variant=variant, sd_true=sd, seed=seed,
                addendum_scaled_error=float((np.abs(est - theta) / SCALE)[:2].max()),
                dedendum_scaled_error=float((np.abs(est - theta) / SCALE)[2:].max()),
                full_profile_rmse_um=prof, chi2=rec['chi2'],
                success=rec['success'],
                **{'addendum_error_h_um': float((est[0] - theta[0]) * 1000),
                   'addendum_error_sa': float(est[1] - theta[1]),
                   'dedendum_error_Cd_um': float((est[2] - theta[2]) * 1000),
                   'dedendum_error_sd': float(est[3] - theta[3])})


def mc(which):
    variants = ['legacy', 'projected-energy'] if which == 'all' else [which]
    existing = []
    if MC_PATH.exists():
        existing = [json.loads(s) for s in MC_PATH.read_text().splitlines() if s.strip()]
    done = {(r['variant'], r['sd_true'], r['seed']) for r in existing}
    tasks = [(v, sd, BASE_SEED + k) for v in variants for sd in SD_CASES
             for k in range(N_SEEDS) if (v, sd, BASE_SEED + k) not in done]
    print('pending:', len(tasks), 'already done:', len(done), flush=True)
    with MC_PATH.open('a', encoding='utf-8') as f:
        for i, (v, sd, seed) in enumerate(tasks, 1):
            f.write(json.dumps(mc_one(v, sd, seed)) + '\n'); f.flush()
            if i % 10 == 0:
                print('MC', i, '/', len(tasks), flush=True)


def summary():
    rr = [json.loads(s) for s in MC_PATH.read_text().splitlines() if s.strip()]
    out = []
    for variant in ['legacy', 'projected-energy']:
        for sd in SD_CASES:
            g = [r for r in rr if r['variant'] == variant and r['sd_true'] == sd]
            row = dict(variant=variant, sd_true=sd, n=len(g),
                       n_success=sum(r['success'] for r in g),
                       seeds=sorted(r['seed'] for r in g))
            for metric in ['addendum_scaled_error', 'dedendum_scaled_error',
                           'full_profile_rmse_um', 'chi2',
                           'dedendum_error_Cd_um', 'dedendum_error_sd']:
                a = np.array([r[metric] for r in g])
                row[metric] = dict(median=float(np.median(a)),
                                   p90=float(np.quantile(a, .9)),
                                   p95=float(np.quantile(a, .95)),
                                   max=float(a.max()))
            out.append(row)
            print('%-16s sd=%.2f n=%3d  add med=%.3f p90=%.3f | ded med=%.3f p90=%.3f | prof med=%.3f um' % (
                variant, sd, len(g),
                row['addendum_scaled_error']['median'], row['addendum_scaled_error']['p90'],
                row['dedendum_scaled_error']['median'], row['dedendum_scaled_error']['p90'],
                row['full_profile_rmse_um']['median']), flush=True)
    (OUT / '04_mc_summary.json').write_text(json.dumps(
        dict(base_seed=BASE_SEED, n_seeds=N_SEEDS, sigma_um=0.1,
             design='G0, 300 Nm, 120 obs; truth [0.02, 0.75, 0.005, sd]; '
                    'two fixed starts (Q1); chi2 reference ~120 (nobs-npar).',
             summary=out), indent=1))
    print('written 04_mc_summary.json')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('command', choices=['sweep', 'mc', 'summary'])
    ap.add_argument('which', nargs='?', default='all')
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    {'sweep': sweep, 'mc': lambda: mc(a.which), 'summary': summary}[a.command]()
