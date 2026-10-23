"""
E7: Controlled compliance perturbations with dependent model variants.

M3 = constant mesh stiffness (lumped-parameter style), calibrated against
M2's mean elastic deflection (see mechanics/alt_models.py). Both models
share involute geometry, the tip-relief parametrization, and the Hertzian
local contact law; they differ in the mesh-stiffness waveform. Cross-model bias here measures compensation for a prescribed compliance
change. The same solver and geometry are reused, so this is not independent
physical validation or an exhaustive bound on model-form error.

Cross-inversion protocol (noise-free first, then selected 0.1 µm synthetic TE noise):
  - data M3 -> inverse with M2   (and the symmetric data M2 -> inverse M3)
  - sanity: data M3 -> inverse M3 (self-consistency of the M3 chain)
  - data M2 -> inverse M2 is covered by E2/E4 and is not repeated.

Run in chunks (records are idempotent):
    python experiments/E07_model_discrepancy.py run  <i0> <i1>
    python experiments/E07_model_discrepancy.py plot
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
from mechanics.alt_models import (
    ConstantStiffnessContactModel,
    WaveScaledContactModel,
    calibrate_constant_stiffness,
    calibrate_wave_mean,
)
from mechanics.transmission_error import TransmissionError
from inverse.reconstruction import InverseReconstructor

THETA_TRUE = np.array([0.020, 0.75, 0.005, 0.25])  # [Ca, sa, Cd, sd]

BOUNDS = np.array([
    [0.0, 0.100],   # Ca [mm]
    [0.3, 0.95],    # sa [-]
    [0.0, 0.050],   # Cd [mm]
    [0.05, 0.50],   # sd [-]
])
SCALE = np.array([0.05, 1.0, 0.01, 1.0])

N_OBS = 60
PARAM_LABELS = ["Ca", "sa", "Cd", "sd"]
LOAD_CASES = {
    "single": np.array([100.0]),
    "multi": np.array([50.0, 300.0]),
}
# (generator_model, inverse_model, sigma_um) cases; seeds per case
CASES = [
    ("M3", "M2", 0.0),
    ("M2", "M3", 0.0),
    ("M3", "M3", 0.0),   # self-consistency sanity
    ("M3", "M2", 0.1),   # discrepancy + realistic noise
    ("M2", "M3", 0.1),
    ("M3b", "M2", 0.0),  # subtle discrepancy: wave scaled to 50%
    ("M2", "M3b", 0.0),
    ("M3b", "M2", 0.1),
    ("M2", "M3b", 0.1),
    ("M3b", "M3b", 0.0),  # M3b self-consistency
]
N_SEEDS = 2
WAVE_BETA = 0.5  # M3b stiffness-wave amplitude factor

THETA0 = np.clip(THETA_TRUE * np.array([1.3, 0.9, 2.0, 1.2]),
                 BOUNDS[:, 0], BOUNDS[:, 1])

RESULTS = Path(__file__).parent.parent / "results"
RECORDS = RESULTS / "E07_records.jsonl"


def build_models():
    """Return dict with M2 and calibrated M3 transmission-error models."""
    g1 = InvoluteGear(z=24, m=3.0, alpha_deg=20.0, b=20.0)
    g2 = InvoluteGear(z=48, m=3.0, alpha_deg=20.0, b=20.0)
    pair = GearPair(g1, g2)
    micro1 = TipRelief(p=2.0)

    m2 = GearContactModel(pair, micro1=micro1, micro2=None,
                          linearize_hertz=False)
    c_const = calibrate_constant_stiffness(m2, torque_Nm=100.0,
                                           n_positions=N_OBS)
    m3 = ConstantStiffnessContactModel(pair, micro1=micro1, micro2=None,
                                       c_const=c_const,
                                       linearize_hertz=False)
    c_mean = calibrate_wave_mean(m2, n_positions=N_OBS)
    m3b = WaveScaledContactModel(pair, c_mean=c_mean, beta=WAVE_BETA,
                                 micro1=micro1, micro2=None,
                                 linearize_hertz=False)
    models = {
        "M2": TransmissionError(m2),
        "M3": TransmissionError(m3),
        "M3b": TransmissionError(m3b),
    }
    return models, c_const


def generate_observations(te_gen, torques, sigma_um, seed):
    rng = np.random.default_rng(seed)
    y_obs = []
    for T in torques:
        res = te_gen.compute_cycle(torque_Nm=T, n_positions=N_OBS,
                                   theta1=THETA_TRUE)
        y = res["TE_lin_fluct"]
        if sigma_um > 0.0:
            y = y + rng.normal(0.0, sigma_um * 1e-3, size=y.size)  # um -> mm
        y_obs.append(y)
    return np.concatenate(y_obs)


def task_list():
    tasks = []
    for (gen, inv, sig) in CASES:
        for case_name, torques in LOAD_CASES.items():
            for seed in range(N_SEEDS):
                tasks.append(dict(gen=gen, inv=inv, sigma_um=sig,
                                  case=case_name, seed=seed))
    return tasks


def run_one(task):
    models, c_const = build_models()
    torques = LOAD_CASES[task["case"]]
    te_gen = models[task["gen"]]
    te_inv = models[task["inv"]]

    y_obs = generate_observations(te_gen, torques, task["sigma_um"],
                                  task["seed"])
    recon = InverseReconstructor(te_inv, torques, BOUNDS, theta_scale=SCALE,
                                 n_positions_forward=N_OBS)
    result = recon.reconstruct(y_obs, theta0=THETA0,jacobian_scheme=task.get('jacobian_scheme','2-point'))

    theta_est = result["theta"]
    abs_err = np.abs(theta_est - THETA_TRUE)
    rel_err = abs_err / (np.abs(THETA_TRUE) + 1e-12)
    hit = ((theta_est <= BOUNDS[:, 0] + 1e-9)
           | (theta_est >= BOUNDS[:, 1] - 1e-9))

    return dict(
        gen=task["gen"], inv=task["inv"], case=task["case"],
        torques=torques.tolist(), sigma_um=task["sigma_um"],
        seed=task["seed"], c_const=c_const,
        theta_est=theta_est.tolist(),
        fit_rmse_mm=result["rmse"],
        param_abs_err=abs_err.tolist(),
        param_rel_err=rel_err.tolist(),
        worst_rel_err=float(np.max(rel_err)),
        hit_bound=hit.tolist(),
        nfev=int(result["nfev"]), success=bool(result["success"]),
        jacobian_scheme=result['jacobian_scheme'],
    )


def run_chunk(i0, i1, workers=4):
    tasks = task_list()
    i1 = min(i1, len(tasks))
    existing = set()
    if RECORDS.exists():
        with open(RECORDS, "r", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                existing.add((r["gen"], r["inv"], r["case"], r["sigma_um"],
                              r["seed"]))
    chunk = [t for t in tasks[i0:i1]
             if (t["gen"], t["inv"], t["case"], t["sigma_um"],
                 t["seed"]) not in existing]
    print(f"Tasks {i0}:{i1}: {len(chunk)} to run "
          f"({len(existing)} already on record)")

    import concurrent.futures as cf

    def execute(t):
        rec = run_one(t)
        fout.write(json.dumps(rec) + "\n")
        fout.flush()
        print(f"  done {t['gen']}->{t['inv']} {t['case']:6s} "
              f"sig={t['sigma_um']:3.1f} seed={t['seed']}  "
              f"worst_rel={rec['worst_rel_err']:.3e} "
              f"rmse={rec['fit_rmse_mm']:.2e} "
              f"bounds={any(rec['hit_bound'])}", flush=True)

    with open(RECORDS, "a", encoding="utf-8") as fout:
        if workers <= 1:
            for t in chunk:
                execute(t)
        else:
            with cf.ProcessPoolExecutor(max_workers=workers) as pool:
                futs = {pool.submit(run_one, t): t for t in chunk}
                for fut in cf.as_completed(futs):
                    t = futs[fut]
                    rec = fut.result()
                    fout.write(json.dumps(rec) + "\n")
                    fout.flush()
                    print(f"  done {t['gen']}->{t['inv']} {t['case']:6s} "
                          f"sig={t['sigma_um']:3.1f} seed={t['seed']}  "
                          f"worst_rel={rec['worst_rel_err']:.3e} "
                          f"rmse={rec['fit_rmse_mm']:.2e} "
                          f"bounds={any(rec['hit_bound'])}", flush=True)
    print(f"Records file: {RECORDS}")


def load_records():
    with open(RECORDS, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def plot():
    recs = load_records()
    if not recs:
        raise SystemExit("No records found; run the experiment first.")

    models, c_const = build_models()

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))

    # (a) TE waveforms of both models at theta_true
    ax = axes[0]
    for name, ls in [("M2", "-"), ("M3b", "-."), ("M3", "--")]:
        res = models[name].compute_cycle(torque_Nm=100.0, n_positions=N_OBS,
                                         theta1=THETA_TRUE)
        ax.plot(np.rad2deg(res["phi"]), res["TE_lin_fluct"] * 1e3, ls,
                label=f"{name} (100 Nm)")
    ax.set_xlabel("Pinion rotation (deg)")
    ax.set_ylabel("TE fluctuation (µm)")
    ax.set_title(f"(a) Model-form difference\n(c_const = {c_const:.3e} mm/N)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # (b) parameter recovery for noise-free cross inversions
    ax = axes[1]
    cases_nf = [r for r in recs if r["sigma_um"] == 0.0]
    x = np.arange(len(PARAM_LABELS))
    width = 0.15
    keys = [("M3", "M2"), ("M2", "M3"), ("M3b", "M2"), ("M2", "M3b"),
            ("M3", "M3"), ("M3b", "M3b")]
    for k, key in enumerate(keys):
        sel = [r for r in cases_nf if r["gen"] == key[0] and r["inv"] == key[1]
               and r["case"] == "single"]
        if not sel:
            continue
        theta_mean = np.mean([r["theta_est"] for r in sel], axis=0)
        scale_v = np.array([1e3, 1.0, 1e3, 1.0])
        ax.bar(x + (k - 2.5) * width, theta_mean * scale_v, width,
               label=f"data {key[0]} → inv {key[1]}", alpha=0.8)
    ax.bar(x + 2.5 * width, THETA_TRUE * scale_v, width, fc="none", ec="k",
           ls="--", lw=1.2, label="true")
    ax.set_xticks(x)
    ax.set_xticklabels(PARAM_LABELS)
    ax.set_ylabel("Value (Ca,Cd in µm; sa,sd dimless)")
    ax.set_title("(b) Cross-model recovery (single load)")
    ax.legend(fontsize=7)
    ax.grid(True, axis="y", alpha=0.3)

    # (c) fit RMSE vs parameter error across all records
    ax = axes[2]
    markers = {("M3", "M2"): "o", ("M2", "M3"): "s", ("M3", "M3"): "^",
               ("M3b", "M2"): "D", ("M2", "M3b"): "v", ("M3b", "M3b"): "P"}
    for key, mk in markers.items():
        rs = [r for r in recs if (r["gen"], r["inv"]) == key]
        if not rs:
            continue
        fit = [max(r["fit_rmse_mm"] * 1e3, 1e-6) for r in rs]
        err = [max(r["worst_rel_err"], 1e-9) for r in rs]
        ax.scatter(fit, err, marker=mk, s=40, alpha=0.7,
                   label=f"data {key[0]} → inv {key[1]}")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Fit RMSE (µm)")
    ax.set_ylabel("Worst-parameter relative error")
    ax.set_title("(c) Discrepancy vs. recovery error")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8)

    plt.tight_layout()
    out = RESULTS / "E07_model_discrepancy.png"
    plt.savefig(out, dpi=150)
    print(f"Figure saved to {out}")

    # Console summary
    print("\n--- E7 summary (worst-param relative error, median over seeds) ---")
    for sig in sorted({r["sigma_um"] for r in recs}):
        for case in ["single", "multi"]:
            for key in [("M3", "M2"), ("M2", "M3"), ("M3", "M3"),
                    ("M3b", "M2"), ("M2", "M3b"), ("M3b", "M3b")]:
                rs = [r for r in recs
                      if r["sigma_um"] == sig and r["case"] == case
                      and (r["gen"], r["inv"]) == key]
                if not rs:
                    continue
                med = np.median([r["worst_rel_err"] for r in rs])
                rmse = np.median([r["fit_rmse_mm"] * 1e3 for r in rs])
                print(f"  sig={sig:3.1f} {case:6s} {key[0]}->{key[1]}: "
                      f"worst_rel={med:.3e}  fit_rmse={rmse:.3f} µm")


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
