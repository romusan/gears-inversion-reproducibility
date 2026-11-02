# Integración y comprobación de la revisión v15

Se conservaron las dos entregas originales en `../revision/` y se preparó una v16. No se ejecutaron experimentos nuevos ni se cambiaron resultados numéricos. Se mantuvieron las mejoras de estructura de v15: contribuciones explícitas, proposiciones con demostraciones, hoja de ruta de resultados, síntesis de evidencia y tablas de apéndice A.1–A.2.

## Corrección de integridad del documento

La v15 rastreada contiene 15 ecuaciones OMML y **9 comentarios**, no 8. La v15 limpia contiene cero ecuaciones OMML; tampoco contiene objetos de fórmula u OLE, y sus once imágenes son las figuras existentes. Por ello no se utilizó la limpia como base. La v16 se construye aceptando los cambios de la rastreada, conserva las 15 ecuaciones y elimina comentarios y revisiones de la entrega limpia. El cambio ℓ→η en la ecuación (2) se verificó; las otras catorce expresiones matemáticas coinciden con v14.

La v16 rastreada muestra únicamente nuestras 15 correcciones de párrafo sobre la **v15 aceptada**. Las revisiones de Claude ya están aceptadas en esa base. Se comprueba automáticamente que aceptar las 15 inserciones y 15 eliminaciones produce exactamente el XML del documento limpio.

## Resolución de las observaciones

| Observación | Resolución |
|---|---|
| Referencia [20] | Se conserva. El texto completo de Xue y Li, p. 1764, §2.1, ecuaciones (1)–(3), desarrolla reparto de carga y error de transmisión con errores de perfil. El título térmico no invalida ese contenido. La Introducción identifica ahora ese pasaje. |
| Referencia [8], «419» | J-STAGE muestra tanto «Session ID: 419» como el título «419 A study…». Se conserva la forma editorial registrada y el DOI. No se confundió la fecha de incorporación a J-STAGE, 2017, con la publicación de 2000. |
| CRediT | Los nueve roles existentes de cada autor se conservan. El usuario confirmó expresamente que los tres participaron en todas las tareas. No se diferenciaron roles por motivos cosméticos. |
| IA | Se conserva Claude porque se mantienen sus cambios editoriales. También se conservan Kimi y ChatGPT/Codex y la responsabilidad autoral. |
| Generación 57/57 | La Tabla 9 y S10 incorporan las tres verdades θ=(Cₐ,sₐ,C_d,s_d), carga 650 Nm y rueda sin modificación, extraídas de `03_cross_inverse.json`: (0.020,0.75,0,0.50), (0.020,0.75,0.005,0.30) y (0.020,0.75,0.005,0.45). |
| Seis arranques | Se describen los tres fijos, las distribuciones uniformes y la semilla 20261101 de los tres aleatorios. Los seis valores exactos están guardados; los 32 casos usan los mismos seis arranques. Se conserva el total de 192 ajustes. |
| Suplemento | Se incluye un archivo v16 separado con S1–S23. Todos sus valores tabulados permanecen idénticos a v14; sólo se amplía el pie S10. |
| Datos y DOI | Se sustituye el marcador por una declaración verificable: archivo reproducible v16 adjunto, baseline público v13 y ningún DOI asignado. Se prepara metadata para un eventual depósito. No se inventa DOI ni se afirma que se haya depositado. |

Fuentes primarias: [ficha editorial J-STAGE de la referencia 8](https://www.jstage.jst.go.jp/article/jsmekansai/2000.75/0/2000.75__4-31_/_article/-char/en); [referencia 20 y resumen editorial](https://xuebao.neu.edu.cn/natural/CN/10.12068/j.issn.1005-3026.2013.12.022). El PDF chino descargado está en `../diagnostico_2026-11-01/referencias/R04_zh.pdf`.

## Ajustes científicos adicionales

1. Se elimina del resumen la afirmación universal de que sólo el flanco cargado puede influir en TE. El control de retirada de material muestra precisamente el límite de esa afirmación física.
2. La Proposición 1 restringe el inicio a su dominio positivo admisible: la ley de relieve divide entre s_d.
3. La Proposición 2 se formula para contacto **lineal acoplado** con H fija y definida positiva. Su prueba mediante potencial cuadrático no permite añadir automáticamente Hertz no lineal. Se mantiene la condición de convexidad adicional en la observación posterior.
4. «Marginal» y «deeper» se presentan como etiquetas de los casos de geometría y muestreo estudiados, sin convertir sus valores s_d en umbrales universales.
5. El diagnóstico distingue el cribado de soporte previo a invertir de los ajustes restringidos posteriores. Los errores de parámetros sólo se piden cuando existe un perfil verdadero independiente; en una inversión real desconocida se informa incertidumbre condicional.
6. La tabla de evidencia informa residuales multistart positivos, sin certificar separación global del conjunto de respuestas. Sus columnas nulas se atribuyen al soporte de las bases, no sólo a coordenadas nodales.
7. El párrafo de limitaciones distingue los operadores gap-only de la prueba de retirada física, que sí reensambla elasticidad.
8. Los Highlights se acotan a las hipótesis del operador y hablan de una respuesta FE, no de detectabilidad experimental demostrada.

## Alcance de las comprobaciones

El auditor comprueba que las once tablas numéricas originales del artículo y las veintitrés del suplemento conservan todas sus celdas. Verifica las 45 referencias por primera aparición, 11 figuras, Tabla 1–10 y A.1–A.2, la notación η, ausencia de comentarios en el limpio y equivalencia entre aceptación de cambios y limpio. Las tablas nuevas de síntesis no constituyen resultados nuevos. La revisión de números no equivale a repetir experimentos ni a validar físicamente los perfiles.

La comprobación de la guía específica de MMT volvió a dar HTTP 403. Por tanto, no se convierte la recomendación de DOI del revisor en un requisito editorial confirmado. El [material general de Elsevier sobre datos](https://www.elsevier.com/researcher/author/tools-and-resources/research-data) recomienda consultar la guía del destino y ofrece mecanismos de depósito y vinculación; no sustituye la política específica de MMT.

## Pendiente externo

La emisión de un DOI real requiere un depósito autenticado y la elección de una licencia por sus titulares. No hay una conexión autenticada a Zenodo disponible en las herramientas de esta sesión. Se dejan archivo, hashes y metadata preparados. El manuscrito puede describir honestamente el archivo adjunto sin un marcador ficticio; no se presenta el depósito como realizado. Tampoco se realizó envío editorial.
