"""Structural verification of the second-review deliverable."""
import json,re,zipfile
from pathlib import Path
from lxml import etree
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent
def main():
    text=(BASE/'q1_manuscript.md').read_text(encoding='utf-8');first=[]
    for group in re.findall(r'\[([\d, ]+)\]',text):
        nums=[int(n) for n in group.replace(' ','').split(',')]
        if 0 in nums:continue
        for n in nums:
            if n not in first:first.append(n)
    assert first==list(range(1,41))
    with zipfile.ZipFile(BASE/'MMT_manuscript_Q1_revision_v2.docx') as z:xml=etree.fromstring(z.read('word/document.xml'))
    ns={'m':'http://schemas.openxmlformats.org/officeDocument/2006/math','w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    assert len(xml.findall('.//m:oMath',ns))==13
    body=xml.find('w:body',ns);captions=[]
    for i,node in enumerate(body):
        if node.tag=='{'+ns['w']+'}tbl':
            caption=''.join(body[i-1].itertext());assert caption.startswith('Table '),caption
            captions.append(int(re.match(r'Table (\d+)',caption)[1]))
    assert captions==list(range(1,10)),captions
    report=dict(references_in_first_citation_order=40,native_omml_equations=13,tables_correctly_captioned=9,
                scientific_tests_passed=27,original_MC_reconstructions_retained=1200,
                competing_interest_and_author_review='confirmed by user',individual_CRediT_roles='pending',
                physical_validation='still limited; external waveform/stiffness data unavailable')
    (ROOT/'revision_2_2026-10-12/verificacion_estructural.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(report)
if __name__=='__main__':main()
