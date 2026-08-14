from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QToolButton, QMessageBox, QInputDialog
)

from statable.state_machine import StateMachine

from .logger import StaTableLogger
from .traceball import TraceBallWidget
from .config import WINDOW_WIDTH, WINDOW_HEIGHT
from .sample_data import create_sample_state_machine
from .widgets import StateMachineTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StaTable - 状態遷移表エディタ")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        self.logger = StaTableLogger()
        self.logger.debug("MainWindow initialization started")

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tab_widget)

        self.add_tab_button = QToolButton()
        self.add_tab_button.setText("+")
        self.add_tab_button.setToolTip("新しい状態遷移表を追加")
        self.add_tab_button.clicked.connect(self.add_new_tab)
        self.tab_widget.setCornerWidget(self.add_tab_button, Qt.TopRightCorner)

        self.create_menus()

        self.traceball = TraceBallWidget(self)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.traceball)
        self.traceball.hide()

        sample_sm = create_sample_state_machine()
        self.add_state_machine_tab("アプリ", sample_sm)

        self.logger.debug("MainWindow initialization completed")

    def create_menus(self):
        menubar = self.menuBar()
        view_menu = menubar.addMenu("表示")
        toggle_traceball = QAction("TraceBall表示", self)
        toggle_traceball.setCheckable(True)
        toggle_traceball.setChecked(False)
        toggle_traceball.toggled.connect(self.toggle_traceball)
        view_menu.addAction(toggle_traceball)

        file_menu = menubar.addMenu("ファイル")
        new_tab_action = QAction("新しい状態遷移表", self)
        new_tab_action.triggered.connect(self.add_new_tab)
        file_menu.addAction(new_tab_action)

    def add_new_tab(self):
        name, ok = QInputDialog.getText(self, "新しい状態遷移表", "タブ名を入力してください：")
        if ok and name:
            sm = StateMachine()
            self.add_state_machine_tab(name, sm)
            self.logger.info(f"New tab added: {name}")

    def add_state_machine_tab(self, name: str, sm: StateMachine):
        tab = StateMachineTab(sm)
        idx = self.tab_widget.addTab(tab, name)
        self.tab_widget.setCurrentIndex(idx)
        self.logger.debug(f"Tab '{name}' added at index {idx}")

    def close_tab(self, index: int):
        if self.tab_widget.count() <= 1:
            QMessageBox.warning(self, "警告", "少なくとも1つのタブが必要です。")
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