# statable_gui/transition_editor_direct/relations_tab.py
"""Relations tab widget (v2.2).

Sequential / Exclusive / Group relations between transitions.
"""

import logging
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QHeaderView, QAbstractItemView, QLabel,
)

from statable.model import TransitionRelation
from .draft import ActionDraft

logger = logging.getLogger("transition_editor_direct.relations_tab")

COL_KIND = 0
COL_MEMBERS = 1
COL_SHARED = 2
COLUMN_COUNT = 3

KIND_CHOICES = ["sequential", "exclusive", "group"]


class RelationsTab(QWidget):
    """Relations tab: relations between transitions in the current cell."""
    relations_changed = Signal()

    def __init__(self, draft: ActionDraft, parent=None):
        super().__init__(parent)
        self.draft = draft

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            "Relations between transitions "
            "(sequential: order, exclusive: at most one, group: shared condition)")
        layout.addWidget(info)

        self.table = QTableWidget(0, COLUMN_COUNT)
        self.table.setHorizontalHeaderLabels(
            ["Kind", "Members (comma-separated)", "Shared condition"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("+ Add")
        add_btn.clicked.connect(lambda: self.add_relation())
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(lambda: self.delete_relation(
            self.table.currentRow()))

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def row_count(self) -> int:
        return self.table.rowCount()

    def _emit_changed(self):
        self.relations_changed.emit()

    def get_available_labels(self) -> List[str]:
        """Labels of transitions currently defined in the draft."""
        labels = []
        for item in self.draft.flow_items:
            if item.item_type == "transition":
                lbl = item.params.get("label", "")
                if lbl:
                    labels.append(lbl)
        return labels

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_relation(self, relation: Optional[TransitionRelation] = None) -> int:
        row = self.table.rowCount()
        self.table.insertRow(row)

        kind_combo = QComboBox()
        kind_combo.addItems(KIND_CHOICES)
        if relation is not None and relation.kind in KIND_CHOICES:
            kind_combo.setCurrentText(relation.kind)
        self.table.setCellWidget(row, COL_KIND, kind_combo)

        members = relation.members if relation else []
        members_item = QTableWidgetItem(",".join(members))
        self.table.setItem(row, COL_MEMBERS, members_item)

        shared = relation.shared_condition if relation else ""
        shared_item = QTableWidgetItem(shared)
        self.table.setItem(row, COL_SHARED, shared_item)

        self._emit_changed()
        return row

    def delete_relation(self, row: int) -> None:
        if 0 <= row < self.table.rowCount():
            self.table.removeRow(row)
            self._emit_changed()

    def get_relations(self) -> List[TransitionRelation]:
        result = []
        for row in range(self.table.rowCount()):
            kind_combo = self.table.cellWidget(row, COL_KIND)
            kind = "sequential"
            if kind_combo is not None:
                kind = kind_combo.currentText().strip() or "sequential"

            members_item = self.table.item(row, COL_MEMBERS)
            members_text = members_item.text().strip() if members_item else ""
            members = [m.strip() for m in members_text.split(",") if m.strip()]

            shared_item = self.table.item(row, COL_SHARED)
            shared = shared_item.text().strip() if shared_item else ""

            result.append(TransitionRelation(
                kind=kind,
                members=members,
                shared_condition=shared,
                note="",
            ))
        return result

    def set_relations(self, relations: List[TransitionRelation]) -> None:
        self.table.setRowCount(0)
        for r in relations:
            self.add_relation(r)