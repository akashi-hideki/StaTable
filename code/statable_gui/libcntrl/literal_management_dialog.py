# statable_gui/libcntrl/literal_management_dialog.py
"""
Literal management dialog (table format, edit-fixed version)
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QLineEdit, QFormLayout, QDialogButtonBox,
    QHeaderView
)
from PySide6.QtCore import Qt

from .literal_library import LiteralLibrary, LiteralDefinition


class LiteralManagementDialog(QDialog):
    """Shared literal management dialog"""

    def __init__(self, literal_library: LiteralLibrary, parent=None):
        super().__init__(parent)
        self.literal_library = literal_library

        self.setWindowTitle("Literal management")
        self.setMinimumSize(600, 400)

        self._setup_ui()
        self._load_table()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Name", "Value", "Type", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        main_layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_literal)
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._edit_literal)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_literal)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        main_layout.addLayout(btn_layout)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        main_layout.addWidget(close_btn)

    def _load_table(self):
        self.table.setRowCount(0)
        for lit in self.literal_library.list_all():
            row = self.table.rowCount()
            self.table.insertRow(row)

            name_item = QTableWidgetItem(lit.name)
            name_item.setData(Qt.UserRole, lit.name)
            self.table.setItem(row, 0, name_item)

            self.table.setItem(row, 1, QTableWidgetItem(lit.value))
            self.table.setItem(row, 2, QTableWidgetItem(lit.literal_type))
            self.table.setItem(row, 3, QTableWidgetItem(lit.description))

    def _get_selected_literal_name(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if item:
            return item.data(Qt.UserRole)
        return None

    def _add_literal(self):
        dialog = LiteralEditDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            lit = dialog.get_literal()
            try:
                self.literal_library.add(lit)
                self._load_table()
            except ValueError as e:
                QMessageBox.warning(self, "Warning", str(e))

    def _edit_literal(self):
        name = self._get_selected_literal_name()
        if name is None:
            QMessageBox.information(self, "Info", "Please select a literal to edit.")
            return

        lit = self.literal_library.get(name)
        if lit is None:
            return

        dialog = LiteralEditDialog(literal=lit, parent=self)
        if dialog.exec() == QDialog.Accepted:
            new_lit = dialog.get_literal()

            # On edit, always delete the old entry before adding
            self.literal_library.remove(name)
            try:
                self.literal_library.add(new_lit)
                self._load_table()
            except ValueError as e:
                # If failure occurs, revert
                self.literal_library.add(lit)
                QMessageBox.warning(self, "Warning", str(e))

    def _delete_literal(self):
        name = self._get_selected_literal_name()
        if name is None:
            QMessageBox.information(self, "Info", "Please select a literal to delete.")
            return

        ret = QMessageBox.warning(
            self,
            "Confirm",
            f"Literal '{name}': confirm delete?\n"
            "If any transition condition uses this literal,\n"
            "It must also be removed from the relevant condition expression.",
            QMessageBox.Yes | QMessageBox.No
        )
        if ret == QMessageBox.Yes:
            self.literal_library.remove(name)
            self._load_table()


class LiteralEditDialog(QDialog):
    """Dialog for adding / editing literals"""

    def __init__(self, literal: LiteralDefinition = None, parent=None):
        super().__init__(parent)
        self.literal = literal

        self.setWindowTitle("LiteralEdit" if literal else "LiteralAdd")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        if literal:
            self.name_edit.setText(literal.name)
        form.addRow("Name:", self.name_edit)

        self.value_edit = QLineEdit()
        if literal:
            self.value_edit.setText(literal.value)
        form.addRow("Value:", self.value_edit)

        self.type_edit = QLineEdit("int")
        if literal:
            self.type_edit.setText(literal.literal_type)
        form.addRow("Type:", self.type_edit)

        self.desc_edit = QLineEdit()
        if literal:
            self.desc_edit.setText(literal.description)
        form.addRow("Description:", self.desc_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Warning", "Please enter a name.")
            return
        self.accept()

    def get_literal(self) -> LiteralDefinition:
        return LiteralDefinition(
            name=self.name_edit.text().strip(),
            value=self.value_edit.text().strip(),
            literal_type=self.type_edit.text().strip() or "int",
            description=self.desc_edit.text().strip(),
        )