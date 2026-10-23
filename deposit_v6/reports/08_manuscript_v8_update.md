# Fase 8 — Integración del análisis de resolución y pulido de tono (v8)

Fecha: 2026-10-23 · Rama: `research/mmt-critical-validation`
Entregables (`gears_inversion/manuscript/`): `MMT_manuscript_Q1_revision_v8.docx`, `MMT_supplementary_Q1_revision_v8.docx` (S1–S12), `q1_manuscript_v8.md`, `build_review8.py`, `review8_sections.py`, `assets/fig_resolution.png`. v7 intacto (22-oct).

## Cambios respecto a v7

1. **Nueva §4.6 «Resolution of the non-parametric relief»** (contribución de primer nivel, no apéndice):
   - método: 41 nodos con base de sombreros, J_h blanqueado, matriz de resolución con Tikhonov ε=10⁻⁶s₁;
   - resultado central: R_jj idénticamente cero para ξ≤0.20 y ≈0.97 para ξ≥0.225 con la frontera en ξ_min — la regla de soporte de §3.1 pasa de heurística a frontera exacta de resolución del operador discreto;
   - espacio nulo 10-d: 9 nodos por debajo de ξ_min + **1 dirección interna de reparto de carga entre pares coactivos** (persistente bajo refinamiento; la condición de soporte es suficiente pero no completa);
   - traza(R)=31.0 (estable en dos décadas de amortiguamiento; 62/81 nodos refinado);
   - null-space shuttle: 5 µm en dirección nula ⇒ 1e-15 µm en TE; en dirección de rango ⇒ 1.76 µm (17×σ);
   - **Figura 7** (incrustada, verificada) y **Tabla suplementaria S12** (estudio de refinamiento).
2. **Tono de publicación Q1** (el paper no es bitácora):
   - «For the robustness experiments of this revision … the reproducible historical baseline» → «The radial energy-projected variant … is adopted as the reference compliance law; the legacy law is retained as a baseline ablation»;
   - «The archived bias experiment E04» → «A dedicated gain-bias experiment»;
   - cláusula del resumen reescrita en afirmativo («under an energy-projected compliance formulation the median dedendum errors change by less than 6%») + párrafo de resolución no paramétrica;
   - highlight nuevo: «Non-parametric resolution maps observable and null flank coordinates…»;
   - discusión: la dirección nula interna como caveat estructural con vía de mitigación (deformación medida en raíz);
   - conclusiones: cierre sobre el criterio de soporte hecho exacto y la única limitación estructural;
   - disponibilidad de datos: etiqueta manuscript-v8.
3. Sin reenumeración de tablas principales (1–11 intactas, sin duplicados); suplementario crece a S12.

## Verificación

- §4.6, Figura 7 (media/image7 incrustada), S12 presentes.
- Lenguaje de bitácora eliminado (4 cadenas comprobadas ausentes).
- Eq (9) sin γ; ningún γ en las 15 ecuaciones OMML.
- Referencias [1]–[40] intactas; 12 tablas suplementarias.
- Números trazados a `results/independent_validation/07_resolution.json` (Fase 7); ningún cálculo nuevo en esta fase.
