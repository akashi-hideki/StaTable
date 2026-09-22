#!/usr/bin/env python3
# code/tools/patch_check_yml_v25.py
"""Add the verify-c-syntax job to .github/workflows/check.yml.

Usage:
    python tools/patch_check_yml_v25.py --dry-run   # preview only
    python tools/patch_check_yml_v25.py             # apply + backup

The script appends a new top-level job `verify-c-syntax` at the end of
the file. YAML does not care about key order, so appending is safe.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import shutil
import sys
from pathlib import Path


# ----------------------------------------------------------------------
# Target file
# ----------------------------------------------------------------------
CANDIDATE_PATHS = [
    Path("../.github/workflows/check.yml"),
    Path(".github/workflows/check.yml"),
    Path("../../.github/workflows/check.yml"),
]


def find_target() -> Path:
    for p in CANDIDATE_PATHS:
        if p.exists():
            return p
    sys.exit(
        "ERROR: .github/workflows/check.yml not found. Tried:\n  "
        + "\n  ".join(str(p) for p in CANDIDATE_PATHS)
    )


# ----------------------------------------------------------------------
# New job YAML (2-space indent for top-level jobs)
# ----------------------------------------------------------------------
NEW_JOB = """

  # ==============================================================
  # Job 5: C syntax verification (gcc + arm-none-eabi-gcc)
  #
  # Runs both the host gcc and the ARM GNU Toolchain against the
  # generated C code. Catches portability issues that only one
  # toolchain surfaces (e.g. NULL without <stddef.h>).
  #
  # Logs are uploaded as an artifact for post-run inspection.
  # ==============================================================
  verify-c-syntax:
    name: C syntax verification (gcc + ARM)
    runs-on: ubuntu-latest
    needs: [syntax]
    env:
      PYTHONIOENCODING: utf-8
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install Qt system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y libegl1 libgl1 libglib2.0-0 libdbus-1-3 libxkbcommon0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xfixes0 libxcb-cursor0 libfontconfig1 libfreetype6

      - name: Install ARM GNU Toolchain
        run: |
          sudo apt-get install -y gcc-arm-none-eabi

      - name: Install PySide6
        run: pip install PySide6

      - name: Show toolchain versions
        run: |
          gcc --version | head -1
          arm-none-eabi-gcc --version | head -1

      - name: Generate C code from test XML
        run: |
          python tools/gen_output_from_xml.py \\
            --xml tests/data/v22_features_test3.xml \\
            --out output

      - name: Verify C syntax (gcc + arm)
        run: |
          python tools/verify_c_syntax.py \\
            --root output --compiler both

      - name: Upload verification log
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: verify-c-syntax-logs
          path: code/verify_report/*.log
          if-no-files-found: warn
          retention-days: 30
"""


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-backup", action="store_true")
    args = parser.parse_args()

    target = find_target()
    print(f"Target: {target}")
    print(f"Mode:   {'DRY-RUN' if args.dry_run else 'APPLY'}")
    print()

    original = target.read_text(encoding="utf-8")

    if "verify-c-syntax:" in original:
        print("[SKIP] verify-c-syntax job already present.")
        return 0

    # Sanity: ensure the anchor exists
    if "verify_generated_code.py --root output" not in original:
        print("[WARN] anchor 'verify_generated_code.py --root output' "
              "not found. Appending anyway.")

    text = original.rstrip() + NEW_JOB

    print(f"Will append {len(NEW_JOB)} chars "
          f"(~{NEW_JOB.count(chr(10))} lines) as a new job.")
    print()

    if args.dry_run:
        print("--- Preview (first 30 lines of new job) ---")
        for line in NEW_JOB.splitlines()[:30]:
            print(line)
        print("--- ... ---")
        print("\nDry-run: no file written.")
        return 0

    # backup
    if not args.no_backup:
        ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = target.with_suffix(target.suffix + f".bak_{ts}")
        shutil.copy2(target, backup)
        print(f"Backup: {backup}")

    target.write_text(text, encoding="utf-8", newline="\n")
    print(f"Written: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())