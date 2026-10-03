"""Entry point for `python -m statable`.

Launches the StaTable GUI, or prints a friendly error if the
GUI extras are not installed.

    pip install statable[gui]    # to enable GUI
    python -m statable           # launch
"""
from __future__ import annotations

import sys


def run_smoke_test() -> int:
    """Headless smoke test for frozen EXE packaging verification."""
    import os
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["STATABLE_DISABLE_MERMAID"] = "1"

    try:
        from PySide6.QtWidgets import QApplication, QFileDialog
    except ImportError:
        return 1

    # Patch dialogs: no user to interact in headless mode
    QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: ("", ""))
    QFileDialog.getSaveFileName = staticmethod(lambda *a, **k: ("", ""))
    QFileDialog.getExistingDirectory = staticmethod(lambda *a, **k: "")

    try:
        app = QApplication.instance() or QApplication(sys.argv)
    except Exception:
        return 4

    try:
        from statable_gui.main_window import MainWindow
        window = MainWindow()
    except Exception as e:
        sys.stderr.write(f"MainWindow failed: {e!r}\n")
        return 2

    # v3.2.2 regression scenario
    try:
        window.open_project(False)
        window.open_project(True)
    except Exception as e:
        sys.stderr.write(f"open_project failed: {e!r}\n")
        return 3

    try:
        window.close()
        app.processEvents()
    except Exception:
        pass

    return 0

def main() -> int:
    if "--smoke-test" in sys.argv:
        return run_smoke_test()

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
