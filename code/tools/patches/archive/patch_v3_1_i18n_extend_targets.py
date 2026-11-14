# code/tools/patches/patch_v3_1_i18n_extend_targets.py
r"""
v3.1 fix: extend i18n_wrap_ast TARGETS with menu/tab/action patterns.

Adds:
  - QAction (menu items)
  - addAction (menu items)
  - addTab (tab titles)
  - setTabText
  - setTitle (dock/group)

Usage:
    cd code
    python tools\patches\patch_v3_1_i18n_extend_targets.py
    python tools\patches\patch_v3_1_i18n_extend_targets.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
TARGET = CODE / "tools" / "i18n_wrap_ast.py"

OLD = '''TARGETS = {
    "QLabel": [0],
    "QPushButton": [0],
    "QCheckBox": [0],
    "QRadioButton": [0],
    "QGroupBox": [0],
    "QToolButton": [0],
    "setWindowTitle": [0],
    "setToolTip": [0],
    "setStatusTip": [0],
    "setWhatsThis": [0],
    "setText": [0],
    "setPlaceholderText": [0],
    "addItem": [0],
}'''

NEW = '''TARGETS = {
    "QLabel": [0],
    "QPushButton": [0],
    "QCheckBox": [0],
    "QRadioButton": [0],
    "QGroupBox": [0],
    "QToolButton": [0],
    "QAction": [0],
    "setWindowTitle": [0],
    "setToolTip": [0],
    "setStatusTip": [0],
    "setWhatsThis": [0],
    "setText": [0],
    "setPlaceholderText": [0],
    "setTabText": [1],
    "addItem": [0],
    "addAction": [0],
    "addTab": [1],
    "setTitle": [0],
}'''


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_1_i18n_extend_targets  [{mode}]")
    print("=" * 70)

    if not TARGET.exists():
        print(f"[FAIL] not found: {TARGET}")
        return 1

    text = TARGET.read_text(encoding="utf-8")
    if "QAction" in text and "addTab" in text:
        print("[SKIP] already extended")
        return 0

    n = text.count(OLD)
    if n != 1:
        print(f"[FAIL] anchor found {n} times (expected 1)")
        return 1

    new_text = text.replace(OLD, NEW, 1)

    print("[APPLY] extend TARGETS with QAction/addAction/addTab/setTabText/setTitle")
    if not args.apply:
        print()
        print("[DRY-RUN] no file written; pass --apply")
        return 0

    bak = TARGET.with_suffix(TARGET.suffix + ".bak_targets")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
        print(f"  Backup: {bak.name}")

    TARGET.write_text(new_text, encoding="utf-8")
    print(f"[DONE] {TARGET.name} updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())