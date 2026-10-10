"""test_v3_5_s1_smoke.py - unit tests for statable.smoke."""
from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("STATABLE_DISABLE_MERMAID", "1")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from statable.smoke import LEVEL_MAX, LEVEL_MIN, parse_level, run

TOTAL = 0
PASSED = 0
FAILED = 0


def check(name, cond, detail=""):
    global TOTAL, PASSED, FAILED
    TOTAL += 1
    if cond:
        PASSED += 1
        print(f"[PASS] {name}")
    else:
        FAILED += 1
        print(f"[FAIL] {name}" + (f" -- {detail}" if detail else ""))


def main() -> int:
    print("=" * 70)
    print("  test_v3_5_s1_smoke")
    print("=" * 70)

    check("LEVEL_MIN == 0", LEVEL_MIN == 0)
    check("LEVEL_MAX == 3", LEVEL_MAX == 3)

    check("parse_level empty -> 0", parse_level([]) == 0)
    check("parse_level =N form",
          parse_level(["--smoke-level=2"]) == 2)
    check("parse_level space form",
          parse_level(["--smoke-level", "3"]) == 3)
    check("parse_level invalid -> 0",
          parse_level(["--smoke-level=abc"]) == 0)
    check("parse_level ignores others",
          parse_level(["--smoke-test", "--smoke-level=1"]) == 1)

    rc = run(0)
    check("run(0) returns 0", rc == 0, f"rc={rc}")

    print("-" * 70)
    print(f"TOTAL: {TOTAL}  PASSED: {PASSED}  FAILED: {FAILED}")
    print("=" * 70)
    os._exit(0 if FAILED == 0 else 1)


if __name__ == "__main__":
    sys.exit(main())
