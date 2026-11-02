# Auditoría independiente y cierre científico de la versión 12

El artículo se reescribe como una contribución teórica y computacional sobre observabilidad condicionada al operador mecánico. Los antecedentes inversos, las hipótesis de cumplimiento fijo y la diferencia entre sensibilidad, identificación y reconstrucción física quedan explícitos. Este informe contiene el historial de revisión; ese historial no estructura la narración del artículo.

## Hallazgos que determinan las conclusiones

La señal FE que aísla el dedendum es combinado menos addendum: 0.178987 µm RMS. La señal analítica comparable es 0.196589 µm; su relación es 0.910464. La antigua relación de nueve veces mezclaba las dos modificaciones y se elimina de las conclusiones.

La auditoría independiente es más restrictiva que una simple corrección del cociente: la estimación de profundidad próxima a la real no demuestra recuperación. En el ajuste archivado, el inicio estimado 0.300621 queda por debajo del primer contacto cargado 0.303605; ambas columnas del Jacobiano del dedendum son nulas. Los 26 arranques, el modelo restringido y los perfiles muestran que el dedendum puede eliminarse sin penalización relevante. El artículo declara que ese ensayo no identifica su presencia ni su geometría.

La secuencia P1 h=0.50, 0.35, 0.25 mm estabiliza el contraste aislado, pero no la onda completa ni la inversión. Sobre las mismas 102 fases, la onda combinada cambia 0.141289 y 0.217928 µm RMS respecto de la malla gruesa, mientras el contraste aislado cambia 0.001060 y 0.001145 µm. La cancelación de errores comunes explica por qué un contraste estable no constituye un certificado de convergencia inversa.

## Nuevos controles de la segunda evaluación

| Observación | Evidencia final | Alcance que se declara |
|---|---|---|
| Interfaz de contacto | S19: tres pasos de presión, P2, cuerpos idénticos y 24 fases comunes elegibles | Sensibilidad de interfaz en un subconjunto; no convergencia de toda la inversión P1 |
| Retirada física de material | S20: contorno realmente desplazado, matriz elástica reensamblada, tres mallas, dos profundidades y ocho fases | Prueba de la hipótesis de cumplimiento fijo; no validación de reconstrucción física |
| Máscara angular | S18: 102, 98, 94 y 90 fases; ocho arranques por modelo y máscara | El modelo sin dedendum conserva el mismo objetivo; las 18 fases no resueltas no se inventan |
| Ondas y residual creciente | Figura 8 y S17: ondas centradas y residuos sobre la misma máscara | Se separa cancelación del contraste de convergencia del observable |
| Novedad | Introducción y discusión confrontan síntesis inversa y rodadura doble flanco | Aporte de soporte, KKT acoplado, transición débil y espacio nulo; no invención de la inversión de engranajes |
| Bibliografía | 41 DOI en Crossref, catálogo ISO, contraste editorial específico | Existencia y metadatos verificados; no se afirma lectura íntegra de 42 textos |
| Orden y formato | 42 referencias por primera aparición, cinco destacados Word ≤85 caracteres | Comprobación automática y revisión visual de los documentos |
| Reproducibilidad | Paquete v12, registros, código, metadatos y manifiesto SHA-256 | El identificador público se confirma en el recibo de publicación; v10 permanece histórico |

### Interfaz

Se seleccionan 24 de las 68 fases interiores cuyas trazas candidatas quedan por encima del empalme de raíz de ambos cuerpos. Se conserva la misma geometría poligonal, los mismos nodos de los cuerpos y el mismo objetivo local de malla. La carga se aproxima mediante sombreros de presión y la separación mediante su promedio consistente. No se confunde este ensayo P2 con la inversión original P1.

| Paso mm | Señal aislada RMS µm | Cambio señal % | Cambio onda combinada RMS µm |
|---|---|---|---|
| 0.04 | 0.083207657 | +0.000000 | 0.000000000 |
| 0.02 | 0.085275342 | +2.484970 | 0.006037811 |
| 0.01 | 0.085008425 | -0.313006 | 0.000716017 |

