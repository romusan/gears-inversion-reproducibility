"""Final narrow revision from preserved v16 and saved stress records; no fitting."""
from pathlib import Path
from copy import deepcopy
import json,re,shutil
from docx import Document
from docx.shared import Cm,Pt
from docx.oxml.ns import qn
from build_corrected_manuscript import table,paragraph
ROOT=Path(__file__).resolve().parent.parent
OLD=ROOT/'revision_16_2026-11-01';OUT=ROOT/'revision_17_final_2026-11-01'
LABEL={'iid':'IID','correlated_iid_fit':'AR / IID fit','correlated_gls_fit':'AR / GLS fit','gain5_iid_fit':'Gain +5%','operator_iid_fit':'Operator change'}
def f(x):return '—' if x is None else f'{x:.3g}'
def median(s,k='dedendum'):return f(s[k]['median']) if s and s[k] else '—'
def write(p,text):
    p.clear();offset=0
    for m in re.finditer(r'\b(C|s)_([A-Za-z0-9]+)',text):
        p.add_run(text[offset:m.start()]+m[1]);p.add_run(m[2]).font.subscript=True;offset=m.end()
    p.add_run(text[offset:]);return p
def main():
    summary=json.loads((OUT/'stress_summary.json').read_text());cells=summary['cells']
    archived=json.loads((OUT/'archived_status_strata.json').read_text())['cells']
    assert summary['cases']==500 and summary['attempts']==1500
    d=Document(OLD/'MMT_manuscript_Q1_revision_v16_clean.docx')
    changes=[]
    def patch(prefix,new):
        p=next(p for p in d.paragraphs if p.text.startswith(prefix));changes.append({'before':p.text,'after':new});write(p,new)
    # Retain the existing abstract's numerical claims; add the finite stress scope.
    p=next(p for p in d.paragraphs if p.text.startswith('Inferring gear microgeometry'))
    text=p.text.replace('These results yield a pre-inversion support diagnostic and operator-conditioned limits on observability without establishing physical profile recovery.','A further 500 synthetic stress cases assess correlated noise, gain and operator mismatch. The results delimit operator-conditioned observability without establishing physical profile recovery.')
    patch('Inferring gear microgeometry',text);assert len(text.split())<=250
    patch('Data availability.','Data availability. The source code, numerical records and editorial construction files supporting this version are supplied in the accompanying MMT_reproducibility_v17.zip. This includes all 500 new stress cases and 1500 attempted fits, the retained version-14 restricted-distance controls, archived Monte Carlo status partitions, software versions, source hashes and a SHA-256 manifest. The preceding version-13 baseline is publicly available at https://github.com/romusan/gears-inversion-reproducibility/tree/manuscript-v13; that historical location does not include the subsequent controls or this revision. No repository DOI is currently assigned.')
    p=next(p for p in d.paragraphs if p.text.startswith('Table 10 '))
    patch('Table 10 ',p.text+' Proposed follow-up experiments are mapped to the evidence groups in Supplementary Table S27; the additional finite stress controls are described in Section 4.8.')
    p.paragraph_format.keep_with_next=True;p.paragraph_format.keep_together=True
    evidence=next(t for t in d.tables if t.cell(0,0).text=='Evidence')
    for cell in evidence.rows[0].cells:
        for hp in cell.paragraphs:hp.paragraph_format.keep_with_next=True
    patch('Figure 5 ','Figure 5 Dedendum error under 100 realizations per cell. Solid lines are medians and dotted lines are 90th percentiles over all selected fits, including nonconverged selections. The maximum possible scaled error in the admissible box is 4.5. Supplementary Table S26 separates converged interior estimates, converged dedendum bound hits and nonconverged selections without changing these historical statistics.')
    anchor=next(p for p in d.paragraphs if p.text=='5 Discussion')
    def insert(text,style=None):
        p=paragraph(d,'',style);write(p,text);anchor._p.addprevious(p._p);return p
    insert('4.8 Finite noise and operator stress controls','Heading 2')
    insert('A separate synthetic campaign uses the nominal G0 pair, 300 Nm, 120 canonical phases and the two generating starts s_d=0.25 and 0.40, with θ=(0.020,0.75,0.005,s_d). The inverse uses projected-energy compliance throughout. Five scenarios each use 50 realizations: independent Gaussian noise; correlated noise fitted as independent; the same correlated observations fitted by generalized least squares (GLS) with their known covariance; an unmodelled 5% response gain plus independent noise; and shear-G generating responses fitted with projected-energy compliance plus independent noise. The last scenario changes the compliance formulation while sharing geometry and the contact reduction; it is not independent physical validation.')
    insert('The marginal noise standard deviation is 0.1 µm. Correlation is stationary and nonperiodic, with C_ij=0.8^|i−j|; GLS whitens residuals and Jacobians with the Cholesky factor of this known covariance. Gaussian innovations use NumPy default_rng seeds 2026110100–2026110149 and are paired across scenarios and generating starts. Noise is added after centring the deterministic response and is not subsequently recentered. These assumed covariance and gain levels are illustrative controls, not estimates from the twelve external amplitude targets, which cannot calibrate waveform error.')
    insert('Each bounded four-parameter fit uses three fixed starts (0.030,0.65,0.010,0.35), (0.015,0.85,0.020,0.45) and (0.010,0.50,0.040,0.48), with depths in mm. Scaled trust-region least squares uses the analytic tangent, at most 600 function evaluations, and tolerances ftol=10⁻⁹, xtol=10⁻¹⁰ and gtol=10⁻⁸. The smallest objective among the three attempts is retained even when its optimizer flag reports nonconvergence. A dedendum bound hit means that either dedendum coordinate lies within 10⁻⁶ of its admissible interval width from a bound. Raw observations, every attempt and selected statuses are archived; this finite multistart search gives no global optimum certificate.')
    result=[]
    for sd in [.25,.4]:
        cc=[c for c in cells if c['sd_true']==sd]
        result.append('At s_d='+str(sd)+', median scaled dedendum errors in the scenario order above are '+', '.join(median(c['strata']['all']) for c in cc)+'.')
    insert(' '.join(result)+f" Across the 500 selected fits, {summary['failed_selected']} report nonconvergence; {summary['failed_attempts']} of the 1500 attempts report nonconvergence. Figure 12 and Supplementary Tables S24–S25 separate converged interior solutions, converged bound hits and failed selections. Medians over all selected fits describe this computational procedure and are not conditional recovery guarantees.")
    disc=[c for c in cells if c['scenario']=='operator_iid_fit']
    insert('The deterministic shear-G versus projected-energy mismatch at the generating truths is '+ ' and '.join(f(c['discrepancy_rms_um']) for c in disc)+' µm RMS for s_d=0.25 and 0.40, respectively. Residual RMS and complete-profile error are reported alongside dedendum error in Supplementary Table S24. A changed error distribution under GLS, gain or compliance mismatch concerns these declared synthetic operators; it does not calibrate confidence-interval coverage, encoder drift, eccentricity or physical model discrepancy. Fifty realizations per cell support a finite stress comparison, not precise tail estimation. Supplementary Table S26 also partitions the unchanged 1800 earlier Monte Carlo selections by convergence and dedendum bound status; no earlier observations or fits are replaced.')
    pic=d.add_paragraph();pic.paragraph_format.keep_with_next=True;pic.add_run().add_picture(str(OUT/'stress_v17.png'),width=Cm(16));anchor._p.addprevious(pic._p)
    cap=insert('Figure 12 Finite synthetic stress controls with 50 paired realizations per scenario and generating start. Blue circles denote converged interior dedendum estimates, red crosses converged dedendum bound hits, and black plus signs nonconverged selections. Black bars show medians over all selected fits. AR denotes the assumed nonperiodic correlation and GLS uses its known covariance. A low residual or an apparently accurate coordinate is not a physical recovery certificate.');cap.paragraph_format.keep_together=True
    for r in cap.runs:r.font.size=Pt(9)
    p=next(p for p in d.paragraphs if p.text.startswith('Limitations and outlook.'))
    patch('Limitations and outlook.',p.text+' The finite stress controls in Section 4.8 relax the independent-noise and same-compliance assumptions under specified synthetic alternatives. They do not resolve the omitted FE transition stations or provide measured waveform calibration. Supplementary Table S27 maps each remaining evidence gap to a concrete follow-up experiment; these follow-ups have not been performed here.')
    p=next(p for p in d.paragraphs if p.text.startswith('The defensible outcome'))
    base=next(c for c in cells if c['sd_true']==.4 and c['scenario']=='iid')['strata']['all']
    gain=next(c for c in cells if c['sd_true']==.4 and c['scenario']=='gain5_iid_fit')['strata']['all']
    patch('The defensible outcome','The finite stress controls extend the numerical evidence to correlated noise, a gain error and a change of compliance formulation, with all optimizer attempts and bound hits retained. At the deeper generating truth, the 5% gain error raises median scaled dedendum error from '+median(base)+' to '+median(gain)+', while the median observation residual is '+median(gain,'fit')+' µm. The defensible outcome remains an operator-conditioned account of observability and uncertainty, together with a pre-inversion support check. Physical reconstruction of the relief profile remains contingent on independent mechanical and experimental validation.')
    d.core_properties.version='17';d.save(OUT/'MMT_manuscript_Q1_revision_v17_clean.docx')
    s=Document(OLD/'MMT_supplementary_Q1_revision_v16.docx')
    paragraph(s,'Additional finite stress controls','Heading 1')
    paragraph(s,'Supplementary Table S24 Finite stress campaign. Each row contains 50 selected fits. D is median maximum scaled dedendum error; P is median complete-profile RMSE (µm, 1001 flank points); R is median observation residual RMS (µm); δ is the noiseless generating-versus-fitted-operator RMS at truth (µm). Medians include nonconverged selections, which are counted explicitly. These are illustrative synthetic scenarios, not measured discrepancy calibration.','Caption')
    table(s,['s_d','Scenario','D','P µm','R µm','δ µm','Failed'],[[str(c['sd_true']),LABEL[c['scenario']],median(c['strata']['all']),median(c['strata']['all'],'profile'),median(c['strata']['all'],'fit'),f(c['discrepancy_rms_um']),str(c['failed'])] for c in cells],[1,3.3,1.6,2.1,2.1,2.1,1.3])
    paragraph(s,'Supplementary Table S25 Status partition for the new campaign. I denotes converged interior dedendum estimates, B converged dedendum bound hits and F failed selected attempts. Each entry gives count / median scaled dedendum error. I+B+F=50 per row. Bound hits include either depth or start; the archived per-coordinate flags retain their distinction.','Caption')
    table(s,['s_d','Scenario','I: n / D','B: n / D','F: n / D'],[[str(c['sd_true']),LABEL[c['scenario']]]+[str(c['strata'][k]['n'])+' / '+median(c['strata'][k]) for k in ['converged_interior','converged_bound','failed']] for c in cells],[1,4,3,3,3])
    paragraph(s,'Supplementary Table S26 Status partition of the 1800 unchanged archived selections. Each cell originally has 100 realizations. Entries give count / median scaled dedendum error; I, B and F follow Table S25. single300 uses the original 120-position cycle; multi50_300 uses two 60-position cycles; 50_even_300_odd is the complementary interleaved design. This table reclassifies stored fits without rerunning them.','Caption')
    def oldentry(c,k):
        v=c['strata'][k];return ('0 / —' if v is None else str(v['n'])+' / '+f(v['median']))
    table(s,['s_d','Design','σ µm','I: n / D','B: n / D','F: n / D'],[[str(c['sd_true']),c['design'],str(c['sigma_um'])]+[oldentry(c,k) for k in ['converged_interior','converged_bound','failed']] for c in archived],[1,3.4,1.4,2.7,2.7,2.7])
    paragraph(s,'Supplementary Table S27 Experiments needed to extend the scope of Table 10. These are proposed follow-ups, not completed results or prerequisites claimed to have been satisfied by the current numerical controls.','Caption')
    rows=[['Fixed-compliance invariance','Physical removal with updated stiffness, contact locations and normals through a complete cycle.'],['Marginal versus deeper support','Map multiple truths and support coordinates, with refinement of the engagement window.'],['Profile uncertainty','Calibrate procedure-specific thresholds under a declared error model and test coverage; synthetic-null calibration alone does not validate misspecified FE intervals.'],['Load and sampling design','Use common phases across a torque sweep, then optimize a dedendum criterion after profiling addendum nuisance parameters; validate nonlinear recovery.'],['Restricted response distance','Broaden the bounded search and report best known objectives; assess independent waveforms.'],['FE gap comparison','Resolve all 18 omitted 24/24 transition stations with verified corner/fillet contact, then repeat forward and inverse refinement.'],['Material removal','Extend the eight-phase control to complete-cycle contact with manufacturing geometry.'],['External fidelity','Measure TE waveforms on gears with independently certified relief, or compare independent complete-geometry 3D waveforms.'],['Arbitrary relief field','Test nonlinear finite perturbations, basis refinement and additional observables with a stated gauge.'],['Noise and operator stress','Estimate waveform covariance, gain and mounting errors from independent measurements; retain optimizer and boundary partitions.']]
    table(s,['Evidence or limitation','Next experiment'],rows,[4.3,10])
    for p in s.paragraphs:
        if any(p.text.startswith('Supplementary Table S'+str(i)+' ') for i in range(24,28)):
            p.style=s.styles['Normal'];p.paragraph_format.keep_with_next=True;p.paragraph_format.keep_together=True
            for r in p.runs:r.font.color.rgb=None;r.font.size=Pt(11);r.bold=False
    for t in s.tables[23:]:
        if t.cell(0,0).text=='s_d':
            p=t.cell(0,0).paragraphs[0];p.clear()
            for value,sub in [('s',False),('d',True)]:
                r=p.add_run(value);r.font.subscript=sub;r.font.size=Pt(9);r.bold=True
    for row in s.tables[-1].rows:
        for p in row.cells[1].paragraphs:p.alignment=0
    s.core_properties.version='17';s.save(OUT/'MMT_supplementary_Q1_revision_v17.docx')
    h=Document(OLD/'Highlights_v16.docx');h.core_properties.version='17';h.save(OUT/'Highlights_v17.docx')
    c=Document(OLD/'Cover_letter_MMT_v16.docx')
    for p in c.paragraphs:
        if p.text.startswith('The submission is accompanied'):
            p.text='The submission is accompanied by supplementary Tables S1–S27, Highlights and a version-17 reproducibility archive containing current article construction files and numerical records. The revision includes 500 additional finite synthetic stress cases with 1500 attempted fits, addressing correlated noise, a 5% gain error and a change of compliance formulation; all selected failures and dedendum bound hits are reported. These controls do not replace measured-data validation or resolve the omitted finite-element transition phases. Funding, competing-interest, author-contribution and AI-assistance statements are included in the manuscript.'
    c.core_properties.version='17';c.save(OUT/'Cover_letter_MMT_v17.docx')
    (OUT/'editorial_changes_v17.json').write_text(json.dumps({'base':'v16 clean, equations and earlier numerical tables preserved','changed_existing_paragraphs':changes,'new_section':'4.8','supplement_tables':27,'abstract_words':len(text.split()),'new_cases':500,'new_attempts':1500},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Built v17 main, supplement, Highlights and cover')
if __name__=='__main__':main()
