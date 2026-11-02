"""Independent postprocessing of moving-contact and CalculiX artifacts."""
import ast,csv,hashlib,json,re,sys
from pathlib import Path
import numpy as np
from scipy.linalg import cho_factor,cho_solve
from shapely.geometry import Polygon
ROOT=Path(__file__).resolve().parent;FE=ROOT.parent/'fe2d';sys.path.insert(0,str(FE))
import updated_surface_contact as u


def read_table(text,label):
    lines=text.splitlines();starts=[i for i,s in enumerate(lines) if label in s]
    if not starts:return {}
    result={};started=False
    for s in lines[starts[-1]+1:]:
        fields=s.split()
        if len(fields)==4 and fields[0].isdigit():
            result[int(fields[0])]=list(map(float,fields[1:]));started=True
        elif started:break
    return result


def frd_block(path,label):
    lines=path.read_text(errors='replace').splitlines()
    starts=[i for i,s in enumerate(lines) if s.startswith(' -4') and label in s]
    if not starts:return {}
    out={}
    for s in lines[starts[-1]+1:]:
        if s.startswith(' -3'):break
        if s.startswith(' -1'):
            # CCX can exceed its nominal field width for a negative mantissa
            # with a three-digit exponent; parse exponent-delimited values.
            fields=re.findall(r'[+-]?\d+\.\d+E[+-]\d{3}',s[13:])
            out[int(s[3:13])]=list(map(float,fields))
    return out


def independent_results():
    u.fe.configure_24_24();records=[]
    paths=list((ROOT/'calculix_crosscheck').glob('*v3_torque.dat'))+list((ROOT/'calculix_crosscheck').glob('*v4_mortar_hard.dat'))
    for path in sorted(paths):
        console=path.with_suffix('.console.txt')
        if not console.exists() or 'Job finished' not in console.read_text(errors='replace'):continue
        text=path.read_text();disp=read_table(text,'displacements (vx,vy,vz) for set CONTROL')
        force=read_table(text,'forces (fx,fy,fz) for set CONTROL')
        if len(disp)!=4 or len(force)!=4:continue
        ids=sorted(disp);rot=ids[-1];T=force[rot][2]
        if abs(T/300000-1)>1e-5:continue
        phase=float(re.search(r'^f([\d.]+)_',path.stem)[1]);step=float(re.search(r'_s([\d.]+)_',path.stem)[1])
        h=float(re.search(r'_h([\d.]+)_',path.stem)[1]);penalty=float(re.search(r'_k([^_]+)_',path.stem)[1])
        contact=frd_block(path.with_suffix('.frd'),'CONTACT')
        assert contact
        min_gap_all=min(v[0] for v in contact.values())
        active_contact=[v for v in contact.values() if len(v)>3 and v[3]>1e-4]
        assert active_contact
        min_gap=min(v[0] for v in active_contact)
        translation=np.array(force[ids[0]])[:2]+np.array(force[ids[2]])[:2]
        force_res=float(np.linalg.norm(translation)/max(np.linalg.norm(force[ids[0]][:2]),1))
        moment=force[ids[1]][2]+force[ids[3]][2]+u.fe.CENTER*force[ids[2]][1]
        moment_res=abs(moment/300000)
        assert force_res<1e-5 and moment_res<1e-5
        meta_path=path.with_name(path.stem.replace('_v4_mortar_hard','_v3_torque')+'_input.json')
        if not meta_path.exists():meta_path=path.with_name(path.stem.replace('_v3_torque','_v2')+'_input.json')
        plane_error=None
        if meta_path.exists():
            meta=json.loads(meta_path.read_text());all_u=frd_block(path.with_suffix('.frd'),'DISP')
            offset=0;errors=[]
            for m in meta['mesh']:
                n=m['nodes_2d']
                for i in range(n):
                    a1=np.array(all_u[offset+i+1][:3]);a2=np.array(all_u[offset+n+i+1][:3])
                    errors.append(max(np.max(abs(a1[:2]-a2[:2])),abs(a1[2]),abs(a2[2])))
                offset+=2*n
            plane_error=max(errors)*1000
            assert plane_error<.001
        mortar='v4_mortar_hard' in path.stem
        records.append(dict(file=path.name,phase=phase,step_mm=step,h_mm=h,penalty_N_mm3=None if mortar else penalty,
            method='hard mortar, default incremental small-sliding pairing' if mortar else 'node-to-surface, finite sliding, linear penalty',
            approach_um=disp[rot][2]*u.fe.RB*1000,hub_angle_rad=disp[rot][2],torque_Nmm=T,
            max_penetration_um=max(0,-min_gap)*1000,global_force_balance_relative=force_res,
            reported_negative_COPEN_all_nodes_um=max(0,-min_gap_all)*1000,
            contact_output_note='Active CPRESS>1e-4 MPa nodes used for the reported active COPEN. Mortar inactive projection values are retained separately; they are not a geometric nonpenetration certificate.',
            plane_strain_kinematic_error_um=plane_error,
            global_moment_balance_relative=moment_res,normal_termination=True,
            input_sha256=hashlib.sha256(path.with_suffix('.inp').read_bytes()).hexdigest()))
    return records


