"""Fase 2: auditoria mecanica del modelo de compliance.

Secciones:
  1. Desglose por componentes (flexion/cortante/axial/fundacion) para cada
     variante, con recomputacion independiente (verificacion cruzada).
  2. Positividad, continuidad y monotonicidad del acercamiento de par.
  3. Convergencia de cuadratura, convergencia angular, convergencia de
     derivadas, rigidez incremental dF/d(delta).
  4. Transiciones 1<->2 pares en contacto (entrega suave de carga).
  5. Simetria de engranaje identico (57/57 del benchmark).

Salida: reports/02_mechanical_components.json y consola.
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
from mechanics.compliance import GearContactModel, ToothCompliance, HertzianContact
from mechanics.batched_operator import BatchedGapOperator

OUT = {}
G0 = GearPair(InvoluteGear(24, 3, 20, 20), InvoluteGear(48, 3, 20, 20))
KORTA = GearPair(InvoluteGear(57, 2.6, 20, 23, pitch_thickness_mm=3.78),
                 InvoluteGear(57, 2.6, 20, 23, pitch_thickness_mm=3.78))
THETA = np.array([.02, .75, .005, .25])
SCALE = np.array([.05, 1, .01, 1])


# ---------- 1. componentes (recomputacion independiente) --------------------
def components(gear, u, variant, nq=96):
    """Replica la integracion de ToothCompliance devolviendo terminos."""
    tc = ToothCompliance(gear, variant=variant)
    r = gear.rb * np.sqrt(1 + u ** 2)
    alpha_r = np.arctan(u)
    r_fix = max(gear.rf, gear.rb * 1.0001)
    h = r - r_fix
    xi, wi = np.polynomial.legendre.leggauss(nq)
    xg = 0.5 * h * (xi + 1.0); wg = 0.5 * h * wi
    E, b = gear.E, gear.b
    G = gear.E / (2 * (1 + gear.nu))
    secs = [tc._section_at_radius(r_fix + x) for x in xg]
    I = np.array([b * s ** 3 / 12 for s, _ in secs])
    A = np.array([b * s for s, _ in secs])
    out = {}
    if variant == 'centerline-energy':
        rr = r_fix + xg
        ar = np.arccos(np.clip(gear.rb / rr, -1, 1))
        tt = np.array([s for s, _ in secs])
        raw = np.array([gear.tooth_thickness_at_radius(rv) for rv in rr])
        beta = tt / (2 * rr)
        width = 2 * rr * np.sin(beta)
        bsf = np.where(raw >= 0.2 * gear.m, np.tan(ar), beta)
        jac = np.cos(beta) + bsf * np.sin(beta)
        bc = tc._section_at_radius(r)[0] / (2 * r)
        Xc, Yc = r * np.sin(bc), r * np.cos(bc)
        fa = alpha_r - bc
        arm = (Yc - rr * np.cos(beta)) * np.cos(fa) - Xc * np.sin(fa)
        I2 = b * width ** 3 / 12; A2 = b * width
        out['bend'] = float(np.sum(wg * jac * arm ** 2 / (E * I2)))
        out['shear'] = float(1.2 * np.cos(fa) ** 2 * np.sum(wg * jac / (G * A2)))
        out['axial'] = float(np.sin(fa) ** 2 * np.sum(wg * jac / (E * A2)))
    else:
        if variant == 'projected-energy':
            t_c = tc._section_at_radius(r)[0]
            arm = (h - xg) * np.cos(alpha_r) - 0.5 * t_c * np.sin(alpha_r)
            out['bend'] = float(np.sum(wg * arm ** 2 / (E * I)))
            out['shear'] = float(1.2 * np.cos(alpha_r) ** 2 * np.sum(wg / (G * A)))
            out['axial'] = float(np.sin(alpha_r) ** 2 * np.sum(wg / (E * A)))
        else:
            sh = E if variant == 'legacy' else G
            out['bend'] = float(np.sum(wg * (h - xg) ** 2 / (E * I)))
            out['shear'] = float(1.2 * np.sum(wg / (sh * A)))
            out['axial'] = 0.0
    out['foundation'] = float(np.cos(alpha_r) ** 2 / (E * b))
    return out


sec1 = {}
for variant in ['legacy', 'shear-G', 'projected-energy', 'centerline-energy']:
    rows = []
    for u in [0.1, 0.3, 0.5, 0.8]:
        comp = components(G0.g1, u, variant, nq=24)
        tc = ToothCompliance(G0.g1, variant=variant)
        total_model = float(tc.flexibility(np.array([u]))[0])
        total_parts = float(sum(comp.values()))
        rows.append({'u': u, **comp, 'total': total_parts,
                     'model_total': total_model,
                     'crosscheck_rel_diff': abs(total_parts - total_model) / total_model})
    sec1[variant] = rows
OUT['1_components'] = sec1

# ---------- 2. positividad / continuidad / monotonicidad -------------------
sec2 = {}
for variant in ['legacy', 'shear-G', 'projected-energy', 'centerline-energy']:
    tc = ToothCompliance(G0.g1, variant=variant)
    u_tip = np.sqrt((G0.g1.ra / G0.g1.rb) ** 2 - 1)
    u_grid = np.linspace(0.02, u_tip * 0.995, 400)
    c = tc.flexibility(u_grid)
    du = u_grid[1] - u_grid[0]
    jumps = np.abs(np.diff(c)) / c[:-1]
    model = GearContactModel(G0, TipRelief(), compliance_variant=variant)
    K = 1 / (np.pi * model.hertz.E_star * model.hertz.b)
    states = [model.get_contact_state(p) for p in np.linspace(0, 0.05, 25)]
    c_pair = np.concatenate([s['c_lin'] for s in states])
    sec2[variant] = {
        'min_compliance': float(c.min()), 'max_compliance': float(c.max()),
        'all_positive': bool(np.all(c > 0)),
        'max_rel_jump': float(jumps.max()),
        'max_jump_at_u': float(u_grid[np.argmax(jumps)]),
        'monotonicity_margin_min_pair': float(np.min(c_pair) - 2 * K),
        'monotone_certified': bool(np.min(c_pair) - 2 * K > 0),
        'pair_approach_slope_at_100N': None}
    # pendiente dc/du (suavidad de la ley de rigidez global)
    sec2[variant]['max_abs_slope'] = float(np.max(np.abs(np.diff(c) / du)))
OUT['2_positivity_continuity'] = sec2

# ---------- 3. convergencia cuadratura / angular / derivadas ---------------
sec3 = {}
quad = {}
for variant in ['legacy', 'projected-energy']:
    for nq in [8, 24, 96]:
        u = np.array([0.15, 0.4, 0.7])
        vals = [float(sum(components(G0.g1, float(ui), variant, nq).values())) for ui in u]
        quad[f'{variant}_{nq}'] = vals
sec3['quadrature'] = quad
sec3['quadrature_rel_diff_24_vs_96'] = {
    k: float(np.max(np.abs(np.array(quad[k + '_24']) - np.array(quad[k + '_96']))
                    / np.array(quad[k + '_96']))) for k in ['legacy', 'projected-energy']}

ang = {}
for variant in ['legacy', 'projected-energy']:
    for n in [120, 240, 480]:
        op = BatchedGapOperator(GearContactModel(G0, TipRelief(), compliance_variant=variant),
                                 300.0, n)
        r = op.evaluate(THETA)
        pred = r['prediction']
        ang[f'{variant}_{n}'] = {'TE_pp_um': float((pred.max() - pred.min()) * 1000),
                                 'rms_um': float(np.sqrt(np.mean(pred ** 2)) * 1000),
                                 'force_residual_N': r['force_residual_N']}
sec3['angular'] = ang
for v in ['legacy', 'projected-energy']:
    sec3.setdefault('angular_rel_diff', {})[v] = {
        'pp_240_vs_480': abs(ang[f'{v}_240']['TE_pp_um'] - ang[f'{v}_480']['TE_pp_um']) / ang[f'{v}_480']['TE_pp_um'],
        'pp_120_vs_480': abs(ang[f'{v}_120']['TE_pp_um'] - ang[f'{v}_480']['TE_pp_um']) / ang[f'{v}_480']['TE_pp_um']}

deriv = {}
for variant in ['legacy', 'projected-energy']:
    op = BatchedGapOperator(GearContactModel(G0, TipRelief(), compliance_variant=variant), 300.0, 120)
    Ja = op.evaluate(THETA, jacobian=True)['jacobian']
    errs = {}
    for h in [1e-3, 1e-4, 1e-5, 1e-6]:
        fd = np.zeros_like(Ja)
        for j in range(4):
            v = np.zeros(4); v[j] = h * SCALE[j]
            fd[:, j] = (op.evaluate(THETA + v)['prediction'] - op.evaluate(THETA - v)['prediction']) / (2 * h * SCALE[j])
        errs[f'{h:g}'] = float(np.max(np.abs(fd - Ja) / np.maximum(np.abs(Ja), 1e-12)))
    deriv[variant] = errs
sec3['derivative_convergence'] = deriv

# rigidez incremental dS/d(delta) en posicion media de ciclo
stiff = {}
for variant in ['legacy', 'projected-energy']:
    model = GearContactModel(G0, TipRelief(), compliance_variant=variant)
    phi_mid = G0.rotation_for_mesh(240)[0][0]
    state = model.get_contact_state(phi_mid, theta1=THETA)
    F_target = 1000 * 300 / G0.g1.rb
    from mechanics.contact_solver import ContactSolver
    solver = ContactSolver(model)
    p, delta, _ = solver.solve_for_delta(state['g'], state['c_lin'], state['r_eq'], F_target)
    mask = p > 1e-12
    hprime = model.hertz.stiffness_derivative(p[mask], state['r_eq'][mask])
    dS = float(np.sum(1 / (state['c_lin'][mask] + hprime)))
    eps = 1e-7
    Sp, _ = solver._forces_for_delta(state['g'], state['c_lin'], state['r_eq'], delta + eps)
    Sm, _ = solver._forces_for_delta(state['g'], state['c_lin'], state['r_eq'], delta - eps)
    dS_fd = (Sp - Sm) / (2 * eps)
    stiff[variant] = {'analytic_dS_ddelta_N_per_mm': dS, 'fd_dS_ddelta': dS_fd,
                      'rel_diff': abs(dS - dS_fd) / dS_fd}
sec3['incremental_stiffness'] = stiff
OUT['3_convergence'] = sec3

# ---------- 4. transiciones 1 <-> 2 pares ---------------------------------
sec4 = {}
for variant in ['legacy', 'projected-energy']:
    op = BatchedGapOperator(GearContactModel(G0, TipRelief(), compliance_variant=variant), 300.0, 240)
    r = op.evaluate(THETA)
    n_contact = np.sum(r['forces'] > 1e-8, axis=1)
    # ventana de transicion: donde cambia el numero de pares
    changes = np.where(np.diff(n_contact) != 0)[0]
    handover = []
    for ix in changes:
        i0, i1 = max(0, ix - 3), min(240, ix + 4)
        F = r['forces'][i0:i1]
        entering = np.argmax(np.diff(F, axis=0) > 0, axis=0)
        handover.append({'transition_at_index': int(ix),
                         'n_before': int(n_contact[ix]), 'n_after': int(n_contact[ix + 1]),
                         'total_force_stable': float(np.max(np.abs(F.sum(axis=1) - r['forces'][i0:i1].sum(axis=1)[0]))),
                         'max_pair_force_jump_N': float(np.max(np.abs(np.diff(F, axis=0))))})
    sec4[variant] = {'min_pairs': int(n_contact.min()), 'max_pairs': int(n_contact.max()),
                     'n_transitions': len(changes),
                     'delta_max_step_between_positions_um':
                         float(np.max(np.abs(np.diff(r['delta']))) * 1000),
                     'handover_samples': handover[:4]}
OUT['4_transitions'] = sec4

# ---------- 5. simetria engranaje identico 57/57 --------------------------
sec5 = {}
model = GearContactModel(KORTA, TipRelief(), compliance_variant='projected-energy')
op = BatchedGapOperator(model, 650.0, 240)
r = op.evaluate(np.array([0.0, 0.75, 0.0, 0.3]))
pred = r['prediction']
mir = pred[::-1]
sec5['korta_identical_gears'] = {
    'TE_pp_um': float((pred.max() - pred.min()) * 1000),
    'max_abs_antisymmetric_component_um': float(np.max(np.abs(pred - mir)) * 1000),
    'note': 'par identico: la curva centrada debe ser antisimmetrica respecto a mid-mesh (pred[::-1] = -pred)'}
pred_c = pred - 0.5 * (pred + mir)
sec5['antisymmetry_residual_um'] = float(np.max(np.abs(0.5 * (pred + mir))) * 1000)
OUT['5_symmetry'] = sec5

(ROOT / 'reports' / '02_mechanical_components.json').write_text(json.dumps(OUT, indent=1))
print(json.dumps(OUT, indent=1)[:6000])
print('... written to reports/02_mechanical_components.json')
