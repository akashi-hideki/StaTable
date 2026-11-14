# code/tools/patches/patch_v3_0_s5_readme.py
r"""
Phase S-5 (v3.0): update README with Eclipse guide.

Targets:
  - README.md (repo root)

Edits:
  E1. Add ECLIPSE_INTEGRATION_ja.md row to Documentation table
  E2. Add Eclipse guide link to Tool Vendors / OEM section

Safety:
  - Idempotent (skips if already applied)
  - Literal anchors; each must appear exactly once

Usage:
    cd code
    python tools\patches\patch_v3_0_s5_readme.py
    python tools\patches\patch_v3_0_s5_readme.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent
README = REPO / "README.md"

# --- E1: docs table ---
E1_OLD = (
    "| [IMPLEMENTATION_PLAN_v2_3.md](code/docs/IMPLEMENTATION_PLAN_v2_3.md) "
    "| English | v2.3 implementation plan |\n"
)
E1_NEW = (
    E1_OLD
    + "| [ECLIPSE_INTEGRATION_ja.md](code/docs/ECLIPSE_INTEGRATION_ja.md) "
    + "| \u65e5\u672c\u8a9e | Eclipse External Tools \u9023\u643a\u30ac\u30a4\u30c9 |\n"
)

# --- E2: Tool Vendors / OEM ---
E2_OLD = (
    "- Python API for code generation\n"
    "- Customizable templates\n"
    "- **Commercial / OEM licenses available** (see Contact)\n"
)
E2_NEW = (
    "- Python API for code generation\n"
    "- Customizable templates\n"
    "- **Eclipse External Tools integration** "
    "([guide](code/docs/ECLIPSE_INTEGRATION_ja.md))\n"
    "- **Commercial / OEM licenses available** (see Contact)\n"
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_0_s5_readme  [{mode}]")
    print("=" * 70)

    if not README.exists():
        print(f"[FAIL] not found: {README}")
        return 1

    text = README.read_text(encoding="utf-8")
    patched = text
    rc = 0

    for tag, old, new, skip in (
        ("E1 docs table", E1_OLD, E1_NEW,
         "ECLIPSE_INTEGRATION_ja.md"),
        ("E2 Tool Vendors", E2_OLD, E2_NEW,
         "**Eclipse External Tools integration**"),
    ):
        if skip in patched:
            print(f"[SKIP] {tag}: already applied")
            continue
        n = patched.count(old)
        if n == 0:
            print(f"[FAIL] {tag}: anchor not found")
            rc = 1
            continue
        if n > 1:
            print(f"[FAIL] {tag}: anchor found {n} times")
            rc = 1
            continue
        print(f"[APPLY] {tag}")
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

    bak = README.with_suffix(README.suffix + ".bak_s5")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
        print(f"  Backup: {bak.name}")

    README.write_text(patched, encoding="utf-8")
    print(f"[DONE] README.md updated ({len(text)} -> {len(patched)} chars)")
    print()
    print("Verify:")
    print("  Select-String -Path ..\\README.md -Pattern 'ECLIPSE'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
