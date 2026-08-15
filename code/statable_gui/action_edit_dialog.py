from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QComboBox,
    QPushButton, QLabel, QDialogButtonBox, QMessageBox, QLineEdit,
    QListWidget, QListWidgetItem, QSplitter, QWidget
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from .role_function_dialog import RoleFunctionDialog
from .global_defs import GlobalDefinitions
from .logger import StaTableLogger


class ActionEditDialog(QDialog):
    """遷移の動作（ロール関数呼び出し・生コード）を編集するダイアログ"""
    def __init__(self, parent=None, action_text="", role_functions=None, global_defs=None):
        super().__init__(parent)
        self.setWindowTitle("動作編集")
        self.setMinimumSize(800, 500)
        self.role_functions = role_functions if role_functions is not None else {}
        self.global_defs = global_defs if global_defs else GlobalDefinitions()

        StaTableLogger.debug(f"ActionEditDialog __init__: action_text length={len(action_text)}, roles={len(self.role_functions)}, global_defs={len(self.global_defs.variables)} vars, {len(self.global_defs.flags)} flags")

        main_layout = QVBoxLayout(self)

        # ロール関数選択・挿入バー
        role_bar = QHBoxLayout()
        role_bar.addWidget(QLabel("ロール関数:"))
        self.role_combo = QComboBox()
        self.refresh_role_combo()
        role_bar.addWidget(self.role_combo)
        insert_role_btn = QPushButton("挿入")
        insert_role_btn.clicked.connect(self.insert_role_function)
        role_bar.addWidget(insert_role_btn)
        new_role_btn = QPushButton("新規ロール関数...")
        new_role_btn.clicked.connect(self.add_new_role_function)
        role_bar.addWidget(new_role_btn)
        main_layout.addLayout(role_bar)

        self.signature_label = QLabel("")
        main_layout.addWidget(self.signature_label)

        # 左右分割
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 左側：検索＋定義一覧（グローバル変数・イベントフラグ）
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("検索:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("メンバ名・グループ名")
        self.search_edit.textChanged.connect(self.refresh_def_list)
        left_layout.addWidget(self.search_edit)

        self.def_list = QListWidget()
        self.def_list.itemDoubleClicked.connect(self.insert_definition)
        left_layout.addWidget(self.def_list)
        splitter.addWidget(left_widget)

        # 右側：動作コード編集
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("動作コード:"))
        self.action_edit = QTextEdit()
        self.action_edit.setAcceptRichText(False)
        self.action_edit.setPlainText(action_text)
        self.action_edit.setFont(QFont("Consolas", 10))
        right_layout.addWidget(self.action_edit)
        splitter.addWidget(right_widget)

        # OK/Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        self.refresh_def_list()
        self.update_signature_label()

        StaTableLogger.debug("ActionEditDialog initialization completed")

    def refresh_role_combo(self):
        self.role_combo.clear()
        for name in self.role_functions.keys():
            self.role_combo.addItem(name)
        self.role_combo.currentTextChanged.connect(self.update_signature_label)
        StaTableLogger.debug(f"ActionEditDialog.refresh_role_combo: {len(self.role_functions)} roles")

    def update_signature_label(self):
        func_name = self.role_combo.currentText()
        if func_name:
            rf = self.role_functions.get(func_name)
            if rf:
                sig = f"{rf.return_type} {rf.name}({rf.arg1_type} {rf.arg1_name}, {rf.arg2_type} {rf.arg2_name})"
                self.signature_label.setText(sig)
            else:
                self.signature_label.setText("")
        else:
            self.signature_label.setText("")

    def insert_role_function(self):
        func_name = self.role_combo.currentText()
        StaTableLogger.debug(f"ActionEditDialog.insert_role_function: '{func_name}'")
        if not func_name:
            return
        rf = self.role_functions.get(func_name)
        if not rf:
            return
        call = f"{func_name}({rf.arg1_name}, {rf.arg2_name});"
        self.action_edit.insertPlainText(call + "\n")
        StaTableLogger.debug(f"  -> inserted: {call}")

    def add_new_role_function(self):
        StaTableLogger.debug("ActionEditDialog.add_new_role_function called")
        dlg = RoleFunctionDialog(self)
        if dlg.exec() == QDialog.Accepted:
            rf = dlg.get_role_function()
            if rf.name in self.role_functions:
                QMessageBox.warning(self, "警告", "同名のロール関数が既に存在します。")
                return
            self.role_functions[rf.name] = rf
            self.refresh_role_combo()
            self.update_signature_label()
            StaTableLogger.debug(f"  -> new role added: {rf.name}")

    def refresh_def_list(self):
        query = self.search_edit.text().strip().lower()
        StaTableLogger.debug(f"ActionEditDialog.refresh_def_list: query='{query}'")
        self.def_list.clear()

        for var in self.global_defs.variables:
            if self._matches(var.name, var.group, query):
                item = QListWidgetItem(f"変数: {var.name}")
                item.setData(Qt.UserRole, var.name)
                item.setToolTip(f"型: {var.type}\nグループ: {var.group}\n説明: {var.description}")
                self.def_list.addItem(item)

        for flag in self.global_defs.flags:
            if self._matches(flag.name, flag.group, query):
                item = QListWidgetItem(f"フラグ: {flag.name}")
                item.setData(Qt.UserRole, flag.name)
                item.setToolTip(f"最小: {flag.min_value}, 最大: {flag.max_value}, ビット幅: {flag.bit_width}\nグループ: {flag.group}\n説明: {flag.description}")
                self.def_list.addItem(item)

        StaTableLogger.debug(f"  -> {self.def_list.count()} items displayed")

    def _matches(self, name: str, group: str, query: str) -> bool:
        if not query:
            return True
        q = query.lower()
        return name.lower().startswith(q) or group.lower().startswith(q)

    def insert_definition(self, item: QListWidgetItem):
        name = item.data(Qt.UserRole)
        StaTableLogger.debug(f"ActionEditDialog.insert_definition: '{name}'")
        if name:
            self.action_edit.insertPlainText(name)

    def get_action_text(self) -> str:
        text = self.action_edit.toPlainText().strip()
        StaTableLogger.debug(f"ActionEditDialog.get_action_text: length={len(text)}")
        return text