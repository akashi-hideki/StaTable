# tools/capture_gui_screenshots.py
"""Capture StaTable GUI screenshots for WeChat promotion.

Usage:
    python tools/capture_gui_screenshots.py

Output:
    wechat_screenshots/*.png
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "windows")

CODE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CODE_DIR))

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

OUT_DIR = CODE_DIR.parent / "wechat_screenshots"
OUT_DIR.mkdir(exist_ok=True)


def _wait(ms: int) -> None:
    """Process events for ms milliseconds (keeps GUI responsive)."""
    loop_until = time.monotonic() + ms / 1000.0
    while time.monotonic() < loop_until:
        QApplication.processEvents()
        time.sleep(0.05)


def capture(name: str) -> Path:
    """Grab the entire primary screen."""
    screen = QGuiApplication.primaryScreen()
    pixmap = screen.grabWindow(0)
    out = OUT_DIR / f"{name}.png"
    pixmap.save(str(out), "PNG")
    print(f"[CAP] {out}  ({pixmap.width()}x{pixmap.height()})")
    return out

def capture_main_window():
    from statable_gui.main_window import MainWindow

    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.resize(1400, 900)

    # Wait for window to fully render
    _wait(2000)

    # Capture the empty / default state
    capture("01_main_default")

    # Load sample project (CookingHeaterController)
    sample_xml = CODE_DIR / "docs" / "samples" / "cooking_heater_controller.xml"
    if sample_xml.exists():
        print(f"[INFO] loading sample: {sample_xml}")
        window.open_project(filepath=str(sample_xml))
        # Wait for Mermaid WebEngine to render
        _wait(6000)
        capture("02_project_loaded")

        # Switch to a Mermaid-heavy tab (Application or a Driver tab)
        try:
            # Try to switch to the second tab if available
            if hasattr(window, "tabs") and window.tabs.count() > 1:
                window.tabs.setCurrentIndex(1)
                _wait(3000)
                capture("03_driver_tab")
        except Exception as e:
            print(f"[WARN] tab switch failed: {e}")

    window.close()
    _wait(500)

def capture_code_gen_dialog():
    from statable_gui.main_window import MainWindow
    app = QApplication.instance() or QApplication(sys.argv)

    window = MainWindow()
    window.show()
    window.resize(1400, 900)
    _wait(2000)

    sample_xml = CODE_DIR / "docs" / "samples" / "cooking_heater_controller.xml"
    if sample_xml.exists():
        window.open_project(filepath=str(sample_xml))
        _wait(4000)

    # Open the code generation dialog
    try:
        window.open_code_generation_dialog()
        _wait(2500)
        capture("04_code_gen_dialog")
    except Exception as e:
        print(f"[WARN] code gen dialog failed: {e}")

    window.close()
    _wait(500)


def main():
    print(f"[INFO] output: {OUT_DIR}")
    capture_main_window()
    capture_code_gen_dialog()
    print("[DONE] all screenshots saved")


if __name__ == "__main__":
    main()
