# statable_gui/transition_editor_direct/relations_edit_dialog.py
"""Dialog to edit one TransitionRelation (v2.2)."""

import logging
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QListWidget, QListWidgetItem, QDialogButtonBox,
    QGroupBox,
)

from statable.model import TransitionRelation

logger = logging.getLogger("transition_editor_direct.relations_edit_dialog")

KIND_CHOICES = ["sequential", "exclusive", "group"]


class RelationsEditDialog(QDialog):
    """Edit a single relation (kind / members / shared_condition)."""

    def __init__(self, parent=None,
                 relation: Optional[TransitionRelation] = None,
                 available_labels: Optional[List[str]] = None):
        super().__init__(parent)
        self.setWindowTitle("Edit relation")
        self.setMinimumSize(500, 450)

        self.available_labels = list(available_labels or [])

        layout = QVBoxLayout(self)

        # ---- Kind ----
        kind_layout = QHBoxLayout()
        kind_layout.addWidget(QLabel("Kind:"))
        self.kind_combo = QComboBox()
        self.kind_combo.addItems(KIND_CHOICES)
        kind_layout.addWidget(self.kind_combo)
        kind_layout.addStretch()
        layout.addLayout(kind_layout)

        # ---- Members (checkbox list) ----
        members_group = QGroupBox("Members (Transition labels)")
        members_layout = QVBoxLayout(members_group)
        self.members_list = QListWidget()
        for lbl in self.available_labels:
            item = QListWidgetItem(lbl)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.members_list.addItem(item)
        members_layout.addWidget(self.members_list)

        if not self.available_labels:
            hint = QLabel(
                "No transitions defined in this cell. "
                "Add transitions first.")
            hint.setStyleSheet("color: #a00;")
            members_layout.addWidget(hint)
        layout.addWidget(members_group)

        # ---- Shared condition ----
        cond_group = QGroupBox("Shared condition (used when kind = group)")
        cond_layout = QVBoxLayout(cond_group)
        self.shared_edit = QLineEdit()
        self.shared_edit.setPlaceholderText("e.g. cond_A")
        cond_layout.addWidget(self.shared_edit)
        layout.addWidget(cond_group)

        # ---- Note ----
        note_layout = QHBoxLayout()
        note_layout.addWidget(QLabel("Note:"))
        self.note_edit = QLineEdit()
        note_layout.addWidget(self.note_edit)
        layout.addLayout(note_layout)

        # ---- OK / Cancel ----
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Load
        if relation is not None:
            self._load(relation)

    def _load(self, relation: TransitionRelation):
        kind = relation.kind if relation.kind in KIND_CHOICES else "sequential"
        self.kind_combo.setCurrentText(kind)
        self.shared_edit.setText(relation.shared_condition or "")
        self.note_edit.setText(relation.note or "")

        selected = set(relation.members or [])
        for i in range(self.members_list.count()):
            item = self.members_list.item(i)
            if item.text() in selected:
                item.setCheckState(Qt.Checked)

    def _on_accept(self):
        members = self.get_members()
        kind = self.kind_combo.currentText()
        if kind == "group" and not members:
            # Group requires at least one member
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "Warning",
                "A group relation requires at least one member.")
            return
        self.accept()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_members(self) -> List[str]:
        result = []
        for i in range(self.members_list.count()):
            item = self.members_list.item(i)
            if item.checkState() == Qt.Checked:
                result.append(item.text())
        return result

    def get_relation(self) -> TransitionRelation:
        return TransitionRelation(
            kind=self.kind_combo.currentText(),
            members=self.get_members(),
            shared_condition=self.shared_edit.text().strip(),
            note=self.note_edit.text().strip(),
        )