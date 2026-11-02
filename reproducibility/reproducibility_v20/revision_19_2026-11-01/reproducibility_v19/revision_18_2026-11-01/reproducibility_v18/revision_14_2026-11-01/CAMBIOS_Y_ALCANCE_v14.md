# Revisión 14 para envío a Mechanism and Machine Theory

Preparada el 1 de noviembre de 2026 a partir de la versión 13. El artículo conserva su pregunta y sus resultados históricos. La contribución sigue siendo un diagnóstico de observabilidad condicionado al operador mecánico y a las observaciones retenidas.

## Cambios científicos y editoriales

- Tres referencias nuevas, para un total de 45: Rigaud y Barday, en francés, sobre acoplamiento entre dientes y cuerpo de rueda; Xue y Li, en chino, sobre rigidez, errores y reparto de carga; Zhou y colaboradores, 2024, sobre influencia directa de parámetros de modificación. Se contrastan con la inferencia de geometría desconocida. No se presenta la física del acoplamiento como una invención propia.
- Sección 4.7, Figura 11 y Tablas S22–S23: distancia entre respuestas sintéticas con dedendum y el conjunto de respuestas de un modelo con sólo addendum, permitiendo que sus dos parámetros se reajusten.
- Resumen y conclusiones actualizados con los nuevos controles. La discusión distingue robustez cualitativa frente a cambios constitutivos de validación mecánica.
- Citas y bibliografía renumeradas por primera aparición. Se conservan 15 objetos matemáticos OMML, 11 tablas principales, 11 figuras y 23 tablas suplementarias. Resumen de 241 palabras; cinco Highlights, cada uno de menos de 85 caracteres.
- Carta de presentación y declaración de disponibilidad actualizada. El archivo adjunto v14 incluye los nuevos registros; no se inventa una URL pública v14 ni un DOI.

## Experimento nuevo ejecutado

G0: engranajes 24/48, módulo 3 mm, ancho 20 mm, presión nominal 20°, carga 300 Nm. Parámetros verdaderos: Cₐ=0.020 mm, sₐ=0.75, C_d=0.005 mm y s_d=0.25 o 0.40. Las cuatro formulaciones generan sus propios datos sin ruido: baseline, cortante con G, energía radial y energía sobre línea central.

Se usan rejillas canónicas de 120, 240 y 480 posiciones y una rejilla de 120 desplazada medio paso. El modelo restringido fija profundidad de dedendum cero y su inicio redundante en 0.50. Se optimizan sólo los dos parámetros de addendum con seis arranques, incluido el addendum verdadero y tres aleatorios con semilla 20261101. Resultado: **32 casos, 192 ajustes, cero estados de no convergencia**. Todos los intentos, no sólo el mejor, están almacenados. Esto no certifica mínimos globales.

En las 120 fases canónicas, el residual restringido es 0.000664–0.000731 µm con s_d=0.25 y 0.072490–0.078939 µm con s_d=0.40. Por tanto, el contraste entre soporte marginal y profundo persiste en las cuatro formulaciones. El resultado se refiere a datos sintéticos del mismo operador, no al experimento FE entre operadores ni a mediciones reales. Un residual positivo frente al modelo restringido no prueba unicidad de los cuatro parámetros.

Se informa D120=120(RMS/0.1 µm)² para comparar escalas sin premiar un mayor número de muestras. No se usa como test calibrado, potencia de detección ni umbral de confianza. La evaluación densa de 960 fases incluye las posiciones canónicas de ajuste: no es un conjunto independiente. La sensibilidad a rejilla se presenta numéricamente sin atribuir convergencia continua.

Comprobaciones: diferencia máxima entre motores iterativo y Lambert de 1.53×10⁻¹¹ µm RMS; error relativo máximo del Jacobiano implícito frente a diferencias centrales de 1.89×10⁻⁷; residual máximo de fuerza inferior a 2×10⁻⁸ N. El recálculo de los 32 residuales desde los parámetros guardados coincide con los valores publicados en la precisión de esta ejecución. Versiones y SHA-256 de las fuentes están en los JSON.

## Qué se pudo resolver

Se precisó la novedad, se incorporaron antecedentes multilingües pertinentes y se comprobó que la conclusión cualitativa de soporte no depende exclusivamente del baseline con cortante inconsistente. Se separó respuesta aislada de distancia tras compensación de addendum, se cuantificó dependencia angular y se mejoró la trazabilidad del paquete vigente.

## Qué continúa abierto

La discrepancia frente a los doce objetivos externos de amplitud persiste. Las cuatro formulaciones incumplen el objetivo investigativo del 5%. Los controles nuevos no identifican la causa física de esa discrepancia ni justifican corregirla con un factor arbitrario.

El ensayo FE retenido sigue permitiendo un ajuste sin dedendum con el mismo residual que el completo. Continúan sin resolverse las fases de transición excluidas, la convergencia de la inversión de ciclo completo y la reconstrucción de una geometría manufacturada con validación independiente. El pequeño efecto de retirada de material no acredita detectabilidad experimental. No se repitieron el FE ni las 1800 inversiones históricas.

La comprobación de acceso de la guía oficial MMT devolvió 403. No se le atribuyen requisitos editoriales nuevos no observados. El kit es una entrega preparada para cargar en el sistema editorial; los campos que dependen de declaraciones personales de los autores deben completarse allí con información real. No se realizó envío editorial.

## Verificación

`audit_v14.json` registra comprobaciones numéricas y de estructura. La revisión visual y los hashes del kit se registran por separado. La suite vigente es la de `deposit_v6/gear_inverse_identifiability/tests` dentro del paquete de reproducibilidad; no confundirla con las 27 pruebas de la carpeta histórica de desarrollo.

Las fuentes bibliográficas se cotejaron mediante los PDF obtenidos y metadatos editoriales. No se presenta esta ampliación dirigida como revisión sistemática de toda la literatura ni como lectura integral de las 45 referencias.
