# statable_gui/transition_editor_direct/transitions_tab.py
"""Transitions tab widget (v2.2).

Ordered list of transitions with Mode (Commit / Tentative).
"""

import logging
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QHeaderView, QAbstractItemView, QLabel,
)

from statable.model import Transition
from .draft import ActionDraft

logger = logging.getLogger("transition_editor_direct.transitions_tab")

# Column indices
COL_ORDER = 0
COL_LABEL = 1
COL_CONDITION = 2
COL_TARGET = 3
COL_ELSE_TARGET = 4
COL_HAS_ELSE = 5
COL_MODE = 6
COLUMN_COUNT = 7


class TransitionsTab(QWidget):
    """Transitions tab: ordered list of transitions in the current cell.

    Priority = row order. Row 0 is evaluated first.
    Mode column: "Commit" (early_return=True) / "Tentative" (False).
    """
    transitions_changed = Signal()

    def __init__(self, draft: ActionDraft, states: Optional[List[str]] = None,
                 global_defs=None, state_machine=None, parent=None):
        super().__init__(parent)
        self.draft = draft
        self.states = states or []
        self.global_defs = global_defs
        self.state_machine = state_machine

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            "Transitions in this cell (top = highest priority, evaluated first)")
        layout.addWidget(info)

        self.table = QTableWidget(0, COLUMN_COUNT)
        self.table.setHorizontalHeaderLabels([
            "#", "Label", "Condition", "Target", "Else target",
            "Has else", "Mode",
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("+ Add")
        add_btn.clicked.connect(lambda: self.add_transition())
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(lambda: self.delete_transition(
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

    # ------------------------------------------------------------------
    # Row helpers
    # ------------------------------------------------------------------
    def row_count(self) -> int:
        return self.table.rowCount()

    def _refresh_priority_column(self):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, COL_ORDER)
            if item is None:
                item = QTableWidgetItem()
                self.table.setItem(row, COL_ORDER, item)
            item.setText(str(row + 1))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)

    def _emit_changed(self):
        self._refresh_priority_column()
        self.transitions_changed.emit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_transition(self, trans: Optional[Transition] = None) -> int:
        row = self.table.rowCount()
        self.table.insertRow(row)

        # 0: priority (auto)
        order_item = QTableWidgetItem(str(row + 1))
        order_item.setFlags(order_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, COL_ORDER, order_item)

        # 1: label
        label = getattr(trans, 'label', '') if trans else ""
        if not label:
            label = f"T{row + 1}"
        label_item = QTableWidgetItem(label)
        self.table.setItem(row, COL_LABEL, label_item)

        # 2: condition
        cond = getattr(trans, 'condition', '') if trans else ""
        cond_item = QTableWidgetItem(cond)
        self.table.setItem(row, COL_CONDITION, cond_item)

        # 3: target
        target_item = QTableWidgetItem(
            getattr(trans, 'target', '') if trans else "")
        self.table.setItem(row, COL_TARGET, target_item)

        # 4: else target
        else_target = getattr(trans, 'else_target', '') if trans else ""
        et_item = QTableWidgetItem(else_target)
        self.table.setItem(row, COL_ELSE_TARGET, et_item)

        # 5: has else
        has_else = getattr(trans, 'has_else', True) if trans else True
        he_item = QTableWidgetItem("Yes" if has_else else "No")
        self.table.setItem(row, COL_HAS_ELSE, he_item)

        # 6: mode (combo)
        mode_combo = QComboBox()
        mode_combo.addItems(["Commit", "Tentative"])
        if trans is not None and getattr(trans, 'early_return', False):
            mode_combo.setCurrentText("Commit")
        else:
            mode_combo.setCurrentText("Tentative")
        self.table.setCellWidget(row, COL_MODE, mode_combo)

        self._emit_changed()
        return row

    def delete_transition(self, row: int) -> None:
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
            if col == COL_MODE:
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

    def get_transitions(self) -> List[Transition]:
        result = []
        source = self.draft.source
        event = self.draft.event
        for row in range(self.table.rowCount()):
            label_item = self.table.item(row, COL_LABEL)
            label = label_item.text().strip() if label_item else ""

            cond_item = self.table.item(row, COL_CONDITION)
            cond = cond_item.text().strip() if cond_item else ""

            target_item = self.table.item(row, COL_TARGET)
            target = target_item.text().strip() if target_item else ""

            et_item = self.table.item(row, COL_ELSE_TARGET)
            else_target = et_item.text().strip() if et_item else ""

            he_item = self.table.item(row, COL_HAS_ELSE)
            has_else = True
            if he_item:
                has_else = he_item.text().strip().lower() in ("yes", "true", "1")

            mode_combo = self.table.cellWidget(row, COL_MODE)
            early_return = False
            if mode_combo is not None:
                early_return = (mode_combo.currentText().strip() == "Commit")

            result.append(Transition(
                source=source,
                event=event,
                condition=cond,
                target=target,
                has_else=has_else,
                else_target=else_target,
                else_actions=[],  # Edited elsewhere
                pre_actions=[],    # Edited elsewhere
                early_return=early_return,
                label=label,
                title="(untitled transition)",
            ))
        return result

    def set_transitions(self, transitions: List[Transition]) -> None:
        self.table.setRowCount(0)
        for t in transitions:
            self.add_transition(t)
        self._refresh_priority_column()