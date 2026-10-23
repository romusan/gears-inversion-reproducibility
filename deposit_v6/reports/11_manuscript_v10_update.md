# Fases 11-12 y manuscrito v10 — cierre de la evaluación crítica pre-envío

Fecha: 2026-10-23. Rama: `research/mmt-critical-validation`.

Este reporte documenta las dos validaciones numéricas añadidas tras la
evaluación crítica del manuscrito v9 y las correcciones de texto
incorporadas en el manuscrito v10, punto por punto.

## Punto B — Segunda prueba FE con dedendum observable (fase 11)

La prueba nominal de §4.5 (S10) nunca ponía el dedendum en la zona cargada:
sobre las diecinueve fases interiores, ξ_min=0.6953, muy por encima de los
inicios de dedendum 0.30 y 0.45. Se añadió una segunda prueba con un par
simétrico 24/24 (módulo 3 mm, 300 Nm; `configure_24_24()` en
`fe2d/run_fe2d.py`), cuyo ξ_min analítico es 0.3036, de modo que un alivio
de dedendum con inicio 0.50 penetra la zona cargada durante todo el ciclo.

- Verdad: C_a=0.020 mm, s_a=0.75, C_d=0.010 mm, s_d=0.50.
- 120 fases FE por caso (3 casos: dedendum verdadero, dedendum cero y
  adendum de referencia); 102 fases interiores y 18 restringidas.
- Señal FE de dedendum 1.768 µm RMS ≈ señal de adendum 1.788 µm, y ~9× la
  respuesta del operador analítico a la misma verdad (0.187–0.197 µm):
  medida directa de la discrepancia de operadores, coherente con la tesis
  de discrepancia estructural de §5.
- Inversión cruzada ruido-libre (compliance proyectada-energía):
  recupera (0.0163, 0.8028, 0.0102, 0.3006) — profundidad de dedendum a
  0.0002 mm del valor verdadero; el inicio solo de forma gruesa; residual
  de ajuste 0.278 µm, por encima del piso de ruido de 0.1 µm.
- Monte Carlo (50 semillas, σ=0.1 µm), errores escalados mediana:
  (C_a 0.074, s_a 0.052, C_d 0.099, s_d 0.255); p90 de C_d 0.385.

Registros: `results/independent_validation/11_fe_cycle_24_24.jsonl` (360
filas) y `11_fe_observable_dedendum.json`. Scripts:
`fe2d/phase11_fe_cycle.py`, `reports/phase11_fe_observable.py`.

## Punto D — Reajuste de los 65 casos sin convergencia (fase 12)

Los 45 casos sin convergencia de la campaña principal (de 1200) y los 20
del control complementario (de 600) se reestimaron con la misma
observación, cuatro arranques adicionales amplios y presupuesto de
evaluación aumentado (max_nfev 1500 frente a 400).

- Solo 14/65 cambiaron el indicador de éxito: el flag marca terminación
  del optimizador en valles planos, no sesgo de identificación.
- Las medianas por celda apenas se mueven: el cambio máximo es 0.0034
  (0.3939 → 0.3972 en la celda nominal single300, s_d=0.25, σ=0.1); en 12
  de 14 celdas la mediana es idéntica tras reemplazar los fallos por el
  mejor reajuste.
- Conclusión: las conclusiones del manuscrito son invariantes a los
  no-convergidos.

Registro: `results/independent_validation/12_convergence_rerun.json`
(reanudable por `12_convergence_rerun_ckpt.jsonl`). Script:
`reports/phase12_convergence_rerun.py`.

## Cambios de texto en el manuscrito v10

- **Crítica E (referencias)**: añadidas [41] Spitas, Costopoulos y Spitas
  (solución analítica inversa del TCA, Inverse Problems in Science and
  Engineering 16(2), 171-186, 2008, doi 10.1080/17415970701256486) y
  [42] Kalligeros et al. (inversión de roll-test de doble flanco,
  Simulation Modelling Practice and Theory 126, 102757, 2023, doi
  10.1016/j.simpat.2023.102757), citadas en la Introducción para delimitar
  la novedad.
- **Crítica F (§4.6)**: párrafo final que distingue el espacio nulo exacto
  del operador linealizado discretizado de una garantía de reconstrucción
  no lineal de perfiles arbitrarios (requeriría control de términos de
  orden superior y del error de discretización).
- **Punto B (§4.5)**: dos párrafos con la segunda prueba FE 24/24 y la
  Tabla suplementaria S13.
- **Punto D (§4.3)**: párrafo de robustez de convergencia con los números
  de la fase 12.
- **Punto C**: las afirmaciones de validación FE en resumen, §5 y §6 se
  acotan a las fases interiores muestreadas.
- **Media**: resumen de 308 a 250 palabras; highlights en archivo
  independiente `highlights.txt` (5 bullets ≤ 85 caracteres); declaración
  de IA que nombra la herramienta (Kimi/Moonshot AI); nota de bases de
  semillas disjuntas en el suplementario.
- **Data availability**: el tag de depósito pasa a `manuscript-v10`, con
  manifiesto SHA-256 (`SHA256SUMS.json`) y tag anotado en este repositorio.

## Verificación

- `MMT_manuscript_Q1_revision_v10.docx` y `MMT_supplementary_Q1_revision_v10.docx`
  pasan la compuerta de validación del paquete OOXML sin violaciones ni
  advertencias.
- Contenido verificado por extracción: sin restos de la «dirección nula de
  transferencia de carga», 5 highlights, referencias 41-42 citadas, 250
  palabras en el resumen, S13 y nota de semillas en el suplementario.
- `python -m pytest tests/ -q` en `gear_inverse_identifiability`: 40/40.
