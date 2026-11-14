# code/tools/cleanup_before_v2_8_commit.py
"""
Pre-commit cleanup for v2.8.0.

Removes diagnostic scripts, backup files, and consolidates patch
scripts. Dry-run by default; pass --apply to actually delete.

Usage:
    cd code
    python tools\\cleanup_before_v2_8_commit.py            # dry-run
    python tools\\cleanup_before_v2_8_commit.py --apply    # apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent

# Files to remove outright
TO_DELETE = [
    # Diagnostics
    CODE / "tools" / "diag_qt_flags.py",
    CODE / "tools" / "diag_gd_empty.py",
    CODE / "tools" / "diag_change_request.py",
    CODE / "tools" / "diag_validation_dialog.py",
    CODE / "tools" / "dump_change_request_section.py",
    # Backups (.bak, .bak2, .bak_fix5, .bak_fix6)
    CODE / "codegen" / "validate" / "prompt_generator.py.bak",
    CODE / "codegen" / "validate" / "change_actions.py.bak",
    CODE / "codegen" / "validate" / "change_actions.py.bak2",
    CODE / "codegen" / "validate" / "response_parser.py.bak",
    CODE / "codegen" / "validate" / "validation_dialog.py.bak",
    CODE / "codegen" / "validate" / "validation_dialog.py.bak_fix5",
    CODE / "tests" / "test_v2_8_p1_ai_prompt.py.bak",
    CODE / "tools" / "gui_smoke_v2_8.py.bak_fix5",
    CODE / "tools" / "gui_smoke_v2_8.py.bak_fix6",
    # Duplicate tests mistakenly placed in tools/
    CODE / "tools" / "test_v2_8_p2_response_parser.py",
    CODE / "tools" / "test_v2_8_p4_gui_integration.py",
]

# Patch scripts to move into tools/patches/
PATCH_SCRIPTS = [
    "patch_v2_8_fix3.py",
    "patch_v2_8_fix4.py",
    "patch_v2_8_fix5.py",
    "patch_v2_8_fix6.py",
    "patch_v2_8_phase_b.py",
    "patch_v2_8_phase_b2.py",
    "patch_v2_8_phase_c2.py",
    "patch_v2_8_phase_d1.py",
    "patch_v2_8_readme.py",
    "create_test_v2_8_p2.py",
]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true",
                        help="actually perform deletion / move")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  cleanup_before_v2_8_commit  [{mode}]")
    print("=" * 70)

    print()
    print("Files to delete:")
    for p in TO_DELETE:
        if p.exists():
            print(f"  DEL  {p.relative_to(CODE)}")
            if args.apply:
                p.unlink()
        else:
            print(f"  --   {p.relative_to(CODE)}  (not present)")

    patches_dir = CODE / "tools" / "patches"
    print()
    print(f"Patch scripts to move into {patches_dir.relative_to(CODE)}/:")
    if args.apply:
        patches_dir.mkdir(parents=True, exist_ok=True)
    for name in PATCH_SCRIPTS:
        src = CODE / "tools" / name
        dst = patches_dir / name
        if src.exists():
            print(f"  MV   tools/{name} -> tools/patches/{name}")
            if args.apply:
                src.rename(dst)
        else:
            print(f"  --   tools/{name}  (not present)")

    print()
    if args.apply:
        print("[DONE] cleanup applied.")
    else:
        print("[DRY-RUN] no changes; pass --apply to execute.")
    return 0


if __name__ == "__main__":
    sys.exit(main())