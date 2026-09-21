#!/usr/bin/env python3
"""Apply C-28 patch: add duplicate checks to ChangeApplier.

ChangeApplier._add_variable / _add_flag did not check for existing
entries, allowing the AI change-applier to create duplicate variables
or flags.

Uses str.replace (not re.sub) to avoid escape-sequence issues.
Verifies the patched file compiles before writing it back.

Usage:
    python tools/patch_c28.py            # dry-run
    python tools/patch_c28.py --apply    # apply
"""

import argparse
import shutil
import sys
from pathlib import Path


# ----------------------------------------------------------------------
# Patch anchors (plain strings, no regex)
# ----------------------------------------------------------------------
OLD_VAR = '''    def _add_variable(self, params: Dict) -> Tuple[bool, str]:
        from statable.global_defs import SystemVariable
        name = params.get('name', '')
        var = SystemVariable(
            name=name, type=params.get('type', 'uint8'),
            group=params.get('group', ''),
            description=params.get('description', ''))
        self.gd.variables.append(var)
        return True, f"Variable '{name}' added"
'''

NEW_VAR = '''    def _add_variable(self, params: Dict) -> Tuple[bool, str]:
        from statable.global_defs import SystemVariable
        name = params.get('name', '')
        if not name:
            return False, "Variable 'name' is required"
        # [C-28 fix] Duplicate check
        if any(getattr(v, 'name', '') == name for v in self.gd.variables):
            return False, f"Variable '{name}' already exists"
        var = SystemVariable(
            name=name, type=params.get('type', 'uint8'),
            group=params.get('group', ''),
            description=params.get('description', ''))
        self.gd.variables.append(var)
        return True, f"Variable '{name}' added"
'''


OLD_FLAG = '''    def _add_flag(self, params: Dict) -> Tuple[bool, str]:
        from statable.global_defs import EventFlag
        name = params.get('name', '')
        flag = EventFlag(
            name=name, min_value=params.get('min_value', 0),
            max_value=params.get('max_value', 1),
            group=params.get('group', ''))
        self.gd.flags.append(flag)
        return True, f"Flag '{name}' added"
'''

NEW_FLAG = '''    def _add_flag(self, params: Dict) -> Tuple[bool, str]:
        from statable.global_defs import EventFlag
        name = params.get('name', '')
        if not name:
            return False, "Flag 'name' is required"
        # [C-28 fix] Duplicate check
        if any(getattr(f, 'name', '') == name for f in self.gd.flags):
            return False, f"Flag '{name}' already exists"
        flag = EventFlag(
            name=name, min_value=params.get('min_value', 0),
            max_value=params.get('max_value', 1),
            group=params.get('group', ''))
        self.gd.flags.append(flag)
        return True, f"Flag '{name}' added"
'''


PATCHES = [
    {
        "id": "C-28-var",
        "old": OLD_VAR,
        "new": NEW_VAR,
        "desc": "Add duplicate check to ChangeApplier._add_variable",
    },
    {
        "id": "C-28-flag",
        "old": OLD_FLAG,
        "new": NEW_FLAG,
        "desc": "Add duplicate check to ChangeApplier._add_flag",
    },
]

TARGET_FILE = "codegen/validate/change_applier.py"


# ----------------------------------------------------------------------
# Application
# ----------------------------------------------------------------------
def apply(root: Path, apply_flag: bool, backup: bool) -> bool:
    path = root / TARGET_FILE
    print("=" * 78)
    print(f"  {TARGET_FILE}")
    print("=" * 78)

    if not path.exists():
        print(f"  [SKIP] file not found: {path}")
        return True

    text = path.read_text(encoding="utf-8")
    original = text
    all_ok = True

    for p in PATCHES:
        count = text.count(p["old"])
        print()
        print(f"  [{p['id']}] {p['desc']}")
        print(f"    Matches: {count}")
        if count == 0:
            print(f"    [SKIP] anchor not found (already patched?)")
            continue
        if count > 1:
            print(f"    [WARN] {count} matches; replacing only the first")

        # Show compact diff preview
        print("    --- diff preview ---")
        for line in p["old"].splitlines():
            print(f"      - {line}")
        for line in p["new"].splitlines():
            print(f"      + {line}")

        text = text.replace(p["old"], p["new"], 1)

    if text == original:
        print()
        print("  [INFO] no changes (all patches already applied)")
        return True

    if not apply_flag:
        print()
        print("  [DRY-RUN] not written (use --apply)")
        return True

    # Verify the patched file compiles
    try:
        compile(text, str(path), "exec")
    except SyntaxError as e:
        print()
        print(f"  [ERROR] patched content has a SyntaxError: {e}")
        print("  [SKIP] refusing to write broken file")
        return False

    if backup:
        bak = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, bak)
        print()
        print(f"  [BACKUP] {bak}")

    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"  [WRITTEN] {path}")
    return all_ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    apply_flag = args.apply
    backup = not args.no_backup

    print("=" * 78)
    print("  C-28 patch applicator (str.replace based)")
    print("=" * 78)
    print(f"  Root: {root}")
    print(f"  Mode: {'APPLY' if apply_flag else 'DRY-RUN'}")

    ok = apply(root, apply_flag, backup)

    print()
    print("=" * 78)
    print(f"  Result: {'OK' if ok else 'FAILED'}")
    print("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())