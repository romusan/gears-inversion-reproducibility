"""Fase 9: correccion de la interpretacion del espacio nulo + mapa de precision.

Punto 1 (revision): la decima direccion nula es la constante sobre los nodos
cargados (observable con media removida), NO una transferencia de carga:
  - los sombreros suman 1 -> J_h·1 = 0 exacto,
  - rango = (#nodos cargados) - 1,
  - R_jj = 1 - 1/n_cargados sobre los cargados, 0 sobre los demas.

Punto 2 (revision): resolucion no es precision. Se reporta la desviacion
estandar por direccion (1/s_k) y por nodo, y cuantas direcciones quedan
por debajo de umbrales de amplitud del relieve.

Menores: bootstrap 0.394 vs 0.369; consistencia de rangos porcentuales de las
Tablas 1-2; dedendum de la Tabla 9 vs puntos de partida; xi_min del 57/57.

Salida: results/independent_validation/09_resolution_corrections.json
"""
import json, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROJ = ROOT / 'gear_inverse_identifiability'
sys.path.insert(0, str(PROJ / 'src'))
sys.path.insert(0, str(PROJ / 'experiments'))

from geometry.involute import InvoluteGear, GearPair
from geometry.microgeometry import TipRelief, GridRelief
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator
from V06_korta_mundo_reproduction import build_pair
from Q1_identifiability_campaign import STARTS

SIGMA = 1e-4
out = {}

# ---------- A. estructura del espacio nulo ---------------------------------
pair = GearPair(InvoluteGear(24, 3, 20, 20), InvoluteGear(48, 3, 20, 20))
grid = GridRelief(n_nodes=41)
model = GearContactModel(pair, micro1=grid, compliance_variant='projected-energy')
op = BatchedGapOperator(model, 300.0, 120)
h_true = TipRelief().evaluate(grid.grid, np.array([.02, .75, .005, .25]))
r = op.evaluate(h_true, jacobian=True)
Jw = r['jacobian'] / SIGMA
U, s, Vt = np.linalg.svd(Jw, full_matrices=False)
V = Vt.T
colnorm = np.linalg.norm(Jw, axis=0)
loaded = colnorm > 1e-9 * s[0]
rank = int(np.sum(s > 1e-9 * s[0]))
one = loaded.astype(float)
J1 = float(np.linalg.norm(Jw @ one) / s[0])

# parte cargada de cada vector nulo: debe ser uniforme/|uniforme|
null_V = V[:, s <= 1e-9 * s[0]]
E = null_V.copy()
E[~loaded, :] = 0.0
E /= np.linalg.norm(E, axis=0, keepdims=True)
uniform_dev = float(np.abs(np.abs(E[loaded, :]) - 1.0 / np.sqrt(loaded.sum())).max())
n_loaded = int(loaded.sum())

rdiag_expected = np.where(loaded, 1.0 - 1.0 / n_loaded, 0.0)
eps = s[0] * 1e-6
f = s ** 2 / (s ** 2 + eps ** 2)
R = V @ np.diag(f) @ Vt
rdiag = np.diag(R)
rdiag_match = float(np.abs(rdiag - rdiag_expected).max())

out['null_structure'] = dict(
    n_nodes=41, n_loaded=n_loaded, rank=rank,
    rank_equals_loaded_minus_one=bool(rank == n_loaded - 1),
    null_dim=int(41 - rank),
    Jh_times_uniform_relative=float(J1),
    null_loaded_part_max_deviation_from_uniform=uniform_dev,
    rdiag_max_deviation_from_1_minus_1_over_n=rdiag_match,
    zero_column_nodes=[float(grid.grid[j]) for j in range(41) if not loaded[j]],
    xi_min_sampled=float(op.xi1[(r['forces'] > 1e-8) & op.valid].min()))
print('[A] loaded=%d rank=%d (loaded-1: %s)' % (n_loaded, rank, rank == n_loaded - 1))
print('[A] ||J*1||/s0=%.2e | null loaded-part dev from uniform=%.2e' % (J1, uniform_dev))
print('[A] max|rdiag - (1 - 1/n)on loaded|=%.2e' % rdiag_match)

