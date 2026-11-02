"""Native-math, historical-data and document-transcription checks."""
from pathlib import Path
import json,re,hashlib,zipfile
from lxml import etree as E
from docx import Document
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT/'revision_19_2026-11-01';OUT=ROOT/'revision_20_2026-11-01';NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
def xml(p):return E.fromstring(zipfile.ZipFile(p).read('word/document.xml'))
def grid(t):return [[c.text for c in r.cells] for r in t.rows]
def main():
    p=OUT/'MMT_manuscript_Q1_revision_v20_clean.docx';d=Document(p);old=Document(OLD/'MMT_manuscript_Q1_revision_v19_clean.docx')
    math=lambda p:[E.tostring(e,method='c14n') for e in xml(p).findall('.//m:oMath',NS)]
    assert len(math(p))==15 and math(p)==math(OLD/'MMT_manuscript_Q1_revision_v19_clean.docx')
    assert len(d.tables)==len(old.tables)==13
    for n,(a,b) in enumerate(zip(d.tables,old.tables)):
        if a.cell(0,0).text in ['Model / design','Evidence']:continue
        assert grid(a)==grid(b),n
    t=next(t for t in d.tables if t.cell(0,0).text=='Model / design');assert grid(t)[1:]==json.loads((OUT/'table10_expected_v20.json').read_text())
    prior=next(t for t in old.tables if t.cell(0,0).text=='Model / design');assert grid(t)[1:5]==grid(prior)[1:5]
    refs=lambda x:[p.text for p in x.paragraphs if re.match(r'^\[\d+\]',p.text)]
    assert refs(d)==refs(old) and len(refs(d))==48
    text='\n'.join(p.text for p in d.paragraphs);abstract=next(p.text for p in d.paragraphs if p.text.startswith('Inferring gear microgeometry'));assert len(abstract.split())<=180
    credit=lambda x:next(p.text for p in x.paragraphs if p.text.startswith('CRediT authorship'))
    assert credit(d)==credit(old)
    assert [int(re.match(r'^Figure (\d+)',p.text)[1]) for p in d.paragraphs if re.match(r'^Figure \d+',p.text)]==list(range(1,14))
    assert 'violating a sufficient condition does not prove sensitivity' in text
    assert '2.0% empirical false-alarm' in text and 'not an established refinement criterion' in text
    s=Document(OUT/'MMT_supplementary_Q1_revision_v20.docx');so=Document(OLD/'MMT_supplementary_Q1_revision_v19.docx');assert len(s.tables)==39
    for i in range(36):
        if i==28:assert [r[:7] for r in grid(s.tables[i])]==grid(so.tables[i])
        else:assert grid(s.tables[i])==grid(so.tables[i]),i
    assert s.tables[28].cell(9,7).text=='2.0' # deeper IID row after 8 marginal scenarios
    assert [int(re.match(r'^Supplementary Table S(\d+)',p.text)[1]) for p in s.paragraphs if p.text.startswith('Supplementary Table S')]==list(range(1,40))
    assert len(s.tables[36].rows)==17 and len(s.tables[37].rows)==9
    for p in OUT.glob('*.docx'):
        z=zipfile.ZipFile(p);assert z.testzip() is None
        assert not xml(p).findall('.//w:ins',NS) and not xml(p).findall('.//w:del',NS)
        assert not any('comment' in n.lower() for n in z.namelist())
    bullets=[p.text[2:] for p in Document(OUT/'Highlights_v20.docx').paragraphs if p.text.startswith('• ')];assert len(bullets)==5 and all(len(x)<=85 for x in bullets)
    out=dict(native_equations_preserved=15,references_unchanged=48,figures_preserved=13,old_numerical_cells_preserved_except_updated_fine_selection=True,old_supplement_numeric_cells_preserved=True,supplement_tables=39,fine_start_rows=16,local_diagnostic_rows=8,abstract_words=len(abstract.split()),credit_preserved=True,clean_comments_and_revisions=0,docx_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.docx')})
    (OUT/'audit_v20.json').write_text(json.dumps(out,indent=2));print(out)
if __name__=='__main__':main()
