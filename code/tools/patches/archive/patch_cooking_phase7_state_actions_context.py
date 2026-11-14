"""Phase 7.2: forward full editing context to StateActionsDialog.

Text-level (idempotent) patch for two call sites:
  1. statable_gui/matrix_table.py :: open_state_actions_for_header
  2. statable_gui/widgets.py      :: _open_state_actions

Both call StateActionsDialog(...) with only (parent, state, state_machine).
This patch adds:
    role_function_library / literal_library /
    [condition_library]   / layer_names_provider / global_defs

Idempotency: skip if the marker "v3.4.0" is already present in the file.

Usage:
    python code/tools/patches/patch_cooking_phase7_state_actions_context.py
    python .../patch_...py --dry-run
    python .../patch_...py --no-backup
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
CODE_DIR = SCRIPT.parent.parent.parent
GUI_DIR = CODE_DIR / "statable_gui"

MARKER = "[v3.4.0]"

# ======================================================================
# Patch definitions
# ======================================================================
PATCHES = [
    {
        "path": GUI_DIR / "matrix_table.py",
        "name": "open_state_actions_for_header",
        "old": (
            "        state = self.sm.states[state_name]\n"
            "        dlg = StateActionsDialog(\n"
            "            parent=self, state=state, state_machine=self.sm)\n"
        ),
        "new": (
            "        state = self.sm.states[state_name]\n"
            "        # [v3.4.0] Forward full editing context\n"
            "        dlg = StateActionsDialog(\n"
            "            parent=self,\n"
            "            state=state,\n"
            "            state_machine=self.sm,\n"
            "            role_function_library=self.role_function_library,\n"
            "            literal_library=self.literal_library,\n"
            "            condition_library=self.condition_library,\n"
            "            layer_names_provider=self.layer_names_provider,\n"
            "            global_defs=self.global_defs,\n"
            "        )\n"
        ),
    },
    {
        "path": GUI_DIR / "widgets.py",
        "name": "_open_state_actions",
        "old": (
            "        state = self.sm.states[name]\n"
            "        dlg = StateActionsDialog(\n"
            "            parent=self, state=state, state_machine=self.sm)\n"
        ),
        "new": (
            "        state = self.sm.states[name]\n"
            "        # [v3.4.0] Forward full editing context\n"
            "        dlg = StateActionsDialog(\n"
            "            parent=self,\n"
            "            state=state,\n"
            "            state_machine=self.sm,\n"
            "            role_function_library=self.role_function_library,\n"
            "            literal_library=self.literal_library,\n"
            "            layer_names_provider=self.layer_names_provider,\n"
            "            global_defs=self.global_defs,\n"
            "        )\n"
        ),
    },
]


# ======================================================================
# Core
# ======================================================================
def patch_file(entry: dict, dry_run: bool, make_backup: bool) -> str:
    """Return one of: 'OK', 'SKIP', 'MISS', 'ERR'."""
    path: Path = entry["path"]
    name = entry["name"]

    if not path.exists():
        print(f"[ERR]  {path.name}: file not found")
        return "ERR"

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # --- Idempotency check ------------------------------------------------
    if MARKER in text:
        print(f"[SKIP] {path.name} ({name}): already patched ({MARKER})")
        return "SKIP"

    # --- Pattern presence check ------------------------------------------
    if entry["old"] not in text:
        # try to locate the target function for a helpful message
        anchor = f"def {name}("
        if anchor in text:
            print(f"[ERR]  {path.name}: '{anchor}' found, but expected "
                  "old snippet not matched.")
            print("       The file may have been modified since the "
                  "patch was authored.")
            # Show the current StateActionsDialog( call for diagnosis
            for i, line in enumerate(lines, 1):
                if "StateActionsDialog(" in line and "import" not in line:
                    print(f"       L{i}: {line.rstrip()}")
            return "ERR"
        print(f"[MISS] {path.name}: '{name}' function not found")
        return "MISS"

    # --- Backup ----------------------------------------------------------
    if make_backup and not dry_run:
        bak = path.with_suffix(path.suffix + ".bak_v3.4.0")
        if not bak.exists():
            shutil.copy2(path, bak)
            print(f"[BAK]  {path.name} -> {bak.name}")

    # --- Apply -----------------------------------------------------------
    new_text = text.replace(entry["old"], entry["new"], 1)

    if dry_run:
        print(f"[DRY]  {path.name}: would replace ({name})")
        # Show diff
        old_lines = entry["old"].rstrip("\n").splitlines()
        new_lines = entry["new"].rstrip("\n").splitlines()
        print("       --- old")
        for ln in old_lines:
            print(f"         {ln}")
        print("       +++ new")
        for ln in new_lines:
            print(f"         {ln}")
        return "OK"

    path.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"[OK]   {path.name}: patched ({name})")
    return "OK"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without writing")
    parser.add_argument("--no-backup", action="store_true",
                        help="Skip .bak_v3.4.0 backup files")
    args = parser.parse_args()

    print("=" * 74)
    print("  Phase 7.2: StateActionsDialog context forwarding")
    print("=" * 74)
    print(f"  GUI dir: {GUI_DIR}")
    print(f"  Dry-run: {args.dry_run}")
    print(f"  Backup : {not args.no_backup}")
    print("=" * 74)

    results = []
    for entry in PATCHES:
        res = patch_file(entry, args.dry_run, not args.no_backup)
        results.append((entry["path"].name, res))

    print()
    print("=" * 74)
    print("  Summary")
    print("=" * 74)
    ok = skip = err = 0
    for fname, res in results:
        print(f"  {res:<5} {fname}")
        if res == "OK":
            ok += 1
        elif res == "SKIP":
            skip += 1
        else:
            err += 1

    print()
    print(f"  OK: {ok}   SKIP: {skip}   ERR/MISS: {err}")
    print("=" * 74)

    if args.dry_run:
        print("  (dry-run: no files were written)")
    elif err:
        print("  !! One or more patches failed. See [ERR]/[MISS] above.")
    else:
        print("  Done. Run tests:")
        print("    python code/tests/test_v2_7_p4.py")
        print("    python code/tests/test_v2_7_p5.py")
    print("=" * 74)

    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
