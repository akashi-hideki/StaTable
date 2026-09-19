# statable_gui/transition_editor_direct/actions_tab.py
"""Pre / Post Actions tab widget (v2.2).

Two groups:
  - Pre  : before_transitions (executed before the transition chain)
  - Post : after_transitions  (executed after the transition chain)

[v2.2 change]
  - `always` trigger removed; old data migrated to `before_transitions`.
  - Role function input is an editable ComboBox.
"""

import logging
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QHeaderView, QAbstractItemView, QLabel,
    QGroupBox,
)

from statable.model import ActionStep
from .draft import ActionDraft

logger = logging.getLogger("transition_editor_direct.actions_tab")


# Supported triggers (always is deprecated)
TRIGGER_PRE = "before_transitions"
TRIGGER_POST = "after_transitions"

# Migration map
_LEGACY_TRIGGER_MAP = {
    "always": TRIGGER_PRE,   # v2.2: always -> before_transitions
}


def _migrate_trigger(trigger: str) -> str:
    """Migrate legacy trigger names to the new ones."""
    t = (trigger or "").strip()
    if t in _LEGACY_TRIGGER_MAP:
        return _LEGACY_TRIGGER_MAP[t]
    if t in (TRIGGER_PRE, TRIGGER_POST):
        return t
    return TRIGGER_PRE


class _ActionGroup(QGroupBox):
    """A QGroupBox containing a role function list for one trigger."""

    changed = Signal()

    def __init__(self, title: str, trigger: str,
                 role_functions: List[str], parent=None):
        super().__init__(title, parent)
        self.trigger = trigger
        self.role_functions = list(role_functions or [])

        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 1)
        self.table.setHorizontalHeaderLabels(["Role function"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.combo.addItems(self.role_functions)
        btn_layout.addWidget(self.combo, stretch=1)

        add_btn = QPushButton("+ Add")
        add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(add_btn)

        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(del_btn)

        up_btn = QPushButton("Up")
        up_btn.clicked.connect(self._on_move_up)
        btn_layout.addWidget(up_btn)

        down_btn = QPushButton("Down")
        down_btn.clicked.connect(self._on_move_down)
        btn_layout.addWidget(down_btn)

        layout.addLayout(btn_layout)

    def set_role_functions(self, names: List[str]):
        self.role_functions = list(names or [])
        current = self.combo.currentText()
        self.combo.clear()
        self.combo.addItems(self.role_functions)
        if current:
            self.combo.setCurrentText(current)

    def set_actions(self, actions: List[ActionStep]):
        """Replace the list (filtered by trigger)."""
        self.table.setRowCount(0)
        for a in actions:
            if _migrate_trigger(a.trigger) != self.trigger:
                continue
            self._append_row(a.role_function)

    def get_actions(self) -> List[ActionStep]:
        result = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            name = item.text().strip() if item else ""
            if name:
                result.append(ActionStep(
                    role_function=name,
                    trigger=self.trigger,
                    title=name,
                ))
        return result

    def row_count(self) -> int:
        return self.table.rowCount()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------
    def _append_row(self, role_function: str):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(role_function))

    def _on_add(self):
        name = self.combo.currentText().strip()
        if not name:
            return
        self._append_row(name)
        self.changed.emit()

    def _on_delete(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self.changed.emit()

    def _on_move_up(self):
        row = self.table.currentRow()
        if row <= 0:
            return
        self._swap(row, row - 1)
        self.table.setCurrentCell(row - 1, 0)
        self.changed.emit()

    def _on_move_down(self):
        row = self.table.currentRow()
        if row < 0 or row >= self.table.rowCount() - 1:
            return
        self._swap(row, row + 1)
        self.table.setCurrentCell(row + 1, 0)
        self.changed.emit()

    def _swap(self, r1: int, r2: int):
        i1 = self.table.takeItem(r1, 0)
        i2 = self.table.takeItem(r2, 0)
        self.table.setItem(r1, 0, i2)
        self.table.setItem(r2, 0, i1)


class ActionsTab(QWidget):
    """Pre / Post Actions tab."""

    actions_changed = Signal()

    def __init__(self, draft: ActionDraft,
                 role_functions: Optional[List[str]] = None,
                 global_defs=None, state_machine=None, parent=None):
        super().__init__(parent)
        self.draft = draft
        self.role_functions = list(role_functions or [])
        self.global_defs = global_defs
        self.state_machine = state_machine

        self._build_ui()

    def set_role_functions(self, names: List[str]):
        self.role_functions = list(names or [])
        self.pre_group.set_role_functions(self.role_functions)
        self.post_group.set_role_functions(self.role_functions)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Cell-level actions:\n"
            "  Pre  = before the transition chain (runs even if no transition fires)\n"
            "  Post = after the transition chain (runs even after early return)"))

        self.pre_group = _ActionGroup(
            "Pre (before transitions)", TRIGGER_PRE, self.role_functions)
        self.pre_group.changed.connect(self._on_changed)
        layout.addWidget(self.pre_group)

        self.post_group = _ActionGroup(
            "Post (after transitions)", TRIGGER_POST, self.role_functions)
        self.post_group.changed.connect(self._on_changed)
        layout.addWidget(self.post_group)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def row_count(self) -> int:
        """Total rows across both groups (for compatibility)."""
        return self.pre_group.row_count() + self.post_group.row_count()

    def add_action(self, action: Optional[ActionStep] = None) -> int:
        """Add a row to the appropriate group. Returns the row index within that group."""
        if action is None:
            action = ActionStep(role_function="", trigger=TRIGGER_PRE)
        trigger = _migrate_trigger(action.trigger)
        target = self.pre_group if trigger == TRIGGER_PRE else self.post_group
        target._append_row(action.role_function)
        self._on_changed()
        return target.row_count() - 1

    def get_actions(self) -> List[ActionStep]:
        result = []
        result.extend(self.pre_group.get_actions())
        result.extend(self.post_group.get_actions())
        return result

    def set_actions(self, actions: List[ActionStep]) -> None:
        self.pre_group.set_actions(actions or [])
        self.post_group.set_actions(actions or [])

    # Legacy helpers (kept for test compatibility)
    def delete_action(self, row: int) -> None:
        # Interpret row as combined index; delete from the first group first
        pre_count = self.pre_group.row_count()
        if 0 <= row < pre_count:
            self.pre_group.table.setCurrentCell(row, 0)
            self.pre_group._on_delete()
        else:
            post_row = row - pre_count
            if 0 <= post_row < self.post_group.row_count():
                self.post_group.table.setCurrentCell(post_row, 0)
                self.post_group._on_delete()
        self._on_changed()

    def move_up(self, row: int) -> int:
        pre_count = self.pre_group.row_count()
        if 0 <= row < pre_count:
            self.pre_group.table.setCurrentCell(row, 0)
            self.pre_group._on_move_up()
            self._on_changed()
            return max(0, row - 1)
        post_row = row - pre_count
        if 0 <= post_row < self.post_group.row_count():
            self.post_group.table.setCurrentCell(post_row, 0)
            self.post_group._on_move_up()
            self._on_changed()
            return row - 1 if post_row > 0 else row
        return row

    def _on_changed(self):
        self.actions_changed.emit()