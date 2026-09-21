# statable_gui/transition_editor_direct/relations_tab.py
"""Relations tab widget (v2.2).

Sequential / Exclusive / Group relations between transitions.
Editing is done via RelationsEditDialog.

[v2.2 enhancement]
  - Members list shows "T1: cond_A -> Active" so labels are identifiable.
  - set_transitions() lets the dialog pass transition details.

[v2.3.1 fix]
  - Add setEditTriggers(NoEditTriggers) to prevent inline edit from
    swallowing subsequent double-clicks. Same fix as transitions_tab.py.
"""

import logging
from typing import List, Optional, Dict

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
        # v2.2: {label: "cond_A -> Active"} populated by set_transitions()
        self.member_details: Dict[str, str] = {}
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
        # [v2.3.1 fix] Disable inline editing so that double-click always
        #              triggers the edit dialog.
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
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
    # Member details (called by dialog.py)
    # ------------------------------------------------------------------
    def set_member_details(self, details: Dict[str, str]):
        """Update the {label: 'cond -> target'} map.

        Called by ActionEditorDialog whenever transitions change.
        """
        self.member_details = dict(details or {})

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

    def _make_item(self, text: str) -> QTableWidgetItem:
        """Create a non-editable table item."""
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item

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
                member_details=self.member_details,
            )
            if dlg.exec() != RelationsEditDialog.Accepted:
                return -1
            relation = dlg.get_relation()

        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, COL_KIND, self._make_item(relation.kind))
        self.table.setItem(row, COL_MEMBERS,
                           self._make_item(", ".join(relation.members)))
        self.table.setItem(row, COL_SHARED,
                           self._make_item(relation.shared_condition))
        self.table.setItem(row, COL_NOTE, self._make_item(relation.note))

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
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, COL_KIND, self._make_item(r.kind))
            self.table.setItem(row, COL_MEMBERS,
                               self._make_item(", ".join(r.members)))
            self.table.setItem(row, COL_SHARED,
                               self._make_item(r.shared_condition))
            self.table.setItem(row, COL_NOTE, self._make_item(r.note))

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
            member_details=self.member_details,
        )
        if dlg.exec() != RelationsEditDialog.Accepted:
            return

        new_r = dlg.get_relation()
        self.table.setItem(row, COL_KIND, self._make_item(new_r.kind))
        self.table.setItem(row, COL_MEMBERS,
                           self._make_item(", ".join(new_r.members)))
        self.table.setItem(row, COL_SHARED,
                           self._make_item(new_r.shared_condition))
        self.table.setItem(row, COL_NOTE, self._make_item(new_r.note))
        self.relations_changed.emit()