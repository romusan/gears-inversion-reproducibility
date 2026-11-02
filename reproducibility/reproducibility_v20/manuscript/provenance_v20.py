"""Verify recorded calculation-source hashes and the unchanged v19 documents."""
from pathlib import Path
import json,hashlib,sys,platform,ast
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'revision_20_2026-11-01';OLD=ROOT/'revision_19_2026-11-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    files=list((ROOT/'fe2d').glob('*.py'))+list((ROOT/'manuscript').glob('*v20.py'))+[ROOT/'manuscript/inverse_moving_v19.py']
    for p in files:ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
    ledger={sha(p):str(p.relative_to(ROOT)).replace('\\','/') for p in files};checked=[]
    for p in list((OUT/'calculix_crosscheck').glob('*_input.json'))+list((OUT/'calculix_cycle_crosscheck').glob('*_input.json')):
        r=json.loads(p.read_text());assert r['source_sha256'] in ledger;checked.append(dict(file=str(p.relative_to(OUT)),source=ledger[r['source_sha256']]))
    for p in [OUT/'experiments/design_diagnostic_v20.json',OUT/'audit_shared_mesh_v20.json',OUT/'audit_ccx_v20.json']:
        r=json.loads(p.read_text());assert r['source_sha256'] in ledger
    for p in (OUT/'experiments').glob('starts_*.json'):
        for r in json.loads(p.read_text()):assert r['source_sha256']==sha(ROOT/'manuscript/starts_v20.py')
    old=json.loads((OLD/'audit_v19.json').read_text())
    for n,h in old['docx_sha256'].items():assert sha(OLD/n)==h
    (OUT/'provenance_v20.json').write_text(json.dumps(dict(python=sys.version,platform=platform.platform(),code_sha256={v:k for k,v in ledger.items()},input_sources_checked=checked,v19_documents_unchanged=True,scientific_scripts_parsed=len(files)),indent=2));print('Source hashes verified;',len(checked),'CCX input sources; v19 preserved')
if __name__=='__main__':main()
