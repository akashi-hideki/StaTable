# code/tools/patches/patch_v3_1_language_menu.py
r"""
v3.1: Add Language menu (English <-> Chinese) and startup auto-load.

Edits:
  E1. i18n/__init__.py: SUPPORTED_LANGUAGES -> ["en", "zh_CN"]
  E2. i18n/__init__.py: LANG_DISPLAY -> remove ja
  E3. main_window.py: add "Language / 语言" menu before View
  E4. gui_main.py: call install_translator(app) at startup

Usage:
    cd code
    python tools\patches\patch_v3_1_language_menu.py
    python tools\patches\patch_v3_1_language_menu.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
I18N_INIT = CODE / "statable_gui" / "i18n" / "__init__.py"
MAIN_WINDOW = CODE / "statable_gui" / "main_window.py"
GUI_MAIN = CODE / "gui_main.py"


def edit_i18n_init(text, apply):
    # E1: SUPPORTED_LANGUAGES
    old1 = 'SUPPORTED_LANGUAGES = ["en", "ja", "zh_CN"]'
    new1 = 'SUPPORTED_LANGUAGES = ["en", "zh_CN"]'
    if old1 in text:
        print("[APPLY] E1 SUPPORTED_LANGUAGES -> [en, zh_CN]")
        text = text.replace(old1, new1, 1)
    elif new1 in text:
        print("[SKIP] E1 already applied")
    else:
        print("[FAIL] E1 anchor not found")
        return text, False

    # E2: LANG_DISPLAY remove ja
    lines = text.split("\n")
    out_lines = []
    removed = False
    for line in lines:
        stripped = line.strip()
        # ja line contains the escape for 日本語
        if stripped.startswith('"ja":') and "65e5" in stripped:
            removed = True
            print("[APPLY] E2 remove ja from LANG_DISPLAY")
            continue
        out_lines.append(line)
    if not removed:
        print("[SKIP] E2 ja already removed")
    text = "\n".join(out_lines)
    return text, True


def edit_main_window(text, apply):
    anchor = '        view_menu = menubar.addMenu(self.tr("View"))'
    if anchor not in text:
        if 'menubar.addMenu("Language / ' in text:
            print("[SKIP] E3 Language menu already present")
            return text, True
        print("[FAIL] E3 view_menu anchor not found")
        return text, False

    insert = (
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
        '\n'
        '        act_en = QAction("English", self)\n'
        '        act_en.triggered.connect(\n'
        '            lambda checked=False: _switch_language("en"))\n'
        '        lang_menu.addAction(act_en)\n'
        '\n'
        '        act_zh = QAction("\\u7b80\\u4f53\\u4e2d\\u6587", self)\n'
        '        act_zh.triggered.connect(\n'
        '            lambda checked=False: _switch_language("zh_CN"))\n'
        '        lang_menu.addAction(act_zh)\n'
        '\n'
    )
    print("[APPLY] E3 insert Language menu before View")
    text = text.replace(anchor, insert + anchor, 1)
    return text, True


def edit_gui_main(text, apply):
    old = (
        '    app = QApplication(sys.argv)\n'
        '    window = MainWindow()'
    )
    new = (
        '    app = QApplication(sys.argv)\n'
        '    from statable_gui.i18n import install_translator\n'
        '    install_translator(app)\n'
        '    window = MainWindow()'
    )
    if old not in text:
        if 'install_translator(app)' in text:
            print("[SKIP] E4 already applied")
            return text, True
        print("[FAIL] E4 anchor not found")
        return text, False
    print("[APPLY] E4 add install_translator(app)")
    text = text.replace(old, new, 1)
    return text, True


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_1_language_menu  [{mode}]")
    print("=" * 70)

    targets = [
        (I18N_INIT, edit_i18n_init),
        (MAIN_WINDOW, edit_main_window),
        (GUI_MAIN, edit_gui_main),
    ]

    modified = {}
    ok = True
    for path, editor in targets:
        if not path.exists():
            print(f"[FAIL] not found: {path}")
            ok = False
            continue
        text = path.read_text(encoding="utf-8")
        new_text, success = editor(text, args.apply)
        if not success:
            ok = False
        if new_text != text:
            modified[path] = (text, new_text)
        print()

    if not ok:
        print("[ABORT] some edits failed")
        return 1

    if not args.apply:
        print("[DRY-RUN] no file written; pass --apply")
        return 0

    for path, (old, new) in modified.items():
        bak = path.with_suffix(path.suffix + ".bak_langmenu")
        if not bak.exists():
            bak.write_text(old, encoding="utf-8")
            print(f"  Backup: {bak.name}")
        path.write_text(new, encoding="utf-8")
        print(f"[DONE] {path.relative_to(CODE.parent)} updated")

    print()
    print("Next:")
    print("  python -c \"import py_compile; py_compile.compile("
          "'statable_gui/main_window.py', doraise=True); print('OK')\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())