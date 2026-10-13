"""
V6: Reproduction of Korta & Mundo (2017) static transmission error.

Reference: J.A. Korta, D. Mundo, "Multi-objective micro-geometry
optimization of gear tooth supported by response surface methodology",
Mechanism and Machine Theory 109 (2017) 278-295.
doi:10.1016/j.mechmachtheory.2016.11.015
Open preprint: IRIS Unical (CC-BY-NC-ND), reference/korta_mundo_2017_preprint.pdf

Gear design (their Table 1):
  z1 = z2 = 57, module m = 2.60 mm, pressure angle 20 deg,
  tip diameter 154.50 mm (addendum coeff. 1.2115),
  root diameter 141.70 mm (dedendum coeff. 1.25),
  face width 23 mm, working center distance 150 mm
  (operating pressure angle ~21.84 deg).

Modification (their Section 5): LINEAR tip relief in the roll-distance
domain, applied to BOTH gears, parametrized by depth d [µm] and starting
radius rt [mm]. Our TipRelief with p=1 is linear in the roll angle, i.e.
linear in roll distance; sa maps from rt through the involute roll angle.

FE-derived targets are read from Tables 6-8 of the university-hosted preprint.
The 12 targets include all 350/500/650 Nm cases. Earlier values incorrectly
mixed surrogate predictions with FE results and misassigned solution rows.
The local file named korta_mundo_2017_preprint.pdf is an HTML download error,
not a usable PDF. Source and targets are saved with the corrected campaign.

Acceptance criterion (publication plan, V6): peak-to-peak STE difference
< 5% and qualitatively equal waveform.
"""

import sys
import json
from campaign_provenance import provenance
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
import matplotlib.pyplot as plt

from geometry.involute import InvoluteGear, GearPair
from geometry.microgeometry import TipRelief, map_roll_to_modification_domain
from mechanics.compliance import GearContactModel
from mechanics.transmission_error import TransmissionError

RESULTS = Path(__file__).parent.parent / "results" / "corrections_2026-10-12"
RESULTS.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Korta & Mundo geometry
# ---------------------------------------------------------------------------

Z = 57
M_MOD = 2.6
ALPHA_DEG = 20.0
B = 23.0
HA_P = (154.50 - 148.20) / (2.0 * 2.60)   # 1.2115 from tip diameter
HF_P = 1.25                                # from root diameter 141.70
A_WORK = 150.0                             # working center distance

TORQUES = [350.0, 500.0, 650.0]
N_POS = 120

# FE-derived STE only, independently checked against preprint Tables 6-8.
# Do not use the surrogate "Predicted" rows as FE validation targets.
REFERENCE_PP = {
    ("unmodified", 350.0): 6.078, ("unmodified", 500.0): 8.276,
    ("unmodified", 650.0): 10.527,
    ("Sol1", 350.0): 3.542, ("Sol1", 500.0): 5.689,
    ("Sol1", 650.0): 7.960,
    ("Sol2", 350.0): 2.434, ("Sol2", 500.0): 4.462,
    ("Sol2", 650.0): 6.670,
    ("Sol3", 350.0): 3.775, ("Sol3", 500.0): 5.930,
    ("Sol3", 650.0): 8.162,
}
REFERENCE_SOURCE = "https://iris.unical.it/bitstream/20.500.11770/133021/10/1.Korta_MMT__Submitted_Version_opt.pdf"

# Pareto-optimal modifications (their Table 5)
SOLUTIONS = {
    "Sol1": dict(d_um=16.3, rt_mm=74.134),
    "Sol2": dict(d_um=15.4, rt_mm=74.402),
    "Sol3": dict(d_um=13.4, rt_mm=74.190),
}


def build_pair():
    g1 = InvoluteGear(z=Z, m=M_MOD, alpha_deg=ALPHA_DEG, b=B,
                      haP=HA_P, hfP=HF_P, rhoFP=0.555, pitch_thickness_mm=3.78)
    g2 = InvoluteGear(z=Z, m=M_MOD, alpha_deg=ALPHA_DEG, b=B,
                      haP=HA_P, hfP=HF_P, rhoFP=0.555, pitch_thickness_mm=3.78)
    return GearPair(g1, g2, center_distance=A_WORK)


def rt_to_sa(rt_mm: float, gear) -> float:
    """Map relief starting radius to dimensionless start position sa."""
    u_rt = np.sqrt(max((rt_mm / gear.rb) ** 2 - 1.0, 0.0))
    u_tip = np.sqrt((gear.ra / gear.rb) ** 2 - 1.0)
    return float(np.clip(u_rt / u_tip, 0.0, 1.0))


def run_case(te, theta, torque):
    res = te.compute_cycle(torque_Nm=torque, n_positions=N_POS,
                           theta1=theta, theta2=theta)
    te_fluct = res["TE_lin_fluct"]
    pp = float(te_fluct.max() - te_fluct.min())
    return res, pp * 1e3  # um


