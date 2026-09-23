# statable_gui/condition_template_dialog.py
"""New condition template dialog (R-8 support).

Simple dialog for creating a ConditionTemplate, used by
ConditionBuilderDialog's "+ New Template" button.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QMessageBox,
)

from statable_gui.libcntrl.condition_library import ConditionTemplate


class NewConditionTemplateDialog(QDialog):
    """Dialog to create a new ConditionTemplate."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Condition Template")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.condition_edit = QLineEdit()
        self.condition_edit.setPlaceholderText(
            "Example: err_code != 0")
        self.desc_edit = QLineEdit()

        form.addRow("Name:", self.name_edit)
        form.addRow("Condition:", self.condition_edit)
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
        if not self.condition_edit.text().strip():
            QMessageBox.warning(self, "Warning", "Condition is required.")
            return
        self.accept()

    def get_template(self) -> ConditionTemplate:
        return ConditionTemplate(
            name=self.name_edit.text().strip(),
            condition=self.condition_edit.text().strip(),
            description=self.desc_edit.text().strip(),
        )