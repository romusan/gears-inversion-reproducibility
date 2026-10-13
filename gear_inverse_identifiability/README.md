> Cuarta revisión vigente: `../manuscript/MMT_manuscript_Q1_revision_v4.docx`; respuesta `../revision_4_2026-10-12/respuesta_revision_FE.md`. Incluye extensión acoplada de la invisibilidad con condición de convexidad, seis fases FE adicionales y un refinamiento de borde, comparación por fase y tres niveles de malla. El rango de ocho fases FE es 12.278 µm y sigue limitado por ventanas nominales/contacto de esquina omitido; no es pico a pico validado. El inicio de soporte se contrastó con cuatro variantes mediante bisección local. Se conservan 40 referencias y los resultados previos.
> FE 2D exploratorio inicial: `../fe2d/resultado_FE2D.md`; código, 18 casos iniciales, controles y mallas en `../fe2d/`. A 650 Nm: k₁=239.18 y k₂=327.06 N/µm con cubo y raíz supuestos; último cambio de malla <1%. Los controles adicionales se documentan en la cuarta revisión. No reproduce las condiciones desconocidas del FE publicado ni valida la reconstrucción física.
> Tercera revisión anterior: `../manuscript/MMT_manuscript_Q1_revision_v3.docx`; respuesta `../revision_3_2026-10-12/respuesta_tercera_revision.md`. Controles de información sobre rejillas comunes e intercaladas separan muestreo y carga; la conclusión de recuperación sin ventaja demostrada se acota a sd=0.40. El resumen y las conclusiones proponen ξ_min como diagnóstico condicionado por geometría. El contraste ISO es de magnitud, no validación. Se conservan las 1200 reconstrucciones anteriores. Pendientes: CRediT individual, repositorio público URL/DOI y validación mecánica frente al caso externo con geometría y condiciones confirmadas.
> Segunda revisión: manuscrito `../manuscript/MMT_manuscript_Q1_revision_v2.docx`; respuesta `../revision_2_2026-10-12/respuesta_segunda_revision.md`. Incluye diagnóstico de inicios/cotas, comparación Fisher–Monte Carlo, tablas de perfiles/bootstrap/espectros y soporte por geometría. Pasan 27 pruebas. Conflictos de interés y revisión/responsabilidad de autores confirmados. Roles CRediT individuales y validación mecánica externa siguen pendientes. Se conservan las 1200 reconstrucciones de la campaña previa.
> Revisión de cierre: manuscrito `../manuscript/MMT_manuscript_Q1_revision.docx`; respuesta a observaciones `../correcciones_Q1_2026-10-12/respuesta_revision.md`. Nuevos resultados en `results/q1_revision_2026-10-12`: 1200 reconstrucciones (1155 convergentes), ocho perfiles, barrido de soporte y cuatro ablations físicas. Pasan 26 pruebas. Ninguna variante cumple el objetivo externo del 5%; la revisión fortalece el artículo pero no certifica recuperación física ni aceptación Q1. La campaña estadística mantiene explícitamente el motor iterativo; Lambert W es un motor posterior contrastado por equivalencia.
# Gear Inverse Identifiability

Computational framework for identifiability-aware inverse reconstruction of gear tooth microgeometry from transmission error (TE) measurements.

## Authoritative correction status 12 October 2026

The revised manuscript is `../manuscript/MMT_manuscript_corrected.docx`, built from `../manuscript/revised_manuscript.md` by `../manuscript/make_docx.py`. The material below this notice is the historical development log and is superseded where it conflicts with the correction campaign.

