"""Fase 7: analisis de resolucion sobre el relieve no parametrico h(xi).

Parametriza h(xi) en N nodos con base de sombreros lineales (GridRelief),
obtiene dF/dh con la tangente implicita de contacto (BatchedGapOperator) y
calcula la matriz de resolucion (Backus-Gilbert con amortiguamiento de
Tikhonov): su diagonal dice que tramo del flanco se resuelve y su traza el
numero efectivo de grados de libertad. Se demuestra el espacio nulo
perturbando h a lo largo de direcciones nulas: F queda invariante, mientras
una direccion de rango del mismo tamano cambia F por encima del ruido.

Diseno: G0, 300 Nm, 120 posiciones, sigma = 0.1 um, projected-energy.
Casos: s_d = 0.25 y 0.40 (verdad parametrica de referencia para h).

Salida: results/independent_validation/07_resolution.json y 07_resolution.png
"""
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
PROJ = ROOT / 'gear_inverse_identifiability'
sys.path.insert(0, str(PROJ / 'src'))

from geometry.involute import InvoluteGear, GearPair
from geometry.microgeometry import TipRelief, GridRelief
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator

SIGMA = 1e-4           # 0.1 um en mm
N_NODES = 41
EPS_MAIN = 1e-6        # amortiguamiento relativo principal (vs s_0)
EPS_SWEEP = [1e-8, 1e-6, 1e-4, 1e-2]
RANK_TOL = 1e-7        # tolerancia de rango relativa (politica del manuscrito)

pair = GearPair(InvoluteGear(24, 3, 20, 20), InvoluteGear(48, 3, 20, 20))
grid = GridRelief(n_nodes=N_NODES)
model = GearContactModel(pair, micro1=grid, compliance_variant='projected-energy')
op = BatchedGapOperator(model, 300.0, 120)
tip = TipRelief()

cases = {}
fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
colors = {0.25: 'C0', 0.40: 'C1'}

