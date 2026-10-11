"""fix_template_encoding.py

- Remove UTF-8 BOM if present
- Convert CRLF -> LF
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TPL = ROOT / "eclipse_installer" / "templates"

for f in TPL.rglob("*"):
    if not f.is_file():
        continue
    data = f.read_bytes()
    orig_len = len(data)

    # 1. Remove BOM
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]

    # 2. CRLF -> LF
    data = data.replace(b"\r\n", b"\n")

    if len(data) != orig_len:
        f.write_bytes(data)
        print(f"[OK] {f.relative_to(TPL)}: {orig_len} -> {len(data)} bytes")
    else:
        print(f"[SKIP] {f.relative_to(TPL)}")
