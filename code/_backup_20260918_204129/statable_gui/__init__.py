# statable_gui package
"""\nStaTable GUI layer\n\n[v1.5 added]\n  - Keep re-exports minimal\n  - Qt-heavy modules (main_window etc.) should be\n    explicitly imported\n"""

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
#   MainWindow / StateMachineTab etc. are not re-exported.
#   Loading before creating the PySide6 QApplication causes errors, so
#   On the caller side, use `from statable_gui.main_window import MainWindow` to
#   明示的に import すること。