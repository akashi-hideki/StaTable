#!/usr/bin/env python3
"""Update SPEC_SDK_API_en.md: 5 additional patches for v2.4.1 sync.

Patches:
  §1.5  - Add used_* terms to glossary
  §3.7  - Add used_global_vars/events/literals to RoleFunction (statable)
  §7.5.2 - Add 5 reserved fields to RoleFunction (libcntrl)
  §10.2 - Add test_v2_3_p1.py, update total to 551
  §10.5 - Version Matrix: 2.2 -> 2.4.1, add GUI/data modules

Uses str.replace to avoid regex escape issues.

Usage:
    python tools/update_sdk_docs_v2.py             # dry-run
    python tools/update_sdk_docs_v2.py --apply
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


TARGET_FILE = "docs/SPEC_SDK_API_en.md"


# ======================================================================
# §1.5 : Add used_* terms after transition_id
# ======================================================================
P15_OLD = (
    "| transition_id | Index within call_sites. `0xFFFF` = no match |\n"
    "| Super include | `statable_all.h`. Aggregates all generated headers |\n"
)
P15_NEW = (
    "| transition_id | Index within call_sites. `0xFFFF` = no match |\n"
    "| `used_global_vars` | v3.8: List of SystemVariable names referenced by a role function |\n"
    "| `used_events` | v3.8: List of Event names referenced by a role function |\n"
    "| `used_literals` | v3.8: List of literal names referenced by a role function |\n"
    "| `layer_names_provider` | v3.11: Callable returning all tab names (namespace combo candidates) |\n"
    "| Reserved fields | v3.7 / v1.5: `return_type` / `arg1_*` / `arg2_*` / `do` — not exposed in UI, preserved through XML |\n"
    "| Super include | `statable_all.h`. Aggregates all generated headers |\n"
)


# ======================================================================
# §3.7 : Add used_* fields to RoleFunction (statable) code block
# ======================================================================
P37_CODE_OLD = (
    "    arg2_type: str = \"\"\n"
    "    arg2_name: str = \"\"\n"
    "    title: str = \"\"\n"
    "```\n"
)
P37_CODE_NEW = (
    "    arg2_type: str = \"\"\n"
    "    arg2_name: str = \"\"\n"
    "    title: str = \"\"\n"
    "    # [v3.8] GUI symbol tracking (mirrors libcntrl.RoleFunction).\n"
    "    # Persisted in XML; not consumed by codegen.\n"
    "    used_global_vars: List[str] = []\n"
    "    used_events: List[str] = []\n"
    "    used_literals: List[str] = []\n"
    "```\n"
)

# §3.7 field table: add rows after title row
P37_TABLE_OLD = (
    "| `arg2_name` | `str` | – | `\"\"` |\n"
    "| `title` | `str` | – | `\"\"` |\n"
    "\n"
    "**Properties**\n"
)
P37_TABLE_NEW = (
    "| `arg2_name` | `str` | – | `\"\"` |\n"
    "| `title` | `str` | – | `\"\"` |\n"
    "| `used_global_vars` | `List[str]` | – | `[]` |\n"
    "| `used_events` | `List[str]` | – | `[]` |\n"
    "| `used_literals` | `List[str]` | – | `[]` |\n"
    "\n"
    "**Properties**\n"
)


# ======================================================================
# §7.5.2 : Add 5 reserved fields to libcntrl RoleFunction table
# ======================================================================
P752_OLD = (
    "| `used_literals` | `List[str]` | `[]` |\n"
    "\n"
    "**Property**: `qualified_name`.\n"
)
P752_NEW = (
    "| `used_literals` | `List[str]` | `[]` |\n"
    "| `return_type` | `str` | `\"\"` (Reserved, v1.5) |\n"
    "| `arg1_type` | `str` | `\"\"` (Reserved, v1.5) |\n"
    "| `arg1_name` | `str` | `\"\"` (Reserved, v1.5) |\n"
    "| `arg2_type` | `str` | `\"\"` (Reserved, v1.5) |\n"
    "| `arg2_name` | `str` | `\"\"` (Reserved, v1.5) |\n"
    "\n"
    "**Reserved fields note (v1.5)**: `return_type` / `arg1_*` / `arg2_*` "
    "are not exposed in the GUI and not consumed by codegen. They are "
    "preserved through XML I/O for backward compatibility with pre-v3.7 "
    "project files.\n"
    "\n"
    "**Property**: `qualified_name`.\n"
)


# ======================================================================
# §10.2 : Add test_v2_3_p1.py row, update total to 551
# ======================================================================
P102_OLD = (
    "| 12 | `test_v2_2_p12_10.py` | Stage 10 | 29 PASS / 2 SKIP |\n"
    "| **Total** | | | **537 PASS / 2 SKIP** |\n"
)
P102_NEW = (
    "| 12 | `test_v2_2_p12_10.py` | Stage 10 | 29 PASS / 2 SKIP |\n"
    "| 13 | `test_v2_3_p1.py` | New Project (v2.3) | 14 PASS |\n"
    "| **Total** | | | **551 PASS / 2 SKIP** |\n"
)


# ======================================================================
# §10.5 : Version Matrix update
# ======================================================================
P105_OLD = (
    "| Component | Version |\n"
    "|-----------|---------|\n"
    "| StaTable | 2.2 |\n"
    "| `c_code_generator.py` | 2.2.9 |\n"
    "| `role_function_generator.py` | 3.3 |\n"
    "| `transition_generator.py` | 2.6 |\n"
    "| `code_templates.py` | 2.2.5 |\n"
    "| `struct_generator.py` | 2.2.1 |\n"
    "| `enum_generator.py` | 1.5 |\n"
    "| `variable_generator.py` | 2.0 |\n"
    "| `timer_generator.py` | 2.2 |\n"
    "| `osal_generator.py` | 2.2 |\n"
    "| `naming_convention.py` | 2.2.5 |\n"
    "| `code_merger.py` | 2.0 |\n"
)
P105_NEW = (
    "| Component | Version |\n"
    "|-----------|---------|\n"
    "| StaTable | 2.4.1 |\n"
    "| `c_code_generator.py` | 2.2.9 |\n"
    "| `role_function_generator.py` | 3.3 |\n"
    "| `transition_generator.py` | 2.6 |\n"
    "| `code_templates.py` | 2.2.5 |\n"
    "| `struct_generator.py` | 2.2.1 |\n"
    "| `enum_generator.py` | 1.5 |\n"
    "| `variable_generator.py` | 2.0 |\n"
    "| `timer_generator.py` | 2.2 |\n"
    "| `osal_generator.py` | 2.2 |\n"
    "| `naming_convention.py` | 2.2.5 |\n"
    "| `code_merger.py` | 2.0 |\n"
    "| `widgets.py` | 3.11 |\n"
    "| `main_window.py` | 2.4 |\n"
    "| `role_function_dialog.py` | 3.9 |\n"
    "| `model.py` | 3.8 |\n"
    "| `xml_io.py` | 3.8.2 |\n"
    "| `sample_data.py` | 3.12 |\n"
    "| `libcntrl/role_function_library.py` | 1.5 |\n"
    "| `validate/change_applier.py` | 2.4.1 (C-28 fix) |\n"
)


PATCHES = [
    {"id": "SDK-1.5",   "desc": "Glossary: add used_* + layer_names_provider",
     "old": P15_OLD,  "new": P15_NEW},
    {"id": "SDK-3.7a",  "desc": "§3.7 code: add used_* fields",
     "old": P37_CODE_OLD, "new": P37_CODE_NEW},
    {"id": "SDK-3.7b",  "desc": "§3.7 table: add used_* rows",
     "old": P37_TABLE_OLD, "new": P37_TABLE_NEW},
    {"id": "SDK-7.5.2", "desc": "§7.5.2: add 5 reserved fields",
     "old": P752_OLD, "new": P752_NEW},
    {"id": "SDK-10.2",  "desc": "§10.2: add test_v2_3_p1, total -> 551",
     "old": P102_OLD, "new": P102_NEW},
    {"id": "SDK-10.5",  "desc": "§10.5: Version Matrix -> 2.4.1",
     "old": P105_OLD, "new": P105_NEW},
]


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

        # Compact diff preview (first 4 lines each)
        old_lines = p["old"].splitlines()
        new_lines = p["new"].splitlines()
        print("    --- diff preview ---")
        for line in old_lines[:4]:
            print(f"      - {line}")
        if len(old_lines) > 4:
            print(f"      - ... ({len(old_lines) - 4} more)")
        for line in new_lines[:4]:
            print(f"      + {line}")
        if len(new_lines) > 4:
            print(f"      + ... ({len(new_lines) - 4} more)")

        text = text.replace(p["old"], p["new"], 1)

    if text == original:
        print()
        print("  [INFO] no changes (all patches already applied)")
        return True

    if not apply_flag:
        print()
        print("  [DRY-RUN] not written (use --apply)")
        return True

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
    print("  SDK API document updater v2 (5 patches)")
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