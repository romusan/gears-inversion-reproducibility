# Fase 5 — Actualización controlada del manuscrito (v7)

Fecha: 2026-10-22 · Rama: `research/mmt-critical-validation`
Entregables (fuera de este repo, carpeta `gears_inversion/manuscript/`):
- `MMT_manuscript_Q1_revision_v7.docx` (nuevo; v6 intacto, sellado 12-oct)
- `MMT_supplementary_Q1_revision_v7.docx` (nuevo, tablas S1–S11)
- `q1_manuscript_v7.md`, `build_review7.py`, `review7_sections.py` (pipeline nuevo)
- `word_math.py` y `build_corrected_manuscript.py` (extensión retrocompatible: `revision=6` por defecto preserva v1–v6)

## Cambios aplicados (todos verificados en el docx generado)

1. **Ecuación (9) sin γ** (Fase 1): ahora `y_ℓi = F_ℓi(θ*) + ε_ℓi; ε ∼ N(0, σ_ℓ²)`. El término multiplicativo (1+γ) desaparece de la ecuación; el sesgo de ganancia se describe en §2.3 como molestia no modelada, con los datos archivados del experimento E04 (γ = 1, 3, 5 %: a γ=5 % el bloque dedendum absorbe el error —C_d se mueve hasta 0.045 mm y s_d hasta 0.14— mientras adendum se mueve como máximo 0.0024 mm y 0.012).
2. **Adopción de projected-energy** (Fase 2): §2.2 declara la variante de energía radial proyectada como formulación de referencia para los experimentos nuevos, con +14 % en TE pp, sin cambios en soporte de contacto, estructura singular ni recuperación sin ruido; legacy queda como línea base histórica.
3. **Nueva §4.5 "Cross-operator inversion and formulation robustness"** (Fases 3–4): ciclo FE de 25 fases, confirmación de invisibilidad dedendum, inversa cruzada (Tabla 9), discrepancia estructural del benchmark en ambas formulaciones, e invarianza de las conclusiones al compliance (Tabla S11).
4. **Discusión §5 y Conclusiones §6**: acotadas — el test cruzado llena parcialmente el hueco de evidencia, acota la precisión práctica a ~0.1 µm en TE, advierte que el dedendum pequeño estimado puede ser absorción de discrepancia, y declara la discrepancia del benchmark como estructural y no resuelta.
5. **Resumen e Highlights**: una frase de confirmación cruzada y un highlight nuevos.
6. **Disponibilidad de datos**: etiqueta manuscript-v7.
7. **Renumeración**: la Tabla nueva toma el número 9; las dos tablas del apéndice pasan de 9,10 a 10,11 (secuencia 1–11 sin duplicados, verificada).

## Reglas del protocolo cumplidas

- v6 no se sobrescribió (mtime 12-oct preservado; OMML de v6 intacto).
- Ningún resultado nuevo se calculó en esta fase: todos los números provienen de `results/independent_validation/03_*.json`, `04_*.json` y de los registros archivados E04.
- Sin reescritura general: ocho reemplazos de texto con aserción (fallan si v6 difiere), más sección nueva autocontenida.
- Sin coeficientes ajustados para forzar concordancia.

## Verificación

- 15 bloques OMML; ninguno contiene γ; eq (9) verificada token a token.
- 11 tablas numeradas 1–11 sin duplicados; S1–S11 presentes (S8 original preservada).
- 40 referencias [1]–[40] intactas (auditoría estructural del build).
