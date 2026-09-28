# code/tools/patches/patch_v3_0_s2_readme_suite_count.py
"""
Phase S-2 (v3.0): update README suite count 36 -> 37.

Adds the S-2 public-API test suite to the count claimed in README.md.

Safety:
  - Literal anchors; each must appear exactly once.
  - Idempotent: skips replacements already applied.

Usage:
    cd code
    python tools\\patches\\patch_v3_0_s2_readme_suite_count.py
    python tools\\patches\\patch_v3_0_s2_readme_suite_count.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent
README = REPO / "README.md"

REPLACEMENTS = [
    ("36 test suites, 1479 PASS", "37 test suites, 1479 PASS"),
    ("36 suites, 1168 tests", "37 suites, 1168 tests"),
    ("across 36 suites.", "across 37 suites."),
    ("All 36 suites should pass", "All 37 suites should pass"),
]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_0_s2_readme_suite_count  [{mode}]")
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

    bak = README.with_suffix(README.suffix + ".bak_s2_suites")
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
