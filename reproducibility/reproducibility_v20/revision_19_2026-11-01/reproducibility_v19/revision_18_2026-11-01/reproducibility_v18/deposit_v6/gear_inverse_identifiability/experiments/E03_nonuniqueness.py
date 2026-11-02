"""
E3: Demonstration of non-uniqueness.

Search for multiple parameter sets that produce nearly identical TE responses.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import fclusterdata

from geometry.involute import InvoluteGear, GearPair
from geometry.microgeometry import TipRelief
from mechanics.compliance import GearContactModel
from mechanics.transmission_error import TransmissionError
from inverse.reconstruction import InverseReconstructor


def run_nonuniqueness(
    torque_Nm: float = 100.0,
    n_starts: int = 40,
    n_positions: int = 120,
    seed: int = 20261012,
):
    print("=" * 60)
    print("E3: Non-Uniqueness Search (Multistart)")
    print("=" * 60)

    g1 = InvoluteGear(z=24, m=3.0, alpha_deg=20.0, b=20.0)
    g2 = InvoluteGear(z=48, m=3.0, alpha_deg=20.0, b=20.0)
    pair = GearPair(g1, g2)

    micro1 = TipRelief(p=2.0)
    model = GearContactModel(pair, micro1=micro1, micro2=None, linearize_hertz=False)
    te = TransmissionError(model)

    # True parameters
    theta_true = np.array([0.020, 0.75, 0.005, 0.25])  # mm
    print(f"True theta: {theta_true}")

    # Generate observations (use same n_positions as forward model in inversion for speed)
    res_true = te.compute_cycle(torque_Nm=torque_Nm, n_positions=n_positions, theta1=theta_true)
    y_obs = res_true["TE_lin_fluct"]

    bounds = np.array([
        [0.0, 0.100],   # Ca
        [0.3, 0.95],    # sa
        [0.0, 0.050],   # Cd
        [0.05, 0.50],   # sd
    ])
    scale = np.array([0.05, 1.0, 0.01, 1.0])

    recon = InverseReconstructor(te, np.array([torque_Nm]), bounds, theta_scale=scale, n_positions_forward=n_positions)
    rng = np.random.default_rng(seed)

    # Multistart optimization
    print(f"\nRunning {n_starts} optimizations from random seeds...")
    solutions = []
    for i in range(n_starts):
        theta0 = rng.uniform(bounds[:, 0], bounds[:, 1])
        result = recon.reconstruct(y_obs, theta0=theta0, verbose=0, max_nfev=200)
        if result["success"] or result["rmse"] < 1e-5:
            solutions.append({
                "theta": result["theta"],
                "rmse": result["rmse"],
                "cost": result["cost"],
            })
        if (i + 1) % 10 == 0:
            print(f"  Completed {i+1}/{n_starts}")

    print(f"Converged solutions: {len(solutions)}")
    if len(solutions) == 0:
        print("No converged solutions found.")
        return

    thetas = np.array([s["theta"] for s in solutions])
    rmses = np.array([s["rmse"] for s in solutions])

    # Normalize for clustering
    theta_norm = thetas / scale

    # Hierarchical clustering
    T = fclusterdata(theta_norm, t=1.0, criterion="distance", metric="euclidean")
    n_clusters = len(np.unique(T))
    print(f"Distinct clusters found: {n_clusters}")

    # Best solution per cluster
    cluster_best = []
    for cid in np.unique(T):
        mask = T == cid
        idx = np.argmin(rmses[mask])
        cluster_best.append({
            "cluster": cid,
            "theta": thetas[mask][idx],
            "rmse": rmses[mask][idx],
        })

    # Sort by RMSE
    cluster_best.sort(key=lambda x: x["rmse"])

    print("\n--- Best solutions per cluster ---")
    for cb in cluster_best:
        print(f"Cluster {cb['cluster']}: theta={cb['theta']}, RMSE={cb['rmse']:.3e}")

    # Geometric error between best distinct clusters
    if n_clusters >= 2:
        t1 = cluster_best[0]["theta"]
        t2 = cluster_best[1]["theta"]
        param_dist = np.linalg.norm(t1 - t2)
        print(f"\nDistance between top-2 clusters: {param_dist:.4f} mm (params mixed units)")

        # Compute TE for both
        r1 = te.compute_cycle(torque_Nm=torque_Nm, n_positions=120, theta1=t1)
        r2 = te.compute_cycle(torque_Nm=torque_Nm, n_positions=120, theta1=t2)
        te_dist = np.linalg.norm(r1["TE_lin_fluct"] - r2["TE_lin_fluct"])
        print(f"TE curve distance between top-2: {te_dist:.3e} mm")

    # ============================================================
    # Plots
    # ============================================================
    fig, axes = plt.subplots(2, 2, figsize=(11, 9))

    # Scatter matrix of converged solutions
    labels = ["Ca", "sa", "Cd", "sd"]
    for i in range(4):
        for j in range(4):
            ax = axes[i // 2, j % 2] if (i < 2 and j < 2) else None
        # Simplified: just plot Ca vs sa
    ax = axes[0, 0]
    scatter = ax.scatter(thetas[:, 0] * 1e3, thetas[:, 1], c=np.log10(rmses + 1e-15), cmap="viridis", edgecolors="k")
    ax.scatter(theta_true[0] * 1e3, theta_true[1], c="red", marker="*", s=200, label="True")
    ax.set_xlabel("Ca (um)")
    ax.set_ylabel("sa (-)")
    ax.set_title("Converged solutions (Ca vs sa)")
    plt.colorbar(scatter, ax=ax, label="log10(RMSE)")
    ax.legend()
    ax.grid(True)

    ax = axes[0, 1]
    ax.scatter(thetas[:, 2] * 1e3, thetas[:, 3], c=np.log10(rmses + 1e-15), cmap="viridis", edgecolors="k")
    ax.scatter(theta_true[2] * 1e3, theta_true[3], c="red", marker="*", s=200, label="True")
    ax.set_xlabel("Cd (um)")
    ax.set_ylabel("sd (-)")
    ax.set_title("Converged solutions (Cd vs sd)")
    plt.colorbar(scatter, ax=ax, label="log10(RMSE)")
    ax.legend()
    ax.grid(True)

    # TE curves for top distinct clusters
    ax = axes[1, 0]
    ax.plot(np.rad2deg(res_true["phi"]), res_true["TE_lin_fluct"] * 1e3, "k-", lw=2, label="True")
    colors = plt.cm.tab10.colors
    for idx, cb in enumerate(cluster_best[:3]):
        r = te.compute_cycle(torque_Nm=torque_Nm, n_positions=120, theta1=cb["theta"])
        ax.plot(np.rad2deg(r["phi"]), r["TE_lin_fluct"] * 1e3, "--", color=colors[idx], label=f"Cluster {cb['cluster']}")
    ax.set_xlabel("Pinion rotation (deg)")
    ax.set_ylabel("TE fluctuation (um)")
    ax.set_title("TE curves of distinct solutions")
    ax.legend()
    ax.grid(True)

    # Profile shapes for top 2 clusters
    ax = axes[1, 1]
    s_eval = np.linspace(0, 1, 200)
    h_true = micro1.evaluate(s_eval, theta_true)
    ax.plot(s_eval, h_true * 1e3, "k-", lw=2, label="True")
    if n_clusters >= 2:
        for idx, cb in enumerate(cluster_best[:2]):
            h = micro1.evaluate(s_eval, cb["theta"])
            ax.plot(s_eval, h * 1e3, "--", color=colors[idx], label=f"Cluster {cb['cluster']}")
    ax.set_xlabel("s (-)")
    ax.set_ylabel("Modification h (um)")
    ax.set_title("Reconstructed profile shapes")
    ax.legend()
    ax.grid(True)

    plt.tight_layout()
    out = Path(__file__).parent.parent / "results" / "E03_nonuniqueness.png"
    plt.savefig(out, dpi=150)
    print(f"\nFigure saved to {out}")

    return {
        "n_clusters": n_clusters,
        "cluster_best": cluster_best,
        "thetas": thetas,
        "rmses": rmses,
    }


if __name__ == "__main__":
    np.random.seed(42)
    run_nonuniqueness(torque_Nm=100.0, n_starts=5)

