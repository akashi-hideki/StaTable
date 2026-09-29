# statable_gui/i18n/__init__.py
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
    "ja": "\u65e5\u672c\u8a9e",
    "zh_CN": "\u7b80\u4f53\u4e2d\u6587",
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
