"""fix_placeholders_v2.py

Normalize any @+KEY@+ to @@KEY@@ via regex.
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TPL = ROOT / "eclipse_installer" / "templates"

fixed = 0
for f in TPL.iterdir():
    if not f.is_file():
        continue
    try:
        t = f.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    orig = t
    for key in ("PROJECT_NAME", "VERSION"):
        t = re.sub(r"@+" + key + r"@+", f"@@{key}@@", t)
    if t != orig:
        f.write_text(t, encoding="utf-8")
        print(f"[OK] {f.name}")
        fixed += 1

print(f"[DONE] {fixed} file(s) updated")
