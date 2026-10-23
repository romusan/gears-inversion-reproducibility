# MMT — Informe final de revisión crítica

**Manuscrito:** *Contact support and practical identifiability of spur gear microgeometry from transmission error*
**Revisión:** v6 (congelada, 12-oct-2026) → **v7** (22-oct-2026)
**Rama:** `research/mmt-critical-validation` · Repo: `gears_inversion/deposit_v6` (github.com/romulan/gears-inversion-reproducibility)
**Estado de pruebas:** 37/37 en verde durante toda la revisión.
**Commits:** `d74914d` Fase 0 · `1fde127` Fase 1 · `3f9ab4a` Fase 2 · `4fbcf94` Fase 3 · `9733fa5` Fase 4 · `89d7efc` Fase 5/6

---

## A. Problemas detectados

| # | Problema | Fase | Severidad |
|---|----------|------|-----------|
| A1 | La ecuación (9) incluía el factor (1+γ), pero γ no se estima en ninguna campaña y solo existe en el experimento archivado E04 (BIAS_GAMMAS = 1, 3, 5 %): el modelo de observación declarado no era el usado | 1 | Alta (declaración incorrecta) |
| A2 | El compliance baseline usaba E en el término de cortante (debe ser G = E/2.6), sin proyección de la fuerza ni brazo de flexión corrido: ley mecánica incorrecta, compensada por el brazo sin proyectar | 2 | Alta (física) / baja (identificabilidad) |
| A3 | El benchmark externo (Korta–Mundo, 12 puntos) nunca cumplió el objetivo del 5 %: sobre-predicción sistemática 9.07–38.08 % | 0/3 | Alta (validación externa ausente) |
| A4 | Toda la evidencia de inversión era mismo-operador (inverse crime): no existía validación cruzada ni física | 3 | Alta |
| A5 | Las conclusiones no estaban acotadas frente a la formulación del compliance ni frente a la discrepancia entre operadores mecánicos | 4 | Media |

## B. Correcciones aplicadas (archivos y pruebas)

- **Fase 0** (`reports/baseline_audit.py`, `00_baseline_audit.md/.json`): línea base v6 reproducida a precisión de máquina — 12/12 celdas Monte Carlo exactas (resumen 0.394 verificado = 0.39389), barrido de soporte idéntico (diff ≤ 1.9e-15), forward G0@300 Nm: residuo de fuerza 1.7e-8, complementariedad 1.9e-15.
- **Fase 1** (`tests/test_observation_model.py`, 10 pruebas nuevas; `01_observation_model_audit.md`): política de γ auditada y fijada; coherencia ruido/Fisher verificada. Decisión: eq (9) sin γ.
- **Fase 2** (`src/mechanics/compliance.py`, `02_mechanical_model_validation.md`, `02_identifiability_variants.json`): corrección del cortante (G·cos², axial E·sin², brazo proyectado) bajo `projected-energy`; limpieza de `n_q` y línea muerta; cuadratura de 24 pt conservada (efecto 2e-9 en TE). Decisión: `projected-energy` como formulación de referencia, selección NO basada en el benchmark.
- **Fase 3** (`phase3_benchmark.py`, `fe2d/phase3_fe_cycle.py`, `phase3_cross_inverse.py`; `03_independent_validation.md`): benchmark recalculado (0/12 en ambas formulaciones); ciclo FE de 25 fases × 4 casos; inversa cruzada FE→analítico.
- **Fase 4** (`phase4_robustness.py`; `04_identifiability_robustness.md`): barrido de transición (61 puntos × 2 variantes), 400 ajustes Monte Carlo con ruido (100 semillas declaradas, base 20261022, por celda).
- **Fase 5** (`gears_inversion/manuscript/`): `MMT_manuscript_Q1_revision_v7.docx` + suplementario S1–S11; pipeline retrocompatible (`math_revision=6` por defecto reproduce v1–v6; verificación OMML token a token).
- **Fase 6**: este informe.

## C. Tablas comparativas v6 → v7

**Magnitudes mecánicas (G0, 300 Nm, 120 obs):**

| Magnitud | v6 (legacy) | v7 (projected-energy) | Cambio |
|---|---|---|---|
| TE pico a pico, s_d=0.25 | 8.726 µm | 9.974 µm | +14.3 % |
| TE pico a pico, s_d=0.40 | 8.625 µm | 9.870 µm | +14.4 % |
| ξ_min cargado | 0.2356 | 0.2356 | 0 % |
| Umbral de visibilidad (s_d) | 0.24 | 0.24 | igual |
| Valor singular mínimo (s_d=0.25/0.40) | 3.6e-2 / 6.4e0 | 3.9e-2 / 6.9e0 | ~10 % |
| Recuperación sin ruido | exacta | exacta | igual |
| MC dedendum mediana (s_d=0.25/0.40, σ=0.1 µm) | 0.369 / 0.108 | 0.374 / 0.104 | <6 % |

**Ecuación (9):** v6: `y = (1+γ)F(θ*) + ε` → v7: `y = F(θ*) + ε`, con el sesgo de ganancia descrito en §2.3 como molestia no modelada (datos E04: a γ=5 %, C_d se mueve hasta 0.045 mm y s_d hasta 0.14; adendum como máximo 0.0024 mm y 0.012).

**Benchmark externo (12 puntos, error relativo):** legacy 9.07–38.08 %; projected-energy 17.9–54.0 %; 0/24 cumple el 5 %.

**Inversa cruzada (generador FE → inversor analítico, 19 fases interiores):**

