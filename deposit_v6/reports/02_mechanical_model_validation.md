# Fase 2 — Revisión mecánica del modelo de compliance

**Fecha:** 2026-10-22 · **Rama:** `research/mmt-critical-validation`
**Scripts:** `reports/phase2_mechanical_audit.py` → `02_mechanical_components.json`; `reports/phase2_minimal_identifiability.py` → `02_identifiability_variants.json`
**Cambio de código registrado:** `src/mechanics/compliance.py` — los arreglos de integración `I_x/A_x` ahora toman su longitud de la regla de cuadratura (`n_q = len(self._quadrature[0])`) y se elimina la línea muerta `xs`. La regla por defecto (24 puntos Gauss–Legendre) es numéricamente idéntica a la histórica; el cambio solo habilita reglas refinadas para chequeos de convergencia. **37/37 pruebas pasan tras el cambio.**

---

## 2.1 Auditoría dimensional y energética (ecuaciones 5–8)

Desglose por componentes recomputado **independientemente** del código (duplicación de auditoría) y cotejado contra `ToothCompliance.flexibility`: diferencia relativa máxima **1.7e-16** en las 4 variantes — la integración del modelo es exactamente la declarada. Ejemplo (piñón G0, u = 0.5, αᵣ ≈ 26.6°):

| Término (mm/N) | legacy | shear-G | projected-energy | centerline-energy |
|---|---|---|---|---|
| Flexión | 4.450e-07 | 4.450e-07 | 1.751e-07 | (ver JSON) |
| Cortante | 2.489e-07 (con **E** ✗) | 6.468e-07 (con G ✓) | 5.177e-07 (G·cos²αᵣ) | 5.19e-07 aprox. |
| Axial | — | — | 4.148e-08 (E·sin²αᵣ) | incluido |
| Fundación | 1.905e-07 | 1.905e-07 | 1.905e-07 | 1.905e-07 |
| **Total** | 8.844e-07 | 1.302e-06 | 9.248e-07 | 9.25e-07 |

Verificaciones dimensionales: [M²/(E·I)]·dx y [1/(G·A)]·dx dan mm/N ✓; factor de forma rectangular 1.2 ✓; Hertz: a_H [mm], w_H [mm] con E* compuesto ✓.

**Diagnóstico del «baseline mejor que lo físico»:** el modelo `legacy` comete dos errores que se compensan: (i) usa E en vez de G en el cortante (subestima la flexibilidad cortante por un factor E/G = 2.6) y (ii) usa el brazo de flexión completo (h−x) sin proyección cos αᵣ ni el término de offset del flanco (sobreestima la flexibilidad de flexión por ~1/cos² y más). Los dos errores tienen signo opuesto y magnitudes comparables; su compensación es accidental, no física. La variante `projected-energy` corrige ambos con la descomposición de Castigliano:

> c = ∫₀ᴴ [((h−x)cos αᵣ − ½t_c sin αᵣ)²/(EI) + 1.2 cos²αᵣ/(GA) + sin²αᵣ/(EA)] dx + cos²αᵣ/(Eb)

con G = E/2(1+ν). El brazo incluye el momento del componente radial aplicado sobre la cara del flanco (signo menos verificado geométricamente).

**Limitaciones declaradas de la formulación adoptada:** ángulo de proyección αᵣ constante a lo largo de la viga; término de fundación de orden de magnitud (cos²αᵣ/Eb); sin filete de raíz ni acoplamiento de cuerpo; no es el método ISO 6335 completo. Es una **ablación mecánicamente consistente**, no un FEM.

## 2.2 Separación modelo histórico / modelo físico

- **`legacy` queda como referencia histórica reproducible** (todas las campañas almacenadas de manuscript-v6 lo usan; no se reescriben resultados).
- **`projected-energy` se adopta como formulación mecánica consistente para los nuevos experimentos** (Fases 3–4), por: módulo de cortante correcto, descomposición de energía de deformación consistente, y el cumplimiento de todas las pruebas de consistencia (§2.3). La selección **no** se basa en la concordancia con el benchmark (que se examina aparte en la Fase 3).
- `centerline-energy` queda como ablación geométrica adicional; sus resultados se reportan en el JSON pero no se adopta (integra sobre la línea media curva con la misma fundación simple; sin ventaja de consistencia clara sobre `projected-energy`).

