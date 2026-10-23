# Spur gear relief identifiability reproducibility package

Scientific controls accompanying manuscript revision 5 by Romulo Sandoval FlÃ³rez, Claudia Patricia Parra Medina and German Leandro Vargas Fonseca.

## Contents and execution

`gear_inverse_identifiability/src` contains the forward and inverse models. Experiments, configurations and final Q1 campaign records are retained with their directory layout. Historical exploratory records outside the Q1 campaigns are excluded.

Install the numerical dependencies in an isolated Python environment using `gear_inverse_identifiability/requirements.txt` and `fe2d/requirements.txt`. The additional quadratic FE controls use NumPy 2.5.1, SciPy 1.18.0, Matplotlib 3.11.1, gmsh 4.15.2, scikit-fem 12.0.2 and meshio 5.3.5. Other library/runtime versions can produce small numerical differences. The elasticity model is two-dimensional plane strain.

Run from `gear_inverse_identifiability`: `python experiments/Q1_review5_monte.py` regenerates the complementary-phase control, using the retained original single-load records. Run `python fe2d/convergence_separated.py` from the repository root to regenerate the separated quadratic bulk/interface controls (ten FE cases; computationally expensive). `python revision_5_2026-10-12/analyze_review5.py` rebuilds the tabular summaries and diagnostics from the stored records. Existing experiment scripts document earlier campaigns.

## Scientific scope

The six paired bootstrap intervals in the added 600-fit campaign contain zero. This does not establish equivalence; twenty fits reported nonconvergence and remain included. The tested complementary assignment uses 50 Nm at even canonical positions and 300 Nm at odd positions.

The final quadratic FE sequence is identified by `fe2d/results/separated_convergence.json` and filenames ending in `weak_hat_local0.01_P2`. The quadratic eight-phase campaign is separately identified by quadratic_eight_phases.json. The original linear/nodal controls must not be pooled with the quadratic formulation. The bulk and pressure controls vary separately. Pressure constraints are weak, averaged constraints; interior numerical stability does not certify a continuous corner-contact cycle or validate the published peak-to-peak benchmark. FE body VTU visualization files are omitted; they can be regenerated from the scripts. No DOI has been assigned.

`SHA256SUMS.json` identifies all deposited files except itself. No licence grant is asserted by this deposit. The cited external publications are referenced, not redistributed.

## Revision 6 controls

The annotated tags `manuscript-v5` and `manuscript-v6` identify separate versions. Revision 6 repeats the eight original FE phases with P2 displacement and weak distributed pressure, reports seed improvement fractions and near ties, and adds 0.21-degree offset envelopes. Run `python fe2d/quadratic_eight_phases.py`, then from `gear_inverse_identifiability` run `python experiments/Q1_review6_angular.py`, then from the repository root run `python revision_6_2026-10-12/summarize_review6.py`.

The FE envelope is computed from an eight-node periodic interpolant. It is not a direct dense FE scan and cannot resolve the FE transition ramp. The analytical waveform uses successively refined angular nodes. The numerical envelope algorithm covers every interpolation-offset interval with a fixed one-cycle window and 30 or 31 samples. Interface stiffness is nonmonotonic; observed small changes are not a certified convergence order or exact-error bound. The fixed-normal FE body torque deviations and adaptive tangent checks are retained in the review-6 summary. No stiffness calibration to the reference is introduced.

No DOI has been assigned. The GitHub tag and commit SHA provide version identification; they are not represented as a Zenodo DOI.
