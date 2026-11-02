"""Resolve each recorded numerical source hash to an immutable source file."""
from pathlib import Path
import hashlib,json,sys,platform,importlib.metadata as im
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'revision_19_2026-11-01'
def main():
    sources=list((ROOT/'fe2d').glob('*.py'))+list((OUT/'source_history').glob('*.py'))+list((ROOT/'manuscript').glob('*v19*.py'))
    lookup={hashlib.sha256(p.read_bytes()).hexdigest():p.relative_to(ROOT).as_posix() for p in sources}
    wanted={}
    for path in (OUT/'experiments').glob('*.json*'):
        if path.suffix=='.jsonl':rr=[json.loads(l) for l in path.read_text().splitlines() if l.strip()]
        else:
            obj=json.loads(path.read_text());rr=obj if isinstance(obj,list) else [obj]
        for r in rr:
            if not isinstance(r,dict):continue
            for k,v in r.items():
                if k.endswith('source_sha256'):
                    assert v in lookup,(path,k,v)
                    wanted[v]=lookup[v]
    versions={}
    sys.path.append(str(ROOT/'fe2d/.venv/Lib/site-packages'))
    for name in ['numpy','scipy','matplotlib','gmsh','scikit-fem','meshio','shapely']:
        try:versions[name]=im.version(name)
        except im.PackageNotFoundError:versions[name]='not found'
    r=dict(recorded_source_versions=len(wanted),all_resolved=True,source_hash_ledger=wanted,python=sys.version,platform=platform.platform(),versions=versions)
    (OUT/'provenance_v19.json').write_text(json.dumps(r,indent=2));print(r)
if __name__=='__main__':main()
