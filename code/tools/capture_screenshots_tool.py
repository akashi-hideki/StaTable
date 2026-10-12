# tools/capture_screenshots_tool.py
r"""Manual screenshot tool for WeChat promotion.

A small always-on-top floating window. Click [Capture] to
snapshot the entire screen (the tool hides itself first).

Output: wechat_screenshots/screenshot_NN.png (auto-numbered)

Usage:
    python tools/capture_screenshots_tool.py

Cleanup (after WeChat publication):
    Remove-Item tools\capture_screenshots_tool.py
    Remove-Item -Recurse ..\wechat_screenshots
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CODE_DIR))

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
    QWidget,
)

OUT_DIR = CODE_DIR.parent / "wechat_screenshots"
OUT_DIR.mkdir(exist_ok=True)


class CaptureTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Capture (WeChat)")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setFixedSize(260, 130)
        self.counter = 0
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.lbl = QLabel(f"Output: {OUT_DIR.name}/")
        self.lbl.setStyleSheet("font-size: 10px; color: #666;")
        layout.addWidget(self.lbl)

        self.status = QLabel("Ready.")
        self.status.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.status)

        row = QHBoxLayout()
        self.btn_cap = QPushButton("Capture")
        self.btn_cap.clicked.connect(self.on_capture)
        row.addWidget(self.btn_cap)

        self.btn_open = QPushButton("Open")
        self.btn_open.clicked.connect(self.on_open)
        row.addWidget(self.btn_open)

        self.btn_quit = QPushButton("Quit")
        self.btn_quit.clicked.connect(self._quit)
        row.addWidget(self.btn_quit)
        layout.addLayout(row)

    def on_capture(self):
        self.status.setText("Capturing in 300 ms...")
        self.btn_cap.setEnabled(False)
        QTimer.singleShot(300, self._do_capture)

    def _do_capture(self):
        self.hide()
        QTimer.singleShot(200, self._grab)

    def _grab(self):
        screen = QGuiApplication.primaryScreen()
        pixmap = screen.grabWindow(0)
        self.counter += 1
        out = OUT_DIR / f"screenshot_{self.counter:02d}.png"
        pixmap.save(str(out), "PNG")
        print(f"[CAP] {out}  ({pixmap.width()}x{pixmap.height()})")
        self.status.setText(f"Saved: {out.name}")
        self.show()
        self.raise_()
        self.activateWindow()
        self.btn_cap.setEnabled(True)

    def _quit(self):
        QApplication.instance().quit()

    def closeEvent(self, event):
        QApplication.instance().quit()
        event.accept()

    def on_open(self):
        os.startfile(str(OUT_DIR))


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    tool = CaptureTool()
    screen = QGuiApplication.primaryScreen().availableGeometry()
    tool.move(screen.right() - tool.width() - 20, screen.top() + 20)
    tool.show()
    print(f"[INFO] output: {OUT_DIR}")
    print("[INFO] Click [Capture] at the moment you want to snapshot.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
