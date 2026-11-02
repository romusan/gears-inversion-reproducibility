"""Check an extracted v16 package without refitting scientific experiments."""
from pathlib import Path
import argparse,zipfile,subprocess,sys,json
from lxml import etree as E
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'revision_16_2026-11-01'
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--doc-python',required=True);args=parser.parse_args()
    target=OUT/'portable_smoke';target.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUT/'MMT_reproducibility_v16.zip') as z:
        assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist());z.extractall(target)
    root=target/'reproducibility_v16'
    result=subprocess.run([sys.executable,'-m','pytest','deposit_v6/gear_inverse_identifiability/tests','-q'],cwd=root,capture_output=True,text=True)
    (OUT/'unit_tests_v16.log').write_text(result.stdout+result.stderr,encoding='utf-8');assert result.returncode==0,result.stderr;print(result.stdout,flush=True)
    result=subprocess.run([args.doc_python,'-X','utf8','manuscript/build_v16.py'],cwd=root,capture_output=True,text=True)
    (OUT/'portable_build_v16.log').write_text(result.stdout+result.stderr,encoding='utf-8');assert result.returncode==0,result.stderr;print(result.stdout,flush=True)
    names=['MMT_manuscript_Q1_revision_v16_clean.docx','MMT_manuscript_Q1_revision_v16_tracked.docx','MMT_supplementary_Q1_revision_v16.docx','Highlights_v16.docx','Cover_letter_MMT_v16.docx']
    report={}
    for name in names:
        with zipfile.ZipFile(OUT/name) as a,zipfile.ZipFile(root/OUT.name/name) as b:
            parts=[n for n in a.namelist() if n.startswith('word/')];assert set(parts)=={n for n in b.namelist() if n.startswith('word/')}
            def normalized(part,data):
                if name.endswith('_tracked.docx') and part=='word/document.xml':
                    xml=E.fromstring(data)
                    for elem in xml.iter():
                        attr='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}date'
                        if attr in elem.attrib:elem.set(attr,'REVISION_TIMESTAMP')
                    return E.tostring(xml,method='c14n')
                return data
            assert all(normalized(n,a.read(n))==normalized(n,b.read(n)) for n in parts),name
            report[name]={'word_parts_compared':len(parts),'content_identical':True,'tracked_revision_timestamps_normalized':name.endswith('_tracked.docx')}
    (OUT/'portable_rebuild_QA_v16.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
