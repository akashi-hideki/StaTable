# code/tools/patches/patch_v3_0_s6_fix_pyproject_readme.py
r"""
v3.0 fix: remove readme field from pyproject.toml.

Reason:
  setuptools refuses to read files outside the package root:
    "Cannot access .../code/../README.md (or anything outside ...)"

Fix:
  Remove the 'readme = { file = "../README.md", ... }' line.
  The readme field is optional. A follow-up patch can add a local
  code/README.md if PyPI publishing requires it.

Usage:
    cd code
    python tools\patches\patch_v3_0_s6_fix_pyproject_readme.py
    python tools\patches\patch_v3_0_s6_fix_pyproject_readme.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
PYPROJECT = CODE / "pyproject.toml"

OLD_LINE = 'readme = { file = "../README.md", content-type = "text/markdown" }\n'


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_0_s6_fix_pyproject_readme  [{mode}]")
    print("=" * 70)

    if not PYPROJECT.exists():
        print(f"[FAIL] not found: {PYPROJECT}")
        return 1

    text = PYPROJECT.read_text(encoding="utf-8")

    if OLD_LINE not in text:
        print("[SKIP] readme line already removed")
        return 0

    n = text.count(OLD_LINE)
    if n > 1:
        print(f"[FAIL] readme line found {n} times")
        return 1

    new_text = text.replace(OLD_LINE, "", 1)

    print("[APPLY] remove readme = { file = '../README.md', ... } line")
    if not args.apply:
        print()
        print("[DRY-RUN] no file written; pass --apply to execute.")
        return 0

    bak = PYPROJECT.with_suffix(PYPROJECT.suffix + ".bak_s6")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
        print(f"  Backup: {bak.name}")

    PYPROJECT.write_text(new_text, encoding="utf-8")
    print(f"[DONE] pyproject.toml updated ({len(text)} -> {len(new_text)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
