# Respuesta a la quinta revisión

Se cerró el control no lineal de fases complementarias y se separaron los controles del cuerpo y de la interfaz FE, con elementos cuadráticos y presión distribuida. Los resultados previos se conservan como diagnósticos de su discretización; la validación física del contacto de esquina sigue abierta.

## Convergencia FE

El ajuste de tres valores lineales con orden 0.32 no justificaba una extrapolación certificada. El seguimiento usa elementos de desplazamiento de seis nodos y funciones continuas de presión integradas sobre la traza real del borde. Las holguras se promedian con las mismas funciones. Se fijaron los vértices geométricos del contacto con independencia del paso de presión y la malla local objetivo en 0.01 mm.

| Fase | Control | h (mm) | Paso presión (mm) | k (N/µm) | Acercamiento (µm) |
|---:|---|---:|---:|---:|---:|
| 0 | bulk | 0.5 | 0.01 | 236.52791 | 40.54457 |
| 0.5 | bulk | 0.5 | 0.01 | 323.85517 | 29.47862 |
| 0 | bulk | 0.35 | 0.01 | 236.40445 | 40.56582 |
| 0.5 | bulk | 0.35 | 0.01 | 323.68316 | 29.49440 |
| 0 | bulk | 0.25 | 0.01 | 236.34936 | 40.57518 |
| 0.5 | bulk | 0.25 | 0.01 | 323.63081 | 29.49916 |
| 0 | interface | 0.25 | 0.02 | 236.25263 | 40.57660 |
| 0.5 | interface | 0.25 | 0.02 | 323.60593 | 29.49995 |
| 0 | interface | 0.25 | 0.005 | 236.49239 | 40.57451 |
| 0.5 | interface | 0.25 | 0.005 | 323.53080 | 29.49883 |

El último cambio del cuerpo, manteniendo el paso de presión, es 0.0233% y 0.0162%. El cambio de interfaz de 0.01 a 0.005 mm, sobre los mismos recuentos de nodos/elementos y con h fijo, es 0.0605% y 0.0309%. La prueba de energía bajo deformación constante con elementos cuadráticos dio error relativo 1.82e-14; los casos conservan los controles de equilibrio, energía y rigidez incremental. La restricción de contacto nueva es débil/promediada; no se afirma no penetración puntual exacta a resolución finita.
Los valores finos son k₁=236.4924 y k₂=323.5308 N/µm; los acercamientos son 40.5745 y 29.4988 µm. La diferencia interior es 11.0757 µm. Esta secuencia no respalda el valor 218 N/µm extrapolado de la combinación anterior de malla lineal y cargas nodales. Las variaciones observadas son medidas de estabilidad numérica, no cotas rigurosas del error exacto ni validación del contorno real.

## Control Monte Carlo

Se asignan 50 Nm a posiciones pares y 300 Nm a impares de la rejilla canónica de 120 puntos. Cada ciclo tiene 60 observaciones y su propio centrado. El ruido independiente se asigna a la posición angular canónica, para emparejar semillas con la carga única almacenada. Se mantienen escalas, cotas, dos inicios independientes y tolerancias. El motor Lambert W nuevo se cotejó con el iterativo en ambas verdades y ambos inicios.

| sd | σ (µm) | Convergentes/100 | Mediana 300 | Mediana par | Mediana diferencia pareada | Intervalo bootstrap 95% |
|---:|---:|---:|---:|---:|---:|---|
| 0.25 | 0.1 | 95 | 0.3939 | 0.4218 | 0.006074 | [-0.0002647, 0.02219] |
| 0.25 | 0.5 | 96 | 0.2949 | 0.3499 | 4.722e-07 | [0, 0.0299] |
| 0.25 | 1 | 94 | 0.3702 | 0.3865 | 0 | [-0.008453, 0.02591] |
| 0.4 | 0.1 | 100 | 0.1058 | 0.1148 | -0.0001536 | [-0.01099, 0.007583] |
| 0.4 | 0.5 | 98 | 0.3246 | 0.2942 | -0.008275 | [-0.02771, 0] |
| 0.4 | 1 | 97 | 0.3374 | 0.4435 | 1.937e-05 | [-7.202e-12, 0.01494] |

Se añadieron 600 reconstrucciones; 580 declaran convergencia y los 20 fallos se conservaron. Los seis intervalos incluyen cero. No se demuestra ventaja del par para este reparto complementario en ninguna de las dos verdades. La mediana de diferencias pareadas no es la diferencia de medianas. Los átomos por saturación de cotas producen empates y algunos intervalos terminan exactamente en cero; no se interpreta esto como equivalencia certificada o una prueba de cobertura de parámetros.

## Inferencia sobre el benchmark

La concordancia aproximada de los rangos FE y baseline en ocho fases motiva auditar la definición de TE, geometría de punta/borde y configuración unmodified del benchmark. No permite atribuir la brecha solo a la ley de rigidez, pero tampoco identifica su causa: ambos modelos comparten idealizaciones geométricas, las fases FE de borde se recortan y la secuencia lineal original no estaba demostrada como asintótica. El +16.6% queda identificado como comparación de rejilla finita con incertidumbre de discretización; no como error físico certificado.
Un rango discreto puede ser un límite inferior del rango angular del mismo operador; con contactos de esquina omitidos y mallas finitas no certifica un límite del pico a pico físico. El control cuadrático resuelve la estabilidad de las fases interiores, no el ciclo continuo de esquina.

## Precisión, norma y edición

Se redondea σ₄ marginal a dos cifras en las tablas de espectros y geometría y en la leyenda de la Figura 6. Se señala su dependencia de la rejilla. El highlight ahora destaca ξ_min como diagnóstico previo.
El rango baseline 14.08–15.07 N/(mm·µm) procede de las 1920 fases, con mínimo 323.8756/23=14.08155. El subconjunto de ocho fases da 14.22–15.07. Los dos rangos son correctos para sus muestreos; se explicita esa diferencia.
ISO 6336-1:2019, 6.4.3 f), páginas impresas 27–28, contiene c′=14 para engranajes rectos dentro de las simplificaciones del método C. La definición y cálculo de rigidez se tratan en la cláusula 9. Se volvió a consultar la transcripción normativa accesible y la ficha oficial; no se afirma disponer de la copia licenciada íntegra.
[Transcripción normativa consultada](https://studylib.net/doc/28005356/iso-6336-1-2019-calculation-of-load-capacity-of-spur-and-...) y [ficha oficial ISO](https://www.iso.org/standard/63819.html).
Las antiguas Tablas 7–10 y 13–14 pasan a S1–S6 del suplemento; S7 contiene los controles separados. El manuscrito principal retiene diez tablas y 40 referencias. Los autores confirmaron los mismos nueve roles CRediT para cada uno. Código y datos: https://github.com/romusan/gears-inversion-reproducibility/tree/manuscript-v5. No se ha asignado DOI.
