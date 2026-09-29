# code/tools/patches/patch_v3_1_tr_action_edit.py
r"""
Phase v3.1 i18n: wrap translatable strings in action_edit_dialog.py.

Targets:
  - code/statable_gui/action_edit_dialog.py

Edits: 10 replacements (all user-visible strings).

Safety:
  - Idempotent (skips if 'self.tr(' already present)

Usage:
    cd code
    python tools\patches\patch_v3_1_tr_action_edit.py
    python tools\patches\patch_v3_1_tr_action_edit.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
TARGET = CODE / "statable_gui" / "action_edit_dialog.py"

Q1 = chr(39)  # single quote

REPLACEMENTS = [
    (
        'self.setWindowTitle("ActionEdit")',
        'self.setWindowTitle(self.tr("ActionEdit"))',
    ),
    (
        'role_bar.addWidget(QLabel("Role function:"))',
        'role_bar.addWidget(QLabel(self.tr("Role function:")))',
    ),
    (
        'insert_role_btn = QPushButton("Insert")',
        'insert_role_btn = QPushButton(self.tr("Insert"))',
    ),
    (
        'new_role_btn = QPushButton("New role function...")',
        'new_role_btn = QPushButton(self.tr("New role function..."))',
    ),
    (
        'right_layout.addWidget(QLabel("Action code:"))',
        'right_layout.addWidget(QLabel(self.tr("Action code:")))',
    ),
    (
        'QMessageBox.warning(self, "Warning", '
        '"A role function with the same name already exists.")',
        'QMessageBox.warning(\n'
        '                self,\n'
        '                self.tr("Warning"),\n'
        '                self.tr("A role function with the same name '
        'already exists."),\n'
        '            )',
    ),
    (
        'add_var_action = menu.addAction(f"' + Q1 + '{selected_text}'
        + Q1 + ' as global variable")',
        'add_var_action = menu.addAction(\n'
        '            self.tr("' + Q1 + '{0}' + Q1
        + ' as global variable").format(selected_text)\n'
        '        )',
    ),
    (
        'add_flag_action = menu.addAction(f"' + Q1 + '{selected_text}'
        + Q1 + ' as event flag")',
        'add_flag_action = menu.addAction(\n'
        '            self.tr("' + Q1 + '{0}' + Q1
        + ' as event flag").format(selected_text)\n'
        '        )',
    ),
    (
        'auto_title = "(untitled action)"',
        'auto_title = self.tr("(untitled action)")',
    ),
]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_1_tr_action_edit  [{mode}]")
    print("=" * 70)

    if not TARGET.exists():
        print(f"[FAIL] not found: {TARGET}")
        return 1

    text = TARGET.read_text(encoding="utf-8")

    if 'self.tr("ActionEdit")' in text:
        print("[SKIP] already wrapped with tr()")
        return 0

    patched = text
    rc = 0
    for i, (old, new) in enumerate(REPLACEMENTS, 1):
        n = patched.count(old)
        if n == 0:
            print(f"[FAIL] R{i}: anchor not found: {old[:60]!r}")
            rc = 1
            continue
        if n > 1:
            print(f"[FAIL] R{i}: anchor found {n} times: {old[:60]!r}")
            rc = 1
            continue
        print(f"[APPLY] R{i}")
        patched = patched.replace(old, new, 1)

    if rc != 0:
        print()
        print("[ABORT] one or more anchors failed")
        return 1

    if not args.apply:
        print()
        print("[DRY-RUN] no file written; pass --apply to execute.")
        return 0

    bak = TARGET.with_suffix(TARGET.suffix + ".bak_i18n")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
        print(f"  Backup: {bak.name}")

    TARGET.write_text(patched, encoding="utf-8")
    print(f"[DONE] {TARGET.name} updated ({len(text)} -> {len(patched)} chars)")
    print()
    print("Next:")
    print("  python tools\\i18n_extract.py")
    print("  python tools\\i18n_status.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())