# code/tools/patches/patch_v3_0_s4_gitignore.py
r"""
Phase S-4 patch (D): add examples/_output/ to .gitignore.

Targets:
  - .gitignore (repo root)

Edits:
  E1. Append "code/examples/_output/" under Project-specific section.

Safety:
  - Idempotent (skips if already present)
  - Anchors on end-of-file; appends only

Usage:
    cd code
    python tools\patches\patch_v3_0_s4_gitignore.py
    python tools\patches\patch_v3_0_s4_gitignore.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# code/tools/patches/patch_...py -> repo root
REPO = Path(__file__).resolve().parent.parent.parent.parent
GITIGNORE = REPO / ".gitignore"

APPEND = """

# v3.0: examples/ runtime output
code/examples/_output/
"""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_0_s4_gitignore  [{mode}]")
    print("=" * 70)

    if not GITIGNORE.exists():
        print(f"[FAIL] not found: {GITIGNORE}")
        return 1

    text = GITIGNORE.read_text(encoding="utf-8")

    if "code/examples/_output/" in text:
        print("[SKIP] .gitignore already contains code/examples/_output/")
        return 0

    new_text = text
    if not new_text.endswith("\n"):
        new_text += "\n"
    new_text += APPEND

    print("[APPLY] append 'code/examples/_output/' to .gitignore")
    if not args.apply:
        print()
        print("[DRY-RUN] no file written; pass --apply to execute.")
        return 0

    bak = GITIGNORE.with_suffix(GITIGNORE.suffix + ".bak_s4")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
        print(f"  Backup: {bak.name}")

    GITIGNORE.write_text(new_text, encoding="utf-8")
    print(f"[DONE] .gitignore updated ({len(text)} -> {len(new_text)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
