# Analytical forward and inverse experiments

The `src` directory contains involute geometry, relief profiles, analytical compliance variants, contact solvers, batched sensitivities, inverse reconstruction and Fisher diagnostics. Units are millimetres, newtons, N mm internally and N m for experiment torque inputs as documented by each API. Experiment scripts add `src` to the module path.

The final manuscript campaigns are in `results/q1_*`. Earlier experiment scripts are retained for provenance but historical E01–E08 result archives are not part of this deposit. Use the Q1 scripts and records for the current scientific claims. `experiments/Q1_review5_monte.py` adds the complementary-phase Monte Carlo control and reads the retained original Q1 single-load records. For scope, dependencies, FE execution and integrity checks, see the repository root README.
