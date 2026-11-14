"""patch_v3_5_version_codegen.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # code/
INIT = ROOT / "codegen" / "__init__.py"

t = INIT.read_text(encoding="utf-8")
if '__version__ = "3.4.3"' not in t:
    raise SystemExit("[FAIL] no 3.4.3 in codegen/__init__.py")
t = t.replace('__version__ = "3.4.3"', '__version__ = "3.5.0"', 1)
INIT.write_text(t, encoding="utf-8")
print(f"[OK] {INIT}")
