"""Debug V6: barrido fino alrededor de phi=1.7 deg (geometria Korta, 350 Nm,
sin modificacion) para localizar la discontinuidad en delta(phi).

Imprime TODOS los pares del estado (no solo los activos) con gaps a 5
decimales, y marcas de clamping de los angulos de rodadura.
"""
import sys
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from geometry.involute import InvoluteGear, GearPair
from geometry.microgeometry import TipRelief
from mechanics.compliance import GearContactModel
from mechanics.contact_solver import ContactSolver

Z, M_MOD, ALPHA_DEG, B = 57, 2.6, 20.0, 23.0
HA_P = (154.50 - 148.20) / (2.0 * 2.60)
HF_P = 1.25
A_WORK = 150.0


def build(linearize_hertz):
    g1 = InvoluteGear(z=Z, m=M_MOD, alpha_deg=ALPHA_DEG, b=B,
                      haP=HA_P, hfP=HF_P)
    g2 = InvoluteGear(z=Z, m=M_MOD, alpha_deg=ALPHA_DEG, b=B,
                      haP=HA_P, hfP=HF_P)
    pair = GearPair(g1, g2, center_distance=A_WORK)
    model = GearContactModel(pair, micro1=None, micro2=None,
                             linearize_hertz=linearize_hertz)
    return pair, ContactSolver(model)


def sweep(linearize_hertz, phi0=1.55, phi1=1.95, step=0.01, torque=350.0):
    pair, sol = build(linearize_hertz)
    rb = pair.g1.rb
    u_tip1 = np.sqrt((pair.g1.ra / rb) ** 2 - 1.0)
    u_tip2 = np.sqrt((pair.g2.ra / pair.g2.rb) ** 2 - 1.0)
    print(f"=== linearize_hertz={linearize_hertz} | rb={rb:.3f} pb={pair.pb:.4f} "
          f"u_tip1={u_tip1:.4f} u_tip2={u_tip2:.4f} ===")
    phis = np.arange(phi0, phi1 + 1e-12, step)
    prev_n_active = None
    for phi in phis:
        res = sol.solve_position(phi1=np.deg2rad(phi), torque_Nm=torque)
        st = res["state"]
        p = res["p"]
        g = res["g"]
        active = p > 1e-9
        u1_raw = (pair.g1.rb * np.tan(pair.alpha_w) + st["s_k"]) / rb
        u2_raw = (pair.g2.rb * np.tan(pair.alpha_w) - st["s_k"]) / pair.g2.rb
        marks = []
        for i, k in enumerate(st["k"]):
            c1 = "T" if u1_raw[i] > u_tip1 else ("B" if u1_raw[i] < 0 else " ")
            c2 = "T" if u2_raw[i] > u_tip2 else ("B" if u2_raw[i] < 0 else " ")
            marks.append(f"{c1}{c2}")
        seg = " | ".join(
            f"k={int(k)} g={g[i]:8.5f} p={p[i]:8.2f} [{marks[i]}] u1={st['u1'][i]:.3f} u2={st['u2'][i]:.3f}"
            for i, k in enumerate(st["k"]))
        n_act = int(np.count_nonzero(active))
        flag = "  <<<< N_ACTIVE CHANGE" if prev_n_active is not None and n_act != prev_n_active else ""
        print(f"phi={phi:7.4f} delta={res['delta'] * 1e3:9.4f} um "
              f"S={p.sum():8.2f} n={n_act}{flag}\n    {seg}")
        prev_n_active = n_act


if __name__ == "__main__":
    sweep(False)
    print()
    sweep(True)