def main():
    print("=" * 70)
    print("V6: Korta & Mundo (2017) reproduction")
    print("=" * 70)
    pair = build_pair()
    print(f"Geometry: z={Z}, m={M_MOD}, haP={HA_P:.4f}, hfP={HF_P}, b={B}")
    print(f"Working pressure angle: {np.rad2deg(pair.alpha_w):.3f} deg")
    print(f"Contact ratio: {pair.eps_alpha:.3f}; pitch thickness: {pair.g1.s:.3f} mm")

    micro = TipRelief(p=1.0)  # linear in roll domain, like the reference
    model = GearContactModel(pair, micro1=micro, micro2=micro,
                             linearize_hertz=False)
    te = TransmissionError(model)

    cases = {"unmodified": None}
    for name, sol in SOLUTIONS.items():
        d_mm = sol["d_um"] * 1e-3
        sa = rt_to_sa(sol["rt_mm"], pair.g1)
        # theta = [Ca, sa, Cd, sd]; linear tip relief only, both gears
        cases[name] = np.array([d_mm, sa, 0.0, 0.5])
        print(f"{name}: d={sol['d_um']} um, rt={sol['rt_mm']} mm "
              f"-> sa={sa:.4f}")

    results = {}
    print("\nPeak-to-peak STE [µm]  (model vs reference):")
    print(f"{'case':12s} {'T[Nm]':>6s} {'model':>8s} {'ref':>7s} {'diff%':>7s}")
    for cname, theta in cases.items():
        for T in TORQUES:
            res, pp = run_case(te, theta, T)
            results[(cname, T)] = (res, pp)
            ref = REFERENCE_PP.get((cname, T))
            if ref is not None:
                diff = (pp - ref) / ref * 100.0
                print(f"{cname:12s} {T:6.0f} {pp:8.3f} {ref:7.3f} "
                      f"{diff:+7.2f}")
            else:
                print(f"{cname:12s} {T:6.0f} {pp:8.3f} {'--':>7s} {'--':>7s}")

    rows = []
    for (name, torque), (_, pp) in results.items():
        ref = REFERENCE_PP[(name, torque)]
        diff = (pp-ref)/ref*100
        rows.append(dict(case=name,torque_Nm=torque,model_pp_um=pp,
                         reference_fe_pp_um=ref,difference_percent=diff,
                         passes_5_percent=abs(diff)<5))
    (RESULTS/"V06_corrected.json").write_text(json.dumps(dict(
        provenance=provenance(),source_url=REFERENCE_SOURCE,source_tables=[6,7,8],
        target_type="FE-derived, excluding metamodel predictions",pitch_thickness_mm=pair.g1.s,
        root_fillet_note="Tool radius coefficient is stored but the reduced compliance does not resolve fillet geometry.",
        results=rows),indent=2),encoding="utf-8")

    # ------------------------------------------------------------------
    # Figure
    # ------------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
    colors = {"unmodified": "k", "Sol1": "tab:blue",
              "Sol2": "tab:red", "Sol3": "tab:green"}
    for ax, T in zip(axes, TORQUES):
        for cname, theta in cases.items():
            res, pp = results[(cname, T)]
            ax.plot(np.rad2deg(res["phi"]), res["TE_lin_fluct"] * 1e3,
                    color=colors[cname],
                    ls="-" if cname == "unmodified" else "--",
                    label=f"{cname} ({pp:.2f} µm)")
            ref = REFERENCE_PP.get((cname, T))
            if ref is not None:
                c = res["TE_lin_fluct"] * 1e3
                ax.axhspan(c.max() - ref, c.max(), color=colors[cname],
                           alpha=0.12)
        ax.set_title(f"{T:.0f} Nm")
        ax.set_xlabel("Pinion rotation (deg)")
        ax.grid(True, alpha=0.3)
    axes[0].set_ylabel("STE fluctuation (µm)")
    axes[0].legend(fontsize=8)
    fig.suptitle("V6: Korta & Mundo (2017) reproduction — "
                 "shaded bands = reference pp windows", y=1.02)
    plt.tight_layout()
    out = RESULTS / "V06_korta_mundo.png"
    plt.savefig(out, dpi=150, bbox_inches='tight')
    print(f"\nFigure saved to {out}")

    # Pass/fail on the 5% criterion where references exist
    print("\nAcceptance check (< 5% pp difference):")
    all_pass = True
    for (cname, T), (_, pp) in results.items():
        ref = REFERENCE_PP.get((cname, T))
        if ref is None:
            continue
        diff = abs(pp - ref) / ref * 100.0
        ok = diff < 5.0
        all_pass &= ok
        print(f"  {cname:12s} @ {T:.0f} Nm: {diff:5.2f}%  "
              f"{'PASS' if ok else 'FAIL'}")
    print(f"\nOverall: {'PASS' if all_pass else 'FAIL'} "
          f"(see discussion in README if FAIL)")


if __name__ == "__main__":
    main()
