#!/usr/bin/env python3
# code/tools/patch_c50_caller.py
"""C-50 fix (caller side): pass state_machine to generate_all_declarations.

Patches codegen/c_code_generator.py:
  - _step_role_declarations (or equivalent) currently calls
    generate_all_declarations(self._get_role_functions_list(sm))
    without forwarding `sm`. This patch adds `sm` as the second
    argument so the generator can build its call_map and honor
    non-prefix namespaces.

Usage:
    python tools/patch_c50_caller.py --dry-run
    python tools/patch_c50_caller.py
"""

from __future__ import annotations
import argparse
import datetime as _dt
import shutil
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent.parent
TARGET = BASE / "codegen" / "c_code_generator.py"


OLD = '''            decls = (self.role_func_gen
                     .generate_all_declarations(
                         self._get_role_functions_list(sm)))
'''

NEW = '''            decls = (self.role_func_gen
                     .generate_all_declarations(
                         self._get_role_functions_list(sm),
                         state_machine=sm))
'''


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    if not TARGET.exists():
        print(f"ERROR: {TARGET} not found", file=sys.stderr)
        return 1

    text = TARGET.read_text(encoding="utf-8")
    print(f"Target: {TARGET}")
    print(f"Mode:   {'DRY-RUN' if args.dry_run else 'APPLY'}")
    print()

    n = text.count(OLD)
    if n == 0:
        print("[MISS] anchor not found")
        return 1
    print(f"[ OK ] caller update  ({n} replacement{'s' if n > 1 else ''})")

    if args.dry_run:
        return 0

    new_text = text.replace(OLD, NEW)

    if not args.no_backup:
        ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = TARGET.with_suffix(f".py.bak_c50caller_{ts}")
        shutil.copy2(TARGET, bak)
        print(f"Backup: {bak.name}")

    TARGET.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"Written: {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())