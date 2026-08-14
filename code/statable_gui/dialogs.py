from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QComboBox, QTextEdit, QFormLayout,
    QLineEdit, QDialogButtonBox, QMessageBox
)
from PySide6.QtGui import QFont

from statable.model import Transition, RoleFunction


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

        # ロール関数挿入バー
        role_bar = QHBoxLayout()
        role_bar.addWidget(QLabel("ロール関数:"))
        self.role_combo = QComboBox()
        self.refresh_role_combo()
        role_bar.addWidget(self.role_combo)
        insert_btn = QPushButton("選択行に挿入")
        insert_btn.clicked.connect(self.insert_role_function)
        role_bar.addWidget(insert_btn)
        new_role_btn = QPushButton("新規ロール関数...")
        new_role_btn.clicked.connect(self.add_new_role_function)
        role_bar.addWidget(new_role_btn)
        layout.addLayout(role_bar)

        # 遷移テーブル
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["遷移条件", "動作（複数行可）", "遷移先", "表示タイトル"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setFont(QFont("Consolas", 10))
        layout.addWidget(self.table)

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

    def refresh_role_combo(self):
        self.role_combo.clear()
        for name in self.role_functions.keys():
            self.role_combo.addItem(name)

    def insert_role_function(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "警告", "行を選択してください。")
            return
        func_name = self.role_combo.currentText()
        if not func_name:
            return
        rf = self.role_functions.get(func_name)
        if not rf:
            return
        call = f"{func_name}({rf.arg1_name}, {rf.arg2_name});"
        action_widget = self.table.cellWidget(row, 1)
        if action_widget and isinstance(action_widget, QTextEdit):
            action_widget.insertPlainText(call + "\n")
        else:
            item = self.table.item(row, 1)
            if item:
                item.setText(item.text() + call + "\n")

    def add_new_role_function(self):
        dlg = RoleFunctionDialog(self)
        if dlg.exec() == QDialog.Accepted:
            rf = dlg.get_role_function()
            if rf.name in self.role_functions:
                QMessageBox.warning(self, "警告", "同名のロール関数が既に存在します。")
                return
            self.role_functions[rf.name] = rf
            self.refresh_role_combo()

    def add_row(self, trans: Optional[Transition] = None):
        row = self.table.rowCount()
        self.table.insertRow(row)

        cond_item = QTableWidgetItem(trans.guard if trans else "")
        cond_item.setToolTip("C言語式（例：err_code != 0）")
        self.table.setItem(row, 0, cond_item)

        action_edit = QTextEdit()
        action_edit.setAcceptRichText(False)
        action_edit.setPlainText(trans.action if trans else "")
        action_edit.setToolTip("ロール関数呼び出しや生Cコードを複数行で記述できます。")
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


class RoleFunctionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新規ロール関数")
        self.setMinimumWidth(400)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        layout.addRow("関数名", self.name_edit)

        self.desc_edit = QLineEdit()
        layout.addRow("説明", self.desc_edit)

        self.return_type_edit = QLineEdit("int")
        layout.addRow("戻り値型", self.return_type_edit)

        self.arg1_type_edit = QLineEdit("int")
        layout.addRow("引数1型", self.arg1_type_edit)
        self.arg1_name_edit = QLineEdit("arg1")
        layout.addRow("引数1名", self.arg1_name_edit)

        self.arg2_type_edit = QLineEdit("int")
        layout.addRow("引数2型", self.arg2_type_edit)
        self.arg2_name_edit = QLineEdit("arg2")
        layout.addRow("引数2名", self.arg2_name_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_role_function(self) -> RoleFunction:
        return RoleFunction(
            name=self.name_edit.text().strip(),
            description=self.desc_edit.text().strip(),
            return_type=self.return_type_edit.text().strip(),
            arg1_type=self.arg1_type_edit.text().strip(),
            arg1_name=self.arg1_name_edit.text().strip(),
            arg2_type=self.arg2_type_edit.text().strip(),
            arg2_name=self.arg2_name_edit.text().strip()
        )