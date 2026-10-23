# Fase 9 — Corrección de la interpretación del espacio nulo y mapa de precisión

**Fecha:** 2026-10-23 · **Rama:** `research/mmt-critical-validation` · **Datos:** `results/independent_validation/09_resolution_corrections.json` (script: `reports/phase9_resolution_corrections.py`)

Verificaciones solicitadas por el revisor para corregir la §4.6 de v8. Resultado global: **el revisor tiene razón en el punto 1** (la décima dirección nula es la constante sobre los nodos cargados); los números corregidos para la reescritura de §4.6 / resumen / highlight / §5 / §6 están en las secciones 1, 2 y 4.

---

## 1. La dirección nula es la constante (media removida), no una transferencia de carga

Operador: `J_h` blanqueado (120×41, σ = 1e-4 mm), pareja 24/48, 300 Nm, GridRelief de 41 nodos. SVD numérico:

| Verificación | Resultado | Lectura |
|---|---|---|
| Nodos cargados | 32 (columna no nula) | ξ > 0.20 |
| Rango | 31 | **rank = cargados − 1** ✔ (no cargados − 2) |
| ‖J_h·1‖/s₁ | 5.49e-16 | **la constante está en el núcleo exacto** ✔ |
| Parte cargada de los 10 vectores nulos, desviación máxima respecto a uniforme/√32 | 1.90e-12 | los 10 son (i) 9 vectores con soporte en nodos ξ≤0.20 y (ii) el vector uniforme sobre los 32 cargados ✔ |
| R_jj sobre cargados, desviación máxima de (1 − 1/32) | 1.37e-08 | **R_jj = 1 − 1/n_cargados**, como predijo el revisor ✔ |

Los nodos con columna cero son exactamente ξ ∈ {0.00, …, 0.20} (9 nodos); ξ mínimo muestreado: 0.2356. Las tres cuentas del revisor (diagonal 0.97 = 1−1/32; traza 31 = 32−1; 62 = 63−1) quedan confirmadas — una dirección real de reparto de carga daría "cargados − 2" y no aparece.

**El "vector interno concentrado en ξ ≈ 0.25–0.375 y 0.875–0.90" citado en v8 §4.6 fue una mala lectura:** era el top-8 arbitrario de una base degenerada rotada del subespacio nulo; la norma 0.177 de su parte cargada era 1/√32, visible en el propio texto. No tiene interpretación física.

**Enunciado correcto (para §4.6, resumen, highlight, §5, §6):** "el relieve se identifica salvo una constante aditiva, consecuencia directa del observable con media removida (§2.3); los nueve nodos ξ ≤ 0.20 fuera de la zona de contacto quedan además totalmente no observables". Quitar la recomendación de medir deformación en la raíz del diente (queda sin sustento).

## 2. Precisión por dirección y por nodo (resolución ≠ precisión)

σ = 0.1 µm. std de amplitud por dirección singular = 1/s_k (µm), sin cotas; std por nodo condicionado al subespacio resuelto (las direcciones nulas quedan excluidas y reportan std infinita — mensaje honesto: la constante y los nodos fuera de soporte no son recuperables).

**Por dirección (31 direcciones de rango, ordenadas):** mín 0.041 µm · mediana 0.081 µm · máx 14.69 µm.

| Umbral de std | Direcciones |
|---|---|
| ≤ 0.5 µm | 24 / 31 |
| ≤ 1.0 µm | 26 / 31 |
| ≤ 5.0 µm | 29 / 31 |

Dos direcciones superan 5 µm (5.26 y 14.69 µm): combinaciones de relieve mal condicionadas, aun no nulas.

**Por nodo (std condicionada, µm):** los 9 nodos ξ ≤ 0.20 → ∞ (fuera de soporte). Sobre la parte cargada:

- 11 nodos con std ≤ 1 µm: ξ ∈ [0.225, 0.25], [0.55, 0.725] y el nodo de punta ξ = 1.0;
- mejor precisión ~0.10 µm en la zona media (ξ ≈ 0.55–0.70);
- peor precisión ~4.8 µm en el centro del flanco (ξ ≈ 0.375–0.475);
- los 32 nodos cargados quedan ≤ 5 µm.

**Frontera de precisión vs. frontera de resolución binaria:** ambas coinciden en el salto de ξ = 0.20 (último nodo no resuelto) a ξ = 0.225 (primero resuelto) — **consistente con el inicio de contacto 0.2346 a 300 Nm de la Tabla 11** (la malla de 0.025 no distingue 0.2346 del mínimo muestreado 0.2356).

**Tono recomendado para reemplazar las frases de v8:** en vez de "resolving power well beyond the four parameters" / "certify the relief over the loaded part", algo como: *"over the supported region the relief is recovered with sub-micrometre standard deviation in 24 of 31 singular directions; the observable leaves a 10-dimensional null space (nine unsupported nodes plus the additive constant) in which no relief information exists."*

