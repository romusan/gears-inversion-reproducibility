VERSION 19: numerical evidence and editable submission documents

Current files are in revision_19_2026-11-01. Prior companion ZIPs and documents
are unchanged historical evidence; their open-transition statements describe
the earlier fixed-normal operator. V19 adds a separate bilateral moving-contact
data set and does not overwrite the historical 102-station observations.

Scope: 24/24 spur pair, assumed sharp-tip/root-blend geometry, small-strain
plane-strain elasticity, finite rigid rotation and iterated bilateral contact.
Three profiles, two resolutions, 120 canonical stations plus closure controls:
720 observations, 6 closure tests. Profile-specific geometry and elastic stiffness
generate observations. The inverse changes geometry but RETAINS NOMINAL ELASTICITY.
At-truth mismatch, finite optimization, failures, closure and grid changes remain
explicit. No physical measurements, manufactured geometry, calibrated parameter
confidence coverage or continuum-converged inversion are claimed.

BUILD FROM SAVED EVIDENCE (Python 3.12, python-docx, lxml):
  python manuscript/build_v19.py
  python manuscript/audit_v19.py
Use current v18 documents included at the top level as the build inputs.
There are 15 unchanged native OMML equations; the old numerical tables are retained.
Tables S33-S36 and Figure 13 document the new experiment. AI and CRediT statements
are preserved; the three authors' common roles were explicitly confirmed.

NUMERICAL REPRODUCTION:
Install fe2d/requirements.txt and shapely==2.1.2. Analytical-control code is included
under deposit_v6/gear_inverse_identifiability/src. OPENBLAS_NUM_THREADS=1 was used
for the accelerated continuation. Preserve original evidence before recomputation.
Cycle commands recreate missing case-body caches even when observations are
complete. To regenerate observations as well, preserve the original evidence
and run on a scratch copy with cycle JSONL files moved aside. Large
body-compliance caches are excluded and hash-listed separately.
  python fe2d/run_cycle_reduced_v19.py --step 0.04 --h 0.5
  python fe2d/run_cycle_reduced_v19.py --step 0.02 --h 0.35
  python manuscript/check_reference_v19.py
  python manuscript/inverse_moving_v19.py --step 0.08 --max-nfev 25
  python manuscript/inverse_moving_v19.py --step 0.04 --max-nfev 25
  python manuscript/analytic_inverse_v19.py
  python manuscript/audit_cycle_v19.py
  python manuscript/analyze_v19.py

Saved-state audit reprojects both contact directions, reconstructs loads and
checks torque, net force, FE residual, elastic energy and global contour overlap.
It is an audit of this implementation. Independent CalculiX controls are SELECTED
NOMINAL PHASES in companions/EVIDENCIA_SIN_FABRICACION.zip, not full-cycle or
inverse-profile validation. That companion retains raw inputs/outputs, failed
development attempts, exact source snapshots and public-data screening.

Exact accelerations retain the candidate model: midpoint broad-phase screening,
vectorized projections/load assembly, sparse force products and constraint
generation with a full-candidate KKT certificate. Equivalence checks and historical
source hashes are included. Tiny roundoff differences are expected on regeneration.
Cached body stiffness is not a contact penalty. Dual regularization and independent
penalty/mortar checks are documented separately; no compliance is added twice.

The v18 companion preserves all earlier data and software, including the 1100
stress selections, 3300 final attempts and 300 covariance pilots. Extract it only
to a separate historical directory; its instructions concern that release.
Solver binaries, library environments, downloaded literature PDFs, regenerable
body caches and visual-QA page images are excluded. Portable CalculiX retrieval
and SHA receipts are in the mechanical-evidence companion. New reference metadata
are included; literature PDFs remain in the author's reference library.

DOCUMENT QA:
Native Word exported all four editable documents; Poppler rasterized every page.
The generic LibreOffice route was unavailable on the authoring host. Audit and
visual-review receipts accompany the release; QA PDFs are local reading copies.

This prepared kit has NOT been submitted, publicly uploaded or assigned a DOI.
The public manuscript-v13 GitHub baseline does not include later controls.
Historical licences and attributions remain in their respective packages;
no new licence grant or author approval of journal submission is asserted here.
SHA256SUMS.json covers every distributed file except itself.
