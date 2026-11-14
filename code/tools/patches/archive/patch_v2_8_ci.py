# code/tools/patch_v2_8_ci.py
"""
Register the 4 new v2.8 test suites in .github/workflows/check.yml.

Inserts a new "Run v2.8 test suites" step immediately after the
existing "Run v2.7 test suites" step in the `tests` job.

Idempotent: skips if the v2.8 step is already present.

Usage:
    cd code
    python tools\\patch_v2_8_ci.py
    python tools\\patch_v2_8_ci.py --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
CI = REPO / ".github" / "workflows" / "check.yml"


ANCHOR = """      - name: Run v2.7 test suites
        run: |
          python tests/test_v2_7_p3.py
          python tests/test_v2_7_p4.py
          python tests/test_v2_7_p5_validation.py
"""

INSERT = """      - name: Run v2.7 test suites
        run: |
          python tests/test_v2_7_p3.py
          python tests/test_v2_7_p4.py
          python tests/test_v2_7_p5_validation.py

      - name: Run v2.8 test suites
        run: |
          python tests/test_v2_8_p1_ai_prompt.py
          python tests/test_v2_8_p2_response_parser.py
          python tests/test_v2_8_p3_response_validator.py
          python tests/test_v2_8_p4_gui_integration.py
"""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    print("=" * 70)
    print("  patch_v2_8_ci")
    print("=" * 70)

    if not CI.exists():
        print(f"[FAIL] check.yml not found: {CI}")
        return 1

    text = CI.read_text(encoding="utf-8")

    if "Run v2.8 test suites" in text:
        print("[SKIP] v2.8 step already present")
        return 0

    count = text.count(ANCHOR)
    if count == 0:
        print("[FAIL] anchor (v2.7 step) not found")
        return 1
    if count > 1:
        print(f"[FAIL] anchor found {count} times (expected 1)")
        return 1

    print(f"Target: {CI}")
    print("[APPLY] insert 'Run v2.8 test suites' after v2.7 step")

    if args.dry_run:
        print("[DRY-RUN] no file written")
        return 0

    bak = CI.with_suffix(CI.suffix + ".bak")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
        print(f"  Backup: {bak}")

    patched = text.replace(ANCHOR, INSERT, 1)
    CI.write_text(patched, encoding="utf-8")
    print("[DONE] check.yml updated")
    print()
    print("Next:")
    print("  git diff .github/workflows/check.yml")
    return 0


if __name__ == "__main__":
    sys.exit(main())