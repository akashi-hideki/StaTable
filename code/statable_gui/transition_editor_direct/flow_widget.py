# statable_gui/transition_editor_direct/flow_widget.py
"""
動作フローエリア（ドラッグアンドドロップ対応）
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QGroupBox,
    QAbstractItemView, QComboBox, QLineEdit
)
from PySide6.QtCore import Qt, Signal

from .draft import ActionDraft, ConditionBlock


class FlowWidget(QWidget):
    """動作フローエリア"""

    draft_updated = Signal()

    def __init__(self, draft: ActionDraft, states=None, parent=None):
        super().__init__(parent)
        self.draft = draft
        self.states = states or []

        self._setup_ui()
        self._load_draft()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # ===== 前処理ブロック =====
        pre_group = QGroupBox("前処理（ロール関数をD&D）")
        pre_layout = QVBoxLayout(pre_group)
        self.pre_list = QListWidget()
        self.pre_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.pre_list.setDefaultDropAction(Qt.MoveAction)
        self.pre_list.setMaximumHeight(80)
        self.pre_list.model().rowsMoved.connect(self._update_pre_from_list)
        pre_layout.addWidget(self.pre_list)
        layout.addWidget(pre_group)

        # ===== 条件ブロック =====
        cond_group = QGroupBox("条件（状態遷移条件をD&D）")
        cond_layout = QVBoxLayout(cond_group)

        self.condition_list = QListWidget()
        self.condition_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.condition_list.setDefaultDropAction(Qt.MoveAction)
        self.condition_list.setMaximumHeight(120)
        self.condition_list.model().rowsMoved.connect(self._update_conditions_from_list)
        cond_layout.addWidget(self.condition_list)

        # デフォルト遷移先
        default_layout = QHBoxLayout()
        default_layout.addWidget(QLabel("デフォルト遷移先:"))
        self.default_target_combo = QComboBox()
        self.default_target_combo.setEditable(True)
        self.default_target_combo.addItems(self.states)
        self.default_target_combo.currentTextChanged.connect(self._on_draft_changed)
        default_layout.addWidget(self.default_target_combo)
        cond_layout.addLayout(default_layout)

        layout.addWidget(cond_group)

        # ===== 実行ブロック =====
        action_group = QGroupBox("実行処理（ロール関数をD&D）")
        action_layout = QVBoxLayout(action_group)
        self.action_list = QListWidget()
        self.action_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.action_list.setDefaultDropAction(Qt.MoveAction)
        self.action_list.setMaximumHeight(120)
        self.action_list.model().rowsMoved.connect(self._update_actions_from_list)
        action_layout.addWidget(self.action_list)
        layout.addWidget(action_group)

        # ===== 後処理ブロック =====
        post_group = QGroupBox("後処理（ロール関数をD&D）")
        post_layout = QVBoxLayout(post_group)
        self.post_list = QListWidget()
        self.post_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.post_list.setDefaultDropAction(Qt.MoveAction)
        self.post_list.setMaximumHeight(80)
        self.post_list.model().rowsMoved.connect(self._update_post_from_list)
        post_layout.addWidget(self.post_list)
        layout.addWidget(post_group)

        layout.addStretch()

    # ===== ドラフト読み込み =====
    def _load_draft(self):
        self.pre_list.clear()
        for action in self.draft.pre_actions:
            self.pre_list.addItem(action)

        self.condition_list.clear()
        for cond in self.draft.conditions:
            self.condition_list.addItem(
                f"[{cond.priority}] {cond.condition_expr} → {cond.target} ({cond.action})"
            )

        self.default_target_combo.setCurrentText(self.draft.default_target)

        self.action_list.clear()
        for action in self.draft.actions:
            self.action_list.addItem(action)

        self.post_list.clear()
        for action in self.draft.post_actions:
            self.post_list.addItem(action)

    # ===== ドロップイベント =====
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            text = event.mimeData().text()
            # ドロップ位置に応じて追加先を決定
            widget = self.childAt(event.position().toPoint())
            if widget:
                # どのリストにドロップされたか確認
                if isinstance(widget, QListWidget) or self._is_child_of(widget, QListWidget):
                    target_list = widget if isinstance(widget, QListWidget) else self._find_parent_list(widget)
                    if target_list:
                        target_list.addItem(text)
                        self._on_draft_changed()
                        event.acceptProposedAction()
                        return
        event.ignore()

    def _is_child_of(self, widget, parent_type):
        while widget:
            if isinstance(widget, parent_type):
                return True
            widget = widget.parent()
        return False

    def _find_parent_list(self, widget):
        while widget:
            if isinstance(widget, QListWidget):
                return widget
            widget = widget.parent()
        return None

    # ===== ドラフト同期 =====
    def _on_draft_changed(self, *args):
        self._update_pre_from_list()
        self._update_conditions_from_list()
        self._update_actions_from_list()
        self._update_post_from_list()
        self.draft.default_target = self.default_target_combo.currentText()
        self.draft_updated.emit()

    def _update_pre_from_list(self, *args):
        self.draft.pre_actions = [
            self.pre_list.item(i).text() for i in range(self.pre_list.count())
        ]

    def _update_conditions_from_list(self, *args):
        self.draft.conditions = []
        for i in range(self.condition_list.count()):
            text = self.condition_list.item(i).text()
            # "[1] voltage > 800 → RUNNING (Start)" を解析
            cond = ConditionBlock(priority=i + 1)
            # 簡易パース
            if "]" in text:
                rest = text.split("]", 1)[1].strip()
                if "→" in rest:
                    cond_part, target_part = rest.split("→", 1)
                    cond.condition_expr = cond_part.strip()
                    target_part = target_part.strip()
                    if "(" in target_part:
                        cond.target = target_part.split("(")[0].strip()
                        cond.action = target_part.split("(")[1].replace(")", "").strip()
                    else:
                        cond.target = target_part.strip()
                else:
                    cond.condition_expr = rest
            else:
                cond.condition_expr = text
            self.draft.conditions.append(cond)

    def _update_actions_from_list(self, *args):
        self.draft.actions = [
            self.action_list.item(i).text() for i in range(self.action_list.count())
        ]

    def _update_post_from_list(self, *args):
        self.draft.post_actions = [
            self.post_list.item(i).text() for i in range(self.post_list.count())
        ]