## 2.3 Validación mecánica interna (resumen del JSON)

| Prueba | legacy | projected-energy | Criterio |
|---|---|---|---|
| Compliance positivo en [0.02, u_tip] | ✓ (2.38e-07…1.63e-06) | ✓ (2.38e-07…1.49e-06) | c > 0 |
| Salto máximo relativo de c(u) | 1.3e-02 (en u ≈ 0.569, **nudo del clamp de espesor**) | 1.1e-02 (mismo nudo) | continuidad a trozos |
| Monotonicidad del acercamiento de par (margen min c − 2K) | +7.19e-07 ✓ | +9.77e-07 ✓ | certificación del operador |
| Convergencia de cuadratura (24 vs 96 pt) | 3.0e-02 en c(u) | 2.2e-02 en c(u) | ver nota abajo |
| — efecto neto en TE_pp (24→96) | — | **2e-09** | despreciable → se conservan 24 pt |
| Convergencia angular TE_pp (120→480) | 0.40 % | 0.24 % | < 1 % |
| Convergencia de derivadas (paso óptimo) | err 9.0e-07 @ h=1e-5 | err 3.4e-06 @ h=1e-5 | consistente con h_rel=1e-4 usado |
| Rigidez incremental dS/dδ analítica vs DF | 4.0e-12 | 6.2e-12 | exacta |
| Transiciones 1↔2 pares | 2 transiciones/ciclo; fuerza total estable a 1.7e-08 N; salto del par entrante 2.2 kN entre posiciones adyacentes (dφ ≈ 0.026°) | idem (2.6 kN) | entrega física, sin oscilación |
| Simetría par idéntico (57/57, 650 Nm) | — | residual antisimétrico **4.3e-11 µm** | simetría exacta |

**Nota de cuadratura:** el error del integrador de 24 puntos (2–3 % en c(u)) se concentra en la zona de raíz (quiebre del clamp de espesor 0.2m), donde la carga transportada es pequeña; su efecto sobre TE del operador completo es ~1e-9. Se conserva la cuadratura histórica de 24 puntos y queda documentada la posibilidad de refinamiento.

## 2.4 Efecto sobre la identificabilidad (G0, 300 Nm, 120 posiciones)

| Config | s_d | TE_pp (µm) | ΔTE_pp vs legacy | ξ_min cargado | rango | SV mín. (escalado) | Recuperación sin ruido (err. dedendum escalado) |
|---|---|---|---|---|---|---|---|
| legacy-24 | 0.25 | 8.726 | — | 0.2356 | 4 | 0.0358 | 2.4e-13 |
| legacy-24 | 0.40 | 8.625 | — | 0.2356 | 4 | 6.370 | 1.0e-15 |
| projected-24 | 0.25 | 9.974 | +14.3 % | 0.2356 | 4 | 0.0392 | 2.4e-13 |
| projected-24 | 0.40 | 9.870 | +14.4 % | 0.2356 | 4 | 6.890 | 2.6e-16 |
| projected-96 | 0.25 | 9.974 | +14.3 % | 0.2356 | 4 | 0.0392 | 1.5e-13 |
| projected-96 | 0.40 | 9.870 | +14.4 % | 0.2356 | 4 | 6.890 | 1.6e-15 |

**Lectura:** la reformulación del compliance cambia la amplitud de TE (+14 %, más flexible) pero **no altera la estructura de identificabilidad**: soporte de contacto (ξ_min), rango, valores singulares (Δ < 0.05 %) y recuperación sin ruido son invariantes en la práctica. La conclusión central del manuscrito (el soporte de contacto gobierna la observabilidad del dedendum) es robusta a esta corrección mecánica. La verificación con ruido y el contraste de conclusiones se ejecutan en la **Fase 4**.

### Criterio de aceptación

✅ **Satisfecho.** La formulación adoptada tiene justificación física explícita (Castigliano con G correcto), supera las pruebas de consistencia (positividad, equilibrio, complementariedad, monotonicidad, simetría, convergencias, rigidez incremental) y permite comparación trazable con el modelo histórico. No se forzó concordancia alguna con el benchmark externo.
