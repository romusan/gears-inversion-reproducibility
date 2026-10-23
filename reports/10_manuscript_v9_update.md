# Fase 10 — Corrección de la interpretación del espacio nulo y cierre de menores (v9)

Fecha: 2026-10-23 · Rama: `research/mmt-critical-validation`
Entregables (`gears_inversion/manuscript/`): `MMT_manuscript_Q1_revision_v9.docx`, `MMT_supplementary_Q1_revision_v9.docx` (S1–S12), `q1_manuscript_v9.md`, `build_review9.py`, `review9_sections.py`. v6–v8 intactos como archivos históricos.

Base numérica: `results/independent_validation/09_resolution_corrections.json` (Fase 9, commit `a20e558`). Verificaciones del revisor confirmadas: la décima dirección nula es la constante sobre los nodos cargados (J_h·1=0 exacto, rango = cargados−1 = 31, R_jj = 1−1/32 ≈ 0.969), no una transferencia de carga.

## Cambios respecto a v8

1. **Espacio nulo corregido en los cinco lugares** (resumen, highlights, §4.6 párrafo 2, §5, §6): «one further null direction, associated with load transfer between simultaneously active pairs» → «the mean-removed observable identifies the relief only up to an additive constant». La recomendación de medir deformación en raíz del diente se elimina (quedaba sin sustento). El §4.6 ahora enuncia la estructura completa: 9 nodos ξ≤0.20 + constante sobre los 32 cargados (los sombreros suman 1 ⇒ J_h 1 = 0), coherente con §2.3 y §4.1.
2. **Precisión, no solo resolución** (§4.6 párrafo nuevo): std por dirección 1/s_k con σ=0.1 µm — 24/31 direcciones ≤0.5 µm, 26 ≤1 µm, 29 ≤5 µm; dos peores (5.3 y 14.7 µm). Por nodo: ~0.10 µm cerca de ξ≈0.6, ~4.8 µm en ξ≈0.375–0.475, <5 µm en todos los cargados; nodos fuera de soporte sin información. Tono «resolving power well beyond the four declared parameters» / «certifies the relief» → lenguaje de precisión medido en §4.6, §5 y §6.
3. **Frontera de resolución** (§4.6): la transición se reporta entre el último nodo descargado (0.20) y el primero cargado (0.225), consistente con el inicio de contacto 0.2346 de la Tabla 11; la malla de 0.025 no distingue 0.2346 de 0.2356.
4. **Highlights 7 → 5**, todos ≤85 caracteres (límite Elsevier): los cinco candidatos del informe 09.
5. **Menores cerrados**:
   - §4.5 dedendum: «absorbs the discrepancy» → «el bloque dedendum no se movió de su inicialización (s_d estimado = valor de partida en ambas formulaciones); los valores reportados no contienen información de relieve». S10 caption acorde.
   - «within 5% of its scale» (3 ocurrencias: resumen, §5, §6) → cifras absolutas: 0.0025 mm (legacy) y 0.0006 mm (projected-energy) frente a 0.020 mm verdadero.
   - §4.5: ξ_min(57/57) = 0.6953 en las 19 fases interiores > s_d = 0.30 y 0.45 ⇒ la invisibilidad dedendum en el FE es la predicción de la condición de soporte.
   - §4.5: nota de semillas 0.394 vs 0.369 (bases disjuntas; bootstrap IC95 [0.310, 0.433] vs [0.291, 0.435] se solapan).
   - §4.5: nota ±0.9 pp del recálculo de rangos (8.9–37.2 % campaña original vs 9.1–38.1 % recálculo; mismos pares caso×torque, mismas referencias FE; configuración del resolvedor).
   - S7: «sampled interface stiffness sequence is nonmonotonic across refinement levels» (dato experimental, sin atribución teórica).
   - S12 caption: la dimensión nula restante cuenta la constante aditiva, aniquilada por el observable con media removida.
   - Disponibilidad de datos: etiqueta manuscript-v9.

## Verificación

- `docx.py validate` PASSED en manuscrito y suplementario (14 partes XSD + chequeos semánticos); reparaciones mecánicas aplicadas en ambos.
- Arreglos de builder heredados (v8 compartía los mismos 76 defectos XSD): `w:shd` con `w:val="clear"`, campo PAGE del footer fuera del run, anchos de Tabla 9 / S10 / S11 ajustados a ≤16.3 cm.
- Contenido verificado por extracción: 0 cadenas «load-split» / «load transfer between» / «within 5% of its scale»; highlights = 5 y ≤85; todas las frases nuevas presentes; «tooth-root» restante solo en la cita legítima de la Introducción [8].
- QA visual: no disponible en este entorno (sin node para el motor de renderizado doc-k); la compuerta de validación es el control final.
- Nota: el intento de validación sobre el archivo histórico v8 aplicó reparaciones mecánicas de orden de esquema (tcPr/tcMar, zoom) sin cambio de contenido ni de renderizado; v8 sigue siendo el artefacto revisado.

Pruebas del paquete de cálculo: 40/40 en verde (sin cambios de código en la Fase 10).
