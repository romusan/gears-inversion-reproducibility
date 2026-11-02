"""Read-only science/document audit; writes only the new v14 audit report."""
import sys,json,re,hashlib,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent;OUT=ROOT/'revision_14_2026-11-01'
sys.path.insert(0,str(ROOT/'deposit_v6/gear_inverse_identifiability/src'))
from geometry.involute import InvoluteGear,GearPair
from geometry.microgeometry import TipRelief
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator
def rms(x):return float(np.sqrt(np.mean(np.asarray(x)**2)))
def main():
    rows=json.loads((OUT/'restricted_distance_records.json').read_text());summary=json.loads((OUT/'restricted_distance_summary.json').read_text())
    assert len(rows)==32 and len({(r['variant'],r['truth'][3],r['n'],r['phase_offset_steps']) for r in rows})==32
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in summary['source_sha256'].items())
    errors=[];models={}
    for r in rows:
        variant=r['variant']
        if variant not in models:models[variant]=GearContactModel(GearPair(InvoluteGear(24,3,20,20),InvoluteGear(48,3,20,20)),micro1=TipRelief(),compliance_variant=variant)
        phases=(np.arange(r['n'])+r['phase_offset_steps'])/r['n']*2*np.pi/24
        op=BatchedGapOperator(models[variant],300,phi_positions=phases)
        value=1000*rms(op.evaluate(np.array(r['truth']))['prediction']-op.evaluate(np.array(r['best']['theta']))['prediction'])
        errors.append(abs(value-r['restricted_residual_rms_um']))
        assert abs(r['normalized_distance_120']-120*(value/.1)**2)<1e-8
        assert abs(r['best']['chi2']-r['n']*(value/.1)**2)<1e-8
        assert len(r['attempts'])==6 and r['best']['chi2']==min(a['chi2'] for a in r['attempts'])
    assert max(errors)<1e-10 and summary['max_engine_difference_rms_um']<1e-8 and summary['max_jacobian_relative_error']<1e-5
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    def read(name):
        with zipfile.ZipFile(BASE/name) as z:
            root=ET.fromstring(z.read('word/document.xml'));pars=[''.join(p.itertext()) for p in root.findall('.//w:p',ns)]
            return root,pars,[p for p in z.namelist() if p.startswith('word/media/')]
    doc,pars,media=read('MMT_manuscript_Q1_revision_v14.docx')
    text='\n'.join(pars);first=[]
    for p in pars:
        if re.match(r'^\[\d+\]',p):continue
        for m in re.finditer(r'\[(\d+(?:,\d+)*)\]',p):
            nums=list(map(int,m[1].split(',')))
            if 0 in nums:continue
            for n in nums:
                if n not in first:first.append(n)
    assert first==list(range(1,46)),first
    assert sum(bool(re.match(r'^\[\d+\]',p)) for p in pars)==45
    assert [int(re.match(r'^Figure (\d+)',p)[1]) for p in pars if re.match(r'^Figure \d+',p)]==list(range(1,12))
    assert [int(re.match(r'^Table (\d+)',p)[1]) for p in pars if re.match(r'^Table \d+',p)]==list(range(1,12))
    assert not re.search(r'Q1_[A-Z_]+|REFERENCES_40|Figure pending|EQ: ',text)
    assert len(media)==11
    omml=len(doc.findall('.//{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath'));assert omml==15
    sup,sp,sm=read('MMT_supplementary_Q1_revision_v14.docx')
    assert [int(re.match(r'^Supplementary Table S(\d+)',p)[1]) for p in sp if p.startswith('Supplementary Table S')]==list(range(1,24))
    _,hp,_=read('Highlights_v14.docx');bullets=[p for p in hp if p.startswith('• ')]
    assert len(bullets)==5 and all(len(p)<=85 for p in bullets)
    raw=(BASE/'q1_manuscript_v14.md').read_text(encoding='utf-8');abstract=raw.split('## Abstract')[1].split('Keywords:')[0]
    assert len(abstract.split())<=250
    assert 'No DOI or public version-14 deposit is claimed.' in text
    assert 'MMT_reproducibility_v14.zip' in text
    report=dict(new_cases=32,new_attempts=192,new_failed_attempts=summary['failed_attempts'],max_recalculated_residual_error_um=max(errors),source_hashes_match=True,references_in_first_appearance_order=45,figures=11,tables=11,supplement_tables=23,omml_equations=omml,abstract_words=len(abstract.split()),highlights_lengths=[len(p) for p in bullets],documents_sha256={name:hashlib.sha256((BASE/name).read_bytes()).hexdigest() for name in ['MMT_manuscript_Q1_revision_v14.docx','MMT_supplementary_Q1_revision_v14.docx','Highlights_v14.docx','Cover_letter_MMT_v14.docx']},scope='Independent recalculation from saved estimates, source integrity and document structure. Not a rerun of FE or the 1800 historical inversions; visual QA recorded separately.')
    (OUT/'audit_v14.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
