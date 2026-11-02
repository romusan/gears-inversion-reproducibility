"""
E2: Inverse recovery without noise.

Generate synthetic data from a known theta_true, then reconstruct.
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
from inverse.reconstruction import InverseReconstructor


def run_recovery(torque_Nm: float = 100.0):
    print("=" * 60)
    print("E2: Inverse Recovery (Noise-Free)")
    print("=" * 60)

    g1 = InvoluteGear(z=24, m=3.0, alpha_deg=20.0, b=20.0)
    g2 = InvoluteGear(z=48, m=3.0, alpha_deg=20.0, b=20.0)
    pair = GearPair(g1, g2)

    micro1 = TipRelief(p=2.0)
    model = GearContactModel(pair, micro1=micro1, micro2=None)
    te = TransmissionError(model)

    # True parameters
    theta_true = np.array([0.020, 0.75, 0.005, 0.25])  # mm
    print(f"True theta: {theta_true}")

    # Generate synthetic observations.
    # NOTE: observations must use the same n_positions as the forward model
    # inside the reconstructor (stacked residual vectors must match).
    n_obs = 60
    res_true = te.compute_cycle(torque_Nm=torque_Nm, n_positions=n_obs, theta1=theta_true)
    y_obs = res_true["TE_lin_fluct"]

    # Bounds: physical / manufacturing plausible
    bounds = np.array([
        [0.0, 0.100],   # Ca [mm]
        [0.3, 0.95],    # sa [-]
        [0.0, 0.050],   # Cd [mm]
        [0.05, 0.50],   # sd [-]
    ])
    scale = np.array([0.05, 1.0, 0.01, 1.0])

    recon = InverseReconstructor(
        te, np.array([torque_Nm]), bounds, theta_scale=scale,
        n_positions_forward=n_obs,
    )

    # Recover from exact initial guess (sanity check)
    print("\n--- Recovery from exact initial guess ---")
    result_exact = recon.reconstruct(y_obs, theta0=theta_true)
    print(f"Recovered:   {result_exact['theta']}")
    print(f"RMSE: {result_exact['rmse']:.6e} mm")

    # Recover from perturbed initial guess
    print("\n--- Recovery from perturbed initial guess ---")
    theta_pert = theta_true * np.array([1.3, 0.9, 2.0, 1.2])
    theta_pert = np.clip(theta_pert, bounds[:, 0], bounds[:, 1])
    result_pert = recon.reconstruct(y_obs, theta0=theta_pert)
    print(f"Perturbed0:  {theta_pert}")
    print(f"Recovered:   {result_pert['theta']}")
    print(f"RMSE: {result_pert['rmse']:.6e} mm")

    # Parameter error
    err = np.abs(result_pert["theta"] - theta_true)
    rel_err = err / (np.abs(theta_true) + 1e-12)
    print(f"Abs error:   {err}")
    print(f"Rel error:   {rel_err}")

    # Plot TE curves
    res_rec = te.compute_cycle(torque_Nm=torque_Nm, n_positions=120, theta1=result_pert["theta"])

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    ax = axes[0]
    ax.plot(np.rad2deg(res_true["phi"]), res_true["TE_lin_fluct"] * 1e3, "b-", label="True")
    ax.plot(np.rad2deg(res_rec["phi"]), res_rec["TE_lin_fluct"] * 1e3, "r--", label="Recovered")
    ax.set_xlabel("Pinion rotation (deg)")
    ax.set_ylabel("TE fluctuation (um)")
    ax.set_title("Noise-free recovery")
    ax.legend()
    ax.grid(True)

    ax = axes[1]
    x_labels = ["Ca", "sa", "Cd", "sd"]
    x_pos = np.arange(len(x_labels))
    ax.bar(x_pos - 0.2, theta_true * np.array([1e3, 1, 1e3, 1]), 0.4, label="True", color="steelblue")
    ax.bar(x_pos + 0.2, result_pert["theta"] * np.array([1e3, 1, 1e3, 1]), 0.4, label="Recovered", color="coral")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels)
    ax.set_ylabel("Value (Ca,Cd in um; sa,sd dimless)")
    ax.set_title("Parameter comparison")
    ax.legend()
    ax.grid(True, axis="y")

    plt.tight_layout()
    out = Path(__file__).parent.parent / "results" / "E02_recovery.png"
    plt.savefig(out, dpi=150)
    print(f"\nFigure saved to {out}")

    return {
        "theta_true": theta_true,
        "theta_recovered": result_pert["theta"],
        "rmse": result_pert["rmse"],
        "rel_error": rel_err,
    }


if __name__ == "__main__":
    run_recovery(torque_Nm=100.0)

