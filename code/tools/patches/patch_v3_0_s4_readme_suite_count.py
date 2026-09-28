# code/tools/patches/patch_v3_0_s4_readme_suite_count.py
r"""
Phase S-4 (v3.0): update README suite count 38 -> 39.

Adds the S-4 docs test suite to the count claimed in README.md.

Usage:
    cd code
    python tools\patches\patch_v3_0_s4_readme_suite_count.py
    python tools\patches\patch_v3_0_s4_readme_suite_count.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent
README = REPO / "README.md"

REPLACEMENTS = [
    ("38 test suites, 1479 PASS", "39 test suites, 1479 PASS"),
    ("38 suites, 1168 tests", "39 suites, 1168 tests"),
    ("across 38 suites.", "across 39 suites."),
    ("All 38 suites should pass", "All 39 suites should pass"),
]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_0_s4_readme_suite_count  [{mode}]")
    print("=" * 70)

    if not README.exists():
        print(f"[FAIL] README not found: {README}")
        return 1

    text = README.read_text(encoding="utf-8")
    patched = text
    rc = 0

    for i, (old, new) in enumerate(REPLACEMENTS, start=1):
        n = patched.count(old)
        if n == 0:
            if new in patched:
                print(f"[SKIP] R{i}: already updated")
                continue
            print(f"[FAIL] R{i}: anchor not found: {old!r}")
            rc = 1
            continue
        if n > 1:
            print(f"[FAIL] R{i}: anchor found {n} times: {old!r}")
            rc = 1
            continue
        print(f"[APPLY] R{i}: {old!r} -> {new!r}")
        patched = patched.replace(old, new, 1)

    if rc != 0:
        print()
        print("[ABORT] one or more anchors failed; no file written.")
        return 1

    if patched == text:
        print()
        print("[SKIP] README.md already up to date")
        return 0

    if not args.apply:
        print()
        print("[DRY-RUN] no file written; pass --apply to execute.")
        return 0

    bak = README.with_suffix(README.suffix + ".bak_s4_suites")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
        print(f"  Backup: {bak.name}")

    README.write_text(patched, encoding="utf-8")
    print(f"[DONE] README.md updated ({len(text)} -> {len(patched)} chars)")
    print()
    print("Verify:")
    print("  python tests\\test_readme_consistency.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
