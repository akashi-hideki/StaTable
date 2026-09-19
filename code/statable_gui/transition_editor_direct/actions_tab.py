# statable_gui/transition_editor_direct/actions_tab.py
"""Actions tab widget (v2.2).

Transition-independent actions (always / before_transitions / after_transitions).
"""

import logging
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QHeaderView, QAbstractItemView, QLabel,
)

from statable.model import ActionStep
from .draft import ActionDraft

logger = logging.getLogger("transition_editor_direct.actions_tab")

COL_ROLE = 0
COL_TRIGGER = 1
COLUMN_COUNT = 2

TRIGGER_CHOICES = ["always", "before_transitions", "after_transitions"]


class ActionsTab(QWidget):
    """Actions tab: cell-level actions."""
    actions_changed = Signal()

    def __init__(self, draft: ActionDraft,
                 role_functions: Optional[List[str]] = None,
                 global_defs=None, state_machine=None, parent=None):
        super().__init__(parent)
        self.draft = draft
        self.role_functions = role_functions or []
        self.global_defs = global_defs
        self.state_machine = state_machine

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            "Cell actions (executed independent of transitions)")
        layout.addWidget(info)

        self.table = QTableWidget(0, COLUMN_COUNT)
        self.table.setHorizontalHeaderLabels(["Role function", "Trigger"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("+ Add")
        add_btn.clicked.connect(lambda: self.add_action())
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(lambda: self.delete_action(
            self.table.currentRow()))
        up_btn = QPushButton("Move Up")
        up_btn.clicked.connect(lambda: self.move_up(
            self.table.currentRow()))
        down_btn = QPushButton("Move Down")
        down_btn.clicked.connect(lambda: self.move_down(
            self.table.currentRow()))

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(up_btn)
        btn_layout.addWidget(down_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def row_count(self) -> int:
        return self.table.rowCount()

    def _emit_changed(self):
        self.actions_changed.emit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_action(self, action: Optional[ActionStep] = None) -> int:
        row = self.table.rowCount()
        self.table.insertRow(row)

        role = action.role_function if action else ""
        role_item = QTableWidgetItem(role)
        self.table.setItem(row, COL_ROLE, role_item)

        trigger_combo = QComboBox()
        trigger_combo.addItems(TRIGGER_CHOICES)
        if action is not None and action.trigger in TRIGGER_CHOICES:
            trigger_combo.setCurrentText(action.trigger)
        self.table.setCellWidget(row, COL_TRIGGER, trigger_combo)

        self._emit_changed()
        return row

    def delete_action(self, row: int) -> None:
        if 0 <= row < self.table.rowCount():
            self.table.removeRow(row)
            self._emit_changed()

    def move_up(self, row: int) -> int:
        if row <= 0 or row >= self.table.rowCount():
            return row
        self._swap_rows(row, row - 1)
        self._emit_changed()
        return row - 1

    def move_down(self, row: int) -> int:
        if row < 0 or row >= self.table.rowCount() - 1:
            return row
        self._swap_rows(row, row + 1)
        self._emit_changed()
        return row + 1

    def _swap_rows(self, r1: int, r2: int):
        for col in range(self.table.columnCount()):
            if col == COL_TRIGGER:
                w1 = self.table.cellWidget(r1, col)
                w2 = self.table.cellWidget(r2, col)
                if w1 is not None and w2 is not None:
                    t1 = w1.currentText()
                    t2 = w2.currentText()
                    w1.setCurrentText(t2)
                    w2.setCurrentText(t1)
            else:
                i1 = self.table.takeItem(r1, col)
                i2 = self.table.takeItem(r2, col)
                self.table.setItem(r1, col, i2)
                self.table.setItem(r2, col, i1)

    def get_actions(self) -> List[ActionStep]:
        result = []
        for row in range(self.table.rowCount()):
            role_item = self.table.item(row, COL_ROLE)
            role = role_item.text().strip() if role_item else ""

            trigger_combo = self.table.cellWidget(row, COL_TRIGGER)
            trigger = "always"
            if trigger_combo is not None:
                trigger = trigger_combo.currentText().strip() or "always"

            result.append(ActionStep(
                role_function=role,
                trigger=trigger,
                title=role or "(untitled action)",
            ))
        return result

    def set_actions(self, actions: List[ActionStep]) -> None:
        self.table.setRowCount(0)
        for a in actions:
            self.add_action(a)