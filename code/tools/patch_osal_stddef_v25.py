#!/usr/bin/env python3
# code/tools/patch_osal_stddef_v25.py
"""Apply v2.5 ARM-toolchain portability fix to codegen/osal_generator.py.

Adds `#include <stddef.h>` to the generated osal.c so that NULL is
defined. Required by ARM GNU Toolchain 14.x (strict C99). MinGW gcc
tolerates the code without it, but the ARM build fails.

Usage:
    python tools/patch_osal_stddef_v25.py --dry-run   # preview only
    python tools/patch_osal_stddef_v25.py             # apply + backup
"""

from __future__ import annotations

import argparse
import datetime as _dt
import shutil
import sys
from pathlib import Path


# ----------------------------------------------------------------------
# Target file
# ----------------------------------------------------------------------
CANDIDATE_PATHS = [
    Path("code/codegen/osal_generator.py"),
    Path("codegen/osal_generator.py"),
    Path("../codegen/osal_generator.py"),
]


def find_target() -> Path:
    for p in CANDIDATE_PATHS:
        if p.exists():
            return p
    sys.exit(
        "ERROR: codegen/osal_generator.py not found. Tried:\n  "
        + "\n  ".join(str(p) for p in CANDIDATE_PATHS)
    )


# ----------------------------------------------------------------------
# Replacement pairs: (description, old, new, expected_count)
# ----------------------------------------------------------------------
REPLACEMENTS: list[tuple[str, str, str, int]] = [

    # ---- [1] docstring: add v2.5 entry ----
    (
        "[1] module docstring: add v2.5 entry",
        "Version: 2.2 (2026-09-20 / MISRA 17.3 fix)\n"
        "  - The generated osal.c now includes its own header \"osal.h\" first.\n"
        "    MISRA C:2012 Rule 17.3 requires that a function be declared before\n"
        "    its definition; including osal.h in osal.c satisfies this without\n"
        "    changing the function signatures.\n"
        "\"\"\"",
        "Version: 2.5 (2026-09-22 / ARM toolchain portability fix)\n"
        "  - The generated osal.c now includes <stddef.h> so that NULL is\n"
        "    defined. Required by ARM GNU Toolchain 14.x (strict C99).\n"
        "\n"
        "Version: 2.2 (2026-09-20 / MISRA 17.3 fix)\n"
        "  - The generated osal.c now includes its own header \"osal.h\" first.\n"
        "    MISRA C:2012 Rule 17.3 requires that a function be declared before\n"
        "    its definition; including osal.h in osal.c satisfies this without\n"
        "    changing the function signatures.\n"
        "\"\"\"",
        1,
    ),

    # ---- [2] _execute_includes docstring: add v2.5 note ----
    (
        "[2] _execute_includes docstring: add v2.5 note",
        "        [v2.2 / MISRA 17.3]\n"
        "          - Header (osal.h): only <stdint.h> / <stdbool.h> are needed.\n"
        "          - Source (osal.c): must include its own header \"osal.h\" FIRST,\n"
        "            so all OSAL function prototypes are visible before the\n"
        "            definitions (MISRA C:2012 Rule 17.3).\n"
        "        \"\"\"",
        "        [v2.2 / MISRA 17.3]\n"
        "          - Header (osal.h): only <stdint.h> / <stdbool.h> are needed.\n"
        "          - Source (osal.c): must include its own header \"osal.h\" FIRST,\n"
        "            so all OSAL function prototypes are visible before the\n"
        "            definitions (MISRA C:2012 Rule 17.3).\n"
        "\n"
        "        [v2.5 / ARM portability]\n"
        "          - Source additionally includes <stddef.h> to make NULL\n"
        "            available. Required by ARM GNU Toolchain 14.x, which\n"
        "            enforces C99 strictly. MinGW gcc accepts the code without\n"
        "            it, but the ARM build fails.\n"
        "        \"\"\"",
        1,
    ),

    # ---- [3] source branch: add #include <stddef.h> ----
    (
        "[3] _execute_includes: insert #include <stddef.h> in source branch",
        "        else:\n"
        "            # Source: include own header first (MISRA 17.3)\n"
        "            os_info = self.osal_templates['os_types'].get(os_type, {})\n"
        "            header_name = os_info.get('header', 'osal.h')\n"
        "            lines.append(f'#include \"{header_name}\"')\n"
        "            lines.append(\"\")\n",
        "        else:\n"
        "            # Source: include own header first (MISRA 17.3)\n"
        "            os_info = self.osal_templates['os_types'].get(os_type, {})\n"
        "            header_name = os_info.get('header', 'osal.h')\n"
        "            lines.append(f'#include \"{header_name}\"')\n"
        "            # [v2.5] <stddef.h> provides NULL. Required by ARM\n"
        "            # GNU Toolchain 14.x (strict C99).\n"
        "            lines.append(\"#include <stddef.h>\")\n"
        "            lines.append(\"\")\n",
        1,
    ),
]


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be applied, without writing.")
    parser.add_argument("--no-backup", action="store_true",
                        help="Do not create a timestamped backup.")
    args = parser.parse_args()

    target = find_target()
    print(f"Target: {target}")
    print(f"Mode:   {'DRY-RUN' if args.dry_run else 'APPLY'}")
    print()

    original = target.read_text(encoding="utf-8")
    text = original

    matched = 0
    missed: list[str] = []
    mismatched: list[tuple[str, int, int]] = []

    for desc, old, new, expected in REPLACEMENTS:
        count = text.count(old)
        if count == 0:
            missed.append(desc)
            print(f"[MISS] {desc}  (old string not found)")
            continue
        if count != expected:
            mismatched.append((desc, expected, count))
            print(f"[WARN] {desc}  "
                  f"(expected {expected}, found {count}) — applying anyway")
        else:
            print(f"[ OK ] {desc}  "
                  f"({count} replacement{'s' if count > 1 else ''})")
        text = text.replace(old, new)
        matched += 1

    print()
    print("=" * 70)
    print(f"  applied:  {matched} / {len(REPLACEMENTS)}")
    print(f"  missed:   {len(missed)}")
    print(f"  mismatch: {len(mismatched)}")
    print("=" * 70)

    if missed:
        print("\nMissed entries (old string not present):")
        for d in missed:
            print(f"  - {d}")

    if args.dry_run:
        print("\nDry-run: no file written.")
        return 0

    if text == original:
        print("\nNo changes; file untouched.")
        return 0

    # ---- backup ----
    if not args.no_backup:
        ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = target.with_suffix(target.suffix + f".bak_{ts}")
        shutil.copy2(target, backup)
        print(f"\nBackup: {backup}")

    # ---- write with LF preserved ----
    target.write_text(text, encoding="utf-8", newline="\n")
    print(f"Written: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())