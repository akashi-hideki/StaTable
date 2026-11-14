# code/tools/patch_v2_8_fix5.py
"""
Patch v2.8.0-fix5:
  1. validation_dialog._parse_response: invalid rows must not
     re-acquire ItemIsUserCheckable (Qt auto-adds it when
     setCheckState is called).
  2. tools/gui_smoke_v2_8.py: fix the low-confidence warning
     expectation for the mixed valid+invalid sample.

Both edits are literal-anchor based and idempotent.

Usage:
    cd code
    python tools\\patch_v2_8_fix5.py
"""
from __future__ import annotations

import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent.parent
VD = CODE_DIR / "codegen" / "validate" / "validation_dialog.py"
SMOKE = CODE_DIR / "tools" / "gui_smoke_v2_8.py"


# ======================================================================
# Fix 1: validation_dialog.py — drop setCheckState on invalid rows
# ======================================================================
VD_OLD = (
    "        for req, reason in outcome.invalid_requests:\n"
    "            item = QTreeWidgetItem()\n"
    "            item.setFlags(Qt.ItemIsEnabled)\n"
    "            item.setCheckState(0, Qt.Unchecked)\n"
    "            item.setText(1, req.action.value)\n"
)
VD_NEW = (
    "        for req, reason in outcome.invalid_requests:\n"
    "            item = QTreeWidgetItem()\n"
    "            # Non-checkable, non-selectable: an excluded\n"
    "            # proposal must not participate in 'apply selected'.\n"
    "            item.setFlags(Qt.ItemIsEnabled)\n"
    "            item.setText(0, \"\")\n"
    "            item.setText(1, req.action.value)\n"
)


# ======================================================================
# Fix 2: gui_smoke_v2_8.py — 0 warnings expected
# ======================================================================
SMOKE_OLD = '        check("1 warning", len(outcome.warnings) == 1)\n'
SMOKE_NEW = (
    "        # C-002 is rejected at the reference-check stage *before*\n"
    "        # the warning collector runs, so no warning is emitted.\n"
    '        check("0 warnings (only invalid was low-conf)",\n'
    "              len(outcome.warnings) == 0)\n"
)


def _apply(path: Path, anchor: str, replacement: str, label: str) -> bool:
    if not path.exists():
        print(f"  [FAIL] {path} not found")
        return False
    text = path.read_text(encoding="utf-8")
    count = text.count(anchor)
    if count == 0:
        print(f"  [SKIP] {label}: anchor not found (already applied?)")
        return False
    if count > 1:
        print(f"  [FAIL] {label}: anchor found {count} times (expected 1)")
        raise SystemExit(1)
    print(f"  [APPLY] {label}")
    path.write_text(text.replace(anchor, replacement, 1),
                    encoding="utf-8")
    return True


def _backup_once(target: Path) -> None:
    if not target.exists():
        return
    bak = target.with_suffix(target.suffix + ".bak_fix5")
    if not bak.exists():
        bak.write_text(target.read_text(encoding="utf-8"),
                       encoding="utf-8")
        print(f"  Backup: {bak}")
    else:
        print(f"  Backup: already exists, keeping {bak}")


def main() -> int:
    print("=" * 70)
    print("  v2.8.0-fix5 patch")
    print("=" * 70)

    print()
    print(f"Target 1: {VD}")
    _backup_once(VD)
    _apply(VD, VD_OLD, VD_NEW,
           "validation_dialog: drop setCheckState on invalid rows")

    print()
    print(f"Target 2: {SMOKE}")
    _backup_once(SMOKE)
    _apply(SMOKE, SMOKE_OLD, SMOKE_NEW,
           "gui_smoke: 0 warnings expected")

    print()
    print("[DONE] fix5 applied.")
    print()
    print("Verify:")
    print("  python -c \"import ast; "
          "ast.parse(open(r'codegen/validate/validation_dialog.py', "
          "encoding='utf-8').read()); print('syntax OK')\"")
    print("  python tools\\gui_smoke_v2_8.py")
    print("  python tests\\test_v2_8_p4_gui_integration.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())