"""
E8: Generalization out-of-sample.

Tests whether the inverse reconstruction framework — bounds, parameter
scaling, and initialization strategy — generalizes beyond the base
geometry used throughout E1-E7:

* Geometry: 3 additional gear pairs spanning module, tooth-number ratio,
  and face width (plus the base pair as reference).
* Modification space: nominal relief, extended relief (deeper/longer,
  which activates complementarity switching), and tip-only relief
  (Cd = 0, exercising the lower bound).
* Bounds/scaling adapt to the module: Ca in [0, 0.035*m] mm, Cd in
  [0, 0.0175*m] mm (i.e., up to 35/17.5 µm per module unit), reflecting
  manufacturing practice.

All runs are noise-free (noise robustness is characterized in E4) and
start from the same perturbed initial guess rule used in E2/E4/E7.

Run in chunks (records are idempotent):
    python experiments/E08_generalization.py run  <i0> <i1>
    python experiments/E08_generalization.py plot
"""

import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
import matplotlib.pyplot as plt

from geometry.involute import InvoluteGear, GearPair
from geometry.microgeometry import TipRelief
from mechanics.compliance import GearContactModel
from mechanics.transmission_error import TransmissionError
from inverse.reconstruction import InverseReconstructor

N_OBS = 60
PARAM_LABELS = ["Ca", "sa", "Cd", "sd"]

# (name, z1, z2, module, face width)
GEOMETRIES = [
    ("G0-base", 24, 48, 3.0, 20.0),
    ("G1-fine", 20, 60, 2.5, 15.0),
    ("G2-coarse", 30, 45, 4.0, 25.0),
    ("G3-small", 16, 64, 2.0, 12.0),
]

# (name, theta_true) — tip relief [Ca mm, sa, Cd mm, sd]
MODIFICATIONS = [
    ("nominal", np.array([0.020, 0.75, 0.005, 0.25])),
    ("extended", np.array([0.045, 0.55, 0.012, 0.40])),
    ("tip-only", np.array([0.030, 0.60, 0.000, 0.25])),
]

LOAD_CASES = {
    "single": np.array([100.0]),
    "multi": np.array([50.0, 300.0]),
}

RESULTS = Path(__file__).parent.parent / "results"
RECORDS = RESULTS / "E08_records.jsonl"


def bounds_and_scale(m: float):
    """Module-adapted physical bounds and conditioning scales."""
    bounds = np.array([
        [0.0, 0.035 * m],    # Ca [mm]
        [0.3, 0.95],         # sa [-]
        [0.0, 0.0175 * m],   # Cd [mm]
        [0.05, 0.50],        # sd [-]
    ])
    scale = np.array([0.05 * m / 3.0, 1.0, 0.01 * m / 3.0, 1.0])
    return bounds, scale


def build_te(geom):
    _, z1, z2, m, b = geom
    g1 = InvoluteGear(z=z1, m=m, alpha_deg=20.0, b=b)
    g2 = InvoluteGear(z=z2, m=m, alpha_deg=20.0, b=b)
    pair = GearPair(g1, g2)
    model = GearContactModel(pair, micro1=TipRelief(p=2.0), micro2=None,
                             linearize_hertz=False)
    return TransmissionError(model)


def task_list():
    tasks = []
    for geom in GEOMETRIES:
        for mod_name, theta_true in MODIFICATIONS:
            # Keep the extended case only where the module-adapted bounds
            # contain it (Ca <= 0.035 m, Cd <= 0.0175 m).
            bounds, _ = bounds_and_scale(geom[3])
            if np.any(theta_true < bounds[:, 0]) or np.any(theta_true > bounds[:, 1]):
                continue
            for case_name, torques in LOAD_CASES.items():
                tasks.append(dict(geom=geom[0], mod=mod_name, case=case_name,
                                  theta_true=theta_true.tolist()))
    return tasks