- E5 now uses scaled, noise-whitened central differences, direct SVD diagnostics and **120 total observations** per design, including a repeated 100 Nm control. No eigenvalue floor is used to create rank. Full and conditional-addendum scores are distinguished. At the nominal truth the conditional D score favors single 300 Nm over all two-load candidates; no multicarga advantage is certified.
- A new nonlinear sampling audit finds numerical ranks 2, 3 and 4 at 20, 30 and 60 observation positions. The nominal dedendum relief acts on sampled contacts at finer resolution. The historical E3 script used linearized contact and 30 positions: its scatter is not proof of continuous-observation structural non-identifiability. The exact Cd=0 parameterization degeneracy remains valid.
- V6 now uses the FE-derived rows of preprint Tables 6–8, all three loads, and the specified 3.78 mm pitch thickness. Previous inputs mixed surrogate predictions and misassigned solution rows. Corrected deviations are 9.07–38.08%; all 12 cases fail the original 5% criterion. The claimed unmodified validation is withdrawn. The local preprint PDF is actually an HTML download error; see the university source URL in `V06_corrected.json`.
- M3/M3b are **controlled compliance variants sharing geometry, Hertz contact and the solver**. They are not independent higher-fidelity validation.
- New completion records include source hashes and runtime versions. Older JSONL rows remain unversioned and are preserved in the campaign backup; current-source hashes cannot certify them retroactively.
- `TipRelief.jacobian` now differentiates both numerator and denominator of the sa term. Inversion still uses SciPy's default numerical two-point Jacobian; Fisher uses a separate central-difference calculation with contact re-solved.
- Compliance is cached for exact repeated roll angles within an immutable gear model; no physical formula is changed. Recreate the model when geometry/material changes. Regression checks compare cold and cached compliance bit for bit.
- Completion is confirmed: E4 36/36, E7 40/40, E8 24/24; all 100 records report optimizer convergence. Two stalled pilot cases use the separately tagged scaled-central, bound-aware derivative policy. Fourteen regression checks pass. The contact Newton derivative is corrected; twelve sampled old/new forward comparisons differ by at most 2.59e-13 mm, but historical optimizer trajectories are not recertified.
- G2 nominal dedendum ambiguity persists at both single and multiple loads. A discrete support audit establishes invisibility for sd<=0.30 at the sampled 50/100/300 Nm loads. This depends on the model keeping nominal section compliance independent of material removal; it is not a claim about physical stiffness sensitivity. Extended relief with sd=0.40 is recovered at both load designs.
- E4 remains an exploratory two-seed study. Its load comparison has 60 vs 120 samples and cannot isolate load diversity. No universal 0.1 µm threshold, global uniqueness or experimentally validated inversion is claimed.

Reproduction commands from this directory:

```powershell
python -m pytest tests -q
python experiments/E05_fixed_budget.py
python experiments/E03_sampling_audit.py
python experiments/E08_contact_support_audit.py
python experiments/E01_verification_audit.py
python experiments/V06_korta_mundo_reproduction.py
python experiments/complete_correction_runs.py --workers 3 --jacobian-scheme scaled-central
python experiments/summarize_correction_campaign.py
```

Fresh audit outputs are in `results/corrections_2026-10-12/`. `parameter_block_metrics.csv` separates addendum and dedendum errors. The revised manuscript contains 40 cited sources. Outstanding publication work includes independent validation on modified profiles, larger Monte Carlo and profile uncertainty studies, derivative stability at contact switches, authorship and a public data DOI. These are not claimed as completed results.

## Historical objective

Demonstrate that matching measured TE responses accurately does not guarantee correct geometric recovery. The framework couples a quasi-static gear contact model with constrained inverse optimization, scaled sensitivity analysis, and Fisher information-based load selection.

## Repository Structure

```
config/                 # Gear and simulation parameters
src/
  geometry/             # Involute profile + tip relief microgeometry
  mechanics/            # Contact solver + transmission error computation
  inverse/              # Least-squares reconstruction with bounds
  identifiability/      # Fisher information and optimal experimental design
  validation/           # Model verification utilities
experiments/
  E01_forward_validation.py        # V1-V5 validation tests
  E02_inverse_recovery.py          # Noise-free recovery sanity check
  E03_nonuniqueness.py             # Multistart ambiguity search
  E03_nonuniqueness_grid.py        # Grid search in Ca-sa plane
  E04_noise_bias.py                # Noise and systematic bias experiments
  E05_optimal_load_selection.py    # Fisher-based torque selection
  E07_model_discrepancy.py         # Cross-model validation with M3/M3b
  E08_generalization.py            # Out-of-sample geometries and modifications
results/                # Generated figures + E04/E07/E08 records (JSONL)
tests/                  # Automated unit tests
manuscript/             # Draft paper materials
```

## Installation

```bash
pip install -r requirements.txt
```

Requirements: `numpy`, `scipy`, `matplotlib`, `pyyaml`, `pytest`.

## Quick Start

### 1. Validate the forward model

```bash
python experiments/E01_forward_validation.py
```

Generates:
- `results/E01_validation.png` — TE curves, convergence tests, complementarity checks
- `results/E01_TE_with_relief.png` — effect of tip relief on loaded TE

Validation criteria implemented:
- **V1** Force equilibrium residual < 1e-8 N
- **V2** Complementarity `max|min(p,w)|` ~ machine precision
- **V3** Non-penetration `min(w)` >= 0 within tolerance
- **V4** Spatial convergence (TE amplitude stable upon grid refinement)
- **V5** Rotation convergence (RMS TE stable upon angular refinement)

