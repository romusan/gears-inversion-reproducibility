# Cierre verificado de la versión 17

El paquete final reúne artículo limpio, suplemento S1–S27, Highlights, carta y archivo reproducible. La versión vigente para carga es v17; las versiones anteriores se conservan como procedencia.

## Evidencia incorporada

- 500 casos sintéticos adicionales, 50 por cada combinación de cinco escenarios y dos verdades de soporte; 1500 intentos desde tres arranques fijos. Tiempo de campaña: 564.33 segundos.
- 13 selecciones no convergidas y 36 intentos no convergidos, conservados y reportados. La Figura 12 distingue estados y límites del bloque dedendum; los indicadores por coordenada permanecen en los registros.
- Ruido independiente, correlación no periódica de parámetro 0.8 con ajuste IID o GLS de covarianza conocida, ganancia del 5% y cambio de compliance shear-G → projected-energy. No son mediciones ni calibración de discrepancia externa.
- En el caso profundo, la ganancia del 5% cambia el error mediano escalado de 0.0896 a 1.56; residual mediano 0.138 µm. Es una vulnerabilidad sintética a error de medición, no una validación física.
- Los 1800 ajustes históricos se particionaron por estado y límites sin repetir ni sustituir sus resultados. Los 32 casos y 192 intentos de v14 permanecen intactos.

## Verificación completada

- **40 pruebas aprobadas en 34.20 segundos.**
- Recalculados independientemente los 500 objetivos seleccionados, las curvas generadoras, los errores de perfil y respuesta, las semillas, la covarianza de ruido y las banderas de límites. Diferencias de objetivos y generadores: cero en la recomputación guardada. Los hashes de fuentes coinciden.
- Quince ecuaciones OMML preservadas exactamente respecto de v16, 45 referencias sin alteración y todas las celdas de las tablas anteriores del artículo y S1–S23 conservadas. La nueva tabla S24 coincide con los registros.
- Resumen de 222 palabras; cinco Highlights de 68–81 caracteres. CRediT conserva los nueve roles comunes confirmados por el usuario. Los cuatro DOCX finales no contienen comentarios ni revisiones pendientes.
- Desde una extracción del ZIP: reconstruidos los cuatro documentos y ejecutada su auditoría. Las 22 partes Word del artículo, 21 del suplemento y nueve de cada documento breve resultaron idénticas. No se repitió la simulación para esta comprobación.
- Exportación nativa de Word: artículo 32 páginas, suplemento 11, Highlights una y carta una. Se revisaron láminas de las 45 páginas y se ampliaron los pasajes nuevos, tablas y figuras. Se corrigieron las letras de la Figura 12, los pies de S24–S27 y el encabezado aislado de la Tabla 10. El exportador empaquetado depende de LibreOffice, ausente en este equipo; se utilizó la alternativa nativa diagnosticada y rasterización con Poppler. Los PDF e imágenes son QA interna y no forman parte del kit de carga.
- Archivo ZIP y manifiestos SHA-256 comprobados por el empaquetador. La entrega definitiva queda identificada en `ENTREGA_VERIFICADA_v17.json`.

El v16 rastreado histórico contiene 15 inserciones y 15 eliminaciones reales; su aceptación produce v16 clean. La revisión final v17 se entrega limpia y sus cambios están documentados en el registro editorial y la respuesta al diagnóstico.

Permanecen explícitas las limitaciones físicas: 18 estaciones FE omitidas, contacto de esquina/filete sin resolver y falta de forma de onda medida con relieve certificado. No se afirma equivalencia de diseños, mínimo global ni cobertura calibrada. No se emitió DOI ni se realizó depósito o envío editorial.
