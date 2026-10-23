"""
E3-alt: Search for non-uniqueness via grid search in Ca-sa plane.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
import matplotlib.pyplot as plt

from geometry.involute import InvoluteGear, GearPair
from geometry.microgeometry import TipRelief
from mechanics.compliance import GearContactModel
from mechanics.transmission_error import TransmissionError


def run_grid_search(torque_Nm: float = 100.0):
    print("=" * 60)
    print("E3-alt: Grid Search for Non-Uniqueness (Ca-sa plane)")
    print("=" * 60)

    g1 = InvoluteGear(z=24, m=3.0, alpha_deg=20.0, b=20.0)
    g2 = InvoluteGear(z=48, m=3.0, alpha_deg=20.0, b=20.0)
    pair = GearPair(g1, g2)

    micro1 = TipRelief(p=2.0)
    model = GearContactModel(pair, micro1=micro1, micro2=None, linearize_hertz=True)
    te = TransmissionError(model)

    Ca_vals = np.linspace(0.005, 0.060, 10)
    sa_vals = np.linspace(0.40, 0.95, 10)

    TE_curves = []
    params = []

    print("Evaluating grid...")
    for Ca in Ca_vals:
        for sa in sa_vals:
            theta = np.array([Ca, sa, 0.0, 0.0])
            res = te.compute_cycle(torque_Nm=torque_Nm, n_positions=30, theta1=theta)
            TE_curves.append(res["TE_lin_fluct"])
            params.append(theta)

    TE_curves = np.array(TE_curves)
    params = np.array(params)
    n = len(params)
    print(f"Grid size: {n}")

    # Find pairs with similar TE
    best_te = 1e9
    best_pair = None
    for i in range(n):
        for j in range(i + 1, n):
            te_d = np.linalg.norm(TE_curves[i] - TE_curves[j])
            if te_d < best_te:
                best_te = te_d
                best_pair = (i, j)

    print(f"Minimum TE distance found: {best_te:.4e}")
    if best_pair:
        i, j = best_pair
        print(f"Params i: {params[i]}")
        print(f"Params j: {params[j]}")
        print(f"Param dist: {np.linalg.norm(params[i] - params[j]):.4f}")

    # Plot heatmap of TE peak-to-peak
    p2p = np.array([np.ptp(te) for te in TE_curves]).reshape(len(Ca_vals), len(sa_vals))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    ax = axes[0]
    im = ax.imshow(p2p * 1e3, aspect="auto", origin="lower",
                   extent=[sa_vals[0], sa_vals[-1], Ca_vals[0]*1e3, Ca_vals[-1]*1e3],
                   cmap="viridis")
    ax.set_xlabel("sa (-)")
    ax.set_ylabel("Ca (um)")
    ax.set_title("TE peak-to-peak (um)")
    plt.colorbar(im, ax=ax)

    ax = axes[1]
    ax.plot(np.rad2deg(res["phi"]), TE_curves[i] * 1e3, "b-", label="Param set A")
    ax.plot(np.rad2deg(res["phi"]), TE_curves[j] * 1e3, "r--", label="Param set B")
    ax.set_xlabel("Pinion rotation (deg)")
    ax.set_ylabel("TE fluctuation (um)")
    ax.set_title(f"Closest TE pair (dist={best_te*1e3:.3f} um)")
    ax.legend()
    ax.grid(True)

    plt.tight_layout()
    out = Path(__file__).parent.parent / "results" / "E03_grid_search.png"
    plt.savefig(out, dpi=150)
    print(f"\nFigure saved to {out}")


if __name__ == "__main__":
    run_grid_search()

