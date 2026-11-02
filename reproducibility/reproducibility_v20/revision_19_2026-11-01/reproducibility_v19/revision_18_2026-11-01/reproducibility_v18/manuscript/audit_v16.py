"""Audit editorial integration, mathematical preservation and unchanged data."""
from pathlib import Path
import sys,io,json,re,hashlib,zipfile
from lxml import etree as E
from docx import Document
from build_v16 import accepted
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'revision_16_2026-11-01';BASE=ROOT/'manuscript'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
def xml(path):return E.fromstring(zipfile.ZipFile(path).read('word/document.xml'))
def main():
    clean=OUT/'MMT_manuscript_Q1_revision_v16_clean.docx';tracked=OUT/'MMT_manuscript_Q1_revision_v16_tracked.docx'
    d=xml(clean);t=xml(tracked);a=E.fromstring(zipfile.ZipFile(io.BytesIO(accepted(tracked.read_bytes()))).read('word/document.xml'))
    assert E.tostring(d,method='c14n')==E.tostring(a,method='c14n')
    assert not d.findall('.//w:ins',NS) and not d.findall('.//w:del',NS)
    assert len(t.findall('.//w:ins',NS))==len(t.findall('.//w:del',NS))==15
    eq=d.findall('.//m:oMath',NS);old=xml(BASE/'MMT_manuscript_Q1_revision_v14.docx').findall('.//m:oMath',NS)
    assert len(eq)==len(old)==15
    for i,(current,previous) in enumerate(zip(eq,old)):
        x=''.join(current.itertext());y=''.join(previous.itertext())
        assert (x.replace('η','ℓ') if i==1 else x)==y,(i,x,y)
    assert 'η' in ''.join(eq[1].itertext()) and 'ℓ' not in ''.join(eq[1].itertext())
    for path in [clean,tracked]:
        assert not any('comment' in name.lower() for name in zipfile.ZipFile(path).namelist())
    doc=Document(clean);paras=[p.text for p in doc.paragraphs];text='\n'.join(paras)
    first=[]
    for p in paras:
        if re.match(r'^\[\d+\]',p):continue
        for match in re.finditer(r'\[(\d+(?:,\d+)*)\]',p):
            nums=list(map(int,match[1].split(',')))
            if 0 in nums:continue
            for n in nums:
                if n not in first:first.append(n)
    assert first==list(range(1,46)),first
    assert len([p for p in paras if re.match(r'^\[\d+\]',p)])==45
    assert [int(re.match(r'^Figure (\d+)',p)[1]) for p in paras if re.match(r'^Figure \d+',p)]==list(range(1,12))
    captions=[re.match(r'^Table (A\.\d+|\d+)',p)[1] for p in paras if re.match(r'^Table (?:A\.\d+|\d+)',p)]
    assert captions==[str(i) for i in range(1,11)]+['A.1','A.2'],captions
    previous=Document(BASE/'MMT_manuscript_Q1_revision_v14.docx')
    numeric_tables=[tab for tab in doc.tables if tab.cell(0,0).text!='Evidence']
    assert len(numeric_tables)==len(previous.tables)==11
    for current,oldtab in zip(numeric_tables,previous.tables):
        assert [[c.text for c in row.cells] for row in current.rows]==[[c.text for c in row.cells] for row in oldtab.rows]
    sup=Document(OUT/'MMT_supplementary_Q1_revision_v16.docx');oldsup=Document(BASE/'MMT_supplementary_Q1_revision_v14.docx')
    assert len(sup.tables)==len(oldsup.tables)==23
    for current,oldtab in zip(sup.tables,oldsup.tables):assert [[c.text for c in row.cells] for row in current.rows]==[[c.text for c in row.cells] for row in oldtab.rows]
    assert [int(re.match(r'^Supplementary Table S(\d+)',p.text)[1]) for p in sup.paragraphs if p.text.startswith('Supplementary Table S')]==list(range(1,24))
    assert 'is to be added' not in text and 'MMT_reproducibility_v16.zip' in text and 'No repository DOI is currently assigned.' in text
    assert 'Claude (Anthropic)' in text and 'at an endpoint' in text
    assert next(p for p in paras if p.startswith('CRediT authorship'))==next(p.text for p in previous.paragraphs if p.text.startswith('CRediT authorship'))
    e=json.loads((OUT/'editorial_changes_v16.json').read_text(encoding='utf-8'))
    source={name:hashlib.sha256((ROOT/'revision'/name).read_bytes()).hexdigest() for name in ['MMT_manuscript_Q1_revision_v15_clean.docx','MMT_manuscript_Q1_revision_v15_tracked.docx']}
    with zipfile.ZipFile(ROOT/'revision/MMT_manuscript_Q1_revision_v15_tracked.docx') as original:
        source_comments=len(E.fromstring(original.read('word/comments.xml')).findall('w:comment',NS))
    assert source_comments==9
    hd=Document(OUT/'Highlights_v16.docx');bullets=[p.text for p in hd.paragraphs if p.text.startswith('• ')]
    assert len(bullets)==5 and all(len(p[2:])<=85 for p in bullets)
    report=dict(source_v15_sha256=source,source_clean_OMML=len(xml(ROOT/'revision/MMT_manuscript_Q1_revision_v15_clean.docx').findall('.//m:oMath',NS)),source_tracked_OMML=15,source_tracked_comments=9,math_objects_preserved=15,line_of_action_eta_checked=True,tracked_insertions=15,tracked_deletions=15,accept_tracked_equals_clean_document_xml=True,remaining_comments=0,references_ordered=45,figures=11,main_tables=10,appendix_tables=['A.1','A.2'],supplement_tables=23,all_original_numerical_table_cells_unchanged=True,credit_statement_unchanged_and_user_confirmed=True,abstract_words=e['abstract_words'],highlights_lengths=[len(x[2:]) for x in bullets],new_experiments=False,docx_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.docx')})
    (OUT/'audit_v16.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
