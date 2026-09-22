#!/usr/bin/env python3
# code/tools/patch_c50_resolved.py
"""Mark C-50 as resolved by the v2.5.1 fix.

Updates SPEC_OVERVIEW_ja.md:
  - C-50 row: state "codegen の暗黙制約" -> "v2.5.1 で解消"

Updates ISSUES_v2_5.md:
  - candidate 6: status "発見" -> "v2.5.1 で解消済み"

Usage:
    python tools/patch_c50_resolved.py --dry-run
    python tools/patch_c50_resolved.py
"""

from __future__ import annotations
import argparse
import datetime as _dt
import shutil
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent.parent

SPEC_PATH = BASE / "docs" / "SPEC_OVERVIEW_ja.md"
ISSUES_PATH = BASE / "docs" / "ISSUES_v2_5.md"


SPEC_OLD = (
    "| C-50 | RoleFunction の namespace は layer_name と「完全一致 or 3文字以上の前方一致」が必要 "
    "| **codegen の暗黙制約** "
)
SPEC_NEW = (
    "| C-50 | RoleFunction の namespace は layer_name と「完全一致 or 3文字以上の前方一致」"
    "または呼び出し元層から呼ばれていること | **v2.5.1 で解消** "
)


ISSUES_OLD = "**Status**: v2.5 で発見（実装は v2.2.5 から）"
ISSUES_NEW = "**Status**: ✅ v2.5.1 で解消（`_should_declare_here` に call_map フォールバック追加）"


REPLACEMENTS = [
    ("SPEC C-50 state", SPEC_PATH, SPEC_OLD, SPEC_NEW),
    ("ISSUES candidate 6 status", ISSUES_PATH, ISSUES_OLD, ISSUES_NEW),
]


def patch(path: Path, old: str, new: str, desc: str,
          dry_run: bool, backup: bool) -> int:
    if not path.exists():
        print(f"[SKIP] {path.name} not found")
        return 0
    text = path.read_text(encoding="utf-8")
    n = text.count(old)
    print(f"[{desc}] {path.name}: {n} occurrence(s)")
    if n == 0:
        return 0
    if dry_run:
        return n
    if backup:
        ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = path.with_suffix(path.suffix + f".bak_c50r_{ts}")
        shutil.copy2(path, bak)
        print(f"  backup: {bak.name}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
    print(f"  written")
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    print(f"BASE: {BASE}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'APPLY'}")
    print()

    total = 0
    for desc, path, old, new in REPLACEMENTS:
        total += patch(path, old, new, desc, args.dry_run,
                       not args.no_backup)

    print()
    print(f"Total: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())