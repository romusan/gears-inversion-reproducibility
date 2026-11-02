# Fase 0 — Auditoría y congelación de la línea base

**Fecha:** 2026-10-22 · **Rama:** `research/mmt-critical-validation` · **Base congelada:** tag `manuscript-v6` (commit `7e72ed9`)
**Entorno:** Python 3.12.15 · numpy 2.4.4 · scipy 1.18.1 · matplotlib 3.10.9 · pytest 9.1.1
**Script de auditoría:** `reports/baseline_audit.py` · **Salida JSON:** `reports/00_baseline_audit.json`

---

## 1. Inventario de código y dependencias

### 1.1 Módulo del operador directo/inverso (`gear_inverse_identifiability/`)

| Función requerida por el protocolo | Archivo | Clase/función |
|---|---|---|
| Geometría de evolvente | `src/geometry/involute.py` | `InvoluteGear`, `GearPair` |
| Correcciones de perfil addendum/dedendum | `src/geometry/microgeometry.py` | `TipRelief.evaluate/jacobian`, `map_roll_to_modification_domain` |
| Cumplimiento elástico de dientes | `src/mechanics/compliance.py` | `ToothCompliance` (variantes `legacy`, `shear-G`, `projected-energy`, `centerline-energy`) |
| Contacto Hertziano | `src/mechanics/compliance.py` | `HertzianContact` (no lineal; linealización opcional) |
| Complementariedad y reparto de carga | `src/mechanics/contact_solver.py` | `ContactSolver._forces_for_delta / solve_for_delta / solve_position` |
| Cálculo de error de transmisión | `src/mechanics/transmission_error.py` | `TransmissionError.compute_cycle` (centrado del ciclo) |
| Operador vectorizado y tangente implícita | `src/mechanics/batched_operator.py` | `BatchedGapOperator.evaluate(jacobian=True)` (motores `lambert`/`iterative`) |
| Modelos M3/M3b de discrepancia | `src/mechanics/alt_models.py` | `ConstantStiffnessContactModel`, `WaveScaledContactModel` |
| Optimización inversa | `src/inverse/reconstruction.py` | `InverseReconstructor.reconstruct` (TRF, esquemas `2-point`/`scaled-central`) |
| Fisher/SVD y diseño de cargas | `src/identifiability/fisher_optimal_loads.py` | `FisherLoadSelector` (sin piso de autovalores) |
| Campañas experimentales | `experiments/Q1_*.py`, `E0*.py`, `V06_korta_mundo_reproduction.py` | ver tabla en §3 |
| Pruebas | `tests/` (2 archivos, 27 pruebas) | `test_batched_operator.py`, `test_identifiability_corrections.py` |

**Dependencias declaradas** (`requirements.txt`): numpy≥1.24, scipy≥1.11, matplotlib≥3.7, pyyaml≥6.0, pytest≥7.4. Todas satisfechas en el entorno de ejecución.

**Verificación previa:** `python -m pytest tests/ -q` → **27 passed** (sin modificaciones de código).

### 1.2 Módulo de elementos finitos 2D (`fe2d/`)

Scripts: `run_fe2d.py` (continuo 2D + contacto nodal condensado, scikit-fem), `quadratic_eight_phases.py`, `convergence_separated.py`, `transition_checks.py`, `verify_coupled_invisibility.py`, `campaign.py`, `summarize_fe2d.py`, `extra_checks.py`.
Dependencias especiales (`.venv` local del directorio `fe2d/` de la copia de trabajo): scikit-fem 12.0.2, gmsh 4.15.2, meshio 5.3.5. La geometría es 57/57, módulo 2.6, distancia entre centros 150 mm — el benchmark de Korta & Mundo, **no** la geometría nominal G0 (24/48, módulo 3).

### 1.3 Estado del repositorio

- `deposit_v6` = referencia congelada `manuscript-v6`, árbol limpio, remoto `github.com/romusan/gears-inversion-reproducibility`.
- Rama de trabajo creada: `research/mmt-critical-validation`.
- La copia raíz `gears_inversion/gear_inverse_identifiability` difiere del depósito **solo en finales de línea** (CRLF/LF) y en artefactos no versionados (`__pycache__`, `.pytest_cache`, resultados históricos); `src/` es idéntico byte a byte en los archivos comparados (`compliance.py`, `batched_operator.py`).

## 2. Caso nominal conservado

- Piñón 24 dientes / rueda 48, módulo 3 mm, presión 20°, ancho 20 mm, E = 210 000 MPa, ν = 0.30 (`config/gear_parameters.yaml`; constructores por defecto de `InvoluteGear`).
- θ = (Cₐ, sₐ, C_d, s_d), límites (0,0.1) / (0.30,0.95) / (0,0.05) / (0.05,0.5), escalas (0.05, 1, 0.01, 1) — definidos en `Q1_identifiability_campaign.py` (SCALE, BOUNDS).
- Verdades nominales de la campaña: θ* = (0.020, 0.75, 0.005, s_d), s_d ∈ {0.25, 0.40}.

## 3. Resultados originales reproducidos

### A. Integridad de la campaña Monte Carlo (1200 registros, 12 celdas)

`monte_carlo_records.jsonl` → recomputación de medianas/p90/p95 de los cuatro errores por celda, y conteos de éxito, contra `monte_carlo_summary.json`. **12/12 celdas exactas** (tolerancia 1e-9 relativa). La cifra del abstract (error escalado mediano 0.394 en s_d=0.25, σ=0.1 µm, carga única 300 Nm) se verifica: 0.39389.

