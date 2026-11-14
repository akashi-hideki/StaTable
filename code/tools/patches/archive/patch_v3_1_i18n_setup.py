# code/tools/patches/patch_v3_1_i18n_setup.py
r"""
Phase v3.1 i18n: create statable_gui/i18n/ infrastructure.

New files:
  - code/statable_gui/i18n/__init__.py
  - code/statable_gui/i18n/README.md

Safety: idempotent (skips if files exist).

Usage:
    cd code
    python tools\patches\patch_v3_1_i18n_setup.py
    python tools\patches\patch_v3_1_i18n_setup.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
I18N_DIR = CODE / "statable_gui" / "i18n"

INIT_PY = '''# statable_gui/i18n/__init__.py
"""Internationalization support for StaTable GUI.

Loads .qm translation files from this directory.

Supported languages:
    en     - English (default, no translation file needed)
    ja     - Japanese
    zh_CN  - Chinese (Simplified)

Usage in gui_main.py or statable_gui/main_window.py:
    from statable_gui.i18n import install_translator
    install_translator(app)
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import (
    QTranslator,
    QLocale,
    QSettings,
    QLibraryInfo,
)
from PySide6.QtWidgets import QApplication

I18N_DIR = Path(__file__).parent
DEFAULT_LANG = "en"
SUPPORTED_LANGUAGES = ["en", "ja", "zh_CN"]
LANG_DISPLAY = {
    "en": "English",
    "ja": "\\u65e5\\u672c\\u8a9e",       # 日本語
    "zh_CN": "\\u7b80\\u4f53\\u4e2d\\u6587",  # 简体中文
}


def available_languages() -> list[str]:
    """Return list of supported language codes."""
    return list(SUPPORTED_LANGUAGES)


def _qm_path(lang: str) -> Path:
    return I18N_DIR / f"statable_{lang}.qm"


def detect_system_language() -> str:
    """Return best-matching language for the current system locale."""
    sys_lang = QLocale.system().name()  # e.g. "ja_JP", "zh_CN"
    for lang in SUPPORTED_LANGUAGES:
        if lang == DEFAULT_LANG:
            continue
        short = lang.split("_")[0]
        if sys_lang.startswith(lang) or sys_lang.startswith(short):
            return lang
    return DEFAULT_LANG


def load_preferred_language() -> str:
    """Load user preference from QSettings, fallback to system."""
    settings = QSettings("StaTable", "StaTable")
    lang = settings.value("ui/language", "")
    if lang and lang in SUPPORTED_LANGUAGES:
        return lang
    return detect_system_language()


def save_preferred_language(lang: str) -> None:
    """Persist user preference."""
    if lang not in SUPPORTED_LANGUAGES:
        return
    settings = QSettings("StaTable", "StaTable")
    settings.setValue("ui/language", lang)


def install_translator(app: QApplication,
                       lang: Optional[str] = None) -> Optional[QTranslator]:
    """Install translator for the given language.

    Returns the installed QTranslator (kept alive by reference on app),
    or None if no translation file was loaded (e.g. English).
    """
    if lang is None:
        lang = load_preferred_language()
    if lang not in SUPPORTED_LANGUAGES or lang == DEFAULT_LANG:
        return None

    qm = _qm_path(lang)
    if not qm.exists():
        return None

    translator = QTranslator()
    if not translator.load(str(qm)):
        return None
    app.installTranslator(translator)

    # Install Qt's own translations for built-in dialogs
    qt_tr = QTranslator()
    qt_path = QLibraryInfo.path(QLibraryInfo.TranslationsPath)
    if qt_tr.load(f"qtbase_{lang}", qt_path):
        app.installTranslator(qt_tr)
        # keep reference alive
        translator._qt_translator = qt_tr  # noqa: SLF001

    # keep reference so Python doesn't GC it
    app._statable_translator = translator  # noqa: SLF001
    return translator


__all__ = [
    "install_translator",
    "available_languages",
    "detect_system_language",
    "load_preferred_language",
    "save_preferred_language",
    "DEFAULT_LANG",
    "SUPPORTED_LANGUAGES",
    "LANG_DISPLAY",
]
'''

README_MD = '''# StaTable GUI - Internationalization (i18n)

This directory holds translation resources for the StaTable GUI.

## Supported languages

| Code   | Language          | Status       |
|--------|-------------------|--------------|
| `en`   | English (default) | n/a (source) |
| `ja`   | Japanese          | planned      |
| `zh_CN`| Chinese (Simplified) | planned   |

## Files

- `statable_<lang>.ts` - Translation source (XML, human-editable)
- `statable_<lang>.qm` - Compiled translation (loaded by QTranslator)

## Workflow

### 1. Wrap translatable strings

In GUI code, wrap user-visible strings with `self.tr(...)`:

    self.setWindowTitle(self.tr("Code generation"))

### 2. Extract strings to .ts files

    cd code
    python tools/i18n_extract.py

This runs `lupdate` and regenerates `statable_ja.ts` and `statable_zh_CN.ts`.

### 3. Translate

Option A: Open with Qt Linguist

    "C:\\Program Files\\Python313\\Lib\\site-packages\\PySide6\\linguist.exe" statable_gui/i18n/statable_ja.ts

Option B: Edit the .ts XML directly

Option C: Machine-translate then review (see HANDOVER for i18n).

### 4. Compile to .qm

    cd code
    python tools/i18n_compile.py

This runs `lrelease` on every `*.ts` and produces `*.qm`.

### 5. Test

    cd code
    python -c "import sys; sys.path.insert(0, '.'); from statable_gui.i18n import install_translator; print('OK')"

Run the GUI and switch language via Settings menu.

## Adding a new language

1. Add the language code to `SUPPORTED_LANGUAGES` in `__init__.py`
2. Add display name to `LANG_DISPLAY`
3. Add the code to `LANGS` in `tools/i18n_extract.py`
4. Run extract + translate + compile
'''


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_1_i18n_setup  [{mode}]")
    print("=" * 70)

    targets = [
        (I18N_DIR / "__init__.py", INIT_PY),
        (I18N_DIR / "README.md", README_MD),
    ]

    rc = 0
    for path, content in targets:
        rel = path.relative_to(CODE.parent)
        if path.exists():
            print(f"[SKIP] {rel} already exists")
            continue
        print(f"[APPLY] create {rel} ({len(content)} chars)")
        if not args.apply:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"[DONE] {rel}")

    if not args.apply:
        print()
        print("[DRY-RUN] no file written; pass --apply to execute.")
    return rc


if __name__ == "__main__":
    sys.exit(main())