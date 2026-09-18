# codegen/validate/clipboard_manager.py
"""\nClipboard management\n"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from validate.logger import logger


class ClipboardManager:
    """Clipboard management class"""
    
    @staticmethod
    def copy_to_clipboard(text: str) -> bool:
        logger.debug(f"copy_to_clipboard: {len(text)} chars")
        try:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(text)
            return True
        except ImportError:
            try:
                from PyQt6.QtWidgets import QApplication
                QApplication.clipboard().setText(text)
                return True
            except ImportError:
                logger.error("Neither PySide6 nor PyQt6 available")
                return False
    
    @staticmethod
    def get_from_clipboard() -> str:
        logger.debug("get_from_clipboard started")
        try:
            from PySide6.QtWidgets import QApplication
            return QApplication.clipboard().text()
        except ImportError:
            try:
                from PyQt6.QtWidgets import QApplication
                return QApplication.clipboard().text()
            except ImportError:
                logger.error("Neither PySide6 nor PyQt6 available")
                return ""