# codegen/validate/clipboard_manager.py
"""Clipboard management (PySide6 only)."""

import os
import sys

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))))

from .logger import logger


class ClipboardManager:
    """Clipboard management class."""

    @staticmethod
    def copy_to_clipboard(text: str) -> bool:
        logger.debug(f"copy_to_clipboard: {len(text)} chars")
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError:
            logger.error("PySide6 not available")
            return False

        try:
            QApplication.clipboard().setText(text)
            return True
        except Exception as e:
            logger.error(f"Clipboard set failed: {e}")
            return False

    @staticmethod
    def get_from_clipboard() -> str:
        logger.debug("get_from_clipboard started")
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError:
            logger.error("PySide6 not available")
            return ""

        try:
            return QApplication.clipboard().text()
        except Exception as e:
            logger.error(f"Clipboard get failed: {e}")
            return ""
