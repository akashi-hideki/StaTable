# code/tools/patch_v2_8_readme_numbers.py
"""
Update README numbers for v2.8.0:
  - Badge total:          1168 -> 1479
  - Body total:           1168 PASS -> 1479 PASS
  - Suite count:          31 -> 35
  - v2.8.0 table format:  remove standalone "NNN PASS" patterns

Idempotent: re-running after a successful apply does nothing.

Usage:
    cd code
    python tools\\patch_v2_8_readme_numbers.py             # dry-run
    python tools\\patch_v2_8_readme_numbers.py --apply     # apply
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
README = REPO / "README.md"

OLD_TOTAL = 1168
NEW_TOTAL = 1479   # 1168 + 123 + 106 + 56 + 26
OLD_SUITES = 31
NEW_SUITES = 35


def compute_fixes(text: str) -> list[tuple[str, str, int]]:
    """Return [(old, new, count), ...] for all applicable replacements."""
    fixes: list[tuple[str, str, int]] = []

    def add(old: str, new: str) -> None:
        c = text.count(old)
        if c > 0:
            fixes.append((old, new, c))

    # 1. Badge in the top shields.io URL
    add(f"Tests-{OLD_TOTAL}%20PASS", f"Tests-{NEW_TOTAL}%20PASS")

    # 2. Body: "1168 PASS" (any context)
    add(f"{OLD_TOTAL} PASS", f"{NEW_TOTAL} PASS")

    # 3. Suite count (multiple possible phrasings)
    add(f"{OLD_SUITES} test suites", f"{NEW_SUITES} test suites")
    add(f"{OLD_SUITES} suites", f"{NEW_SUITES} suites")
    add(f"{OLD_SUITES} test_", f"{NEW_SUITES} test_")

    # 4. v2.8.0 section test table: drop " PASS / 0 FAIL" tokens
    v28_rows = [
        ("| `test_v2_8_p1_ai_prompt.py` | 123 PASS / 0 FAIL |",
         "| `test_v2_8_p1_ai_prompt.py` | 123 assertions |"),
        ("| `test_v2_8_p2_response_parser.py` | 106 PASS / 0 FAIL |",
         "| `test_v2_8_p2_response_parser.py` | 106 assertions |"),
        ("| `test_v2_8_p3_response_validator.py` | 56 PASS / 0 FAIL |",
         "| `test_v2_8_p3_response_validator.py` | 56 assertions |"),
        ("| `test_v2_8_p4_gui_integration.py` | 26 PASS / 0 FAIL |",
         "| `test_v2_8_p4_gui_integration.py` | 26 assertions |"),
        ("| Regression `test_v2_2_p12_6.py` | 55 PASS / 0 FAIL |",
         "| Regression `test_v2_2_p12_6.py` | 55 assertions |"),
    ]
    for old, new in v28_rows:
        add(old, new)

    # 5. Fallback: any remaining "<digits> PASS / 0 FAIL" inside the
    #    v2.8.0 section only.
    #    (Not applied globally - too risky.)
    v28_start = text.find("## v2.8.0")
    if v28_start != -1:
        v28_end = text.find("\n## ", v28_start + 1)
        if v28_end == -1:
            v28_end = len(text)
        section = text[v28_start:v28_end]
        for m in re.finditer(r"(\d+) PASS / 0 FAIL", section):
            old = m.group(0)
            new = f"{m.group(1)} assertions"
            if not any(o == old for o, _, _ in fixes):
                add(old, new)

    return fixes


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v2_8_readme_numbers  [{mode}]")
    print("=" * 70)

    if not README.exists():
        print(f"[FAIL] README not found: {README}")
        return 1

    text = README.read_text(encoding="utf-8")
    fixes = compute_fixes(text)

    if not fixes:
        print("[SKIP] no applicable replacements found")
        return 0

    print(f"\nPlanned replacements ({len(fixes)} patterns):")
    for old, new, count in fixes:
        shown_old = old if len(old) < 70 else old[:67] + "..."
        shown_new = new if len(new) < 70 else new[:67] + "..."
        print(f"  [{count}x]")
        print(f"     - {shown_old}")
        print(f"     + {shown_new}")

    if not args.apply:
        print()
        print("[DRY-RUN] no file written; pass --apply to execute.")
        return 0

    patched = text
    for old, new, _ in fixes:
        patched = patched.replace(old, new)

    if patched == text:
        print("\n[INFO] no changes made")
        return 0

    bak = README.with_suffix(README.suffix + ".bak_v28nums")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
        print(f"\n  Backup: {bak}")

    README.write_text(patched, encoding="utf-8")
    print(f"\n[DONE] README.md updated ({len(patched)} chars)")
    print()
    print("Verify:")
    print("  python tests\\test_readme_consistency.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())