"""Fase 12: repeticion de los 65 casos sin convergencia con reinicios extra.

Punto D de la evaluacion cientifica de v9: los experimentos principales
conservan 45 reconstrucciones sin convergencia de 1200 (campana original,
q1_revision_2026-10-12) y el control complementario 20 de 600
(q1_review5_2026-10-12), todas en la celda marginal s_d=0.25, sigma=0.1 um.

Este script:
  1. regenera exactamente la misma observacion ruidosa de cada caso fallido
     (default_rng(seed), mismo operador y diseno);
  2. reproduce el ajuste original con los dos STARTS fijos (verificacion);
  3. reajusta con seis arranques adicionales amplios y max_nfev mayor;
  4. compara el error de identificacion original frente al mejor reajuste y
     cuantifica si las conclusiones por celda (mediana de error dedendum)
     cambian al reemplazar los fallos.

Salida: results/independent_validation/12_convergence_rerun.json
"""
import json, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROJ = ROOT / 'gear_inverse_identifiability'
sys.path.insert(0, str(PROJ / 'src'))
sys.path.insert(0, str(PROJ / 'experiments'))

import Q1_identifiability_campaign as q1
from Q1_review5_monte import getops as comp_getops, predict as comp_predict

RES = ROOT / 'results' / 'independent_validation'
MAIN = PROJ / 'results' / 'q1_revision_2026-10-12' / 'monte_carlo_records.jsonl'
COMP = PROJ / 'results' / 'q1_review5_2026-10-12' / 'complementary_monte_records.jsonl'

EXTRA_STARTS = [np.array([.05, .50, .040, .20]),
                np.array([.01, .90, .001, .49]),
                np.array([.02, .80, .005, .48]),
                np.array([.05, .55, .045, .15])]


def load_fails(path):
    return [json.loads(s) for s in path.read_text().splitlines()
            if s.strip() and not json.loads(s)['success']]


def rerun_main(rec):
    """Repeticion de un fallo de la campana principal (disenos declarados)."""
    sd, name, sig, seed = rec['sd_true'], rec['design'], rec['sigma_um'], rec['seed']
    ops = q1.operators(q1.DESIGNS[name])
    theta = np.array([.02, .75, .005, sd]); sigma = sig * .001
    y = q1.predict(ops, theta) + np.random.default_rng(seed).normal(0, sigma, 120)
    fits = [q1.fit(ops, y, sigma, s) for s in q1.STARTS]
    fits += [q1.fit(ops, y, sigma, s, max_nfev=1500) for s in EXTRA_STARTS]
    best = min(fits, key=lambda r: r['chi2'])
    best['all_starts_success'] = bool(all(f['success'] for f in fits))
    return y, theta, sigma, fits[:2], best


def rerun_comp(rec):
    """Repeticion de un fallo del control complementario (fases entrelazadas)."""
    sd, sig, seed = rec['sd_true'], rec['sigma_um'], rec['seed']
    ops = comp_getops()
    theta = np.array([.02, .75, .005, sd])
    noise = np.random.default_rng(seed).normal(0, sig * .001, 120)
    y = comp_predict(ops, theta) + np.r_[noise[::2], noise[1::2]]
    fits = [q1.fit(ops, y, sig * .001, s) for s in q1.STARTS]
    fits += [q1.fit(ops, y, sig * .001, s, max_nfev=1500) for s in EXTRA_STARTS]
    best = min(fits, key=lambda r: r['chi2'])
    best['all_starts_success'] = bool(all(f['success'] for f in fits))
    return y, theta, sig * .001, fits[:2], best


def key(rec):
    return (rec['source'], rec['design'], rec['sd_true'], rec['sigma_um'],
            rec['seed'])


def summarize(records, redone, label):
    """Por celda con fallos: mediana de error dedendum original vs reemplazada."""
    by_key = {key(d): d for d in redone}
    cells = sorted({(r['design'], r['sd_true'], r['sigma_um']) for r in records
                    if not r['success']})
    out = []
    for design, sd, sig in cells:
        base = [r for r in records if r['design'] == design
                and r['sd_true'] == sd and r['sigma_um'] == sig]
        cell = [r for r in base if not r['success']]
        orig = np.array([r['dedendum_scaled_error'] for r in base])
        replaced = orig.copy()
        orig_prof = [r.get('full_profile_rmse_um', r.get('fit_rmse_um'))
                     for r in base]
        replaced_prof = list(orig_prof)
        resolved = 0
        for r in cell:
            d = by_key.get((label, design, sd, sig, r['seed']))
            if d is None:
                continue
            resolved += int(d['rerun_success'])
            i = base.index(r)
            replaced[i] = d['rerun_dedendum_scaled_error']
            replaced_prof[i] = d['rerun_profile_rmse_um']
        out.append(dict(design=design, sd_true=sd, sigma_um=sig,
                        n=len(base), n_fail=len(cell), n_resolved=resolved,
                        median_original=float(np.median(orig)),
                        median_replaced=float(np.median(replaced)),
                        p90_original=float(np.quantile(orig, .9)),
                        p90_replaced=float(np.quantile(replaced, .9)),
                        profile_rmse_median_original=float(np.median(orig_prof)),
                        profile_rmse_median_replaced=float(np.median(replaced_prof))))
    return dict(campaign=label, cells=out)