### Geometría físicamente modificada

La región retirada queda fuera de todas las estaciones de contacto candidatas de las ocho fases seleccionadas, no sólo fuera de sus contactos cargados. Esto permite mantener las normales y la matriz de carga exactamente iguales y aislar el cambio de flexibilidad. El contorno de los flancos superiores y su empalme de raíz se desplaza hacia el interior; una deformación armónica adapta la malla. Se reensambla la matriz de elasticidad P2 para cada profundidad. Este ensayo controlado no incluye relieve de addendum. El área retirada es positiva y no hay elementos invertidos. El parámetro de profundidad conserva la definición de relieve cuadrático del modelo; no representa una medición metrológica del punto más profundo de un filete manufacturado.

| h mm | Profundidad µm | Diferencia centrada RMS µm | Cambio medio de aproximación µm | Cambio relativo máximo H |
|---|---|---|---|---|
| 0.5 | 10 | 0.000406279 | 0.002291135 | 0.00023805741 |
| 0.5 | 50 | 0.002110214 | 0.011855032 | 0.0012360197 |
| 0.35 | 10 | 0.000399676 | 0.002233223 | 0.0002334413 |
| 0.35 | 50 | 0.002078703 | 0.011572922 | 0.0012135826 |
| 0.25 | 10 | 0.000396548 | 0.002205949 | 0.00023165 |
| 0.25 | 50 | 0.002063475 | 0.011437029 | 0.0012046369 |

El cambio no nulo verifica una limitación esencial de la teoría: un relieve fuera del contacto puede modificar la respuesta por su efecto estructural cuando el cumplimiento cambia. Su pequeña amplitud en este ensayo no demuestra invisibilidad física universal. La discretización del contorno y la reducción a ocho fases continúan limitando esa interpretación.

## Verificación y procedencia

Se comprobaron 72 registros de interfaz y 72 registros de geometría modificada, sin claves duplicadas. Los RMS publicados se recalcularon directamente desde los registros. Área mínima retirada: 0.15350682 mm²; razón mínima de área firmada de elementos: 0.78487038. Residual máximo de fuerza del control geométrico: 3.64e-12 N; residual máximo de contacto: 2.08e-17 mm.

Las 40 pruebas unitarias pasan. Se conserva el control de métricas de los 1800 ajustes históricos, sin afirmar que se hayan vuelto a ejecutar las 1800 optimizaciones. Los nuevos ajustes de máscara y los nuevos controles FE sí se ejecutaron. Los ensayos exploratorios que fallaron las comprobaciones de cobertura de traza o proyección de contorno se conservaron localmente como pilotos incompletos y se excluyeron del paquete reproducible final. La selección de fases y el emparejamiento de segmentos del contorno se corrigieron antes de los registros verificados.

Los datos bibliográficos descargados se incluyen para auditar el contraste por DOI. La ficha ISO confirma edición y alcance, no la implementación integral de su texto normativo. La guía general de Elsevier confirma 3–5 destacados y un máximo de 85 caracteres; la guía específica de MMT no fue accesible por respuesta 403 y no se le atribuyen requisitos adicionales no verificados.

## Límites que no se presentan como resueltos

No se demuestra convergencia de la inversión de ciclo completo, recuperación física del dedendum, convergencia de las fases de esquina ni fidelidad tridimensional de un perfil manufacturado. Las cuatro formulaciones siguen excediendo el objetivo investigativo del 5% en los doce valores externos. No están disponibles las ondas completas, el CAD y las condiciones de soporte originales del benchmark, por lo que no se inventa una validación puntual ni una descomposición causal de su discrepancia. Las precisiones submicrométricas son condicionales al operador y al ruido supuesto.

La versión terminada sostiene una contribución científica delimitada y verificable. Las objeciones que requerirían nuevos datos experimentales o un nuevo generador físico de ciclo completo se reflejan en el alcance de las conclusiones; no se sustituyen por afirmaciones de aceptación editorial.