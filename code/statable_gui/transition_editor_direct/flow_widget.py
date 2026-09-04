# statable_gui/transition_editor_direct/flow_widget.py
"""
動作フローリストウィジェット（修正版）
パレットからのD&Dと行挿入、ダブルクリック編集をサポート
"""

import json
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QComboBox,
    QAbstractItemView
)

from .draft import ActionDraft, FlowItem
from .edit_dialogs import (
    FunctionEditDialog, ConditionEditDialog, VariableEditDialog
)


class FlowListWidget(QListWidget):
    """D&Dと行挿入をサポートするフローリスト"""

    MIME_TYPE = "application/x-flow-item"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(self.MIME_TYPE) or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(self.MIME_TYPE) or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat(self.MIME_TYPE):
            # パレットからのドロップ
            data = json.loads(event.mimeData().data(self.MIME_TYPE).data().decode("utf-8"))
            item_type = data.get("item_type", "unknown")
            name = data.get("name", "")

            # 挿入位置を決定
            drop_pos = event.position().toPoint()
            item_at_pos = self.itemAt(drop_pos)
            if item_at_pos is not None:
                rect = self.visualItemRect(item_at_pos)
                insert_before = drop_pos.y() < rect.center().y()
                insert_row = self.row(item_at_pos)
                if not insert_before:
                    insert_row += 1
            else:
                insert_row = self.count()

            # FlowItemを作成して挿入
            flow_item = FlowItem(item_type=item_type, name=name)
            list_item = QListWidgetItem(name)
            list_item.setData(Qt.UserRole, flow_item)
            self.insertItem(insert_row, list_item)
            self._notify_draft_changed()
            event.acceptProposedAction()
        else:
            # 内部移動（並べ替え）は標準動作に任せる
            super().dropEvent(event)
            self._notify_draft_changed()

    def _notify_draft_changed(self):
        # 親のFlowWidgetに通知
        parent = self.parentWidget()
        if hasattr(parent, '_on_flow_list_changed'):
            parent._on_flow_list_changed()


class FlowWidget(QWidget):
    """動作フローリストウィジェット"""

    draft_updated = Signal()

    def __init__(self, draft: ActionDraft, role_functions=None, states=None, parent=None):
        super().__init__(parent)
        self.draft = draft
        self.role_functions = role_functions or []
        self.states = states or []

        self._setup_ui()
        self._load_draft()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("動作フロー（D&Dで並べ替え・ダブルクリックで編集）"))

        # カスタムリスト
        self.flow_list = FlowListWidget()
        self.flow_list.setMinimumHeight(300)
        self.flow_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.flow_list)

        # デフォルト遷移先
        default_layout = QHBoxLayout()
        default_layout.addWidget(QLabel("デフォルト遷移先:"))
        self.default_target_combo = QComboBox()
        self.default_target_combo.setEditable(True)
        self.default_target_combo.addItems(self.states)
        self.default_target_combo.currentTextChanged.connect(self._on_draft_changed)
        default_layout.addWidget(self.default_target_combo)
        layout.addLayout(default_layout)

    # ===== ドラフト読み込み =====
    def _load_draft(self):
        self.flow_list.clear()
        for item in self.draft.flow_items:
            list_item = QListWidgetItem(item.display_text())
            list_item.setData(Qt.UserRole, item)
            self.flow_list.addItem(list_item)
        self.default_target_combo.setCurrentText(self.draft.default_target)

    # ===== リスト変更時の同期 =====
    def _on_flow_list_changed(self):
        self._sync_draft_from_list()
        self.draft_updated.emit()

    def _sync_draft_from_list(self):
        self.draft.flow_items = []
        for i in range(self.flow_list.count()):
            item = self.flow_list.item(i)
            flow_item = item.data(Qt.UserRole)
            if not flow_item:
                flow_item = FlowItem(item_type="unknown", name=item.text())
                item.setData(Qt.UserRole, flow_item)
            self.draft.flow_items.append(flow_item)

    def _on_draft_changed(self, *args):
        self._sync_draft_from_list()
        self.draft.default_target = self.default_target_combo.currentText()
        self.draft_updated.emit()

    # ===== ダブルクリック編集 =====
    def _on_item_double_clicked(self, item):
        flow_item = item.data(Qt.UserRole)
        if not flow_item:
            flow_item = FlowItem(item_type="unknown", name=item.text())
            item.setData(Qt.UserRole, flow_item)

        if flow_item.item_type == "function":
            dialog = FunctionEditDialog(flow_item, self.role_functions, self)
        elif flow_item.item_type == "condition":
            dialog = ConditionEditDialog(
                flow_item, self.states, self.role_functions, self
            )
        elif flow_item.item_type == "variable":
            dialog = VariableEditDialog(flow_item, self)
        else:
            dialog = VariableEditDialog(flow_item, self)

        if dialog.exec():
            edited_text, params = dialog.get_result()
            flow_item.edited_text = edited_text
            flow_item.params = params
            item.setText(edited_text if edited_text else flow_item.name)
            self._on_draft_changed()