CKPT = RES / '12_convergence_rerun_ckpt.jsonl'


def worker(task):
    source, rec = task
    fn = rerun_main if source == 'main' else rerun_comp
    y, theta, sigma, orig_fits, best = fn(rec)
    est_o = np.array(orig_fits[0]['theta'])  # primer arranque fijo, como el original
    est_r = np.array(best['theta'])
    err_o = np.abs(est_o - theta) / q1.SCALE
    err_r = np.abs(est_r - theta) / q1.SCALE
    xi = np.linspace(0, 1, 1001)
    prof_r = float(np.sqrt(np.mean((q1.TipRelief().evaluate(xi, est_r)
                                    - q1.TipRelief().evaluate(xi, theta)) ** 2)) * 1000)
    return dict(
        source=source, design=rec['design'], sd_true=rec['sd_true'],
        sigma_um=rec['sigma_um'], seed=rec['seed'], is_fail=True,
        orig_chi2=orig_fits[0]['chi2'], rerun_chi2=best['chi2'],
        orig_success=orig_fits[0]['success'], rerun_success=bool(best['success']),
        orig_theta=est_o.tolist(), rerun_theta=est_r.tolist(),
        orig_dedendum_scaled_error=float(err_o[2:].max()),
        rerun_dedendum_scaled_error=float(err_r[2:].max()),
        rerun_profile_rmse_um=prof_r,
        rerun_all_starts_success=best['all_starts_success'])


def main():
    done = set()
    if CKPT.exists():
        done = {(json.loads(s)['source'], json.loads(s)['design'],
                 json.loads(s)['sd_true'], json.loads(s)['sigma_um'],
                 json.loads(s)['seed'])
                for s in CKPT.read_text().splitlines() if s.strip()}
        print('checkpoint: %d hechos' % len(done), flush=True)
    main_records = [json.loads(s) for s in MAIN.read_text().splitlines() if s.strip()]
    comp_records = [json.loads(s) for s in COMP.read_text().splitlines() if s.strip()]
    main_fails = load_fails(MAIN)
    comp_fails = load_fails(COMP)
    print('fallos: main=%d comp=%d' % (len(main_fails), len(comp_fails)), flush=True)

    tasks = [('main', r) for r in main_fails] + [('complementary', r) for r in comp_fails]
    tasks = [t for t in tasks
             if (t[0], t[1]['design'], t[1]['sd_true'], t[1]['sigma_um'],
                 t[1]['seed']) not in done]
    print('pendientes: %d' % len(tasks), flush=True)
    for i, res in enumerate(map(worker, tasks)):
            with CKPT.open('a', encoding='utf-8') as fh:
                fh.write(json.dumps(res) + chr(10))
            print('%d/%d %s %s seed=%d orig_err=%.3f rerun_err=%.3f chi2 %.1f->%.1f success=%s' % (
                i + 1, len(tasks), res['source'], res['design'], res['seed'],
                res['orig_dedendum_scaled_error'], res['rerun_dedendum_scaled_error'],
                res['orig_chi2'], res['rerun_chi2'], res['rerun_success']), flush=True)

    out = [json.loads(s) for s in CKPT.read_text().splitlines() if s.strip()]
    summary = [summarize(main_records, [d for d in out if d['source'] == 'main'], 'main'),
               summarize(comp_records, [d for d in out if d['source'] == 'complementary'], 'complementary')]
    for s in summary:
        for c in s['cells']:
            print(s['campaign'], c['design'], 'sd=%.2f sig=%.1f' % (c['sd_true'], c['sigma_um']),
                  'fails=%d/%d resueltos=%d med %.3f->%.3f p90 %.2f->%.2f' % (
                      c['n_fail'], c['n'], c['n_resolved'],
                      c['median_original'], c['median_replaced'],
                      c['p90_original'], c['p90_replaced']), flush=True)
    for s in summary:
        print(json.dumps(s), flush=True)

    (RES / '12_convergence_rerun.json').write_text(json.dumps(
        dict(reruns=out, summary=summary,
             note='Misma observacion (default_rng(seed)), cuatro arranques adicionales '
                  'amplios y max_nfev=1500 en los extras (400 en los originales). Las '
                  'medianas por celda comparan el registro original con el reemplazo '
                  'de los fallos por el mejor reajuste.'),
        indent=1))
    print('written 12_convergence_rerun.json')


if __name__ == '__main__':
    main()
