# statable_gui/literal_definition_dialog.py
"""New literal definition dialog (R-7 support).

Simple dialog for creating a LiteralDefinition, used by
RoleFunctionDialog's "+ New Literal" button.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QDialogButtonBox, QMessageBox,
)

from statable_gui.libcntrl.literal_library import LiteralDefinition


class NewLiteralDialog(QDialog):
    """Dialog to create a new LiteralDefinition."""

    TYPES = ["int", "float", "bool", "string"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Literal")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.value_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(self.TYPES)
        self.desc_edit = QLineEdit()

        form.addRow("Name:", self.name_edit)
        form.addRow("Value:", self.value_edit)
        form.addRow("Type:", self.type_combo)
        form.addRow("Description:", self.desc_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Warning", "Name is required.")
            return
        if not self.value_edit.text().strip():
            QMessageBox.warning(self, "Warning", "Value is required.")
            return
        self.accept()

    def get_literal(self) -> LiteralDefinition:
        return LiteralDefinition(
            name=self.name_edit.text().strip(),
            value=self.value_edit.text().strip(),
            literal_type=self.type_combo.currentText(),
            description=self.desc_edit.text().strip(),
        )