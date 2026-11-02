"""Assemble the final clean submission kit and verify every distributed hash."""
from pathlib import Path
import shutil,json,zipfile,hashlib
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'revision_17_final_2026-11-01';DEST=OUT/'reproducibility_v17'
DOCS=['MMT_manuscript_Q1_revision_v17_clean.docx','MMT_supplementary_Q1_revision_v17.docx','Highlights_v17.docx','Cover_letter_MMT_v17.docx']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    if not DEST.exists():shutil.copytree(ROOT/'revision_16_2026-11-01/reproducibility_v16',DEST,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
    target=DEST/OUT.name;target.mkdir(exist_ok=True)
    for p in OUT.iterdir():
        if p.is_file() and p.name!='ENTREGA_VERIFICADA_v17.json' and (p.suffix in ['.docx','.json','.jsonl','.md','.log'] or p.name=='stress_v17.png'):shutil.copy2(p,target/p.name)
    for name in ['stress_v17.py','audit_stress_v17.py','plot_stress_v17.py','build_v17.py','audit_v17.py','package_v17.py','render_v17.py','smoke_v17.py']:
        shutil.copy2(ROOT/'manuscript'/name,DEST/'manuscript'/name)
    # The former final article is a provenance input to the narrow v17 builder.
    old=DEST/'revision_16_2026-11-01'
    for name in ['MMT_manuscript_Q1_revision_v16_clean.docx','MMT_supplementary_Q1_revision_v16.docx','Highlights_v16.docx','Cover_letter_MMT_v16.docx']:
        shutil.copy2(ROOT/'revision_16_2026-11-01'/name,old/name)
    (DEST/'README.md').write_text('''# Version 17 final evidence package

Current upload documents are in revision_17_final_2026-11-01. Earlier versions are provenance and are not current submission copies. The article preserves all 15 equations and 45 references. S1–S23 and all earlier numerical tables remain unchanged; S24–S27 add finite stress results, optimizer partitions and proposed follow-up experiments.

The additional campaign comprises 500 selected synthetic fits, 1500 attempted local fits, 50 paired realizations per scenario and generating start. It covers IID noise, stationary nonperiodic AR correlation (rho=0.8) with IID/known-covariance GLS fitting, a 5% gain error, and shear-G generation versus projected-energy inversion. These are illustrative controls, not measurements, discrepancy calibration, a global optimization certificate or a coverage study. Raw data and all attempted fits are retained. The 1800 historical selections are stratified without rerunning or replacing them. See stress_summary.json and numerical_audit_v17.json.

## Reproduce the saved-results article

From the extracted package root, with Python 3.12, python-docx and lxml:

```
python manuscript/build_v17.py
python manuscript/audit_v17.py
```

The builder reads preserved v16 documents and saved stress results; it does not simulate new data. It preserves OMML and existing numerical tables. Rebuilt Word parts should be identical; container metadata timestamps can differ. Native Microsoft Word export and Poppler rasterization were used for visual QA because LibreOffice is absent on the authoring host. Internal QA images/PDFs are not submission files.

## Reproduce and audit the numerical controls

NumPy, SciPy and Matplotlib are additionally required; exact used versions and source hashes are in stress_summary.json. The campaign script resumes only when its recorded source hash matches and writes completed cases incrementally. To regenerate from scratch, use a fresh copy with the stress records/source receipt absent; do not overwrite the distributed evidence without preserving it.

```
python manuscript/stress_v17.py
python manuscript/plot_stress_v17.py
python manuscript/audit_stress_v17.py
python -m pytest deposit_v6/gear_inverse_identifiability/tests -q
```

The audit independently recomputes every selected objective, observation seed/covariance, generating curve and bound partition. All numerical errors are conditional on declared synthetic truths and operators. The complementarity/contact modules and retained earlier campaigns remain under deposit_v6 and the historical version folders.

## Submission status and provenance

The five-file submission kit contains four clean editable documents plus this evidence ZIP. Prepared files are not an editorial submission. No DOI has been issued or deposit published for v17. The public manuscript-v13 baseline is historical. The metadata draft does not grant a licence. The unresolved 18 FE transition phases, physical corner/fillet contact and measured-waveform validation remain explicit limitations. The v16 tracked copy retained in provenance has 15 insertions and 15 deletions; accepting them matches v16 clean. The current v17 clean has no comments or pending revisions. The final revision is described in editorial_changes_v17.json and RESPUESTA_REVISION_FINAL.md.

SHA256SUMS.json covers distributed files except itself. Previous manifests describe their historical releases. No new licence grant is asserted.
''',encoding='utf-8')
    cff=(DEST/'CITATION.cff').read_text(encoding='utf-8').replace('version: "16"','version: "17"');(DEST/'CITATION.cff').write_text(cff,encoding='utf-8')
    files=[p for p in sorted(DEST.rglob('*')) if p.is_file() and p!=DEST/'SHA256SUMS.json' and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts]
    manifest={p.relative_to(DEST).as_posix():sha(p) for p in files};(DEST/'SHA256SUMS.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    archive=OUT/'MMT_reproducibility_v17.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files+[DEST/'SHA256SUMS.json']:z.write(p,Path('reproducibility_v17')/p.relative_to(DEST))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,h in manifest.items():assert hashlib.sha256(z.read('reproducibility_v17/'+name)).hexdigest()==h
    kit=OUT/'submission_kit_v17';kit.mkdir(exist_ok=True)
    for name in DOCS:shutil.copy2(OUT/name,kit/name)
    shutil.copy2(archive,kit/archive.name)
    entries={n:sha(kit/n) for n in DOCS+[archive.name]};(kit/'CONTENIDO_Y_SHA256.json').write_text(json.dumps(entries,indent=2),encoding='utf-8')
    with zipfile.ZipFile(OUT/'MMT_submission_kit_v17.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in entries:z.write(kit/name,name)
        z.write(kit/'CONTENIDO_Y_SHA256.json','CONTENIDO_Y_SHA256.json');assert z.testzip() is None
    receipt=dict(files=len(manifest),submission_files=5,kit_sha256=sha(OUT/'MMT_submission_kit_v17.zip'),reproducibility_sha256=sha(archive),kit_MiB=round((OUT/'MMT_submission_kit_v17.zip').stat().st_size/1024**2,2),all_manifest_hashes_verified=True)
    (OUT/'ENTREGA_VERIFICADA_v17.json').write_text(json.dumps(receipt,indent=2));print(receipt)
if __name__=='__main__':main()
