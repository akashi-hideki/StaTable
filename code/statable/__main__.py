"""Allow `python -m statable` to launch the StaTable GUI.

This provides a friendlier entry point:
    python -m statable

Equivalent to:
    python gui_main.py
"""

import sys
from PySide6.QtWidgets import QApplication
from statable_gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())