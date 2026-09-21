#!/usr/bin/env python3
"""Bump SPEC_SDK_API_en.md version 1.1 -> 1.2 and append revision entry.

Uses str.replace / line-based insertion to avoid regex escape issues.

Usage:
    python tools/bump_sdk_version.py            # dry-run
    python tools/bump_sdk_version.py --apply
"""

import argparse
import shutil
import sys
from pathlib import Path


TARGET_FILE = "docs/SPEC_SDK_API_en.md"


# ----------------------------------------------------------------------
# Patch 1: version header
# ----------------------------------------------------------------------
VERSION_OLD = (
    "Version: 1.1 (English Master / Reviewed)\n"
    "Date: 2026-09-21"
)
VERSION_NEW = (
    "Version: 1.2 (English Master / Reviewed)\n"
    "Date: 2026-09-22"
)


# ----------------------------------------------------------------------
# Patch 2: revision entry (insert after v1.1 block)
# ----------------------------------------------------------------------
# New entry (v1.2) to insert at the END of the v1.1 block.
# We locate the v1.1 header, then walk forward while lines start with
# "| | |" (continuation rows), and insert after the last such line.
V12_ENTRY = (
    "| 1.2 | 2026-09-22 | Sync with v2.4.1 fixes: |\n"
    "| | | - C-28 now implemented (§5.7.3, §9 L-19) |\n"
    "| | | - L-30 / L-31 added (§5.3, §5.4, §9) |\n"
)


def _apply_version(text: str):
    """Return (new_text, message)."""
    if VERSION_OLD not in text:
        return text, "version anchor not found (already 1.2?)"
    return text.replace(VERSION_OLD, VERSION_NEW, 1), "version 1.1 -> 1.2"


def _apply_revision(text: str):
    """Insert v1.2 entry after the v1.1 block (continuation rows)."""
    lines = text.splitlines(keepends=True)
    anchor_re_marker = "| 1.1 | 2026-09-21 |"

    start = None
    for i, line in enumerate(lines):
        if line.startswith(anchor_re_marker):
            start = i
            break
    if start is None:
        return text, "v1.1 revision header not found"

    # Walk forward while lines start with "| | |" (continuation rows)
    end = start
    j = start + 1
    while j < len(lines) and lines[j].lstrip().startswith("| | |"):
        end = j
        j += 1

    insert_at = end + 1
    lines.insert(insert_at, V12_ENTRY)
    return "".join(lines), f"v1.2 entry inserted after v1.1 block (line {insert_at})"


def apply(root: Path, apply_flag: bool, backup: bool) -> bool:
    path = root / TARGET_FILE
    print("=" * 78)
    print(f"  {TARGET_FILE}")
    print("=" * 78)

    if not path.exists():
        print(f"  [SKIP] file not found: {path}")
        return True

    text = path.read_text(encoding="utf-8")
    original = text

    # Patch 1: version
    print()
    print("  [1] Version header: 1.1 -> 1.2")
    text, msg = _apply_version(text)
    print(f"      {msg}")

    # Patch 2: revision entry
    print()
    print("  [2] Revision entry: add v1.2 after v1.1 block")
    text, msg = _apply_revision(text)
    print(f"      {msg}")
    print("      Inserted:")
    for line in V12_ENTRY.splitlines():
        print(f"        + {line}")

    if text == original:
        print()
        print("  [INFO] no changes (already applied)")
        return True

    if not apply_flag:
        print()
        print("  [DRY-RUN] not written (use --apply)")
        return True

    if backup:
        bak = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, bak)
        print()
        print(f"  [BACKUP] {bak}")

    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"  [WRITTEN] {path}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    apply_flag = args.apply
    backup = not args.no_backup

    print("=" * 78)
    print("  SDK doc version bump (1.1 -> 1.2)")
    print("=" * 78)
    print(f"  Root: {root}")
    print(f"  Mode: {'APPLY' if apply_flag else 'DRY-RUN'}")

    ok = apply(root, apply_flag, backup)

    print()
    print("=" * 78)
    print(f"  Result: {'OK' if ok else 'FAILED'}")
    print("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())