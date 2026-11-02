# Version 18 evidence package

Current upload documents are in revision_18_2026-11-01. Historical documents and readmes are provenance. V18 preserves 15 equations, 45 references and all prior numerical table cells. S28–S32 add stress diagnostics, extended gain controls, bootstrap uncertainty and noise-free transfer. S24–S25 are the original 50-seed summaries; S28–S30 supersede their deeper IID/gain summaries with 200 paired seeds.

The combined stress evidence comprises 1100 selected cases: 500 retained v17 cases and 600 new cases. There are 3300 final fitting attempts, plus 300 covariance-pilot attempts for one-step feasible GLS. The deeper IID and 5% gain cells have 200 seeds each; other cells have 50. Additional rotation harmonics preserve 0.1 µm full-rotation amplitudes, so their centred single-tooth-pass RMS is generally much smaller. The tooth-pass harmonic has 0.1 µm RMS over the observation window. Both include independent noise of 0.1 µm standard deviation. These are controlled perturbations, not measured encoder or eccentricity calibration.

Known GLS and one-step FGLS use the same AR observations. FGLS estimates clipped lag-one correlation and marginal residual RMS from three IID pilot fits, then refits with the fixed plug-in covariance. Its score is descriptive, not a known-covariance chi-square statistic. No equal computational-budget efficiency claim is made. The fixed-covariance Q screen uses chi-square with 120 degrees of freedom at 95%, without subtracting a parameter count; its conservative interpretation requires the correct covariance and exact minimization. Operational flags also depend on the operator and optimizer. Passing the screen does not certify identifiability.

## Rebuild the article from saved evidence

From the extracted package root, Python 3.12 with python-docx and lxml:

```
python manuscript/build_v18.py
python manuscript/audit_v18.py
```

This does not refit data. It uses the preserved v17 documents, analysis_v18.json and stress_v18.png. Word parts should reproduce exactly; ZIP timestamps are not content changes. Native Microsoft Word and Poppler were used for visual QA because LibreOffice is absent on the authoring host. QA PDFs and page images are excluded.

## Recompute the extension and analysis

NumPy, SciPy and Matplotlib are additionally required. The v17 summary records the numerical environment; current analysis and source receipts provide file hashes. Do not modify scientific source files before resuming a partial run. The extension verifies its own hash and preserves incremental records. Existing records are reused; a scratch regeneration must preserve the original evidence and start without its extension records/source receipt.

```
python manuscript/stress_v18.py
python manuscript/analyze_v18.py
python manuscript/audit_numerical_v18.py
python manuscript/plot_v18.py
python -m pytest deposit_v6/gear_inverse_identifiability/tests -q
```

The analysis combines archived v17 and extension records without replacing old fits. It recomputes all 1100 weighted objectives and evaluates noise-free transfer at 200 Nm on 240 phases, against nominal and scenario-generating targets. This transfer shares reduced mechanics and is not external physical validation. Bootstrap uses 10000 jointly resampled seed-index sets, seed 20261118, and the statistic median(A)-median(B). It differs from the median of paired differences used in earlier tables. All 21 bootstrap distributions are archived. Their uncertainty is conditional on the synthetic experiment and algorithm; it is not physical parameter coverage or a tail certificate. Numerical audit checks new observations, covariance pilots, profiles, scores and source hashes, checks transfer samples and independently compares the paired percentile bootstrap with SciPy.

## Scope and submission

The five-file upload kit contains four clean editable documents and this evidence archive. The 18 omitted FE transition stations, corner/fillet contact and absence of certified measured waveform validation remain unresolved. A deterministic FE discrepancy curve alone does not identify a stochastic covariance. No physical inverse validation, TOST equivalence or globally optimal load design is claimed. The profile thresholds remain nominal, and the new bootstrap addresses Monte Carlo summaries rather than FE likelihood coverage.

Prepared files are not an editorial submission. No DOI or public v18 deposit is claimed. The public manuscript-v13 baseline is historical. No new licence grant is asserted. User-confirmed common CRediT roles are preserved. See RESPUESTA_REVISION_v17.md and CIERRE_VERIFICADO_v18.md for disposition and verification. SHA256SUMS.json covers all current distributed files except itself; older manifests describe historical releases.
