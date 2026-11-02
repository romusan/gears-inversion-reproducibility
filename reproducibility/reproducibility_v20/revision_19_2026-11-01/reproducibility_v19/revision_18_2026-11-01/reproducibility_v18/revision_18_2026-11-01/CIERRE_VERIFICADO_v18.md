# Cierre verificado de la versión 18

La v18 integra la crítica específica de la Sección 4.8 con 600 casos adicionales y análisis de los registros existentes. La versión de carga es el artículo limpio v18, acompañado por suplemento S1–S32, Highlights, carta y archivo reproducible. Los originales de v17 permanecen sin modificación.

## Resultados del cierre

- Campaña combinada: **1100 selecciones**, 3300 intentos finales y 300 pilotos adicionales para covarianza. La ampliación de 600 casos tomó 771.05 segundos. Las celdas profundas IID y ganancia tienen 200 pares; las otras celdas, 50.
- Se conservan 32 selecciones no convergidas, 91 intentos finales no convergidos y tres pilotos no convergidos. Las medianas generales incluyen esas selecciones y se rotulan como resultados del procedimiento finito.
- Ganancia profunda del 5%: error mediano escalado **0.0916 frente a 1.86**; diferencia de medianas **1.77**, intervalo percentil pareado del 95% **[1.44, 3.32]**. El resultado de 50 pares se mantiene como antecedente anidado, no como réplica independiente.
- GLS marginal: 16/50 límites del bloque dedendum frente a 7/50 bajo ponderación IID; en 28 pares conjuntamente convergidos e interiores las medianas son 0.489 y 0.211. Los límites no explican por sí solos la diferencia. La propagación lineal local favorece a GLS, pero sus desviaciones de profundidad exceden la caja completa.
- La conclusión «GLS es peor» tampoco sigue de esos datos: aunque el perfil marginal empeora de 0.697 a 1.11 µm, la transferencia nominal a 200 Nm mejora de 0.0301 a 0.0196 µm. En el caso profundo, el intervalo del contraste GLS–IID [−0.0656, 0.0681] no resuelve un orden de ese error.
- El filtro de compatibilidad usa el percentil χ²₁₂₀(0.95)=146.56735758076744, sin sustraer cuatro parámetros. Marca 200/200 ajustes profundos de ganancia frente a 4/200 IID; incluye 14 selecciones de ganancia no convergidas. Su interpretación requiere las hipótesis especificadas y no identifica la causa de la incompatibilidad. FGLS no recibe un conteo chi-cuadrado calibrado.
- Añadidos controles de armónicas 1×/2× de rotación y paso de diente, así como FGLS de un paso. Se preserva la distinción entre amplitud de vuelta completa y RMS de una sola ventana de paso. Las perturbaciones no se presentan como mediciones de encoder o excentricidad.

## Comprobaciones completadas

- **40 pruebas aprobadas en 19.24 segundos.**
- Verificadas las 600 nuevas observaciones y sus semillas, los objetivos seleccionados y errores de perfil, y las 100 estimaciones piloto de covarianza. Diferencia máxima de observación reconstruida: cero. El análisis recalcula los objetivos de los 1100 casos combinados.
- Recalculadas independientemente 32 transferencias, dos por celda, frente a sus objetivos nominal y generador. Verificadas las 16 celdas de resúmenes y sus conteos.
- El primer bootstrap se contrastó independientemente con `scipy.stats.bootstrap`, opción pareada y método percentil. Coinciden sus extremos. Las 21 distribuciones archivadas tienen 10000 réplicas cada una y sus percentiles reproducen los intervalos. Son intervalos puntuales sin ajuste de multiplicidad y no cuantifican cobertura física.
- Quince ecuaciones OMML y 45 referencias preservadas. Todas las celdas de las tablas anteriores del artículo y S1–S27 son idénticas a v17; las tablas nuevas coinciden con el análisis. S24–S25 siguen siendo el antecedente de 50 semillas, y S28–S30 indican la actualización de las celdas profundas a 200.
- Resumen de 232 palabras; cinco Highlights de hasta 85 caracteres. Los roles CRediT comunes confirmados por el usuario se conservan. Los cuatro documentos limpios no tienen comentarios ni revisiones pendientes.
- Desde una extracción independiente del archivo: reconstruidos y auditados los cuatro documentos. Coinciden exactamente sus partes Word: 23 en el artículo, 21 en el suplemento y nueve en cada documento breve. Solo las fechas del contenedor ZIP pueden cambiar.
- Exportación nativa de Word y rasterización con Poppler: artículo 33 páginas, suplemento 14, Highlights una y carta una. Se revisaron láminas de las 49 páginas y se ampliaron resumen, sección nueva, figura y tablas. Se amplió la columna de verdad generadora para impedir que 0.25 se partiera en dos líneas. La Figura 12 usa escala logarítmica y n por celda. Se mantuvieron encabezados repetidos en las tablas continuadas. El renderizador empaquetado depende de LibreOffice, ausente en este equipo, por lo que se utilizó la alternativa nativa ya diagnosticada. PDF y PNG son QA interna y se excluyen del kit.
- El empaquetador comprueba CRC y todos los hashes SHA-256 del archivo de evidencia; el kit contiene las cuatro copias finales y dicho archivo. La identidad definitiva se registra en `ENTREGA_VERIFICADA_v18.json`.

La v18 no resuelve las 18 estaciones FE omitidas ni el contacto de esquina/filete y no incorpora una medición o validación 3D completa. No afirma equivalencia TOST, diseño global óptimo, mínimo global ni cobertura calibrada de perfiles FE. El bootstrap nuevo atiende los resúmenes Monte Carlo y no sustituye esos estudios. Tampoco se emitió DOI, se publicó un depósito o se realizó el envío editorial.