def run_one(task):
    geom = next(g for g in GEOMETRIES if g[0] == task["geom"])
    m = geom[3]
    theta_true = np.array(task["theta_true"])
    bounds, scale = bounds_and_scale(m)

    te = build_te(geom)
    torques = LOAD_CASES[task["case"]]

    # Fixed perturbed initial guess (same rule as E2/E4/E7)
    theta0 = np.clip(theta_true * np.array([1.3, 0.9, 2.0, 1.2]),
                     bounds[:, 0], bounds[:, 1])

    y_obs = []
    for T in torques:
        res = te.compute_cycle(torque_Nm=T, n_positions=N_OBS,
                               theta1=theta_true)
        y_obs.append(res["TE_lin_fluct"])
    y_obs = np.concatenate(y_obs)

    recon = InverseReconstructor(te, torques, bounds, theta_scale=scale,
                                 n_positions_forward=N_OBS)
    result = recon.reconstruct(y_obs, theta0=theta0)

    theta_est = np.array(result["theta"])
    abs_err = np.abs(theta_est - theta_true)
    rel_err = abs_err / (np.abs(theta_true) + 1e-12)
    # Characteristic scales for normalized error: when theta_true is 0
    # (e.g. tip-only relief), relative error is meaningless; normalize by
    # a module-adapted characteristic magnitude instead.
    char = np.array([0.02, 0.25, 0.005, 0.25]) * (m / 3.0)
    norm_err = abs_err / np.maximum(np.abs(theta_true), char)
    hit = ((theta_est <= bounds[:, 0] + 1e-9)
           | (theta_est >= bounds[:, 1] - 1e-9))

    return dict(
        geom=task["geom"], mod=task["mod"], case=task["case"],
        m=m, z1=geom[1], z2=geom[2], b=geom[4],
        theta_true=theta_true.tolist(), theta_est=theta_est.tolist(),
        fit_rmse_mm=result["rmse"],
        param_abs_err=abs_err.tolist(),
        param_rel_err=rel_err.tolist(),
        param_norm_err=norm_err.tolist(),
        worst_rel_err=float(np.max(rel_err)),
        worst_norm_err=float(np.max(norm_err)),
        hit_bound=hit.tolist(),
        nfev=int(result["nfev"]), success=bool(result["success"]),
    )


