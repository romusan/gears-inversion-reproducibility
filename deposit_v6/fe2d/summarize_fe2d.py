"""Release tables, figures and interpretation from completed FE records."""
import json,csv,hashlib,zipfile
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from run_fe2d import OUT,solve_contact,RB
import meshio

BASE=Path(__file__).resolve().parent
def main():
    report=json.loads((OUT/'campaign.json').read_text());rows=report['records']
    extras=json.loads((OUT/'geometry_patch_checks.json').read_text())
    nominal=[next(r for r in rows if r['phase_fraction']==p and r['mesh_h_mm']==.25 and r['bore_radius_mm']==25 and r['root_trim_mm']==.4) for p in [0,.5]]
    a=np.load(OUT/'f0.5_h0.25_d0.01_b25_r0.4_exactgap_contact.npz');H=a['H_mm_N'].copy();n=len(H)//2
    H[:n,n:]=0;H[n:,:n]=0;ablation=solve_contact(H,a['gap_mm'],650000/RB)
    baseline=dict(phase_fraction=[0,.5],k_incremental_N_um=[346.50674595884794,535.4921473519315],approach_um=[28.059656592715353,17.99218843592849],
        source='Existing analytical baseline evaluated at exactly the same two phases and nominal dimensions; not external measured/FE values.')
    checks=[]
    for r in extras:
        ref=nominal[0 if r['phase_fraction']==0 else 1]
        checks.append(dict(phase_fraction=r['phase_fraction'],geometry_factor=r.get('geometry_factor',1),patch_halfwidth_mm=r['patch_halfwidth_mm'],
            k_change_relative=float(r['k_incremental_N_um']/ref['k_incremental_N_um']-1)))
    allrows=rows+extras
    assert all(r['force_residual_N']<1e-6 and r['contact_residual_mm']<1e-9 and r['elastic_residual_relative']<1e-8 for r in allrows)
    assert all(r['tangent_relative_difference']<1e-6 and r['torque_relative_error']<1e-4 for r in allrows)
    assert all(c['within_one_percent'] for c in report['mesh_convergence'])
    assert all(abs(c['k_change_relative'])<.01 for c in checks)
    summary=dict(nominal=nominal,k2_over_k1=nominal[1]['k_incremental_N_um']/nominal[0]['k_incremental_N_um'],
        baseline=baseline,baseline_k2_over_k1=baseline['k_incremental_N_um'][1]/baseline['k_incremental_N_um'][0],
        coupling_ablation=dict(uncoupled_k2_N_um=ablation['k_N_um'],uncoupled_approach_um=ablation['delta']*1000,
            relative_k_reduction=float(1-nominal[1]['k_incremental_N_um']/ablation['k_N_um']),
            interpretation='Controlled removal of cross-pair FE flexibility blocks; a counterfactual diagnostic, not another physical geometry.'),
        mesh_convergence=report['mesh_convergence'],geometry_and_patch_checks=checks,fe_runs=len(allrows),
        maximum_torque_relative_error=max(r['torque_relative_error'] for r in allrows),
        physical_scope='Assumed bore and approximate root; independent numerical continuum test, not validated reconstruction of the published FE model.')
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    fields=['phase_fraction','nominal_pairs','mesh_h_mm','contact_step_mm','bore_radius_mm','root_trim_mm','patch_halfwidth_mm','geometry_factor','approach_um','k_incremental_N_um','k_secant_N_um','nodes','elements','force_residual_N','contact_residual_mm','elastic_residual_relative','torque_relative_error']
    with (OUT/'fe2d_results.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(allrows)
    fig,axes=plt.subplots(1,3,figsize=(13,4.2))
    for phase,label in [(0,'One pair'),(.5,'Two pairs')]:
        rr=[r for r in rows if r['phase_fraction']==phase and r['bore_radius_mm']==25 and r['root_trim_mm']==.4]
        axes[0].plot([sum(r['elements'])/1000 for r in rr],[r['k_incremental_N_um'] for r in rr],'o-',label=label)
    axes[0].set_xlabel('Total triangles (thousands)');axes[0].set_ylabel('Incremental stiffness (N/µm)');axes[0].set_title('Mesh refinement');axes[0].legend();axes[0].grid(alpha=.25)
    names=['20','25','35'];x=np.arange(3)
    for phase,label,shift in [(0,'One pair',-.18),(.5,'Two pairs',.18)]:
        yy=[next(r['k_incremental_N_um'] for r in rows if r['phase_fraction']==phase and r['bore_radius_mm']==float(b) and r['root_trim_mm']==.4 and r['mesh_h_mm']==.25) for b in names]
        axes[1].bar(x+shift,yy,.36,label=label)
    axes[1].set_xticks(x,names);axes[1].set_xlabel('Assumed clamped bore radius (mm)');axes[1].set_ylabel('Incremental stiffness (N/µm)');axes[1].set_title('Support assumption');axes[1].legend();axes[1].grid(axis='y',alpha=.25)
    axes[2].bar(['Coupled FE','Cross blocks\nremoved','Analytical\nbaseline'],[nominal[1]['k_incremental_N_um'],ablation['k_N_um'],baseline['k_incremental_N_um'][1]],color=['tab:blue','tab:orange','gray'])
    axes[2].tick_params(axis='x',labelsize=8);axes[2].set_ylabel('Two-pair stiffness (N/µm)');axes[2].set_title('Coupling diagnostic');axes[2].grid(axis='y',alpha=.25)
    fig.suptitle('Exploratory plane-strain FE, 650 Nm; assumed bore and root geometry');fig.tight_layout();fig.savefig(OUT/'fe2d_summary.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,4.8))
    meshes=[meshio.read(OUT/f'f0.5_h0.25_d0.01_b25_r0.4_exactgap_body{i}.vtu') for i in [1,2]]
    maxdisp=max(float(np.linalg.norm(m.point_data['displacement_mm'],axis=1).max())*1000 for m in meshes)
    for m in meshes:
        mag=np.linalg.norm(m.point_data['displacement_mm'],axis=1)*1000
        artist=ax.tripcolor(m.points[:,0],m.points[:,1],m.get_cells_type('triangle'),mag,shading='gouraud',vmin=0,vmax=maxdisp)
    ax.set_aspect('equal');ax.set_xlabel('x (mm)');ax.set_ylabel('y (mm)');ax.set_title('Two-pair contact configuration; displacement magnitude (µm)')
    fig.colorbar(artist,ax=ax,label='µm');fig.tight_layout();fig.savefig(OUT/'fe2d_gears.png',dpi=180);plt.close(fig)
    lines=['# Resultado del contraste FE 2D a 650 Nm','',
        'Se ejecutó un modelo continuo de los dos engranajes completos con contacto unilateral sin fricción. El caso nominal supone un cubo rígido de radio 25 mm y una transición de raíz aproximada con recorte de 0.4 mm. Las cifras siguientes son resultados de ese modelo exploratorio; no reproducen el CAD ni las restricciones desconocidas del benchmark publicado.','',
        '| Configuración | FE k incremental (N/µm) | FE k secante (N/µm) | Acercamiento (µm) | Baseline k incremental (N/µm) |',
        '|---|---:|---:|---:|---:|']
    for i,r in enumerate(nominal):lines.append(f"| {i+1} par(es), fase {r['phase_fraction']} | {r['k_incremental_N_um']:.2f} | {r['k_secant_N_um']:.2f} | {r['approach_um']:.3f} | {baseline['k_incremental_N_um'][i]:.2f} |")
    lines+=['',f"La razón k₂/k₁ es {summary['k2_over_k1']:.4f}, frente a {summary['baseline_k2_over_k1']:.4f} del baseline en las mismas fases. El equilibrio corresponde a una fuerza normal total de {nominal[0]['normal_force_N']:.3f} N. La diferencia de acercamientos entre estas dos fases es {nominal[0]['approach_um']-nominal[1]['approach_um']:.3f} µm; no es una amplitud pico a pico de un ciclo completo.",'','## Controles numéricos','',
        f"La campaña comprende {len(allrows)} casos FE de dos cuerpos. En tres niveles de malla, el último cambio de rigidez es {100*report['mesh_convergence'][0]['last_k_change']:.3f}% con un par y {100*report['mesh_convergence'][1]['last_k_change']:.3f}% con dos. Son cambios entre discretizaciones, no cotas demostradas del error exacto.",
        f"Duplicar la discretización del contorno y ampliar el semiancho candidato de contacto de 0.35 a 0.50 mm cambia cada rigidez menos de {100*max(abs(c['k_change_relative']) for c in checks):.3f}%. Los extremos de los parches quedan descargados.",
        f"Las pruebas de deformación constante, energía y rotación rígida pasan. En todos los casos, el residuo elástico relativo es menor que {max(r['elastic_residual_relative'] for r in allrows):.2e}, el de contacto menor que {max(r['contact_residual_mm'] for r in allrows):.2e} mm y el de fuerza menor que {max(r['force_residual_N'] for r in allrows):.2e} N. El máximo error relativo de torque es {summary['maximum_torque_relative_error']:.2e}. La rigidez tangente coincide con diferencias de fuerza ±0.1% dentro de {max(r['tangent_relative_difference'] for r in allrows):.2e} relativo.",'','## Sensibilidad física y acoplamiento','',
        '| Radio asumido del cubo (mm) | k₁ (N/µm) | k₂ (N/µm) | k₂/k₁ |','|---:|---:|---:|---:|']
    for bore in [20,25,35]:
        r=[next(t for t in rows if t['phase_fraction']==p and t['mesh_h_mm']==.25 and t['bore_radius_mm']==bore and t['root_trim_mm']==.4) for p in [0,.5]]
        lines.append(f"| {bore} | {r[0]['k_incremental_N_um']:.2f} | {r[1]['k_incremental_N_um']:.2f} | {r[1]['k_incremental_N_um']/r[0]['k_incremental_N_um']:.4f} |")
    lines+=['','La sujeción del cubo cambia tanto el nivel absoluto como la razón de rigidez. Esa incertidumbre física supera los cambios del último refinamiento; no puede ocultarse usando una coincidencia aislada con una amplitud externa. El contorno de raíz también influye y sus variantes están en el CSV.',
        f"Al anular únicamente los bloques de flexibilidad cruzada entre los dos pares, k₂ aumenta de {nominal[1]['k_incremental_N_um']:.2f} a {ablation['k_N_um']:.2f} N/µm. El acoplamiento reduce la rigidez un {100*summary['coupling_ablation']['relative_k_reduction']:.2f}% respecto a ese contrafactual. Esto demuestra un efecto del acoplamiento en el modelo FE supuesto; no demuestra que sea la causa de toda la discrepancia del benchmark ni que haya errores compensados.",
        '','## Alcance','',
        'Se resolvieron dos fases interiores, no las transiciones ni un ciclo TE completo. El modelo supone deformación plana, normales fijas, pequeñas deformaciones, contacto sin fricción, cubo circular empotrado y raíz aproximada. No incluye el contorno de herramienta real, llanta o eje del benchmark, efectos de ancho, contacto de esquina ni validación experimental. Para el artículo puede presentarse como contraste independiente exploratorio con estas hipótesis, sin declarar validado el modelo publicado ni certificada la reconstrucción física.',
        '','## Archivos','',
        '- `run_fe2d.py`: geometría, mallado, elasticidad y contacto.',
        '- `campaign.py` y `extra_checks.py`: barrido y controles.',
        '- `results/campaign.json`, `summary.json`, `geometry_patch_checks.json` y `fe2d_results.csv`: registros completos.',
        '- `results/*exactgap_body1.vtu` y `body2.vtu`: mallas y desplazamientos del caso nominal en coordenadas globales, compatibles con ParaView.',
        '- `results/*contact.npz`: matrices de flexibilidad, huecos y fuerzas.',
        '- `results/fe2d_summary.png` y `fe2d_gears.png`: figuras.',
        '','El manuscrito v3 se conserva. Este contraste está documentado por separado para distinguir sus hipótesis de la referencia mecánica externa.']
    (BASE/'resultado_FE2D.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    release_files=[p for p in BASE.iterdir() if p.suffix in ['.py','.md','.txt']]+[p for p in OUT.iterdir() if p.is_file() and ('exactgap' in p.name or p.name in ['campaign.json','summary.json','geometry_patch_checks.json','fe2d_results.csv','fe2d_summary.png','fe2d_gears.png'])]
    manifest={str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in release_files}
    (BASE/'manifest.json').write_text(json.dumps(manifest,indent=2))
    with zipfile.ZipFile(BASE/'FE2D_650Nm.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in release_files+[BASE/'manifest.json']:z.write(p,p.relative_to(BASE))
    print(json.dumps({'k1':nominal[0]['k_incremental_N_um'],'k2':nominal[1]['k_incremental_N_um'],'ratio':summary['k2_over_k1'],'runs':len(allrows)},indent=2))

if __name__=='__main__':main()
