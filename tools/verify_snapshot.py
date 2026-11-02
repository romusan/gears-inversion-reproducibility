"""Verify archived bytes and parse Python files without running experiments."""
from pathlib import Path
import ast
import hashlib
import json
import os

root = Path(__file__).resolve().parents[1]
if os.name == "nt" and not str(root).startswith("\\\\?\\"):
    root = Path("\\\\?\\" + str(root))
manifest = json.loads((root / "provenance/SOURCE_FILES.json").read_text(encoding="utf-8"))
python_count = 0
for name, record in manifest.items():
    data = (root / name).read_bytes()
    if hashlib.sha256(data).hexdigest() != record["sha256"]:
        raise SystemExit(f"SHA-256 mismatch: {name}")
    if name.endswith(".py"):
        ast.parse(data, filename=name)
        python_count += 1
print(f"Verified {len(manifest)} archived files; parsed {python_count} Python files. No experiments executed.")
