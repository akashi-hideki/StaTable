#!/usr/bin/env python3
"""Update SPEC_SDK_API_en.md to reflect v2.4.1 fixes.

Reflects:
  - C-28 (ChangeApplier duplicate check) — L-19 resolved
  - C-19 (warning newline) — no SDK impact, but noted
  - C-38 (settings_changed emit) — GUI only, no SDK impact

Also adds:
  - C-27 (AIResponseParser cell-level not implemented) note
  - C-30 (CellValidator design) note
  - C-31 (EventValidator duplication) note

Uses str.replace to avoid regex escape issues.

Usage:
    python tools/update_sdk_docs.py             # dry-run
    python tools/update_sdk_docs.py --apply
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


# ======================================================================
# Patch definitions (literal str.replace)
# ======================================================================

# --- §9 L-19 : ChangeApplier duplicate check now implemented -----------
L19_OLD = (
    "| L-19 | `ChangeApplier._add_variable/_add_flag` do not check "
    "duplicates |\n"
)
L19_NEW = (
    "| L-19 | `ChangeApplier._add_variable/_add_flag` **now reject "
    "duplicates** (fixed in v2.4.1, C-28) |\n"
)


# --- §9 L-18 : AIResponseParser cell-level (unchanged, keep) -----------
# (no change; kept for reference)

# --- §9 : add L-30 (C-30) and L-31 (C-31) if missing -------------------
L30_ADD_ANCHOR = (
    "| L-29 | Two distinct `GlobalDefinitions` classes "
    "(`statable` vs `statable_gui`) |\n"
)
L30_ADD_NEW = (
    L30_ADD_ANCHOR
    + "| L-30 | `CellValidator` uses a different design pattern "
    "(no `validate()` override, `suggestion` unset) |\n"
    + "| L-31 | `EventValidator` has semantically duplicated rules "
    "(`EVENT_UNUSED` ≡ `EVENT_NO_TRANSITION`) |\n"
)


# --- §5.7.3 ChangeApplier : add C-28 note -------------------------------
CHANGE_APPLIER_OLD = (
    "**Limitation**: `_add_variable` and `_add_flag` do not check "
    "duplicates. See §9 L-19."
)
CHANGE_APPLIER_NEW = (
    "**Note (v2.4.1 / C-28)**: `_add_variable` and `_add_flag` now "
    "reject duplicate names and empty names. See §9 L-19."
)


# --- §5.4 Item Validators : add C-31 note --------------------------------
EVENT_VALIDATOR_OLD = (
    "**Note on `ROLE_FUNC_UNUSED`**: The implementation checks only "
    "`Transition.action` and `Transition.condition` (exact string match). "
    "In v2.2, `pre_actions` / `else_actions` / cell actions are **not** "
    "considered, so the rule may produce false positives when only v2.2 "
    "action fields are used. See §9 L-23."
)
EVENT_VALIDATOR_NEW = (
    EVENT_VALIDATOR_OLD
    + "\n\n**Note on `EventValidator` (v2.4.1)**: `EVENT_UNUSED` and "
    "`EVENT_NO_TRANSITION` are semantically duplicated. See §9 L-31."
)


# --- §5.3 BaseValidator : add C-30 note ---------------------------------
BASE_VALIDATOR_OLD = (
    "**Pattern B (1 validator: `CellValidator`)**: Do **not** override "
    "`validate()`; use `_make_issue(code, message, target)` with a "
    "hard-coded message string. `suggestion` is not set. See §9 L-21."
)
BASE_VALIDATOR_NEW = (
    "**Pattern B (1 validator: `CellValidator`)**: Do **not** override "
    "`validate()`; use `_make_issue(code, message, target)` with a "
    "hard-coded message string. `suggestion` is not set. See §9 L-21 / L-30."
)


PATCHES = [
    {
        "id": "SDK-L19",
        "desc": "§9 L-19: ChangeApplier duplicate check now implemented",
        "old": L19_OLD,
        "new": L19_NEW,
    },
    {
        "id": "SDK-L30-L31",
        "desc": "§9: add L-30 (C-30) and L-31 (C-31)",
        "old": L30_ADD_ANCHOR,
        "new": L30_ADD_NEW,
    },
    {
        "id": "SDK-5.7.3",
        "desc": "§5.7.3: ChangeApplier note updated",
        "old": CHANGE_APPLIER_OLD,
        "new": CHANGE_APPLIER_NEW,
    },
    {
        "id": "SDK-5.4",
        "desc": "§5.4: EventValidator duplication note added",
        "old": EVENT_VALIDATOR_OLD,
        "new": EVENT_VALIDATOR_NEW,
    },
    {
        "id": "SDK-5.3",
        "desc": "§5.3: BaseValidator CellValidator reference updated",
        "old": BASE_VALIDATOR_OLD,
        "new": BASE_VALIDATOR_NEW,
    },
]

TARGET_FILE = "docs/SPEC_SDK_API_en.md"


# ======================================================================
# Application engine
# ======================================================================
def apply_patches(root: Path, apply: bool, backup: bool) -> bool:
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

        # Diff preview
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

    if not apply:
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
    apply = args.apply
    backup = not args.no_backup

    print("=" * 78)
    print("  SDK API document updater (v2.4.1)")
    print("=" * 78)
    print(f"  Root: {root}")
    print(f"  Mode: {'APPLY' if apply else 'DRY-RUN'}")

    ok = apply_patches(root, apply, backup)

    print()
    print("=" * 78)
    print(f"  Result: {'OK' if ok else 'FAILED'}")
    print("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())