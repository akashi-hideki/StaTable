# code/tools/patches/patch_v3_1_language_restart.py
r"""
v3.1: Add auto-restart to Language menu.

Replaces the "please restart" message box with a QMessageBox
that offers "Restart now" button. On click, relaunches the app
via QProcess.startDetached and quits the current instance.

Usage:
    cd code
    python tools\patches\patch_v3_1_language_restart.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
TARGET = CODE / "statable_gui" / "main_window.py"

# The block we inserted previously (from patch_v3_1_language_menu.py)
OLD = (
    '        # [v3.1] Language menu (English / Chinese)\n'
    '        lang_menu = menubar.addMenu("Language / \\u8bed\\u8a00")\n'
    '\n'
    '        def _switch_language(code):\n'
    '            from statable_gui.i18n import save_preferred_language\n'
    '            save_preferred_language(code)\n'
    '            from PySide6.QtWidgets import QMessageBox\n'
    '            QMessageBox.information(\n'
    '                self,\n'
    '                "Language / \\u8bed\\u8a00",\n'
    '                "Please restart StaTable to apply the change.\\n"\n'
    '                "\\u8bf7\\u91cd\\u65b0\\u542f\\u52a8 StaTable \\u4ee5'
    '\\u5e94\\u7528\\u66f4\\u6539\\u3002",\n'
    '            )\n'
)

NEW = (
    '        # [v3.1] Language menu (English / Chinese) with auto-restart\n'
    '        lang_menu = menubar.addMenu("Language / \\u8bed\\u8a00")\n'
    '\n'
    '        def _switch_language(code):\n'
    '            from statable_gui.i18n import (\n'
    '                save_preferred_language,\n'
    '                load_preferred_language,\n'
    '            )\n'
    '            current = load_preferred_language()\n'
    '            if code == current:\n'
    '                return\n'
    '            save_preferred_language(code)\n'
    '\n'
    '            from PySide6.QtWidgets import QMessageBox\n'
    '            msg = QMessageBox(self)\n'
    '            msg.setIcon(QMessageBox.Question)\n'
    '            msg.setWindowTitle("Language / \\u8bed\\u8a00")\n'
    '            msg.setText(\n'
    '                "Restart StaTable to apply the new language?\\n"\n'
    '                "\\u662f\\u5426\\u91cd\\u65b0\\u542f\\u52a8 StaTable '
    '\\u4ee5\\u5e94\\u7528\\u65b0\\u7684\\u8bed\\u8a00\\uff1f"\n'
    '            )\n'
    '            btn_restart = msg.addButton(\n'
    '                "Restart now / \\u7acb\\u5373\\u91cd\\u542f",\n'
    '                QMessageBox.AcceptRole)\n'
    '            msg.addButton(\n'
    '                "Later / \\u7a0d\\u540e",\n'
    '                QMessageBox.RejectRole)\n'
    '            msg.exec()\n'
    '            if msg.clickedButton() is not btn_restart:\n'
    '                return\n'
    '\n'
    '            _relaunch_application()\n'
    '\n'
    '        def _relaunch_application():\n'
    '            """Start a new instance detached, then quit."""\n'
    '            import os\n'
    '            import sys as _sys\n'
    '            from PySide6.QtCore import QProcess, QCoreApplication\n'
    '\n'
    '            # Prefer python -m statable (works in editable & installed)\n'
    '            exe = _sys.executable\n'
    '            args = ["-m", "statable"]\n'
    '            cwd = os.getcwd()\n'
    '            ok = QProcess.startDetached(exe, args, cwd)\n'
    '            if not ok:\n'
    '                QMessageBox.warning(\n'
    '                    self,\n'
    '                    "Restart failed",\n'
    '                    "Could not restart automatically.\\n"\n'
    '                    "Please start StaTable manually.",\n'
    '                )\n'
    '                return\n'
    '            QCoreApplication.quit()\n'
)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_1_language_restart  [{mode}]")
    print("=" * 70)

    if not TARGET.exists():
        print(f"[FAIL] not found: {TARGET}")
        return 1

    text = TARGET.read_text(encoding="utf-8")

    if "_relaunch_application" in text:
        print("[SKIP] already has auto-restart")
        return 0

    n = text.count(OLD)
    if n != 1:
        print(f"[FAIL] anchor found {n} times (expected 1)")
        print("--- anchor preview (first 100 chars):")
        print(OLD[:100])
        return 1

    new_text = text.replace(OLD, NEW, 1)
    print("[APPLY] replace restart messagebox with auto-restart dialog")
    if not args.apply:
        print()
        print("[DRY-RUN] no file written; pass --apply")
        return 0

    bak = TARGET.with_suffix(TARGET.suffix + ".bak_restart")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
        print(f"  Backup: {bak.name}")

    TARGET.write_text(new_text, encoding="utf-8")
    print(f"[DONE] {TARGET.relative_to(CODE.parent)} updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())