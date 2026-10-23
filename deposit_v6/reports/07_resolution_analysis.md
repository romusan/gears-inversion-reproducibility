# Fase 7 — Análisis de resolución sobre el relieve no paramétrico h(ξ)

Fecha: 2026-10-23 · Rama: `research/mmt-critical-validation`
Script: `reports/phase7_resolution_analysis.py`
Datos: `results/independent_validation/07_resolution.json`, `07_resolution.png`
Código: `src/geometry/microgeometry.py` (nueva clase `GridRelief`), `src/mechanics/batched_operator.py` (reshape generalizado, retrocompatible), `tests/test_grid_relief.py` (3 pruebas nuevas; **40/40 en verde**).

## Qué se hizo

Siguiendo la idea 2 de la revisión de literatura (matriz de resolución / null-space shuttle, de tomografía): el relieve se parametriza de forma **no paramétrica** en 41 nodos uniformes ξ∈[0,1] con base de sombreros lineales (`GridRelief`), y la tangente implícita de contacto (`BatchedGapOperator`, formulación projected-energy) da el Jacobiano dF/dh (120×41) blanqueado con σ=0.1 µm. La matriz de resolución de Backus–Gilbert con Tikhonov, R = (JᵀJ+ε²I)⁻¹JᵀJ = V·diag(s²/(s²+ε²))·Vᵀ, se calcula con ε_rel = 1e-6 (barrido 1e-8…1e-2).

Configuración: G0, 300 Nm, 120 posiciones, σ = 0.1 µm, verdad paramétrica de referencia [0.02, 0.75, 0.005, s_d] con s_d ∈ {0.25, 0.40}.

## Resultados

### 1. La regla de soporte es exacta: resolución nula por debajo de ξ_min

- **R_jj = 0.000 por completo para ξ ≤ 0.200** y **R_jj ≈ 0.969 para ξ ≥ 0.225**: frontera de resolución abrupta que coincide con ξ_min cargado = 0.2356. Las columnas del Jacobiano de los nodos no cargados son **idénticamente cero** (‖J_j‖ = 0.0): el espacio nulo contiene el subespacio {h con soporte por debajo del mínimo coordenado cargado} — el análogo discreto exacto del teorema de invisibilidad del manuscrito.
- La regla heurística «comparar ξ_min con el rango esperado de s_d» pasa a ser un **corolario** de la matriz de resolución, como anticipaba la revisión de literatura.

### 2. El espacio nulo tiene una segunda componente: el reparto de carga entre pares coactivos

- rango(J_h) = 31 con 41 nodos → 10 direcciones nulas: 9 corresponden a los nodos con ξ ≤ 0.200 (soporte no cargado) y **1 es interna**, con soporte en ξ ∈ [0.25, 0.375] ∪ [0.875, 0.9].
- El modo nulo interno **persiste bajo refinamiento** (posiciones 120→480, nodos 41→81: siempre exactamente 1 dirección interna): es estructural, no aliasing. Mecanismo: con dos pares coactivos, el acercamiento δ solo ve la combinación ponderada Σ w_k·dh(ξ_1k) con w_k = 1/(c_k + w′_H); la perturbación que anula esa suma en cada fase (reparto de fuerza entre pares a suma fija) es invisible en el observable. La condición de soporte del manuscrito es suficiente pero **no completa**: hay más nulidad de la que predice la heurística (1 dirección sobre 31 resueltas en esta configuración).

### 3. Número efectivo de parámetros resueltos

- **traza(R) = 31.0** (de 41 nodos), estable en el barrido de amortiguamiento (31.0 para ε_rel ∈ [1e-8, 1e-4]; 28.9 en 1e-2). A doble resolución (81 nodos, 240–480 posiciones): traza-equivalente 62/81 — la traza escala con el número de nodos cargados, no con los 4 parámetros del modelo paramétrico: el observable es mucho más informativo localmente de lo que sugiere la parametrización de 4 parámetros (cada fase con 1–2 contactos activos muestrea h directamente).

### 4. Demostración del null-space shuttle

Perturbación de h con amplitud máxima 5 µm (el orden del relieve dedendum verdadero):

| Dirección | Cambio RMS del TE |
|---|---|
| Nula (primera), s_d=0.25 | **1.3e-15 µm** (precisión de máquina) |
| Nula de mayor contenido dedendum, s_d=0.25 | 6.4e-12 µm |
| Nula (primera), s_d=0.40 | 9.9e-12 µm |
| De rango (principal), ambas | **1.76 µm** (≈17× el ruido σ=0.1) |

El contraste es de 12+ órdenes de magnitud: variar el relieve a lo largo del espacio nulo deja la TE invariante; la misma amplitud en dirección de rango es plenamente observable. Esto cierra el ciclo «explorar el espacio nulo» de la literatura de tomografía sobre este operador.

## Figura

`07_resolution.png`: (a) diagonal de resolución R_jj vs ξ con la línea de ξ_min; (b) espectro blanqueado de J_h con el bloque nulo (caída a ~1e-12 después del valor singular 31); (c) contraste null vs range a amplitud 5 µm con la línea de ruido.

## Consecuencia para el manuscrito

- **Convertir el resultado negativo en constructivo** (objetivo de la revisión de literatura): en vez de «el dedendum no se recupera en s_d=0.25», el paper puede reportar el **mapa de resolución del flanco**: ξ resueltos (≥0.225, R_jj≈0.97), ξ en el espacio nulo (≤0.20, R_jj=0) y la dirección nula interna de reparto de carga. La condición suficiente de invisibilidad se mantiene y se precisa.
- **Advertencia honesta**: la nulidad interna no la predice la condición de soporte; si el relieve real tuviera contenido en esa combinación, tampoco sería observable en TE de acercamiento — un límite del observable, no del optimizador.
- Integración en v7 pendiente: este análisis es posterior a v7; se propone como §4.6 o como ampliación de §3.1, con la figura (a)–(c) y una tabla de traza(R) vs (s_d, torque).

## Reproductibilidad

- Semillas: no aplica (análisis determinista, sin ruido).
- Verificación: Jacobiano de malla por diferencias finitas (test), interpolación y base de sombreros (test), forward malla-vs-paramétrico <0.05 µm (test).
