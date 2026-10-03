#!/usr/bin/env python3
"""
StaTable Release Helper - PySide6 GUI

Release workflow automation:
- PyPI API token management (load/save/test)
- Clean build (dist/, build/, *.egg-info/)
- Version consistency check + sensitive file scan + twine check
- Upload to PyPI / TestPyPI
- Full release (build -> verify -> upload) with one click

Requirements:
    pip install PySide6 build twine

Usage:
    python tools/release_helper.py
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tarfile
import zipfile
from datetime import datetime
from pathlib import Path

try:
    from PySide6.QtCore import Qt, QThread, Signal, QTimer
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import (
        QApplication, QCheckBox, QFileDialog, QFormLayout, QGroupBox,
        QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
        QMainWindow, QMessageBox, QPlainTextEdit, QPushButton,
        QRadioButton, QSplitter, QStatusBar, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget, QButtonGroup
    )
except ImportError:
    print("ERROR: PySide6 is required. Install with: pip install PySide6")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SENSITIVE_PATTERNS = [
    "apitoken", "recovery-codes", "pypirc", "pypi-token",
    "github-recovery", ".env", "credential", "secret", "password",
]

DEFAULT_TOKEN_PATH_WIN = r"C:\secure_statable\pypi-apitoken.txt"
DEFAULT_TOKEN_PATH_UNIX = "~/.secure_statable/pypi-apitoken.txt"

PYPI_URL = "https://upload.pypi.org/legacy/"
TESTPYPI_URL = "https://test.pypi.org/legacy/"


# ---------------------------------------------------------------------------
# Worker thread
# ---------------------------------------------------------------------------

class CommandWorker(QThread):
    """Run a subprocess and emit its output line by line."""
    line = Signal(str, str)   # (level, text)
    done = Signal(bool, str)  # (success, summary)

    def __init__(self, cmd, cwd=None, env=None, label="", parent=None):
        super().__init__(parent)
        self.cmd = [str(c) for c in cmd]
        self.cwd = cwd
        self.env = env
        self.label = label
        self._proc = None

    def run(self):
        try:
            self.line.emit("cmd", "$ " + " ".join(self.cmd))
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            # Force UTF-8 output from subprocesses to avoid CP932 mojibake
            _env = (self.env or os.environ).copy()
            _env["PYTHONIOENCODING"] = "utf-8"
            _env["PYTHONUTF8"] = "1"
            self._proc = subprocess.Popen(
                self.cmd,
                cwd=self.cwd,
                env=_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                shell=False,
                creationflags=creationflags,
            )
            for line in iter(self._proc.stdout.readline, ""):
                self.line.emit("info", line.rstrip("\r\n"))
            self._proc.stdout.close()
            code = self._proc.wait()
            self._proc = None
            if code == 0:
                self.line.emit("ok", f"[{self.label}] 成功")
                self.done.emit(True, self.label)
            else:
                self.line.emit("fail", f"[{self.label}] 失敗 (exit={code})")
                self.done.emit(False, f"{self.label} (exit={code})")
        except Exception as e:
            self.line.emit("fail", f"[{self.label}] 例外: {e}")
            self.done.emit(False, f"{self.label}: {e}")

    def terminate(self):
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.kill()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class ReleaseHelper(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StaTable Release Helper")
        self.resize(1050, 780)

        self._workers: list[CommandWorker] = []
        self._repo_root: Path | None = None
        self._code_dir: Path | None = None
        self._config_path = Path.home() / ".statable_release_helper.json"
        self._config = self._load_config()
        self._full_release_stage: str | None = None

        self._detect_paths()
        self._build_ui()
        self._refresh_dist_list()
        self._check_deps()

    # -- config ------------------------------------------------------------

    def _load_config(self) -> dict:
        try:
            if self._config_path.exists():
                return json.loads(self._config_path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _save_config(self):
        try:
            self._config["token_path"] = self.token_path_edit.text()
            self._config_path.write_text(
                json.dumps(self._config, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            self._log("warn", f"設定保存失敗: {e}")

    # -- path detection ----------------------------------------------------

    def _detect_paths(self):
        here = Path(__file__).resolve()
        candidates = [
            here.parent.parent.parent,  # <repo>/code/tools/x.py -> <repo>
            Path.cwd(),
            Path.cwd().parent,
        ]
        for c in candidates:
            if (c / "code" / "pyproject.toml").exists():
                self._repo_root = c
                self._code_dir = c / "code"
                return
            if (c / "pyproject.toml").exists():
                self._code_dir = c
                self._repo_root = c.parent
                return

    # -- UI construction ---------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)

        # Header
        header = QLabel("<b>StaTable Release Helper</b>")
        header.setStyleSheet("font-size: 14pt; padding: 2px 6px;")
        root.addWidget(header)

        # Path indicator
        if self._code_dir:
            path_text = f"repo: {self._repo_root} | code: {self._code_dir}"
        else:
            path_text = "(リポジトリが見つかりません)"
        self.path_label = QLabel(path_text)
        self.path_label.setStyleSheet("color: #666; padding: 2px 6px; font-size: 9pt;")
        self.path_label.setWordWrap(True)
        root.addWidget(self.path_label)

        # Splitter: tabs + log
        splitter = QSplitter(Qt.Vertical)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_settings(), "設定")
        self.tabs.addTab(self._tab_build(), "ビルド")
        self.tabs.addTab(self._tab_verify(), "検証")
        self.tabs.addTab(self._tab_upload(), "アップロード")
        self.tabs.addTab(self._tab_full_release(), "フルリリース")
        splitter.addWidget(self.tabs)

        # Log
        log_group = QGroupBox("ログ")
        log_v = QVBoxLayout(log_group)
        log_v.setContentsMargins(6, 6, 6, 6)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 9))
        self.log_view.setStyleSheet("background-color: #fafafa; border: 1px solid #ddd;")
        log_v.addWidget(self.log_view)

        log_btns = QHBoxLayout()
        log_btns.addStretch()
        btn_clear = QPushButton("ログをクリア")
        btn_clear.clicked.connect(self.log_view.clear)
        log_btns.addWidget(btn_clear)
        log_v.addLayout(log_btns)

        splitter.addWidget(log_group)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter, stretch=1)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

    def _wrap(self, layout):
        w = QWidget()
        w.setLayout(layout)
        return w

    # -- tabs --------------------------------------------------------------

    def _tab_settings(self):
        w = QWidget()
        v = QVBoxLayout(w)

        # Token group
        gb = QGroupBox("PyPI API トークン")
        f = QFormLayout(gb)

        default_path = (DEFAULT_TOKEN_PATH_WIN if os.name == "nt"
                        else str(Path(DEFAULT_TOKEN_PATH_UNIX).expanduser()))
        self.token_path_edit = QLineEdit(self._config.get("token_path", default_path))
        btn_browse = QPushButton("参照...")
        btn_browse.clicked.connect(lambda: self._browse_file(self.token_path_edit))
        row = QHBoxLayout()
        row.addWidget(self.token_path_edit, stretch=1)
        row.addWidget(btn_browse)
        f.addRow("トークンファイル:", self._wrap(row))

        self.token_edit = QLineEdit()
        self.token_edit.setEchoMode(QLineEdit.Password)
        self.token_edit.setPlaceholderText("pypi-...")
        f.addRow("トークン:", self.token_edit)

        btns = QHBoxLayout()
        self.btn_load_token = QPushButton("読込")
        self.btn_load_token.clicked.connect(self._on_load_token)
        btns.addWidget(self.btn_load_token)

        self.btn_save_token = QPushButton("保存")
        self.btn_save_token.clicked.connect(self._on_save_token)
        btns.addWidget(self.btn_save_token)

        self.btn_show_token = QPushButton("表示")
        self.btn_show_token.setCheckable(True)
        self.btn_show_token.toggled.connect(self._on_toggle_show_token)
        btns.addWidget(self.btn_show_token)

        self.btn_test_token = QPushButton("テスト")
        self.btn_test_token.clicked.connect(self._on_test_token)
        btns.addWidget(self.btn_test_token)

        btns.addStretch()
        f.addRow("", self._wrap(btns))
        v.addWidget(gb)

        # TestPyPI token group (optional)
        gb2 = QGroupBox("TestPyPI トークン（任意）")
        f2 = QFormLayout(gb2)
        self.testpypi_token_edit = QLineEdit()
        self.testpypi_token_edit.setEchoMode(QLineEdit.Password)
        self.testpypi_token_edit.setPlaceholderText("pypi-... (TestPyPI 用)")
        f2.addRow("トークン:", self.testpypi_token_edit)
        v.addWidget(gb2)

        v.addStretch()
        return w

    def _tab_build(self):
        w = QWidget()
        v = QVBoxLayout(w)

        gb = QGroupBox("ビルド設定")
        f = QFormLayout(gb)
        dir_text = str(self._code_dir) if self._code_dir else "(未検出)"
        lbl = QLabel(dir_text)
        lbl.setStyleSheet("color: #333;")
        f.addRow("作業ディレクトリ:", lbl)

        self.cb_clean_dist = QCheckBox("dist/ を削除")
        self.cb_clean_dist.setChecked(True)
        f.addRow("", self.cb_clean_dist)

        self.cb_clean_build = QCheckBox("build/ を削除")
        self.cb_clean_build.setChecked(True)
        f.addRow("", self.cb_clean_build)

        self.cb_clean_egg = QCheckBox("*.egg-info/ を削除")
        self.cb_clean_egg.setChecked(True)
        f.addRow("", self.cb_clean_egg)
        v.addWidget(gb)

        row = QHBoxLayout()
        self.btn_build = QPushButton("ビルド実行")
        self.btn_build.setMinimumHeight(32)
        self.btn_build.clicked.connect(self._on_build)
        row.addWidget(self.btn_build)

        self.btn_refresh_dist = QPushButton("dist/ を更新")
        self.btn_refresh_dist.clicked.connect(self._refresh_dist_list)
        row.addWidget(self.btn_refresh_dist)
        row.addStretch()
        v.addLayout(row)

        gb2 = QGroupBox("dist/ の生成物")
        v2 = QVBoxLayout(gb2)
        self.dist_list = QListWidget()
        v2.addWidget(self.dist_list)
        v.addWidget(gb2, stretch=1)
        return w

    def _tab_verify(self):
        w = QWidget()
        v = QVBoxLayout(w)

        gb = QGroupBox("検証項目")
        f = QFormLayout(gb)
        self.cb_twine_check = QCheckBox("twine check を実行")
        self.cb_twine_check.setChecked(True)
        f.addRow("", self.cb_twine_check)

        self.cb_sensitive_scan = QCheckBox("機密ファイルの混入チェック")
        self.cb_sensitive_scan.setChecked(True)
        f.addRow("", self.cb_sensitive_scan)

        self.cb_version_check = QCheckBox("バージョン整合性チェック")
        self.cb_version_check.setChecked(True)
        f.addRow("", self.cb_version_check)
        v.addWidget(gb)

        row = QHBoxLayout()
        self.btn_verify = QPushButton("検証実行")
        self.btn_verify.setMinimumHeight(32)
        self.btn_verify.clicked.connect(self._on_verify)
        row.addWidget(self.btn_verify)
        row.addStretch()
        v.addLayout(row)

        gb2 = QGroupBox("検証結果")
        v2 = QVBoxLayout(gb2)
        self.verify_results = QListWidget()
        v2.addWidget(self.verify_results)
        v.addWidget(gb2, stretch=1)
        return w

    def _tab_upload(self):
        w = QWidget()
        v = QVBoxLayout(w)

        gb = QGroupBox("アップロード先")
        vv = QVBoxLayout(gb)
        self.rb_pypi = QRadioButton(f"本番 PyPI ({PYPI_URL})")
        self.rb_pypi.setChecked(True)
        self.rb_testpypi = QRadioButton(f"TestPyPI ({TESTPYPI_URL})")
        self._upload_target_group = QButtonGroup(self)
        self._upload_target_group.addButton(self.rb_pypi)
        self._upload_target_group.addButton(self.rb_testpypi)
        vv.addWidget(self.rb_pypi)
        vv.addWidget(self.rb_testpypi)
        v.addWidget(gb)

        gb2 = QGroupBox("アップロード対象（dist/ の中身）")
        v2 = QVBoxLayout(gb2)
        self.upload_list = QListWidget()
        v2.addWidget(self.upload_list)
        v.addWidget(gb2, stretch=1)

        row = QHBoxLayout()
        self.btn_upload = QPushButton("アップロード実行")
        self.btn_upload.setMinimumHeight(32)
        self.btn_upload.clicked.connect(self._on_upload)
        row.addWidget(self.btn_upload)

        self.btn_refresh_upload = QPushButton("リスト更新")
        self.btn_refresh_upload.clicked.connect(self._refresh_dist_list)
        row.addWidget(self.btn_refresh_upload)
        row.addStretch()
        v.addLayout(row)
        return w

    def _tab_full_release(self):
        w = QWidget()
        v = QVBoxLayout(w)

        info = QLabel(
            "このタブは以下を一括実行します：\n"
            "  1. クリーンビルド（dist / build / egg-info 削除 → build）\n"
            "  2. 検証（バージョン整合性 / 機密ファイル / twine check）\n"
            "  3. アップロード（PyPI or TestPyPI）\n\n"
            "※ アップロード先は「アップロード」タブの選択に従います"
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            "padding: 10px; background: #eef4ff; "
            "border: 1px solid #cce; border-radius: 4px;"
        )
        v.addWidget(info)

        v.addStretch()

        row = QHBoxLayout()
        row.addStretch()
        self.btn_full_release = QPushButton("フルリリース実行")
        self.btn_full_release.setMinimumHeight(46)
        self.btn_full_release.setStyleSheet(
            "font-size: 13pt; font-weight: bold; background: #2a8; "
            "color: white; border-radius: 6px; padding: 8px 28px;"
        )
        self.btn_full_release.clicked.connect(self._on_full_release)
        row.addWidget(self.btn_full_release)
        row.addStretch()
        v.addLayout(row)

        v.addStretch()
        return w

    # -- logging / status --------------------------------------------------

    def _log(self, level: str, msg: str):
        colors = {
            "info": "#333", "ok": "#0a7a0a", "fail": "#c00",
            "warn": "#c80", "cmd": "#06c", "head": "#004",
        }
        icons = {
            "info": "", "ok": "✓", "fail": "✗",
            "warn": "⚠", "cmd": "$", "head": "▶",
        }
        color = colors.get(level, "#333")
        icon = icons.get(level, "")
        safe = (msg.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;"))
        ts = datetime.now().strftime("%H:%M:%S")
        html = (f'<span style="color:#999;">[{ts}]</span> '
                f'<span style="color:{color};">{icon} {safe}</span>')
        self.log_view.append(html)
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _set_status(self, text: str):
        self.status.showMessage(text)

    def _set_busy(self, busy: bool):
        state = not busy
        for btn in (
            self.btn_build, self.btn_verify, self.btn_upload,
            self.btn_full_release, self.btn_test_token,
            self.btn_refresh_dist, self.btn_refresh_upload,
        ):
            btn.setEnabled(state)

    # -- command runner ----------------------------------------------------

    def _run(self, cmd, cwd=None, env=None, label="", on_done=None):
        if self._workers:
            QMessageBox.warning(self, "実行中", "別のタスクが実行中です")
            return
        worker = CommandWorker(cmd, cwd=cwd, env=env, label=label, parent=self)
        worker.line.connect(self._log)

        def _finish(ok, msg):
            if worker in self._workers:
                self._workers.remove(worker)
            self._set_busy(False)
            self._set_status("Ready" if ok else f"エラー: {msg}")
            if on_done:
                on_done(ok)

        worker.done.connect(_finish)
        self._workers.append(worker)
        self._set_busy(True)
        self._set_status(f"実行中: {label}")
        worker.start()

    # -- helpers -----------------------------------------------------------

    def _browse_file(self, line_edit: QLineEdit):
        p, _ = QFileDialog.getOpenFileName(self, "ファイルを選択")
        if p:
            line_edit.setText(p)

    @staticmethod
    def _remove_dir(path: Path):
        if not path.exists():
            return
        if path.is_dir():
            import shutil
            shutil.rmtree(path, ignore_errors=True)
        else:
            try:
                path.unlink()
            except Exception:
                pass

    def _refresh_dist_list(self):
        self.dist_list.clear()
        self.upload_list.clear()
        if not self._code_dir:
            return
        dist = self._code_dir / "dist"
        if not dist.exists():
            return
        for f in sorted(dist.iterdir()):
            if f.is_file():
                size_kb = f.stat().st_size / 1024
                text = f"{f.name}  ({size_kb:.1f} KiB)"
                self.dist_list.addItem(QListWidgetItem(text))
                self.upload_list.addItem(QListWidgetItem(text))

    def _add_verify_result(self, ok: bool, text: str):
        icon = "✓" if ok else "✗"
        item = QListWidgetItem(f"{icon} {text}")
        if ok:
            item.setForeground(Qt.darkGreen)
        else:
            item.setForeground(Qt.red)
        self.verify_results.addItem(item)

    def _check_deps(self):
        """Check build / twine availability at startup."""
        missing = []
        for mod in ("build", "twine"):
            try:
                __import__(mod)
            except ImportError:
                missing.append(mod)
        if missing:
            self._log("warn", f"未インストール: {', '.join(missing)}  →  pip install {' '.join(missing)}")
        else:
            self._log("info", "依存パッケージ OK (build, twine)")

    # -- token handlers ----------------------------------------------------

    def _on_load_token(self):
        p = Path(self.token_path_edit.text()).expanduser()
        if not p.exists():
            QMessageBox.warning(self, "エラー", f"ファイルが存在しません:\n{p}")
            return
        try:
            text = p.read_text(encoding="utf-8").strip()
            self.token_edit.setText(text)
            self._log("ok", f"トークン読込完了 ({len(text)} 文字)")
        except Exception as e:
            QMessageBox.critical(self, "エラー", str(e))

    def _on_save_token(self):
        p = Path(self.token_path_edit.text()).expanduser()
        token = self.token_edit.text().strip()
        if not token:
            QMessageBox.warning(self, "エラー", "トークンが空です")
            return
        if not token.startswith("pypi-"):
            r = QMessageBox.question(
                self, "確認",
                "トークンが 'pypi-' で始まっていません。保存しますか？",
                QMessageBox.Yes | QMessageBox.No,
            )
            if r != QMessageBox.Yes:
                return
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(token, encoding="utf-8")
            self._log("ok", f"トークン保存完了: {p}")
        except Exception as e:
            QMessageBox.critical(self, "エラー", str(e))

    def _on_toggle_show_token(self, checked: bool):
        self.token_edit.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password
        )

    def _on_test_token(self):
        if not self._code_dir:
            QMessageBox.warning(self, "エラー", "code/ が見つかりません")
            return
        token = self.token_edit.text().strip()
        if not token:
            QMessageBox.warning(self, "エラー", "トークンが空です")
            return
        dist = self._code_dir / "dist"
        if not dist.exists() or not any(dist.iterdir()):
            QMessageBox.warning(
                self, "エラー",
                "dist/ が空です。\nトークンのテストには、既存パッケージが必要です。"
            )
            return

        env = os.environ.copy()
        env["TWINE_USERNAME"] = "__token__"
        env["TWINE_PASSWORD"] = token
        files = [str(p) for p in dist.iterdir() if p.is_file()]
        cmd = [sys.executable, "-m", "twine", "upload",
               "--skip-existing", "--repository-url", PYPI_URL] + files
        self._log("head", "=== トークン認証テスト ===")
        self._log("info", "『Skipping ... already exists』が出れば認証成功です")
        self._run(cmd, cwd=str(self._code_dir), env=env,
                  label="token test", on_done=self._on_test_token_done)

    def _on_test_token_done(self, ok: bool):
        if ok:
            self._log("ok", "トークン認証テスト: 成功")
        else:
            self._log("fail", "トークン認証テスト: 失敗（トークン / スコープを確認してください）")

    # -- build handlers ----------------------------------------------------

    def _on_build(self):
        if not self._code_dir:
            QMessageBox.warning(self, "エラー", "code/ が見つかりません")
            return
        if self._workers:
            return

        if self.cb_clean_dist.isChecked():
            self._remove_dir(self._code_dir / "dist")
            self._log("info", "dist/ 削除")
        if self.cb_clean_build.isChecked():
            self._remove_dir(self._code_dir / "build")
            self._log("info", "build/ 削除")
        if self.cb_clean_egg.isChecked():
            for d in self._code_dir.glob("*.egg-info"):
                self._remove_dir(d)
                self._log("info", f"{d.name} 削除")

        self._log("head", "=== ビルド開始 ===")
        cmd = [sys.executable, "-m", "build"]
        self._run(cmd, cwd=str(self._code_dir), label="build",
                  on_done=self._on_build_done)

    def _on_build_done(self, ok: bool):
        if ok:
            self._refresh_dist_list()
        stage = self._full_release_stage
        if stage == "build":
            if ok:
                self._full_release_stage = "verify"
                self._log("info", "フルリリース: 検証フェーズへ")
                QTimer.singleShot(400, self._on_verify)
            else:
                self._log("fail", "フルリリース中止（ビルド失敗）")
                self._full_release_stage = None

    # -- verify handlers ---------------------------------------------------

    def _on_verify(self):
        if not self._code_dir:
            return
        dist = self._code_dir / "dist"
        if not dist.exists() or not any(dist.iterdir()):
            QMessageBox.warning(self, "エラー",
                                "dist/ が空です。先にビルドしてください。")
            if self._full_release_stage == "verify":
                self._full_release_stage = None
            return

        self.verify_results.clear()
        self._log("head", "=== 検証開始 ===")

        if self.cb_version_check.isChecked():
            self._check_versions()
        if self.cb_sensitive_scan.isChecked():
            self._scan_sensitive()

        if self.cb_twine_check.isChecked():
            files = [str(p) for p in dist.iterdir() if p.is_file()]
            cmd = [sys.executable, "-m", "twine", "check"] + files
            self._run(cmd, cwd=str(self._code_dir), label="twine check",
                      on_done=self._on_verify_done)
        else:
            self._on_verify_done(True)

    def _check_versions(self):
        targets = [
            ("pyproject.toml", self._code_dir / "pyproject.toml",
             r'^version\s*=\s*"([^"]+)"'),
            ("statable/__init__.py", self._code_dir / "statable" / "__init__.py",
             r'__version__\s*=\s*"([^"]+)"'),
            ("codegen/__init__.py", self._code_dir / "codegen" / "__init__.py",
             r'__version__\s*=\s*"([^"]+)"'),
            ("statable/cli.py", self._code_dir / "statable" / "cli.py",
             r'CLI_VERSION\s*=\s*"([^"]+)"'),
        ]
        versions: dict[str, str] = {}
        for name, path, pattern in targets:
            try:
                text = path.read_text(encoding="utf-8")
                m = re.search(pattern, text, re.MULTILINE)
                versions[name] = m.group(1) if m else "?"
            except Exception as e:
                versions[name] = f"ERROR: {e}"

        for name, v in versions.items():
            self._add_verify_result(not v.startswith("ERROR"), f"{name}: {v}")

        valid = [v for v in versions.values() if not v.startswith("ERROR")]
        unique = set(valid)
        if len(unique) == 1 and valid:
            v = next(iter(unique))
            self._add_verify_result(True, f"バージョン整合性: OK ({v})")
            self._log("ok", f"バージョン整合性 OK: {v}")
        else:
            self._add_verify_result(False, f"バージョン不整合: {unique}")
            self._log("fail", f"バージョン不整合: {unique}")

    def _scan_sensitive(self):
        dist = self._code_dir / "dist"
        for f in dist.iterdir():
            if not f.is_file():
                continue
            names: list[str] = []
            try:
                if f.suffix in (".whl", ".zip"):
                    with zipfile.ZipFile(f) as z:
                        names = z.namelist()
                elif f.name.endswith(".tar.gz"):
                    with tarfile.open(f, "r:gz") as t:
                        names = t.getnames()
            except Exception as e:
                self._add_verify_result(False, f"{f.name}: 読込失敗 ({e})")
                continue

            hits: list[str] = []
            for n in names:
                low = n.lower()
                for pat in SENSITIVE_PATTERNS:
                    if pat in low:
                        hits.append(f"{n} (matches '{pat}')")
                        break

            if hits:
                self._add_verify_result(
                    False, f"{f.name}: {len(hits)} 件の機密ファイル混入")
                for h in hits[:5]:
                    self._log("fail", f"  {h}")
            else:
                self._add_verify_result(True, f"{f.name}: 機密ファイルなし")
                self._log("ok", f"{f.name}: 機密ファイルなし")

    def _on_verify_done(self, ok: bool):
        stage = self._full_release_stage
        if stage == "verify":
            if ok:
                self._full_release_stage = "upload"
                self._log("info", "フルリリース: アップロードフェーズへ")
                QTimer.singleShot(400, lambda: self._on_upload(skip_confirm=True))
            else:
                self._log("fail", "フルリリース中止（検証失敗）")
                self._full_release_stage = None

    # -- upload handlers ---------------------------------------------------

    def _get_token(self, target_testpypi: bool) -> str:
        if target_testpypi:
            t = self.testpypi_token_edit.text().strip()
            if t:
                return t
            # Fallback to main token
        t = self.token_edit.text().strip()
        if t:
            return t
        # Try loading from file
        try:
            p = Path(self.token_path_edit.text()).expanduser()
            t = p.read_text(encoding="utf-8").strip()
            self.token_edit.setText(t)
            return t
        except Exception:
            return ""

    def _on_upload(self, skip_confirm: bool = False):
        if not self._code_dir:
            return
        dist = self._code_dir / "dist"
        if not dist.exists() or not any(dist.iterdir()):
            QMessageBox.warning(self, "エラー", "dist/ が空です")
            if self._full_release_stage == "upload":
                self._full_release_stage = None
            return

        use_test = self.rb_testpypi.isChecked()
        token = self._get_token(use_test)
        if not token:
            QMessageBox.warning(self, "エラー", "トークンが設定されていません")
            if self._full_release_stage == "upload":
                self._full_release_stage = None
            return

        target_name = "TestPyPI" if use_test else "本番 PyPI"
        target_url = TESTPYPI_URL if use_test else PYPI_URL

        if not skip_confirm:
            files = [p.name for p in dist.iterdir() if p.is_file()]
            msg = (f"{target_name} へアップロードします：\n\n"
                   + "\n".join(f"  - {f}" for f in files)
                   + "\n\nよろしいですか？")
            r = QMessageBox.question(self, "アップロード確認", msg,
                                     QMessageBox.Yes | QMessageBox.No)
            if r != QMessageBox.Yes:
                self._full_release_stage = None
                return

        env = os.environ.copy()
        env["TWINE_USERNAME"] = "__token__"
        env["TWINE_PASSWORD"] = token
        files = [str(p) for p in dist.iterdir() if p.is_file()]
        cmd = [sys.executable, "-m", "twine", "upload",
               "--repository-url", target_url] + files

        self._log("head", f"=== {target_name} へアップロード ===")
        self._run(cmd, cwd=str(self._code_dir), env=env,
                  label=f"upload ({target_name})",
                  on_done=self._on_upload_done)

    def _on_upload_done(self, ok: bool):
        if ok:
            self._log("ok", "アップロード成功")
        else:
            self._log("fail", "アップロード失敗")
        if self._full_release_stage == "upload":
            self._full_release_stage = None
            if ok:
                self._log("ok", "=== フルリリース完了 ===")
            else:
                self._log("fail", "=== フルリリース中断 ===")

    # -- full release ------------------------------------------------------

    def _on_full_release(self):
        if not self._code_dir:
            QMessageBox.warning(self, "エラー", "code/ が見つかりません")
            return
        use_test = self.rb_testpypi.isChecked()
        target_name = "TestPyPI" if use_test else "本番 PyPI"
        r = QMessageBox.question(
            self, "フルリリース確認",
            f"以下を順に実行します:\n"
            f"  1. クリーンビルド\n"
            f"  2. 検証（バージョン / 機密 / twine）\n"
            f"  3. {target_name} へアップロード\n\n"
            f"実行しますか？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if r != QMessageBox.Yes:
            return

        self._log("head", "=== フルリリース開始 ===")
        self._full_release_stage = "build"
        self._on_build()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("StaTable Release Helper")
    win = ReleaseHelper()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()