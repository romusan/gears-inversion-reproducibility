# Fase 3 — Validación mecánica independiente (FEM, benchmark, inversa cruzada)

Fecha: 2026-10-22 · Rama: `research/mmt-critical-validation`
Scripts: `reports/phase3_benchmark.py`, `reports/phase3_cross_inverse.py`, `fe2d/phase3_fe_cycle.py` (driver, copia raíz `gears_inversion/fe2d`)
Datos: `results/independent_validation/03_benchmark_reproduction.json`, `03_fe_cycle_v2.jsonl`, `03_cross_inverse.json`

## Alcance

Esta fase contrasta el modelo analítico de contacto del manuscrito (viga + Hertz, `GearContactModel`) con una fuente mecánica **independiente**: un modelo de elementos finitos 2D propio (`run_fe2d`, scikit-fem + gmsh), y con el benchmark publicado de Korta–Mundo (datos FE externos). Tres productos:

1. **(3.1) Auditoría del FEM** — verificación numérica del código FE utilizado como generador.
2. **(3.3) Reproducción del benchmark** — los 12 puntos de referencia (4 configuraciones × 3 torques) recalculados con ambas variantes de compliance (legacy y projected-energy).
3. **(3.2 + 3.5) Curva FE completa e inversa cruzada** — ciclo de 25 fases generado por el FE, invertido con el operador analítico. Generador ≠ inversor: esto es, por primera vez en el proyecto, una validación cruzada y no una recuperación interna.

## (3.1) Auditoría del FEM

El código FE (`gears_inversion/fe2d/run_fe2d.py`) fue auditado en fases anteriores y sus controles numéricos quedaron registrados en `fe2d/results/campaign.json` y resumidos en `fe2d/resultado_FE2D.md`:

- **Formulación:** elasticidad plana (deformación plana), elementos P1 nodales (triángulos, h = 0.5 mm en el caso nominal), contacto unilateral sin fricción, normales fijas en la dirección LOA, pequeñas deformaciones.
- **Convergencia de malla:** en tres niveles de refino, el último cambio de rigidez es 0.974 % (un par) y 0.697 % (dos pares). Duplicar la discretización del contorno y ampliar el semiancho de contacto de 0.35 a 0.50 mm cambia cada rigidez menos de 0.121 %.
- **Solidez (patch tests):** deformación constante, energía y rotación rígida pasan. Residuo elástico relativo < 3.92e-12, residuo de contacto < 2.78e-17 mm, residuo de fuerza < 3.64e-12 N. Error relativo máximo de torque 4.06e-06. La rigidez tangente coincide con diferencias de fuerza ±0.1 % dentro de 1.21e-13 relativo.
- **Hipótesis geométricas documentadas (limitaciones explícitas):** cubo rígido empotrado de radio **asumido** 25 mm (no reproduce el eje real del benchmark), transición de raíz aproximada con recorte (root_trim) de 0.4 mm (no reproduce el contorno de herramienta real), sin contacto de esquina, sin efectos de ancho (3D).

Veredicto de auditoría: el código FE es numéricamente correcto y convergente **dentro de sus hipótesis declaradas**. No reproduce el CAD ni las restricciones desconocidas del benchmark publicado; se emplea como generador independiente exploratorio, no como verdad experimental.

## (3.3) Reproducción del benchmark Korta–Mundo

Los 12 puntos de referencia (TE pico a pico, 4 configuraciones × 350/500/650 Nm) se recalcularon con `phase3_benchmark.py`. Resultado (`03_benchmark_reproduction.json`):

| Variante | rango de error relativo | 0/12 cumple 5 % |
|---|---|---|
| legacy | 9.07 % – 38.08 % | ✗ (todo sobre-predice) |
| projected-energy | 17.9 % – 54.0 % | ✗ (todo sobre-predice, más que legacy) |

Dos conclusiones:

1. **La discrepancia del benchmark es estructural, no atribuible al término de cortante del compliance.** La corrección de la Fase 2 (G en lugar de E en el cortante, con brazo proyectado) no acerca el modelo a la referencia externa; lo aleja. La diferencia procede de otra parte: rigidez del sistema (sujeción, llanta, eje), acoplamiento cruzado entre pares, o la propia referencia.
2. Los valores recalculados con legacy **reproducen exactamente** los almacenados en el código del manuscrito: la tabla del benchmark estaba bien transcrita; lo que no se cumple es el criterio de validación del 5 %.

## (3.4) Análisis de discrepancias (del contraste FE nominal a 650 Nm)

Del contraste FE documentado en `fe2d/resultado_FE2D.md`:

- Rigidez incremental FE: k₁ = 239.18 N/µm (un par), k₂ = 327.06 N/µm (dos pares); razón k₂/k₁ = 1.367 frente a 1.545 del modelo analítico en las mismas fases.
- **Sensibilidad a la sujeción:** con cubo de 20/25/35 mm, k₂/k₁ varía de 1.323 a 1.426. La incertidumbre física de la sujeción **supera** los cambios del último refinamiento de malla (< 1 %); no puede resolverse forzando una coincidencia aislada de amplitud.
- **Acoplamiento cruzado:** al anular los bloques de flexibilidad cruzada entre los dos pares, k₂ pasa de 327.06 a 408.13 N/µm; el acoplamiento reduce la rigidez un 19.9 % en el modelo FE supuesto. Es un efecto real del FE, pero no demuestra por sí solo que explique toda la discrepancia del benchmark.

## (3.2) Ciclo FE completo (25 fases, 650 Nm, 57/57)

Driver `fe2d/phase3_fe_cycle.py` (copia raíz con `.venv` gmsh/scikit-fem; raíz de resultados en `deposit_v6`). Cuatro casos: `unmodified`, `addendum` (h=0.02, ξₐ=0.75), `dedendum` (h=0.005, ξₐ=0.30), `dedendum-deep` (h=0.005, ξₐ=0.45). Relieve de piñón p=2 aplicado como gap += h(ξ).

**Respuesta al "si no es posible" del protocolo:** un ciclo completo validado no existe en este FEM — las fases de entrada/salida de contacto quedan restringidas por la ventana nominal del parche (`restricted_nominal_window`), con dominios de contacto recortados (`clipped_contact_domains`). Se excluyen 6 de 25 fases (0.28, 0.32, 0.36, 0.64, 0.68, 0.72) y la inversa usa solo las **19 fases interiores**. Esto se documenta como limitación, no se corrige.

Resultados (`03_fe_cycle_v2.jsonl`):

- Fase 0: δ = 39.199 µm, coincidente con la campaña FE almacenada (39.1986 µm) — coherencia interna del generador.
- Régimen de un par: δ ≈ 39.2 – 40.4 µm; régimen de dos pares: δ ≈ 28.6 – 29.1 µm.
- δ pp en fases interiores: **11.818 µm** (unmodified), frente a 10.527 µm del benchmark a 650 Nm (interior, configuración sin modificar).
- Caso addendum: δ aumenta entre **+0.35 y +6.72 µm** respecto a unmodified en fases interiores.

**Hallazgo científico mayor:** el relieve de dedendum es **completamente invisible** para el FE en las 25 fases — los casos `dedendum` y `dedendum-deep` producen valores idénticos a `addendum` (diferencia exactamente cero, verificada aserción a aserción). El relieve de dedendum (ξ ∈ [0.30, 0.45]) no intersecta la zona cargada en ninguna fase del ciclo. Esto es una **confirmación cruzada independiente** del mecanismo central del manuscrito (la condición suficiente de invisibilidad por soporte de contacto), obtenida con un operador mecánico distinto del analítico.

## (3.5) Inversa cruzada (generador FE → operador analítico inverso)

`phase3_cross_inverse.py`: y = δ_FE − media sobre las 19 fases interiores, φ = fracción·2π/57; inversor = `build_pair()` (57/57) + `BatchedGapOperator` a 650 Nm con las variantes legacy y projected-energy; ajuste `bestfit` (2 inicios, SCALE y BOUNDS de la campaña Q1). σ = 0.1 µm. Salida: `03_cross_inverse.json`.