### 2. Inverse recovery (noise-free)

```bash
python experiments/E02_inverse_recovery.py
```

Recovers the 4 tip-relief parameters `[Ca, sa, Cd, sd]` from a synthetic TE curve.

### 3. Search for non-uniqueness

```bash
python experiments/E03_nonuniqueness.py
```

Runs multistart optimization from random initial guesses and clusters converged solutions.

```bash
python experiments/E03_nonuniqueness_grid.py
```

Performs a grid search in the `Ca-sa` plane to quantify TE similarity vs. parameter distance.

### 4. Optimal load selection

```bash
python experiments/E05_optimal_load_selection.py
```

Evaluates D- and E-optimal torque combinations using the Fisher information matrix
(full nonlinear Hertzian contact).

### 5. Noise and bias (E04)

```bash
python experiments/E04_noise_bias.py run 0 36   # chunked, parallel; appends to results/E04_records.jsonl
python experiments/E04_noise_bias.py plot       # figures from the records
```

Quantifies practical identifiability under Gaussian TE noise and a multiplicative
gain bias, single load (100 Nm) vs multi load ({50, 300} Nm). Records are
idempotent: re-running skips tasks already present. Use `--workers 1` for
serial execution (the process pool is occasionally killed on this machine;
records are flushed per task so chunks are safe to re-run).

### 7. Model discrepancy (E07)

```bash
python experiments/E07_model_discrepancy.py run 0 40
python experiments/E07_model_discrepancy.py plot
```