def run_chunk(i0, i1, workers=4):
    tasks = task_list()
    i1 = min(i1, len(tasks))
    existing = set()
    if RECORDS.exists():
        with open(RECORDS, "r", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                existing.add((r["geom"], r["mod"], r["case"]))
    chunk = [t for t in tasks[i0:i1]
             if (t["geom"], t["mod"], t["case"]) not in existing]
    print(f"Tasks {i0}:{i1}: {len(chunk)} to run "
          f"({len(existing)} already on record)")

    import concurrent.futures as cf
    with open(RECORDS, "a", encoding="utf-8") as fout:
        if workers <= 1:
            for t in chunk:
                rec = run_one(t)
                fout.write(json.dumps(rec) + "\n")
                fout.flush()
                print(f"  done {t['geom']:9s} {t['mod']:8s} {t['case']:6s} "
                      f"worst_rel={rec['worst_rel_err']:.3e} "
                      f"rmse={rec['fit_rmse_mm']:.2e} "
                      f"bounds={any(rec['hit_bound'])}", flush=True)
        else:
            with cf.ProcessPoolExecutor(max_workers=workers) as pool:
                futs = {pool.submit(run_one, t): t for t in chunk}
                for fut in cf.as_completed(futs):
                    t = futs[fut]
                    rec = fut.result()
                    fout.write(json.dumps(rec) + "\n")
                    fout.flush()
                    print(f"  done {t['geom']:9s} {t['mod']:8s} {t['case']:6s} "
                          f"worst_rel={rec['worst_rel_err']:.3e} "
                          f"rmse={rec['fit_rmse_mm']:.2e} "
                          f"bounds={any(rec['hit_bound'])}", flush=True)
    print(f"Records file: {RECORDS}")


def load_records():
    with open(RECORDS, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def worst_norm(rec):
    """Normalized worst-parameter error; recomputed for older records that
    lack the field (records store abs errors, theta_true, and module)."""
    if "worst_norm_err" in rec:
        return rec["worst_norm_err"]
    char = np.array([0.02, 0.25, 0.005, 0.25]) * (rec["m"] / 3.0)
    tt = np.array(rec["theta_true"])
    ae = np.array(rec["param_abs_err"])
    return float(np.max(ae / np.maximum(np.abs(tt), char)))


def plot():
    recs = load_records()
    if not recs:
        raise SystemExit("No records found; run the experiment first.")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))

    # (a) worst-parameter relative error by geometry (median over mods/loads)
    ax = axes[0]
    geoms = [g[0] for g in GEOMETRIES]
    x = np.arange(len(geoms))
    for j, case in enumerate(["single", "multi"]):
        meds = []
        for g in geoms:
            errs = [max(worst_norm(r), 1e-12) for r in recs
                    if r["geom"] == g and r["case"] == case]
            meds.append(np.median(errs) if errs else np.nan)
        ax.bar(x + (j - 0.5) * 0.35, meds, 0.35,
               label=f"{case} load", alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(geoms, rotation=20)
    ax.set_ylabel("Median worst-parameter relative error")
    ax.set_title("(a) Recovery across geometries")
    ax.set_yscale("log")
    ax.axhline(1e-2, color="k", ls="--", lw=0.8)
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)

    # (b) estimated vs true for Ca and Cd (µm), colored by geometry
    ax = axes[1]
    cmap = plt.cm.tab10
    for k, g in enumerate(geoms):
        rs = [r for r in recs if r["geom"] == g]
        t_true = np.array([r["theta_true"] for r in rs]) * 1e3  # um
        t_est = np.array([r["theta_est"] for r in rs]) * 1e3
        ax.scatter(t_true[:, 0], t_est[:, 0], marker="o", s=40,
                   color=cmap(k), alpha=0.7, label=g)
        ax.scatter(t_true[:, 2], t_est[:, 2], marker="s", s=40,
                   color=cmap(k), alpha=0.7)
    lim = [0, max(np.max(np.array([r["theta_true"] for r in recs])[ :, [0, 2]]) * 1e3,
                  np.max(np.array([r["theta_est"] for r in recs])[:, [0, 2]]) * 1e3) * 1.1]
    ax.plot(lim, lim, "k--", lw=1)
    ax.set_xlabel("True relief amount (µm)")
    ax.set_ylabel("Recovered relief amount (µm)")
    ax.set_title("(b) Amplitude recovery (o=Ca, s=Cd)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # (c) position parameters sa, sd: recovered vs true
    ax = axes[2]
    for k, g in enumerate(geoms):
        rs = [r for r in recs if r["geom"] == g]
        t_true = np.array([r["theta_true"] for r in rs])
        t_est = np.array([r["theta_est"] for r in rs])
        ax.scatter(t_true[:, 1], t_est[:, 1], marker="o", s=40,
                   color=cmap(k), alpha=0.7, label=g)
        ax.scatter(t_true[:, 3], t_est[:, 3], marker="s", s=40,
                   color=cmap(k), alpha=0.7)
    ax.plot([0, 1], [0, 1], "k--", lw=1)
    ax.set_xlabel("True relief start position")
    ax.set_ylabel("Recovered relief start position")
    ax.set_title("(c) Position recovery (o=sa, s=sd)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = RESULTS / "E08_generalization.png"
    plt.savefig(out, dpi=150)
    print(f"Figure saved to {out}")

    print("\n--- E8 summary (median worst-relative error) ---")
    for g in geoms:
        for case in ["single", "multi"]:
            rs = [r for r in recs if r["geom"] == g and r["case"] == case]
            if not rs:
                continue
            med = np.median([worst_norm(r) for r in rs])
            n_bounds = sum(any(r["hit_bound"]) for r in rs)
            print(f"  {g:9s} {case:6s}: worst_norm={med:.3e}  "
                  f"bounds-hit runs: {n_bounds}/{len(rs)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", nargs="?", default="plot",
                    choices=["run", "plot"])
    ap.add_argument("i0", nargs="?", type=int, default=0)
    ap.add_argument("i1", nargs="?", type=int, default=10 ** 9)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    if args.command == "run":
        run_chunk(args.i0, args.i1, workers=args.workers)
    else:
        plot()
