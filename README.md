# Contact support and practical identifiability of spur gear microgeometry

Code and saved numerical records supporting the Results in Engineering manuscript, editorial version 27 (2 November 2026).

This branch is `paper/rineng-v27`. The main branch and historical manuscript branches are unchanged. This is a code and numerical-record subset of `RINENG_reproducibility_v27.zip`, not a journal submission receipt or a DOI-bearing repository deposit. Editorial versions 21–27 did not introduce new experiments: the latest scientific records retain their original v19/v20 filenames.

## Contents and provenance

- `reproducibility/reproducibility_v20/`: latest numerical package, analytical and FE code, inverse routines, input decks, saved predictions, fit records and audit scripts.
- Nested companion archives have been expanded alongside their original archive locations. Their original paths and SHA-256 hashes are in `provenance/ARCHIVE_MAPPING.json`.
- `provenance/SOURCE_FILES.json`: SHA-256 hashes and original archive members for every included source/evidence file.
- `provenance/VALIDATION.json`: checks performed when preparing this branch.

The branch includes 305 Python files and 807 NPZ files across current and preserved historical packages. It excludes manuscripts, rendered figures, native solver visualisation output (`.frd`), logs, binary environments and executables. The exact exclusions are recorded in the archive mapping. Some historical document/solver audit scripts require those omitted files and are not runnable from this subset alone. Original archive manifests and readmes are preserved as provenance; they describe the full original archives, not this subset. No upstream source or numerical record has been edited.

## Verification and execution

Use Python 3.12. Before making changes, verify the distributed files:

```sh
python tools/verify_snapshot.py
```

For numerical execution, work in a scratch copy of `reproducibility/reproducibility_v20` to preserve saved evidence. Install `fe2d/requirements.txt` and `shapely==2.1.2`. The archived `README.txt` documents commands, contact-cache regeneration, continuation choices and the pinned external CalculiX download receipt. CalculiX executables are not included. On Windows, enable Git long paths before checkout (`git config --global core.longpaths true`) and use a short clone destination because preserved companion paths are long.

Representative commands from the numerical package root:

```sh
python manuscript/analyze_v20.py
python manuscript/starts_v20.py interior
python manuscript/starts_v20.py with_transitions
python manuscript/design_diagnostic_v20.py
```

The analysis command uses saved records. Forward/inverse commands may be expensive, regenerate caches, or reuse archived outputs; read the original README and scripts before running. Do not run native solver jobs concurrently in the same directory. No new experiment or full rerun is claimed for this GitHub upload.

## Scientific scope

The study establishes conditional invariance under fixed contact geometry and compliance and investigates practical identifiability with synthetic and finite-element controls. A dedendum signal does not by itself demonstrate recoverable relief. Cross-operator negative findings, uncalibrated stiffness, the single virtual truth in the full-cycle design comparison, and the limited noise regimes remain limitations. This is not experimental validation using measured gears with certified relief.

## Authors

- Rómulo Sandoval Flórez — Universidad ECCI — ORCID https://orcid.org/0000-0003-4157-6842
- Claudia Patricia Parra Medina — Universidad Militar Nueva Granada — ORCID https://orcid.org/0000-0003-2115-4167
- Germán Leandro Vargas Fonseca — Universidad Militar Nueva Granada — ORCID https://orcid.org/0009-0001-3862-4201

Correspondence: romulo@ecci.edu.co. No new licence grant is introduced by this branch; retained third-party notices continue to apply. No repository DOI has been assigned.
