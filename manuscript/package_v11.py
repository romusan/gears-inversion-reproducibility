"""Assemble a portable local package without publishing or altering v10."""
import json,hashlib,shutil,zipfile
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent;AUD=ROOT/'revision_11_2026-10-23';DEST=AUD/'reproducibility_v11'
def copy(path,relative=None):
    target=DEST/(relative or path.relative_to(ROOT));target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
def main():
    DEST.mkdir(exist_ok=True)
    for p in (ROOT/'deposit_v6').rglob('*'):
        if p.is_file() and not any(x in p.parts for x in ['.git','.pytest_cache','__pycache__','.venv']):copy(p)
    for p in BASE.glob('*.py'):copy(p)
    for name in ['q1_manuscript_v11.md','MMT_manuscript_Q1_revision_v11.docx','MMT_supplementary_Q1_revision_v11.docx','highlights_v11.txt','render_word_v11.ps1']:copy(BASE/name)
    for p in (BASE/'assets').glob('*.png'):copy(p)
    copy(ROOT/'referencias_42_q1.json')
    for p in (ROOT/'gear_inverse_identifiability/results').rglob('*'):
        if p.is_file() and p.suffix in ['.json','.jsonl','.png'] and 'reference' not in p.parts:copy(p)
    for p in (ROOT/'fe2d').glob('*.py'):copy(p)
    copy(ROOT/'fe2d/requirements.txt');copy(ROOT/'fe2d/results/quadratic_eight_phases.json')
    for relative in ['revision_4_2026-10-12/numerical_review4.json','revision_5_2026-10-12/review5_summary.json','revision_5_2026-10-12/analytic_spectra_v5.png','revision_6_2026-10-12/review6_summary.json','revision_6_2026-10-12/angular_offset_control.json']:copy(ROOT/relative)
    for p in AUD.iterdir():
        if p.is_file() and p.suffix in ['.json','.jsonl','.png','.md']:copy(p)
    readme='''# Spur gear microgeometry identifiability

Reproducibility package accompanying the audited article and supplementary controls prepared on 23 October 2026.

The article establishes observability limits for a fixed-geometry gap operator. It does not establish validated physical reconstruction. The 24/24 FE dedendum signal is the centred combined-relief curve minus the centred addendum-only curve: 0.178987 µm RMS. An addendum-only inverse reaches the same residual as the four-parameter fit. The fitted dedendum is outside loaded support, and its depth and start profiles are flat over the tested domains.

## Layout

`manuscript/` contains the final article, supplement, editable Markdown, figure scripts and builders. `revision_11_2026-10-23/` contains independent audit records, the two new 102-phase FE cycles, mesh summaries and a Spanish scientific audit. `deposit_v6/` is an unchanged snapshot of the manuscript-v10 baseline at commit 8a08285ea9b6e8026d147102278f67e4c403e6bf. Its historical reports and phase11 signal label contain the superseded error; they are retained as evidence and must not be used as v11 conclusions. Other root directories contain the specific retained numerical inputs required by the article builder.

## Execution

Use Python 3.12 with NumPy, SciPy, Matplotlib, python-docx and Pillow. FE generation also requires gmsh, scikit-fem and meshio from the retained FE requirements. Exact versions used for the audit are recorded in `revision_11_2026-10-23/provenance.json`.

From this package root:

```text
python -m pytest deposit_v6/gear_inverse_identifiability/tests -q
python manuscript/audit_structure_v11.py
python manuscript/audit_statistics_v11.py
python manuscript/audit_v11.py
python manuscript/diagnose_invariance_v11.py
python manuscript/convergence_v11.py
python manuscript/figures_v11.py
python manuscript/build_review11.py
python manuscript/report_audit_v11.py
```

`audit_v11.py` reruns the broad-start, restricted and profile inversions. The convergence script retains completed FE phases and refits twelve starts per mesh. Remove only a deliberately selected new-cycle output file if a fresh rather than resumed FE run is desired. The archived h=0.50 mm cycle is used as the common baseline. The corrected phase11 script is optional and reruns the original two-start/50-realization experiment, writing a separate corrected output; it is not required for the independent audit.

## Evidence boundaries

Forty unit tests passed. Metrics, counts and keys of all 1800 original statistical fits were checked; those 1800 optimizations were not rerun. The 24/24 bulk study uses h=0.50, 0.35 and 0.25 mm at a fixed 0.02 mm nodal interface. It does not certify contact-interface refinement, excluded corner phases or the effect of physically remeshed relief. The original 57/57 controls are distinct and do not certify the 24/24 inversion. Profiles under deterministic cross-operator discrepancy are diagnostic objectives, not calibrated confidence intervals.

The twelve external amplitude cases are evaluated with four formulations; no formulation meets the stated 5% research target. Complete reference waveforms and matching CAD/support settings are not supplied. This package does not claim to reproduce the full external FE simulation.

`SHA256SUMS.json` covers package files except itself. This package has not been uploaded, assigned a DOI or represented as a public manuscript-v11 tag. The v10 baseline remains available at https://github.com/romusan/gears-inversion-reproducibility/tree/manuscript-v10. No new licence grant is asserted.
'''
    (DEST/'README.md').write_text(readme,encoding='utf-8')
    manifest={str(p.relative_to(DEST)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DEST.rglob('*')) if p.is_file() and p!=DEST/'SHA256SUMS.json'}
    (DEST/'SHA256SUMS.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    destzip=AUD/'MMT_reproducibility_v11.zip'
    with zipfile.ZipFile(destzip,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(DEST.rglob('*')):
            if p.is_file():z.write(p,Path('reproducibility_v11')/p.relative_to(DEST))
    print('Package files',len(manifest),'zip MB',destzip.stat().st_size/1e6)

if __name__=='__main__':main()
