# Contact support and practical identifiability of spur gear microgeometry

Version 13 accompanying the final article and supplementary controls finalized on 24 October 2026. The versioned repository is https://github.com/romusan/gears-inversion-reproducibility/tree/manuscript-v13. No DOI is assigned. Historical v10 results are preserved inside `deposit_v6/`; they contain the superseded mixed-relief signal comparison and are not the current conclusions.

## Scientific result

The fixed-geometry gap operator has exactly invisible relief sets determined by loaded support. Its coupled-compliance extension, weak transition and centred-response gauge are conditional observability results. The corrected 24/24 FE isolated dedendum signal is 0.178987 µm RMS, versus 0.196589 µm analytically. Nevertheless, restricted and unrestricted inversions have the same residual and dedendum profiles are flat. This does not demonstrate physical profile recovery.

Bulk P1 refinement stabilizes the isolated contrast while the combined waveform and inverse residual still move. Dedicated v12 controls compare complete retained waveforms, erode the angular mask, refine pressure hats on identical P2 body meshes, and physically remove material with reassembled elastic stiffness. The latter two controls use explicitly recorded eligible phase subsets, not a complete-cycle or inverse convergence certificate. Unresolved corner phases are not treated as validated FE observations. All four analytical formulations exceed the adopted 5% external amplitude target.

## Layout and execution

`manuscript/` contains final DOCX files, editable scientific Markdown, figure scripts and deterministic builders. `revision_12_2026-10-23/` contains new verified records, phase selection, summaries, 42-reference verification, source metadata and the Spanish independent audit. `revision_11_2026-10-23/` supplies broad-start and restricted inversions, profiles and bulk-mesh cycles. The unchanged historical baseline is commit 8a08285ea9b6e8026d147102278f67e4c403e6bf, preserved under `deposit_v6/`.

Use Python 3.12 with NumPy, SciPy, Matplotlib, python-docx and Pillow. FE generation additionally requires gmsh, scikit-fem and meshio; retained requirements and recorded versions are included. From this package root:

```text
python -m pytest deposit_v6/gear_inverse_identifiability/tests -q
python manuscript/audit_structure_v11.py
python manuscript/audit_statistics_v11.py
python manuscript/audit_v11.py
python manuscript/diagnose_invariance_v11.py
python manuscript/convergence_v11.py
python manuscript/waveform_mask_v12.py
python manuscript/interface_v12.py
python manuscript/physical_geometry_v12.py
python manuscript/audit_references_v12.py
python manuscript/prepare_bibliography_v12.py
python manuscript/prepare_source_v12.py
python manuscript/figures_v11.py
python manuscript/figures_controls_v12.py
python manuscript/build_review12.py
python manuscript/final_audit_v12.py
```

The FE scripts resume their verified JSONL outputs. Do not combine pilot files with verified runs. Failed exploratory trace/projection checks were corrected before the final verified runs; incomplete pilot records are excluded from this package. Reproduction from scratch requires moving the deliberately selected verified output files aside before rerunning. The bibliography fetcher uses cached publisher-deposited Crossref metadata and respects rate limits. Registry verification is distinguished from full-text reading; targeted editorial abstracts and ISO catalogue checks are documented. Distributed metadata caches omit complete abstracts; titles, authors, publication fields and identifiers are retained.

Forty unit tests pass. Metrics from all 1800 archived statistical fits were audited; those 1800 optimizations were not rerun. Statistical precision assumes the declared noise and mechanical operator. Deterministic cross-operator profile objectives are not calibrated confidence intervals. Complete external benchmark waveforms, CAD and solver settings are unavailable; this package does not claim to reproduce those external FE simulations.

`SHA256SUMS.json` covers every package file except itself. PDF page renders are local QA outputs, not required numerical inputs. The final article is written as a scientific argument; revision history belongs to the separate audit, not its narrative. No new licence grant is asserted.


## Focused version 13 numerical controls

The current submission files end in v13. The retained v12 files document the previous evidence. Version 13 adds only targeted numerical controls for the nanometre physical-removal contrast and clarifies the information excluded by the phase mask. S21 is not a rigorous continuum error bound or a certificate for the P1 full-cycle inverse.

Install mpmath 1.4.1 in addition to the recorded FE dependencies. The full elastic assembly remains float64. The enhanced control uses alternative sparse-LU ordering, four elastic residual corrections, and 80-digit polishing of the condensed active-contact equations. Weighted harmonic morphing holds the identical boundary polygon fixed; pressure refinement uses the same eight phases as S20.

```text
python manuscript/precision_v13.py
python manuscript/build_review13.py
python manuscript/audit_v13.py
```

The 1800 archived optimizations are not repeated in this focused revision. The main DOCX, supplementary DOCX, editable Highlights and reproducibility ZIP are explicitly listed in the separate journal upload kit. A prepared upload kit does not imply submission to a journal.
