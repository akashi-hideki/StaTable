#!/usr/bin/env python3
"""
Fix absolute imports (from validate.xxx) to relative imports
in codegen/validate/*.py.

Rules:
  - Files at codegen/validate/*.py (depth 0):
      from validate.xxx        -> from .xxx
  - Files at codegen/validate/items/*.py (depth 1):
      from validate.items.xxx  -> from .xxx        (same package)
      from validate.xxx        -> from ..xxx       (parent)
  - Files at codegen/validate/data/*.py (depth 1):
      from validate.data.xxx   -> from .xxx        (same package)
      from validate.xxx        -> from ..xxx       (parent)

Backup is created before modification.

Usage:
    cd <project-root>
    python tools/fix_validate_imports.py
"""

import pathlib
import shutil
from datetime import datetime

ROOT = pathlib.Path("codegen/validate")


def make_backup() -> pathlib.Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = pathlib.Path(f"_backup_validate_{ts}")
    shutil.copytree(ROOT, backup / "validate")
    return backup


def fix_file(p: pathlib.Path) -> bool:
    """Fix one file. Returns True if modified."""
    rel = p.relative_to(ROOT)
    depth = len(rel.parts) - 1   # 0 for top-level, 1 for sub-package

    original = p.read_text(encoding="utf-8")
    text = original

    if depth == 0:
        # Top-level: from validate.xxx -> from .xxx
        text = text.replace("from validate.", "from .")
    else:
        # Sub-package: handle same-package imports first
        own_pkg = rel.parts[0]   # "items" or "data"
        text = text.replace(f"from validate.{own_pkg}.", "from .")
        # Remaining: from validate.xxx -> from ..xxx
        text = text.replace("from validate.", "from ..")

    if text != original:
        p.write_text(text, encoding="utf-8")
        return True
    return False


def main():
    if not ROOT.exists():
        print(f"ERROR: {ROOT} not found. Run from project root.")
        return

    backup = make_backup()
    print(f"Backup created: {backup}")

    fixed = []
    for p in sorted(ROOT.rglob("*.py")):
        try:
            if fix_file(p):
                fixed.append(str(p))
                print(f"  [FIXED] {p}")
        except Exception as e:
            print(f"  [ERROR] {p}: {e}")

    print()
    print("=" * 60)
    print(f"  Fixed {len(fixed)} file(s)")
    print("=" * 60)

    # Verification: search remaining "from validate." patterns
    remaining = []
    for p in sorted(ROOT.rglob("*.py")):
        text = p.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            if line.strip().startswith("from validate."):
                remaining.append(f"{p}:{i}: {line.strip()}")

    if remaining:
        print("\nWARNING: Remaining absolute imports:")
        for r in remaining:
            print(f"  {r}")
    else:
        print("\nNo remaining 'from validate.' imports.")


if __name__ == "__main__":
    main()