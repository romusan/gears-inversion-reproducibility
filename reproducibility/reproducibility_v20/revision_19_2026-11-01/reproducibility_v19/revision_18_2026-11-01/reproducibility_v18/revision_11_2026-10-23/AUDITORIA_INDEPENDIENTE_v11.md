# Auditoría científica independiente del manuscrito de identificabilidad de microgeometría

23 de octubre de 2026

La comparación FE de la v10 contiene el error señalado por el dictamen. La auditoría encuentra además un problema más concluyente: el dedendum estimado en el ajuste publicado no alcanza ningún contacto cargado del operador inverso. Suprimirlo deja la TE predicha exactamente igual. El valor de profundidad cercano al verdadero no constituye una recuperación geométrica. La v11 conserva y desarrolla la contribución sobre observabilidad condicionada al operador, retira esa interpretación de recuperación y presenta explícitamente los límites mecánicos.

## Alcance y evidencia

Se inspeccionaron el operador de contacto, el generador FE, el cálculo de señales, las funciones de coste, las derivadas y los constructores del manuscrito. La base local corresponde al commit `8a08285ea9b6e8026d147102278f67e4c403e6bf`, con árbol limpio al inicio. No se modificaron la v10 ni sus registros. Las nuevas salidas están en este directorio y los constructores en `../manuscript`.

Se ejecutaron las 40 pruebas automatizadas del depósito: 40 aprobadas. Se recalcularon las 48 amplitudes analíticas de los doce casos externos; el espacio nulo y las incertidumbres por dirección; las señales FE de los 360 registros; y las métricas y claves de los 1800 registros estadísticos originales. Se realizaron nuevas inversiones del caso 24/24, restricciones sin dedendum, perfiles de objetivo y dos ciclos FE de malla adicionales. Las versiones del entorno y los hashes de entrada están en los JSON de auditoría.

No se repitieron las 1800 optimizaciones originales, la campaña histórica completa de FE 57/57 ni los 50 ajustes Monte Carlo del ensayo 24/24. Sus agregados conservados se distinguen de los nuevos cálculos. La revisión bibliográfica comprobó coherencia estructural de 42 referencias y la procedencia de los objetivos externos; no constituye una verificación exhaustiva de cada afirmación de las 42 publicaciones.

## Comparación FE corregida

Las señales se calculan sobre las mismas 102 fases interiores, después de centrar cada curva. Hay 120 fases y tres casos por fase, sin duplicados; 18 fases se excluyen por la ventana de contacto restringida.

| Contraste | RMS µm |
| --- | ---: |
| Addendum y dedendum frente a nominal | 1.768443919 |
| Solo addendum frente a nominal | 1.787551808 |
| Addendum y dedendum frente a solo addendum | 0.178987000 |
| Dedendum aislado analítico radial energy | 0.196588825 |

La relación comparable es 0.910464. Se elimina la afirmación de una respuesta específica nueve veces mayor. La concordancia aproximada de RMS no establece concordancia de formas de onda ni valida la inversión.

El script histórico restaba `dedendum - unmodified`, aunque `dedendum` designa un perfil combinado. `phase11_fe_observable_corrected.py` conserva el experimento pero utiliza `dedendum - addendum` y escribe a un archivo nuevo. El análisis independiente `audit_v11.py` no depende de la señal agregada histórica.

## Hallazgo adicional en la inversión

En el ajuste radial energy publicado, s_d=0.3006205374, mientras que el primer contacto cargado es ξ=0.3036049785. Hay cero puntos cargados con ξ menor que s_d, ambas columnas dedendum del Jacobiano son exactamente cero y eliminar la profundidad estimada produce RMS de cambio de TE igual a cero. El mismo diagnóstico se cumple para el ajuste histórico baseline y los nuevos mínimos de ambas formulaciones. Los datos se conservan en `audit_fit_invariance.json`.

La inversión independiente usa 26 inicializaciones: las dos originales, 22 uniformes en toda la caja y dos cercanas a sus extremos, con semilla 20261023. Cada inicialización dispone de hasta 1600 evaluaciones. El modelo nulo fija C_d=0 y s_d=0.50 porque el inicio es redundante cuando la profundidad es cero. Se optimizan únicamente los dos parámetros de addendum. Todos los ajustes seleccionados de estas pruebas notifican convergencia; ello no demuestra optimalidad global.

Para radial energy, el mínimo amplio estima C_d=25.8399 µm y s_d=0.236833, con RMS TE 0.277750805 µm y error RMS de perfil 3.402029 µm. El modelo sin dedendum obtiene RMS TE 0.277750805 µm y Δχ²=5.223e-09. La profundidad cambió sustancialmente respecto a la estimación histórica sin mejorar el ajuste.

Los perfiles cubren 41 profundidades de 0 a 50 µm y 46 inicios de 0.05 a 0.50, con cinco inicializaciones por punto y hasta 1000 evaluaciones por ajuste. Ambos parámetros presentan perfiles planos en todo el dominio en las dos formulaciones, con aumentos de objetivo inferiores a 10⁻⁸. No hay evidencia de identificación de presencia, profundidad o inicio de dedendum por este inverso. La escala 0.1 µm es una hipótesis de ponderación; las curvas no proporcionan intervalos físicos de confianza bajo discrepancia determinista.

## Malla del caso 24/24

Se conserva h=0.50 mm y se generan nuevamente las 102 fases interiores para h=0.35 y 0.25 mm. Los tres niveles comparten P1, interfaz nodal de 0.02 mm, contorno nominal, cubo de 12 mm, trim de raíz de 0.4 mm y carga de 300 Nm. Por nivel se ajusta radial energy desde doce inicializaciones. Los registros de los nuevos ciclos son incrementales y no reemplazan el archivo histórico.