# ---------- B. precision por direccion y por nodo ----------------------------
std_dir_um = 1.0 / s[:rank] * 1000.0          # 1/s_k en um (amplitud de modo)
counts = {str(a): int(np.sum(std_dir_um <= a)) for a in (0.5, 1.0, 5.0)}
# std por nodo condicionado al subespacio resuelto (proyeccion de las
# direcciones nulas excluida: los nodos nulos quedan con std infinita);
# la descomposicion es exacta porque los V_k de rango se anulan en los
# nodos con columna cero
Vr = V[:, :rank]
node_std_um = np.sqrt((Vr ** 2 / s[:rank] ** 2).sum(axis=1)) * 1000.0
node_std_um[~loaded] = np.inf
boundary = {}
for a in (1.0, 5.0):
    b = [float(grid.grid[j]) for j in range(41)
         if node_std_um[j] <= a and loaded[j]]
    boundary[str(a)] = dict(
        n_nodes=int(len(b)),
        xi_range=[min(b), max(b)] if b else None,
        max_xi=max(b) if b else None)
out['precision'] = dict(
    direction_std_um=std_dir_um.tolist(),
    directions_with_std_below_um=counts,
    node_std_um=[float(x) for x in node_std_um],
    boundary=boundary,
    note='std de amplitud por direccion singular (1/s_k, sigma=0.1 um, sin '
         'cotas); std por nodo condicionado al subespacio resuelto (las '
         'direcciones nulas quedan excluidas: std infinita)')
print('[B] direcciones con std<=0.5/1/5 um:', counts)
print('[B] nodos con std<=1 um: xi hasta', boundary['1.0']['max_xi'],
      '| <=5 um: xi hasta', boundary['5.0']['max_xi'])

# ---------- C1. bootstrap 0.394 (campana original) vs 0.369 (fase 4) --------
def med_bootstrap(values, n=10000, seed=1):
    rng = np.random.default_rng(seed)
    vals = np.asarray(values, float)
    meds = np.empty(n)
    for i in range(n):
        meds[i] = np.median(rng.choice(vals, len(vals), replace=True))
    return float(np.median(vals)), float(np.quantile(meds, .025)), float(np.quantile(meds, .975))

orig = [json.loads(l) for l in (PROJ / 'results' / 'q1_revision_2026-10-12' /
                                'monte_carlo_records.jsonl').read_text().splitlines() if l.strip()]
orig_cell = [x['dedendum_scaled_error'] for x in orig
             if x['sd_true'] == .25 and x['design'] == 'single300' and x['sigma_um'] == .1]
new = [json.loads(l) for l in (ROOT / 'results' / 'independent_validation' /
                               '04_mc_records.jsonl').read_text().splitlines() if l.strip()]
new_cell = [x['dedendum_scaled_error'] for x in new
            if x['sd_true'] == .25 and x['variant'] == 'legacy']
m1 = med_bootstrap(orig_cell)
m2 = med_bootstrap(new_cell)
out['mc_025_legacy_single300'] = dict(
    original_campaign=dict(n=len(orig_cell), median=m1[0], ci95=[m1[1], m1[2]]),
    phase4_cells=dict(n=len(new_cell), median=m2[0], ci95=[m2[1], m2[2]]),
    note='semillas disjuntas (original 0-99 vs base 20261022+k); bootstrap '
         'del mediana con 10000 remuestreos')
print('[C1] original n=%d med=%.3f CI=[%.3f,%.3f] | fase4 n=%d med=%.3f CI=[%.3f,%.3f]'
      % (len(orig_cell), m1[0], m1[1], m1[2], len(new_cell), m2[0], m2[1], m2[2]))

# ---------- C2. rangos porcentuales Tabla 1 (ablation) vs Fase 3 ------------
ab = json.loads((PROJ / 'results' / 'q1_revision_2026-10-12' /
                 'forward_ablation.json').read_text())
