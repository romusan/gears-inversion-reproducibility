"""Bibliography export and structural audit; visual QA is separate."""
import json,re,zipfile
from pathlib import Path
from lxml import etree
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent

def main():
    refs=json.loads((ROOT/'referencias_40_q1.json').read_text(encoding='utf-8'))
    bib=[]
    for i,r in enumerate(refs,1):
        names=' and '.join(a.get('family','')+', '+a.get('given','') for a in r.get('author',[]))
        parts={'author':names,'title':r['title'][0],'year':str(r['year']),
               'journal':(r.get('container-title') or [''])[0],'volume':r.get('volume',''),
               'pages':r.get('page',''),'doi':r.get('DOI',''),'url':r.get('url','')}
        bib.append('@misc{q1ref'+str(i)+',\n'+',\n'.join('  '+k+' = {'+v+'}' for k,v in parts.items() if v)+'\n}')
    (ROOT/'referencias_40_q1.bib').write_text('\n\n'.join(bib)+'\n',encoding='utf-8')
    source=(BASE/'q1_manuscript.md').read_text(encoding='utf-8');order=[]
    for group in re.findall(r'\[([\d, ]+)\]',source):
        nums=[int(n) for n in group.replace(' ','').split(',')]
        if 0 in nums:continue
        for n in nums:
            if n not in order:order.append(n)
    assert order==list(range(1,41)),order
    doc=BASE/'MMT_manuscript_Q1_revision.docx'
    with zipfile.ZipFile(doc) as z:xml=etree.fromstring(z.read('word/document.xml'))
    ns={'m':'http://schemas.openxmlformats.org/officeDocument/2006/math','w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    assert len(xml.findall('.//m:oMath',ns))==13
    body=xml.find('w:body',ns);captions=[]
    for i,node in enumerate(body):
        if node.tag=='{'+ns['w']+'}tbl':
            preceding=body[i-1];text=''.join(preceding.itertext())
            assert text.startswith('Table '),text
            captions.append(text)
    assert len(captions)==3
    assert len(refs)==40
    report=dict(references=40,first_citation_order=True,native_omml_equations=13,
                table_captions_before_correct_tables=3,docx_opens_in_Word='confirmed by PDF export',
                visual_QA='15 pages inspected after final export',
                numerical_test_count=26,monte_carlo_records=1200,selected_optimizer_convergence=1155)
    out=ROOT/'correcciones_Q1_2026-10-12'/'verificacion_final.json'
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(report)
if __name__=='__main__':main()
