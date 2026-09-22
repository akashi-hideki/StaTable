#!/usr/bin/env python3
# code/tools/patch_user_suppress_v25.py
"""Move the ctx->data (void) suppression block into the user-code marker.

Motivation:
  The auto-generated role function body currently emits:

      uint32_t *const balance = &ctx->data.balance;
      ...
      (void)balance;   /* suppress unused warning */
      ...

      /* [[STABLE_USER_CODE_START:xxx]] */
      /* Write user implementation code here */
      /* [[STABLE_USER_CODE_END:xxx]] */

  Users who want to remove the (void) lines once they start using the
  variables must delete them from the auto-generated (non-editable)
  region, which is overwritten on regeneration.

Fix:
  Move the (void) suppression block inside the USER_CODE marker with
  an explanatory comment. After the first regeneration, users can
  freely delete individual (void) lines and the change is preserved
  by code_merger (marker contents are user-owned).

Changes to codegen/role_function_generator.py:
  [1] Split _generate_local_data_pointers into:
        - _generate_local_data_decls    (declarations only)
        - _generate_local_data_suppress (the (void) block + comment)
      Keep _generate_local_data_pointers as a thin wrapper for
      backward compatibility (delegates to _decls).
  [2] generate_implementation: insert _generate_local_data_suppress
      inside the user marker, right after user_marker_start.

Usage:
    python tools/patch_user_suppress_v25.py --dry-run
    python tools/patch_user_suppress_v25.py
"""

from __future__ import annotations
import argparse
import datetime as _dt
import shutil
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent.parent
TARGET = BASE / "codegen" / "role_function_generator.py"


# ----------------------------------------------------------------------
# [1] Split _generate_local_data_pointers
# ----------------------------------------------------------------------
OLD_1 = '''    def _generate_local_data_pointers(self, global_defs) -> str:
        """Generate local pointers to ctx->data and explicitly discard
        them with (void) so that unused ones don't raise warnings.

        [v3.2 / MISRA 17.7 / unreadVariable]
          User code marker may use only a subset of these pointers.
          The (void) cast suppresses the warning while leaving the
          pointers usable inside the marker.
        """
        if global_defs is None:
            return ""
        variables = getattr(global_defs, 'variables', []) or []
        if not variables:
            return ""
        T = self.IMPLEMENTATION_TEMPLATES
        parts = [T['local_data_header']]
        for var in variables:
            var_name = self.naming.sanitize_identifier(
                getattr(var, 'name', 'unnamed')
            )
            c_type = self.mapper.map_type(
                getattr(var, 'type', 'void')
            )
            comment = self._format_var_comment(var)
            array_size = getattr(var, 'array_size', 0)
            if array_size > 0:
                parts.append(T['local_data_array'].substitute(
                    c_type=c_type, var_name=var_name,
                    comment=comment,
                ))
            else:
                parts.append(T['local_data_pointer'].substitute(
                    c_type=c_type, var_name=var_name,
                    comment=comment,
                ))
        # [v3.2] Explicit discard to suppress unreadVariable warnings.
        for var in variables:
            var_name = self.naming.sanitize_identifier(
                getattr(var, 'name', 'unnamed')
            )
            parts.append(f'    (void){var_name};'
                         f'   /* suppress unused warning */\\n')
        parts.append(T['blank'])
        return ''.join(parts)
'''

