# code/tools/patches/patch_v3_2_3_register_signals.py
"""Patch for v3.2.3: register v3.2 signal test in CI and update README PASS count.

Changes:
  1. .github/workflows/check.yml: insert v3.2 test step before README consistency
  2. README.md: replace all "1537" with "1545" (5 occurrences)

Run from anywhere:
  python code/tools/patches/patch_v3_2_3_register_signals.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# code/tools/patches/ -> code/tools -> code -> StaTable
ROOT = Path(__file__).resolve().parent.parent.parent.parent
CHECK_YML = ROOT / ".github" / "workflows" / "check.yml"
README = ROOT / "README.md"

OLD_PASS = "1537"
NEW_PASS = "1545"

V32_BLOCK = """\
      - name: Run v3.2 test suites
        run: |
          python tests/test_v3_2_s2_signals.py

"""


def patch_check_yml() -> bool:
    text = CHECK_YML.read_text(encoding="utf-8")
    if "test_v3_2_s2_signals.py" in text:
        print("[SKIP] check.yml already contains v3.2 test step")
        return False
    anchor = "      - name: Run README consistency test"
    if anchor not in text:
        print(f"[FAIL] anchor not found in {CHECK_YML}")
        sys.exit(1)
    new_text = text.replace(anchor, V32_BLOCK + anchor, 1)
    CHECK_YML.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"[OK]   inserted v3.2 step in {CHECK_YML.relative_to(ROOT)}")
    return True


def patch_readme() -> int:
    text = README.read_text(encoding="utf-8")
    count = len(re.findall(rf"\b{OLD_PASS}\b", text))
    print(f"       README: {count} occurrence(s) of '{OLD_PASS}'")
    if count == 0:
        print("[SKIP] README already updated")
        return 0
    new_text = re.sub(rf"\b{OLD_PASS}\b", NEW_PASS, text)
    README.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"[OK]   replaced {OLD_PASS} -> {NEW_PASS} ({count} occurrence(s))")
    return count


def show_diff() -> None:
    print("\n" + "=" * 70)
    print("  git diff --stat")
    print("=" * 70)
    subprocess.run(["git", "diff", "--stat"], cwd=ROOT)
    print("\n" + "=" * 70)
    print("  git diff")
    print("=" * 70)
    subprocess.run(["git", "diff"], cwd=ROOT)


def main() -> None:
    print("=" * 70)
    print("  Patch v3.2.3: register signal test + update PASS count")
    print(f"  ROOT = {ROOT}")
    print("=" * 70)

    patch_check_yml()
    patch_readme()

    show_diff()

    print("\n" + "=" * 70)
    ans = input("  Apply commit? [y/N] ").strip().lower()
    if ans != "y":
        print("  Aborted. Files modified but not committed.")
        print("  Revert: git checkout -- README.md .github/workflows/check.yml")
        return

    subprocess.run(["git", "add", "README.md", ".github/workflows/check.yml"], cwd=ROOT)
    msg = (
        "ci(check): register v3.2 signal regression test suite\n\n"
        "- test_v3_2_s2_signals.py was added in v3.2.2 but not wired\n"
        "  into check.yml Job 3, so it never ran in CI\n"
        "- executed PASS 1537 -> 1545 (suite count stays 42)\n"
        "- README badge and body updated accordingly\n"
    )
    subprocess.run(["git", "commit", "-m", msg], cwd=ROOT)
    print("[OK]   committed")


if __name__ == "__main__":
    main()