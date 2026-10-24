"""Prepare the focused revision and a complete journal upload kit."""
import json,hashlib,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;BASE=ROOT/'manuscript';OUT=ROOT/'revision_13_2026-10-23';DEST=OUT/'reproducibility_v13'
def main():
    source=ROOT/'revision_12_2026-10-23/reproducibility_v12'
    if not DEST.exists():shutil.copytree(source,DEST,ignore=shutil.ignore_patterns('.git'))
    for p in BASE.glob('*.py'):shutil.copy2(p,DEST/'manuscript'/p.name)
    for name in ['MMT_manuscript_Q1_revision_v13.docx','MMT_supplementary_Q1_revision_v13.docx','Highlights_v13.docx','highlights_v13.txt','q1_manuscript_v13.md']:shutil.copy2(BASE/name,DEST/'manuscript'/name)
    target=DEST/OUT.name;target.mkdir(exist_ok=True)
    for p in OUT.iterdir():
        if p.is_file() and p.suffix in ['.json','.jsonl','.md'] and p.name!='publication_receipt.json':shutil.copy2(p,target/p.name)
    readme=(source/'README.md').read_text(encoding='utf-8').replace('Version 12 accompanying','Version 13 accompanying').replace('tree/manuscript-v12','tree/manuscript-v13').replace('prepared on 23 October 2026','finalized on 24 October 2026')
    readme+='''

## Focused version 13 numerical controls

The current submission files end in v13. The retained v12 files document the previous evidence. Version 13 adds only targeted numerical controls for the nanometre physical-removal contrast and clarifies the information excluded by the phase mask. S21 is not a rigorous continuum error bound or a certificate for the P1 full-cycle inverse.

Install mpmath 1.4.1 in addition to the recorded FE dependencies. The full elastic assembly remains float64. The enhanced control uses alternative sparse-LU ordering, four elastic residual corrections, and 80-digit polishing of the condensed active-contact equations. Weighted harmonic morphing holds the identical boundary polygon fixed; pressure refinement uses the same eight phases as S20.

```text
python manuscript/precision_v13.py
python manuscript/build_review13.py
python manuscript/audit_v13.py
```

The 1800 archived optimizations are not repeated in this focused revision. The main DOCX, supplementary DOCX, editable Highlights and reproducibility ZIP are explicitly listed in the separate journal upload kit. A prepared upload kit does not imply submission to a journal.
'''
    (DEST/'README.md').write_text(readme,encoding='utf-8')
    c=(source/'CITATION.cff').read_text(encoding='utf-8').replace('version: "12"','version: "13"').replace('tree/manuscript-v12','tree/manuscript-v13').replace('date-released: "2026-10-23"','date-released: "2026-10-24"');(DEST/'CITATION.cff').write_text(c,encoding='utf-8')
    files=[p for p in sorted(DEST.rglob('*')) if p.is_file() and '.git' not in p.parts and p!=DEST/'SHA256SUMS.json']
    manifest={p.relative_to(DEST).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (DEST/'SHA256SUMS.json').write_text(json.dumps(manifest,indent=2))
    archive=OUT/'MMT_reproducibility_v13.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files+[DEST/'SHA256SUMS.json']:z.write(p,Path('reproducibility_v13')/p.relative_to(DEST))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,digest in manifest.items():assert hashlib.sha256(z.read('reproducibility_v13/'+name)).hexdigest()==digest
    kit=OUT/'submission_kit_v13';kit.mkdir(exist_ok=True)
    for name in ['MMT_manuscript_Q1_revision_v13.docx','MMT_supplementary_Q1_revision_v13.docx','Highlights_v13.docx']:shutil.copy2(BASE/name,kit/name)
    shutil.copy2(archive,kit/archive.name)
    entries={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in kit.iterdir() if p.is_file() and p.name!='CONTENIDO_Y_SHA256.json'}
    assert set(entries)=={'MMT_manuscript_Q1_revision_v13.docx','MMT_supplementary_Q1_revision_v13.docx','Highlights_v13.docx','MMT_reproducibility_v13.zip'}
    (kit/'CONTENIDO_Y_SHA256.json').write_text(json.dumps(entries,indent=2))
    with zipfile.ZipFile(OUT/'MMT_submission_kit_v13.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in kit.iterdir():z.write(p,p.name)
    print('Verified reproducibility files',len(manifest),'and all four journal upload files')
if __name__=='__main__':main()