for sd in [0.25, 0.40]:
    theta = np.array([.02, .75, .005, sd])
    h_true = tip.evaluate(grid.grid, theta)
    r = op.evaluate(h_true, jacobian=True)
    J = r['jacobian'] / SIGMA                      # (120, 41) blanqueado
    U, s, Vt = np.linalg.svd(J, full_matrices=False)
    V = Vt.T
    loaded = op.xi1[(r['forces'] > 1e-8) & op.valid]
    xi_min = float(loaded.min())

    sweep = {}
    for er in EPS_SWEEP:
        eps = s[0] * er
        f = s ** 2 / (s ** 2 + eps ** 2)
        R = V @ np.diag(f) @ Vt
        sweep[er] = dict(trace=float(np.trace(R)),
                         resolved_nodes=int(np.sum(np.diag(R) > 0.5)),
                         rdiag=np.diag(R).tolist())
    f_main = s ** 2 / (s ** 2 + (s[0] * EPS_MAIN) ** 2)
    R = V @ np.diag(f_main) @ Vt
    rdiag = np.diag(R)
    trace = float(np.trace(R))
    numerical_rank = int(np.sum(s > s[0] * RANK_TOL))

    # frontera de resolucion: primer nodo con rdiag>0.5 sostenido
    above = rdiag > 0.5
    xi_res = None
    for i in range(N_NODES):
        if above[i] and np.all(above[i:]):
            xi_res = float(grid.grid[i]); break

    # demostracion del espacio nulo
    null_idx = [i for i in range(len(s)) if s[i] < s[0] * RANK_TOL]
    rng_idx = int(np.argmax(s))
    demo = {}
    for name, idx in [('null_first', null_idx[0]), ('range_first', rng_idx)]:
        v = V[:, idx]
        alpha = 0.005 / np.abs(v).max()            # amplitud max 5 um
        r_plus = op.evaluate(h_true + alpha * v)
        d_mm = r_plus['prediction'] - r['prediction']
        demo[name] = dict(sv_ratio=float(s[idx] / s[0]),
                          rms_um=float(np.sqrt(np.mean(d_mm ** 2)) * 1000),
                          max_abs_um=float(np.abs(d_mm).max() * 1000))
    # direccion nula con mayor contenido en la zona dedendum [0, 0.5]
    null_vs = V[:, null_idx]
    ded_content = np.abs(null_vs[: (N_NODES + 1) // 2]).sum(axis=0)
    v = null_vs[:, int(np.argmax(ded_content))]
    alpha = 0.005 / np.abs(v).max()
    r_plus = op.evaluate(h_true + alpha * v)
    d_mm = r_plus['prediction'] - r['prediction']
    demo['null_dedendum_richest'] = dict(
        sv_ratio=float(s[null_idx[int(np.argmax(ded_content))]] / s[0]),
        rms_um=float(np.sqrt(np.mean(d_mm ** 2)) * 1000),
        max_abs_um=float(np.abs(d_mm).max() * 1000),
        profile=v.tolist(), alpha=float(alpha))

    cases[sd] = dict(xi_min=xi_min, xi_resolved_boundary=xi_res,
                     trace=trace, numerical_rank=numerical_rank,
                     singular_values=s.tolist(), rdiag=rdiag.tolist(),
                     sweep={str(k): {kk: vv for kk, vv in v.items() if kk != 'rdiag'}
                            for k, v in sweep.items()},
                     demo=demo)
    print('sd=%.2f xi_min=%.4f xi_res=%s trace=%.2f rank=%d demo null rms=%.2e um range rms=%.2e um'
          % (sd, xi_min, xi_res, trace, numerical_rank,
             demo['null_first']['rms_um'], demo['range_first']['rms_um']), flush=True)

    axes[0].plot(grid.grid, rdiag, '.-', color=colors[sd],
                 label=f'true $s_d$={sd}')
    axes[1].semilogy(range(1, len(s) + 1), s, 'o-', color=colors[sd],
                     label=f'true $s_d$={sd}')

axes[0].axvline(cases[0.25]['xi_min'], color='k', ls='--', lw=1,
                label='$\\xi_{min}$ loaded')
axes[0].axhline(0.5, color='grey', ls=':', lw=1)
axes[0].set_xlabel('flank coordinate $\\xi$'); axes[0].set_ylabel('resolution $R_{jj}$')
axes[0].set_title('(a) Resolution along the flank'); axes[0].grid(alpha=.2); axes[0].legend(fontsize=8)
for er in [EPS_MAIN]:
    axes[1].axhline(cases[0.25]['singular_values'][0] * er, color='grey', ls=':', lw=1)
axes[1].set_xlabel('singular value index'); axes[1].set_ylabel('whitened singular value')
axes[1].set_title('(b) Spectrum of $J_h$'); axes[1].grid(alpha=.2); axes[1].legend(fontsize=8)
labels = []
vals = []
for sd in [0.25, 0.40]:
    d = cases[sd]['demo']
    labels += [f'{sd} null', f'{sd} range']
    vals += [max(d['null_first']['rms_um'], 1e-9), d['range_first']['rms_um']]
axes[2].bar(range(4), vals, color=[colors[0.25], colors[0.25], colors[0.40], colors[0.40]],
            alpha=.75)
axes[2].set_xticks(range(4)); axes[2].set_xticklabels(labels, rotation=20, fontsize=8)
axes[2].axhline(0.1, color='k', ls='--', lw=1, label='noise $\\sigma$ = 0.1 µm')
axes[2].set_yscale('log'); axes[2].set_ylabel('RMS change of TE (µm)')
axes[2].set_title('(c) Null-space shuttle at 5 µm amplitude'); axes[2].legend(fontsize=8); axes[2].grid(alpha=.2, which='both')
# estudio de refinamiento: persistencia del modo nulo interno
refinement = {}
for npos, nnodes in [(120, 41), (240, 41), (240, 81), (480, 81)]:
    gr = GridRelief(n_nodes=nnodes)
    mr = GearContactModel(pair, micro1=gr, compliance_variant='projected-energy')
    opr = BatchedGapOperator(mr, 300.0, npos)
    hr = tip.evaluate(gr.grid, np.array([.02, .75, .005, .25]))
    rr = opr.evaluate(hr, jacobian=True)
    Jr = rr['jacobian'] / SIGMA
    cn = np.linalg.norm(Jr, axis=0)
    sr = np.linalg.svd(Jr, compute_uv=False)
    rank_r = int(np.sum(sr > sr[0] * RANK_TOL))
    refinement[f'{npos}_{nnodes}'] = dict(
        n_positions=npos, n_nodes=nnodes, zero_columns=int(np.sum(cn < 1e-6)),
        numerical_rank=rank_r, null_dim=nnodes - rank_r,
        min_range_singular_value=float(sr[rank_r - 1]))
    print('refinement', npos, nnodes, refinement[f'{npos}_{nnodes}'], flush=True)

fig.tight_layout()
out = ROOT / 'results' / 'independent_validation'
fig.savefig(out / '07_resolution.png', dpi=160)
(out / '07_resolution.json').write_text(json.dumps(dict(
    sigma_um=0.1, n_nodes=N_NODES, torque_Nm=300, variant='projected-energy',
    eps_main_relative=EPS_MAIN, rank_tol=RANK_TOL,
    refinement=refinement,
    cases=cases,
    note='h discretized on uniform linear-hat grid; J_h from implicit contact '
         'tangent; resolution R=(J^T J + eps^2 I)^-1 J^T J via SVD; null demo '
         'perturbs h by 5 um amplitude along singular directions.'), indent=1))
print('written 07_resolution.json / 07_resolution.png')
