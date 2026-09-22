#!/usr/bin/env python3
# code/tools/patch_c50_fix.py
"""C-50 fix: make _should_declare_here honor call_map.

Patches codegen/role_function_generator.py:
  [1] _should_declare_here(func) -> _should_declare_here(func, call_map=None)
      Adds the call_map fallback so a non-prefix namespace is declared
      when it is actually called from this layer.
  [2] generate_all_declarations(role_functions) ->
      generate_all_declarations(role_functions, state_machine=None)
      Builds call_map from state_machine and forwards it.

Backward compatible: existing callers keep working (state_machine=None),
only the new argument enables the extended behavior.

Usage:
    python tools/patch_c50_fix.py --dry-run
    python tools/patch_c50_fix.py
"""

from __future__ import annotations
import argparse
import datetime as _dt
import shutil
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent.parent
TARGET = BASE / "codegen" / "role_function_generator.py"


OLD_1 = '''    def _should_declare_here(self, func) -> bool:
        if not self.layer_name:
            return True
        name, namespace = self._resolve_name_and_namespace(func)
        layer = self.layer_name
        if namespace == layer:
            return True
        ns_l, ly_l = namespace.lower(), layer.lower()
        if min(len(ns_l), len(ly_l)) >= 3:
            if ly_l.startswith(ns_l) or ns_l.startswith(ly_l):
                return True
        return False
'''

NEW_1 = '''    def _should_declare_here(self, func, call_map=None) -> bool:
        """Decide whether to emit this function's declaration here.

        [C-50 fix]
          A function is declared in this layer's header if either:
            1. its namespace matches the layer (exact or 3+ char
               prefix match), OR
            2. it is called from somewhere in this layer (call_map hit).

          Condition (2) mirrors _should_emit_implementation so that
          declaration (.h) and definition (.c) stay in sync. Without
          it, a non-prefix namespace (e.g. layer_name="Application",
          namespace="Vending") produced a definition without a
          declaration, causing 'implicit declaration of function'.
        """
        if not self.layer_name:
            return True
        name, namespace = self._resolve_name_and_namespace(func)
        layer = self.layer_name

        # 1a. Exact match
        if namespace == layer:
            return True

        # 1b. Prefix match (App <-> Application, Drv <-> Driver)
        ns_l, ly_l = namespace.lower(), layer.lower()
        if min(len(ns_l), len(ly_l)) >= 3:
            if ly_l.startswith(ns_l) or ns_l.startswith(ly_l):
                return True

        # 1c. [C-50 fix] Called from this layer
        if call_map:
            qn = getattr(func, 'qualified_name', None) or ''
            if qn and call_map.get(qn):
                return True
            bare = getattr(func, 'name', '') or ''
            if bare and call_map.get(bare):
                return True

        return False
'''


OLD_2 = '''    def generate_all_declarations(self, role_functions: List) -> str:
        """Generate declarations for self-layer role functions only.
'''

NEW_2 = '''    def generate_all_declarations(self, role_functions: List,
                                  state_machine=None) -> str:
        """Generate declarations for self-layer role functions only.
'''


OLD_3 = '''        unique_funcs = self._dedupe_by_name(role_functions)
        parts = []
        for func in unique_funcs:
            if not self._should_declare_here(func):
                continue
            parts.append(self.generate_declaration(func))
            parts.append('\\n')
        return ''.join(parts)
'''

NEW_3 = '''        unique_funcs = self._dedupe_by_name(role_functions)
        call_map = self._collect_call_sites(state_machine) \\
            if state_machine is not None else {}
        parts = []
        for func in unique_funcs:
            if not self._should_declare_here(func, call_map):
                continue
            parts.append(self.generate_declaration(func))
            parts.append('\\n')
        return ''.join(parts)
'''


REPLACEMENTS = [
    ("[1] _should_declare_here + call_map", OLD_1, NEW_1),
    ("[2] generate_all_declarations signature", OLD_2, NEW_2),
    ("[3] generate_all_declarations body", OLD_3, NEW_3),
]


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

    matched = 0
    missed = []
    for desc, old, new in REPLACEMENTS:
        n = text.count(old)
        if n == 0:
            missed.append(desc)
            print(f"[MISS] {desc}")
            continue
        print(f"[ OK ] {desc}  ({n} replacement{'s' if n > 1 else ''})")
        text = text.replace(old, new)
        matched += 1

    print()
    print(f"applied: {matched} / {len(REPLACEMENTS)}  missed: {len(missed)}")

    if args.dry_run or matched == 0:
        return 0

    if not args.no_backup:
        ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = TARGET.with_suffix(f".py.bak_c50_{ts}")
        shutil.copy2(TARGET, bak)
        print(f"Backup: {bak.name}")

    TARGET.write_text(text, encoding="utf-8", newline="\n")
    print(f"Written: {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())