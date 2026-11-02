"""Integrity and transcription audit of the response to the v17 review."""
from pathlib import Path
import json,re,zipfile,hashlib
from lxml import etree as E
from docx import Document
ROOT=Path(__file__).resolve().parent.parent;OLD=ROOT/'revision_17_final_2026-11-01';OUT=ROOT/'revision_18_2026-11-01'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
def xml(p):return E.fromstring(zipfile.ZipFile(p).read('word/document.xml'))
def values(t):return [[c.text for c in r.cells] for r in t.rows]
def main():
    from build_v18 import f,LABEL
    a=json.loads((OUT/'analysis_v18.json').read_text());mainfile=OUT/'MMT_manuscript_Q1_revision_v18_clean.docx';d=Document(mainfile);old=Document(OLD/'MMT_manuscript_Q1_revision_v17_clean.docx')
    assert [E.tostring(x,method='c14n') for x in xml(mainfile).findall('.//m:oMath',NS)]==[E.tostring(x,method='c14n') for x in xml(OLD/'MMT_manuscript_Q1_revision_v17_clean.docx').findall('.//m:oMath',NS)]
    assert len(xml(mainfile).findall('.//m:oMath',NS))==15
    assert len(d.tables)==len(old.tables) and all(values(x)==values(y) for x,y in zip(d.tables,old.tables))
    pars=[p.text for p in d.paragraphs];text='\n'.join(pars)
    refs=lambda dd:[p.text for p in dd.paragraphs if re.match(r'^\[\d+\]',p.text)]
    assert refs(d)==refs(old) and len(refs(d))==45
    assert [int(re.match(r'^Figure (\d+)',p)[1]) for p in pars if re.match(r'^Figure \d+',p)]==list(range(1,13))
    assert sum(p.startswith('4.8 ') for p in pars)==1
    assert next(p for p in pars if p.startswith('CRediT authorship'))==next(p.text for p in old.paragraphs if p.text.startswith('CRediT authorship'))
    s=Document(OUT/'MMT_supplementary_Q1_revision_v18.docx');oldS=Document(OLD/'MMT_supplementary_Q1_revision_v17.docx')
    assert len(s.tables)==32 and all(values(x)==values(y) for x,y in zip(s.tables[:27],oldS.tables))
    assert [int(re.match(r'^Supplementary Table S(\d+)',p.text)[1]) for p in s.paragraphs if p.text.startswith('Supplementary Table S')]==list(range(1,33))
    expected=[[str(c['sd']),LABEL[c['scenario']],str(c['n'])]+[f(c[k]) for k in ['dedendum_error','profile_um','heldout_nominal_um','heldout_generator_um']]+[str(c['failed'])] for c in a['cells']]
    assert values(s.tables[27])[1:]==expected
    expected=[[str(c['sd']),LABEL[c['scenario']],str(c['n']),f(c['window_bias_um']),f(c['residual_um']),f(c['Q_per_n']),str(c['score_flags']) if c['score_flags'] is not None else '—'] for c in a['cells']]
    assert values(s.tables[28])[1:]==expected
    gain=next(b for b in a['bootstrap'] if b['sd']==.4 and b['A']=='gain5_iid_fit' and b['n']==200)['metrics']['dedendum_error']
    abstract=next(p for p in pars if p.startswith('Inferring gear microgeometry'));assert len(abstract.split())<=250
    assert all(f(gain[k]) in abstract for k in ['median_A','median_B','lower','upper'])
    assert 'MMT_reproducibility_v18.zip' in text and '3300 final fitting attempts' in text and '300 covariance-pilot attempts' in text
    assert 'No repository DOI is currently assigned.' in text
    for p in OUT.glob('*.docx'):
        z=zipfile.ZipFile(p);xx=xml(p);assert z.testzip() is None
        assert not any('comment' in n.lower() for n in z.namelist())
        assert not xx.findall('.//w:ins',NS) and not xx.findall('.//w:del',NS)
    assert len([p for p in Document(OUT/'Highlights_v18.docx').paragraphs if p.text.startswith('• ') and len(p.text[2:])<=85])==5
    report=dict(equations_preserved=15,references_unchanged=45,figures=12,main_table_cells_unchanged=True,old_supplement_table_cells_unchanged=True,supplement_tables=32,new_summary_tables_match_analysis=True,gain_bootstrap_transcribed_in_abstract=True,abstract_words=len(abstract.split()),clean_comments_and_revisions=0,credit_confirmation_retained=True,docx_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.docx')})
    (OUT/'audit_v18.json').write_text(json.dumps(report,indent=2));print(report)
if __name__=='__main__':main()
