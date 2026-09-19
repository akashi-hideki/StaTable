# statable_gui/transition_editor_direct/relations_tab.py
"""Relations tab widget (v2.2).

Sequential / Exclusive / Group relations between transitions.
Editing is done via RelationsEditDialog.
"""

import logging
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QAbstractItemView, QLabel, QMessageBox,
)

from statable.model import TransitionRelation
from .draft import ActionDraft
from .relations_edit_dialog import RelationsEditDialog

logger = logging.getLogger("transition_editor_direct.relations_tab")

COL_KIND = 0
COL_MEMBERS = 1
COL_SHARED = 2
COL_NOTE = 3
COLUMN_COUNT = 4


class RelationsTab(QWidget):
    """Relations tab."""

    relations_changed = Signal()

    def __init__(self, draft: ActionDraft, parent=None):
        super().__init__(parent)
        self.draft = draft
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            "Relations between transitions in this cell.\n"
            "  sequential: evaluate members in order\n"
            "  exclusive : at most one fires\n"
            "  group     : hoists shared_condition as outer if")
        layout.addWidget(info)

        self.table = QTableWidget(0, COLUMN_COUNT)
        self.table.setHorizontalHeaderLabels(
            ["Kind", "Members", "Shared condition", "Note"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.cellDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("+ Add")
        add_btn.clicked.connect(lambda: self._add())
        edit_btn = QPushButton("Edit...")
        edit_btn.clicked.connect(lambda: self._edit(self.table.currentRow()))
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(lambda: self.delete_relation(
            self.table.currentRow()))

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Available labels (from current cell's transitions)
    # ------------------------------------------------------------------
    def _get_available_labels(self) -> List[str]:
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
    def row_count(self) -> int:
        return self.table.rowCount()

    def add_relation(self, relation: Optional[TransitionRelation] = None) -> int:
        """Add a relation. If relation is None, opens the edit dialog first."""
        if relation is None:
            available = self._get_available_labels()
            if not available:
                QMessageBox.warning(
                    self, "Warning",
                    "No transitions defined in this cell.\n"
                    "Add transitions first.")
                return -1
            dlg = RelationsEditDialog(
                parent=self,
                relation=None,
                available_labels=available,
            )
            if dlg.exec() != RelationsEditDialog.Accepted:
                return -1
            relation = dlg.get_relation()

        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, COL_KIND, QTableWidgetItem(relation.kind))
        self.table.setItem(row, COL_MEMBERS,
                           QTableWidgetItem(", ".join(relation.members)))
        self.table.setItem(row, COL_SHARED,
                           QTableWidgetItem(relation.shared_condition))
        self.table.setItem(row, COL_NOTE, QTableWidgetItem(relation.note))

        self.relations_changed.emit()
        return row

    def delete_relation(self, row: int) -> None:
        if 0 <= row < self.table.rowCount():
            self.table.removeRow(row)
            self.relations_changed.emit()

    def get_relations(self) -> List[TransitionRelation]:
        result = []
        for row in range(self.table.rowCount()):
            def _txt(col: int) -> str:
                it = self.table.item(row, col)
                return it.text().strip() if it else ""

            members = [m.strip() for m in _txt(COL_MEMBERS).split(",")
                       if m.strip()]
            result.append(TransitionRelation(
                kind=_txt(COL_KIND) or "sequential",
                members=members,
                shared_condition=_txt(COL_SHARED),
                note=_txt(COL_NOTE),
            ))
        return result

    def set_relations(self, relations: List[TransitionRelation]) -> None:
        self.table.setRowCount(0)
        for r in relations:
            # Bypass the dialog for programmatic setting
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, COL_KIND, QTableWidgetItem(r.kind))
            self.table.setItem(row, COL_MEMBERS,
                               QTableWidgetItem(", ".join(r.members)))
            self.table.setItem(row, COL_SHARED,
                               QTableWidgetItem(r.shared_condition))
            self.table.setItem(row, COL_NOTE, QTableWidgetItem(r.note))

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------
    def _on_double_click(self, row: int, col: int):
        self._edit(row)

    def _add(self):
        self.add_relation(None)

    def _edit(self, row: int):
        if row < 0 or row >= self.table.rowCount():
            return

        # Reconstruct the relation from the row
        def _txt(col: int) -> str:
            it = self.table.item(row, col)
            return it.text().strip() if it else ""

        current = TransitionRelation(
            kind=_txt(COL_KIND) or "sequential",
            members=[m.strip() for m in _txt(COL_MEMBERS).split(",")
                     if m.strip()],
            shared_condition=_txt(COL_SHARED),
            note=_txt(COL_NOTE),
        )

        available = self._get_available_labels()
        dlg = RelationsEditDialog(
            parent=self,
            relation=current,
            available_labels=available,
        )
        if dlg.exec() != RelationsEditDialog.Accepted:
            return

        new_r = dlg.get_relation()
        self.table.setItem(row, COL_KIND, QTableWidgetItem(new_r.kind))
        self.table.setItem(row, COL_MEMBERS,
                           QTableWidgetItem(", ".join(new_r.members)))
        self.table.setItem(row, COL_SHARED,
                           QTableWidgetItem(new_r.shared_condition))
        self.table.setItem(row, COL_NOTE, QTableWidgetItem(new_r.note))
        self.relations_changed.emit()