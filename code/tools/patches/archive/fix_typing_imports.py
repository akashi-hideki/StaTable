"""fix_typing_imports.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FILES = [
    "codegen/validate/data/action_definitions.py",
    "codegen/validate/data/keywords.py",
]

for rel in FILES:
    p = ROOT / rel
    lines = p.read_text(encoding="utf-8").split("\n")

    # Remove any existing typing import
    lines = [l for l in lines if not l.lstrip().startswith("from typing import")]

    # Find docstring end
    insert_at = 0
    in_doc = False
    for i, l in enumerate(lines):
        stripped = l.strip()
        if i == 0:
            continue  # skip shebang
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if in_doc:
                # closing
                insert_at = i + 1
                break
            else:
                in_doc = True
                # single-line docstring?
                if stripped.count('"""') >= 2:
                    insert_at = i + 1
                    break
                continue

    if insert_at == 0:
        raise SystemExit(f"[FAIL] {rel}: docstring end not found")

    lines.insert(insert_at, "")
    lines.insert(insert_at + 1, "from typing import Any, Dict")

    p.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] {rel}")
