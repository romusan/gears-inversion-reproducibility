"""Independent CalculiX finite-sliding contact, controlled hub rotation.
Extruded wedges with u_z=0 on both planes reproduce a plane-strain test,
not a 3D face-width validation. Geometry and Gmsh mesh are shared inputs.
"""
import argparse,hashlib,json,os,subprocess,time
from pathlib import Path
import numpy as np
import pilot_surface_contact as p

ROOT=Path(__file__).resolve().parents[1]/'objetivos_numericos_2026-11-01'
OUT=ROOT/'calculix_crosscheck';OUT.mkdir(exist_ok=True)
EXE=ROOT/'calculix/CalculiX-2.23.0-win-x64/bin/ccx_MT.exe'


def make_deck(phase,angle,step=.04,h=.5,penalty=1e7,torque_control=False,mortar_hard=False):
    fe=p.fe;fe.configure_24_24();poly,_=p.contour(step);cc=fe.contacts(phase,.05,.025,True)
    nodes=[];elements=[];surfaces=[];hubs=[];mesh=[]
    for which in [1,2]:
        R=cc[0]['R'+str(which)];center=np.array([0 if which==1 else fe.CENTER,0])
        world=poly@R.T+center;near=(abs(world[:,0]-fe.CENTER/2)<5)&(abs(world[:,1])<12)
        body=p.make_body(poly,h,near);xy=body['xy']@R.T+center
        n=len(xy);offset=len(nodes);tri=body['basis'].mesh.t.T.copy()
        negative=p.cross2(xy[tri[:,1]]-xy[tri[:,0]],xy[tri[:,2]]-xy[tri[:,0]])<0
        tri[negative]=tri[negative][:,[0,2,1]]
        nodes.extend([(float(x),float(y),z) for z in [-fe.WIDTH/2,fe.WIDTH/2] for x,y in xy])
        face_edges={};eo=len(elements)
        for k,t in enumerate(tri):
            elements.append([offset+int(j)+1 for j in np.r_[t,t+n]])
            for side,(a,b) in enumerate([(t[0],t[1]),(t[1],t[2]),(t[2],t[0])],3):
                key=tuple(sorted([int(a),int(b)]));face_edges.setdefault(key,[]).append((eo+k+1,side))
        surf=[]
        for (a,b),faces in face_edges.items():
            mid=(xy[a]+xy[b])/2
            if len(faces)==1 and abs(mid[0]-fe.CENTER/2)<5 and abs(mid[1])<12:surf.append(faces[0])
        surfaces.append(surf)
        hub=np.where(np.linalg.norm(body['xy'],axis=1)<12+1e-7)[0]
        hubs.append([offset+int(i)+1 for i in np.r_[hub,hub+n]])
        mesh.append(dict(nodes_2d=n,triangles=len(tri),contact_faces=len(surf)))
    total_nodes=len(nodes);control=[]
    for center in [0,fe.CENTER]:
        nodes.extend([(center,0,0),(0,0,0)]);control.append((len(nodes)-1,len(nodes)))
    lines=['*HEADING','24/24 assumed geometry, independent contact cross-check; mm N MPa','*NODE']
    lines += [f'{i+1}, {x:.12g}, {y:.12g}, {z:.12g}' for i,(x,y,z) in enumerate(nodes)]
    lines += ['*ELEMENT,TYPE=C3D6,ELSET=ALLGEARS']
    lines += [str(i+1)+', '+', '.join(map(str,e)) for i,e in enumerate(elements)]
    lines += ['*MATERIAL,NAME=STEEL','*ELASTIC',f'{fe.E}, {fe.NU}','*SOLID SECTION,ELSET=ALLGEARS,MATERIAL=STEEL']
    for i in [0,1]:
        lines += [f'*NSET,NSET=HUB{i+1}']
        lines += [', '.join(map(str,hubs[i][j:j+15])) for j in range(0,len(hubs[i]),15)]
        lines += [f'*RIGID BODY,NSET=HUB{i+1},REF NODE={control[i][0]},ROT NODE={control[i][1]}']
        lines += [f'*SURFACE,NAME=SURF{i+1},TYPE=ELEMENT']+[f'{e},S{s}' for e,s in surfaces[i]]
    plane=sorted(set(range(1,total_nodes+1))-set(hubs[0])-set(hubs[1]))
    lines += ['*NSET,NSET=PLANESTRAIN']+[', '.join(map(str,plane[j:j+15])) for j in range(0,len(plane),15)]
    lines += ['*NSET,NSET=CONTROL',', '.join(str(j) for pair in control for j in pair),
        '*SURFACE INTERACTION,NAME=FRICTIONLESS','*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR',f'{penalty}, 0.001, 0.1',
        '*CONTACT PAIR,INTERACTION=FRICTIONLESS,TYPE=NODE TO SURFACE','SURF1,SURF2',
        '*BOUNDARY','PLANESTRAIN,3,3,0']
    for ref,rot in control:lines += [f'{ref},1,3,0',f'{rot},1,2,0']
    lines += [f'{control[0][1]},3,3,0',f'{control[1][1]},3,3,0',
        '*STEP,NLGEOM,INC=150','*STATIC','0.1,1.,1e-7,0.2',
        '*BOUNDARY',f'{control[1][1]},3,3,{angle:.12g}',
        '*NODE PRINT,NSET=CONTROL,FREQUENCY=999','U,RF',
        '*NODE PRINT,NSET=HUB2,FREQUENCY=999','RF',
        '*NODE FILE,FREQUENCY=999','U,RF','*CONTACT FILE,FREQUENCY=999','CDIS,CSTR','*END STEP']
    if torque_control:
        lines += ['*STEP,NLGEOM,INC=150','*STATIC','0.2,1.,1e-7,0.5','*BOUNDARY,OP=NEW','PLANESTRAIN,3,3,0']
        for ref,rot in control:lines += [f'{ref},1,3,0',f'{rot},1,2,0']
        lines += [f'{control[0][1]},3,3,0','*CLOAD',f'{control[1][1]},3,300000',
            '*NODE PRINT,NSET=CONTROL,FREQUENCY=999','U,RF','*CONTACT FILE,FREQUENCY=999','CDIS,CSTR','*END STEP']
    if mortar_hard:
        revised=[];skip=False
        for line in lines:
            if skip:skip=False;continue
            if line.startswith('*SURFACE BEHAVIOR'):skip=True;continue
            revised.append(line.replace('TYPE=NODE TO SURFACE','TYPE=MORTAR'))
        lines=revised
    tag=f'f{phase:.9f}_s{step:g}_h{h:g}_k{penalty:g}_a{angle:.9g}_v2'
    if torque_control:tag=tag.replace('_v2','_v3_torque')
    if mortar_hard:tag=tag.replace('_v3_torque','_v4_mortar_hard')
    path=OUT/(tag+'.inp');path.write_text('\n'.join(lines)+'\n',encoding='ascii')
    (OUT/(tag+'_input.json')).write_text(json.dumps(dict(phase=phase,angle_rad=angle,step=step,h=h,penalty=penalty,
        mesh=mesh,control_nodes=control,total_mesh_nodes=total_nodes,contact_method='hard mortar' if mortar_hard else 'finite-sliding nodal penalty',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2))
    return path


def execute(path):
    env=os.environ.copy();env['OMP_NUM_THREADS']='2';start=time.time()
    with path.with_suffix('.console.txt').open('w',encoding='utf-8') as f:
        result=subprocess.run([str(EXE.resolve()),'-i',path.stem],cwd=OUT,stdout=f,stderr=subprocess.STDOUT,
                              env=env,creationflags=subprocess.CREATE_NO_WINDOW,timeout=600)
    text=path.with_suffix('.console.txt').read_text(errors='replace')
    receipt=dict(returncode=result.returncode,seconds=time.time()-start,normal_termination='Job finished' in text,
        exe_sha256=hashlib.sha256(EXE.read_bytes()).hexdigest())
    path.with_suffix('.execution.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
    return receipt


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--phase',type=float,default=.174048546)
    ap.add_argument('--angle',type=float,default=.0008285);ap.add_argument('--penalty',type=float,default=1e7)
    ap.add_argument('--step',type=float,default=.04);ap.add_argument('--h',type=float,default=.5)
    ap.add_argument('--torque-control',action='store_true')
    ap.add_argument('--mortar-hard',action='store_true')
    a=ap.parse_args();execute(make_deck(a.phase,a.angle,a.step,a.h,a.penalty,a.torque_control,a.mortar_hard))
