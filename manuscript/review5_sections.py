"""Compact main tables, preserved diagnostics and new controlled experiments."""
import json,re
from pathlib import Path
from review4_sections import add_section as previous
from review2_sections import ROOT,tab
SUPPLEMENT=[]
MOVED={7:'S1',8:'S2',9:'S3',10:'S4',13:'S5',14:'S6',17:'S7'}
MAIN={11:8,12:9,15:10,16:7}
NEW=ROOT/'revision_5_2026-10-12'

def relabel(text):
    def change(m):
        n=int(m[1]);return 'Supplementary Table '+MOVED[n] if n in MOVED else 'Table '+str(MAIN.get(n,n))
    return re.sub(r'Table (\d+)\b',change,text)

def add_section(doc,marker,paragraph,table,figure):
    pending=[]
    def prose(d,text):
        m=re.match(r'^Table (\d+) ',text)
        if m and int(m[1]) in MOVED:
            pending.append((int(m[1]),text));return None
        if text.startswith('The baseline single-pair incremental stiffness per width is'):
            text=text.replace('The baseline single-pair incremental stiffness per width is 14.08–15.07',
                'Across 1920 angular positions, the baseline single-pair incremental stiffness per width is 14.08–15.07')
            text+=' The eight-phase subset in Table 12 spans 14.22–15.07; these ranges concern different angular samples.'
        if text.startswith('The eight-phase FE range is'):
            text='At the original linear nodal resolution, the eight-phase FE range is 12.278 µm, versus 11.662 µm at matched baseline phases and 11.950 µm over 1920 baseline positions. The descriptive +16.6% difference from 10.527 µm is discretization dependent and is not a validated discrepancy estimate. A sampled range bounds a full angular range only within the same well-defined operator; it is not a certified bound for physical corner contact. The separated quadratic-element study below checks interior discretization independently of the edge approximation.'
        if text.startswith('Table 12 FE and baseline'):
            text=text.replace('Table 12 FE and baseline','Table 12 Linear-element nodal FE and baseline')
        if text.startswith('A three-point fit k(h)'):
            text='The original joint refinement of linear elements and nodal contact gave effective orders 0.32 and 1.12. Three points did not establish an asymptotic regime, so a Richardson extrapolation from that sequence is not certified. Supplementary Table S7 reports a separate quadratic-element and distributed-pressure study. The original contour/patch checks did not measure the unresolved bulk and contact errors separately.'
        return paragraph(d,relabel(text))
    def tables(d,headers,rows,widths):
        if pending:
            n,caption=pending.pop();SUPPLEMENT.append(dict(number=MOVED[n],caption=relabel(caption),headers=headers,rows=rows,widths=widths));return None
        return table(d,headers,rows,widths)
    if marker=='Q1_SPECTRA':
        # Rebuild existing spectrum table with honest marginal precision.
        from review2_sections import read
        rr=read('support_transition.json')['spectra']
        rows=[[r['sd_true'],int(r['torque_Nm']),f"{r['singular_values'][2]:.4g}",format(r['singular_values'][3],'.2g' if r['sd_true']==.25 else '.4g')] for r in rr]
        tab(doc,8,'Scaled singular values at 120 positions and σ=0.1 µm. Marginal σ₄ uses two significant figures because angular sampling affects it.',
            ['True s_d','Torque Nm','σ₃','σ₄'],rows,[3.8,3.8,4.4,4.4],prose,tables)
        # Delegate with suppression of only the original table and image.
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.shared import Cm,Pt
        p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.keep_with_next=True
        p.add_run().add_picture(str(NEW/'analytic_spectra_v5.png'),width=Cm(15.5))
        cap=prose(doc,'Figure 6 Full singular spectra at 120 positions; legend σ₄ values use two significant figures. The marginal values are grid dependent; see Supplementary Tables S2–S4.')
        cap.alignment=WD_ALIGN_PARAGRAPH.CENTER
        for run in cap.runs:run.font.size=Pt(9)
        def skip_spectrum(d,text):
            if text.startswith('Table 8 '):pending.append(('skip',text));return None
            if text.startswith('Figure 6 '):return prose(d,text+' Marginal values depend on the grid; see Supplementary Tables S3–S4.')
            return prose(d,text)
        def skip_table(d,headers,rows,widths):
            if pending and pending[-1][0]=='skip':pending.pop();return None
            return tables(d,headers,rows,widths)
        # Replace figure asset temporarily by choosing it in the prior picture helper.
        import review2_sections as v2
        old_pic=v2.pic
        v2.pic=lambda d,name,caption,paragraph,new=False: None if name=='analytic_spectra.png' else old_pic(d,name,caption,paragraph,new)
        try:previous(doc,marker,skip_spectrum,skip_table,figure)
        finally:v2.pic=old_pic
        return
    if marker=='Q1_GEOMETRIES':
        def rounded_table(d,headers,rows,widths):
            for row in rows:
                if row[1]==.25:row[5]=f'{float(row[5]):.2g}'
            return tables(d,headers,rows,widths)
        previous(doc,marker,prose,rounded_table,figure)
        prose(doc,'Marginal σ₄ is rounded to two significant figures. Dense budget-normalized values vary approximately from 0.030 to 0.036 across grids and allocations; the 120-position value is near the upper end. Contact overlap remains a useful support screen, but precision requires angular refinement and nonlinear diagnostics.')
        return
    previous(doc,marker,prose,tables,figure)
    if marker=='Q1_MONTE_CARLO':
        r=json.loads((ROOT/'gear_inverse_identifiability/results/q1_review5_2026-10-12/complementary_monte_summary.json').read_text())
        prose(doc,'A controlled nonlinear experiment allocates 50 Nm to even and 300 Nm to odd indices of the canonical 120-position grid, 60 measurements per separately centred load cycle. Independent errors are assigned to the same canonical phases as the single-load experiment, paired by seed. The same bounds, parameter scales, two fixed starts and optimizer tolerances are used. A Lambert-W force engine is checked against the original iterative engine at both truths and starts. The control adds 600 reconstructions, 580 reporting convergence; all selected fits, including 20 failures, enter the statistics.')
        rows=[[x['sd_true'],x['sigma_um'],x['new_success'],f"{x['single300_median']:.3g}",f"{x['complementary_median']:.3g}",f"{x['median_paired_difference']:.3g}",*[f'{v:.3g}' if abs(v)>1e-9 else '0' for v in x['bootstrap_percentile_95']]] for x in r['summary']]
        tab(doc,16,'Complementary-phase control, 100 realizations per cell. Dedendum errors use declared scales. Δ is the median of paired error differences, not the difference of the two medians; 95% percentile bounds use 5000 seed-pair bootstrap samples.',
            ['True s_d','σ µm','Success','Single median','Pair median','Paired Δ','Lower','Upper'],rows,[1.6,1.5,1.5,2.5,2.4,2.4,2.2,2.1],prose,tables)
        prose(doc,'All six controlled bootstrap intervals include zero, with some endpoints at zero because box-limited errors produce ties. No statistically resolved complementary-load advantage is demonstrated at either relief start in these experiments. This closes the nonlinear control for the tested phase assignment, without establishing equivalence, certified coverage, global minima or optimality of maximum torque. The swapped phase assignment has only a local-information control and is not included in this Monte Carlo claim.')
    if marker=='Q1_FE_APPENDIX':
        r=json.loads((NEW/'review5_summary.json').read_text())
        prose(doc,f"The convergence follow-up uses six-node quadratic displacement elements and normalized continuous pressure hats integrated against the actual FE boundary trace. Gap constraints use the same pressure averages. The geometry vertices are fixed independently of pressure-station spacing, so the interface study retains the same body mesh. At fixed contact step 0.01 mm, the last bulk refinement changes stiffness by {100*r['bulk_changes'][0]:.3f}% and {100*r['bulk_changes'][1]:.3f}%. At fixed h=0.25 mm, reducing the interface step from 0.01 to 0.005 mm changes stiffness by {100*r['interface_changes'][0]:.3f}% and {100*r['interface_changes'][1]:.3f}%. These are observed changes, not certified exact-error bounds. The finite quadratic/contact results, rather than the low-order three-point extrapolation, support the interior comparison.")
        tab(doc,17,'Separated quadratic-element/distributed-pressure convergence. Local contact mesh target remains 0.01 mm; interface spacing changes on a fixed geometric body mesh. k is N/µm and approach is µm. Weak contact constraints differ from the original nodal discretization.',
            ['Study','Fraction','h mm','Contact mm','k','Approach'],
            [[x['study'],x['phase_fraction'],x['mesh_h_mm'],x['contact_step_mm'],f"{x['k_incremental_N_um']:.4f}",f"{x['approach_um']:.4f}"] for x in r['separated_records']],
            [2.4,2,2,2.8,3.4,3.6],prose,tables)
