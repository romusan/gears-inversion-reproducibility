"""Build v14 reproducibility and journal-upload kits with verified manifests."""
import json,hashlib,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;BASE=ROOT/'manuscript';OUT=ROOT/'revision_14_2026-11-01';DEST=OUT/'reproducibility_v14'
DOCS=['MMT_manuscript_Q1_revision_v14.docx','MMT_supplementary_Q1_revision_v14.docx','Highlights_v14.docx','Cover_letter_MMT_v14.docx']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    if not DEST.exists():shutil.copytree(ROOT/'revision_13_2026-10-23/reproducibility_v13',DEST,ignore=shutil.ignore_patterns('.git','__pycache__','.pytest_cache'))
    for name in ['experiment_v14.py','review14_sections.py','prepare_v14.py','finish_bibliography_v14.py','build_review14.py','audit_v14.py','package_v14.py','render_v14.py','q1_manuscript_v14.md','highlights_v14.txt',*DOCS]:shutil.copy2(BASE/name,DEST/'manuscript'/name)
    shutil.copy2(BASE/'assets/fig_restricted_distance_v14.png',DEST/'manuscript/assets/fig_restricted_distance_v14.png')
    shutil.copy2(ROOT/'referencias_45_v14.json',DEST/'referencias_45_v14.json')
    target=DEST/OUT.name;target.mkdir(exist_ok=True)
    for p in OUT.iterdir():
        if p.is_file() and p.suffix in ['.json','.md','.log']:shutil.copy2(p,target/p.name)
    metadata=DEST/'diagnostico_2026-11-01/referencias';metadata.mkdir(parents=True,exist_ok=True)
    for name in ['R06_crossref.json','catalogo.json']:shutil.copy2(ROOT/'diagnostico_2026-11-01/referencias'/name,metadata/name)
    (DEST/'README.md').write_text('''# Version 14 evidence accompanying the MMT submission

Current article: manuscript/MMT_manuscript_Q1_revision_v14.docx. Current supplement: manuscript/MMT_supplementary_Q1_revision_v14.docx. Prepared 1 November 2026. The current v14 archive accompanies the submission; no public v14 URL or DOI is claimed. The public historical baseline is https://github.com/romusan/gears-inversion-reproducibility/tree/manuscript-v13.

This package preserves v13 evidence and adds 32 noiseless same-operator controls with 192 restricted fits, an eleventh figure, supplementary Tables S22–S23 and three pertinent references. New records are under revision_14_2026-11-01. Historical files ending v12 or v13 are prior evidence, not the current upload files. No new physical validation, experimental data or complete-cycle FE inverse convergence is asserted. The four analytical formulations still miss the external 5% amplitude research target. New controls do not recertify the 1800 historical optimizations.

## Reproduction

Use Python 3.12 with NumPy, SciPy, Matplotlib, python-docx, Pillow and lxml; FE-specific requirements are retained with the baseline. Recorded numerical versions and hashes are in restricted_distance_summary.json. The new experiment uses the retained deposit_v6 mechanics and both Lambert-W and iterative force engines. From this package root:

```text
python -m pytest deposit_v6/gear_inverse_identifiability/tests -q
python manuscript/experiment_v14.py
python manuscript/prepare_v14.py
python manuscript/build_review14.py
python manuscript/audit_v14.py
```

The experiment records all six bounded starts per cell, including truth addendum coordinates and three fixed-seed random starts. Reported minima are multistart local results, not global certificates. Dense 960-position evaluations share canonical fitting points and are not independent data. D120 normalizes residuals to a reference sample count and noise scale; it is not a calibrated significance test.

The scientific Markdown uses the original reference IDs and section markers for deterministic construction. The final DOCX references are renumbered by first appearance, with mapping and ordered metadata under revision_14_2026-11-01. Markers are absent from the final DOCX; editable OMML equations are preserved.

## Documents and visual QA

Existing figure and table formatting is preserved. The bundled render_docx.py failed because LibreOffice is absent on this Windows host. Native Microsoft Word PDF export was used, followed by page rasterization with pdf2image/Poppler and visual inspection. Exported PDFs and page PNGs are local QA artifacts, excluded from this archive. render_v14.py can rasterize available local Word-exported PDFs; pdf2image, Pillow and native Poppler are needed for that optional step. The scientific reproduction does not depend on native Word.

SHA256SUMS.json covers every distributed file except itself. No new licence grant is asserted. The archive does not distribute the downloaded third-party full texts. A prepared kit is not an editorial submission or an acceptance decision.
''',encoding='utf-8')
    cff=(ROOT/'revision_13_2026-10-23/reproducibility_v13/CITATION.cff').read_text(encoding='utf-8').replace('version: "13"','version: "14"').replace('date-released: "2026-10-24"','date-released: "2026-11-01"')
    cff='\n'.join(line for line in cff.splitlines() if not line.startswith('url:'))+'\n';(DEST/'CITATION.cff').write_text(cff,encoding='utf-8')
    files=[p for p in sorted(DEST.rglob('*')) if p.is_file() and p!=DEST/'SHA256SUMS.json' and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts]
    manifest={p.relative_to(DEST).as_posix():digest(p) for p in files};(DEST/'SHA256SUMS.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    archive=OUT/'MMT_reproducibility_v14.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files+[DEST/'SHA256SUMS.json']:z.write(p,Path('reproducibility_v14')/p.relative_to(DEST))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,h in manifest.items():assert hashlib.sha256(z.read('reproducibility_v14/'+name)).hexdigest()==h
    kit=OUT/'submission_kit_v14';kit.mkdir(exist_ok=True)
    for name in DOCS:shutil.copy2(BASE/name,kit/name)
    shutil.copy2(archive,kit/archive.name)
    entries={name:digest(kit/name) for name in DOCS+[archive.name]}
    (kit/'CONTENIDO_Y_SHA256.json').write_text(json.dumps(entries,indent=2),encoding='utf-8')
    with zipfile.ZipFile(OUT/'MMT_submission_kit_v14.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in entries:z.write(kit/name,name)
        z.write(kit/'CONTENIDO_Y_SHA256.json','CONTENIDO_Y_SHA256.json')
    print('Verified',len(manifest),'reproducibility files and five upload files')
if __name__=='__main__':main()
