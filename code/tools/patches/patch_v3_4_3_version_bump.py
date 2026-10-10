"""v3.4.3 release: bump version 3.4.0 -> 3.4.3 in 3 files."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent

TARGETS = [
    (ROOT / "code" / "pyproject.toml",              'version = "3.4.0"', 'version = "3.4.3"'),
    (ROOT / "code" / "statable" / "__init__.py",    '__version__ = "3.4.0"', '__version__ = "3.4.3"'),
    (ROOT / "code" / "codegen" / "__init__.py",     '__version__ = "3.4.0"', '__version__ = "3.4.3"'),
]

def main() -> int:
    for path, old, new in TARGETS:
        if not path.exists():
            print(f"[MISS] {path.name}")
            continue
        text = path.read_text(encoding="utf-8")
        if new in text:
            print(f"[SKIP] {path.name}: already at 3.4.3")
            continue
        if old not in text:
            print(f"[ERR]  {path.name}: pattern '{old}' not found")
            continue
        text = text.replace(old, new, 1)
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"[OK]   {path.name}: 3.4.0 -> 3.4.3")
    return 0

if __name__ == "__main__":
    sys.exit(main())