# statable_gui package
"""\nStaTable GUI layer\n\n[v1.5 added]\n  - Keep re-exports minimal\n  - Qt-heavy modules (main_window etc.) should be\n    explicitly imported\n"""

# Settings / environment
from .config import WINDOW_WIDTH, WINDOW_HEIGHT

# Logger (lightweight)
try:
    from .logger import StaTableLogger
except ImportError:
    StaTableLogger = None

__all__ = [
    'WINDOW_WIDTH',
    'WINDOW_HEIGHT',
    'StaTableLogger',
]

# Note:
#   MainWindow / StateMachineTab etc. are not re-exported.
#   Loading before creating the PySide6 QApplication causes errors, so
#   On the caller side, use `from statable_gui.main_window import MainWindow` to
#Explicitly import it.