from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox
)

from statable.model import RoleFunction


class RoleFunctionDialog(QDialog):
    """ロール関数の新規登録・編集用ダイアログ"""
    def __init__(self, parent=None, role_function=None):
        super().__init__(parent)
        self.setWindowTitle("ロール関数編集")
        self.setMinimumWidth(400)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.name_edit.setText(role_function.name if role_function else "")
        layout.addRow("関数名", self.name_edit)

        self.desc_edit = QLineEdit()
        self.desc_edit.setText(role_function.description if role_function else "")
        layout.addRow("説明", self.desc_edit)

        self.return_type_edit = QLineEdit("int")
        self.return_type_edit.setText(role_function.return_type if role_function else "int")
        layout.addRow("戻り値型", self.return_type_edit)

        self.arg1_type_edit = QLineEdit("int")
        self.arg1_type_edit.setText(role_function.arg1_type if role_function else "int")
        layout.addRow("引数1型", self.arg1_type_edit)
        self.arg1_name_edit = QLineEdit("arg1")
        self.arg1_name_edit.setText(role_function.arg1_name if role_function else "arg1")
        layout.addRow("引数1名", self.arg1_name_edit)

        self.arg2_type_edit = QLineEdit("int")
        self.arg2_type_edit.setText(role_function.arg2_type if role_function else "int")
        layout.addRow("引数2型", self.arg2_type_edit)
        self.arg2_name_edit = QLineEdit("arg2")
        self.arg2_name_edit.setText(role_function.arg2_name if role_function else "arg2")
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