def forward_results():
    records=[];failures=[]
    for path in (ROOT/'updated_contact').glob('f*.json'):
        r=json.loads(path.read_text())
        if 'stages' not in r:continue
        r['result_file']=path.name;r.setdefault('case','nominal');r.setdefault('master_slave_reversed',False)
        if r['all_load_stages_converged']:records.append(r)
        else:failures.append(dict(file=path.name,stages=r['stages']))
    # Prefer expanded-patch results for the same physical configuration.
    best={}
    for r in sorted(records,key=lambda x:('_patch2' in x['result_file'],x['result_file'])):
        key=(r['phase'],r['step_mm'],r['h_mm'],r['case'],r['master_slave_reversed'],r.get('two_pass',False),r.get('dual_regularization_relative',0.));best[key]=r
    verified=[]
    for r in best.values():
        for stage in r['stages']:
            last=stage['last']
            assert last['true_gap_error_um']<.001 and last['penetration_um']<.001
            assert last['torque_relative_error']<1e-6 and last['elastic_fixed_point_relative_error']<1e-5
        tag=r.get('tag',Path(r['result_file']).stem)
        state=np.load(ROOT/'updated_contact'/(tag+'_state.npz'))
        polys=[state['poly1'],state['poly2']] if 'poly1' in state else [state['poly'],state['poly']]
        indices=[state['indices1'],state['indices2']];u.N1=len(polys[0]);u.N2=len(polys[1])
        cc=u.fe.contacts(r['phase'],.05,.025,True);R1=cc[0]['R1'];R2=cc[0]['R2']
        dis=[state['u1'],state['u2']];theta=float(state['theta'])
        x,y,Q2=u.geometry(polys,indices,dis,R1,R2,theta);rows=u.contacts(x,y,r['master_slave_reversed'],two_pass=r.get('two_pass',False))
        minimum_gap=min(c['gap'] for c in rows)*1000
        assert minimum_gap>-.001
        opposite=u.contacts(x,y,not r['master_slave_reversed'])
        opposite_penetration=max(0,-min(c['gap'] for c in opposite))*1000
        pg1,pg2=Polygon(x),Polygon(y)
        assert pg1.is_valid and pg2.is_valid
        overlap_area=pg1.intersection(pg2).area
        # Recover physical nodal boundary forces from independently saved C,u.
        nodal=[];energies=[];torques=[];resultants=[]
        for k,R in enumerate([R1,Q2]):
            z=np.load(ROOT/'updated_contact'/(r.get('cache_tag',tag)+f'_body{k+1}.npz'));C=z['C']
            factor=cho_factor(C)
            f=cho_solve(factor,dis[k]);nodal.append(f);energies.append(float(.5*dis[k]@f))
            coord=(polys[k][indices[k]]+dis[k].reshape(-1,2))@R.T
            fw=f.reshape(-1,2)@R.T
            torques.append(float(np.sum(u.old.cross2(coord,fw))));resultants.append(fw.sum(axis=0))
        torque_error=abs(torques[1]/(-300000)-1)
        # Gear2 surface load opposes the positive prescribed hub torque.
        force_balance=float(np.linalg.norm(resultants[0]+resultants[1])/max(np.linalg.norm(resultants[0]),1))
        assert torque_error<2e-5 and force_balance<2e-5
        active=[];slave_body=1 if r['master_slave_reversed'] else 0
        fb=nodal[slave_body].reshape(-1,2);Rslave=Q2 if slave_body else R1
        lookup={int(v):k for k,v in enumerate(indices[slave_body])}
        if r.get('two_pass',False):
            current={(c['reverse'],c['i']):c for c in rows}
            for pressure,direction,index in zip(state['force'],state['slave_directions'],state['slave_indices']):
                if pressure>1e-4:active.append(abs(current[(bool(direction),int(index))]['gap'])*1000)
        else:
            for c in rows:
                force_norm=np.linalg.norm(fb[lookup[c['i']]])
                if force_norm>1e-4:active.append(abs(c['gap'])*1000)
        assert active and max(active)<.001
        verified.append(dict(phase=r['phase'],step_mm=r['step_mm'],h_mm=r['h_mm'],case=r['case'],
            reverse=r['master_slave_reversed'],two_pass=r.get('two_pass',False),regularization_relative=r.get('dual_regularization_relative',0.),file=r['result_file'],tag=tag,
            approach_um=theta*u.fe.RB*1000,minimum_researched_gap_um=minimum_gap,
            opposite_direction_penetration_um=opposite_penetration,polygon_overlap_area_mm2=overlap_area,
            global_polygon_overlap_within_tolerance=overlap_area<1e-8,
            two_direction_gap_within_1nm=opposite_penetration<.001,
            max_researched_active_gap_um=max(active),recovered_torque_error=torque_error,
            recovered_force_balance_relative=force_balance,strain_energy_N_mm=sum(energies),
            load_stages=len(r['stages'])))
    return sorted(verified,key=lambda r:(r['phase'],r['case'],r['reverse'],-r['step_mm'])),failures


