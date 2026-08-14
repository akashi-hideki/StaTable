from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QComboBox,
    QPushButton, QLabel, QDialogButtonBox, QMessageBox
)
from PySide6.QtGui import QFont

from .role_function_dialog import RoleFunctionDialog


class ActionEditDialog(QDialog):
    """遷移の動作（ロール関数呼び出し・生コード）を編集するダイアログ"""
    def __init__(self, parent=None, action_text="", role_functions=None):
        super().__init__(parent)
        self.setWindowTitle("動作編集")
        self.setMinimumSize(600, 400)
        self.role_functions = role_functions if role_functions is not None else {}

        layout = QVBoxLayout(self)

        # ロール関数選択・挿入バー
        role_bar = QHBoxLayout()
        role_bar.addWidget(QLabel("ロール関数:"))
        self.role_combo = QComboBox()
        self.refresh_role_combo()
        role_bar.addWidget(self.role_combo)
        insert_btn = QPushButton("挿入")
        insert_btn.clicked.connect(self.insert_role_function)
        role_bar.addWidget(insert_btn)
        new_role_btn = QPushButton("新規ロール関数...")
        new_role_btn.clicked.connect(self.add_new_role_function)
        role_bar.addWidget(new_role_btn)
        layout.addLayout(role_bar)

        # 選択したロール関数のシグネチャ表示
        self.signature_label = QLabel("")
        layout.addWidget(self.signature_label)

        # 動作入力欄
        self.action_edit = QTextEdit()
        self.action_edit.setAcceptRichText(False)
        self.action_edit.setPlainText(action_text)
        self.action_edit.setFont(QFont("Consolas", 10))
        layout.addWidget(self.action_edit)

        # OK/Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.update_signature_label()

    def refresh_role_combo(self):
        self.role_combo.clear()
        for name in self.role_functions.keys():
            self.role_combo.addItem(name)
        self.role_combo.currentTextChanged.connect(self.update_signature_label)

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
        if not func_name:
            return
        rf = self.role_functions.get(func_name)
        if not rf:
            return
        call = f"{func_name}({rf.arg1_name}, {rf.arg2_name});"
        self.action_edit.insertPlainText(call + "\n")

    def add_new_role_function(self):
        dlg = RoleFunctionDialog(self)
        if dlg.exec() == QDialog.Accepted:
            rf = dlg.get_role_function()
            if rf.name in self.role_functions:
                QMessageBox.warning(self, "警告", "同名のロール関数が既に存在します。")
                return
            self.role_functions[rf.name] = rf
            self.refresh_role_combo()
            self.update_signature_label()

    def get_action_text(self) -> str:
        return self.action_edit.toPlainText().strip()