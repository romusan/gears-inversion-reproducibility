"""
E4: Noise and systematic bias in inverse recovery.

Quantifies how measurement noise and a multiplicative metrology bias
(gain error of the TE measurement chain) degrade the *practical
identifiability* of the tip-relief parameters, comparing:
  - single-load observation   (T = 100 Nm)
  - multi-load observation    (T = {50, 300} Nm; fixed historical pair,
                              not certified optimal at a fixed total budget)

Design notes
------------
* Observations and the forward model inside the reconstructor use the SAME
  number of angular positions (n_obs = 60) so stacked residual vectors match.
* TE observations are the fluctuating part of loaded TE (mean removed), as
  produced by TransmissionError.compute_cycle. A constant additive bias is
  therefore absorbed by mean removal and is NOT studied here; the bias
  studied is multiplicative, y = (1+gamma) * TE + noise, which mimics a
  calibration/gain error of the TE measurement chain and survives
  mean removal.
* All runs start from the same perturbed initial guess (the one E2 showed
  converges to machine precision in the noise-free case) to control one initialization rule. This does not rule out local-minimum
  or optimization effects; broader multistart checks are separate.
* Records are appended to results/E04_records.jsonl so the (expensive)
  reconstructions can be run in chunks from the command line:
      python experiments/E04_noise_bias.py run  <i0> <i1>
      python experiments/E04_noise_bias.py plot
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

# ----------------------------------------------------------------------------
# Experiment definition
# ----------------------------------------------------------------------------

THETA_TRUE = np.array([0.020, 0.75, 0.005, 0.25])  # [Ca mm, sa -, Cd mm, sd -]

BOUNDS = np.array([
    [0.0, 0.100],   # Ca [mm]
    [0.3, 0.95],    # sa [-]
    [0.0, 0.050],   # Cd [mm]
    [0.05, 0.50],   # sd [-]
])
SCALE = np.array([0.05, 1.0, 0.01, 1.0])

N_OBS = 60
NOISE_SIGMAS_UM = [0.0, 0.1, 0.5, 1.0, 2.0, 5.0]
BIAS_GAMMAS = [0.01, 0.03, 0.05]
N_SEEDS = 2                      # noise realizations per (sigma, loads)
BIAS_SIGMA_UM = 0.1              # small noise present during bias runs
LOAD_CASES = {
    "single": np.array([100.0]),
    "multi": np.array([50.0, 300.0]),
}

# Fixed perturbed initial guess (E2 converges from here, noise-free)
THETA0 = np.clip(THETA_TRUE * np.array([1.3, 0.9, 2.0, 1.2]),
                 BOUNDS[:, 0], BOUNDS[:, 1])

PARAM_LABELS = ["Ca", "sa", "Cd", "sd"]
RESULTS = Path(__file__).parent.parent / "results"
RECORDS = RESULTS / "E04_records.jsonl"


def build_model():
    g1 = InvoluteGear(z=24, m=3.0, alpha_deg=20.0, b=20.0)
    g2 = InvoluteGear(z=48, m=3.0, alpha_deg=20.0, b=20.0)
    pair = GearPair(g1, g2)
    micro1 = TipRelief(p=2.0)
    model = GearContactModel(pair, micro1=micro1, micro2=None,
                             linearize_hertz=False)  # full nonlinear
    return TransmissionError(model)


def generate_observations(te, torques, sigma_um, gamma, seed):
    """Synthetic multi-load TE observation with noise and gain bias."""
    rng = np.random.default_rng(seed)
    y_obs = []
    for T in torques:
        res = te.compute_cycle(torque_Nm=T, n_positions=N_OBS,
                               theta1=THETA_TRUE)
        y = res["TE_lin_fluct"]
        if gamma != 0.0:
            y = (1.0 + gamma) * y
        if sigma_um > 0.0:
            y = y + rng.normal(0.0, sigma_um * 1e-3, size=y.size)  # um -> mm
        y_obs.append(y)
    return np.concatenate(y_obs)


def task_list():
    """Enumerate all (mode, loads_case, level, seed) reconstruction tasks."""
    tasks = []
    for case_name, torques in LOAD_CASES.items():
        for sigma in NOISE_SIGMAS_UM:
            for seed in range(N_SEEDS):
                tasks.append(dict(mode="noise", case=case_name,
                                  sigma_um=sigma, gamma=0.0, seed=seed))
        for gamma in BIAS_GAMMAS:
            for seed in range(N_SEEDS):
                tasks.append(dict(mode="bias", case=case_name,
                                  sigma_um=BIAS_SIGMA_UM, gamma=gamma,
                                  seed=seed))
    return tasks


def run_one(task):
    te = build_model()
    torques = LOAD_CASES[task["case"]]
    y_obs = generate_observations(te, torques, task["sigma_um"],
                                  task["gamma"], task["seed"])

    recon = InverseReconstructor(te, torques, BOUNDS, theta_scale=SCALE,
                                 n_positions_forward=N_OBS)
    result = recon.reconstruct(y_obs, theta0=THETA0,jacobian_scheme=task.get('jacobian_scheme','2-point'))

    theta_est = result["theta"]
    abs_err = np.abs(theta_est - THETA_TRUE)
    rel_err = abs_err / (np.abs(THETA_TRUE) + 1e-12)
    hit = ((theta_est <= BOUNDS[:, 0] + 1e-9)
           | (theta_est >= BOUNDS[:, 1] - 1e-9))

    rec = dict(
        mode=task["mode"], case=task["case"],
        torques=torques.tolist(),
        sigma_um=task["sigma_um"], gamma=task["gamma"], seed=task["seed"],
        theta_est=theta_est.tolist(),
        fit_rmse_mm=result["rmse"],
        param_abs_err=abs_err.tolist(),
        param_rel_err=rel_err.tolist(),
        worst_rel_err=float(np.max(rel_err)),
        hit_bound=hit.tolist(),
        nfev=int(result["nfev"]), success=bool(result["success"]),
        jacobian_scheme=result['jacobian_scheme'],
    )
    return rec


def run_chunk(i0, i1, workers=4):
    tasks = task_list()
    i1 = min(i1, len(tasks))
    done = 0
    if RECORDS.exists():
        done = sum(1 for _ in open(RECORDS, "r", encoding="utf-8"))
    chunk = tasks[i0:i1]
    print(f"Running tasks {i0}:{i1} ({len(chunk)} tasks, "
          f"{done} already on record)")

    # Skip tasks already present (idempotent re-runs)
    existing = set()
    if RECORDS.exists():
        with open(RECORDS, "r", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                existing.add((r["mode"], r["case"], r["sigma_um"],
                              r["gamma"], r["seed"]))
    todo = [t for t in chunk
            if (t["mode"], t["case"], t["sigma_um"], t["gamma"],
                t["seed"]) not in existing]

    import concurrent.futures as cf
    with open(RECORDS, "a", encoding="utf-8") as fout:
        if workers <= 1:
            for t in todo:
                rec = run_one(t)
                fout.write(json.dumps(rec) + "\n")
                fout.flush()
                print(f"  done {t['mode']:5s} {t['case']:6s} "
                      f"sig={t['sigma_um']:4.1f} g={t['gamma']:4.2f} "
                      f"seed={t['seed']}  worst_rel={rec['worst_rel_err']:.3e} "
                      f"rmse={rec['fit_rmse_mm']:.2e} "
                      f"bounds={any(rec['hit_bound'])}", flush=True)
        else:
            with cf.ProcessPoolExecutor(max_workers=workers) as pool:
                futs = {pool.submit(run_one, t): t for t in todo}
                for fut in cf.as_completed(futs):
                    t = futs[fut]
                    rec = fut.result()
                    fout.write(json.dumps(rec) + "\n")
                    fout.flush()
                    print(f"  done {t['mode']:5s} {t['case']:6s} "
                          f"sig={t['sigma_um']:4.1f} g={t['gamma']:4.2f} "
                          f"seed={t['seed']}  worst_rel={rec['worst_rel_err']:.3e} "
                          f"rmse={rec['fit_rmse_mm']:.2e} "
                          f"bounds={any(rec['hit_bound'])}", flush=True)
    print(f"Records file: {RECORDS}")


# ----------------------------------------------------------------------------
# Plotting
# ----------------------------------------------------------------------------

def load_records():
    recs = []
    with open(RECORDS, "r", encoding="utf-8") as f:
        for line in f:
            recs.append(json.loads(line))
    return recs


def plot():
    recs = load_records()
    noise = [r for r in recs if r["mode"] == "noise"]
    bias = [r for r in recs if r["mode"] == "bias"]
    if not noise:
        raise SystemExit("No noise records found; run the experiment first.")

    # ---- Figure 1: noise robustness + fit-vs-recovery decoupling ----
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))

    ax = axes[0]
    colors = {"single": "tab:blue", "multi": "tab:red"}
    markers = {"single": "o", "multi": "s"}
    for case in ["single", "multi"]:
        sigmas = sorted({r["sigma_um"] for r in noise if r["case"] == case})
        xs, med, p90 = [], [], []
        for s in sigmas:
            errs = [r["worst_rel_err"] for r in noise
                    if r["case"] == case and r["sigma_um"] == s]
            ax.scatter([s] * len(errs), errs, color=colors[case],
                       marker=markers[case], alpha=0.55, s=35,
                       label=f"{case} load" if s == sigmas[0] else None)
            xs.append(s)
            med.append(np.median(errs))
            p90.append(np.percentile(errs, 90))
        ax.plot(xs, med, color=colors[case], lw=1.5)
        ax.plot(xs, p90, color=colors[case], lw=1, ls=":")
    ax.set_xscale("symlog", linthresh=0.1)
    ax.set_yscale("log")
    ax.set_xlabel("Noise level $\\sigma$ on TE (µm)")
    ax.set_ylabel("Worst-parameter relative error")
    ax.set_title("(a) Recovery error vs. noise")
    ax.legend()
    ax.grid(True, which="both", alpha=0.3)

    ax = axes[1]
    for case in ["single", "multi"]:
        rs = [r for r in noise if r["case"] == case and r["sigma_um"] > 0.0]
        fit = [r["fit_rmse_mm"] * 1e3 for r in rs]        # um
        err = [max(r["worst_rel_err"], 1e-9) for r in rs]
        sig = [r["sigma_um"] for r in rs]
        sc = ax.scatter(fit, err, c=sig, cmap="viridis", s=35, alpha=0.8,
                        marker=markers[case],
                        label=f"{case} load")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Fit RMSE (µm)")
    ax.set_ylabel("Worst-parameter relative error")
    ax.set_title("(b) Good fit $\\neq$ good geometry")
    ax.set_xlim(0.02, 30)
    ax.set_ylim(1e-2, 30)
    cb = plt.colorbar(sc, ax=ax)
    cb.set_label("noise $\\sigma$ (µm)")
    ax.legend()
    ax.grid(True, which="both", alpha=0.3)

    plt.tight_layout()
    out = RESULTS / "E04_noise_recovery.png"
    plt.savefig(out, dpi=150)
    print(f"Figure saved to {out}")

    # ---- Figure 2: systematic gain bias ----
    if bias:
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
        gammas = sorted({r["gamma"] for r in bias})
        x = np.arange(len(gammas))

        for k, (params, title) in enumerate([
            ([0, 1], "(a) Tip relief (Ca, sa)"),
            ([2, 3], "(b) Root relief (Cd, sd)"),
        ]):
            ax = axes[k]
            width = 0.35
            for j, case in enumerate(["single", "multi"]):
                for pi, pidx in enumerate(params):
                    est = []
                    for g in gammas:
                        vals = [r["theta_est"][pidx] for r in bias
                                if r["case"] == case and r["gamma"] == g]
                        est.append(np.mean(vals))
                    scale = 1e3 if pidx in (0, 2) else 1.0
                    offset = (j - 0.5) * width + (pi - 0.5) * width * 0.9
                    ax.bar(x + offset, np.array(est) * scale, width * 0.9,
                           color=colors[case], alpha=0.55 if pi else 0.9,
                           hatch="" if pi == 0 else "//",
                           edgecolor="k", linewidth=0.4,
                           label=f"{case} ({PARAM_LABELS[pidx]})"
                           if k == 0 else None)
                    ax.axhline(THETA_TRUE[pidx] * scale, color="k", ls="--",
                               lw=0.8)
            ax.set_xticks(x)
            ax.set_xticklabels([f"{100*g:.0f}%" for g in gammas])
            ax.set_xlabel("Gain bias $\\gamma$")
            ax.set_ylabel("Recovered value (Ca,Cd in µm; sa,sd dimless)")
            ax.set_title(title)
            if k == 0:
                ax.legend(fontsize=8)
            ax.grid(True, axis="y", alpha=0.3)

        plt.tight_layout()
        out = RESULTS / "E04_bias.png"
        plt.savefig(out, dpi=150)
        print(f"Figure saved to {out}")

    # ---- Console summary ----
    print("\n--- Noise summary (worst-param relative error, median) ---")
    for case in ["single", "multi"]:
        row = []
        for s in sorted({r["sigma_um"] for r in noise if r["case"] == case}):
            errs = [r["worst_rel_err"] for r in noise
                    if r["case"] == case and r["sigma_um"] == s]
            row.append(f"{s:>4.1f}µm:{np.median(errs):.2e}")
        print(f"  {case:6s}: " + "  ".join(row))
    if bias:
        print("\n--- Bias summary (mean recovered theta) ---")
        for case in ["single", "multi"]:
            for g in gammas:
                ts = np.mean([r["theta_est"] for r in bias
                              if r["case"] == case and r["gamma"] == g], axis=0)
                print(f"  {case:6s} γ={g:4.2f}: "
                      + " ".join(f"{l}={v:.4g}" for l, v in
                                 zip(PARAM_LABELS, ts)))


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
