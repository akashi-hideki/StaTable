# tests/test_ci_registration.py
"""Meta test: ensure every test_*.py under tests/ is registered in check.yml.

Prevents the v3.2.2 oversight where test_v3_2_s2_signals.py was
added but never wired into CI Job 3.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TESTS_DIR = ROOT / "code" / "tests"
CHECK_YML = ROOT / ".github" / "workflows" / "check.yml"

# Files intentionally excluded from CI registration (add only with reason)
EXCLUDE: set[str] = set()


def find_test_files() -> set[str]:
    return {p.name for p in TESTS_DIR.glob("test_*.py")}


def find_registered() -> set[str]:
    text = CHECK_YML.read_text(encoding="utf-8")
    # Matches:   python tests/test_xxx.py
    #            python tests\test_xxx.py
    # Matches:  python tests/test_xxx.py
    #           python tests\\test_xxx.py
    #           coverage run --parallel-mode tests/test_xxx.py
    return set(re.findall(
        r"(?:python|coverage\s+run(?:\s+--parallel-mode)?)\s+tests[\\/](test_\w+\.py)",
        text,
    ))


def main() -> int:
    files = find_test_files()
    registered = find_registered()
    missing = files - registered - EXCLUDE
    stale = registered - files

    passed = failed = 0

    def check(name: str, cond: bool) -> None:
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"[PASS] {name}")
        else:
            failed += 1
            print(f"[FAIL] {name}")

    print("=" * 70)
    print("  CI registration consistency")
    print("=" * 70)
    print(f"  tests/*.py files:   {len(files)}")
    print(f"  registered in CI:   {len(registered)}")
    print()

    check(f"all {len(files)} test files registered in check.yml", not missing)
    for m in sorted(missing):
        print(f"    [MISSING] {m}  -> add 'python tests/{m}' to check.yml")

    check("no stale registrations (referenced file missing)", not stale)
    for s in sorted(stale):
        print(f"    [STALE]   {s}  -> file does not exist")

    print()
    print(f"  TOTAL: {passed + failed}   PASSED: {passed}   FAILED: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())