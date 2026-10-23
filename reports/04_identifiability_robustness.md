# Fase 4 — Robustez de las conclusiones frente a la formulación de compliance

Fecha: 2026-10-22 · Rama: `research/mmt-critical-validation`
Script: `reports/phase4_robustness.py`
Datos: `results/independent_validation/04_support_transition_sweep.json`, `04_forward_cases.json`, `04_mc_records.jsonl` (400), `04_mc_summary.json`

## Pregunta central

1. ¿Sobrevive la conclusión del manuscrito —«la identificabilidad depende de la intersección del relieve con las regiones cargadas, pero la intersección no garantiza precisión»— al cambiar la formulación del compliance (legacy → projected-energy)?
2. ¿Sigue siendo válida, matemáticamente, la **condición suficiente de invisibilidad** (relieve sin intersección con la zona cargada ⇒ columna dedendum del Jacobiano nula)?

Diseño: G0 (24/48, módulo 3, ángulo 20°), 300 Nm, 120 posiciones, σ = 0.1 µm, verdad θ = [0.02, 0.75, 0.005, s_d], dos inicios fijos (política Q1). Casos s_d ∈ {0.25, 0.40}: intersección marginal (4 puntos cargados) vs amplia (43 puntos). Monte Carlo: 100 semillas declaradas por configuración (base 20261022), 400 ajustes en total.

## (4.1) El umbral de visibilidad es geométrico, no mecánico

Barrido forward s_d ∈ [0.20, 0.50] (61 puntos, sin ajuste) para ambas variantes (`04_support_transition_sweep.json`):

- s_min cargado a 300 Nm: **0.2356**, idéntico en legacy y projected-energy.
- Primer s_d con puntos del relieve cargados: **0.24** en ambas variantes.
- Primer s_d con señal dedendum > 1e-6 µm: **0.24** en ambas variantes.

La transición visibilidad/invisibilidad es puramente geométrica (intersección del soporte de contacto con el soporte del relieve) y **no se desplaza** al corregir la formulación del compliance. La condición suficiente de invisibilidad (s_d ≤ s_min ⇒ sin intersección ⇒ sin señal) sigue siendo válida matemáticamente en la formulación adoptada: fuera del relieve, la columna del Jacobiano es idénticamente nula porque h(s) ≡ 0 y ∂h/∂θ ≡ 0 en s ≥ s_d.

## (4.2) Métricas forward y espectro (300 Nm, 120 obs)

| Variante | s_d | TE pp (µm) | puntos cargados en relieve | señal dedendum RMS (µm) | SV mín (blanqueado) | cond. Fisher | rango |
|---|---:|---:|---:|---:|---:|---:|---:|
| legacy | 0.25 | 8.726 | 4 | 0.0006 | 3.6e-02 | 7.0e+08 | 4 |
| legacy | 0.40 | 8.625 | 43 | 0.0790 | 6.4e+00 | 2.2e+04 | 4 |
| projected-energy | 0.25 | 9.974 | 4 | 0.0007 | 3.9e-02 | 5.8e+08 | 4 |
| projected-energy | 0.40 | 9.870 | 43 | 0.0860 | 6.9e+00 | 1.9e+04 | 4 |

- La magnitud mecánica cambia (TE pp +14 %, consistente con la Fase 2), pero la **estructura de identificabilidad no**: mismos puntos cargados, misma jerarquía de valores singulares, misma condición de Fisher dentro de ~20 %.
- Recuperación sin ruido exacta en las 4 configuraciones (error escalado ≤ 2.6e-13): el operador inverso cierra el ciclo con ambas formulaciones.

## (4.3) Monte Carlo con ruido (σ = 0.1 µm, 100 semillas por celda)

Errores escalados (|Δθ|/SCALE; mediana / p90):

| Variante | s_d | adendum med/p90 | dedendum med/p90 | RMSE perfil med (µm) | χ² med (ref. 116) |
|---|---:|---:|---:|---:|---:|
| legacy | 0.25 | 0.002 / 0.003 | **0.369 / 4.500** | 0.835 | 115 |
| legacy | 0.40 | 0.002 / 0.003 | 0.108 / 0.330 | 0.280 | 114 |
| projected-energy | 0.25 | 0.002 / 0.003 | **0.374 / 4.500** | 0.833 | 115 |
| projected-energy | 0.40 | 0.002 / 0.003 | 0.104 / 0.295 | 0.271 | 114 |

Lectura:

1. **Adendum: identificable en todos los regímenes**, con precisión ~200 veces mejor que la escala del parámetro, en ambas variantes.
2. **s_d = 0.25 (intersección marginal): señal 0.0006–0.0007 µm frente a ruido 0.1 µm** — el dedendum no es identificable en la práctica: mediana del error 0.37·SCALE y cola pesada (p90 = 4.5·SCALE; una fracción de ajustes golpea el límite C_d = 50 µm). Esto es exactamente lo que afirma el manuscrito: *la intersección no garantiza precisión*.
3. **s_d = 0.40 (intersección amplia): dedendum recuperado con precisión práctica** (mediana 0.10·SCALE, p90 0.30, RMSE de perfil ~0.27 µm) — identificable, no exacto.
4. **Las diferencias legacy vs projected-energy son de segundo orden** (medianas dentro del 5 %, p90s dentro del 12 %). La conclusión cualitativa es **invariante a la formulación del compliance**.
5. Los χ² medios (114–115) coinciden con n_obs − n_par = 116: los ajustes son estadísticamente consistentes con el modelo generador en ambas variantes; no hay señal de falta de ajuste interna.

## Veredicto sobre la pregunta central

- **La condición suficiente de invisibilidad sigue siendo válida** en projected-energy (demostración geométrica + confirmación numérica del barrido).
- **La conclusión del manuscrito sobrevive al cambio de formulación**: dependencia del soporte de contacto, no-garantía de precisión con intersección marginal, recuperación práctica con intersección amplia. Las cifras absolutas de TE cambian (+14 %), las de identificabilidad prácticamente no.
- **Acotación honesta**: estos experimentos son mismo-operador (inverse crime). La Fase 3 fijó el límite externo: la discrepancia estructural con el benchmark (~9–38 %) y el residual FE↔analítico (~0.1 µm en TE) dominan cualquier diferencia entre formulaciones. La elección legacy vs projected-energy es de segundo orden frente a la incertidumbre del modelo de sistema completo.

## Consecuencia para el manuscrito (v7)

Las afirmaciones de identificabilidad pueden mantenerse con la formulación projected-energy y deben presentarse como **independientes de la formulación del compliance** (robustez demostrada). La magnitud absoluta de TE reportada cambia (+14 %) y debe actualizarse donde aparezca. La validación cuantitativa frente al benchmark externo queda acotada como discrepancia estructural documentada (Fase 3), no como validación cumplida.
