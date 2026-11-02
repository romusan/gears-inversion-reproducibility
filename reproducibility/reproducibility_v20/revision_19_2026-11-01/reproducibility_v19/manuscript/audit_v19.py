"""Document integrity and exact transcription checks for the final v19."""
from pathlib import Path
import re,json,hashlib,zipfile
from lxml import etree as E
from docx import Document
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT/'revision_18_2026-11-01';OUT=ROOT/'revision_19_2026-11-01'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
def xml(p):return E.fromstring(zipfile.ZipFile(p).read('word/document.xml'))
def grid(t):return [[c.text for c in r.cells] for r in t.rows]
def main():
    mainpath=OUT/'MMT_manuscript_Q1_revision_v19_clean.docx';d=Document(mainpath);old=Document(OLD/'MMT_manuscript_Q1_revision_v18_clean.docx')
    canonical=lambda p:[E.tostring(x,method='c14n') for x in xml(p).findall('.//m:oMath',NS)]
    assert canonical(mainpath)==canonical(OLD/'MMT_manuscript_Q1_revision_v18_clean.docx') and len(canonical(mainpath))==15
    assert len(d.tables)==len(old.tables)+1
    assert all(any(grid(t)==grid(s) for t in d.tables) for s in old.tables if s.cell(0,0).text!='Evidence')
    old_evidence=next(t for t in old.tables if t.cell(0,0).text=='Evidence');new_evidence=next(t for t in d.tables if t.cell(0,0).text=='Evidence')
    assert grid(new_evidence)[:len(old_evidence.rows)]==grid(old_evidence) and len(new_evidence.rows)==len(old_evidence.rows)+2
    assert grid(next(t for t in d.tables if t.cell(0,0).text=='Model / design'))[1:]==json.loads((OUT/'table10_expected.json').read_text())
    refs=lambda doc:[p.text for p in doc.paragraphs if re.match(r'^\[\d+\]',p.text)]
    r,ro=refs(d),refs(old);assert len(r)==48 and all(r[i]==ro[i] for i in range(45) if i!=7)
    pars=[p.text for p in d.paragraphs];assert [int(re.match(r'^Figure (\d+)',p)[1]) for p in pars if re.match(r'^Figure \d+',p)]==list(range(1,14))
    assert sum(p.startswith('4.9 ') for p in pars)==1
    credit=lambda doc:next(p.text for p in doc.paragraphs if p.text.startswith('CRediT authorship'))
    assert credit(d)==credit(old)
    abstract=next(p for p in pars if p.startswith('Inferring gear microgeometry'));assert len(abstract.split())<=180
    assert 'MMT_reproducibility_v19.zip' in '\n'.join(pars)
    s=Document(OUT/'MMT_supplementary_Q1_revision_v19.docx');so=Document(OLD/'MMT_supplementary_Q1_revision_v18.docx');assert len(s.tables)==36
    assert all(grid(s.tables[i])==grid(so.tables[i]) for i in range(32) if i!=26)
    assert [int(re.match(r'^Supplementary Table S(\d+)',p.text)[1]) for p in s.paragraphs if p.text.startswith('Supplementary Table S')]==list(range(1,37))
    for p in OUT.glob('*.docx'):
        z=zipfile.ZipFile(p);assert z.testzip() is None;root=xml(p)
        assert not root.findall('.//w:ins',NS) and not root.findall('.//w:del',NS)
        assert not any('comment' in n.lower() for n in z.namelist())
    highlights=[p.text[2:] for p in Document(OUT/'Highlights_v19.docx').paragraphs if p.text.startswith('• ')]
    assert len(highlights)==5 and all(len(p)<=85 for p in highlights)
    report=dict(native_equations_preserved=15,old_numerical_main_tables_preserved=True,old_numerical_supplement_tables_preserved=True,figures=13,references=48,credit_confirmation_preserved=True,abstract_words=len(abstract.split()),supplement_tables=36,clean_comments_and_revisions=0,highlights_lengths=list(map(len,highlights)),docx_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.docx')})
    (OUT/'audit_v19.json').write_text(json.dumps(report,indent=2));print(report)
if __name__=='__main__':main()
