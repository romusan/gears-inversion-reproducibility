"""Build revision 9 from the v8 markdown: correct the null-space
interpretation throughout (the tenth null direction is the additive constant
over the loaded nodes, not load transfer), add the precision analysis,
condense the highlights to five within Elsevier's 85-character limit, and
close the remaining minor review points.

Every edit is an asserted string replacement so drift in the source fails
the build instead of patching silently.
"""
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from build_corrected_manuscript import build, paragraph, table
from build_review5 import format_inline
import review5_sections as v5
import review9_sections  # noqa: F401  (used by section_builder name)
BASE = Path(__file__).resolve().parent


def rep(t, old, new, count=1):
    assert old in t, 'v8 text drifted: ' + old[:80]
    return t.replace(old, new, count)


def main():
    t = (BASE / 'q1_manuscript_v8.md').read_text(encoding='utf-8')

    # --- abstract: constant null direction + precision ---------------------
    t = rep(t,
        "A non-parametric resolution analysis over the flank shows that transmission error "
        "resolves the relief exactly where contact loads it: resolution is near-unit above "
        "the minimum loaded coordinate, the null space below it is exact, and one further "
        "null direction, associated with load transfer between simultaneously active pairs, "
        "lies inside the loaded flank.",
        "A non-parametric resolution analysis over the flank shows that transmission error "
        "resolves the relief exactly where contact loads it: resolution is near-unit above "
        "the minimum loaded coordinate, the null space below it is exact, and the "
        "mean-removed observable identifies the relief only up to an additive constant, with "
        "sub-micrometre precision in most resolved directions.")

    # --- highlights: 7 -> 5, all <= 85 characters ---------------------------
    t = rep(t,
        "- Relief visibility depends on penetration into the loaded part of the flank\n"
        "- Contact support supplies a sufficient condition for exact relief invisibility\n"
        "- Implicit contact sensitivities support nonlinear uncertainty diagnostics\n"
        "- Minimum loaded flank coordinate screens relief visibility before inversion\n"
        "- Mechanical ablations expose persistent external response discrepancies\n"
        "- Independent finite-element cycles confirm exact relief invisibility outside loaded contact support\n"
        "- Non-parametric resolution maps observable and null flank coordinates; one load-split "
        "null direction lies inside the loaded flank",
        "- Relief visibility depends on penetration into the loaded part of the flank\n"
        "- Minimum loaded flank coordinate screens relief visibility before inversion\n"
        "- Mean-removed contact observable leaves relief known up to a constant\n"
        "- Non-parametric resolution analysis maps observable and null flank coordinates\n"
        "- External benchmark comparisons remain systematically discrepant")

    # --- discussion: constant null direction, no root-strain recommendation --
    t = rep(t,
        "The resolution analysis of Section 4.6 adds a structural caveat: the approach "
        "observable carries one null direction beyond the support condition, associated with "
        "load transfer between simultaneously active pairs. Relief content in that "
        "combination is unobservable in transmission error regardless of the inversion "
        "method; constraining the individual pair forces, for example through instrumented "
        "tooth-root strain, would be required to resolve it.",
        "The resolution analysis of Section 4.6 adds a structural caveat: the mean-removed "
        "approach observable annihilates the constant over the loaded nodes, so the relief "
        "is identified only up to an additive constant, and the nine nodal values below the "
        "support boundary are exactly unobservable. No inversion method can recover these "
        "components from transmission error alone.")

    # --- abstract, discussion and conclusions: absolute addendum precision ---
    t = rep(t,
        "yields addendum-depth recovery within 5% of its scale when the analytical "
        "operator inverts the finite-element response",
        "yields addendum-depth recovery of the true 0.020 mm depth to 0.0025 mm (legacy) "
        "and 0.0006 mm (projected-energy) when the analytical operator inverts the "
        "finite-element response")
    t = rep(t,
        "recover the addendum depth within 5% of its scale",
        "recover the addendum depth to 0.0025 mm (legacy) and 0.0006 mm "
        "(projected-energy) of its true 0.020 mm value")
    t = rep(t,
        "the addendum depth is recovered within 5% of its scale",
        "the addendum depth is recovered to 0.0025 mm (legacy) and 0.0006 mm "
        "(projected-energy) of its true 0.020 mm value")

    # --- conclusions: constant null direction, measured tone ------------------
    t = rep(t,
        "Resolution analysis over a non-parametric flank discretization makes the support "
        "criterion exact: near-unit resolution above the minimum loaded coordinate, an "
        "identically zero null space below it, and one additional load-split null direction "
        "between active pairs. Transmission-error inversion can therefore certify the relief "
        "over the loaded part of the flank, subject to that single structural limitation.",
        "Resolution analysis over a non-parametric flank discretization makes the support "
        "criterion exact: near-unit resolution above the minimum loaded coordinate and an "
        "identically zero null space below it, while the mean-removed observable identifies "
        "the relief over the loaded part of the flank only up to an additive constant.")

    # --- data availability: v8 -> v9 ------------------------------------------
    t = rep(t,
        "https://github.com/romusan/gears-inversion-reproducibility/tree/manuscript-v8. The "
        "annotated tag manuscript-v8 and a SHA-256 manifest identify the deposited version. The "
        "preceding manuscript-v7 tag remains available. No DOI has been assigned.",
        "https://github.com/romusan/gears-inversion-reproducibility/tree/manuscript-v9. The "
        "annotated tag manuscript-v9 and a SHA-256 manifest identify the deposited version. The "
        "preceding manuscript-v8 tag remains available. No DOI has been assigned.")

    (BASE / 'q1_manuscript_v9.md').write_text(t, encoding='utf-8')

    v5.SUPPLEMENT.clear()
    path = build(BASE / 'q1_manuscript_v9.md',
                 BASE / 'MMT_manuscript_Q1_revision_v9.docx',
                 BASE.parent / 'referencias_40_q1.json',
                 section_builder='review9_sections', math_revision=7)
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
        if item['number'] == 'S7':
            item['caption'] = item['caption'].replace(
                'The interface stiffness sequence is nonmonotonic.',
                'The sampled interface stiffness sequence is nonmonotonic across refinement levels.')
        p = paragraph(s, item['caption']); p.paragraph_format.keep_with_next = True
        table(s, item['headers'], item['rows'], item['widths'])
    paragraph(s, 'S1–S4 retain the original statistical and local-information controls. S5–S6 and '
                 'S8 preserve the original linear/nodal FE records. S7 varies quadratic bulk and '
                 'pressure controls separately; the sampled interface stiffness sequence is '
                 'nonmonotonic across refinement levels. S9 reports '
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
    s.save(BASE / 'MMT_supplementary_Q1_revision_v9.docx')
    print('Saved revision 9, supplementary tables', len(v5.SUPPLEMENT))


if __name__ == '__main__':
    main()
