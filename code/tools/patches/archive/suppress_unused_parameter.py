"""suppress_unused_parameter.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MK = ROOT / "eclipse_installer" / "templates" / "Makefile.tmpl"
t = MK.read_text(encoding="utf-8")

old = "-std=c99 -Wall -Wextra -ffunction-sections"
new = "-std=c99 -Wall -Wextra -Wno-unused-parameter -ffunction-sections"
if old not in t:
    raise SystemExit("[FAIL] anchor not found")
t = t.replace(old, new, 1)
MK.write_text(t, encoding="utf-8")
print(f"[OK] {MK}")