def main():
    u.fe.configure_24_24();forward,nonconverged=forward_results();cross=independent_results()
    extended_path=ROOT/'updated_contact/extended_campaign.json'
    exceptions=[r for r in json.loads(extended_path.read_text()) if 'error' in r] if extended_path.exists() else []
    source_files=list(FE.glob('*surface*.py'))+[FE/'crosscheck_calculix.py',FE/'extend_surface_objectives.py',FE/'run_bilateral_objectives.py',FE/'run_fe2d.py',Path(__file__),ROOT/'screen_public_data.py']+list((ROOT/'updated_contact').glob('*.py'))
    hashes={}
    for f in source_files:ast.parse(f.read_text(encoding='utf-8'));hashes[str(f.relative_to(ROOT.parent))]=hashlib.sha256(f.read_bytes()).hexdigest()
    source_provenance=[]
    for path in (ROOT/'updated_contact').glob('f*.json'):
        raw=json.loads(path.read_text());sha=raw.get('source_sha256')
        if sha:
            matched=[name for name,value in hashes.items() if value==sha]
            assert matched,'Missing exact numerical source for '+path.name
            source_provenance.append(dict(result=path.name,source_sha256=sha,matching_sources=matched))
    nominal=[];contrasts=[];contrasts_by_load=[];cross_compare=[]
    for phase in sorted({r['phase'] for r in forward}):
        ff=[r for r in forward if r['phase']==phase and r['case']=='nominal' and not r['reverse'] and not r['two_pass']]
        ff.sort(key=lambda r:-r['step_mm'])
        for mode in [False,True]:
            series=[r for r in forward if r['phase']==phase and r['case']=='nominal' and not r['reverse'] and r['two_pass']==mode and (not mode or r['regularization_relative']==1e-8)]
            series.sort(key=lambda r:-r['step_mm'])
            for a,b in zip(series,series[1:]):nominal.append(dict(phase=phase,two_pass=mode,coarse_step=a['step_mm'],fine_step=b['step_mm'],approach_change_um=b['approach_um']-a['approach_um']))
        for step in [.02,.01]:
            aa=next((r for r in forward if r['phase']==phase and r['step_mm']==step and r['case']=='addendum' and not r['reverse'] and r['two_pass']),None)
            bb=next((r for r in forward if r['phase']==phase and r['step_mm']==step and r['case']=='combined' and not r['reverse'] and r['two_pass']),None)
            if aa and bb:
                contrasts.append(dict(phase=phase,step_mm=step,geometry_dedendum_contrast_um=bb['approach_um']-aa['approach_um']))
                ar=json.loads((ROOT/'updated_contact'/aa['file']).read_text());br=json.loads((ROOT/'updated_contact'/bb['file']).read_text())
                for astage in ar['stages']:
                    bstage=next(s for s in br['stages'] if s['torque_Nm']==astage['torque_Nm'])
                    contrasts_by_load.append(dict(phase=phase,step_mm=step,torque_Nm=astage['torque_Nm'],
                        geometry_dedendum_contrast_um=bstage['last']['approach_um']-astage['last']['approach_um'],
                        maximum_runtime_gap_error_um=max(astage['last']['true_gap_error_um'],bstage['last']['true_gap_error_um']),
                        note='Intermediate load states checked by runtime records; final 300 Nm state additionally reconstructed from stored compliance/displacement.'))
        for c in [c for c in cross if c['phase']==phase]:
            for bilateral in [False,True]:
                f=next((r for r in forward if r['phase']==phase and r['case']=='nominal' and not r['reverse'] and r['two_pass']==bilateral and r['step_mm']==c['step_mm'] and r['h_mm']==c['h_mm']),None)
                if f:cross_compare.append(dict(phase=phase,step_mm=c['step_mm'],two_pass=bilateral,calculix_method=c['method'],penalty=c['penalty_N_mm3'],calculix_um=c['approach_um'],updated_um=f['approach_um'],difference_um=c['approach_um']-f['approach_um']))
    role=[]
    for r in [r for r in forward if r['reverse']]:
        f=next((f for f in forward if f['phase']==r['phase'] and f['step_mm']==r['step_mm'] and f['h_mm']==r['h_mm'] and f['case']==r['case'] and f['two_pass']==r['two_pass'] and f['regularization_relative']==r['regularization_relative'] and not f['reverse']),None)
        if f:role.append(dict(phase=r['phase'],step_mm=r['step_mm'],reverse_minus_forward_um=r['approach_um']-f['approach_um']))
    offset_free=[]
    for step in [.02,.01]:
        for torque in [60.,150.,300.]:
            entry=next((r for r in contrasts_by_load if r['phase']==.174048546 and r['step_mm']==step and r['torque_Nm']==torque),None)
            interior=next((r for r in contrasts_by_load if r['phase']==.5 and r['step_mm']==step and r['torque_Nm']==torque),None)
            if entry and interior:offset_free.append(dict(step_mm=step,torque_Nm=torque,entry_minus_interior_dedendum_contrast_um=entry['geometry_dedendum_contrast_um']-interior['geometry_dedendum_contrast_um'],
                definition='(combined_entry-combined_interior) - (addendum_entry-addendum_interior): cancels a constant offset per load, not unknown gain or phase error. Not full-cycle RMS.'))
    result=dict(forward_configurations=len(forward),load_stages_verified=sum(r['load_stages'] for r in forward),
        forward=forward,nonconverged=nonconverged,exceptions_retained=exceptions,
        calculix=cross,cross_solver_comparisons=cross_compare,nominal_refinement=nominal,
        master_slave_comparisons=role,actual_geometry_dedendum_contrasts=contrasts,
        actual_geometry_dedendum_contrasts_by_load=contrasts_by_load,
        offset_free_two_phase_contrasts=offset_free,
        source_hashes=hashes,source_provenance=source_provenance,public_screening=json.loads((ROOT/'public_data_screening.json').read_text()),
        scope='Selected phases only, idealized 2D plane strain and assumed sharp-tip/root geometry. No physical validation, no new inverse recovery claim, no full-cycle transition validation. v18 untouched.')
    (ROOT/'AUDITORIA_OBJETIVOS.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    with (ROOT/'resultados_directos.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(forward[0]));writer.writeheader();writer.writerows(forward)
    if offset_free:
        with (ROOT/'contraste_entre_fases.csv').open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(offset_free[0]));writer.writeheader();writer.writerows(offset_free)
    print('verified configurations',len(forward),'load stages',result['load_stages_verified'],'CalculiX cases',len(cross),'retained exceptions',len(exceptions))


if __name__=='__main__':main()
