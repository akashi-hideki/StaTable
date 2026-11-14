"""patch_v3_5_version.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # code/
PYPROJ = ROOT / "pyproject.toml"
INIT = ROOT / "statable" / "__init__.py"

for p in (PYPROJ, INIT):
    t = p.read_text(encoding="utf-8")
    old = t.replace('version = "3.4.3"', "").replace(
        '__version__ = "3.4.3"', "")
    if t == old:
        raise SystemExit(f"[FAIL] no 3.4.3 in {p}")
    t = t.replace('version = "3.4.3"', 'version = "3.5.0"', 1)
    t = t.replace('__version__ = "3.4.3"',
                  '__version__ = "3.5.0"', 1)
    p.write_text(t, encoding="utf-8")
    print(f"[OK] {p}")
