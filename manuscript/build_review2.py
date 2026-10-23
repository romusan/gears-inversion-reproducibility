"""Regenerate the second-review DOCX without replacing the first revision."""
from pathlib import Path
from prepare_q1_manuscript import main as prepare
from build_corrected_manuscript import build
BASE=Path(__file__).resolve().parent
if __name__=='__main__':
    prepare()
    build(BASE/'q1_manuscript.md',BASE/'MMT_manuscript_Q1_revision_v2.docx',BASE.parent/'referencias_40_q1.json',section_builder='review2_sections')
