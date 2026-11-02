# Cierre verificado de la versión 14

1 de noviembre de 2026.

- Se ejecutaron 32 casos nuevos y se conservaron los 192 ajustes restringidos: todos reportan convergencia. Se recalcularon los 32 residuales desde los parámetros guardados sin discrepancias en esta ejecución.
- La versión final contiene 45 referencias por primera aparición, 11 figuras, 11 tablas principales, 23 tablas suplementarias y 15 objetos matemáticos editables. El resumen tiene 241 palabras.
- Se inspeccionaron las 38 páginas renderizadas: 28 del artículo, 8 del suplemento, 1 de Highlights y 1 de carta. La última corrección afecta sólo a la página 26; se volvió a inspeccionar y las otras 37 imágenes permanecieron idénticas.
- Desde una extracción nueva del ZIP reproducible: **40 pruebas aprobadas en 16.18 segundos**. La reconstrucción portátil produjo partes `word/` idénticas a las entregables en los cuatro documentos: 21 partes comparadas por artículo/suplemento y 9 por Highlights/carta. Las diferencias posibles en metadatos de fecha del contenedor no representan cambios del artículo.
- Los archivos del kit se identifican mediante `CONTENIDO_Y_SHA256.json`. El paquete reproducible tiene su propio `SHA256SUMS.json`, validado dentro del ZIP.

La v14 está preparada para cargar en MMT con alcance teórico y computacional. No se realizó envío editorial ni se afirma aceptación. La guía oficial respondió 403: los campos finales del formulario y las declaraciones personales deben completarse según la interfaz vigente. Se conservan explícitamente la discrepancia mecánica externa y los límites de reconstrucción física y convergencia FE.

Registros: `audit_v14.json`, `visual_QA_v14.json`, `portable_rebuild_QA_v14.json`, `unit_tests_v14.log` y `portable_build_v14.log`. La prueba portátil no repitió los 1800 ajustes históricos ni la campaña FE.
