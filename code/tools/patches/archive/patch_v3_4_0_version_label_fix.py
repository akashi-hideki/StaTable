"""v3.4.0 version-label fix (safe scope).

Corrects the misapplied "v2.7.2" labels introduced by the
StateActionsDialog combo patch series. Release version: v3.4.0.

SAFE SCOPE:
  - Only touches files I created/modified in this session.
  - Does NOT touch codegen/validate/items/*.py (existing v2.7.2).
  - Does NOT touch test_v2_7_p5_validation.py (existing v2.7.2).

File renames (dry-run aware):
  patch_v2_7_2_regression.py -> patch_v3_4_0_regression.py
  patch_v2_7_2_hotfix.py     -> patch_v3_4_0_hotfix.py
  test_v2_7_p5.py            -> test_v3_4_0_state_actions.py
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
CODE = ROOT / "code"

# Text edits: (path, old, new, idempotency_marker)
TEXT_EDITS = [
    (CODE / "statable_gui" / "matrix_table.py",
     "[v2.7.2] Forward", "[v3.4.0] Forward"),
    (CODE / "statable_gui" / "widgets.py",
     "[v2.7.2] Forward", "[v3.4.0] Forward"),
    (CODE / "tools" / "patches" / "patch_cooking_phase7_state_actions_context.py",
     "v2.7.2", "v3.4.0"),
    (CODE / "tools" / "patches" / "patch_v2_7_2_regression.py",
     "v2.7.2", "v3.4.0"),
    (CODE / "tools" / "patches" / "patch_v2_7_2_hotfix.py",
     "v2.7.2", "v3.4.0"),
    (CODE / "tests" / "test_v2_7_p4.py",
     "[v2.7.2]", "[v3.4.0]"),
    (CODE / "tests" / "test_v2_7_p4.py",
     "v2.7.2", "v3.4.0"),
]

# File renames: (old_rel_path, new_rel_path)
RENAMES = [
    (CODE / "tools" / "patches" / "patch_v2_7_2_regression.py",
     CODE / "tools" / "patches" / "patch_v3_4_0_regression.py"),
    (CODE / "tools" / "patches" / "patch_v2_7_2_hotfix.py",
     CODE / "tools" / "patches" / "patch_v3_4_0_hotfix.py"),
    (CODE / "tests" / "test_v2_7_p5.py",
     CODE / "tests" / "test_v3_4_0_state_actions.py"),
]

# Version bumps: (path, old, new)
VERSION_BUMPS = [
    (CODE / "statable" / "__init__.py", '3.3.0', '3.4.0'),
    (CODE / "codegen" / "__init__.py",  '3.3.0', '3.4.0'),
    (CODE / "pyproject.toml",           '3.3.0', '3.4.0'),
]


def apply_text_edits(dry_run: bool) -> int:
    n = 0
    for path, old, new in TEXT_EDITS:
        if not path.exists():
            print(f"  [MISS] {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        if old not in text:
            print(f"  [SKIP] {path.name}: no '{old}'")
            continue
        count = text.count(old)
        if dry_run:
            print(f"  [DRY]  {path.name}: {count} x '{old}' -> '{new}'")
        else:
            text = text.replace(old, new)
            path.write_text(text, encoding="utf-8", newline="\n")
            print(f"  [OK]   {path.name}: {count} replaced")
        n += 1
    return n


def apply_renames(dry_run: bool) -> int:
    n = 0
    for old, new in RENAMES:
        if not old.exists():
            if new.exists():
                print(f"  [SKIP] {old.name} -> already renamed to {new.name}")
            else:
                print(f"  [MISS] {old.name}")
            continue
        if dry_run:
            print(f"  [DRY]  rename {old.name} -> {new.name}")
        else:
            new.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old), str(new))
            print(f"  [OK]   rename {old.name} -> {new.name}")
        n += 1
    return n


def apply_version_bumps(dry_run: bool) -> int:
    n = 0
    for path, old, new in VERSION_BUMPS:
        if not path.exists():
            print(f"  [MISS] {path.name}")
            continue
        text = path.read_text(encoding="utf-8")
        # Only replace version string in version context
        if path.name == "pyproject.toml":
            old_line = f'version = "{old}"'
            new_line = f'version = "{new}"'
        else:
            old_line = f'__version__ = "{old}"'
            new_line = f'__version__ = "{new}"'
        if old_line not in text:
            if new_line in text:
                print(f"  [SKIP] {path.name}: already at {new}")
            else:
                print(f"  [MISS] {path.name}: pattern '{old_line}' not found")
            continue
        if dry_run:
            print(f"  [DRY]  {path.name}: {old} -> {new}")
        else:
            text = text.replace(old_line, new_line)
            path.write_text(text, encoding="utf-8", newline="\n")
            print(f"  [OK]   {path.name}: version {old} -> {new}")
        n += 1
    return n


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--skip-rename", action="store_true")
    p.add_argument("--skip-version-bump", action="store_true")
    args = p.parse_args()

    print("=" * 74)
    print(f"  v3.4.0 version-label fix  (dry-run={args.dry_run})")
    print("=" * 74)

    print("\n[1] Text edits (v2.7.2 -> v3.4.0 in my session files)")
    print("-" * 74)
    n1 = apply_text_edits(args.dry_run)

    if not args.skip_rename:
        print("\n[2] File renames")
        print("-" * 74)
        n2 = apply_renames(args.dry_run)
    else:
        n2 = 0
        print("\n[2] File renames: SKIPPED")

    if not args.skip_version_bump:
        print("\n[3] Version bumps (3.3.0 -> 3.4.0)")
        print("-" * 74)
        n3 = apply_version_bumps(args.dry_run)
    else:
        n3 = 0
        print("\n[3] Version bumps: SKIPPED")

    print()
    print("=" * 74)
    print(f"  Text edits:    {n1}")
    print(f"  Renames:       {n2}")
    print(f"  Version bumps: {n3}")
    print("=" * 74)
    if args.dry_run:
        print("  (dry-run: no files were modified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())