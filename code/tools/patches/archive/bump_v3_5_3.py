"""bump_v3_5_3.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
targets = [
    (ROOT / "pyproject.toml", 'version = "3.5.2"', 'version = "3.5.3"'),
    (ROOT / "statable" / "__init__.py",
     '__version__ = "3.5.2"', '__version__ = "3.5.3"'),
    (ROOT / "codegen" / "__init__.py",
     '__version__ = "3.5.2"', '__version__ = "3.5.3"'),
    (ROOT / "eclipse_installer" / "__init__.py",
     '__version__ = "0.1.0"', '__version__ = "0.1.1"'),
]
for p, old, new in targets:
    t = p.read_text(encoding="utf-8")
    if old not in t:
        raise SystemExit(f"[FAIL] {old} not in {p}")
    p.write_text(t.replace(old, new, 1), encoding="utf-8")
    print(f"[OK] {p}")
