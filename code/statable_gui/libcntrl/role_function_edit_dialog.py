# statable_gui/libcntrl/role_function_edit_dialog.py
"""
Edit role function dialog
"""

from typing import List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QListWidget, QListWidgetItem, QDialogButtonBox, QGroupBox
)
from PySide6.QtCore import Qt

from .role_function_library import RoleFunction


class RoleFunctionEditDialog(QDialog):
    """Shared role function edit dialog"""

    def __init__(self, role_function: RoleFunction,
                 global_vars: List[str] = None,
                 events: List[str] = None,
                 literals: List[str] = None,
                 parent=None):
        super().__init__(parent)
        self.role_function = role_function
        self.global_vars = global_vars or []
        self.events = events or []
        self.literals = literals or []

        self.setWindowTitle("Edit role function")
        self.setMinimumWidth(500)

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        form = QFormLayout()
        self.name_edit = QLineEdit()
        form.addRow("Function name:", self.name_edit)
        self.title_edit = QLineEdit()
        form.addRow("Display name:", self.title_edit)
        self.desc_edit = QLineEdit()
        form.addRow("Description:", self.desc_edit)
        main_layout.addLayout(form)

        # Used global variables
        global_group = QGroupBox("Used global variables")
        global_layout = QVBoxLayout(global_group)
        self.global_list = QListWidget()
        self.global_list.setSelectionMode(QListWidget.NoSelection)
        for var in self.global_vars:
            item = QListWidgetItem(var)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.global_list.addItem(item)
        global_layout.addWidget(self.global_list)
        main_layout.addWidget(global_group)

        # Used events
        event_group = QGroupBox("Used events")
        event_layout = QVBoxLayout(event_group)
        self.event_list = QListWidget()
        self.event_list.setSelectionMode(QListWidget.NoSelection)
        for event in self.events:
            item = QListWidgetItem(event)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.event_list.addItem(item)
        event_layout.addWidget(self.event_list)
        main_layout.addWidget(event_group)

        # Used literals
        literal_group = QGroupBox("Used literals (select from existing)")
        literal_layout = QVBoxLayout(literal_group)
        self.literal_list = QListWidget()
        self.literal_list.setSelectionMode(QListWidget.NoSelection)
        for lit in self.literals:
            item = QListWidgetItem(lit)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.literal_list.addItem(item)
        literal_layout.addWidget(self.literal_list)
        main_layout.addWidget(literal_group)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def _load_data(self):
        self.name_edit.setText(self.role_function.name)
        self.title_edit.setText(self.role_function.title)
        self.desc_edit.setText(self.role_function.description)

        for i in range(self.global_list.count()):
            item = self.global_list.item(i)
            if item.text() in self.role_function.used_global_vars:
                item.setCheckState(Qt.Checked)

        for i in range(self.event_list.count()):
            item = self.event_list.item(i)
            if item.text() in self.role_function.used_events:
                item.setCheckState(Qt.Checked)

        for i in range(self.literal_list.count()):
            item = self.literal_list.item(i)
            if item.text() in self.role_function.used_literals:
                item.setCheckState(Qt.Checked)

    def _on_accept(self):
        name = self.name_edit.text().strip()
        if not name:
            name = "NewRoleFunction"
        self.role_function.name = name
        self.role_function.title = self.title_edit.text().strip() or name
        self.role_function.description = self.desc_edit.text().strip()

        used_global_vars = []
        for i in range(self.global_list.count()):
            item = self.global_list.item(i)
            if item.checkState() == Qt.Checked:
                used_global_vars.append(item.text())
        self.role_function.used_global_vars = used_global_vars

        used_events = []
        for i in range(self.event_list.count()):
            item = self.event_list.item(i)
            if item.checkState() == Qt.Checked:
                used_events.append(item.text())
        self.role_function.used_events = used_events

        used_literals = []
        for i in range(self.literal_list.count()):
            item = self.literal_list.item(i)
            if item.checkState() == Qt.Checked:
                used_literals.append(item.text())
        self.role_function.used_literals = used_literals

        self.accept()

    def get_role_function(self) -> RoleFunction:
        return self.role_function