## 3. Menores

**(a) Frontera 0.2356 vs 0.2346.** Corregido arriba: la frontera efectiva reportable es "entre ξ = 0.20 y ξ = 0.225", y es consistente con 0.2346; no afirmar que está *en* 0.2356.

**(b) Highlights.** v8 lleva 7; Elsevier pide 3–5 de ≤ 85 caracteres. Candidatos (todos ≤ 77):

1. `Relief visibility depends on penetration into the loaded part of the flank` (74)
2. `Minimum loaded flank coordinate screens relief visibility before inversion` (74)
3. `Mean-removed contact observable leaves relief known up to a constant` (68)
4. `Non-parametric resolution analysis maps observable and null flank coordinates` (77)
5. `External benchmark comparisons remain systematically discrepant` (63)

**(c) 0.394 (abstract) vs 0.369 (§Fase 4).** Bootstrap de la mediana (10 000 remuestreos, n = 100 cada uno):

| Campaña | n | Mediana | IC95 |
|---|---|---|---|
| Original (q1_revision, single300, σ=0.1, s_d=0.25) | 100 | 0.394 | [0.310, 0.433] |
| Fase 4 (mismas condiciones, semillas base 20261022) | 100 | 0.369 | [0.291, 0.435] |

Semillas disjuntas (0–99 vs 20261022+k). **Los IC95 se solapan ampliamente: las dos cifras son estadísticamente indistinguibles.** Añadir una nota de semillas donde aparezcan ambas.

**(d) 9.1–38.1 % (recálculo) vs 8.9–37.2 % (Tablas 1–2).** Mismos 12 pares (caso × torque), misma definición (100·(pp−ref)/ref), mismas referencias FE. La diferencia (≤ 0.9 pp) viene de `model_pp_um`: el modelo del recálculo independiente difiere ≤ 0.6 % del de la campaña original por configuración del resolvedor. Rangos consistentes dentro de tolerancia de reproducción; no es un error de definición.

**(e) Dedendum de la Tabla 9 = puntos de partida exactos.**

| Variante | Dedendum estimado | Punto de partida | Igual |
|---|---|---|---|
| legacy | [0.02, 0.45] | [0.02, 0.45] | ✔ exacto |
| projected-energy | [0.01, 0.35] | [0.01, 0.35] | ✔ exacto |

El bloque dedendum **no se movió de la inicialización**: no se identifica a partir del observable y el valor reportado no contiene relieve físico. El adendum sí se movió: error absoluto |est−true| = 0.0025 mm (legacy) y 0.0006 mm (projected), frente a errores de partida de 0.0087 y 0.0222 mm — mejoras de ~3.4× y ~35×. Reemplazar "absorbe la discrepancia" por: *"the dedendum block is not identifiable from this observable; the reported dedendum values equal the initialization and should be read as non-informative, while the addendum block is recovered to 0.0025 mm (legacy) and 0.0006 mm (projected-energy)."*

**(f) "Within 5 % of its scale" = 12.5 % del valor verdadero.** Sustituir por cifras absolutas del punto (e).

**(g) ξ_min del par 57/57.** En las 19 fases interiores del ciclo (650 Nm): ξ_min = 0.6953. Ambos s_d (0.30 y 0.45) quedan **por debajo** del soporte: la invisibilidad del relieve dedendum en el FE es la predicción de la condición de soporte — el FE confirma la teoría, no descubre nada nuevo. Cerrado con (a) de la Fase 3.

**(h) "Nonmonotonic" en S7.** Mantener la observación como dato experimental del FE; no atribuirla a identificabilidad (queda fuera del observable analítico).

---

## 4. Frases de reemplazo propuestas (para la reescritura del revisor)

- **§4.6 párrafo 2:** reemplazar el párrafo del "load-split null direction" por: *"The tenth null direction is the constant over the loaded nodes: the hat functions sum to one, so a constant relief shift moves every gap and approach reading by the same amount and is erased by the cycle mean (§2.3). Accordingly rank(J_h) = n_loaded − 1 (31 = 32 − 1) and R_jj = 1 − 1/n_loaded on the loaded part. The relief is therefore identified up to an additive constant — a property of the mean-removed observable, not of load transfer."* Y eliminar la recomendación de medir deformación en la raíz.
- **Resumen / §5 / §6:** mismo enunciado ("identified up to an additive constant"); ajustar highlight 7 por el candidato 3 del punto (b).
- **Tono de §4.6 sobre precisión:** usar el párrafo sugerido al final de la sección 2.

## 5. Estado de pruebas

`python -m pytest tests/ -q` en `gear_inverse_identifiability`: 40/40 en verde (sin cambios de código en la Fase 9; el único cambio es este script de reporte).
