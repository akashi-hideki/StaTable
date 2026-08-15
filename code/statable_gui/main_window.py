from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QToolButton, QMessageBox, QInputDialog,
    QFileDialog
)

from statable.state_machine import StateMachine
from statable.xml_io import project_to_xml, project_from_xml

from .logger import StaTableLogger
from .traceball import TraceBallWidget
from .config import WINDOW_WIDTH, WINDOW_HEIGHT
from .sample_data import create_sample_state_machine
from .widgets import StateMachineTab
from .preferences import Preferences
from .global_defs import GlobalDefinitions
from .global_defs_dialog import GlobalDefinitionsDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StaTable - State Transition Editor")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        self.logger = StaTableLogger()
        self.logger.debug("MainWindow initialization started")

        # 環境設定
        self.prefs = Preferences()

        # グローバル変数・イベントフラグ定義（プロジェクト全体で共有）
        self.global_defs = GlobalDefinitions()

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tab_widget)

        # 「+」ボタン
        self.add_tab_button = QToolButton()
        self.add_tab_button.setText("+")
        self.add_tab_button.setToolTip("Add new state machine")
        self.add_tab_button.clicked.connect(self.add_new_tab)
        self.tab_widget.setCornerWidget(self.add_tab_button, Qt.TopRightCorner)

        # ダブルクリックでタブ名変更
        self.tab_widget.tabBarDoubleClicked.connect(self.rename_tab_at)

        self.create_menus()

        self.traceball = TraceBallWidget(self)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.traceball)
        self.traceball.hide()

        # 初期タブ
        sample_sm = create_sample_state_machine()
        self.add_state_machine_tab("Application", sample_sm)

        self.logger.debug("MainWindow initialization completed")

    def create_menus(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")
        open_action = QAction("Open Project...", self)
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)

        save_action = QAction("Save Project...", self)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)

        rename_action = QAction("Rename Tab...", self)
        rename_action.triggered.connect(self.rename_current_tab)
        file_menu.addAction(rename_action)

        file_menu.addSeparator()

        new_tab_action = QAction("New State Machine", self)
        new_tab_action.triggered.connect(self.add_new_tab)
        file_menu.addAction(new_tab_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        global_defs_action = QAction("Global Definitions...", self)
        global_defs_action.triggered.connect(self.open_global_defs_dialog)
        edit_menu.addAction(global_defs_action)

        # View menu
        view_menu = menubar.addMenu("View")
        toggle_traceball = QAction("TraceBall", self)
        toggle_traceball.setCheckable(True)
        toggle_traceball.setChecked(False)
        toggle_traceball.toggled.connect(self.toggle_traceball)
        view_menu.addAction(toggle_traceball)

    def open_global_defs_dialog(self):
        """グローバル変数・イベントフラグ定義ダイアログを開く"""
        dlg = GlobalDefinitionsDialog(self.global_defs, self)
        dlg.exec()

    # ------------------------------------------------------------------
    # プロジェクト保存・読み込み（既存）
    # ------------------------------------------------------------------
    def save_project(self):
        tabs = []
        for index in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(index)
            name = self.tab_widget.tabText(index)
            tabs.append((name, tab.sm))

        last_dir = self.prefs.last_project_dir
        default_path = str(Path(last_dir) / "project.xml") if last_dir else "project.xml"

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Project", default_path, "XML files (*.xml)"
        )
        if not filepath:
            return
        try:
            project_to_xml(tabs, filepath)
            self.prefs.last_project_dir = str(Path(filepath).parent)
            self.logger.info(f"Project saved to {filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project:\n{e}")
            self.logger.error(f"Failed to save project: {filepath}, error: {e}")

    def open_project(self):
        last_dir = self.prefs.last_project_dir
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Project", last_dir, "XML files (*.xml)"
        )
        if not filepath:
            return
        try:
            tabs = project_from_xml(filepath)
            self.close_all_tabs()
            for name, sm in tabs:
                self.add_state_machine_tab(name, sm)
            self.prefs.last_project_dir = str(Path(filepath).parent)
            self.logger.info(f"Project loaded from {filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open project:\n{e}")
            self.logger.error(f"Failed to open project: {filepath}, error: {e}")

    def close_all_tabs(self):
        while self.tab_widget.count() > 0:
            widget = self.tab_widget.widget(0)
            self.tab_widget.removeTab(0)
            widget.deleteLater()

    # ------------------------------------------------------------------
    # タブ操作
    # ------------------------------------------------------------------
    def rename_current_tab(self):
        index = self.tab_widget.currentIndex()
        if index >= 0:
            self.rename_tab_at(index)

    def rename_tab_at(self, index: int):
        if index < 0:
            return
        current_name = self.tab_widget.tabText(index)
        new_name, ok = QInputDialog.getText(
            self, "Rename Tab", "Enter new tab name:", text=current_name
        )
        if ok and new_name.strip():
            self.tab_widget.setTabText(index, new_name.strip())
            self.logger.info(f"Tab renamed: {current_name} -> {new_name.strip()}")

    def add_new_tab(self):
        name, ok = QInputDialog.getText(
            self, "New State Machine", "Enter tab name:"
        )
        if ok and name.strip():
            sm = StateMachine()
            self.add_state_machine_tab(name.strip(), sm)
            self.logger.info(f"New tab added: {name.strip()}")

    def add_state_machine_tab(self, name: str, sm: StateMachine):
        # ★ global_defs をタブへ渡す
        tab = StateMachineTab(sm, global_defs=self.global_defs)
        idx = self.tab_widget.addTab(tab, name)
        self.tab_widget.setCurrentIndex(idx)
        self.logger.debug(f"Tab '{name}' added at index {idx}")

    def close_tab(self, index: int):
        if self.tab_widget.count() <= 1:
            QMessageBox.warning(self, "Warning", "At least one tab is required.")
            return
        widget = self.tab_widget.widget(index)
        self.tab_widget.removeTab(index)
        widget.deleteLater()
        self.logger.info(f"Tab closed at index {index}")

    def toggle_traceball(self, checked: bool):
        if checked:
            self.traceball.show()
            self.logger.debug("TraceBall shown")
        else:
            self.traceball.hide()
            self.logger.debug("TraceBall hidden")