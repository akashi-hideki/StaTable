# code/tools/patches/patch_v3_0_g1d_gitignore_generated.py
r"""
v3.0 addendum: ignore Eclipse artifacts + External Tools output.

Ignores:
  - .project              (Eclipse project file)
  - .settings/            (Eclipse per-project settings)
  - generated/            (External Tools output at repo root)

Safety:
  - Idempotent (skips if marker present)
  - Appends only

Usage:
    cd code
    python tools\patches\patch_v3_0_g1d_gitignore_generated.py
    python tools\patches\patch_v3_0_g1d_gitignore_generated.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent
GITIGNORE = REPO / ".gitignore"

MARKER = "# v3.0: Eclipse artifacts + External Tools output"
APPEND = f"""

{MARKER}
.project
.settings/
generated/
"""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_0_g1d_gitignore_generated  [{mode}]")
    print("=" * 70)

    if not GITIGNORE.exists():
        print(f"[FAIL] not found: {GITIGNORE}")
        return 1

    text = GITIGNORE.read_text(encoding="utf-8")

    if MARKER in text:
        print("[SKIP] .gitignore already has Eclipse section")
        return 0

    new_text = text if text.endswith("\n") else text + "\n"
    new_text += APPEND

    print("[APPLY] append Eclipse artifacts + generated/ to .gitignore")
    if not args.apply:
        print()
        print("[DRY-RUN] no file written; pass --apply to execute.")
        return 0

    bak = GITIGNORE.with_suffix(GITIGNORE.suffix + ".bak_g1d")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
        print(f"  Backup: {bak.name}")

    GITIGNORE.write_text(new_text, encoding="utf-8")
    print(f"[DONE] .gitignore updated ({len(text)} -> {len(new_text)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())