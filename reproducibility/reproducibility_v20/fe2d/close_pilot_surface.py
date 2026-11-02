"""Write the Spanish pilot receipt and portable evidence bundle after audit."""
import hashlib,importlib.metadata,json,shutil,zipfile
from pathlib import Path
import pilot_surface_contact as p


def main():
    out=p.OUT;a=json.loads((out/'audit.json').read_text());rr=a['convergence']
    table=['fase | acercamiento nominal (um) | cambio ultimo refinamiento (um) | contraste dedendum (um) | error contacto deformado (um) | fuerza par extra (%) | fuerza punta/esquina (%)']
    for r in rr:
        table.append(f"{r['phase']:.6f} | {r['approach_fine_um']:.6f} | {r['last_approach_change_um']:.6f} | {r['gap_law_dedendum_difference_fine_um']:.6f} | {r['deformed_contact_gap_error_um']:.6f} | {100*r['extra_pair_force_fraction']:.3f} | {100*r['true_tip_or_corner_force_fraction']:.3f}")
    interior=next(r for r in rr if r['phase']==.5)
    text=f'''PILOTO DE CONTACTO SOBRE CONTORNOS — 2026-11-01
Estado: EXPLORATORIO. NO INCORPORAR COMO RESULTADO VALIDADO DEL PAPER.

Se ejecutaron cinco fases, tres refinamientos y tres casos por configuración
(sin relieve, addendum, ambos): 15 configuraciones y 45 equilibrios. Se hicieron
además cinco comparaciones con las ventanas nominales del código anterior.
El manuscrito y el paquete de envío v18 no se modificaron.

QUÉ SE IMPLEMENTÓ
Contornos de dientes completos en la zona de engrane, incluidos segmentos de
punta y transiciones aproximadas de raíz. Búsqueda nodo-segmento sobre dichos
contornos, con normales dependientes de la fase. La presión se transmite a los
dos sólidos FE mediante fuerzas nodales e interpolación en el segmento maestro.
La restricción de carga usa el momento real respecto del centro del engranaje 2,
no una fuerza normal única supuesta sobre la línea de acción. El multiplicador
conjugado es radio base por acercamiento angular; no es TE centrado del ciclo.
Se impone 300 Nm al engranaje 2; el momento de reacción del engranaje 1 se registra.
No se sumó una compliance de Hertz o de viga al continuo FE.

El solve conserva elasticidad de pequeñas deformaciones y normales/puntos de
contacto nominales durante cada equilibrio. Una búsqueda posterior sobre las
superficies deformadas comprueba la insuficiencia de esa linealización. No se ha
implementado todavía la iteración geométrica completa durante el contacto.

RESULTADOS FINOS (son contrastes de aproximación, NO RMS de TE del ciclo)
{chr(10).join(table)}

En la fase interior 0.5, el modelo de ventanas nominales da
{interior['nominal_window_baseline_um']:.6f} um y el piloto {interior['approach_fine_um']:.6f} um:
la diferencia es {100*interior['difference_vs_nominal_window_relative']:.3f} %.
Esto comprueba proximidad en un caso interior; no establece equivalencia total.

El contraste dedendum se define como aproximación con ambos relieves menos
aproximación con addendum solo, en la MISMA fase. Se usó la ley p=2, xi=u/u_tip,
theta=(0.020,0.75,0.010,0.50), aplicada únicamente como gap adicional del piñón.
En la punta se prolonga constantemente el valor de addendum: es una hipótesis
de gap, no una geometría mecanizada de punta. Compliance y normales no cambian
con el relieve. No se infiere recuperación de parámetros a partir del contraste.

VEREDICTO
La búsqueda permite activar un par que las ventanas nominales excluyen cerca
de entrada/salida. Eso no demuestra que se haya validado contacto de esquina.
El error posterior de ubicación del contacto llega a superar el contraste
del dedendum. El buen equilibrio algebraico no subsana esa deficiencia física.
Por ello no se promueven estas cifras al manuscrito y no se realiza una nueva
inversión con ellas. Tampoco se presenta un ciclo completo, un experimento real
ni evidencia nueva de identificación única. Una diferencia nula en las fases de
salida muestreadas no implica invisibilidad global del dedendum.

CONTROL DE CALIDAD Y CORRECCIÓN
Se verificaron las 45 soluciones guardadas (torque, no negatividad y condiciones
de contacto), un caso analítico de reparto 2:1 y los brazos de palanca mediante
perturbación angular independiente. También se revisaron simetría de compliance,
residuo elástico, trabajo/energía y sensibilidad al refinamiento.
Error máximo de torque: {a['maximum_torque_residual']:.3g}; residuo elástico máximo:
{a['maximum_elastic_residual']:.3g}; error máximo de energía: {a['maximum_energy_residual']:.3g}.

La primera etiqueta de punta contaba como punta el segmento de flanco que parte
de su vértice. Se corrigió comprobando AMBOS extremos del segmento. Los datos
brutos se conservan para trazabilidad. Para conclusiones se deben usar
campaign_verified.json y classification_*.npz; las máscaras edge de los NPZ
originales y las etiquetas de campaign.json anteriores a la auditoría quedan
superadas. La corrección es geométrica y no altera fuerzas, gaps ni matrices.
Los hashes son del código final auditado, que incorpora esa corrección y métricas
adicionales. La auditoría reconstruye los candidatos y verifica los gaps contra
los guardados antes de volver a resolver las 45 condiciones de equilibrio.

SIGUIENTE PASO TÉCNICO NECESARIO
1. Iterar búsqueda, proyección y normales sobre las superficies deformadas y
   actualizar la transmisión de fuerzas y el brazo de palanca en cada iteración.
2. Comprobar independencia al intercambio maestro/esclavo; el contacto actual
   es de una pasada y la entrada/salida aún muestra sesgo de discretización.
3. Definir radio real de punta y fillete generado, o hacer una campaña declarada
   de sensibilidad geométrica. Una punta aguda no permite validar presión pico.
4. Reducir errores de geometría/contacto y discretización por debajo de la señal
   de interés; después repetir contrastes de relieve con geometría modificada.
5. Sólo entonces ampliar el ciclo y hacer perfiles de identificación con el
   mismo conjunto de observaciones y parámetros de calibración explícitos.

REFERENCIAS METODOLÓGICAS (ya descargadas en la biblioteca de referencias)
Bruzzone et al. (2021), Machines 9, 223. Búsqueda geométrica y actualización
de contactos: https://doi.org/10.3390/machines9100223
Lin et al. (1993), NASA-TM-106174, contacto extendido fuera del engrane nominal:
https://ntrs.nasa.gov/citations/19930019222
Ye y Tsai (2016), MMT 97, 190–214, contacto de esquina:
https://doi.org/10.1016/j.mechmachtheory.2015.11.008
De esta última referencia sólo se dispone del resumen verificado, no de su
texto completo; no se atribuyen ni implementan ecuaciones suyas no leídas.

ARCHIVOS Y REPRODUCCIÓN
summary.csv: cifras finas y cambios de refinamiento.
audit.json: comprobaciones, decisiones y supuestos.
campaign_verified.json: los 15 registros auditados, con sus tres casos.
pilot_diagnostics.png: comparación y limitación de contacto deformado.
NPZ: matrices/gaps/fuerzas, posiciones, normales y clasificación auditada aparte.
development_initial/: ensayos de desarrollo preservados, excluidos del ZIP final.

Ejecutar desde fe2d con las dependencias indicadas en requirements_pilot.txt:
python run_pilot_surface_campaign.py
python analyze_pilot_surface.py
python close_pilot_surface.py
El cierre vuelve a generar los documentos y el ZIP, no el manuscrito v18.
'''
    (out/'LEER_PRIMERO_PILOTO.txt').write_text(text,encoding='utf-8')
    req=[]
    for name in ['numpy','scipy','matplotlib','gmsh','scikit-fem','meshio']:
        req.append(name+'=='+importlib.metadata.version(name))
    (out/'requirements_pilot.txt').write_text('\n'.join(req)+'\n')
    shutil.copy2(Path(__file__),out/Path(__file__).name)
    hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()
            if f.is_file() and f.name not in ['SHA256SUMS.json','piloto_contacto_evidencia.zip','audit_console.txt']}
    (out/'SHA256SUMS.json').write_text(json.dumps(hashes,indent=2))
    target=out/'piloto_contacto_evidencia.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for f in out.iterdir():
            if f.is_file() and f!=target and f.name!='audit_console.txt':z.write(f,f.name)
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
    print(target,'bytes',target.stat().st_size,'sha256',hashlib.sha256(target.read_bytes()).hexdigest())


if __name__=='__main__':main()
