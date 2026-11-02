"""Audit final document integrity and saved-data transcription."""
from pathlib import Path
import json,re,zipfile,hashlib
from lxml import etree as E
from docx import Document
ROOT=Path(__file__).resolve().parent.parent;OLD=ROOT/'revision_16_2026-11-01';OUT=ROOT/'revision_17_final_2026-11-01'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
def xml(p):return E.fromstring(zipfile.ZipFile(p).read('word/document.xml'))
def values(t):return [[c.text for c in r.cells] for r in t.rows]
def main():
    mainfile=OUT/'MMT_manuscript_Q1_revision_v17_clean.docx';d=Document(mainfile);previous=Document(OLD/'MMT_manuscript_Q1_revision_v16_clean.docx')
    x=xml(mainfile);old=xml(OLD/'MMT_manuscript_Q1_revision_v16_clean.docx')
    assert len(x.findall('.//m:oMath',NS))==15
    assert [E.tostring(e,method='c14n') for e in x.findall('.//m:oMath',NS)]==[E.tostring(e,method='c14n') for e in old.findall('.//m:oMath',NS)]
    assert len(d.tables)==len(previous.tables)
    assert all(values(a)==values(b) for a,b in zip(d.tables,previous.tables))
    paras=[p.text for p in d.paragraphs];text='\n'.join(paras)
    assert [int(re.match(r'^Figure (\d+)',p)[1]) for p in paras if re.match(r'^Figure \d+',p)]==list(range(1,13))
    assert len([p for p in paras if re.match(r'^\[\d+\]',p)])==45
    assert [p for p in paras if re.match(r'^\[\d+\]',p)]==[p.text for p in previous.paragraphs if re.match(r'^\[\d+\]',p.text)]
    assert next(p for p in paras if p.startswith('CRediT authorship'))==next(p.text for p in previous.paragraphs if p.text.startswith('CRediT authorship'))
    s=Document(OUT/'MMT_supplementary_Q1_revision_v17.docx');sp=Document(OLD/'MMT_supplementary_Q1_revision_v16.docx')
    assert len(s.tables)==27 and all(values(a)==values(b) for a,b in zip(s.tables[:23],sp.tables))
    assert [int(re.match(r'^Supplementary Table S(\d+)',p.text)[1]) for p in s.paragraphs if p.text.startswith('Supplementary Table S')]==list(range(1,28))
    summary=json.loads((OUT/'stress_summary.json').read_text())
    from build_v17 import median,f,LABEL
    expected=[[str(c['sd_true']),LABEL[c['scenario']],median(c['strata']['all']),median(c['strata']['all'],'profile'),median(c['strata']['all'],'fit'),f(c['discrepancy_rms_um']),str(c['failed'])] for c in summary['cells']]
    assert values(s.tables[23])[1:]==expected
    assert str(summary['failed_selected'])+' report nonconvergence' in text
    assert str(summary['failed_attempts'])+' of the 1500 attempts' in text
    abstract=next(p for p in paras if p.startswith('Inferring gear microgeometry'));assert len(abstract.split())<=250
    assert 'MMT_reproducibility_v17.zip' in text and 'No repository DOI is currently assigned.' in text
    for p in OUT.glob('*.docx'):
        z=zipfile.ZipFile(p);xx=xml(p);assert z.testzip() is None
        assert not any('comment' in n.lower() for n in z.namelist())
        assert not xx.findall('.//w:ins',NS) and not xx.findall('.//w:del',NS)
    tracked=xml(OLD/'MMT_manuscript_Q1_revision_v16_tracked.docx')
    assert len(tracked.findall('.//w:ins',NS))==15 and len(tracked.findall('.//w:del',NS))==15
    lengths=[len(p.text[2:]) for p in Document(OUT/'Highlights_v17.docx').paragraphs if p.text.startswith('• ')];assert len(lengths)==5 and max(lengths)<=85
    report=dict(equations_preserved_exactly=15,all_existing_main_table_cells_unchanged=True,all_existing_supplement_table_cells_unchanged=True,references_preserved=45,figures=12,supplement_tables=27,abstract_words=len(abstract.split()),highlights_lengths=lengths,new_summary_table_matches_records=True,clean_comments_and_revisions=0,credit_user_confirmation_retained=True,historical_v16_tracked_insertions=15,historical_v16_tracked_deletions=15,docx_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.docx')})
    (OUT/'audit_v17.json').write_text(json.dumps(report,indent=2));print(report)
if __name__=='__main__':main()
