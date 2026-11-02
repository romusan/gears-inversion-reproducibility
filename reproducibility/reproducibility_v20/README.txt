VERSION 20 — response to the v19 diagnostic

Current editable documents are in revision_20_2026-11-01. The Spanish response
states what was done and what remains open. No journal submission, DOI or
physical reconstruction is claimed. The v19 companion is unchanged and contains
earlier releases and the original scientific code/data. Do not treat historical
readmes as the current scientific scope.

New evidence: four additional full starts and two restricted starts per design
at the 0.04/0.50 mm nominal-elasticity inverse reference. Together with preserved
attempts there are five full and three restricted starts per design (16 total),
12 additional attempts and 30 total cycle-inverse attempts. Selection uses the
smallest training objective, never known-truth profile error. Failed flags and
all returned points remain. Full predictions at the selected points are repeated
from cold contact states. Timings include task scheduling and are not benchmarks.

Local central finite differences at the known truth use the declared steps and
their halves. Nuisance projections separate addendum and estimated/fixed offset.
These matrices and linear discrepancy predictions are descriptive, not calibrated
physical covariance or parameter intervals. Generator component contrasts are
computed separately from actual-geometry/reassembled-stiffness observations.
There is no noisy moving-contact refitting campaign or new full-cycle third grid.

CalculiX pairs compare actual addendum-only and combined profiles. The matched
cycle-mesh tests use f=0.225 (an actual former omission) and f=0.50. A two-phase
contrast cancels a constant offset per profile; it is not full-cycle RMS. Mesh
transfer is checked by reconstructing eight condensed-compliance columns per
body from exported nodes/elements. Shared geometry/mesh does not imply identical
contact enforcement or nonlinear kinematics. Weak mortar nodal penetration and
polygon overlap are reported independently of active/inactive COPEN output.

A slow fine-grid run exceeded 600 seconds; its paired run was interrupted before
final equilibrium. All partial inputs/outputs and reasons remain. Both profiles
were retried with a full initial fraction, with an additional same-grid pair to
measure continuation sensitivity. These are final 300 Nm deterministic controls,
not physical validation or an asymptotic mesh study. A separate 0.01/0.25 mm
selected-phase pair does not constitute a third full-cycle generator grid.

REBUILD DOCUMENTS from saved evidence (Python 3.12, python-docx and lxml):
  python manuscript/build_v20.py
  python manuscript/audit_v20.py
The preserved v19 documents at the top level are required inputs. Fifteen native
OMML equations and 48 references are unchanged. All historical numerical cells
remain, except the explicitly updated fine selection in main Table 10. S29 adds
flag percentages without replacing old cells. S37-S39 contain the extensions.

NUMERICAL RECOMPUTATION (use a scratch copy preserving the archived evidence):
Install fe2d/requirements.txt plus shapely==2.1.2. The old source uses its default
body-cache directory under revision_19_2026-11-01/experiments/body_cache. These
large regenerable matrices and binary environments are excluded. Starting an
operator recreates its missing reference cache. To audit cycle meshes, first
regenerate the case caches using the v19 cycle commands described in its archive.
OPENBLAS_NUM_THREADS=1 was used. Do not change source files during a resumed run.

  python manuscript/starts_v20.py interior
  python manuscript/starts_v20.py with_transitions
  python manuscript/design_diagnostic_v20.py
  python manuscript/audit_starts_v20.py
  python manuscript/audit_shared_mesh_v20.py
  python manuscript/audit_ccx_v20.py
  python manuscript/analyze_v20.py

Saved starts and local-forward records are reused after source checks. A fresh
regeneration requires preserving/moving these output files aside. The CalculiX
executables are NOT distributed: retrieve the pinned binary using the download
receipt in objetivos_numericos_2026-11-01, preserving upstream licences. The v19
companion includes the preceding solver evidence. New builders are
crosscheck_relief_v20.py, crosscheck_relief_fast_v20.py and crosscheck_cycle_v20.py.
All final inputs are supplied, so each native job can also be run directly using
ccx_MT.exe -i INPUT_STEM in its own solver directory. OMP_NUM_THREADS=2 was used.
Do not run native jobs concurrently in the same directory because they share
scratch files. The original slow runner includes intentionally preserved timeout
attempts; the fast runner performs the accepted continuation checks. The extra
interior runner waits for the entry-pair campaign marker before reusing that directory.

Native Word exported the four final documents, and Poppler rasterized every page
for visual review. The generic LibreOffice route was unavailable on the authoring
host; its diagnostic log is retained. QA PDFs/page images are local reading copies
and excluded from the distribution. The public manuscript-v13 baseline predates
later evidence. No new licence grant or author approval of submission is asserted.
SHA256SUMS.json covers every distributed file except itself.
