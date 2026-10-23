"""Preserve the v5 deposit and add the reviewed v6 numerical controls."""
from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/'deposit_v6'
DEST.mkdir(exist_ok=True)
OLD=ROOT/'deposit_v5';manifest=json.loads((OLD/'SHA256SUMS.json').read_text())
def write(path,data):
    target=DEST/path;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(data)
def copy(path):
    p=ROOT/path;data=p.read_bytes()
    if p.suffix in ['.py','.md','.json','.jsonl','.csv','.txt','.bib','.yaml','.cff']:
        data=data.replace(b'\r\n',b'\n')
        for root in [str(ROOT),str(ROOT).replace('\\','/'),str(ROOT).replace('\\','\\\\')]:data=data.replace(root.encode(),b'.')
    write(path,data)
for path in manifest:write(path,(OLD/path).read_bytes())
for name in ['run_fe2d.py','quadratic_eight_phases.py']:copy(Path('fe2d')/name)
for p in (ROOT/'fe2d/results').glob('*'):
    if ('_transition_weak_hat_local0.01_P2' in p.name and p.suffix in ['.json','.npz']) or p.name=='quadratic_eight_phases.json':copy(p.relative_to(ROOT))
copy(Path('gear_inverse_identifiability/experiments/Q1_review6_angular.py'))
for p in (ROOT/'revision_6_2026-10-12').glob('*'):
    if p.is_file() and p.suffix in ['.json','.csv','.md','.npz','.py'] and 'partial' not in p.name:copy(p.relative_to(ROOT))
readme=(DEST/'README.md').read_text()
readme=readme.replace('Remaining FE records are the original linear/nodal controls and must not be pooled with the new formulation.', 'The quadratic eight-phase campaign is separately identified by quadratic_eight_phases.json. The original linear/nodal controls must not be pooled with the quadratic formulation.')
readme+='''
## Revision 6 controls

The annotated tags `manuscript-v5` and `manuscript-v6` identify separate versions. Revision 6 repeats the eight original FE phases with P2 displacement and weak distributed pressure, reports seed improvement fractions and near ties, and adds 0.21-degree offset envelopes. Run `python fe2d/quadratic_eight_phases.py`, then from `gear_inverse_identifiability` run `python experiments/Q1_review6_angular.py`, then from the repository root run `python revision_6_2026-10-12/summarize_review6.py`.

The FE envelope is computed from an eight-node periodic interpolant. It is not a direct dense FE scan and cannot resolve the FE transition ramp. The analytical waveform uses successively refined angular nodes. The numerical envelope algorithm covers every interpolation-offset interval with a fixed one-cycle window and 30 or 31 samples. Interface stiffness is nonmonotonic; observed small changes are not a certified convergence order or exact-error bound. The fixed-normal FE body torque deviations and adaptive tangent checks are retained in the review-6 summary. No stiffness calibration to the reference is introduced.

No DOI has been assigned. The GitHub tag and commit SHA provide version identification; they are not represented as a Zenodo DOI.
'''
write(Path('README.md'),readme.encode())
write(Path('CITATION.cff'),'''cff-version: 1.2.0
message: "Please cite the exact tagged version and commit used."
title: "Contact support and practical identifiability of spur gear microgeometry from transmission error numerical controls"
type: software
version: manuscript-v6
date-released: 2026-10-12
repository-code: "https://github.com/romusan/gears-inversion-reproducibility"
url: "https://github.com/romusan/gears-inversion-reproducibility/tree/manuscript-v6"
authors:
  - family-names: "Sandoval Flórez"
    given-names: "Romulo"
    affiliation: "Universidad ECCI"
  - family-names: "Parra Medina"
    given-names: "Claudia Patricia"
    affiliation: "Grupo GAV Universidad Militar Nueva Granada"
  - family-names: "Vargas Fonseca"
    given-names: "German Leandro"
    affiliation: "Grupo GAV Universidad Militar Nueva Granada"
'''.encode())
summary_path=Path('revision_6_2026-10-12/review6_summary.json')
summary=json.loads((DEST/summary_path).read_text())
summary['source_sha256_observed_local']=summary['source_sha256']
summary['source_sha256']={key.replace('\\','/'):hashlib.sha256((DEST/key.replace('\\','/')).read_bytes()).hexdigest() for key in summary['source_sha256_observed_local']}
write(summary_path,json.dumps(summary,indent=2).encode())
new={p.relative_to(DEST).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DEST.rglob('*')) if p.is_file() and not any(s in ['.git','__pycache__','.pytest_cache'] for s in p.parts) and p.name!='SHA256SUMS.json' and p.suffix!='.pyc'}
write(Path('SHA256SUMS.json'),json.dumps(new,indent=2).encode())
with zipfile.ZipFile(ROOT/'revision_6_2026-10-12/reproducibility_v6.zip','w',zipfile.ZIP_DEFLATED) as z:
    for path in list(new)+['SHA256SUMS.json']:z.write(DEST/path,path)
print('Prepared version 6:',len(new),'files')
