# eclipse_installer/gui.py
"""[Eclipse Installer] PySide6 GUI."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton, QFileDialog,
    QCheckBox, QComboBox, QTextEdit, QDialogButtonBox, QMessageBox,
    QProgressDialog,
)

from .core import InstallOptions, install


def _preload_codegen_modules():
    """Pre-import codegen modules at app startup (frozen EXE is slow)."""
    try:
        from statable import xml_io  # noqa
        from codegen import c_code_generator  # noqa
        from codegen import config  # noqa
        from codegen.comm_monitor import config as _cm_cfg  # noqa
        from codegen.comm_monitor import generator as _cm_gen  # noqa
        from codegen.comm_monitor import registry as _cm_reg  # noqa
        from codegen.comm_monitor import templates as _cm_tpl  # noqa
    except Exception:
        pass


class _InstallWorker(QThread):
    """Run install() in a worker thread so the GUI stays responsive."""
    finished_ok = Signal(object)

    def __init__(self, opts):
        super().__init__()
        self._opts = opts

    def run(self):
        import tempfile, time, traceback
        from pathlib import Path as _P
        log_path = _P(tempfile.gettempdir()) / "eclipse_installer_debug.log"
        def _dbg(msg):
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
            except Exception:
                pass

        _dbg("worker.run() ENTER")
        from .core import install, InstallResult
        try:
            _dbg(f"calling install(opts) xml={self._opts.xml_path} "
                 f"cm={self._opts.with_comm_monitor} "
                 f"out={self._opts.output_dir}")
            res = install(self._opts)
            _dbg(f"install() returned: installed={len(res.installed)} "
                 f"skipped={len(res.skipped)} errors={len(res.errors)}")
        except Exception as e:
            _dbg(f"EXCEPTION: {e!r}")
            _dbg(traceback.format_exc())
            res = InstallResult()
            res.errors.append((self._opts.project_root,
                               f"unhandled exception: {e}"))
        _dbg("emitting finished_ok")
        self.finished_ok.emit(res)
        _dbg("worker.run() EXIT")


class InstallDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("StaTable Eclipse Installer")
        self.setMinimumWidth(720)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        # --- Paths ---
        paths = QGroupBox("Paths")
        f = QFormLayout(paths)

        self.ed_project = QLineEdit()
        b1 = QPushButton("Browse...")
        b1.clicked.connect(self._pick_project)
        row1 = QHBoxLayout(); row1.addWidget(self.ed_project); row1.addWidget(b1)
        f.addRow("Eclipse project root:", row1)

        self.ed_xml = QLineEdit()
        self.ed_xml.setPlaceholderText(
            "(optional) StaTable XML -> auto-generate C code")
        bxml = QPushButton("Browse...")
        bxml.clicked.connect(self._pick_xml)
        rowxml = QHBoxLayout(); rowxml.addWidget(self.ed_xml); rowxml.addWidget(bxml)
        f.addRow("XML (optional):", rowxml)

        self.cb_comm_mode = QComboBox()
        self.cb_comm_mode.addItem(
            "Auto (follow XML comm_monitor_enabled)", "auto")
        self.cb_comm_mode.addItem("Force ON (override XML)", "on")
        self.cb_comm_mode.addItem("Force OFF (override XML)", "off")
        f.addRow("comm_monitor:", self.cb_comm_mode)

        self.ed_output = QLineEdit()
        b2 = QPushButton("Browse...")
        b2.clicked.connect(self._pick_output)
        row2 = QHBoxLayout(); row2.addWidget(self.ed_output); row2.addWidget(b2)
        f.addRow("StaTable output/ dir:", row2)

        self.ed_subdir = QLineEdit("src/statable_generated")
        f.addRow("Install generated code to:", self.ed_subdir)

        root.addWidget(paths)

        # --- Scaffolding options ---
        opts = QGroupBox("Scaffolding files")
        v = QVBoxLayout(opts)
        self.cb_startup   = QCheckBox("startup_stm32f405.s")
        self.cb_linker    = QCheckBox("linker_stm32f405.ld")
        self.cb_syscalls  = QCheckBox("syscalls.c (printf -> USART2)")
        self.cb_main      = QCheckBox("main.c (demo entry)")
        self.cb_makefile  = QCheckBox("Makefile (arm-none-eabi-gcc)")
        self.cb_eclipse   = QCheckBox(".project / .cproject (Eclipse CDT)")
        self.cb_samples   = QCheckBox("samples/*.xml (optional)")
        for cb in (self.cb_startup, self.cb_linker, self.cb_syscalls,
                   self.cb_main, self.cb_makefile, self.cb_eclipse):
            cb.setChecked(True)
            v.addWidget(cb)
        v.addWidget(self.cb_samples)
        root.addWidget(opts)

        # --- Safety ---
        safety = QGroupBox("Safety")
        vs = QVBoxLayout(safety)
        self.cb_overwrite_gen = QCheckBox(
            "Overwrite generated C code (under install subdir)")
        self.cb_overwrite_gen.setChecked(True)
        self.cb_overwrite_scaff = QCheckBox(
            "Overwrite existing scaffolding files (root-level)")
        self.cb_overwrite_scaff.setChecked(False)
        vs.addWidget(self.cb_overwrite_gen)
        vs.addWidget(self.cb_overwrite_scaff)
        root.addWidget(safety)

        # --- Log ---
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(160)
        root.addWidget(QLabel("Log:"))
        root.addWidget(self.log)

        # --- Buttons ---
        btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Install")
        btns.accepted.connect(self._on_install)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    # ---- slots ----
    def _pick_project(self) -> None:
        d = QFileDialog.getExistingDirectory(
            self, "Select Eclipse project root")
        if d:
            self.ed_project.setText(d)

    def _pick_xml(self) -> None:
        f, _ = QFileDialog.getOpenFileName(
            self, "Select StaTable XML", "",
            "XML files (*.xml);;All files (*)")
        if f:
            self.ed_xml.setText(f)

    def _pick_output(self) -> None:
        d = QFileDialog.getExistingDirectory(
            self, "Select StaTable output directory")
        if d:
            self.ed_output.setText(d)

    def _log(self, msg: str) -> None:
        self.log.append(msg)

    def _validate_output_dir(self, out: str):
        import sys
        try:
            out_resolved = Path(out).resolve()
        except Exception:
            return None
        if getattr(sys, 'frozen', False):
            exe_dir = Path(sys.executable).resolve().parent
            if out_resolved == exe_dir or exe_dir in out_resolved.parents:
                return (
                    "Output directory must NOT be the installer's own folder "
                    "(would corrupt _internal).\n"
                    f"Refused: {out_resolved}"
                )
        return None

    def _on_install(self) -> None:
        proj = self.ed_project.text().strip()
        out = self.ed_output.text().strip()
        sub = self.ed_subdir.text().strip() or "src/statable_generated"
        xml = self.ed_xml.text().strip()
        mode = self.cb_comm_mode.currentData()

        if not proj or not Path(proj).is_dir():
            QMessageBox.warning(self, "Error", "Project root is invalid.")
            return
        if not out:
            QMessageBox.warning(self, "Error", "Output dir is not set.")
            return
        if not xml and not Path(out).is_dir():
            QMessageBox.warning(self, "Error", "Output dir does not exist.")
            return
        if xml and not Path(xml).is_file():
            QMessageBox.warning(self, "Error", f"XML not found: {xml}")
            return

        err = self._validate_output_dir(out)
        if err:
            QMessageBox.warning(self, "Error", err)
            return

        opts = InstallOptions(
            project_root=Path(proj),
            output_dir=Path(out),
            generated_subdir=sub,
            with_startup=self.cb_startup.isChecked(),
            with_linker=self.cb_linker.isChecked(),
            with_syscalls=self.cb_syscalls.isChecked(),
            with_main=self.cb_main.isChecked(),
            with_makefile=self.cb_makefile.isChecked(),
            with_eclipse_project=self.cb_eclipse.isChecked(),
            with_samples=self.cb_samples.isChecked(),
            overwrite_generated=self.cb_overwrite_gen.isChecked(),
            overwrite_scaffolding=self.cb_overwrite_scaff.isChecked(),
            xml_path=Path(xml) if xml else None,
            with_comm_monitor=(None if mode == "auto" else (mode == "on")),
        )

        self._log("--- install start ---")
        if xml:
            self._log(f"  XML: {xml}  mode={mode}")
        self._log(f"  project: {proj}")
        self._log(f"  output : {out}")

        self._progress = QProgressDialog(
            "Generating C code and installing...", None, 0, 0, self)
        self._progress.setWindowTitle("Install")
        self._progress.setWindowModality(Qt.WindowModal)
        self._progress.setCancelButton(None)
        self._progress.setMinimumDuration(0)
        self._progress.setValue(0)
        self._progress.show()

        self._worker = _InstallWorker(opts)
        self._worker.finished_ok.connect(self._on_install_finished)
        self._worker.start()

    def _on_install_finished(self, res) -> None:
        try:
            self._progress.close()
        except Exception:
            pass

        for pth in res.installed:
            self._log(f"[OK]      {pth}")
        for pth in res.skipped:
            self._log(f"[SKIP]    {pth}")
        for pth, msg in res.errors:
            self._log(f"[ERROR]   {pth}: {msg}")
        for w in res.warnings:
            self._log(f"[WARN]    {w}")

        summary = (
            f"Installed: {len(res.installed)}\n"
            f"Skipped:   {len(res.skipped)}\n"
            f"Errors:    {len(res.errors)}"
        )
        self._log("--- summary ---")
        self._log(summary)

        if res.errors:
            QMessageBox.warning(self, "Completed with errors", summary)
        else:
            QMessageBox.information(self, "Install complete", summary)



def main() -> int:
    # [v3.6.0] guard: pytest may leave QT_QPA_PLATFORM=offscreen in the
    # parent shell; clear it so the GUI renders on the visible desktop.
    import os
    if os.environ.get('QT_QPA_PLATFORM') == 'offscreen':
        del os.environ['QT_QPA_PLATFORM']
        sys.stderr.write('[eclipse-installer] cleared QT_QPA_PLATFORM=offscreen\n')

    app = QApplication.instance() or QApplication(sys.argv)
    dlg = InstallDialog()
    dlg.show()

    # [v3.6.0] preload codegen modules in background so the first Install
    # does not stall on frozen-EXE lazy import.
    from PySide6.QtCore import QTimer
    QTimer.singleShot(100, _preload_codegen_modules)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
