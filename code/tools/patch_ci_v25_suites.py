#!/usr/bin/env python3
# code/tools/patch_ci_v25_suites.py
"""Add v2.4 and v2.5 test suites to .github/workflows/check.yml.

Currently only v2.2 and v2.3 suites are run in the 'tests:' job.
This patch appends two new steps:

  - name: Run v2.4 test suites
    run: |
      python tests/test_v2_4_p1_merge.py

  - name: Run v2.5 test suites
    run: |
      python tests/test_v2_5_p1.py
      python tests/test_v2_5_p2.py
      python tests/test_v2_5_p3.py

Usage:
    python tools/patch_ci_v25_suites.py --dry-run
    python tools/patch_ci_v25_suites.py
"""

from __future__ import annotations
import argparse
import datetime as _dt
import shutil
import sys
from pathlib import Path


CANDIDATE_PATHS = [
    Path("../.github/workflows/check.yml"),
    Path(".github/workflows/check.yml"),
    Path("../../.github/workflows/check.yml"),
]

ANCHOR = (
    "      - name: Run v2.3 test suites\n"
    "        run: |\n"
    "          python tests/test_v2_3_p1.py\n"
)

NEW_BLOCK = ANCHOR + (
    "\n"
    "      - name: Run v2.4 test suites\n"
    "        run: |\n"
    "          python tests/test_v2_4_p1_merge.py\n"
    "\n"
    "      - name: Run v2.5 test suites\n"
    "        run: |\n"
    "          python tests/test_v2_5_p1.py\n"
    "          python tests/test_v2_5_p2.py\n"
    "          python tests/test_v2_5_p3.py\n"
)


def find_target() -> Path:
    for p in CANDIDATE_PATHS:
        if p.exists():
            return p
    sys.exit(
        "ERROR: check.yml not found. Tried:\n  "
        + "\n  ".join(str(p) for p in CANDIDATE_PATHS)
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    target = find_target()
    print(f"Target: {target}")
    print(f"Mode:   {'DRY-RUN' if args.dry_run else 'APPLY'}")
    print()

    text = target.read_text(encoding="utf-8")

    if "Run v2.5 test suites" in text:
        print("[SKIP] v2.5 test suite step already present")
        return 0

    n = text.count(ANCHOR)
    if n == 0:
        print("[MISS] anchor not found:")
        print(ANCHOR)
        return 1
    print(f"[ OK ] anchor found ({n} occurrence)")

    if args.dry_run:
        print()
        print("--- block to be appended after anchor ---")
        print(NEW_BLOCK[len(ANCHOR):])
        return 0

    if not args.no_backup:
        ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = target.with_suffix(target.suffix + f".bak_ci_{ts}")
        shutil.copy2(target, bak)
        print(f"Backup: {bak.name}")

    new_text = text.replace(ANCHOR, NEW_BLOCK, 1)
    target.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"Written: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())