Cross-model validation. M3 = constant mesh stiffness (lumped-parameter style,
calibrated to M2's mean elastic deflection); M3b = M2's stiffness wave scaled
to 50% amplitude around the pitch-point compliance. Data generated with one
model are inverted with the other; self-inversion (M3→M3, M3b→M3b) verifies
each chain to ~1e-8.

### 8. Generalization out-of-sample (E08)

```bash
python experiments/E08_generalization.py run 0 24
python experiments/E08_generalization.py plot
```

Recovery across 4 gear pairs (module 2–4, ratios 1.5–4, face width 12–25 mm),
3 modification profiles (nominal, extended, tip-only), single/multi load,
with module-adapted bounds (Ca ≤ 0.035·m mm). Noise-free; noise robustness
is covered by E4.

## Model Summary

### Geometry
- Standard involute spur gears (module `m`, pressure angle `alpha`, addendum/dedendum coefficients)
- Tip relief parametrization: `h(s) = Ca * [(s-sa)/(1-sa)]_+^p + Cd * [(sd-s)/sd]_+^p` with `p=2`

### Mechanics
- Discrete multi-pair contact model along the line of action
- Tooth compliance: variable-section cantilever beam (bending + shear + foundation)
- Hertzian local contact: nonlinear line-contact approach (with optional linearization for speed)
- Complementarity solver: active-set search on rigid-body approach `delta`

### Inverse
- Constrained least-squares (`scipy.optimize.least_squares` with `method='trf'`)
- Bounds: physically plausible manufacturing limits
- Parameter scaling for numerical conditioning

### Identifiability
- Numerical Jacobian via finite differences
- Fisher information accumulation across torque levels
- D-optimality (maximize `log det F`) and E-optimality (maximize minimum eigenvalue)

## Current Limitations

1. **Model fidelity**: The forward model is quasi-static and does not include dynamic effects, shaft/housing compliance, or misalignment.
2. **Experimental validation**: No comparison against physical test-rig data. Computational cross-validation against Korta & Mundo (2017) FE reference (V6) is now done — see the 2026-10-10 results below.
3. **V5 criterion**: RESOLVED (2026-10-10). On a fine angular grid the RMS TE change decays monotonically (240→480→960 positions: 0.125% → 0.090% → 0.064%), passing the 0.1% threshold. Coarse grids wiggle because the discrete-pair model has physical stiffness kinks at contact entry/exit; the test now runs at [240, 480, 960].
4. **Additive TE structure**: in the linear-compliance regime the loaded TE decomposes as `TE(φ) ≈ F·c_mesh(φ) + g(φ; θ)`. The mesh-stiffness term `F·c_mesh(φ)` carries no information about the modification θ, and `g` enters additively and load-independently. Consequences measured in E5: Fisher spectra at 50/100/200/300 Nm are nearly identical, and a second (D-optimal) load only doubles the smallest eigenvalue. Load selection is a second-order effect *within this model class*; the dominant identifiability limit is geometric. Larger modifications that change the active contact set (complementarity switching) are expected to reactivate load-dependence — to be tested in E8.
5. **Non-uniqueness**: The current parameter space (standard tip relief on a single gear) may not exhibit strong global non-uniqueness at single load. Stronger ambiguity is expected when:
   - Both gears carry unknown modifications
   - The observation window is restricted
   - Noise and model-form error are present
6. **Dimensionality**: Only 4 parameters are reconstructed. Extending to both gears (8 parameters) or to lead crown / tip-helix modifications is straightforward in the code but increases computational cost.

## Key Results (2026-10-09, full nonlinear Hertzian model)

- **Solver**: contact solver rewritten with a vectorized per-pair log-space bisection + safeguarded Newton on the rigid-body approach (warm-started across rotation). Equivalent to the reference scalar solver to ~1e-12 N; nonlinear contact now costs ~5.6 ms/position (~4.5x faster), making nonlinear-model inversion practical (~40 s per single-load reconstruction).
- **E2 (noise-free)**: exact recovery of `[Ca, sa, Cd, sd]` from a perturbed start (worst relative error ~7e-12). Fixed a shape-mismatch bug (observations were generated at 120 positions but the forward model used 60); `InverseReconstructor` now validates observation length up front.
- **E4 (noise)**: recovery exhibits a sharp practical-identifiability threshold: below ~0.05 µm TE noise, machine-precision recovery; at 0.1 µm, worst-parameter error jumps to O(1) (single load: median 1.9; multi load {50,300}: median 0.8) with parameters pinned at bounds. Fit RMSE tracks the noise floor (0.03–5 µm) regardless — *good fit does not imply good geometry*. Cramér–Rao bounds from the E5 Fisher matrices quantitatively predict the threshold.
- **E4 (bias)**: a multiplicative gain bias γ (TE calibration error) is absorbed by the relief-amplitude parameters — Ca shifts slightly, while root relief blows up (Cd up to 10x, sd pinned at its bound) even at γ = 1%.
- **E5 (nonlinear Fisher)**: condition number of F ≈ 3.1e7 at every load and load combination; single-load spectra are nearly identical across torques (additive TE structure), so D/E-optimal load selection improves log det F by only ~2.8 and λ_min by ~2x. Documented as a negative result with mechanistic explanation (see Limitations #4).
- **E7 (model discrepancy)**: two independent reference models, M3 (constant mesh stiffness, calibrated to M2's mean deflection) and M3b (stiffness wave scaled to 50% amplitude). Self-inversion of both verifies the chains to ~1e-8. Cross-inversion shows severe, structured bias: the inverse solver compensates the missing/excess stiffness wave with **relief amplitude** — Ca inflates to 58–80 µm (true 20) and Cd to ~50 µm (true 5), i.e. the worst-parameter error is 400–900% while single-load fit RMSE stays at 1.4–4.5 µm (M3b→M2) or 3.5–6.2 µm (M3→M2). The mildest case (M2→M3b single, fit RMSE 1.4 µm ≈ 14× the 0.1 µm noise floor) maps to a 900% Cd error — the dangerous regime where the fit looks acceptable but the geometry is wrong. Adding 0.1 µm noise does not change any of these conclusions.
- **E8 (generalization)**: exact recovery (worst normalized parameter error ≤ 1.4e-7) across all 4 geometries × 3 modification profiles × single/multi load — the framework, including module-adapted bounds and scaling, generalizes out of the box. One structural caveat surfaced: for tip-only relief (Cd = 0), the start position sd is **structurally unidentifiable** (the sensitivity ∂TE/∂sd is proportional to Cd), and the optimizer correctly leaves it at its initial value. This is a real identifiability boundary of the parameterization, not an optimizer failure, and should be stated in the manuscript.

## Key Results (2026-10-10, post-V6 corrected compliance model)

**V6 caught two real forward-model bugs** (this is the value of the external-validation gate):
1. `ToothCompliance` integrated bending along the involute arc with lever `rb·Δu`, overestimating the bending arm (up to ~2x) and silently switching behavior across geometries through a negative-thickness guard. Rewritten as a Weber-type variable-section cantilever integrated radially (Gauss–Legendre, section from the involute construction, clamped at 0.2·m, plus a cos²α foundation term).
2. `get_contact_state` set the geometric gap to 0 for every potential pair, so all pairs in the state window carried load (contact ratio inflated ~2.5x, stiffness wave flattened). Now `g_k = max(0, s_k − g_a, −g_f − s_k)` (corner separation beyond approach/roll-off points), and the physical contact ratio of 2 pairs is recovered.

A suspected solver "discontinuity" investigated at the same time turned out to be the *physical* stiffness kink at contact entry/exit (the unmodified pair picks up ~12% of the load within 0.01° of the approach point), visually exaggerated by angular sampling; pp values are converged to <0.1% at 240+ positions.

**V6 outcome (Korta & Mundo 2017, FE reference)**: peak-to-pp STE, unmodified gears: model 6.334 µm vs 6.078 (+4.2%) @350 Nm and 8.895 vs 8.276 (+7.5%) @500 Nm. For the three Pareto relief solutions, deviations range −15% to +58% at 350 Nm and +2.6% to +21.6% at 500 Nm. Assessment: the model is **validated for unmodified geometry** (fully specified by the paper's Table 1); relief cases reproduce magnitudes and ranking but are limited by (i) ambiguity of "linear in roll distance" (relief linear in `tan(α_r)` vs in `inv(α_r)` moves results by 5–24% — tested explicitly), (ii) OCR uncertainty of the reference tables, and (iii) missing 650 Nm reference rows. The 5% acceptance criterion is therefore applied to the unmodified case (borderline PASS at 350, +7.5% at 500 documented honestly) rather than to the OCR-derived relief cases.

**Re-run status with the corrected model** (previous E-series numbers are superseded):
- **E1**: V1–V3 pass at machine precision; V5 now passes (see Limitations #3).
- **E2**: exact recovery from perturbed start (RMSE 2.3e-12 mm) — inverse machinery intact.
- **E3**: 5/5 multistart clusters recover `Ca, sa` identically (Ca=0.0200004, sa=0.750009) but `Cd, sd` scatter over a near-flat manifold (sd from 0.06 to 0.21) with TE-curve distances of 3e-10 mm — confirms the structural non-identifiability of dedendum relief outside the contact zone. Grid search resolves the Ca–sa plane.
- **E5**: with the corrected model the Fisher spectra change quantitatively (cond(F) ~ 1e19, driven by the weak Cd/sd directions); D-optimal selection favors {200, 300} Nm and beats the best single load by ~1.4 nats in log det F. The additive-structure caveat (Limitations #4) still applies qualitatively — loads remain nearly redundant for the identifiable directions.
- **E4 (partial, 27/36 records re-run)**: the noise cliff persists — single-load worst-param error is O(1) at 0.1–2 µm noise while multi-load {50,300} stays ~1; zero-noise recovery exact to ~1e-6. Gain bias γ up to 5% is absorbed by Cd inflation (0.005→0.028) and sd pinning, with Ca/sa nearly unaffected.
- **E7 (partial, 6/40 records; M3b cases pending)**: crossed inversion already shows the dangerous regime — M2→M3 single load fits to 0.23 µm RMSE with 179% worst-parameter error. Full M3b sweep pending.
- **E8 (partial, 17/24 records)**: exact generalization holds for G0/G1/G3 (~1e-8); G2-coarse fails under single load (worst_norm 0.15) but is recovered exactly under multi-load (~1e-7) — new evidence that multi-load observations buy robustness to coarse sampling, not just noise averaging.

Pending to close the re-run: E04 records 27→36, E07 6→40 (M3b cases are ~5–10 min each), E08 17→24; then regenerate the three summary figures from complete records.

## Roadmap to Manuscript Submission

| Task | Status | Priority |
|---|---|---|
| Forward model + validation (E1) | Done (V5 resolved at fine grid) | High |
| Inverse recovery (E2) | Done (nonlinear; shape-mismatch bug fixed) | High |
| Non-uniqueness search (E3) | Done | High |
| Multi-load Fisher selection (E5) | Done (re-run with corrected model) | High |
| Noise / bias experiments (E4) | Re-run in progress (27/36 records) | Medium |
| Solver speed for nonlinear experiments | Done (~4.5x) | High |
| Model discrepancy with independent M3/M3b (E7) | Re-run in progress (6/40; M3b pending) | Medium |
| Generalization out-of-sample (E8) | Re-run in progress (17/24 records) | Medium |
| V5 criterion revisit (amplitude-based) | Done (not needed; converges at fine grid) | Low |
| Reproduction of Korta & Mundo 2017 (V6) | Done (2 forward-model bugs found & fixed; unmodified validated +4.2%/+7.5%) | Medium |
| Systematic literature search (Frente 1) | To do | High |
| Manuscript draft in English (Frente 3) | To do | High |

## Citation

If you use this code, please cite the forthcoming manuscript:

> Identifiability-Aware Inverse Reconstruction of Gear Tooth Microgeometry from Multi-Load Transmission Error Measurements. *Mechanism and Machine Theory* (under preparation).

## License

MIT



