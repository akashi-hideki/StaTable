"""Entry point for `python -m statable`.

Launches the StaTable GUI, or prints a friendly error if the
GUI extras are not installed.

    pip install statable[gui]    # to enable GUI
    python -m statable           # launch
"""
from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        sys.stderr.write(
            "error: The StaTable GUI requires PySide6.\n"
            "       Install with:  pip install \"statable[gui]\"\n"
            "       For CLI-only usage:  statable-cli --help\n"
        )
        return 1

    try:
        from statable_gui.main_window import MainWindow
    except ImportError as exc:
        sys.stderr.write(
            f"error: Failed to import GUI module: {exc}\n"
            "       The GUI files may be missing from the install.\n"
        )
        return 1

    app = QApplication(sys.argv)

    # [v3.1] Apply saved language preference (en / zh_CN)
    try:
        from statable_gui.i18n import install_translator
        install_translator(app)
    except Exception:
        pass  # i18n is optional; fall back to English

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
