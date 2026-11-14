"""fix_qemu_serial.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BR = ROOT / "tools" / "build_and_run.py"
t = BR.read_text(encoding="utf-8")

old = '        "-serial", "stdio",'
new = '        "-serial", "mon:stdio",'
if old not in t:
    raise SystemExit("[FAIL] anchor not found")
t = t.replace(old, new, 1)
BR.write_text(t, encoding="utf-8")
print(f"[OK] patched {BR}")
