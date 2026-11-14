"""v3.5.0 S-3 Step 1: pin all CI jobs to ubuntu-24.04.

Freezes the currently-known-good image before the automatic
ubuntu-latest -> ubuntu-26.04 migration (2026-10-19 .. 2026-11-19).

Run from repo root (StaTable/):
    python code/tools/patches/patch_v3_5_s3_pin_ubuntu.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
YML = REPO / ".github" / "workflows" / "check.yml"


def main() -> int:
    print("=" * 70)
    print("  patch_v3_5_s3_pin_ubuntu (Step 1: pin only)")
    print("=" * 70)

    txt = YML.read_text(encoding="utf-8")
    n = txt.count("runs-on: ubuntu-latest")
    if n == 0:
        print("[INFO] no 'runs-on: ubuntu-latest' found (already pinned?)")
    else:
        txt = txt.replace("runs-on: ubuntu-latest", "runs-on: ubuntu-24.04")
        YML.write_text(txt, encoding="utf-8")
        print(f"  pinned {n} occurrence(s) to ubuntu-24.04")
        print(f"  wrote: {YML.relative_to(REPO)}")

    print()
    print("[OK] Step 1 done. Next:")
    print("     1. cd code")
    print("     2. git diff ..\\.github\\workflows\\check.yml")
    print("     3. git add / commit / push")
    print("     4. Confirm all 8 jobs remain green on ubuntu-24.04")
    print()
    print("     Step 2 (ubuntu-26.04 preview job) will run after")
    print("     confirming the pinned image still passes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())