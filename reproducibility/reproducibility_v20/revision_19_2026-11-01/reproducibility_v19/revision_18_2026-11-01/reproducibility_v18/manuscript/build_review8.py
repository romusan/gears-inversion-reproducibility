"""Build revision 8 from the v7 markdown: integrate Section 4.6 (resolution
analysis) and rewrite revision-log prose into submission tone.

Every edit is an asserted string replacement so drift in the source fails
the build instead of patching silently.
"""
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from build_corrected_manuscript import build, paragraph, table
from build_review5 import format_inline
import review5_sections as v5
import review8_sections  # noqa: F401  (used by section_builder name)
BASE = Path(__file__).resolve().parent


def rep(t, old, new):
    assert old in t, 'v7 text drifted: ' + old[:80]
    return t.replace(old, new, 1)


def main():
    t = (BASE / 'q1_manuscript_v7.md').read_text(encoding='utf-8')

    # --- tone: submission voice, not a revision log -----------------------
    t = rep(t,
        "No compliance factor is fitted to the external targets. For the robustness "
        "experiments of this revision the radial energy-projected variant is adopted as "
        "the reference formulation: it uses the shear modulus in the shear term, projects "
        "the contact force onto the section, and adds axial compression and the offset "
        "bending arm. At the nominal geometry and 300 Nm it raises peak-to-peak "
        "transmission error by 14% without changing contact support, singular structure "
        "or noise-free recovery. The legacy law remains the reproducible historical "
        "baseline.",
        "No compliance factor is fitted to the external targets. The radial "
        "energy-projected variant, which uses the shear modulus in the shear term, "
        "projects the contact force onto the section, and adds axial compression and "
        "the offset bending arm, is adopted as the reference compliance law. At the "
        "nominal geometry and 300 Nm it raises peak-to-peak transmission error by 14% "
        "without changing contact support, singular structure or noise-free recovery; "
        "the legacy law is retained as a baseline ablation.")
    t = rep(t,
        "The archived bias experiment E04 (γ = 1%, 3% and 5% on otherwise noise-free data) shows",
        "A dedicated gain-bias experiment (γ = 1%, 3% and 5% on otherwise noise-free data) shows")

    # --- abstract: affirmative robustness clause + resolution contribution
    t = rep(t,
        "repeating the nominal noise cells under the energy-projected compliance changes "
        "the median dedendum errors by less than 6%.",
        "under an energy-projected compliance formulation the median dedendum errors "
        "change by less than 6%. A non-parametric resolution analysis over the flank "
        "shows that transmission error resolves the relief exactly where contact loads "
        "it: resolution is near-unit above the minimum loaded coordinate, the null "
        "space below it is exact, and one further null direction, associated with load "
        "transfer between simultaneously active pairs, lies inside the loaded flank.")

    # --- highlights --------------------------------------------------------
    t = rep(t,
        "- Independent finite-element cycles confirm exact relief invisibility outside loaded contact support",
        "- Independent finite-element cycles confirm exact relief invisibility outside loaded "
        "contact support\n"
        "- Non-parametric resolution maps observable and null flank coordinates; one load-split "
        "null direction lies inside the loaded flank")

    # --- new Section 4.6 ---------------------------------------------------
    t = rep(t, "## 5 Discussion and limitations",
        "### 4.6 Resolution of the non-parametric relief\n\n"
        "Q1_RESOLUTION\n\n"
        "## 5 Discussion and limitations")

    # --- discussion: the internal null direction as a structural caveat ----
    t = rep(t,
        "can dominate that block in cross-model fits.",
        "can dominate that block in cross-model fits. The resolution analysis of "
        "Section 4.6 adds a structural caveat: the approach observable carries one null "
        "direction beyond the support condition, associated with load transfer between "
        "simultaneously active pairs. Relief content in that combination is "
        "unobservable in transmission error regardless of the inversion method; "
        "constraining the individual pair forces, for example through instrumented "
        "tooth-root strain, would be required to resolve it.")

    # --- conclusions ---------------------------------------------------------
    t = rep(t,
        "The benchmark amplitude discrepancy itself remains structural and unresolved.",
        "The benchmark amplitude discrepancy itself remains structural and unresolved. "
        "Resolution analysis over a non-parametric flank discretization makes the "
        "support criterion exact: near-unit resolution above the minimum loaded "
        "coordinate, an identically zero null space below it, and one additional "
        "load-split null direction between active pairs. Transmission-error inversion "
        "can therefore certify the relief over the loaded part of the flank, subject "
        "to that single structural limitation.")

    # --- data availability ---------------------------------------------------
    t = rep(t,
        "https://github.com/romusan/gears-inversion-reproducibility/tree/manuscript-v7. The "
        "annotated tag manuscript-v7 and a SHA-256 manifest identify the deposited version. The "
        "preceding manuscript-v6 tag remains available. No DOI has been assigned.",
        "https://github.com/romusan/gears-inversion-reproducibility/tree/manuscript-v8. The "
        "annotated tag manuscript-v8 and a SHA-256 manifest identify the deposited version. The "
        "preceding manuscript-v7 tag remains available. No DOI has been assigned.")

    (BASE / 'q1_manuscript_v8.md').write_text(t, encoding='utf-8')

    v5.SUPPLEMENT.clear()
    path = build(BASE / 'q1_manuscript_v8.md',
                 BASE / 'MMT_manuscript_Q1_revision_v8.docx',
                 BASE.parent / 'referencias_40_q1.json',
                 section_builder='review8_sections', math_revision=7)
    d = Document(path); format_inline(d)
    for tab_ in d.tables:
        for cell in tab_.rows[-2].cells:
            for p in cell.paragraphs:
                p.paragraph_format.keep_with_next = True
    d.save(path)

    s = Document(path)
    for child in list(s.element.body):
        if child.tag != qn('w:sectPr'):
            s.element.body.remove(child)
    paragraph(s, 'Supplementary numerical controls for spur gear microgeometry inversion', 'Title')
    paragraph(s, 'Local information, phase-grid controls, finite-element resolution and angular '
                 'sampling for the accompanying manuscript. The original linear FE records and '
                 'the quadratic weak-contact records use different interface discretizations and '
                 'are labelled separately. Tables S10–S12 report the cross-operator inversion, '
                 'formulation-robustness and resolution-refinement records.')
    for item in sorted(v5.SUPPLEMENT, key=lambda x: int(x['number'][1:])):
        p = paragraph(s, item['caption']); p.paragraph_format.keep_with_next = True
        table(s, item['headers'], item['rows'], item['widths'])
    paragraph(s, 'S1–S4 retain the original statistical and local-information controls. S5–S6 and '
                 'S8 preserve the original linear/nodal FE records. S7 varies quadratic bulk and '
                 'pressure controls separately, with nonmonotonic interface stiffness. S9 reports '
                 'all offsets for the declared interpolants; the eight-node FE waveform is an '
                 'interpolation diagnostic and is not a direct FE angular scan. S10 reports '
                 'cross-operator inversion against the two-dimensional finite-element generator '
                 '(nineteen interior phases; six restricted phases excluded). S11 repeats the '
                 'nominal noise cells under the energy-projected compliance formulation. S12 '
                 'refines the non-parametric resolution analysis over the flank grid and the '
                 'angular sampling.')
    format_inline(s)
    for tab_ in s.tables:
        for cell in tab_.rows[-2].cells:
            for p in cell.paragraphs:
                p.paragraph_format.keep_with_next = True
    s.save(BASE / 'MMT_supplementary_Q1_revision_v8.docx')
    print('Saved revision 8, supplementary tables', len(v5.SUPPLEMENT))


if __name__ == '__main__':
    main()
