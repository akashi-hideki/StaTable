# statable_gui/transition_editor_direct/relations_edit_dialog.py
"""Dialog to edit one TransitionRelation (v2.2).

[v2.2 enhancement]
  - Members list shows each transition as "T1: cond_A -> Active"
    so the user can identify which label belongs to which condition.
"""

import logging
from typing import List, Optional, Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QListWidget, QListWidgetItem, QDialogButtonBox,
    QGroupBox, QMessageBox,
)

from statable.model import TransitionRelation

logger = logging.getLogger("transition_editor_direct.relations_edit_dialog")

KIND_CHOICES = ["sequential", "exclusive", "group"]


def _fmt_member(label: str, detail: str) -> str:
    """Format a member list entry: 'T1: cond_A -> Active'."""
    if detail:
        return f"{label}: {detail}"
    return label


class RelationsEditDialog(QDialog):
    """Edit a single relation (kind / members / shared_condition)."""

    def __init__(self, parent=None,
                 relation: Optional[TransitionRelation] = None,
                 available_labels: Optional[List[str]] = None,
                 member_details: Optional[Dict[str, str]] = None):
        """
        Args:
            relation: existing relation (None for new)
            available_labels: list of Transition labels in this cell
            member_details: {label: "cond_A -> Active"} for display
        """
        super().__init__(parent)
        self.setWindowTitle("Edit relation")
        self.setMinimumSize(600, 500)

        self.available_labels = list(available_labels or [])
        self.member_details = dict(member_details or {})

        layout = QVBoxLayout(self)

        # ---- Kind ----
        kind_layout = QHBoxLayout()
        kind_layout.addWidget(QLabel("Kind:"))
        self.kind_combo = QComboBox()
        self.kind_combo.addItems(KIND_CHOICES)
        kind_layout.addWidget(self.kind_combo)
        kind_layout.addStretch()
        layout.addLayout(kind_layout)

        # ---- Members (checkbox list with condition/target) ----
        members_group = QGroupBox("Members (Transition labels)")
        members_layout = QVBoxLayout(members_group)
        self.members_list = QListWidget()
        for lbl in self.available_labels:
            detail = self.member_details.get(lbl, "")
            text = _fmt_member(lbl, detail)
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, lbl)   # store the raw label
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            if detail:
                item.setToolTip(f"{lbl}\n{detail}")
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
            raw_label = item.data(Qt.UserRole) or item.text()
            if raw_label in selected:
                item.setCheckState(Qt.Checked)

    def _on_accept(self):
        members = self.get_members()
        kind = self.kind_combo.currentText()
        if kind == "group" and not members:
            QMessageBox.warning(
                self, "Warning",
                "A group relation requires at least one member.")
            return
        self.accept()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_members(self) -> List[str]:
        """Return only the raw labels (T1, T2, ...)."""
        result = []
        for i in range(self.members_list.count()):
            item = self.members_list.item(i)
            if item.checkState() == Qt.Checked:
                label = item.data(Qt.UserRole) or item.text()
                result.append(label)
        return result

    def get_relation(self) -> TransitionRelation:
        return TransitionRelation(
            kind=self.kind_combo.currentText(),
            members=self.get_members(),
            shared_condition=self.shared_edit.text().strip(),
            note=self.note_edit.text().strip(),
        )