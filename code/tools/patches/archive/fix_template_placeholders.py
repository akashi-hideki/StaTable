"""fix_template_placeholders.py

Unify placeholder format to @@KEY@@ (matches core._write_template).
"""
from __future__ import annotations
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
    # @KEY@ -> @@KEY@@ (but avoid @@KEY@@ -> @@@@KEY@@@@)
    for key in ("PROJECT_NAME", "VERSION"):
        # Only replace single @ form
        t = t.replace(f"@ {key} @".replace(" ", ""), f"@@{key}@@")
        # above is a no-op if not found; use direct
    # Simpler: replace '@PROJECT_NAME@' (single) with '@@PROJECT_NAME@@'
    t = t.replace("@PROJECT_NAME@", "@@PROJECT_NAME@@")
    t = t.replace("@VERSION@", "@@VERSION@@")
    if t != orig:
        f.write_text(t, encoding="utf-8")
        print(f"[OK] {f.name}")
        fixed += 1

print(f"[DONE] {fixed} file(s) updated")
