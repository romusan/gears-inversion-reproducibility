"""Content-addressed provenance for the correction campaign."""
import hashlib
import platform
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]

def provenance():
    files = sorted((ROOT/'src').rglob('*.py')) + sorted((ROOT/'experiments').glob('*.py'))
    digest=hashlib.sha256()
    hashes={}
    for path in files:
        rel=path.relative_to(ROOT).as_posix()
        data=path.read_bytes()
        hashes[rel]=hashlib.sha256(data).hexdigest()
        digest.update(rel.encode());digest.update(data)
    return {'campaign':'corrections-2026-10-12','created_utc':datetime.now(timezone.utc).isoformat(),
            'source_sha256':digest.hexdigest(),'files_sha256':hashes,
            'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__}
