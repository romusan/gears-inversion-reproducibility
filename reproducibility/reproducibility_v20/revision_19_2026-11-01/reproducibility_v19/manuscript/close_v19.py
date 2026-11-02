"""Explain final scope in Spanish and identify the current release."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'revision_19_2026-11-01'
def main():
    a=json.loads((OUT/'analysis_v19.json').read_text());q=json.loads((OUT/'audit_v19.json').read_text());assert (OUT/'visual_QA_v19.json').exists()
    inv=a['inverse'];failed=sum(not r.get('success',False) for r in inv)
    text='''CIERRE DEL PROYECTO SIN FABRICACIÓN — VERSIÓN 19

QUÉ INVESTIGAMOS
Queremos determinar qué partes del relieve de un engranaje pueden inferirse
a partir del error de transmisión, y cuándo un buen ajuste de esa señal permite
recuperar el perfil. Son preguntas diferentes: detectar un efecto, ajustar la
señal y recuperar de manera única la geometría no son equivalentes.

OBJETIVOS ALCANZADOS
1. Resultado matemático: condición suficiente de invisibilidad del relieve
   fuera del soporte cargado bajo geometría y rigidez fijas, también con
   acoplamiento elástico entre pares de dientes.
2. Diagnóstico numérico: sensibilidad, perfiles de objetivo, alternativas sin
   dedendum y controles sintéticos de ruido, ganancia, muestreo y formulación.
   Se conservan los 1100 casos de estrés anteriores, incluidos los fallidos.
3. Nuevo problema directo: tres perfiles virtuales, dos mallas y 120 estaciones
   por perfil. Son 720 observaciones, más seis controles de cierre. Las 18
   estaciones antes excluidas están resueltas en este operador nuevo.
4. Auditoría de 726 estados: reproyección por ambos sentidos, no penetración,
   equilibrio, energía positiva, consistencia elástica y solape de contornos.
5. Comprobación con otro código: seis controles nominales seleccionados con
   CalculiX. No son una validación independiente del ciclo o del problema inverso.
6. Comparación inversa: diseños de igual tamaño (30 observaciones), con y sin
   las estaciones antes excluidas; inversores analítico y de contacto móvil;
   contraste de mallas y ajuste restringido sin dedendum. Todos los intentos se
   conservan. El inversor móvil conserva rigidez nominal; el generador sí cambia
   la geometría y reensambla la rigidez. Esa discrepancia está cuantificada.

RESULTADOS NUEVOS
'''
    fine=a['cycle'][1]
    text+=f"Señal aislada del dedendum, centrada: {fine['dedendum_centered_RMS_um']:.6g} µm RMS.\nDiferencia entre mallas de esa señal: {a['dedendum_contrast_refinement_RMS_um']:.6g} µm RMS.\nDiferencia entre mallas del TE combinado: {a['cycle_centered_refinement_RMS_um']['combined']:.6g} µm RMS.\nNuevos intentos de inversión: {len(inv)}; con indicador de no convergencia: {failed}.\n\n"
    text+=f"En las 18 estaciones antes excluidas, el cambio entre mallas del TE centrado es {a['transition_centered_refinement_RMS_um']['combined']:.6g} µm RMS; el cambio de aproximación sin centrar es {a['transition_raw_refinement_RMS_um']['combined']:.6g} µm RMS. Solo el primero queda por debajo de la escala histórica de 0,18 µm. Es un criterio empírico de dos mallas, no una cota certificada de error.\n\n"
    for name in ['inverse_reference_s0.08.json','inverse_reference_s0.04.json','inverse_analytic.json']:
        for design in ['interior','with_transitions']:
            rr=[r for r in inv if r['file']==name and r['design']==design and not r['restricted'] and 'cost' in r]
            b=min(rr,key=lambda r:r['cost']);th=b['theta'];text+=f"{name}, {design}: mejor θ={th}; RMS ajuste={b['residual_RMS_um']:.6g} µm; RMS ciclo={b['full_cycle_prediction_RMS_um']:.6g} µm; indicador convergencia={b['success']}.\n"
    text+='''
QUÉ NO PODEMOS AFIRMAR
No hemos demostrado recuperación física de relieve certificado, unicidad global
de los parámetros, convergencia de la inversión al continuo, cobertura estadística
calibrada ni validez tridimensional. La convergencia del optimizador es una bandera
numérica: distintos perfiles pueden dar residuos próximos. Los controles de malla
y de otro código no sustituyen mediciones físicas. El estudio deja esos límites
explícitos y no necesita inventar una fabricación o un ensayo para cerrarse como
trabajo computacional.

La búsqueda de datos públicos revisó ocho pistas y descargó dos archivos de TE
de un repositorio; no se verificó un par utilizable de TE y relieve certificado
para este problema. No se reutilizaron como si fueran esa validación. El registro
de selección y las atribuciones se conservan en la evidencia mecánica adjunta.

DOCUMENTOS
MMT_manuscript_Q1_revision_v19_clean.docx — artículo vigente.
MMT_supplementary_Q1_revision_v19.docx — Tablas S1–S36.
Highlights_v19.docx — cinco puntos, cada uno con 85 caracteres o menos.
Cover_letter_MMT_v19.docx — carta.
MMT_reproducibility_v19.zip — evidencia, código y manifiesto de integridad.
MMT_submission_kit_v19.zip — paquete de carga con los cinco archivos anteriores.

Los PDF en render_main/render_supplement son copias de lectura y revisión visual.
Se conservaron las 15 ecuaciones nativas y las tablas numéricas históricas.
CRediT conserva la confirmación de los tres autores para los mismos roles.

ESTADO EDITORIAL
Esta preparación no envía el artículo a la revista. Tampoco publica datos ni
asigna DOI. El repositorio público v13 es histórico y no contiene la evidencia
posterior. El depósito público de la versión actual y la carga editorial quedan
como gestiones externas. La aceptación y el nivel editorial no están garantizados.
'''
    (OUT/'CIERRE_VERIFICADO_v19.txt').write_text(text,encoding='utf-8')
    (OUT/'LEER_PRIMERO_ENVIO_MMT.txt').write_text('''VERSIÓN VIGENTE: v19 — 1 de noviembre de 2026

Utilizar únicamente los archivos de submission_kit_v19 o su ZIP homónimo.
El paquete contiene artículo limpio, suplemento, Highlights, carta y archivo
de reproducibilidad. El manifiesto CONTENIDO_Y_SHA256.json verifica los cinco.
Los estados y parámetros computados, incluso fallos, están en la evidencia.

Leer CIERRE_VERIFICADO_v19.txt para el alcance y las limitaciones.
La v18 y las anteriores son antecedentes; no mezclar sus tablas/documentos
con el artículo actual. El conjunto histórico de 102 estaciones no se alteró:
el ciclo completo es un experimento con otro operador.

Antes de una carga editorial, usar la declaración de datos que corresponde al
depósito real. No existe DOI asignado a esta versión. No se ha enviado el artículo.
''',encoding='utf-8')
    if (OUT/'ENTREGA_VERIFICADA_v19.json').exists():
        (ROOT/'LEER_PRIMERO.md').write_text('''# Estado actual de gears_inversion

**Versión vigente: v19, 1 de noviembre de 2026.**

- [Instrucciones de carga](revision_19_2026-11-01/LEER_PRIMERO_ENVIO_MMT.txt).
- [Cierre y objetivos alcanzados](revision_19_2026-11-01/CIERRE_VERIFICADO_v19.txt).
- [Artículo editable](revision_19_2026-11-01/MMT_manuscript_Q1_revision_v19_clean.docx).
- [Paquete completo](revision_19_2026-11-01/MMT_submission_kit_v19.zip).
- [Verificación de entrega](revision_19_2026-11-01/ENTREGA_VERIFICADA_v19.json).

La v19 incorpora un ciclo virtual completo de contacto bilateral: 720 observaciones
y seis controles de cierre, tres perfiles y dos mallas. Resuelve las 18 estaciones
antes omitidas en un operador nuevo y compara diseños inversos de igual tamaño.
Conserva los resultados negativos, el error entre mallas y la aproximación de rigidez
nominal del inversor. No demuestra recuperación física ni unicidad global.

Las carpetas anteriores son antecedentes inmutables. La v15 limpia perdió las
ecuaciones y no debe usarse; la v19 conserva las 15 ecuaciones OMML recuperadas.
No se ha realizado un envío editorial ni un depósito público actual con DOI.
La fabricación y la validación física quedan fuera del alcance acordado.
''',encoding='utf-8')
    print('Cierre v19 documentado')
if __name__=='__main__':main()
