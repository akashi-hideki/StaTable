# statable_gui/transition_editor/preview_widget.py
"""
遷移プレビューウィジェット
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from .draft import TransitionDraft


class TransitionPreviewWidget(QWidget):
    """遷移プレビュー"""

    def __init__(self, draft: TransitionDraft, parent=None):
        super().__init__(parent)
        self.draft = draft
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text)
        self.update_preview()

    def update_preview(self):
        lines = []
        lines.append(f"遷移: {self.draft.source} --[{self.draft.event}]--> ?")

        if self.draft.use_pre_action:
            lines.append(f"前処理: {self.draft.pre_action}() → {self.draft.pre_result_var}")

        if self.draft.conditions:
            for c in self.draft.conditions:
                lines.append(f"条件[{c.priority}]: {c.condition} → {c.target} ({c.action})")
        elif self.draft.use_transition_guard:
            lines.append(f"付帯条件: {self.draft.transition_guard}")
            lines.append(f"成立時: → {self.draft.guard_success_target}")
            if self.draft.guard_fail_mode == "target":
                lines.append(f"不成立時: → {self.draft.guard_fail_target} ({self.draft.guard_fail_action})")
            else:
                lines.append("不成立時: 現状維持")

        if self.draft.actions:
            for a in self.draft.actions:
                lines.append(f"実行[{a.order}]: {a.action}()")

        if self.draft.use_post_action:
            lines.append(f"後処理: {self.draft.post_action}()")

        self.preview_text.setPlainText("\n".join(lines))