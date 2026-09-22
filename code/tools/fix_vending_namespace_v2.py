#!/usr/bin/env python3
# code/tools/fix_vending_namespace_v2.py
"""Fix the vending tutorial XML: replace ALL Vending references with App.

The v1 script only replaced `namespace="Vending"`, but the XML also
references Vending in:
  - <PreAction action="Vending.XXX" />
  - <Action name="Vending.XXX" />
  - <Action role_function="Vending.XXX" />
  - <Condition condition="RoleFunc_Vending_XXX(...)" />
  - Transition condition="RoleFunc_Vending_XXX(...)"
  - Cell source="..." event="..." (unaffected)

This script replaces the token `Vending.` -> `App.` and the C-name
prefix `RoleFunc_Vending_` -> `RoleFunc_App_` globally.

Usage:
    python tools/fix_vending_namespace_v2.py --dry-run
    python tools/fix_vending_namespace_v2.py
"""

from __future__ import annotations
import argparse
import shutil
import sys
from pathlib import Path


TARGET = (Path(__file__).resolve().parent.parent
          / "docs" / "tutorial" / "vending_machine.xml")

REPLACEMENTS = [
    ('Vending.', 'App.'),
    ('RoleFunc_Vending_', 'RoleFunc_App_'),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    if not TARGET.exists():
        print(f"ERROR: {TARGET} not found", file=sys.stderr)
        return 1

    text = TARGET.read_text(encoding="utf-8")
    print(f"Target: {TARGET}")
    print(f"Mode:   {'DRY-RUN' if args.dry_run else 'APPLY'}")
    print()

    total = 0
    new_text = text
    for old, new in REPLACEMENTS:
        n = new_text.count(old)
        print(f"  {old!r:30s} -> {new!r:20s}  ({n} occurrences)")
        new_text = new_text.replace(old, new)
        total += n

    print()
    print(f"Total replacements: {total}")

    if args.dry_run or total == 0:
        return 0

    if not args.no_backup:
        backup = TARGET.with_suffix(".xml.bak2")
        shutil.copy2(TARGET, backup)
        print(f"Backup:  {backup}")

    TARGET.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"Written: {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())