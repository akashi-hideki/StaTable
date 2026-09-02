# codegen/validate/clipboard_manager.py
"""
クリップボード管理
"""

from .logger import logger


class ClipboardManager:
    """クリップボード管理クラス"""
    
    @staticmethod
    def copy_to_clipboard(text: str) -> bool:
        """テキストをクリップボードにコピー"""
        logger.debug(f"copy_to_clipboard: {len(text)} chars")
        try:
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            logger.debug("Copied to clipboard successfully")
            return True
        except ImportError:
            try:
                from PyQt6.QtWidgets import QApplication
                clipboard = QApplication.clipboard()
                clipboard.setText(text)
                logger.debug("Copied to clipboard successfully (PyQt6)")
                return True
            except ImportError:
                logger.error("Neither PySide6 nor PyQt6 available")
                return False
        except Exception as e:
            logger.error(f"Clipboard copy failed: {e}")
            return False
    
    @staticmethod
    def get_from_clipboard() -> str:
        """クリップボードからテキストを取得"""
        logger.debug("get_from_clipboard started")
        try:
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            logger.debug(f"Got {len(text)} chars from clipboard")
            return text
        except ImportError:
            try:
                from PyQt6.QtWidgets import QApplication
                clipboard = QApplication.clipboard()
                text = clipboard.text()
                logger.debug(f"Got {len(text)} chars from clipboard (PyQt6)")
                return text
            except ImportError:
                logger.error("Neither PySide6 nor PyQt6 available")
                return ""
        except Exception as e:
            logger.error(f"Clipboard read failed: {e}")
            return ""