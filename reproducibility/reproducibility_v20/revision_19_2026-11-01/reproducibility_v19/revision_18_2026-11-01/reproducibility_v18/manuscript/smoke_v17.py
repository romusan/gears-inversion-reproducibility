"""Rebuild the four Word artifacts from an independently extracted final archive."""
from pathlib import Path
import argparse,zipfile,subprocess,json
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'revision_17_final_2026-11-01'
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--doc-python',required=True);args=parser.parse_args()
    target=OUT/'portable_validation';target.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUT/'MMT_reproducibility_v17.zip') as z:
        assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist());z.extractall(target)
    root=target/'reproducibility_v17'
    for script in ['build_v17.py','audit_v17.py']:
        r=subprocess.run([args.doc_python,'-X','utf8','manuscript/'+script],cwd=root,capture_output=True,text=True,encoding='utf-8')
        (OUT/('portable_'+script+'.log')).write_text(r.stdout+r.stderr,encoding='utf-8');assert r.returncode==0,r.stderr
    names=['MMT_manuscript_Q1_revision_v17_clean.docx','MMT_supplementary_Q1_revision_v17.docx','Highlights_v17.docx','Cover_letter_MMT_v17.docx'];report={}
    for name in names:
        with zipfile.ZipFile(OUT/name) as a,zipfile.ZipFile(root/OUT.name/name) as b:
            parts=[n for n in a.namelist() if n.startswith('word/')];assert set(parts)=={n for n in b.namelist() if n.startswith('word/')}
            assert all(a.read(n)==b.read(n) for n in parts),name
            report[name]={'word_parts_compared':len(parts),'content_identical':True}
    (OUT/'portable_rebuild_QA_v17.json').write_text(json.dumps(report,indent=2));print(report)
if __name__=='__main__':main()
