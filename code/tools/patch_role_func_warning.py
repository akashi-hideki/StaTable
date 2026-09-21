#!/usr/bin/env python3
"""Fix false-positive "Undefined role function reference" warnings.

Background
----------
v3.12's sample_data.py sets namespace="Application" on all sample role
functions, so their qualified_name is "Application.Start_Init", etc.
However, the sample's pre_actions / cell_actions still reference the
bare name "Start_Init". The codegen's call_map therefore contains the
bare name, but defined_keys only contains qualified names — causing a
false-positive warning for every role function.

The code path that actually resolves call_sites already falls back to
the bare name (see _get_call_sites_for_func), so the generated C code
was always correct. Only the warning was wrong.

Fix
---
Add the bare name to defined_keys alongside qualified_name. This
prevents the false positives without changing any generated code.

Version History
---------------
v1.0 - Initial: add bare name to defined_keys.

Usage
-----
    python tools/patch_role_func_warning.py            # dry-run
    python tools/patch_role_func_warning.py --apply
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


TARGET_FILE = "codegen/role_function_generator.py"


# The "before" snippet exactly as it appears in v3.3.
OLD = """\
        # v1.5 addition: detect undefined references (before filtering)
        if call_map:
            defined_keys = set()
            for f in unique_funcs:
                qn = getattr(f, 'qualified_name', None) \\
                    or getattr(f, 'name', '')
                if qn:
                    defined_keys.add(qn)
            for ref in call_map.keys():
                if ref and ref not in defined_keys:
                    self._log_debug(
                        f"Undefined role function reference in "
                        f"transitions: '{ref}' (not in role_functions)",
                        'warning',
                    )
"""

# The "after" snippet: register the bare name too.
NEW = """\
        # v1.5 addition: detect undefined references (before filtering)
        if call_map:
            defined_keys = set()
            for f in unique_funcs:
                qn = getattr(f, 'qualified_name', None) \\
                    or getattr(f, 'name', '')
                if qn:
                    defined_keys.add(qn)
                # [v3.3.1 fix] Also register the bare name. The call_map
                # may contain bare names (e.g. "Start_Init") even when
                # the function is defined with a namespace
                # (e.g. "Application.Start_Init"). The resolver
                # _get_call_sites_for_func() already falls back to bare
                # names, so the generated C code was always correct;
                # only this warning was wrong.
                bare = getattr(f, 'name', '')
                if bare:
                    defined_keys.add(bare)
            for ref in call_map.keys():
                if ref and ref not in defined_keys:
                    self._log_debug(
                        f"Undefined role function reference in "
                        f"transitions: '{ref}' (not in role_functions)",
                        'warning',
                    )
"""


def apply_patch(root: Path, apply: bool, backup: bool) -> bool:
    path = root / TARGET_FILE
    print("=" * 78)
    print(f"  {TARGET_FILE}")
    print("=" * 78)

    if not path.exists():
        print(f"  [SKIP] file not found: {path}")
        return True

    text = path.read_text(encoding="utf-8")
    original = text

    count = text.count(OLD)
    print()
    print(f"  Matches: {count}")

    if count == 0:
        print("  [SKIP] anchor not found (already patched?)")
        return True
    if count > 1:
        print(f"  [WARN] {count} matches; replacing only the first")

    text = text.replace(OLD, NEW, 1)

    # Diff preview
    print()
    print("  --- diff preview ---")
    for line in OLD.splitlines()[-8:]:
        print(f"      - {line}")
    print("      ...")
    for line in NEW.splitlines()[-12:]:
        print(f"      + {line}")

    if text == original:
        print()
        print("  [INFO] no changes")
        return True

    if not apply:
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
    return True


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
    print("  Fix false-positive role function reference warnings")
    print("=" * 78)
    print(f"  Root: {root}")
    print(f"  Mode: {'APPLY' if apply_flag else 'DRY-RUN'}")

    ok = apply_patch(root, apply_flag, backup)

    print()
    print("=" * 78)
    print(f"  Result: {'OK' if ok else 'FAILED'}")
    print("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())