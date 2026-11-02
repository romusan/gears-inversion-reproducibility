"""Integrate the supplied v15 review while preserving all original OMML.

No numerical experiment is executed. Original v15 files remain unchanged.
The tracked v16 shows only the corrections relative to accepted v15.
"""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import io,json,re,zipfile,hashlib
from lxml import etree as E
from docx import Document
from docx.shared import Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parent.parent;BASE=ROOT/'manuscript';OUT=ROOT/'revision_16_2026-11-01'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
W='{'+NS['w']+'}'

def rewrite_zip(data,replacements,remove=()):
    output=io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(data)) as src,zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as dst:
        for name in src.namelist():
            if name not in remove:dst.writestr(name,replacements.get(name,src.read(name)))
    return output.getvalue()

def accepted(data):
    z=zipfile.ZipFile(io.BytesIO(data));d=E.fromstring(z.read('word/document.xml'))
    assert not d.findall('.//w:pPr/w:rPr/w:del',NS),'Paragraph merge revisions require explicit handling'
    for x in list(d.findall('.//w:del',NS))+list(d.findall('.//w:moveFrom',NS)):x.getparent().remove(x)
    for tag in ['ins','moveTo']:
        for x in list(d.findall('.//w:'+tag,NS)):
            parent=x.getparent();index=parent.index(x)
            for child in list(x):parent.insert(index,child);index+=1
            parent.remove(x)
    for tag in ['pPrChange','rPrChange','tblPrChange','tcPrChange','trPrChange','commentRangeStart','commentRangeEnd','commentReference']:
        for x in list(d.findall('.//w:'+tag,NS)):x.getparent().remove(x)
    changes={'word/document.xml':E.tostring(d,xml_declaration=True,encoding='UTF-8',standalone=True)}
    remove=[name for name in z.namelist() if 'comment' in name.lower()]
    for name in ['word/_rels/document.xml.rels','[Content_Types].xml']:
        part=E.fromstring(z.read(name))
        for x in list(part):
            if any('comment' in value.lower() for value in x.attrib.values()):part.remove(x)
        changes[name]=E.tostring(part,xml_declaration=True,encoding='UTF-8',standalone=True)
    settings=E.fromstring(z.read('word/settings.xml'))
    for x in list(settings.findall('.//w:trackRevisions',NS)):x.getparent().remove(x)
    changes['word/settings.xml']=E.tostring(settings,xml_declaration=True,encoding='UTF-8',standalone=True)
    return rewrite_zip(data,changes,remove)

def layout(doc):
    # Float the tall resolution figure within its own subsection to avoid a
    # mostly empty preceding page; data, image scale and caption are unchanged.
    caption=next(p for p in doc.paragraphs if p.text.startswith('Figure 10 '))
    anchor=next(p for p in doc.paragraphs if p.text.startswith('The remaining null direction'))
    picture=caption._p.getprevious();assert picture.xpath('.//w:drawing')
    anchor._p.addprevious(picture);anchor._p.addprevious(caption._p)

