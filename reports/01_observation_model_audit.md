# Fase 1 — Auditoría del modelo de observación y de la inversión

**Fecha:** 2026-10-22 · **Rama:** `research/mmt-critical-validation`
**Pruebas nuevas:** `tests/test_observation_model.py` (10 pruebas) · **Total:** 37 passed (27 previas + 10 nuevas)
**Script de apoyo:** verificación directa en código (sin cambios de modelo)

---

## 1.1 Cómo se generan los datos (respuestas verificadas en código)

| Pregunta del protocolo | Respuesta | Evidencia |
|---|---|---|
| ¿Se utiliza realmente γ? | **Solo en los casos de sesgo de E04** (`BIAS_GAMMAS = [0.01, 0.03, 0.05]`, con σ = 0.1 µm). En todas las campañas Q1 (Monte Carlo, perfiles, barridos, controles complementarios) **γ no aparece**. | `experiments/E04_noise_bias.py:62,97-98`; ausencia en `Q1_identifiability_campaign.py`, `Q1_review5_monte.py` |
| ¿γ = 0 en todas las simulaciones de ruido? | **Sí.** Las tareas de ruido se encolan con `gamma=0.0` (E04, línea 112); los generadores Q1 no tienen γ. | `E04_noise_bias.py:112` |
| ¿La observación se centra antes de adicionar ruido? | **Sí.** La predicción del operador ya es `δ − media(δ)` (ciclo centrado); el ruido i.i.d. se suma después. | `batched_operator.py:119`; `transmission_error.py:63-64`; `Q1_review5_monte.py:18-20` |
| ¿Las curvas de diferentes cargas se centran individualmente? | **Sí.** Cada operador/predicción centra su propia media de δ antes de apilar; no hay centrado del vector apilado. | `Q1_identifiability_campaign.predict` (concatenación de predicciones ya centradas) |
| ¿El ruido se añade de manera independiente? | **Sí.** `rng.normal(0, sigma, N)` i.i.d. por realización; en el control complementario los errores se asignan por índice de fase canónico, no por fila concatenada. | `Q1_identifiability_campaign.py:140`; `Q1_review5_monte.py:18-20` |
| ¿Se aplica algún centrado adicional a los datos simulados? | **No.** La media realizada del ruido contribuye al costo y no altera gradientes. | prueba `test_noise_added_to_centered_prediction_keeps_mean_unremoved` |
| ¿La función objetivo coincide con el modelo de observación? | **Sí.** Residuos blanqueados `(pred − y)/σ`; `cost = ½‖r‖²`. Coherencia verificada incluido gradiente `Jᵀr/σ` contra diferencias finitas. | `Q1_identifiability_campaign.fit:48-51`; prueba `test_residual_objective_coherence` |
| ¿La Fisher usa la covarianza correcta? | **Sí.** `J_q = σ⁻¹(∂F/∂θ)diag(s)`, `𝓘 = J_qᵀJ_q`, covarianza σ²I (no proyectada, pues no hay centrado posterior al ruido). Duplicar σ divide 𝓘 por 4 — verificado. | `fisher_optimal_loads.py`; prueba `test_fisher_matches_noise_model_and_implicit_tangent` |

## 1.2 Corrección de la inconsistencia γ — decisión documentada

**Problema:** la ecuación (9) del Word (`y_ℓi = (1+γ)F_ℓi(θ*) + ε_ℓi`) sugiere que γ forma parte del modelo estadístico general, pero (i) γ = 0 en todos los experimentos de ruido del manuscrito, (ii) cuando γ ≠ 0 (E04-bias) **no se estima** ni aparece en la ecuación (10) ni en el código, y (iii) el texto Markdown fuente ya lo omite.

**Decisión (sin introducir un quinto parámetro):**
1. La ecuación (9) de la v7 se reescribe al modelo efectivamente usado por todos los experimentos de ruido: `y_ℓi = F_ℓi(θ*) + ε_ℓi`, `ε ~ N(0, σ²I)`.
2. El sesgo multiplicativo se describe en la sección del experimento de sesgo (E04) como **perturbación no modelada** (`y = (1+γ)F + ε` con γ ∈ {1, 3, 5} % conocido del generador pero no estimado por el inversor), explícitamente fuera del modelo de observación principal.
3. Se conserva la nota sobre la covarianza proyectada σ²(I − 11ᵀ/N) **solo** como advertencia metodológica (qué modelo usaría un pipeline que centrara después del ruido), sin intercambiarlo con el pipeline actual.

La aplicación al documento Word es parte de la Fase 5 (actualización controlada a v7); aquí queda fijada la decisión y su justificación.

## 1.3 Verificación del tratamiento del ruido

- **Pipeline actual:** centrado de F → ruido i.i.d. → objetivo blanqueado. Covarianza σ²I, rango pleno. **Correcto y consistente con la Fisher.**
- **Modelo alternativo (proyectado):** solo aplicaría si se centrara la observación tras añadir ruido; entonces Σ_c = σ²(I − 11ᵀ/N) es singular (rango N−1) y exigiría base ortonormal del subespacio centrado o formulación reducida. **No se usa en ningún experimento; no se requiere modificación.** La advertencia se conserva en el manuscrito como nota metodológica.

## 1.4 Pruebas implementadas (`tests/test_observation_model.py`)

| Prueba | Verifica |
|---|---|
| `test_seed_reproducibility_of_noise` | Reproducibilidad con semillas fijas |
| `test_prediction_is_cycle_centered` (×3 cargas) | Centrado correcto de cada curva |
| `test_noise_added_to_centered_prediction_keeps_mean_unremoved` | Política de no re-centrado; covarianza σ²I |
| `test_stacked_jacobian_dimensions_two_loads` | Dimensiones del Jacobiano apilado (120×4) |
| `test_residual_objective_coherence` | Residuos ↔ objetivo; gradiente analítico vs FD |
| `test_fisher_matches_noise_model_and_implicit_tangent` | Fisher ↔ modelo de ruido y tangente implícita |
| `test_fixed_parameter_and_bounds_policy` | Parámetros fijados y límites físicos |
| `test_gamma_is_zero_in_noise_campaigns` | Política γ = 0 en campañas de ruido (guarda de regresión) |

Las comprobaciones «derivadas analíticas vs diferencias finitas» ya existían (`test_implicit_contact_tangent`, `test_relief_derivatives_against_perturbations`, `test_hertz_compliance_derivative_including_clipped_branch`) y siguen pasando.

## Criterio de aceptación

✅ **Satisfecho.** Ecuaciones del manuscrito (tras la corrección de la Fase 5), funciones implementadas y experimentos describen exactamente el mismo problema estadístico: observación centrada antes del ruido, ruido i.i.d. σ²I, objetivo blanqueado coherente, Fisher sin piso artificial y consistente con el modelo de ruido.