| h mm | Señal aislada µm RMS | Residual TE µm | Error de perfil µm RMS | Cₐ sₐ C_d s_d |
| ---: | ---: | ---: | ---: | --- |
| 0.50 | 0.178987 | 0.277751 | 1.9884 | 0.016257, 0.802782, 0.011027, 0.237284 |
| 0.35 | 0.178994 | 0.367759 | 5.5425 | 0.016112, 0.812192, 0.034674, 0.275349 |
| 0.25 | 0.178969 | 0.423886 | 4.5561 | 0.015936, 0.816919, 0.034369, 0.176826 |

El último cambio relativo de señal es 0.0137% y el de residual es 15.2620%. La señal aislada es estable, pero la inversión no presenta estabilidad suficiente del residual ni del perfil reconstruido: no se declara convergencia de recuperación inversa. Se reportan los valores observados sin atribuirles un orden asintótico. Esta prueba aísla sensibilidad a la malla del cuerpo; la discretización de interfaz no se refina. Tampoco valida las fases excluidas ni un ciclo continuo con contacto de esquina. La interpretación de los parámetros debe tener en cuenta la invariancia del bloque dedendum.

## Mecánica y benchmark externo

La matriz H se construye para el contorno nominal y se reutiliza en los tres casos, añadiendo el relieve a las separaciones. El resultado FE verifica sensibilidad de contacto con cumplimiento fijo y acoplado. No constituye una simulación de retirada física de material. No se implementó un nuevo mallado de contornos aliviados con recalculo de normales y contacto; por ello, el manuscrito limita expresamente la conclusión. Esa validación sigue siendo necesaria para afirmar reconstrucción física.

La reproducción independiente de los doce objetivos a 240 posiciones confirma errores relativos 8.928–37.172% para baseline, 38.638–105.478% para shear-G, 17.826–53.122% para radial energy y 20.214–58.833% para centre-line. Son doce casos evaluados cuatro veces, y todas las diferencias son positivas. El 5% sigue siendo un objetivo de investigación, no una norma editorial.

Se contrastaron dimensiones, cargas y convención del relieve con la referencia de [Korta y Mundo](https://doi.org/10.1016/j.mechmachtheory.2016.11.015) y su [versión de autor](https://iris.unical.it/bitstream/20.500.11770/133021/10/1.Korta_MMT__Submitted_Version_opt.pdf). Los datos locales contienen objetivos de amplitud, no las formas de onda numéricas completas ni el CAD y las condiciones exactas de solución. No se fabricó una comparación punto a punto a partir de amplitudes. El artículo separa este error directo del error inverso y presenta las condiciones no igualadas como limitaciones, sin asignar una causa demostrada a la discrepancia.

## Matemática y estadística

La demostración por KKT es válida con H simétrica definida positiva, estaciones y normales fijas y perturbaciones no negativas de gap nulas en contactos cargados. El añadido de Hertz requiere positividad del Hessiano compuesto; H positiva por sí sola no basta. La tangente es por tramos, fuera de cambios de conjunto activo. Estas hipótesis permanecen explícitas.

La auditoría reproduce rango 31 con 41 coeficientes, nueve columnas nulas y una constante anulada por centramiento. El nodo ξ=0.225 es sensible aunque el primer contacto está en ξ=0.235629: su función sombrero alcanza el soporte cargado. La v11 corrige la identificación literal entre coordenada nodal y frontera física. La igualdad rango=número de coeficientes sensibles menos uno se presenta como resultado de los diseños comprobados, no como teorema universal.

Las desviaciones 1/sₖ son locales y condicionadas al subespacio resuelto, al gauge y al ruido supuesto. Las direcciones nulas no adquieren incertidumbre finita por usar una pseudoinversa. No se garantiza recuperación global de perfiles no paramétricos arbitrarios a partir de un Jacobiano local.

Los 1200 y 600 registros estadísticos tienen claves únicas, 100 semillas por celda y 45 y 20 fallos respectivamente. Las métricas de parámetros y los RMS de perfil disponibles coinciden exactamente con su recomputación. La identidad χ²=N(RMS/σ)² se cumple con diferencia máxima 8.53×10⁻¹⁴. Estos controles verifican los registros, no equivalen a repetir las optimizaciones ni certificar sus mínimos.

## Reescritura y estado científico

El artículo se reescribe en inglés con una secuencia de problema, operador, resultado de observabilidad, evidencia de incertidumbre y límites mecánicos. El historial de versiones y esta auditoría quedan fuera de la narrativa del artículo. El suplemento se amplía de 13 a 16 tablas y muestra errores del perfil, ajustes sin dedendum, perfiles de objetivo y malla propia. Las figuras de sensibilidad, perfiles y resolución se regeneran con etiquetas mayores. La declaración de asistencia incluye las herramientas utilizadas y no afirma una revisión humana aún no realizada.

La v11 no debe presentarse como demostración de reconstrucción física validada. Su contribución defendible es teórico-computacional: límites de observabilidad condicionados al operador y evidencia de que señal, ajuste y recuperación geométrica son conceptos diferentes. Permanecen abiertas la validación de contornos físicamente modificados, la convergencia independiente de interfaz y la comparación externa de formas de onda y condiciones mecánicas. Las contribuciones CRediT y declaraciones de financiación se conservan de la fuente y requieren la comprobación habitual de los autores.
