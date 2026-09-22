#!/usr/bin/env python3
# code/tools/test_runner_gui.py
"""Standalone GUI runner for StaTable tests and code generation.

Not integrated into statable_gui: launch this script directly.

Features:
  - Select any subset of tests/test_v2_*.py
  - Optionally generate C code from an XML and verify it with gcc / arm
  - Sequential execution via QProcess (non-blocking)
  - Live output pane, progress bar, and PASS/FAIL summary

Usage:
    python tools/test_runner_gui.py

Requires:
    PySide6 (already a project dependency)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QProcess, QProcessEnvironment
from PySide6.QtGui import QFont, QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QCheckBox, QGroupBox, QListWidget,
    QListWidgetItem, QPlainTextEdit, QProgressBar, QFileDialog,
    QLineEdit, QSplitter, QMessageBox, QScrollArea,
)


# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
CODE_DIR = Path(__file__).resolve().parent.parent
TESTS_DIR = CODE_DIR / "tests"
TOOLS_DIR = CODE_DIR / "tools"
DEFAULT_XML = CODE_DIR / "docs" / "tutorial" / "vending_machine.xml"
DEFAULT_OUTPUT = CODE_DIR / "output_verify"


# ----------------------------------------------------------------------
# Test discovery
# ----------------------------------------------------------------------
def discover_tests() -> list[Path]:
    """Return all tests/test_v2_*.py sorted by name."""
    if not TESTS_DIR.is_dir():
        return []
    return sorted(TESTS_DIR.glob("test_v2_*.py"))


def classify_version(test_path: Path) -> str:
    """Return a coarse version bucket, e.g. '2.2', '2.3', '2.5'."""
    name = test_path.stem  # test_v2_5_p1
    parts = name.split("_")
    # test, v2, 5, p1  -> '2.5'
    if len(parts) >= 3 and parts[0] == "test" and parts[1].startswith("v"):
        major = parts[1][1:]  # '2'
        minor = parts[2]      # '5'
        return f"{major}.{minor}"
    return "other"


# ----------------------------------------------------------------------
# Main window
# ----------------------------------------------------------------------
class TestRunnerWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("StaTable Verification Runner")
        self.resize(1100, 800)

        self._queue: list[dict] = []
        self._current: dict | None = None
        self._process: QProcess | None = None
        self._stats = {"pass": 0, "fail": 0, "skip": 0}
        self._log_path: Path | None = None

        self._build_ui()
        self._populate_tests()
        self._setup_env()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # ---- Top: two side-by-side panels ----
        top_split = QSplitter(Qt.Horizontal)

        # Left: tests
        tests_box = QGroupBox("Test suites")
        tests_layout = QVBoxLayout(tests_box)

        # filter buttons
        filt = QHBoxLayout()
        for label, slot in [
            ("All", self._select_all),
            ("None", self._select_none),
            ("v2.2", lambda: self._select_version("2.2")),
            ("v2.3", lambda: self._select_version("2.3")),
            ("v2.4", lambda: self._select_version("2.4")),
            ("v2.5", lambda: self._select_version("2.5")),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(slot)
            filt.addWidget(btn)
        filt.addStretch()
        tests_layout.addLayout(filt)

        self.test_list = QListWidget()
        self.test_list.setFont(QFont("Consolas", 9))
        tests_layout.addWidget(self.test_list)

        top_split.addWidget(tests_box)

        # Right: generate + compile
        gen_box = QGroupBox("Generate & compile")
        gen_layout = QVBoxLayout(gen_box)

        # XML
        xml_row = QHBoxLayout()
        xml_row.addWidget(QLabel("XML:"))
        self.xml_edit = QLineEdit(str(DEFAULT_XML))
        xml_row.addWidget(self.xml_edit, stretch=1)
        browse_xml = QPushButton("...")
        browse_xml.clicked.connect(self._browse_xml)
        xml_row.addWidget(browse_xml)
        gen_layout.addLayout(xml_row)

        # Output dir
        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("Output:"))
        self.out_edit = QLineEdit(str(DEFAULT_OUTPUT))
        out_row.addWidget(self.out_edit, stretch=1)
        browse_out = QPushButton("...")
        browse_out.clicked.connect(self._browse_output)
        out_row.addWidget(browse_out)
        gen_layout.addLayout(out_row)

        # Compilers
        comp_row = QHBoxLayout()
        comp_row.addWidget(QLabel("Compilers:"))
        self.chk_gcc = QCheckBox("gcc")
        self.chk_gcc.setChecked(True)
        comp_row.addWidget(self.chk_gcc)
        self.chk_arm = QCheckBox("arm")
        self.chk_arm.setChecked(True)
        comp_row.addWidget(self.chk_arm)
        comp_row.addStretch()
        gen_layout.addLayout(comp_row)

        # Enable generate
        self.chk_generate = QCheckBox("Run Generate + Compile")
        self.chk_generate.setChecked(False)
        gen_layout.addWidget(self.chk_generate)

        gen_layout.addStretch()
        top_split.addWidget(gen_box)

        top_split.setSizes([600, 500])
        root.addWidget(top_split, stretch=0)

        # ---- Output pane ----
        out_box = QGroupBox("Output")
        out_layout = QVBoxLayout(out_box)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 9))
        self.output.setMaximumBlockCount(20000)
        out_layout.addWidget(self.output)
        root.addWidget(out_box, stretch=1)

        # ---- Bottom: progress + run/close ----
        bottom = QHBoxLayout()

        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setValue(0)
        bottom.addWidget(self.progress, stretch=1)

        self.summary_label = QLabel("Ready.")
        bottom.addWidget(self.summary_label)

        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._on_run)
        bottom.addWidget(self.run_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        bottom.addWidget(self.close_btn)

        root.addLayout(bottom)

    # ------------------------------------------------------------------
    # Env setup (headless Qt for tests)
    # ------------------------------------------------------------------
    def _setup_env(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        os.environ.setdefault("STATABLE_DISABLE_MERMAID", "1")
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    # ------------------------------------------------------------------
    # Test list population
    # ------------------------------------------------------------------
    def _populate_tests(self):
        self.test_list.clear()
        for t in discover_tests():
            version = classify_version(t)
            item = QListWidgetItem(f"[v{version}] {t.name}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            item.setData(Qt.UserRole, str(t))
            self.test_list.addItem(item)

    def _select_all(self):
        for i in range(self.test_list.count()):
            self.test_list.item(i).setCheckState(Qt.Checked)

    def _select_none(self):
        for i in range(self.test_list.count()):
            self.test_list.item(i).setCheckState(Qt.Unchecked)

    def _select_version(self, version: str):
        for i in range(self.test_list.count()):
            item = self.test_list.item(i)
            path = Path(item.data(Qt.UserRole))
            if classify_version(path) == version:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)

    # ------------------------------------------------------------------
    # Browse handlers
    # ------------------------------------------------------------------
    def _browse_xml(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select project XML", str(CODE_DIR), "XML (*.xml)")
        if path:
            self.xml_edit.setText(path)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select output directory", str(CODE_DIR))
        if path:
            self.out_edit.setText(path)

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------
    def _on_run(self):
        if self._current is not None or self._process is not None:
            QMessageBox.information(self, "Busy",
                                    "A run is already in progress.")
            return

        self.output.clear()
        self._stats = {"pass": 0, "fail": 0, "skip": 0}
        self.summary_label.setText("Running...")
        self.run_btn.setEnabled(False)

        # Build task queue
        self._queue = []

        for i in range(self.test_list.count()):
            item = self.test_list.item(i)
            if item.checkState() == Qt.Checked:
                path = item.data(Qt.UserRole)
                self._queue.append({
                    "kind": "test",
                    "label": f"TEST  {Path(path).name}",
                    "cmd": [sys.executable, path],
                    "cwd": str(CODE_DIR),
                })

        if self.chk_generate.isChecked():
            xml = self.xml_edit.text().strip()
            out = self.out_edit.text().strip()

            if not Path(xml).is_file():
                QMessageBox.warning(self, "XML not found",
                                    f"XML file not found:\n{xml}")
                self._queue = []
                self.run_btn.setEnabled(True)
                return

            # Remove old output directory
            try:
                import shutil
                if Path(out).exists():
                    shutil.rmtree(out)
            except Exception as e:
                self._append(f"[warn] could not clean {out}: {e}")

            self._queue.append({
                "kind": "generate",
                "label": f"GEN   {Path(xml).name} -> {Path(out).name}",
                "cmd": [sys.executable,
                        str(TOOLS_DIR / "gen_output_from_xml.py"),
                        "--xml", xml, "--out", out],
                "cwd": str(CODE_DIR),
            })

            compilers = []
            if self.chk_gcc.isChecked():
                compilers.append("gcc")
            if self.chk_arm.isChecked():
                compilers.append("arm")

            compiler_arg = "both" if len(compilers) == 2 else (
                compilers[0] if compilers else None)

            if compiler_arg is None:
                self._append("[warn] no compiler selected; "
                             "skipping verify step")
            else:
                self._queue.append({
                    "kind": "verify",
                    "label": f"VERIFY {compiler_arg}",
                    "cmd": [sys.executable,
                            str(TOOLS_DIR / "verify_c_syntax.py"),
                            "--root", out,
                            "--compiler", compiler_arg],
                    "cwd": str(CODE_DIR),
                })

        if not self._queue:
            self.summary_label.setText("Nothing selected.")
            self.run_btn.setEnabled(True)
            return

        self.progress.setMaximum(len(self._queue))
        self.progress.setValue(0)
        self._append("=" * 70)
        self._append(f"Queued {len(self._queue)} task(s)")
        self._append("=" * 70)
        self._append("")

        self._next_task()

    # ------------------------------------------------------------------
    # Sequential task execution
    # ------------------------------------------------------------------
    def _next_task(self):
        if not self._queue:
            self._finish()
            return

        self._current = self._queue.pop(0)

        self._append("")
        self._append("=" * 70)
        self._append(f">>> {self._current['label']}")
        self._append("=" * 70)

        self._process = QProcess(self)
        self._process.setWorkingDirectory(self._current["cwd"])

        # Provide env vars (tests expect offscreen)
        env = QProcessEnvironment.systemEnvironment()
        env.insert("QT_QPA_PLATFORM", "offscreen")
        env.insert("STATABLE_DISABLE_MERMAID", "1")
        env.insert("PYTHONIOENCODING", "utf-8")
        self._process.setProcessEnvironment(env)

        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.readyReadStandardError.connect(self._on_stderr)
        self._process.finished.connect(self._on_finished)

        self._process.start(self._current["cmd"][0],
                            self._current["cmd"][1:])

    def _on_stdout(self):
        if self._process is None:
            return
        data = bytes(self._process.readAllStandardOutput()).decode(
            "utf-8", errors="replace")
        self._append(data, newline=False)

    def _on_stderr(self):
        if self._process is None:
            return
        data = bytes(self._process.readAllStandardError()).decode(
            "utf-8", errors="replace")
        self._append(data, newline=False)

    def _on_finished(self, exit_code: int, _status):
        kind = self._current["kind"] if self._current else "?"

        if exit_code == 0:
            self._stats["pass"] += 1
            self._append("")
            self._append(f"<<< OK    {self._current['label']}")
        else:
            self._stats["fail"] += 1
            self._append("")
            self._append(f"<<< FAIL  {self._current['label']} "
                         f"(exit {exit_code})")

        self._process.deleteLater()
        self._process = None
        self._current = None

        self.progress.setValue(self.progress.value() + 1)
        self._next_task()

    def _finish(self):
        self._append("")
        self._append("=" * 70)
        self._append(
            f"  DONE  PASS={self._stats['pass']}  "
            f"FAIL={self._stats['fail']}")
        self._append("=" * 70)

        self.summary_label.setText(
            f"Done. PASS={self._stats['pass']} "
            f"FAIL={self._stats['fail']}")
        self.run_btn.setEnabled(True)

    # ------------------------------------------------------------------
    # Output helper
    # ------------------------------------------------------------------
    def _append(self, text: str, newline: bool = True):
        cursor = self.output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.output.setTextCursor(cursor)
        if newline and not text.endswith("\n"):
            text = text + "\n"
        self.output.insertPlainText(text)
        self.output.ensureCursorVisible()


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    win = TestRunnerWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())