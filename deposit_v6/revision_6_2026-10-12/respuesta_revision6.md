# Respuesta a la revisión de la v5

Se repitieron las ocho fases con desplazamientos cuadráticos y presión distribuida débil. El rango muestreado es 12.463291 µm, frente al rango lineal original 12.278 µm y al baseline en esas fases, 11.662 µm. La comparación con 10.527 µm es +18.394% y continúa siendo de ocho fases y de un operador con contactos de esquina omitidos; no se convierte en p-p físico certificado.
Las ocho matrices condensadas son definidas positivas. Se verificaron simetría, equilibrio elástico y de fuerza, contacto promediado y tangente por perturbación independiente. La desviación máxima del momento resultante respecto al torque nominal es 0.033321%; se conserva como diagnóstico de la normal fija, sin recalibrar rigidez ni cargas.

## Semillas, empates y bootstrap

| sd | σ µm | Par mejora % | Par empeora % | Empates exactos | Empates con tolerancia 1e-8 |
|---:|---:|---:|---:|---:|---:|
| 0.25 | 0.1 | 43 | 56 | 1 | 8 |
| 0.25 | 0.5 | 38 | 56 | 6 | 13 |
| 0.25 | 1 | 49 | 48 | 3 | 10 |
| 0.4 | 0.1 | 50 | 50 | 0 | 0 |
| 0.4 | 0.5 | 59 | 38 | 3 | 7 |
| 0.4 | 1 | 44 | 53 | 3 | 12 |

Las fracciones usan las 100 semillas por celda, incluidos los fallos. La comparación estricta puede contar diferencias del optimizador casi nulas; la tolerancia se muestra separadamente y está expresada en el error máximo de parámetros normalizado. No se equipara un extremo bootstrap en cero con equivalencia o cobertura de parámetros.

## Muestreo cada 0.21 grados

El periodo es 360/57=6.315789474°. Se recorre todo el intervalo de desfase [0,0.21°), conservando los 30 o 31 puntos que caen en el ciclo fijo. El baseline da un rango de p-p de 11.706350 a 11.955462 µm. Las representaciones de 3840, 7680 y 15360 nodos dan prácticamente el mismo intervalo. Este control no permite explicar 10.527 µm solo por el muestreo angular del baseline.
El interpolante lineal periódico de las ocho fases FE cuadráticas da 12.269918–12.442531 µm. Es un diagnóstico del interpolante, no un barrido FE directo. Ocho fases no resuelven una rampa de 0.02°; por ello sigue pendiente un ciclo FE angular denso, con contacto de esquina y convergencia propia, para decidir el efecto de muestreo físico.
El cálculo divide todos los desfases en intervalos cuyos límites son nudos desplazados y el cambio del número de muestras. Dentro de cada intervalo el rango de líneas afines es convexo; su máximo está en un extremo y el mínimo se obtiene por búsqueda ternaria de 70 pasos. No se selecciona un desfase para ajustar el benchmark.

## Interfaz, contribuciones, datos y norma

La interfaz de S7 es no monótona. El texto describe estabilidad observada y excluye una certificación de convergencia asintótica o error exacto.
Los nueve roles CRediT comunes proceden de la respuesta expresa de los autores en esta conversación; no se deducen de las afiliaciones. No se han enviado mensajes a coautores ni se afirma una confirmación independiente por correo.
El repositorio GitHub es público (HTTP 200 sin autenticación) y se creó el tag anotado manuscript-v5 sobre e33ca4edb7eb09a7dd34c890d4bd7e6d988c4d99. La revisión nueva se deposita por separado como manuscript-v6. No se ha asignado DOI ni se presenta GitHub como un depósito Zenodo.
La vista previa normativa accesible confirma que 6.4.3 trata el método C del factor dinámico y que la cláusula 9 trata rigidez. No expone el cuerpo de 6.4.3 f). La copia completa indexada no pudo recuperarse. Se retira del manuscrito la afirmación numérica c′=14 asociada a esa cláusula; no se presenta la transcripción de terceros como verificación definitiva.
[Vista previa de ISO 6336-1:2019](https://cdn.standards.iteh.ai/sist-preview/iso/iso-6336-1-2019/31cd8c848a1146a9926fec6fc8290727/iso-6336-1-2019.pdf).