Comando: `python reports/baseline_audit.py` (sección A).

### B. Barrido de soporte — filas s_d = 0.25 y 0.40 (100 Nm, 240 posiciones)

Recomputadas con el código congelado y comparadas con `support_transition.json`:

| Magnitud | s_d=0.25 almacenado | s_d=0.25 nuevo | s_d=0.40 almacenado | s_d=0.40 nuevo |
|---|---|---|---|---|
| RMS señal dedendum (µm) | 5.7177e-04 | idéntico | (ver JSON) | idéntico |
| ξ_min cargado | 0.23538850 | idéntico | idéntico | idéntico |
| Puntos cargados con relieve | 8 | 8 | idéntico | idéntico |
| Rango numérico | 4 | 4 | 4 | 4 |
| Error dedendum escalado (sin ruido) | 5.45e-14 | idéntico | idéntico | idéntico |
| Valores singulares | — | dif. máx. rel. 1.9e-15 | — | 2.9e-16 |

Recuperación sin ruido reproducida con los dos inicios fijos (χ² ~ 1e-28, éxito en ambos). Los valores singulares escalados/blanqueados para s_d=0.25: (1270.6, 184.9, 14.12, 0.0470) — rango completo pero condicionamiento κ(J) ≈ 2.7e4.

### C. Chequeo forward nominal G0 a 300 Nm (120 posiciones)

| s_d | TE pico a pico (µm) | RMS (µm) | Residuo fuerza (N) | Complementariedad máx (mm) | Pares en contacto |
|---|---|---|---|---|---|
| 0.25 | 8.726 | 3.372 | 1.7e-08 | 1.9e-15 | 2 |
| 0.40 | 8.625 | 3.325 | 1.7e-08 | 2.0e-15 | 2 |

Margen de monotonicidad certificado por el operador: +7.19e-07 (condición c > 2K satisfecha). Jacobiano analítico implícito con forma (120, 4). Penetración numérica máxima ~2e-15 mm (nivel de tolerancia del solver, no física).

## 4. Resultados NO reproducidos en esta fase (y por qué)

| Resultado | Estado | Motivo / destino |
|---|---|---|
| Benchmark Korta & Mundo (12 comparaciones pico a pico, desviaciones 9.07–38.08 %, 0/12 < 5 %) | **Auditado, no recalculado** | Valores almacenados verificados en `V06_corrected.json` (procedencia registrada); reproducción completa con el script del depósito es parte de la **Fase 3** (§3.3 del protocolo). |
| Campaña Monte Carlo completa (600 reconstrucciones × 2 diseños) | No recorrida íntegramente | La integridad registro↔resumen se verificó exactamente (§3-A); repetir las 1200+600 inversión es costosa y no aporta trazabilidad adicional. Subconjuntos puntuales sí se recalcularon (§3-B). |
| Curva FEM de ciclo completo | **No existe** | El módulo `fe2d` dispone de 8 fases cuadráticas seleccionadas y controles de convergencia parcial; el propio protocolo (Fase 3.1–3.2) ordena verificar su alcance antes de cualquier uso. Ninguna curva continua FEM se presenta como validada. |

## 5. Diferencias numéricas

- Reproducción B: diferencias máximas relativas 1.9e-15 (s_d=0.25) y 2.9e-16 (s_d=0.40) en valores singulares — ruido de máquina entre ejecuciones; todo lo demás bit-a-bit o dentro de 1e-12.
- A: cero diferencias (estadísticas de orden sobre los mismos registros).
- C: primera medición forward directa en esta auditoría (no existía un valor almacenado del TE nominal a 300 Nm en el depósito); sirve de referencia para las Fases 2 y 4.

## 6. Comandos exactos utilizados

```bash
# desde deposit_v6/
git checkout -b research/mmt-critical-validation
python -m pytest tests/ -q                       # 27 passed
python reports/baseline_audit.py                 # genera 00_baseline_audit.json
```

## 7. Problemas detectados durante la auditoría (alimentan Fases 1–3)

1. **La ecuación (9) del Word** (`y_ℓi = (1+γ)F_ℓi(θ*) + ε_ℓi`) **contiene γ, pero ningún experimento de la campaña Q1 lo usa** (γ solo aparece en los casos de sesgo de E04, donde tampoco se estima). El texto Markdown fuente ya lo omite; la inconsistencia vive solo en la ecuación OMML del Word. → Fase 1.
2. **El modelo `legacy` usa E en el cortante** (`c_shear = 1.2 ∫ 1/(E·A)`), con G correcto solo en variantes de ablación; el baseline «histórico» es el que mejor coincide con el benchmark externo, señal de posible compensación de errores. → Fase 2.
3. **Las 48/12 comparaciones externas sobreestiman** el TE pico a pico en todos los casos; la validación FEM disponible es de 8 fases, no un ciclo. → Fase 3.

## 8. Condición de avance

✅ **Satisfecha.** Los resultados principales del manuscrito v6 (campaña Monte Carlo, barrido de soporte, recuperaciones sin ruido) se reproducen con precisión de máquina usando el código congelado; las pruebas existentes pasan; el benchmark externo queda auditado con procedencia y calendarizado para reproducción en la Fase 3. Se autoriza modificar el modelo en la rama de trabajo conservando `manuscript-v6` intacto.
