"""Finalize first-appearance citations, bibliography and submission documents."""
import json,re
from pathlib import Path
from docx import Document
from docx.shared import Pt,RGBColor,Cm
from build_corrected_manuscript import paragraph
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent;OUT=ROOT/'revision_14_2026-11-01'
def final_bibliography(doc):
    refs=json.loads((ROOT/'referencias_45_v14.json').read_text(encoding='utf-8'))
    source=(BASE/'q1_manuscript_v14.md').read_text(encoding='utf-8')
    data=next(b.strip() for b in source.split('\n\n') if b.startswith('Data availability.'))
    for p in doc.paragraphs:
        if p.text.startswith('Data availability.'):
            # Filename underscores are literal characters, not mathematical subscripts.
            p.text=data
    order=[];pattern=re.compile(r'\[(\d+(?:,\s*\d+)*)\]')
    for p in doc.paragraphs:
        if re.match(r'^\[\d+\]',p.text):continue
        for m in pattern.finditer(p.text):
            nums=[int(x) for x in m[1].split(',')]
            if 0 in nums:continue
            for n in nums:
                if n not in order:order.append(n)
    assert set(order)==set(range(1,46)),order
    mapping={old:new for new,old in enumerate(order,1)}
    (OUT/'reference_first_appearance_mapping.json').write_text(json.dumps(mapping,indent=2),encoding='utf-8')
    def name(a):
        initials=''.join(x[0]+'.' for x in re.findall(r'[^\W\d_]+',a.get('given',''),flags=re.UNICODE))
        return (initials+' '+a.get('family','')).strip()
    refparas=[p for p in doc.paragraphs if re.match(r'^\[\d+\]',p.text)]
    assert len(refparas)==45
    for new,p in enumerate(refparas,1):
        r=refs[order[new-1]-1]
        authors=', '.join(name(a) for a in r.get('author',[])[:6])
        if len(r.get('author',[]))>6:authors+=', et al.'
        title=r['title'][0].rstrip('.');journal=(r.get('container-title') or [''])[0]
        year=r.get('year') or r['published']['date-parts'][0][0]
        if r.get('type') in ['book','monograph']:body=f"{authors}, {title}, {r.get('publisher','')}, {year}."
        elif r.get('type')=='standard':body=f"{authors}, {title}, ISO, Geneva, {year}."
        else:body=f"{authors}, {title}, {journal} {r.get('volume','')} ({year}) {r.get('page') or r.get('article-number') or ''}."
        link='https://doi.org/'+r['DOI'] if r.get('DOI') else r.get('url','')
        if r.get('language')=='zh':body+=' (In Chinese; English title supplied.)'
        p.text=f'[{new}] {body} {link}'
        for run in p.runs:run.font.size=Pt(10)
    def replace(m):
        nums=[int(x) for x in m[1].split(',')]
        if 0 in nums:return m[0]
        return '['+','.join(str(mapping[x]) for x in nums)+']'
    for p in doc.paragraphs:
        if re.match(r'^\[\d+\]',p.text):continue
        for run in p.runs:
            updated=pattern.sub(replace,run.text)
            if updated!=run.text:run.text=updated
    (OUT/'references_ordered_v14.json').write_text(json.dumps([refs[x-1] for x in order],ensure_ascii=False,indent=2),encoding='utf-8')
def basic():
    doc=Document();s=doc.sections[0];s.top_margin=s.bottom_margin=Cm(2.3)
    for name in ['Normal','Title']:
        doc.styles[name].font.name='Times New Roman';doc.styles[name].font.color.rgb=RGBColor(0,0,0)
    doc.styles['Normal'].font.size=Pt(11);doc.styles['Normal'].paragraph_format.space_after=Pt(9)
    doc.styles['Title'].font.size=Pt(16)
    doc.styles['Title'].font.bold=True
    for border in list(doc.styles.element.xpath('.//w:pBdr')):border.getparent().remove(border)
    for fonts in doc.styles.element.xpath('.//w:rFonts'):
        for key in list(fonts.attrib):
            if key.endswith('Theme'):del fonts.attrib[key]
    return doc
def clean_title(doc):
    for border in list(doc.element.xpath('.//w:pBdr')):border.getparent().remove(border)
    for p in doc.paragraphs:
        if p.style.name=='Title':
            for run in p.runs:run.font.name='Times New Roman';run.font.color.rgb=RGBColor(0,0,0);run.font.underline=False
def write_highlights():
    doc=basic();paragraph(doc,'Highlights','Title')
    bullets=[x[2:] for x in (BASE/'highlights_v14.txt').read_text(encoding='utf-8').splitlines() if x.startswith('• ')]
    assert len(bullets)==5 and all(len(x)<=85 for x in bullets)
    for text in bullets:paragraph(doc,'• '+text)
    clean_title(doc);doc.save(BASE/'Highlights_v14.docx')
def write_cover_letter():
    doc=basic();paragraph(doc,'Submission to Mechanism and Machine Theory','Title')
    paragraph(doc,'1 November 2026')
    paragraph(doc,'Dear Editor,')
    paragraph(doc,'Please consider our manuscript, “Contact support and practical identifiability of spur gear microgeometry from transmission error”, by Romulo Sandoval Flórez, Claudia Patricia Parra Medina and German Leandro Vargas Fonseca, for publication as a research article in Mechanism and Machine Theory.')
    paragraph(doc,'The manuscript addresses a practical question in inverse gear analysis: which profile modifications can be determined from mean-removed quasistatic transmission error? A sufficient loaded-support condition defines exactly invariant relief sets for fixed geometry and compliance. A coupled-contact argument, implicit tangent, nonlinear profiles and numerical controls connect this condition to weak practical identifiability. The contribution is an observability diagnostic before inversion, with explicit distinctions from inverse tooth-contact synthesis and forward profile optimization.')
    paragraph(doc,'The evidence includes noise experiments, fixed-budget angular and load controls, finite-element comparisons and 32 new same-operator restricted-distance cases with 192 bounded fits. These controls assess whether a dedendum response can be explained by refitting the addendum alone and whether the result persists across four compliance formulations. They distinguish a response effect from evidence for geometrical recovery.')
    paragraph(doc,'The manuscript explicitly reports its negative validation findings. The analytical formulations do not meet the adopted external amplitude target; the retained cross-operator FE observations do not identify the dedendum; full-cycle physical inverse convergence is not established. These limits are part of the scientific result and are not presented as resolved by the internal controls. We believe the combination of contact mechanics and inverse stability is relevant to the journal’s readership working on gear modelling, transmission error and microgeometry.')
    paragraph(doc,'The submission is accompanied by a supplementary document, Highlights and a reproducibility archive containing the current sources, numerical records and integrity manifest. The preceding version-13 baseline is publicly accessible; the new version-14 records are included in the accompanying archive. Funding, competing-interest, author-contribution and AI-assistance statements are included in the manuscript.')
    paragraph(doc,'Sincerely,')
    paragraph(doc,'Romulo Sandoval Flórez\nCorresponding author\nUniversidad ECCI\nromulo@ecci.edu.co')
    clean_title(doc);doc.save(BASE/'Cover_letter_MMT_v14.docx')