NEW_1 = '''    def _generate_local_data_decls(self, global_defs) -> str:
        """Generate local pointer declarations to ctx->data.

        [v2.5.2 / user-editable suppression]
          The (void) suppression lines previously emitted here have
          been moved into the user-code marker (see
          _generate_local_data_suppress). This keeps the declarations
          outside the marker (they must match the data layout) while
          letting the user delete individual (void) lines.
        """
        if global_defs is None:
            return ""
        variables = getattr(global_defs, 'variables', []) or []
        if not variables:
            return ""
        T = self.IMPLEMENTATION_TEMPLATES
        parts = [T['local_data_header']]
        for var in variables:
            var_name = self.naming.sanitize_identifier(
                getattr(var, 'name', 'unnamed')
            )
            c_type = self.mapper.map_type(
                getattr(var, 'type', 'void')
            )
            comment = self._format_var_comment(var)
            array_size = getattr(var, 'array_size', 0)
            if array_size > 0:
                parts.append(T['local_data_array'].substitute(
                    c_type=c_type, var_name=var_name,
                    comment=comment,
                ))
            else:
                parts.append(T['local_data_pointer'].substitute(
                    c_type=c_type, var_name=var_name,
                    comment=comment,
                ))
        parts.append(T['blank'])
        return ''.join(parts)

    def _generate_local_data_suppress(self, global_defs) -> str:
        """Generate the (void) suppression block for ctx->data pointers.

        [v2.5.2 / user-editable]
          This block is emitted INSIDE the user-code marker so the user
          can delete individual (void) lines as they start using the
          variables. Once edited, code_merger preserves the user's
          version across regenerations.
        """
        if global_defs is None:
            return ""
        variables = getattr(global_defs, 'variables', []) or []
        if not variables:
            return ""
        parts = []
        # [v2.5.2] Explanatory header, printed once per role function.
        parts.append(
            '    /* --- auto-generated: unused-variable suppression ---\\n'
            '     *     Delete each (void) line once you start using the\\n'
            '     *     corresponding pointer. Keeping them all is\\n'
            '     *     harmless (no-op).                                   */\\n'
        )
        for var in variables:
            var_name = self.naming.sanitize_identifier(
                getattr(var, 'name', 'unnamed')
            )
            parts.append(f'    (void){var_name};'
                         f'   /* suppress unused warning */\\n')
        parts.append('\\n')
        return ''.join(parts)

    def _generate_local_data_pointers(self, global_defs) -> str:
        """Legacy wrapper: delegate to _generate_local_data_decls.

        Kept for backward compatibility with any caller (including
        tests) that still uses the old name. New code should call
        _generate_local_data_decls directly.
        """
        return self._generate_local_data_decls(global_defs)
'''


# ----------------------------------------------------------------------
# [2] generate_implementation: move suppress into user marker
# ----------------------------------------------------------------------
OLD_2 = '''        if self._has_local_data_pointers(global_defs):
            parts.append(self._generate_local_data_pointers(global_defs))
        else:
            parts.append(T['unused_ctx'])

        parts.append(self._generate_local_retvar())

        parts.append(T['todo_comment'].substitute(
            todo=self.strings['todo']
        ))
        parts.append(T['blank'])

        marker_name = self._get_marker_name(func)
        parts.append(T['user_marker_start'].substitute(
            marker_name=marker_name
        ))
        parts.append(T['user_marker_hint'])
        parts.append(T['user_marker_end'].substitute(
            marker_name=marker_name
        ))
'''

NEW_2 = '''        if self._has_local_data_pointers(global_defs):
            parts.append(self._generate_local_data_decls(global_defs))
        else:
            parts.append(T['unused_ctx'])

        parts.append(self._generate_local_retvar())

        parts.append(T['todo_comment'].substitute(
            todo=self.strings['todo']
        ))
        parts.append(T['blank'])

        marker_name = self._get_marker_name(func)
        parts.append(T['user_marker_start'].substitute(
            marker_name=marker_name
        ))

        # [v2.5.2] (void) suppression lines now live INSIDE the
        # user-code marker so they can be deleted freely.
        if self._has_local_data_pointers(global_defs):
            parts.append(self._generate_local_data_suppress(global_defs))

        parts.append(T['user_marker_hint'])
        parts.append(T['user_marker_end'].substitute(
            marker_name=marker_name
        ))
'''


REPLACEMENTS = [
    ("[1] split _generate_local_data_pointers", OLD_1, NEW_1),
    ("[2] generate_implementation marker order", OLD_2, NEW_2),
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
        bak = TARGET.with_suffix(f".py.bak_usersuppress_{ts}")
        shutil.copy2(TARGET, bak)
        print(f"Backup: {bak.name}")

    TARGET.write_text(text, encoding="utf-8", newline="\n")
    print(f"Written: {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())