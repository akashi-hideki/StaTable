# statable_gui/transition_editor_direct/transition_actions_dialog.py
"""Dialog to edit pre_actions / else_actions for one transition (v2.2)."""

import logging
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QListWidget, QListWidgetItem, QDialogButtonBox, QGroupBox,
)

logger = logging.getLogger("transition_editor_direct.transition_actions_dialog")


class TransitionActionsDialog(QDialog):
    """Edit pre_actions and else_actions for a single transition.

    Provides two list widgets with [+ Add] / [Delete] buttons.
    The add button uses a combo box populated from the role function library.
    """

    def __init__(self, parent=None,
                 label: str = "",
                 pre_actions: List[str] = None,
                 else_actions: List[str] = None,
                 role_functions: List[str] = None):
        super().__init__(parent)
        self.label = label or "(unnamed)"
        self.role_functions = role_functions or []

        self.setWindowTitle(f"Edit actions: {self.label}")
        self.setMinimumSize(500, 450)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            f"Transition: {self.label}\n"
            "Set role functions executed before / after the transition."))

        # ---- Pre-actions group ----
        pre_group = QGroupBox("Pre-actions (executed before next_state assignment)")
        pre_layout = QVBoxLayout(pre_group)
        self.pre_list = QListWidget()
        for a in (pre_actions or []):
            self.pre_list.addItem(a)
        pre_layout.addWidget(self.pre_list)

        pre_btn = QHBoxLayout()
        self.pre_combo = QComboBox()
        self.pre_combo.setEditable(True)
        self.pre_combo.addItems(self.role_functions)
        pre_btn.addWidget(self.pre_combo, stretch=1)
        pre_add = QPushButton("+ Add")
        pre_add.clicked.connect(lambda: self._add(self.pre_list, self.pre_combo))
        pre_btn.addWidget(pre_add)
        pre_del = QPushButton("Delete")
        pre_del.clicked.connect(lambda: self._del(self.pre_list))
        pre_btn.addWidget(pre_del)
        pre_layout.addLayout(pre_btn)
        layout.addWidget(pre_group)

        # ---- Else-actions group ----
        else_group = QGroupBox("Else-actions (executed in the else branch)")
        else_layout = QVBoxLayout(else_group)
        self.else_list = QListWidget()
        for a in (else_actions or []):
            self.else_list.addItem(a)
        else_layout.addWidget(self.else_list)

        else_btn = QHBoxLayout()
        self.else_combo = QComboBox()
        self.else_combo.setEditable(True)
        self.else_combo.addItems(self.role_functions)
        else_btn.addWidget(self.else_combo, stretch=1)
        else_add = QPushButton("+ Add")
        else_add.clicked.connect(lambda: self._add(self.else_list, self.else_combo))
        else_btn.addWidget(else_add)
        else_del = QPushButton("Delete")
        else_del.clicked.connect(lambda: self._del(self.else_list))
        else_btn.addWidget(else_del)
        else_layout.addLayout(else_btn)
        layout.addWidget(else_group)

        # ---- OK / Cancel ----
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _add(self, list_widget: QListWidget, combo: QComboBox):
        name = combo.currentText().strip()
        if not name:
            return
        list_widget.addItem(name)
        logger.debug(f"Added: {name}")

    def _del(self, list_widget: QListWidget):
        row = list_widget.currentRow()
        if row >= 0:
            list_widget.takeItem(row)

    def get_pre_actions(self) -> List[str]:
        return [self.pre_list.item(i).text()
                for i in range(self.pre_list.count())]

    def get_else_actions(self) -> List[str]:
        return [self.else_list.item(i).text()
                for i in range(self.else_list.count())]