| Variante | caso | ĥ | ξ̂ₐ | error adendum (escala) | error dedendum (escala) | RMSE TE (µm) | pp pred/FE (µm) |
|---|---|---:|---:|---:|---:|---:|---|
| legacy | addendum | 0.0175 | 0.741 | 0.051 | 2.00 (espurio) | 0.109 | 12.30 / 12.42 |
| legacy | dedendum | = idéntico | = | 0.051 | 1.50 | 0.109 | 12.30 / 12.42 |
| legacy | dedendum-deep | = idéntico | = | 0.051 | 1.50 | 0.109 | 12.30 / 12.42 |
| projected-energy | addendum | 0.0206 | 0.772 | 0.022 | 1.00 (espurio) | 0.151 | 12.90 / 12.42 |
| projected-energy | dedendum | = idéntico | = | 0.022 | 0.50 | 0.151 | 12.90 / 12.42 |
| projected-energy | dedendum-deep | = idéntico | = | 0.022 | 0.50 | 0.151 | 12.90 / 12.42 |

(Soporte analítico cargado: ξ_min = 0.695 en todos los casos; señal analítica del addendum ≈ 2.3 µm RMS. Referencia unmodified, pp interior: FE 11.818, legacy 11.565, projected-energy 12.640 µm.)

Interpretación:

1. **El relieve de addendum sí es recuperable de datos FE con el inversor analítico**, en ambas variantes y con las dos fases del ciclo: ĥ = 0.0175 (legacy) y 0.0206 (projected-energy) frente a verdad 0.02; error ≤ 0.051·SCALE (5 % de la escala del parámetro). La validación cruzada confirma que el operador inverso extrae el relieve **donde el relieve intersecta la zona cargada**.
2. **La no-recuperación del dedendum no es un fallo del inversor: el generador FE no produjo señal dedendum alguna.** Como los datos FE de los tres casos son idénticos, el ajuste es idéntico. El inversor no puede inventar una señal que el generador no contiene.
3. **El dedendum estimado es espurio** (0.01–0.02 mm donde la verdad es 0 o 0.005): es el grado de libertad que absorbe la discrepancia de modelo FE↔analítico. Con RMSE TE residual de 0.109–0.151 µm en las fases observadas, un relieve dedendum ficticio de ~0.01–0.02 mm es el síntoma observable del sesgo estructural documentado en (3.4). **Esto acota la precisión absoluta del pipeline de inversión a ~0.1 µm en TE y advierte contra la interpretación literal de ĥ_d pequeños.**
4. Ningún hallazgo de las fases 0–2 se contradice: la discrepancia con el benchmark externo (3.3) y la sensibilidad a la sujeción (3.4) señalan que el límite práctico del modelo no es la formulación del compliance sino la modelización del sistema completo (sujeción, llanta, acoplamiento 3D).

## Conclusiones de la fase

- El FEM propio es numéricamente correcto y convergente dentro de sus hipótesis declaradas; se conserva como generador exploratorio independiente.
- El benchmark externo **no se reproduce al 5 % con ninguna de las dos variantes** (9–38 % legacy, 18–54 % projected-energy). La conclusión honesta para el manuscrito: la validación cuantitativa frente a Korta–Mundo queda como discrepancia estructural documentada, con hipótesis de causa (sujeción/acoplamiento) pero sin cierre.
- La inversa cruzada **sí valida el mecanismo cualitativo central**: el relieve se recupera donde intersecta la carga y es invisible donde no intersecta, ahora con generador e inversor mecánicamente independientes.
- El límite práctico de precisión absoluta del pipeline es ~0.1 µm en TE (residual FE↔analítico), y el relieve dedendum pequeño estimado en ajustes reales puede ser absorbente de sesgo de modelo.

## Limitaciones declaradas

- Cubo de 25 mm asumido; raíz recortada 0.4 mm; plano deformación P1; sin fricción; sin 3D.
- 6/25 fases restringidas excluidas de la inversa.
- La referencia externa (Korta–Mundo) no se recalculó con FE propio en su geometría exacta (CAD y restricciones desconocidas).
