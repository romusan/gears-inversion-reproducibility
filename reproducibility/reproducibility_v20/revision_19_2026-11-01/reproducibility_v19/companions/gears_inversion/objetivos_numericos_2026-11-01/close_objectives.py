"""Create an evidence report, scientific figure and compact bundle after audit."""
import hashlib,importlib.metadata,json,shutil,zipfile,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent;GEARS=ROOT.parent
sys.path.append(str(GEARS/'fe2d/.venv/Lib/site-packages'))


def main():
    a=json.loads((ROOT/'AUDITORIA_OBJETIVOS.json').read_text());allf=a['forward']
    bilateral=[r for r in allf if r['two_pass']]
    campaign=json.loads((ROOT/'updated_contact/bilateral_campaign.json').read_text())
    successful={tuple(r['configuration']) for r in campaign if r.get('result',{}).get('all_load_stages_converged',False)}
    assert len(successful)==19,'Complete planned campaign and audit before closing'
    assert all(r['two_direction_gap_within_1nm'] for r in bilateral)
    assert all(r['global_polygon_overlap_within_tolerance'] for r in bilateral)
    def best(phase,step):
        return next(r for r in bilateral if r['phase']==phase and r['step_mm']==step and r['case']=='nominal' and not r['reverse'] and r['regularization_relative']==1e-8)
    phases=[.174048546,.5,.825951454]
    tables=['fase | acercamiento 0.04 / 0.02 / 0.01 mm (µm) | ultimo cambio (µm) | penetracion bilateral fina (µm)']
    for phase in phases:
        r=[best(phase,s) for s in [.04,.02,.01]]
        gap=max(-r[-1]['minimum_researched_gap_um'],r[-1]['opposite_direction_penetration_um'],0)
        tables.append(f"{phase:.6f} | "+' / '.join(f"{x['approach_um']:.6f}" for x in r)+f" | {r[-1]['approach_um']-r[-2]['approach_um']:.6f} | {gap:.6g}")
    contrasts=a['actual_geometry_dedendum_contrasts']
    ct=['fase | paso contacto mm | contraste geometrico combinado - punta (µm)']
    for r in contrasts:ct.append(f"{r['phase']:.6f} | {r['step_mm']:.3f} | {r['geometry_dedendum_contrast_um']:.8f}")
    ot=['torque Nm | paso mm | contraste dedendum entre entrada e interior (µm)']
    for r in a['offset_free_two_phase_contrasts']:ot.append(f"{r['torque_Nm']:.0f} | {r['step_mm']:.3f} | {r['entry_minus_interior_dedendum_contrast_um']:.8f}")
    xc=[r for r in a['cross_solver_comparisons'] if r['two_pass']]
    xt=['fase | paso mm | contacto CalculiX | diferencia CalculiX - propio (µm)']
    for r in xc:xt.append(f"{r['phase']:.6f} | {r['step_mm']:.3f} | {r['calculix_method']} | {r['difference_um']:.8f}")
    samples=a['public_screening']['downloaded_experimental_samples']
    rows=sum(r['rows'] for r in samples)
    roles=[r for r in a['master_slave_comparisons'] if r['step_mm']==.04]
    description=f'''OBJETIVOS SIN FABRICACIÓN — ESTADO VERIFICADO 2026-11-01

DECISIÓN Y ALCANCE
Se avanzó en contacto móvil, verificación con un solver independiente y búsqueda
de datos públicos. Este paquete es evidencia computacional de una geometría
virtual declarada. El manuscrito y los archivos de envío v18 no se modificaron.

Resultado útil: el operador nuevo supera el control geométrico bilateral en las
fases ensayadas. En el caso virtual, retirar material en la raíz cambia la forma
de la respuesta entre entrada e interior; su magnitud se registra más abajo.
Todavía no se demostró recuperación única de parámetros ni un ciclo completo.
La búsqueda de datos públicos tampoco obtuvo una pareja elegible de relieve
medido y TE del mismo engranaje. Estos dos pendientes quedan explícitos.

1. CONTACTO MÓVIL: IMPLEMENTADO Y VERIFICADO EN FASES SELECCIONADAS
Se actualizaron proyecciones, normales, transmisión de fuerzas y momento real
durante la deformación. El primer esquema de una pasada convergía algebraicamente
pero admitía penetración vista desde el otro engranaje. Se conservan esos casos
como diagnóstico. La formulación final impone restricciones de ambos lados.

Se completaron 19 configuraciones bilaterales planificadas: nueve controles
nominales (tres fases, tres resoluciones), dos controles de regularización/orden
y ocho casos con geometría de relieve (punta/ambos, dos fases, dos resoluciones).
Cada configuración se resolvió mediante continuación de carga a 60, 150 y 300 Nm. Las iteraciones
no se cuentan como experimentos independientes. El archivo de auditoría también
incluye controles unilaterales de desarrollo y comparaciones de CalculiX.

MODELO Y DATOS VIRTUALES
24/24 dientes; módulo 3 mm; ángulo de presión 20 grados; ancho 20 mm; E = 210 GPa; nu = 0.3;
radio de apoyo del cubo 12 mm, empotrado; deformación plana y elasticidad lineal
en ejes de cada cuerpo, con giro rígido finito del cubo de salida. Se impone el
torque real del engranaje 2. La punta es aguda y el enlace de raíz es una curva
cuadrática supuesta con trim = 0.4 mm. No son un radio ni un filete certificados.
La discretización de esa raíz usa 12 intervalos fijos; no es una certificación
de convergencia de toda la geometría ni un estudio de radios de fabricación.
Cinco dientes se refinan localmente; los flancos lejanos conservan paso de 0.35 mm.
El remuestreo de arcos/cuerdas entre las geometrías nominal y de punta produce
pequeñas diferencias de área que se registran en la auditoría geométrica. En
cambio, la geometría combinada es retirada de material respecto de la de punta
con la misma discretización, comprobado mediante diferencia de polígonos.

La ley de relieve del piñón usa p=2, xi=u/u_tip y parámetros
(Ca,sa,Cd,sd)=(0.020,0.75,0.010,0.50), en mm para profundidades. Se cambia el
contorno del flanco cargado y se vuelve a generar su sólido FE. El flanco
modificado se extiende hasta la circunferencia de punta original y se enlaza
a la raíz mediante la construcción declarada. El caso de punta usa Cd=0.
Cambian tanto geometría como rigidez; no se añadió una compliance de Hertz.

NÚMEROS DIRECTOS A 300 Nm
{chr(10).join(tables)}

Estos valores son radio base por giro de acercamiento en una fase. No son RMS,
ni máximos-mínimos ni TE centrado de un ciclo completo. Un último cambio de
refinamiento es una estimación de sensibilidad, no una cota certificada del error.
El residuo del contacto verifica las ecuaciones de una malla; no certifica la
exactitud de la solución continua ni de un engranaje real. Los decimales se
guardan para trazabilidad computacional y no expresan precisión metrológica.

CONTRASTE DEL DEDENDUM CON GEOMETRÍA MODIFICADA
{chr(10).join(ct)}

El contraste es acercamiento con ambos relieves menos acercamiento con relieve
de punta, en la misma fase. La estabilidad de esa diferencia debe juzgarse junto
con el cambio de cada respuesta, la discretización y la geometría asumida.
Detectar un contraste no demuestra recuperar de forma única profundidad y
extensión. No se hizo una nueva inversión ni se declararon intervalos de
identificación a partir de estos resultados directos.
Este generador cambia también la rigidez al retirar material. La invisibilidad
exacta del artículo se refiere al operador, soporte y compliance especificados
en sus proposiciones. Una respuesta de otro operador con geometría/rigidez
actualizadas se debe comparar respetando esas hipótesis.

CONTRASTE ENTRE FASES QUE CANCELA UN OFFSET CONSTANTE
Se calcula (combinado_entrada - combinado_interior) menos
(punta_entrada - punta_interior), en cada carga y resolución.
{chr(10).join(ot)}
Este contraste elimina un nivel constante por carga. No elimina errores de
ganancia o fase, ni es RMS de un ciclo. Su estabilidad es evidencia de cambio
en la forma de la respuesta virtual, no identificación de cuatro parámetros.

2. SOLVER INDEPENDIENTE: COMPARACIÓN NUMÉRICA REALIZADA
Se descargó CalculiX 2.23 portátil y se ejecutaron análisis con no linealidad
geométrica. Los primeros casos usan contacto nodo-superficie con deslizamiento
finito y penalización. Se estudió el cambio de penalización en entrada. También
se ejecutó contacto mortar duro en entrada con dos resoluciones. Mortar usa
el emparejamiento incremental por defecto del programa; no se afirma una
validación de su presión de esquina ni independencia completa del incremento.

Cada comparación final usa 300 Nm. Una etapa previa prescribe un pequeño giro
para establecer contacto; después se libera ese giro y se aplica el momento.
Los cuerpos se extruyen con cuñas C3D6 y u_z=0; es una comparación de deformación
plana, no validación tridimensional a lo ancho del diente. La geometría y el
mallador se comparten: se contrasta el operador/solver de contacto.

{chr(10).join(xt)}

3. DATOS EXPERIMENTALES PÚBLICOS: BÚSQUEDA HECHA; VALIDACIÓN INVERSA ABIERTA
Se cribaron ocho fuentes, incluidas pistas en mandarín. Se descargaron dos
CSV experimentales públicos ({rows} filas en total) del conjunto DaRUS de
Bauer y Nowinski (2026), DOI 10.18419/DARUS-5760, licencia CC BY 4.0. Se conservan
en su forma original, unidades radianes, junto con metadatos y hashes.
Corresponden a un reductor robótico, y no se ha verificado una pareja de
geometría/relieve/TE apropiada para la inversión de nuestros engranajes rectos.
No se ajustó un relieve de engranaje a esas señales ni se les asignó un radio.

La literatura con perfiles helicoidales medidos encontrada incluye datos bajo
solicitud; otros repositorios son numéricos, de fallos/vibración o conceptuales.
No se obtuvo una pareja pública elegible de relieve medido y TE del mismo par.
Esto describe el resultado de esta búsqueda; no demuestra inexistencia global.
No se contactó a autores/laboratorios ni se fabricaron componentes.

CONTROL Y TRAZABILIDAD
AUDITORIA_OBJETIVOS.json contiene {a['forward_configurations']} configuraciones
directas auditadas y {a['load_stages_verified']} estados de carga, incluyendo los
controles de desarrollo conservados. Se comprobaron geometría deformada en
ambos sentidos, validez de polígonos, área de solape, equilibrio, energía positiva,
reciprocidad y recuperación de fuerzas a partir de las matrices condensadas.
Las soluciones unilaterales que fallan el control bilateral se identifican como
tales: no son soluciones físicas validadas por converger su conjunto activo.

Se usó una regularización dual diminuta para restricciones redundantes; se
verificó con un caso analítico y cambio de magnitud en el caso de entrada.
No es una compliance física añadida. Se registró su perturbación máxima de gap.
También se verificaron contra soluciones independientes los problemas cuadráticos de contacto (QP), el arranque
con solución anterior, el uso de matrices dispersas y el filtro espacial.
Se retuvo el fallo de salida de la zona condensada y su corrección mediante
una zona ampliada independiente de la normal inicial.

QUÉ SIGUE ABIERTO
- Validar todas las 18 fases antes excluidas y un ciclo completo, con refinamiento
  suficiente para cada contraste local. Los 102 casos interiores previos eran
  fases conservadas, no 102 ensayos de convergencia de malla.
- Cuantificar radios de punta, filete generado, apoyos y efectos tridimensionales.
- Hacer perfiles de identificación con el operador nuevo y comparar la misma
  selección de observaciones con/sin transiciones. No se puede prometer que
  incluirlas vuelva identificable cualquier relieve.
- Validar con datos experimentales existentes y geometría/relieve documentados,
  si se obtiene una fuente elegible. No hace falta fabricar para buscar esa vía.

La señal RMS de 0.18 µm de una campaña anterior no es una tolerancia universal.
Las señales estructurales del orden de nanómetros exigen otro presupuesto de
error; este paquete no certifica su resolución. Tampoco actualiza S27 a
“resuelto” por haber instalado un solver o por analizar tres fases.

ARCHIVOS
resultados_directos.csv: respuestas y controles por configuración.
AUDITORIA_OBJETIVOS.json: cifras, fuentes y comprobaciones.
diagnostico_sin_fabricacion.png: resultados y alcance.
public_data_screening.csv/json: cribado y motivos de elegibilidad.
updated_contact/: estados, matrices locales y registros de ejecución.
calculix_crosscheck/: entradas y salidas originales del solver independiente.
source_snapshot/: código final y requirements_sin_fabricacion.txt.

REPRODUCIR LOS NUEVOS CASOS BILATERALES EN UNA CARPETA VACÍA
python fe2d/run_bilateral_objectives.py --out RUTA_NUEVA
El script genera 19 configuraciones y conserva fallos si los hay. Los caches
grandes se conservan localmente y se omiten del ZIP compacto. Por ello el ZIP
incluye evidencia y código para regenerarlos, no todos los caches necesarios
para ejecutar la auditoría histórica sin recálculo. Las entradas de CalculiX
son autónomas; requieren el ejecutable portátil documentado en download_receipt.

FUENTES
CalculiX oficial y manual 2.23: https://www.dhondt.de/
Código/binario usado: https://github.com/calculix/CalculiX-Windows
Datos públicos: https://doi.org/10.18419/DARUS-5760
Fuentes metodológicas de engranajes ya descargadas en la biblioteca:
https://doi.org/10.3390/machines9100223
https://ntrs.nasa.gov/citations/19930019222
'''
    (ROOT/'ESTADO_SIN_FABRICACION.txt').write_text(description,encoding='utf-8')
    fig,ax=plt.subplots(1,3,figsize=(14,4.2))
    for phase,label in zip(phases,['Entry','Interior','Exit']):
        rr=[best(phase,s) for s in [.04,.02,.01]]
        ax[0].plot([r['step_mm'] for r in rr],[r['approach_um'] for r in rr],'o-',label=label)
    ax[0].invert_xaxis();ax[0].set_xlabel('Contour step (mm)');ax[0].set_ylabel('Approach (micrometres)');ax[0].set_title('Bilateral contact: refinement');ax[0].legend(fontsize=8)
    base=[r for r in allf if not r['two_pass'] and not r['reverse'] and r['case']=='nominal' and r['step_mm']==.02]
    for i,phase in enumerate(phases):
        one=next((r for r in base if r['phase']==phase),None)
        if one:ax[1].scatter(i-.1,max(one['opposite_direction_penetration_um'],1e-10),c='tab:red',marker='x',label='One pass' if i==0 else None)
        two=best(phase,.02);ax[1].scatter(i+.1,max(two['opposite_direction_penetration_um'],-two['minimum_researched_gap_um'],1e-10),c='tab:blue',label='Two passes' if i==0 else None)
    ax[1].axhline(.001,color='gray',ls='--',label='1 nm check');ax[1].set_yscale('log');ax[1].set_xticks(range(3),['Entry','Interior','Exit']);ax[1].set_ylabel('Penetration (micrometres)');ax[1].set_title('Both directions, step 0.02 mm');ax[1].legend(fontsize=7)
    for step in [.02,.01]:
        ss=[r for r in contrasts if r['step_mm']==step]
        ax[2].plot([r['phase'] for r in ss],[r['geometry_dedendum_contrast_um'] for r in ss],'o--',label=f'{step:g} mm')
    ax[2].set_xlabel('Selected mesh phase');ax[2].set_ylabel('Combined minus addendum (micrometres)');ax[2].set_title('Actual relief geometry; not inverse recovery');ax[2].legend(fontsize=8)
    for aa in ax:aa.grid(alpha=.25)
    fig.suptitle('Declared virtual geometry, selected phases: numerical verification',fontsize=12)
    fig.tight_layout();fig.savefig(ROOT/'diagnostico_sin_fabricacion.png',dpi=160);plt.close(fig)
    snapshot=ROOT/'source_snapshot';snapshot.mkdir(exist_ok=True)
    names=['run_fe2d.py','pilot_surface_contact.py','updated_surface_contact.py','relieved_surface_geometry.py','crosscheck_calculix.py','run_bilateral_objectives.py','extend_surface_objectives.py']
    for name in names:shutil.copy2(GEARS/'fe2d'/name,snapshot/name)
    requirements=[n+'=='+importlib.metadata.version(n) for n in ['numpy','scipy','gmsh','scikit-fem','meshio','matplotlib','shapely']]
    (ROOT/'requirements_sin_fabricacion.txt').write_text('\n'.join(requirements)+'\n')
    attribution='Bauer, Christian Johannes Eugen; Nowinski, Simon (2026). Replication Data for: Transmission Error Compensation for Industrial Robots Using Fourier Series. DaRUS, V1. DOI:10.18419/DARUS-5760. CC BY 4.0, https://creativecommons.org/licenses/by/4.0/. Two original CSV samples are redistributed unchanged; see downloads.json and darus_metadata.json. They are not a validation of spur-gear relief inversion.\n'
    (ROOT/'public_data/ATTRIBUTION.txt').write_text(attribution,encoding='utf-8')
    omitted=[];files=[]
    for f in ROOT.rglob('*'):
        if not f.is_file():continue
        rel=f.relative_to(ROOT)
        if rel.parts[0]=='calculix' or f.name in ['solver_zip.zip','solver_manual.pdf','EVIDENCIA_SIN_FABRICACION.zip','SHA256SUMS.json','CACHES_OMITIDOS_DEL_ZIP.json'] or '__pycache__' in rel.parts:continue
        if '_body' in f.stem and f.suffix=='.npz':omitted.append(dict(file=str(rel),bytes=f.stat().st_size));continue
        files.append(f)
    (ROOT/'CACHES_OMITIDOS_DEL_ZIP.json').write_text(json.dumps(omitted,indent=2))
    files.append(ROOT/'CACHES_OMITIDOS_DEL_ZIP.json')
    hashes={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    (ROOT/'SHA256SUMS.json').write_text(json.dumps(hashes,indent=2));files.append(ROOT/'SHA256SUMS.json')
    target=ROOT/'EVIDENCIA_SIN_FABRICACION.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for f in files:z.write(f,'gears_inversion/objetivos_numericos_2026-11-01/'+str(f.relative_to(ROOT)).replace('\\','/'))
        for name in names:z.write(GEARS/'fe2d'/name,'gears_inversion/fe2d/'+name)
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
    print('closed',target,'bytes',target.stat().st_size,'sha256',hashlib.sha256(target.read_bytes()).hexdigest())


if __name__=='__main__':main()
