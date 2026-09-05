# statable_gui/transition_editor_direct/dialog.py
"""
動作編集メインダイアログ（ビジュアル編集 + コードプレビュー）
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QSplitter, QPlainTextEdit, QLabel
)
from PySide6.QtCore import Qt

from .draft import ActionDraft
from .palette_widget import PaletteWidget
from .flow_widget import FlowWidget


class ActionEditorDialog(QDialog):
    """動作編集ダイアログ"""

    def __init__(self, draft: ActionDraft,
                 role_functions=None, transition_events=None,
                 states=None, parent=None):
        super().__init__(parent)
        self.draft = draft
        self.role_functions = role_functions or []
        self.transition_events = transition_events or []
        self.states = states or []

        self.setWindowTitle(f"動作編集: {draft.source} --[{draft.event}]--> ?")
        self.setMinimumSize(850, 650)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # スプリッター（左:パレット / 右:フロー）
        splitter = QSplitter(Qt.Horizontal)

        self.palette = PaletteWidget(self.role_functions, self.transition_events)
        self.palette.setMinimumWidth(200)
        splitter.addWidget(self.palette)

        self.flow = FlowWidget(self.draft, self.role_functions, self.states)
        self.flow.setMinimumWidth(500)
        self.flow.draft_updated.connect(self._update_code_preview)
        splitter.addWidget(self.flow)

        splitter.setSizes([200, 600])
        main_layout.addWidget(splitter)

        # コードプレビュー（読み取り専用）
        main_layout.addWidget(QLabel("生成コード（読み取り専用）:"))
        self.code_preview = QPlainTextEdit()
        self.code_preview.setReadOnly(True)
        self.code_preview.setMaximumHeight(150)
        main_layout.addWidget(self.code_preview)

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

        self._update_code_preview()

    def _update_code_preview(self):
        """フローからコードを生成してプレビューに表示"""
        code = self._generate_code()
        self.draft.generated_code = code
        self.code_preview.setPlainText(code)

    def _generate_code(self) -> str:
        lines = []
        for item in self.draft.flow_items:
            if item.item_type == "function":
                lines.append(f"{item.name}();")
            elif item.item_type == "transition":
                cond = item.params.get('condition', '')
                target = item.params.get('target', '')
                pre_actions = item.params.get('pre_actions', [])
                if cond:
                    lines.append(f"if ({cond}) {{")
                    for pre in pre_actions:
                        lines.append(f"    {pre}();")
                    lines.append(f"    next_state = {target};")
                    lines.append("}")
                else:
                    lines.append(f"next_state = {target};")
        if self.draft.default_target:
            lines.append(f"// default: {self.draft.default_target}")
        return "\n".join(lines)