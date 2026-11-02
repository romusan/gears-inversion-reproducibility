"""Package the accepted editorial integration without changing numerical evidence."""
from pathlib import Path
import json,zipfile,hashlib,shutil
ROOT=Path(__file__).resolve().parent.parent;BASE=ROOT/'manuscript';OUT=ROOT/'revision_16_2026-11-01';DEST=OUT/'reproducibility_v16'
DOCS=['MMT_manuscript_Q1_revision_v16_clean.docx','MMT_supplementary_Q1_revision_v16.docx','Highlights_v16.docx','Cover_letter_MMT_v16.docx']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    if not DEST.exists():shutil.copytree(ROOT/'revision_14_2026-11-01/reproducibility_v14',DEST,ignore=shutil.ignore_patterns('.git','__pycache__','.pytest_cache'))
    for name in ['build_v16.py','audit_v16.py','render_v16.py','package_v16.py','smoke_v16.py','render_markup_v16.ps1','render_word_v11.ps1']:shutil.copy2(BASE/name,DEST/'manuscript'/name)
    target=DEST/OUT.name;target.mkdir(exist_ok=True)
    for p in OUT.iterdir():
        if p.is_file() and p.suffix in ['.json','.md','.log','.docx']:shutil.copy2(p,target/p.name)
    (target/'editorial_sources').mkdir(exist_ok=True)
    shutil.copy2(OUT/'editorial_sources/v15_accepted_OMML.docx',target/'editorial_sources/v15_accepted_OMML.docx')
    (DEST/'revision').mkdir(exist_ok=True)
    for name in ['MMT_manuscript_Q1_revision_v15_clean.docx','MMT_manuscript_Q1_revision_v15_tracked.docx']:shutil.copy2(ROOT/'revision'/name,DEST/'revision'/name)
    (DEST/'README.md').write_text('''# Version 16 editorial and numerical evidence package

Current submission article: revision_16_2026-11-01/MMT_manuscript_Q1_revision_v16_clean.docx. Current supplement, Highlights and cover letter are in the same folder. The tracked v16 is for author review, not the journal's clean upload. It shows only 15 paragraph corrections relative to accepted v15.

Version 16 integrates the supplied editorial review without new numerical experiments. The v14 restricted-distance records (32 cases, 192 attempted fits) and all earlier numerical evidence are retained unchanged. Physical inverse validation, unresolved FE transition phases and external amplitude discrepancy are not claimed as resolved. No DOI or new public deposit is claimed; the historical baseline is https://github.com/romusan/gears-inversion-reproducibility/tree/manuscript-v13.

## Editorial source and construction

The supplied v15 originals in revision/ are provenance inputs, not current submission files. In particular, the supplied clean v15 lost its OMML equations and retains comments. Do not use it for submission. The stable construction seed is revision_16_2026-11-01/editorial_sources/v15_accepted_OMML.docx, obtained by accepting the v15 tracked input and removing comments. It preserves all 15 equations. build_v16.py applies the documented narrow corrections and produces clean and tracked files, a supplement, Highlights and cover. Equation (2) uses η for the line-of-action coordinate; the remaining expressions match v14. No simulation is run by the editorial builder.

With Python 3.12, python-docx and lxml, from this package root:

```text
python manuscript/build_v16.py
python manuscript/audit_v16.py
```

The audit verifies that accepting the new tracked changes produces the exact clean document XML; all 45 references are ordered; numeric table cells match v14; S1–S23 remain complete; the line-of-action notation is distinct from the load index; and no unfilled DOI promise or comments remain in the clean manuscript. Original v15 hashes and the user-confirmed common CRediT roles are documented in the audit and response report.

## Retained numerical reproduction

NumPy, SciPy and Matplotlib are additionally required for the retained numerical scripts. Their versions, source hashes, random starts, optimizer flags and results are stored with the v14 evidence. To run the existing regression suite:

```text
python -m pytest deposit_v6/gear_inverse_identifiability/tests -q
```

For the v14 experiment use manuscript/experiment_v14.py, and consult the retained v14 README/history for older campaigns. Do not treat synthetic same-operator data as physical validation, or a descriptive D120 distance as a calibrated test. Dense evaluation grids share fitting positions. Historical v14 builders reconstruct the historical v14 article; they do not replace the current v16 editorial construction.

## Submission and deposit

Use only the separate submission_kit_v16 folder or its ZIP for journal upload: four clean/editable documents plus MMT_reproducibility_v16.zip. Keep the tracked manuscript as an author-review copy. A prepared kit is not an editorial submission. Metadata for a possible authenticated repository deposit are provided as a descriptive draft; no licence grant or DOI issuance is asserted. The current specific MMT guide could not be independently read because it returned HTTP 403.

Native Word PDF export and pdf2image/Poppler page rasterization were used for visual QA because bundled render_docx.py requires LibreOffice, which is absent on this host. QA PDFs and page PNGs are excluded. SHA256SUMS.json covers all distributed files except itself. No new licence grant is asserted.
''',encoding='utf-8')
    cff=(ROOT/'revision_14_2026-11-01/reproducibility_v14/CITATION.cff').read_text(encoding='utf-8').replace('version: "14"','version: "16"');(DEST/'CITATION.cff').write_text(cff,encoding='utf-8')
    files=[p for p in sorted(DEST.rglob('*')) if p.is_file() and p!=DEST/'SHA256SUMS.json' and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts]
    manifest={p.relative_to(DEST).as_posix():sha(p) for p in files};(DEST/'SHA256SUMS.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    archive=OUT/'MMT_reproducibility_v16.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files+[DEST/'SHA256SUMS.json']:z.write(p,Path('reproducibility_v16')/p.relative_to(DEST))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,h in manifest.items():assert hashlib.sha256(z.read('reproducibility_v16/'+name)).hexdigest()==h
    kit=OUT/'submission_kit_v16';kit.mkdir(exist_ok=True)
    for name in DOCS:shutil.copy2(OUT/name,kit/name)
    shutil.copy2(archive,kit/archive.name)
    entries={name:sha(kit/name) for name in DOCS+[archive.name]}
    (kit/'CONTENIDO_Y_SHA256.json').write_text(json.dumps(entries,indent=2),encoding='utf-8')
    with zipfile.ZipFile(OUT/'MMT_submission_kit_v16.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in entries:z.write(kit/name,name)
        z.write(kit/'CONTENIDO_Y_SHA256.json','CONTENIDO_Y_SHA256.json')
        assert z.testzip() is None
    print('Verified',len(manifest),'package files and five journal upload files')
if __name__=='__main__':main()
