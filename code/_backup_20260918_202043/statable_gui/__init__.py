# statable_gui package
"""
StaTable GUI 層

【v1.5 追加】
  - 再エクスポートは最小限に留める
  - Qt 依存の重いモジュール（main_window 等）は
    明示的に import することを推奨
"""

# 設定・環境
from .config import WINDOW_WIDTH, WINDOW_HEIGHT

# ロガー（軽量・依存小）
try:
    from .logger import StaTableLogger
except ImportError:
    StaTableLogger = None

__all__ = [
    'WINDOW_WIDTH',
    'WINDOW_HEIGHT',
    'StaTableLogger',
]

# 注意:
#   MainWindow / StateMachineTab 等は再エクスポートしない。
#   PySide6 の QApplication 生成前にロードするとエラーの原因になるため、
#   利用側で `from statable_gui.main_window import MainWindow` と
#   明示的に import すること。