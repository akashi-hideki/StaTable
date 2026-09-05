# statable_gui/transition_editor_direct/dialog.py
"""
動作編集メインダイアログ
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget,
    QWidget, QSplitter
)
from PySide6.QtCore import Qt

from .draft import ActionDraft
from .palette_widget import PaletteWidget
from .canvas_widget import FlowCanvas
from .code_widget import CodeWidget
from .system_global_dialog import SystemGlobalDialog


class ActionEditorDialog(QDialog):
    def __init__(self, draft: ActionDraft,
                 role_functions=None, transition_events=None,
                 states=None, parent=None):
        super().__init__(parent)
        self.draft = draft
        self.role_functions = role_functions or []
        self.transition_events = transition_events or []
        self.states = states or []

        self.setWindowTitle(f"動作編集: {draft.source} --[{draft.event}]--> ?")
        self.setMinimumSize(900, 650)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # タブ
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # フロー編集タブ
        flow_tab = QWidget()
        flow_layout = QVBoxLayout(flow_tab)

        splitter = QSplitter(Qt.Horizontal)
        self.palette = PaletteWidget(self.role_functions, self.transition_events)
        self.palette.setMinimumWidth(200)
        splitter.addWidget(self.palette)

        self.canvas = FlowCanvas(self.draft)
        splitter.addWidget(self.canvas)
        splitter.setSizes([200, 650])

        flow_layout.addWidget(splitter)
        self.tabs.addTab(flow_tab, "フロー編集")

        # コードタブ
        self.code_widget = CodeWidget(self.draft)
        self.tabs.addTab(self.code_widget, "コード")

        # システムグローバルボタン
        global_btn = QPushButton("システムグローバル...")
        global_btn.clicked.connect(self._open_system_global)
        main_layout.addWidget(global_btn)

        # OK/キャンセル
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        main_layout.addLayout(btn_layout)

    def _open_system_global(self):
        dialog = SystemGlobalDialog(self.draft, self)
        dialog.exec()
        self.code_widget.update_code()