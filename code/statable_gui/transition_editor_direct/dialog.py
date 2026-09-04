# statable_gui/transition_editor_direct/dialog.py
"""
動作編集ダイアログ
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QSplitter
)
from PySide6.QtCore import Qt

from .draft import ActionDraft
from .palette_widget import PaletteWidget
from .flow_widget import FlowWidget


class ActionEditorDialog(QDialog):
    """動作編集ダイアログ（D&D対応）"""

    def __init__(self, draft: ActionDraft,
                 variables=None, flags=None, role_functions=None,
                 conditions=None, states=None, parent=None):
        super().__init__(parent)
        self.draft = draft
        self.variables = variables or []
        self.flags = flags or []
        self.role_functions = role_functions or []
        self.conditions = conditions or []
        self.states = states or []

        self.setWindowTitle(f"動作編集: {draft.source} --[{draft.event}]--> ?")
        self.setMinimumSize(800, 600)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # スプリッター（左:パレット / 右:フロー）
        splitter = QSplitter(Qt.Horizontal)

        # 左: パレット
        self.palette = PaletteWidget(
            self.variables, self.flags, self.role_functions, self.conditions
        )
        self.palette.setMinimumWidth(200)
        splitter.addWidget(self.palette)

        # 右: フロー
        self.flow = FlowWidget(self.draft, self.states)
        self.flow.setMinimumWidth(500)
        splitter.addWidget(self.flow)

        splitter.setSizes([200, 600])
        main_layout.addWidget(splitter)

        # ボタン
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        main_layout.addLayout(btn_layout)