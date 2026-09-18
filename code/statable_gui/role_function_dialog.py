from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox
)

from statable.model import RoleFunction
from .logger import StaTableLogger


class RoleFunctionDialog(QDialog):
    """Dialog for creating / editing role functions"""
    def __init__(self, parent=None, role_function=None):
        super().__init__(parent)
        self.setWindowTitle("Edit role function")
        self.setMinimumWidth(450)
        layout = QFormLayout(self)

        # Title input field (required / provisional title auto-set)
        self.title_edit = QLineEdit()
        self.title_edit.setText(role_function.title if role_function else "")
        self.title_edit.setPlaceholderText("Label shown in the list (auto-set if empty)")
        self.title_edit.setToolTip("Enter the title of this role function. If empty, a provisional title is set automatically.")
        layout.addRow("Title *", self.title_edit)

        self.name_edit = QLineEdit()
        self.name_edit.setText(role_function.name if role_function else "")
        layout.addRow("Function name", self.name_edit)

        # v1.5 new: namespace input field
        self.namespace_edit = QLineEdit()
        self.namespace_edit.setText(
            role_function.namespace if role_function else ""
        )
        self.namespace_edit.setPlaceholderText("Example: Driver (empty = no layer)")
        self.namespace_edit.setToolTip(
            "Namespace (layer name / feature group name).\n"
            "If specified, it can be referenced as 'Driver.Init'.\n"
            "If empty, it is treated as having no layer ('Init')."
        )
        layout.addRow("Namespace", self.namespace_edit)

        self.desc_edit = QLineEdit()
        self.desc_edit.setText(role_function.description if role_function else "")
        layout.addRow("Description", self.desc_edit)

        self.return_type_edit = QLineEdit("int")
        self.return_type_edit.setText(role_function.return_type if role_function else "int")
        layout.addRow("Return type", self.return_type_edit)

        self.arg1_type_edit = QLineEdit("int")
        self.arg1_type_edit.setText(role_function.arg1_type if role_function else "int")
        layout.addRow("Arg 1 type", self.arg1_type_edit)
        self.arg1_name_edit = QLineEdit("arg1")
        self.arg1_name_edit.setText(role_function.arg1_name if role_function else "arg1")
        layout.addRow("Arg 1 name", self.arg1_name_edit)

        self.arg2_type_edit = QLineEdit("int")
        self.arg2_type_edit.setText(role_function.arg2_type if role_function else "int")
        layout.addRow("Arg 2 type", self.arg2_type_edit)
        self.arg2_name_edit = QLineEdit("arg2")
        self.arg2_name_edit.setText(role_function.arg2_name if role_function else "arg2")
        layout.addRow("Arg 2 name", self.arg2_name_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        StaTableLogger.debug("RoleFunctionDialog initialized")

    def _on_accept(self):
        """OK button: auto-set provisional title if title is empty"""
        if not self.title_edit.text().strip():
            auto_title = f"ロール関数: {self.name_edit.text().strip() or '(unnamed)'}"
            self.title_edit.setText(auto_title)
            StaTableLogger.debug(f"Auto title generated: '{auto_title}'")
        self.accept()

    def get_role_function(self) -> RoleFunction:
        """\n        [v1.5 change]\n          - Set namespace and specify all arguments as kwargs\n          - Since model.py's RoleFunction became kw_only=True,\n            it cannot be constructed with positional arguments.\n        """
        return RoleFunction(
            name=self.name_edit.text().strip(),
            namespace=self.namespace_edit.text().strip(),   # NewAdd
            description=self.desc_edit.text().strip(),
            return_type=self.return_type_edit.text().strip(),
            arg1_type=self.arg1_type_edit.text().strip(),
            arg1_name=self.arg1_name_edit.text().strip(),
            arg2_type=self.arg2_type_edit.text().strip(),
            arg2_name=self.arg2_name_edit.text().strip(),
            title=self.title_edit.text().strip(),
        )