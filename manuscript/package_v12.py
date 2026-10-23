"""Portable final evidence package, with a manifest verified after compression."""
import json,hashlib,shutil,zipfile
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent;AUD=ROOT/'revision_12_2026-10-23';DEST=AUD/'reproducibility_v12'
def copy(path,relative=None):
    target=DEST/(relative or path.relative_to(ROOT));target.parent.mkdir(parents=True,exist_ok=True)
    if 'deposit_v6' not in path.parts and path.suffix=='.json' and (path.name.startswith('referencias_') or path.name=='bibliography_registry_audit.json' or path.parent.name=='reference_sources'):
        def bibliographic(value):
            if isinstance(value,dict):return {k:bibliographic(v) for k,v in value.items() if k!='abstract'}
            if isinstance(value,list):return [bibliographic(v) for v in value]
            return value
        target.write_text(json.dumps(bibliographic(json.loads(path.read_text(encoding='utf-8'))),indent=2,ensure_ascii=False),encoding='utf-8')
    else:shutil.copy2(path,target)
def main():
    DEST.mkdir(exist_ok=True)
    for p in (ROOT/'deposit_v6').rglob('*'):
        if p.is_file() and not any(x in p.parts for x in ['.git','.pytest_cache','__pycache__','.venv']):copy(p)
    for p in BASE.glob('*.py'):copy(p)
    for name in ['q1_manuscript_v12.md','MMT_manuscript_Q1_revision_v12.docx','MMT_supplementary_Q1_revision_v12.docx','Highlights_v12.docx','highlights_v12.txt','render_word_v11.ps1']:copy(BASE/name)
    for p in (BASE/'assets').glob('*.png'):copy(p)
    for name in ['referencias_42_q1.json','referencias_42_v12.json']:copy(ROOT/name)
    for p in (ROOT/'gear_inverse_identifiability/results').rglob('*'):
        if p.is_file() and p.suffix in ['.json','.jsonl','.png'] and 'reference' not in p.parts:copy(p)
    for p in (ROOT/'fe2d').glob('*.py'):copy(p)
    copy(ROOT/'fe2d/requirements.txt');copy(ROOT/'fe2d/results/quadratic_eight_phases.json')
    for relative in ['revision_4_2026-10-12/numerical_review4.json','revision_5_2026-10-12/review5_summary.json','revision_5_2026-10-12/analytic_spectra_v5.png','revision_6_2026-10-12/review6_summary.json','revision_6_2026-10-12/angular_offset_control.json']:copy(ROOT/relative)
    for p in (ROOT/'revision_11_2026-10-23').iterdir():
        if p.is_file() and p.suffix in ['.json','.jsonl','.png','.md']:copy(p)
    for p in AUD.iterdir():
        if p.is_file() and p.suffix in ['.json','.jsonl','.md'] and p.name not in ['physical_geometry_records.jsonl','interface24_records.jsonl','publication_receipt.json']:copy(p)
    for p in (AUD/'reference_sources').glob('*.json'):copy(p)
    readme='''# Contact support and practical identifiability of spur gear microgeometry

Version 12 accompanying the final article and supplementary controls prepared on 23 October 2026. The versioned repository is https://github.com/romusan/gears-inversion-reproducibility/tree/manuscript-v12. No DOI is assigned. Historical v10 results are preserved inside `deposit_v6/`; they contain the superseded mixed-relief signal comparison and are not the current conclusions.

## Scientific result

The fixed-geometry gap operator has exactly invisible relief sets determined by loaded support. Its coupled-compliance extension, weak transition and centred-response gauge are conditional observability results. The corrected 24/24 FE isolated dedendum signal is 0.178987 µm RMS, versus 0.196589 µm analytically. Nevertheless, restricted and unrestricted inversions have the same residual and dedendum profiles are flat. This does not demonstrate physical profile recovery.

Bulk P1 refinement stabilizes the isolated contrast while the combined waveform and inverse residual still move. Dedicated v12 controls compare complete retained waveforms, erode the angular mask, refine pressure hats on identical P2 body meshes, and physically remove material with reassembled elastic stiffness. The latter two controls use explicitly recorded eligible phase subsets, not a complete-cycle or inverse convergence certificate. Unresolved corner phases are not treated as validated FE observations. All four analytical formulations exceed the adopted 5% external amplitude target.

## Layout and execution

`manuscript/` contains final DOCX files, editable scientific Markdown, figure scripts and deterministic builders. `revision_12_2026-10-23/` contains new verified records, phase selection, summaries, 42-reference verification, source metadata and the Spanish independent audit. `revision_11_2026-10-23/` supplies broad-start and restricted inversions, profiles and bulk-mesh cycles. The unchanged historical baseline is commit 8a08285ea9b6e8026d147102278f67e4c403e6bf, preserved under `deposit_v6/`.

Use Python 3.12 with NumPy, SciPy, Matplotlib, python-docx and Pillow. FE generation additionally requires gmsh, scikit-fem and meshio; retained requirements and recorded versions are included. From this package root:

```text
python -m pytest deposit_v6/gear_inverse_identifiability/tests -q
python manuscript/audit_structure_v11.py
python manuscript/audit_statistics_v11.py
python manuscript/audit_v11.py
python manuscript/diagnose_invariance_v11.py
python manuscript/convergence_v11.py
python manuscript/waveform_mask_v12.py
python manuscript/interface_v12.py
python manuscript/physical_geometry_v12.py
python manuscript/audit_references_v12.py
python manuscript/prepare_bibliography_v12.py
python manuscript/prepare_source_v12.py
python manuscript/figures_v11.py
python manuscript/figures_controls_v12.py
python manuscript/build_review12.py
python manuscript/final_audit_v12.py
```

The FE scripts resume their verified JSONL outputs. Do not combine pilot files with verified runs. Failed exploratory trace/projection checks were corrected before the final verified runs; incomplete pilot records are excluded from this package. Reproduction from scratch requires moving the deliberately selected verified output files aside before rerunning. The bibliography fetcher uses cached publisher-deposited Crossref metadata and respects rate limits. Registry verification is distinguished from full-text reading; targeted editorial abstracts and ISO catalogue checks are documented. Distributed metadata caches omit complete abstracts; titles, authors, publication fields and identifiers are retained.

Forty unit tests pass. Metrics from all 1800 archived statistical fits were audited; those 1800 optimizations were not rerun. Statistical precision assumes the declared noise and mechanical operator. Deterministic cross-operator profile objectives are not calibrated confidence intervals. Complete external benchmark waveforms, CAD and solver settings are unavailable; this package does not claim to reproduce those external FE simulations.

`SHA256SUMS.json` covers every package file except itself. PDF page renders are local QA outputs, not required numerical inputs. The final article is written as a scientific argument; revision history belongs to the separate audit, not its narrative. No new licence grant is asserted.
'''
    (DEST/'README.md').write_text(readme,encoding='utf-8')

    (DEST/'CITATION.cff').write_text('''cff-version: 1.2.0
message: "Cite this versioned evidence package with the accompanying article."
type: software
title: "Contact support and practical identifiability of spur gear microgeometry from transmission error"
version: "12"
date-released: "2026-10-23"
url: "https://github.com/romusan/gears-inversion-reproducibility/tree/manuscript-v12"
authors:
  - family-names: "Sandoval Flórez"
    given-names: "Romulo"
  - family-names: "Parra Medina"
    given-names: "Claudia Patricia"
  - family-names: "Vargas Fonseca"
    given-names: "German Leandro"
''',encoding='utf-8')

    files=[p for p in sorted(DEST.rglob('*')) if p.is_file() and '.git' not in p.parts and p!=DEST/'SHA256SUMS.json']
    manifest={p.relative_to(DEST).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (DEST/'SHA256SUMS.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    destzip=AUD/'MMT_reproducibility_v12.zip'
    with zipfile.ZipFile(destzip,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files+[DEST/'SHA256SUMS.json']:z.write(p,Path('reproducibility_v12')/p.relative_to(DEST))
    with zipfile.ZipFile(destzip) as z:
        assert z.testzip() is None
        for name,digest in manifest.items():assert hashlib.sha256(z.read('reproducibility_v12/'+name)).hexdigest()==digest,name
    print('Verified package files',len(manifest),'zip MB',destzip.stat().st_size/1e6)
if __name__=='__main__':main()
