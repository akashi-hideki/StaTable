"""v3.4.0 final: register new test in CI + bump README PASS count.

Changes:
  1. .github/workflows/check.yml:
     insert 'python tests/test_v3_4_0_state_actions.py' right after
     the existing 'python tests/test_v2_7_p5_validation.py' line.
  2. README.md: replace '1635' -> '1642' everywhere (PASS count).
     Correct count = 1605 (v3.3.0) + 30 (new test) + 7 (p4 additions).

Both edits are idempotent.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent

CHECK_YML = ROOT / ".github" / "workflows" / "check.yml"
README = ROOT / "README.md"

NEW_TEST_LINE = "          python tests/test_v3_4_0_state_actions.py\n"
ANCHOR_LINE = "          python tests/test_v2_7_p5_validation.py\n"


def patch_check_yml() -> bool:
    if not CHECK_YML.exists():
        print(f"[ERR]  {CHECK_YML} not found")
        return False
    text = CHECK_YML.read_text(encoding="utf-8")

    if "test_v3_4_0_state_actions.py" in text:
        print("[SKIP] check.yml already has test_v3_4_0_state_actions.py")
        return True

    if ANCHOR_LINE not in text:
        print("[ERR]  anchor line not found in check.yml:")
        print(f"       {ANCHOR_LINE.rstrip()}")
        return False

    text = text.replace(ANCHOR_LINE, ANCHOR_LINE + NEW_TEST_LINE, 1)
    CHECK_YML.write_text(text, encoding="utf-8", newline="\n")
    print("[OK]   check.yml: inserted test_v3_4_0_state_actions.py")
    return True


def patch_readme() -> bool:
    if not README.exists():
        print(f"[ERR]  {README} not found")
        return False
    text = README.read_text(encoding="utf-8")

    if "1642" in text and "1635" not in text:
        print("[SKIP] README.md already at 1642")
        return True

    before = text.count("1635")
    text = text.replace("1635%20PASS", "1642%20PASS")
    text = text.replace("1635 PASS", "1642 PASS")
    after = text.count("1635")

    if before == after:
        print("[WARN] README.md: no 1635 occurrences replaced")
        return False

    README.write_text(text, encoding="utf-8", newline="\n")
    print(f"[OK]   README.md: 1635 -> 1642 ({before - after} replaced)")
    return True


def main() -> int:
    print("=" * 74)
    print("  v3.4.0 final: CI registration + README PASS count")
    print("=" * 74)
    ok1 = patch_check_yml()
    ok2 = patch_readme()
    print()
    print(f"  check.yml : {'OK' if ok1 else 'FAIL'}")
    print(f"  README.md : {'OK' if ok2 else 'FAIL'}")
    print("=" * 74)
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    sys.exit(main())