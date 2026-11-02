"""Self-contained evidence layer with unchanged prior companion releases."""
from pathlib import Path
import json,zipfile,hashlib,shutil,sys
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'revision_19_2026-11-01';DEST=OUT/'reproducibility_v19'
DOCS=['MMT_manuscript_Q1_revision_v19_clean.docx','MMT_supplementary_Q1_revision_v19.docx','Highlights_v19.docx','Cover_letter_MMT_v19.docx']
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def copy(p,target):target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
def main():
    assert (OUT/'audit_v19.json').exists() and (OUT/'visual_QA_v19.json').exists()
    DEST.mkdir(exist_ok=True)
    for p in OUT.iterdir():
        if p.is_file() and p.suffix in ['.docx','.json','.jsonl','.csv','.txt','.log','.png'] and not p.name.startswith(('contact_','pdf_text_','manuscript_v18_text')) and p.name!='ENTREGA_VERIFICADA_v19.json':copy(p,DEST/OUT.name/p.name)
    for name in ['experiments','source_history']:
        for p in (OUT/name).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and 'body_cache' not in p.parts:copy(p,DEST/OUT.name/p.relative_to(OUT))
    for p in (ROOT/'fe2d').iterdir():
        if p.is_file() and p.suffix in ['.py','.txt']:copy(p,DEST/'fe2d'/p.name)
    for p in (ROOT/'manuscript').glob('*v19*'):
        if p.is_file():copy(p,DEST/'manuscript'/p.name)
    for name in ['build_v17.py','build_corrected_manuscript.py','render_v18.py','render_word_v11.ps1']:copy(ROOT/'manuscript'/name,DEST/'manuscript'/name)
    for p in (ROOT/'deposit_v6/gear_inverse_identifiability/src').rglob('*.py'):copy(p,DEST/p.relative_to(ROOT))
    for n in ['MMT_reproducibility_v18.zip']+['MMT_manuscript_Q1_revision_v18_clean.docx','MMT_supplementary_Q1_revision_v18.docx','Highlights_v18.docx','Cover_letter_MMT_v18.docx']:copy(ROOT/'revision_18_2026-11-01'/n,DEST/'revision_18_2026-11-01'/n)
    copy(ROOT/'objetivos_numericos_2026-11-01/EVIDENCIA_SIN_FABRICACION.zip',DEST/'companions/EVIDENCIA_SIN_FABRICACION.zip')
    for n in ['catalogo.json','LEER_PRIMERO.md']:
        p=ROOT/'referencias_soluciones_2026-11-01'/n
        if p.exists():copy(p,DEST/'referencias_soluciones_2026-11-01'/n)
    omitted={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in (OUT/'experiments/body_cache').glob('*.npz')}
    (DEST/'CACHES_EXCLUDED.json').write_text(json.dumps(omitted,indent=2))
    (DEST/'README.txt').write_text('''VERSION 19: numerical evidence and editable submission documents

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
''',encoding='utf-8')
    files=[p for p in sorted(DEST.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.json'];manifest={p.relative_to(DEST).as_posix():sha(p) for p in files}
    (DEST/'SHA256SUMS.json').write_text(json.dumps(manifest,indent=2))
    archive=OUT/'MMT_reproducibility_v19.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files+[DEST/'SHA256SUMS.json']:z.write(p,Path('reproducibility_v19')/p.relative_to(DEST))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for n,h in manifest.items():assert hashlib.sha256(z.read('reproducibility_v19/'+n)).hexdigest()==h
    kit=OUT/'submission_kit_v19';kit.mkdir(exist_ok=True)
    for n in DOCS:copy(OUT/n,kit/n)
    copy(archive,kit/archive.name);entries={n:sha(kit/n) for n in DOCS+[archive.name]};(kit/'CONTENIDO_Y_SHA256.json').write_text(json.dumps(entries,indent=2))
    path=OUT/'MMT_submission_kit_v19.zip'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for n in entries:z.write(kit/n,n)
        z.write(kit/'CONTENIDO_Y_SHA256.json','CONTENIDO_Y_SHA256.json');assert z.testzip() is None
    r=dict(files=len(manifest),submission_files=5,kit_sha256=sha(path),reproducibility_sha256=sha(archive),kit_MiB=round(path.stat().st_size/1024**2,2),all_manifest_hashes_verified=True)
    (OUT/'ENTREGA_VERIFICADA_v19.json').write_text(json.dumps(r,indent=2));print(r)
if __name__=='__main__':main()
