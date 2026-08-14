from typing import Optional, List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QComboBox, QTextEdit, QDialogButtonBox,
    QMessageBox
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from statable.model import Transition
from .action_edit_dialog import ActionEditDialog


class TransitionListDialog(QDialog):
    """1セル内の複数の遷移条件を一括編集するダイアログ"""
    def __init__(self, parent=None, state_names=None, event_name="",
                 existing_transitions=None, role_functions=None):
        super().__init__(parent)
        self.setWindowTitle("遷移編集（複数条件）")
        self.setMinimumSize(800, 500)
        self.state_names = state_names or []
        self.role_functions = role_functions or {}

        layout = QVBoxLayout(self)

        # イベント表示
        event_label = QLabel(f"イベント: {event_name if event_name else '完了遷移'}")
        layout.addWidget(event_label)

        # 遷移テーブル
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["遷移条件", "動作（複数行可）", "遷移先", "表示タイトル"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setFont(QFont("Consolas", 10))
        layout.addWidget(self.table)

        # ダブルクリックで動作編集ダイアログを開く
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)

        # ボタン
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("行追加")
        add_btn.clicked.connect(self.add_row)
        del_btn = QPushButton("行削除")
        del_btn.clicked.connect(self.delete_row)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # OK/Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if existing_transitions:
            for trans in existing_transitions:
                self.add_row(trans)
        else:
            self.add_row()

    def on_cell_double_clicked(self, row, col):
        """テーブルセルのダブルクリックで動作編集ダイアログを開く"""
        # 動作列（1列目）の編集に限定
        action_widget = self.table.cellWidget(row, 1)
        if action_widget and isinstance(action_widget, QTextEdit):
            current_action = action_widget.toPlainText()
        else:
            item = self.table.item(row, 1)
            current_action = item.text() if item else ""

        dlg = ActionEditDialog(
            self,
            action_text=current_action,
            role_functions=self.role_functions
        )
        if dlg.exec() == QDialog.Accepted:
            new_action = dlg.get_action_text()
            if action_widget and isinstance(action_widget, QTextEdit):
                action_widget.setPlainText(new_action)
            else:
                item = QTableWidgetItem(new_action)
                self.table.setItem(row, 1, item)

    def add_row(self, trans: Optional[Transition] = None):
        row = self.table.rowCount()
        self.table.insertRow(row)

        cond_item = QTableWidgetItem(trans.guard if trans else "")
        cond_item.setToolTip("C言語式（例：err_code != 0）")
        self.table.setItem(row, 0, cond_item)

        action_edit = QTextEdit()
        action_edit.setAcceptRichText(False)
        action_edit.setPlainText(trans.action if trans else "")
        action_edit.setToolTip("ダブルクリックで編集ダイアログを開きます")
        self.table.setCellWidget(row, 1, action_edit)

        target_combo = QComboBox()
        target_combo.addItem("")
        target_combo.addItems(self.state_names)
        if trans and trans.target:
            idx = target_combo.findText(trans.target)
            if idx >= 0:
                target_combo.setCurrentIndex(idx)
        self.table.setCellWidget(row, 2, target_combo)

        title = self._generate_title(trans) if trans else ""
        title_item = QTableWidgetItem(title)
        title_item.setToolTip("表に表示する短いラベル（空なら自動生成）")
        self.table.setItem(row, 3, title_item)

    def _generate_title(self, trans: Optional[Transition]) -> str:
        if not trans:
            return ""
        parts = [trans.target] if trans.target else ["(内部)"]
        if trans.guard:
            parts.append(f"[{trans.guard}]")
        if trans.action:
            parts.append(f"/ {trans.action}")
        return " ".join(parts)

    def delete_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def get_transitions(self) -> List[Transition]:
        transitions = []
        for row in range(self.table.rowCount()):
            guard = self.table.item(row, 0).text().strip() if self.table.item(row, 0) else ""
            action_widget = self.table.cellWidget(row, 1)
            action = action_widget.toPlainText().strip() if action_widget else ""
            target_widget = self.table.cellWidget(row, 2)
            target = target_widget.currentText().strip() if target_widget else ""
            title_item = self.table.item(row, 3)
            title = title_item.text().strip() if title_item else ""
            if not title and (guard or action or target):
                title = self._generate_title(Transition(source="", event="", guard=guard, action=action, target=target))
            transitions.append(Transition(
                source="",
                event="",
                guard=guard,
                action=action,
                target=target,
                transition_type="external"
            ))
        return transitions