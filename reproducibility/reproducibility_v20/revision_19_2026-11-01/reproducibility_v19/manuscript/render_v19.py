"""Native Word export raster QA, adapted from the verified v18 workflow."""
import render_v18
from pathlib import Path
render_v18.OUT=Path(__file__).resolve().parents[1]/'revision_19_2026-11-01'
if __name__=='__main__':render_v18.main()
