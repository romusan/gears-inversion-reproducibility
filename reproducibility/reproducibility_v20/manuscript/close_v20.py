"""Spanish disposition of the review; no unperformed experiment is claimed."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'revision_20_2026-11-01'
def main():
    a=json.loads((OUT/'analysis_v20.json').read_text());cx=a['calculix'];assert (OUT/'audit_v20.json').exists() and (OUT/'visual_QA_v20.json').exists()
    sel=a['fine_selected'];bi=next(r for r in sel if r['design']=='interior' and not r['restricted']);bm=next(r for r in sel if r['design']=='with_transitions' and not r['restricted'])
    text='''RESPUESTA AL DIAGNÓSTICO DE V19 — V20

PRIORIDAD A. CONECTAR EL TEOREMA CON EL CONTACTO ACTUALIZADO
Hecho en Discusión, resumen y conclusiones. Se evita una inferencia incorrecta:
violar las hipótesis de una condición suficiente elimina su garantía, pero no
demuestra el converso. El teorema no predice por sí solo que aparezca información
ni dónde aparecerá. Los ajustes próximos a la verdad son resultados numéricos
condicionales de otro operador, no una prueba de identificación física o global.

PRIORIDAD B. DISEÑO MIXTO E INICIOS
Se añadieron cuatro inicios completos y dos restringidos por diseño en la
referencia 0.04/0.50 mm. Junto con los controles preservados, cada diseño cuenta
con cinco intentos completos y tres restringidos. Son 12 intentos nuevos y
16 intentos finos en total. Se conservaron todos los registros y se repitieron
dos ciclos completos desde estados de contacto fríos en los mejores ajustes.
El límite por intento, escalas, cotas y tolerancias se declaran en el artículo.
La Tabla S37 lista todos los intentos, sin seleccionar por cercanía a la verdad.
'''
    text+=f"\nError de campo normal: interior {bi['normal_relief_RMS_um']:.6g} µm; mixto {bm['normal_relief_RMS_um']:.6g} µm.\n"
    text+='''El resultado negativo sobre error de campo se hizo explícito. La Tabla S38
prueba las hipótesis propuestas con diferencias centrales a dos tamaños de paso,
eliminación del addendum como nuisance y controles con offset estimado/fijado.
Los dos criterios locales reportados favorecen al diseño mixto; el offset reduce
su información relativa, pero no invierte ese orden. No se sostiene una explicación
simple de dilución por addendum. La proyección de la discrepancia determinística
aproxima la dirección y magnitud del sesgo de dedendum en los dos diseños.
Este es un diagnóstico local de una verdad virtual, no una demostración causal
exclusiva, un mapa global o una evaluación de recuperación bajo ruido añadido.

PRIORIDAD C. CONTRASTE CON CALCULIX
Se ejecutaron perfiles addendum-only y combinados, no solamente perfiles nominales.
El control de ciclo incluye f=0.225 (índice 27, antes omitido) y f=0.50. Comparte
contornos y mallas corporales con el generador; ocho columnas de compliance por
cuerpo verifican la transferencia. Se auditan equilibrio, deformación plana,
presión/contacto, reproyección bilateral y solape de polígonos desde los FRD.
'''
    e=next(r for r in cx['comparisons'] if r['folder']=='calculix_cycle_crosscheck' and r['phase']==.225);o=cx['offset_free_two_phase']
    text+=f"\nContraste puntual en f=0.225: propio {e['own_contrast_um']:.8g} µm; CalculiX {e['calculix_contrast_um']:.8g} µm; diferencia {e['difference_um']:.8g} µm.\nContraste de dos fases libre de offset constante: propio {o['own_two_phase_contrast_um']:.8g} µm; CalculiX {o['calculix_two_phase_contrast_um']:.8g} µm; diferencia {o['difference_um']:.8g} µm.\nEstados finales nuevos aceptados: {len(cx['results'])}; entradas no terminadas retenidas: {len(cx['failed_or_unfinished'])}.\n"
    text+='''Se distingue aproximación absoluta, contraste puntual y contraste entre dos
fases. Ninguno equivale al RMS de un ciclo completo. También se reporta la
penetración nodal del contacto mortar débil; estos controles no certifican el
efecto estructural separado de 0.4–2.1 nm ni validación física.

Una corrida fina con incrementos pequeños agotó 600 segundos; su par fue
interrumpido antes del equilibrio final. Las salidas parciales quedan preservadas.
Se repitieron los pares con un incremento inicial completo y se añadió un control
en la misma malla para cuantificar el efecto de esa pauta. La Tabla S39 y los
registros contienen las dos pautas; no se aceptó como resultado la corrida truncada.

OTRAS CORRECCIONES IMPLEMENTADAS
- Se retiró la afirmación de que dos mallas cumplen un criterio de refinamiento.
  Se reporta 0.0389 frente a 0.18 µm como comparación de escalas declarada,
  sin orden de convergencia ni cota de error al continuo.
- S29 incluye porcentajes de flag junto a los conteos originales: el control
  IID profundo tiene 4/200 = 2.0% de falsa alarma empírica bajo ese protocolo.
- Los resultados históricos, 15 ecuaciones nativas, 48 referencias y CRediT
  confirmado por los autores se preservan. Las tablas nuevas son S37–S39.

NO REALIZADO NI PRESENTADO COMO RESUELTO
- Campaña de inversión con ruido σ=0.1 µm para el operador de contacto móvil.
- Tercer nivel del generador de ciclo COMPLETO. Los controles CalculiX a
  0.01/0.25 mm son fases seleccionadas y no sustituyen ese tercer ciclo.
- Calibración de cobertura del umbral de perfil Δχ²=3.841. El bootstrap de
  medianas del efecto de ganancia no calibra intervalos de parámetros.
- Diseño óptimo de carga que barra el soporte, TOST y mapa global de
  identificabilidad. No se afirma optimalidad universal, equivalencia o unicidad.
- Validación experimental con relieve certificado y TE medido.
- Depósito público actual con DOI y envío editorial. No se han efectuado.

ARCHIVOS VIGENTES
MMT_manuscript_Q1_revision_v20_clean.docx
MMT_supplementary_Q1_revision_v20.docx
Highlights_v20.docx
Cover_letter_MMT_v20.docx
MMT_reproducibility_v20.zip
MMT_submission_kit_v20.zip

Las versiones anteriores son antecedentes preservados; no mezclar sus documentos
con los de v20. Preparar este paquete no garantiza aceptación editorial.
'''
    (OUT/'RESPUESTA_DIAGNOSTICO_v19.txt').write_text(text,encoding='utf-8')
    (OUT/'LEER_PRIMERO_ENVIO_MMT.txt').write_text('''VERSIÓN VIGENTE: v20 — 1 de noviembre de 2026

El kit contiene artículo limpio, suplemento S1–S39, Highlights, carta y evidencia.
Leer RESPUESTA_DIAGNOSTICO_v19.txt para lo incorporado y lo que sigue abierto.
El archivo de reproducibilidad preserva v19 e incluye los nuevos datos crudos,
intentos de ajuste, ejecuciones incompletas, auditorías y construcción documental.

No se han asignado DOI ni enviado archivos a la revista. Las comprobaciones son
numéricas y condicionales; no se afirma reconstrucción física ni cobertura de
parámetros calibrada. Usar la declaración de datos que corresponda al depósito real.
''',encoding='utf-8')
    if (OUT/'ENTREGA_VERIFICADA_v20.json').exists():
        (ROOT/'LEER_PRIMERO.md').write_text('''# Estado actual de gears_inversion

**Versión vigente: v20, 1 de noviembre de 2026.**

- [Artículo editable](revision_20_2026-11-01/MMT_manuscript_Q1_revision_v20_clean.docx).
- [Paquete completo](revision_20_2026-11-01/MMT_submission_kit_v20.zip).
- [Respuesta al diagnóstico y límites](revision_20_2026-11-01/RESPUESTA_DIAGNOSTICO_v19.txt).
- [Instrucciones](revision_20_2026-11-01/LEER_PRIMERO_ENVIO_MMT.txt).
- [Verificación](revision_20_2026-11-01/ENTREGA_VERIFICADA_v20.json).

La v20 añade cinco inicios finos por diseño, diagnóstico de offset y discrepancia,
y contrastes pareados con CalculiX que incluyen una estación antes omitida.
Preserva los 720 datos virtuales y seis controles de cierre de v19, las 15
ecuaciones nativas y las 48 referencias. Las versiones anteriores son antecedentes;
no mezclar documentos. La v15 limpia perdió ecuaciones y no debe usarse.

No se afirma validación física, unicidad global, cobertura calibrada de parámetros
ni convergencia de la inversión al continuo. No se ha enviado el artículo ni
depositado públicamente la versión actual con DOI. La respuesta al diagnóstico
identifica los experimentos adicionales todavía no realizados.
''',encoding='utf-8')
    print('Respuesta y alcance v20 documentados')
if __name__=='__main__':main()
