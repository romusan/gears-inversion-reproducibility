"""Recompute CalculiX balances and paired relief contrasts from raw files."""
import sys,json,re,hashlib
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'revision_20_2026-11-01';sys.path[:0]=[str(ROOT/'fe2d'),str(ROOT/'objetivos_numericos_2026-11-01')]
from audit_objectives import read_table,frd_block
import updated_surface_contact as mc
from vectorized_projection_v19 import search
mc.search=search
def main():
    mc.fe.configure_24_24();results=[];failed=[]
    meshes=json.loads((ROOT/'revision_19_2026-11-01/experiments/mesh_metadata.json').read_text())
    for folder in [OUT/'calculix_crosscheck',OUT/'calculix_cycle_crosscheck']:
        for meta_path in sorted(folder.glob('*_input.json')):
            stem=meta_path.name.replace('_input.json','');path=folder/(stem+'.dat');console=folder/(stem+'.console.txt')
            if not console.exists() or 'Job finished' not in console.read_text(errors='replace'):
                note=folder/(stem+'.interrupted.json')
                failed.append(dict(input=stem+'.inp',normal_termination=False,interruption=json.loads(note.read_text()) if note.exists() else None));continue
            m=json.loads(meta_path.read_text());text=path.read_text();U=read_table(text,'displacements (vx,vy,vz) for set CONTROL');F=read_table(text,'forces (fx,fy,fz) for set CONTROL');assert len(U)==len(F)==4
            ids=sorted(U);rot=ids[-1];torque=F[rot][2];force=np.array(F[ids[0]])[:2]+np.array(F[ids[2]])[:2]
            ferr=float(np.linalg.norm(force)/max(np.linalg.norm(F[ids[0]][:2]),1));terr=float(abs(torque/300000-1));merr=float(abs((F[ids[1]][2]+F[ids[3]][2]+mc.fe.CENTER*F[ids[2]][1])/300000))
            assert max(ferr,terr,merr)<1e-5
            disp=frd_block(folder/(stem+'.frd'),'DISP');contact=frd_block(folder/(stem+'.frd'),'CONTACT');assert disp and contact
            active=[v for v in contact.values() if len(v)>3 and v[3]>1e-4];assert active
            b=json.loads((folder/(stem+'_boundary.json')).read_text());polys=[];plane=[]
            offset=0
            for which,bound in enumerate(b):
                n=m['mesh'][which]['nodes_2d']
                for i in range(n):
                    a=np.array(disp[offset+i+1][:3]);bb=np.array(disp[offset+n+i+1][:3]);plane.append(max(abs(a[2]),abs(bb[2]),max(abs(a[:2]-bb[:2]))))
                du=np.array([(np.array(disp[i][:2])+np.array(disp[j][:2]))/2 for i,j in zip(bound['bottom_ids'],bound['top_ids'])]);polys.append(np.array(bound['initial_world'])+du);offset+=2*n
            assert max(plane)*1000<.001
            assert all(Polygon(p).is_valid for p in polys)
            mc.N1,mc.N2=map(len,polys);rows=mc.contacts(*polys,two_pass=True);minimum_gap=min(c['gap'] for c in rows)*1000
            if folder.name=='calculix_cycle_crosscheck':
                theta=np.array(m['theta']);tag='profile_'+hashlib.sha256(theta.tobytes()).hexdigest()[:12]+f"_s{m['step']:g}_h{m['h']:g}"
                expected=next(q for q in meshes if q['tag']==tag)
                assert m['mesh'][0]['nodes_2d']==expected['nodes'] and m['mesh'][0]['triangles']==expected['triangles']
            results.append(dict(folder=folder.name,file=stem,phase=m['phase'],step=m['step'],h=m['h'],case=m['case'],method=m['contact_method'],initial_increment=m.get('initial_increment',.1),approach_um=U[rot][2]*mc.fe.RB*1000,torque_relative_error=terr,force_balance_relative=ferr,moment_balance_relative=merr,plane_strain_error_um=max(plane)*1000,active_COPEN_min_um=min(v[0] for v in active)*1000,all_COPEN_min_um=min(v[0] for v in contact.values())*1000,reprojected_minimum_gap_um=float(minimum_gap),polygon_overlap_area_mm2=float(Polygon(polys[0]).intersection(Polygon(polys[1])).area),input_sha256=hashlib.sha256((folder/(stem+'.inp')).read_bytes()).hexdigest(),normal_termination=True))
    prior=json.loads((ROOT/'objetivos_numericos_2026-11-01/AUDITORIA_OBJETIVOS.json').read_text())['forward'];cycle=[json.loads(x) for x in (ROOT/'revision_19_2026-11-01/experiments/cycle_s0.02_h0.35.jsonl').read_text().splitlines()]
    comparisons=[]
    keys=sorted({(r['folder'],r['phase'],r['step'],r['h'],r['method'],r['initial_increment']) for r in results})
    for folder,phase,step,h,method,increment in keys:
        pair=[r for r in results if (r['folder'],r['phase'],r['step'],r['h'],r['method'],r['initial_increment'])==(folder,phase,step,h,method,increment)]
        if len(pair)!=2:continue
        add=next(r for r in pair if r['case']=='addendum');comb=next(r for r in pair if r['case']=='combined')
        if folder=='calculix_cycle_crosscheck':own=[r for r in cycle if abs(r['phase']-phase)<1e-10 and r['case'] in ['addendum','combined']]
        else:own=[r for r in prior if r['phase']==phase and r['step_mm']==step and r['h_mm']==h and r['case'] in ['addendum','combined'] and r['two_pass'] and not r['reverse']]
        assert len(own)==2
        aa=next(r for r in own if r['case']=='addendum')['approach_um'];bb=next(r for r in own if r['case']=='combined')['approach_um'];delta=comb['approach_um']-add['approach_um'];reference=bb-aa
        comparisons.append(dict(folder=folder,phase=phase,step=step,h=h,method=method,initial_increment=increment,calculix_contrast_um=delta,own_contrast_um=reference,difference_um=delta-reference,relative_contrast_difference_percent=100*(delta-reference)/reference,addendum_absolute_difference_um=add['approach_um']-aa,combined_absolute_difference_um=comb['approach_um']-bb))
    selected=[r for r in comparisons if r['folder']=='calculix_cycle_crosscheck'];offset=None
    if len(selected)==2:
        a=next(r for r in selected if r['phase']==.225);b=next(r for r in selected if r['phase']==.5)
        offset=dict(calculix_two_phase_contrast_um=a['calculix_contrast_um']-b['calculix_contrast_um'],own_two_phase_contrast_um=a['own_contrast_um']-b['own_contrast_um']);offset['difference_um']=offset['calculix_two_phase_contrast_um']-offset['own_two_phase_contrast_um']
    continuation=None
    slow=next((r for r in comparisons if r['folder']=='calculix_crosscheck' and r['step']==.02 and r['initial_increment']==.1),None);fast=next((r for r in comparisons if r['folder']=='calculix_crosscheck' and r['step']==.02 and r['initial_increment']==1.),None)
    if slow and fast:continuation=dict(slow_contrast_um=slow['calculix_contrast_um'],fast_contrast_um=fast['calculix_contrast_um'],difference_um=fast['calculix_contrast_um']-slow['calculix_contrast_um'])
    report=dict(results=results,failed_or_unfinished=failed,comparisons=comparisons,offset_free_two_phase=offset,continuation_control=continuation,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Selected deterministic phases. Pointwise contrasts and a two-phase offset-free contrast are not full-cycle RMS, physical validation, or calibrated error bounds. Reprojected gaps/overlap additionally quantify geometric discrepancy in penalty/weak mortar contact.')
    (OUT/'audit_ccx_v20.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
