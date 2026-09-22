#!/usr/bin/env python3
"""Revert the vending tutorial XML: App. -> Vending."""

from __future__ import annotations
import argparse
import shutil
import sys
from pathlib import Path

TARGET = (Path(__file__).resolve().parent.parent
          / "docs" / "tutorial" / "vending_machine.xml")

REPLACEMENTS = [
    ('RoleFunc_App_', 'RoleFunc_Vending_'),
    ('namespace="App"', 'namespace="Vending"'),
    ('App.', 'Vending.'),
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
        print(f"  {old!r:25s} -> {new!r:28s}  ({n})")
        new_text = new_text.replace(old, new)
        total += n

    print()
    print(f"Total replacements: {total}")

    if args.dry_run or total == 0:
        return 0

    if not args.no_backup:
        bak = TARGET.with_suffix(".xml.bak_revert")
        shutil.copy2(TARGET, bak)
        print(f"Backup: {bak.name}")

    TARGET.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"Written: {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
