# code/tools/patches/patch_v3_0_g1c_finalize.py
r"""
Phase G-1c: register G-1 test in CI + bump README suite count.

Edits:
  E1. .github/workflows/check.yml: add test_v3_0_g1_shared.py
  E2. README.md: 39 -> 40 suite count (4 occurrences)

Usage:
    cd code
    python tools\patches\patch_v3_0_g1c_finalize.py
    python tools\patches\patch_v3_0_g1c_finalize.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
REPO = CODE.parent
CHECK_YML = REPO / ".github" / "workflows" / "check.yml"
README = REPO / "README.md"

# --- E1 ---
CI_OLD = (
    "          python tests/test_v3_0_s4_docs.py\n"
)
CI_NEW = (
    "          python tests/test_v3_0_s4_docs.py\n"
    "          python tests/test_v3_0_g1_shared.py\n"
)

# --- E2 ---
README_REPLACEMENTS = [
    ("39 test suites, 1479 PASS", "40 test suites, 1479 PASS"),
    ("39 suites, 1168 tests", "40 suites, 1168 tests"),
    ("across 39 suites.", "across 40 suites."),
    ("All 39 suites should pass", "All 40 suites should pass"),
]


def _hdr(mode: str) -> None:
    print("=" * 70)
    print(f"  patch_v3_0_g1c_finalize  [{mode}]")
    print("=" * 70)


def _backup_once(path: Path, suffix: str) -> None:
    bak = path.with_suffix(path.suffix + suffix)
    if not bak.exists():
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"  Backup: {bak.name}")


def edit_check_yml(apply: bool) -> int:
    rel = CHECK_YML.relative_to(REPO)
    if not CHECK_YML.exists():
        print(f"[FAIL] E1: not found: {rel}")
        return 1
    text = CHECK_YML.read_text(encoding="utf-8")
    if "test_v3_0_g1_shared.py" in text:
        print("[SKIP] E1: already registered")
        return 0
    n = text.count(CI_OLD)
    if n != 1:
        print(f"[FAIL] E1: anchor found {n} times (expected 1)")
        return 1
    new_text = text.replace(CI_OLD, CI_NEW, 1)
    print("[APPLY] E1 check.yml: add test_v3_0_g1_shared.py")
    if not apply:
        return 0
    _backup_once(CHECK_YML, ".bak_g1c")
    CHECK_YML.write_text(new_text, encoding="utf-8")
    print(f"[DONE] {rel} updated")
    return 0


def edit_readme(apply: bool) -> int:
    rel = README.relative_to(REPO)
    if not README.exists():
        print(f"[FAIL] E2: not found: {rel}")
        return 1
    text = README.read_text(encoding="utf-8")
    patched = text
    rc = 0
    for i, (old, new) in enumerate(README_REPLACEMENTS, start=1):
        n = patched.count(old)
        if n == 0:
            if new in patched:
                print(f"[SKIP] E2 R{i}: already updated")
                continue
            print(f"[FAIL] E2 R{i}: anchor not found: {old!r}")
            rc = 1
            continue
        if n > 1:
            print(f"[FAIL] E2 R{i}: anchor found {n} times")
            rc = 1
            continue
        print(f"[APPLY] E2 R{i}: {old!r} -> {new!r}")
        patched = patched.replace(old, new, 1)
    if rc != 0:
        return 1
    if patched == text:
        print("[SKIP] E2: README already up to date")
        return 0
    if not apply:
        return 0
    _backup_once(README, ".bak_g1c")
    README.write_text(patched, encoding="utf-8")
    print(f"[DONE] {rel} updated ({len(text)} -> {len(patched)} chars)")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    _hdr(mode)

    rc = 0
    rc |= edit_check_yml(args.apply)
    print()
    rc |= edit_readme(args.apply)
    print()

    if not args.apply:
        print("[DRY-RUN] no file written; pass --apply to execute.")
        return rc

    print("Verify:")
    print("  python tests\\test_readme_consistency.py")
    return rc


if __name__ == "__main__":
    sys.exit(main())