| Resultado | Valor |
|---|---|
| ĥ (verdad 0.020 mm) | 0.0175 (legacy) / 0.0206 (projected-energy) — ≤5 % de escala |
| RMSE TE en fases observadas | 0.109 / 0.151 µm |
| Dedendum estimado | espurio: 0.01–0.02 mm (verdad 0–0.005) — absorbente de discrepancia |
| Invisibilidad dedendum en FE | exacta en las 25 fases (dedendum ≡ addendum) |

## D. Clasificación de la evidencia por categoría de validación

| Categoría | ¿Cumplida? | Evidencia |
|---|---|---|
| Verificación numérica (mismo operador) | **Sí** | Reproducción a precisión de máquina (Fase 0); controles FE: residuos <4e-12, torque ±4e-6, convergencia de malla 0.97/0.70 %, patch tests |
| Recuperación interna (genera e invierte el mismo modelo) | Sí, acotada | Monte Carlo 1200 + 400 ajustes; mide sensibilidad al ruido, NO precisión física |
| Validación cruzada (FE genera, analítico invierte) | **Parcial** | Mecanismo cualitativo confirmado (visibilidad/invisibilidad); precisión absoluta acotada a ~0.1 µm TE; dedendum pequeño no interpretable |
| Validación frente a referencia externa (Korta–Mundo) | **No** | 0/24 dentro del 5 %; discrepancia estructural; hipótesis de causa (sujeción/acoplamiento) sin cierre |
| Validación experimental | **Ausente** | No hay datos de banco; es el vacío principal |

## E. Conclusiones del manuscrito: estado tras la revisión

**Sobreviven (reforzadas):**
1. La condición suficiente de invisibilidad por soporte de contacto — es geométrica, demostrada para el operador declarado y ahora **confirmada por un operador mecánico independiente** (FE) en ciclo completo.
2. "La intersección no garantiza precisión": en s_d=0.25 (4 puntos cargados, señal 0.0006 µm vs ruido 0.1 µm) la mediana del error es 0.37–0.37·SCALE con cola hasta el tope — no identificable en la práctica.
3. El adendum es identificable en todos los regímenes (mediana 0.002·SCALE).
4. El diagnóstico pre-inversión ξ_min vs rango de s_d — invariante a la formulación del compliance.
5. La invarianza de las conclusiones a la formulación mecánica (legacy vs projected-energy: diferencias <6 % en medianas).

**Acotadas:**
1. Las magnitudes absolutas de TE cambian +14 % con la formulación corregida (tablas actualizadas en v7).
2. La precisión práctica del pipeline de inversión está acotada por el residual entre operadores independientes: ~0.1 µm en TE.
3. Un dedendum estimado pequeño puede ser absorción de discrepancia de modelo, no relieve real.

**Retiradas o corregidas:**
1. La ecuación (9) con (1+γ) (A1).
2. Cualquier sugerencia de que corregir el cortante acerca al benchmark: **empeora** (18–54 % vs 9–38 %).
3. Cualquier lectura implícita de validación frente a Korta–Mundo: nunca se cumplió el 5 % y v7 lo declara explícitamente.

## F. Limitaciones pendientes (declaradas en v7)

1. FEM generador: cubo de 25 mm **asumido**, raíz aproximada (trim 0.4 mm), deformación plana, P1, sin fricción ni 3D.
2. 6/25 fases del ciclo FE restringidas por la ventana de contacto; la inversa usa solo fases interiores.
3. El CAD y las restricciones del benchmark publicado son desconocidos: la discrepancia estructural queda con hipótesis pero sin cierre.
4. γ no es estimable con las campañas actuales (solo existe el experimento archivado E04 con 2 semillas por nivel).
5. La cobertura de los perfiles de verosimilitud no está certificada cerca de fronteras/direcciones débiles.
6. Sin datos experimentales de transmisión.

## G. Prioridades recomendadas

1. **Datos experimentales** (TE medido de un par con geometría medida) — la única vía a validación física plena.
2. **Modelo de sistema completo** (sujeción/llanta/eje, idealmente 3D) para cerrar o cuantificar la discrepancia del benchmark; la sensibilidad al cubo (k₂/k₁ de 1.32 a 1.43) dice que la sujeción es el primer candidato.
3. **Ciclo FE continuo con contacto de esquina** para recuperar las fases de entrada/salida hoy excluidas.
4. Estimación conjunta de γ o calibración de cadena si llegan datos reales.
5. DOI del repo (p. ej. Zenodo) y etiqueta `manuscript-v7` antes del envío.

## Recomendación final sobre el envío

**v7 está lista como manuscrito honesto y defendible, pero no cumple el estándar de validación de un Q1 experimental.** La revisión convirtió afirmaciones débiles en evidencia clasificada (sección D): el núcleo identificabilidad/soporte está validado cruzadamente y es robusto; la validación externa y experimental sigue abierta y v7 lo declara sin ambigüedad.

- **Enviar a MMT ahora:** no recomendado — el benchmark externo incumplido y la ausencia de validación experimental son objeciones previsibles de revisión.
- **Enviar a un journal del scope que acepte caracterización numérica con validación cruzada y limitaciones explícitas:** viable con v7 (ver sección H).
- **Esperar a cerrar el ciclo FE de sistema completo o a obtener datos de banco:** la opción más fuerte para MMT/MSSP.

## H. Journals del scope a considerar (verificar cuartil vigente al envío)

- *Mechanism and Machine Theory* — teoría de mecanismos y engranajes.
- *Mechanical Systems and Signal Processing* — exigente en validación experimental.
- *Journal of Sound and Vibration* — dinámica de engranajes/TE.
- *Inverse Problems in Science and Engineering* — problemas inversos; más receptivo a caracterización numérica.

La elección condiciona el tono: con datos experimentales, MSSP/JSV; sin ellos, MMT o IPSE con las limitaciones explícitas de v7.