def main():
    OUT.mkdir(exist_ok=True);sources=OUT/'editorial_sources';sources.mkdir(exist_ok=True)
    seed=sources/'v15_accepted_OMML.docx'
    if not seed.exists():seed.write_bytes(accepted((ROOT/'revision/MMT_manuscript_Q1_revision_v15_tracked.docx').read_bytes()))
    doc=Document(seed);layout(doc);edits=[]
    def settext(p,text,reason):
        previous=p.text
        size=Pt(8.5) if p._p.getparent().tag==qn('w:tc') else Pt(11)
        for plain,styled in [('Cd','C_d'),('Ca','C_a'),('sd','s_d'),('sa','s_a'),('smax','s_max')]:
            text=re.sub(r'\b'+plain+r'\b',styled,text)
        for child in list(p._p):
            if child.tag!=qn('w:pPr'):p._p.remove(child)
        # Preserve literal filename/URL underscores; format only mathematical indices.
        pattern=re.compile(r'\b(C|s|p|g|r|η|ξ|w|λ)_([A-Za-z0-9]+)')
        offset=0
        for match in pattern.finditer(text):
            run=p.add_run(text[offset:match.start()]+match[1]);run.font.name='Times New Roman';run.font.size=size
            run=p.add_run(match[2]);run.font.name='Times New Roman';run.font.size=size;run.font.subscript=True
            offset=match.end()
        run=p.add_run(text[offset:]);run.font.name='Times New Roman';run.font.size=size
        edits.append(dict(before=previous,after=text,reason=reason))
    def patch(prefix,text,reason):
        matches=[p for p in doc.paragraphs if p.text.startswith(prefix)];assert len(matches)==1,(prefix,len(matches))
        settext(matches[0],text,reason)
    abstract=('Inferring gear microgeometry from transmission error requires distinguishing contact sensitivity from geometrical recovery. For a quasistatic operator with fixed geometry and compliance, we prove that nonnegative dedendum relief outside loaded support is exactly invisible, and extend the result to coupled linear elastic contact. An implicit contact tangent connects invariance with local sensitivities and the resolution of a discretized relief field. Profile likelihood and Monte Carlo experiments separate exact invariance from weak practical identifiability: for the nominal pair, median scaled dedendum error falls from 0.394 to 0.106 when the relief start moves deeper into contact, using 100 realizations, 120 observations, 300 Nm and 0.1 µm Gaussian noise. Equal-budget controls reveal angular-sampling effects and no statistically resolved benefit of the tested two-load allocation. Same-operator restricted fits across four compliance formulations preserve the distinction between marginal and deeper support. A finite-element contact comparison isolates a dedendum response of 0.179 µm RMS, close to the analytical 0.197 µm, yet an addendum-only inverse attains the same residual and dedendum profiles remain flat. An eight-phase material-removal control gives 0.4–2.1 nm centred changes outside contact, delimiting exact invariance to fixed compliance. None of four formulations meets the adopted 5% research target on twelve external amplitude references. These results yield a pre-inversion support diagnostic and operator-conditioned limits on observability without establishing physical profile recovery.')
    assert len(abstract.split())<=250
    patch('Transmission error is widely used',abstract,'Avoid universal physical invisibility and retain the v14 robustness control in the abstract.')
    patch('Coupling between the wheel body','Coupling between the wheel body and adjacent loaded teeth is an established mechanism in transmission-error prediction, including three-dimensional finite-element treatments [19]. Xue and Li [20] also derive load-sharing and transmission-error relations under profile and machining errors in Section 2.1 of their Chinese-language study, Eqs. (1)–(3), before analysing temperature fields. More recent direct parameter studies examine how modification settings influence transmission error [21]. These precedents motivate a precise distinction: a forward influence or a synthesis for a prescribed response does not establish which unknown relief coordinates can be inferred from a centred measured response. Our coupled-contact result concerns invariance under fixed compliance, rather than a new physical coupling model.','Reference 20 verified against the full text, page 1764; the thermal title does not invalidate its mechanical sections.')
    p=next(p for p in doc.paragraphs if p.text.startswith('Proposition 1 ('))
    text=p.text.replace('for every Cd≥0 and every sd≤smax','for every admissible C_d≥0 and 0<s_d≤s_max')
    assert text!=p.text
    settext(p,text,'Restrict the start to its admissible positive domain so the relief law remains defined.')
    p=next(p for p in doc.paragraphs if p.text.startswith('Proposition 1 is sufficient'))
    base=p.text.split(' Throughout,')[0]
    settext(p,base+' In the nominal geometry and declared sampling designs, we call the s_d=0.25 case marginal and the s_d=0.40 case deeper: the former has limited loaded-support overlap and the latter has more. These labels describe the tested cases, not universal thresholds in s_d.','Make marginal/deeper labels specific to the tested geometry and sampling.')
    patch('Proposition 2 (','Proposition 2 (fixed coupled linear compliance). Consider the frictionless, load-controlled contact system w=Hp+g−δ1≥0, p≥0, pᵀw=0 and 1ᵀp=F>0, with a fixed symmetric positive-definite H, fixed stations and normals. If Δg≥0 and Δg_i=0 wherever the original solution has p_i>0, the forces p and approach δ are unchanged. In particular, the support condition of Proposition 1 implies this gap condition. Proof. The force-constrained contact solution uniquely minimizes the strictly convex potential below.','The quadratic-potential proof applies to linear coupled contact, not automatically to an additional nonlinear Hertz law.')
    patch('Pre-inversion diagnostic.','Diagnostic workflow. A support screen precedes inversion; sensitivity analysis, restricted fits and reporting then complete the assessment. (1) Solve the zero-dedendum contact problem on the intended load and phase grid and compare the loaded-support minimum with the admissible relief starts; a region satisfying Proposition 1 defines an invariant parameter set for those observations. (2) Where support overlaps relief, inspect the scaled tangent and nonlinear profiles rather than equating nonzero rank with usable precision. (3) Compare unrestricted and addendum-only fits. (4) Report the complete reconstructed profile and conditional uncertainty; where a generating or independently measured profile is available, also report parameter and profile errors. These steps concern the same declared mechanical operator and retained observations. Physical interpretation requires an independent fidelity check.','Separate the pre-inversion screen from subsequent fits; errors require an available independent truth.')
    p=next(p for p in doc.paragraphs if p.text.startswith('Research question and contributions.'))
    text=p.text.replace('that can be applied before any microgeometry inversion.','for the declared contact model and intended observations.')
    assert text!=p.text;settext(p,text,'Avoid presenting a sufficient support check as a universal diagnostic for every inverse gear model.')
    cross=json.loads((ROOT/'deposit_v6/results/independent_validation/03_cross_inverse.json').read_text())
    truths={r['case']:r['truth'] for r in cross['rows']};assert truths=={'addendum':[.02,.75,0.,.5],'dedendum':[.02,.75,.005,.3],'dedendum-deep':[.02,.75,.005,.45]}
    patch('Table 9 Analytical inversion','Table 9 Analytical inversion of the 57/57 interior FE observations at 650 Nm. Generating pinion θ=(Cₐ,sₐ,C_d,s_d) is (0.020,0.75,0,0.50) for addendum, (0.020,0.75,0.005,0.30) for dedendum and (0.020,0.75,0.005,0.45) for dedendum-deep; the wheel is unmodified. Depths are mm; residual and predicted versus FE sampled range are µm. The fitted dedendum coordinates retain their initial values because the retained observations have no dedendum signal.','Recover all three generating cases directly from archived 57/57 records.')
    records=json.loads((ROOT/'revision_14_2026-11-01/restricted_distance_records.json').read_text());starts=[a['start'] for a in records[0]['attempts']]
    assert all([a['start'] for a in r['attempts']]==starts for r in records)
    prefix='A further same-operator experiment'
    p=next(p for p in doc.paragraphs if p.text.startswith(prefix))
    text=p.text.replace('with six bounded starts, including the true addendum coordinates and three fixed-seed random starts','with six bounded starts for (Cₐ,sₐ): the three fixed pairs (0.020,0.75), (0.030,0.65) and (0.015,0.85), plus three random pairs generated with NumPy default_rng seed 20261101 using independent uniform draws over Cₐ∈[0.001,0.090] mm and sₐ∈[0.31,0.94]. Their exact saved values are supplied with the numerical records')
    assert text!=p.text;settext(p,text,'Describe all six archived starts, their generating intervals and fixed seed.')
    patch('The results suggest three practical rules','The results suggest three practical rules for inverse microgeometry work. First, compute the loaded-support range for the intended geometry, torque and phase grid: the sufficient condition can identify invariant relief sets in a fixed-compliance gap model. At s_d=0.25, G2 has no loaded dedendum support and rank two, while G1 and G3 have appreciable dedendum sensitivity (Table 8). Second, a small transmission-error residual, nonzero tangent rank or close depth estimate does not by itself establish recovery of the relief shape; in the 24/24 test the near-true depth was one arbitrary value in an invariant fit set. Third, report a restricted addendum-only fit and the complete reconstructed profile together with parameter estimates and conditional uncertainty. Table 10 summarizes the scope of each evidence group.','Preserve the fixed-compliance and finite-observation qualifications in practical recommendations.')
    p=next(p for p in doc.paragraphs if p.text.startswith('Limitations and outlook.'))
    text=p.text.replace('both are frictionless and quasistatic, with fixed sections, normals and contact coordinates.','both are frictionless and quasistatic. The gap-only inverse operators retain fixed sections, normals and contact coordinates; the separate material-removal control relaxes the fixed-section assumption by reassembling elasticity.')
    text=text.replace('The finite-element tests share the nominal sections with the analytical model,','The finite-element gap tests share the nominal sections with the analytical model,')
    assert text!=p.text;settext(p,text,'Avoid describing the material-removal control as a fixed-section test.')
    p=next(p for p in doc.paragraphs if p.text.startswith('For a fixed-geometry quasistatic contact operator'))
    text=p.text.replace('for independent or for symmetric positive-definite coupled compliance','under the independent-pair uniqueness condition or fixed symmetric positive-definite linear coupled compliance')
    settext(p,text,'Align the conclusion with the precise hypotheses of both propositions.')
    patch('Data availability.','Data availability. The source code, numerical records and editorial construction files supporting this version are supplied in the accompanying MMT_reproducibility_v16.zip, including the version-14 restricted-distance controls, all attempted fits, software versions, source hashes and a SHA-256 manifest. The preceding version-13 baseline is publicly available at https://github.com/romusan/gears-inversion-reproducibility/tree/manuscript-v13; that historical location does not include the subsequent controls or this editorial revision. No repository DOI is currently assigned.','Remove the unfilled DOI promise and accurately distinguish the supplied archive from the public historical baseline.')
    evidence=next(t for t in doc.tables if t.cell(0,0).text=='Evidence')
    for row in evidence.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                if p.text.startswith('Deeper-support response stays distinguishable'):
                    settext(p,'Positive six-start restricted residuals at deeper support in four formulations (D₁₂₀=63–75, versus 0.005–0.006 at marginal support)','A finite multistart search does not certify separation from an entire nonlinear set.')
                if p.text.startswith('Rank 31 of 41 nodal coefficients'):
                    settext(p,'Rank 31 of 41 nodal coefficients; nine basis functions without loaded-support overlap have zero columns; heterogeneous conditional precision','A zero sensitivity column concerns interpolation support, not merely a nodal coordinate.')
    for p in doc.paragraphs:
        if re.match(r'^Figure \d+ ',p.text):p.paragraph_format.keep_together=True
    doc.core_properties.version='16';doc.core_properties.modified=datetime.now(timezone.utc)
    clean=OUT/'MMT_manuscript_Q1_revision_v16_clean.docx';doc.save(clean)
    # Track only changed body/table paragraphs relative to accepted v15.
    original=Document(seed);layout(original);before=list(original.element.body.iter(qn('w:p')))
    final=list(doc.element.body.iter(qn('w:p')));assert len(before)==len(final)
    data=clean.read_bytes();z=zipfile.ZipFile(io.BytesIO(data));xml=E.fromstring(z.read('word/document.xml'))
    trackedpars=xml.findall('.//w:p',NS);assert len(trackedpars)==len(final)
    changed=0;date=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    for i,(a,b) in enumerate(zip(before,final)):
        if ''.join(a.itertext())==''.join(b.itertext()):continue
        p=trackedpars[i];content=[deepcopy(c) for c in p if c.tag!=qn('w:pPr')]
        for c in list(p):
            if c.tag!=qn('w:pPr'):p.remove(c)
        deleted=E.SubElement(p,W+'del',{W+'id':str(changed*2+1000),W+'author':'Codex',W+'date':date})
        for c in a:
            if c.tag==qn('w:pPr'):continue
            oldc=deepcopy(c)
            for t in oldc.findall('.//w:t',NS):t.tag=W+'delText'
            deleted.append(oldc)
        inserted=E.SubElement(p,W+'ins',{W+'id':str(changed*2+1001),W+'author':'Codex',W+'date':date})
        for c in content:inserted.append(c)
        changed+=1
    settings=E.fromstring(z.read('word/settings.xml'));E.SubElement(settings,W+'trackRevisions')
    tracked=rewrite_zip(data,{'word/document.xml':E.tostring(xml,xml_declaration=True,encoding='UTF-8',standalone=True),'word/settings.xml':E.tostring(settings,xml_declaration=True,encoding='UTF-8',standalone=True)})
    (OUT/'MMT_manuscript_Q1_revision_v16_tracked.docx').write_bytes(tracked)
    cleanxml=E.fromstring(z.read('word/document.xml'));acceptedxml=E.fromstring(zipfile.ZipFile(io.BytesIO(accepted(tracked))).read('word/document.xml'))
    assert E.tostring(cleanxml,method='c14n')==E.tostring(acceptedxml,method='c14n')
    sup=Document(BASE/'MMT_supplementary_Q1_revision_v14.docx')
    for p in sup.paragraphs:
        if p.text.startswith('Supplementary Table S10 '):
            p.text+=' Generating θ is (0.020,0.75,0,0.50), (0.020,0.75,0.005,0.30) and (0.020,0.75,0.005,0.45) for addendum, dedendum and dedendum-deep, respectively; the wheel is unmodified and torque is 650 Nm.'
    sup.save(OUT/'MMT_supplementary_Q1_revision_v16.docx')
    from finish_bibliography_v14 import basic,clean_title
    from build_corrected_manuscript import paragraph
    highlights=['Fixed-compliance contact can leave unloaded dedendum relief exactly invisible','Loaded-support invariance extends to fixed coupled linear elastic compliance','Profile likelihood separates exact invariance from weak practical identifiability','FE contact responses need not identify dedendum presence or geometry','A loaded-support check identifies invariant sets before profile inversion']
    assert all(len(s)<=85 for s in highlights)
    h=basic();paragraph(h,'Highlights','Title')
    for s in highlights:paragraph(h,'• '+s)
    clean_title(h);h.save(OUT/'Highlights_v16.docx')
    cover=Document(BASE/'Cover_letter_MMT_v14.docx')
    for p in cover.paragraphs:
        if p.text.startswith('The evidence includes'):p.text=p.text.replace('32 new same-operator','32 same-operator')
        if p.text.startswith('The submission is accompanied'):
            p.text='The submission is accompanied by supplementary Tables S1–S23, Highlights and a version-16 reproducibility archive with current article construction files and the retained numerical evidence. The preceding version-13 baseline is publicly accessible; subsequent controls are included in the accompanying archive. Funding, competing-interest, author-contribution and AI-assistance statements are included in the manuscript.'
    cover.save(OUT/'Cover_letter_MMT_v16.docx')
    (OUT/'editorial_changes_v16.json').write_text(json.dumps(dict(source='Accepted supplied v15 tracked document',changed_paragraphs=changed,edits=edits,abstract_words=len(abstract.split()),exact_starts=starts,truths_57_57=truths,highlights=highlights,credit_roles_confirmed_by_user=True,new_experiments=False),ensure_ascii=False,indent=2),encoding='utf-8')
    print('Saved clean/tracked v16, supplement, Highlights and cover. Changed paragraphs:',changed)
if __name__=='__main__':main()
