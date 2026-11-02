"""Fase 3.2/3.5: curva angular FE 2D del acercamiento (57/57, 650 Nm).

Reutiliza la infraestructura verificada de run_fe2d (root copy con .venv):
  - contacto sin friccion, normales fijas, deformacion plana, deformaciones
    pequenas, cubo empotrado (radio asumido 25 mm), raiz aproximada
    (root_trim 0.4 mm), P1 nodal, h=0.5, step=0.02, patch=0.35.
  - La matriz condensada H se calcula una vez por fase (malla) y se reutiliza
    para todos los casos de relieve (H no depende del gap).

Casos: unmodified, addendum-only (0.02,0.75,0,0.5), dedendum (0.02,0.75,0.005,0.30)
       (relieve de pinon, p=2, dominio xi = u/u_tip).

Salida incremental: results/independent_validation/03_fe_cycle.jsonl
Uso: python phase3_fe_cycle.py [i0] [i1]   # subrango de fases, reanudable
"""
import sys, json, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                          # deposit_v6/
WORK_FE = ROOT.parent / 'fe2d'              # copia de trabajo con .venv
sys.path.insert(0, str(WORK_FE))
sys.path.insert(0, str(ROOT / 'gear_inverse_identifiability' / 'src'))

import run_fe2d as fe                       # configura .venv de paquetes FE
import numpy as np
from geometry.microgeometry import TipRelief

OUT = ROOT / 'results' / 'independent_validation'
OUT.mkdir(parents=True, exist_ok=True)
PATH = OUT / '03_fe_cycle_v2.jsonl'

H_MM = 0.5
STEP = 0.02
PATCH = 0.35
BORE = 25.0
ROOT_TRIM = 0.4
N_PHASES = 25
FRACTIONS = np.arange(N_PHASES) / N_PHASES

MICRO = TipRelief(p=2.0)
U_TIP = float(np.sqrt((fe.RA / fe.RB) ** 2 - 1))
CASES = {
    'unmodified': None,
    'addendum': np.array([0.02, 0.75, 0.0, 0.5]),
    'dedendum': np.array([0.02, 0.75, 0.005, 0.30]),
    'dedendum-deep': np.array([0.02, 0.75, 0.005, 0.45]),
}


def relief_gap(contact, theta):
    """Devuelve el vector de relieve concatenado para el gap (pinon)."""
    parts = []
    for c in contact:
        xi = np.clip(np.asarray(c['v1']) / U_TIP, 0.0, 1.0)
        parts.append(MICRO.evaluate(xi, theta))
    return np.concatenate(parts)


def one_phase(fraction):
    t0 = time.time()
    clipped = False
    try:
        contact = fe.contacts(fraction, PATCH, STEP, allow_clipped=False)
    except ValueError:
        contact = fe.contacts(fraction, PATCH, STEP, allow_clipped=True)
        clipped = True
    bodies = [fe.mesh_body(contact, i, H_MM, BORE, ROOT_TRIM,
                           f'phase3_f{fraction:g}_b{i}', 1, 'nodal', None, 1)
              for i in (1, 2)]
    H = sum(b['H'] for b in bodies)
    gap0 = np.concatenate([x['gap'] for x in contact])
    F = 650000.0 / fe.RB
    rec_base = dict(phase_fraction=float(fraction),
                    phi_rad=float(fraction * 2 * np.pi / fe.Z),
                    restricted_nominal_window=clipped,
                    clipped_contact_domains=[bool(c['truncated']) for c in contact],
                    nominal_pairs=len(contact),
                    nodes=[b['nodes'] for b in bodies],
                    h_mm=H_MM, bore_mm=BORE, root_trim_mm=ROOT_TRIM,
                    traction='nodal_P1', seconds_mesh_factor=time.time() - t0)
    out = []
    for name, theta in CASES.items():
        gap = gap0 if theta is None else gap0 + relief_gap(contact, theta)
        sol = fe.solve_contact(H, gap, F)
        out.append(dict(case=name,
                        approach_um=float(sol['delta'] * 1000),
                        k_incremental_N_um=sol['k_N_um'],
                        pair_forces_N=[float(p) for p in
                                       np.add.reduceat(sol['p'], np.r_[0, np.cumsum([len(c['x']) for c in contact])[:-1]])],
                        force_residual_N=sol['force_residual_N'],
                        contact_residual_mm=sol['gap_residual_mm'],
                        **rec_base))
    return out


def main(i0, i1):
    done = set()
    if PATH.exists():
        done = {json.loads(s)['phase_fraction']
                for s in PATH.read_text().splitlines() if s.strip()}
    with PATH.open('a', encoding='utf-8') as f:
        for fraction in FRACTIONS[i0:i1]:
            if float(fraction) in done:
                continue
            rows = one_phase(float(fraction))
            for r in rows:
                f.write(json.dumps(r) + '\n')
            f.flush()
            print('phase', round(float(fraction), 4),
                  {r['case']: round(r['approach_um'], 3) for r in rows},
                  'restricted' if rows[0]['restricted_nominal_window'] else '', flush=True)


if __name__ == '__main__':
    a = sys.argv[1:]
    main(int(a[0]) if a else 0, int(a[1]) if len(a) > 1 else N_PHASES)