leg = [x for x in ab['results'] if x['variant'] == 'legacy']
bench = json.loads((ROOT / 'results' / 'independent_validation' /
                    '03_benchmark_reproduction.json').read_text())
bleg = [x for x in bench if x['variant'] == 'legacy']
out['percent_ranges'] = dict(
    table1_forward_ablation=dict(
        field_sample={k: leg[0][k] for k in ('case', 'torque_Nm') if k in leg[0]},
        difference_percent=[min(x['difference_percent'] for x in leg),
                            max(x['difference_percent'] for x in leg)],
        unmodified_normalized=[min(x['unmodified_normalized_percent'] for x in leg),
                               max(x['unmodified_normalized_percent'] for x in leg)]),
    phase3_recalculation=dict(
        relative_error_percent=[min(x['relative_error_percent'] for x in bleg),
                                max(x['relative_error_percent'] for x in bleg)]))
print('[C2] Tabla1/2 difference_percent: %.1f-%.1f | phase3 relative_error: %.1f-%.1f'
      % (out['percent_ranges']['table1_forward_ablation']['difference_percent'][0],
         out['percent_ranges']['table1_forward_ablation']['difference_percent'][1],
         out['percent_ranges']['phase3_recalculation']['relative_error_percent'][0],
         out['percent_ranges']['phase3_recalculation']['relative_error_percent'][1]))

# ---------- C3. dedendum Tabla 9 vs puntos de partida ------------------------
cross = json.loads((ROOT / 'results' / 'independent_validation' /
                    '03_cross_inverse.json').read_text())
rows9 = cross['rows']
start_match = {}
for variant, start in [('legacy', STARTS[1]), ('projected-energy', STARTS[0])]:
    rr = [x for x in rows9 if x['variant'] == variant][0]
    est = np.array(rr['estimate'])
    start_match[variant] = dict(
        estimate_dedendum=est[2:].tolist(), start_dedendum=start[2:].tolist(),
        equal=bool(np.allclose(est[2:], start[2:], atol=1e-9)),
        addendum_abs_error_mm=float(np.abs(est[0] - 0.02)),
        addendum_start_error=float(np.abs(est[1] - 0.75)))
out['table9_vs_starts'] = start_match
for v_, m_ in start_match.items():
    print('[C3] %-16s dedendum==start: %s | err h=%.4f mm err sa=%.4f'
          % (v_, m_['equal'], m_['addendum_abs_error_mm'], m_['addendum_start_error']))

# ---------- C4. xi_min del par 57/57 frente a sd=0.30/0.45 -------------------
bp = build_pair()
mg = GearContactModel(bp, micro1=TipRelief(p=2.0), micro2=None,
                      compliance_variant='projected-energy')
recs = [json.loads(l) for l in (ROOT / 'results' / 'independent_validation' /
                                '03_fe_cycle_v2.jsonl').read_text().splitlines() if l.strip()]
fractions = sorted({x['phase_fraction'] for x in recs})
interior = [f for f in fractions if not any(x['restricted_nominal_window']
                                            for x in recs if x['phase_fraction'] == f)]
phi_fe = np.array([f * 2 * np.pi / 57.0 for f in interior])
op57 = BatchedGapOperator(mg, 650.0, phi_positions=phi_fe)
r57 = op57.evaluate(np.array([0.02, 0.75, 0.0, 0.5]))
xi57 = float(op57.xi1[(r57['forces'] > 1e-8) & op57.valid].min())
out['xi_min_57_57'] = dict(xi_min=xi57, sd_cases=[0.30, 0.45],
                           both_sd_above_xi_min=bool(xi57 > 0.45),
                           note='soporte analitico en las 19 fases interiores; '
                                'relieve dedendum invisible para ambos casos '
                                'por la condicion de soporte')
print('[C4] xi_min(57/57, 650 Nm, fases interiores)=%.4f > sd=0.30 y 0.45: %s'
      % (xi57, xi57 > 0.45))

(ROOT / 'results' / 'independent_validation' / '09_resolution_corrections.json'
 ).write_text(json.dumps(out, indent=1))
print('written 09_resolution_corrections.json')
