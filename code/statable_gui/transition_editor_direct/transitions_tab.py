# statable_gui/transition_editor_direct/transitions_tab.py
"""Transitions tab widget (v2.2, v2.5 new role function button).

Ordered list of transitions with Mode (Commit / Tentative).
- Pre-actions / Else-actions columns (double-click to edit).
- Target / Else target: ComboBox (states + "(none)").
- Has else: ComboBox (Yes / No), linked to Else target enable state.

[v2.5 change]
  - New "+ New Role Function" button.
    Clicking it opens RoleFunctionDialog, registers the resulting
    role function into state_machine.role_functions, and appends
    its qualified_name to self.role_functions. The new name then
    becomes available in the TransitionActionsDialog / 
    ConditionBuilderDialog candidates opened from this tab.
  - New constructor args: role_function_library, literal_library,
    layer_names_provider (all optional / keyword).
"""

import logging
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QHeaderView, QAbstractItemView, QLabel,
    QDialog, QMessageBox,
)

from statable.model import Transition
from statable_gui.role_function_dialog import RoleFunctionDialog
from .draft import ActionDraft
from .transition_actions_dialog import TransitionActionsDialog

logger = logging.getLogger("transition_editor_direct.transitions_tab")

# Column indices
COL_ORDER = 0
COL_LABEL = 1
COL_CONDITION = 2
COL_PRE = 3
COL_TARGET = 4
COL_HAS_ELSE = 5
COL_ELSE_TARGET = 6
COL_ELSE = 7
COL_MODE = 8
COLUMN_COUNT = 9

# Columns that use a QComboBox
WIDGET_COLUMNS = (COL_TARGET, COL_HAS_ELSE, COL_ELSE_TARGET, COL_MODE)

NONE_LABEL = "(none)"


def _qualified_name(rf) -> str:
    """Return qualified_name if available, else fall back to name."""
    qn = getattr(rf, 'qualified_name', None)
    if qn:
        return qn
    return getattr(rf, 'name', '') or ''


class TransitionsTab(QWidget):
    """Transitions tab (priority = row order)."""

    transitions_changed = Signal()

    def __init__(self, draft: ActionDraft, states: Optional[List[str]] = None,
                 global_defs=None, state_machine=None,
                 role_function_library=None,
                 literal_library=None,
                 condition_library=None,
                 layer_names_provider=None,
                 parent=None):
        super().__init__(parent)
        self.draft = draft
        self.states = list(states or [])
        self.global_defs = global_defs
        self.state_machine = state_machine
        self.role_functions: List[str] = []

        # v2.5: context for RoleFunctionDialog
        self.role_function_library = role_function_library
        self.literal_library = literal_library
        self.condition_library = condition_library
        self.layer_names_provider = layer_names_provider

        self._build_ui()

    def set_role_functions(self, names: List[str]):
        self.role_functions = list(names or [])

    def set_states(self, states: List[str]):
        """Replace the state list and rebuild all state combos."""
        self.states = list(states or [])
        for row in range(self.table.rowCount()):
            self._refresh_state_combo(row, COL_TARGET)
            self._refresh_state_combo(row, COL_ELSE_TARGET)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            "Transitions in this cell (top = highest priority, evaluated first)\n"
            "Double-click on the Condition cell to open the condition builder.\n"
            "Double-click on the Pre/Else cell to edit role functions.")
        layout.addWidget(info)

        self.table = QTableWidget(0, COLUMN_COUNT)
        self.table.setHorizontalHeaderLabels([
            "#", "Label", "Condition",
            "Pre-actions", "Target", "Has else",
            "Else target", "Else-actions", "Mode",
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        # [FIX] Disable inline editing so that double-click always triggers
        #       the dialog handler (ConditionBuilderDialog / TransitionActionsDialog).
        #       Without this, Qt starts inline editing after the first dialog
        #       closes, and subsequent double-clicks are swallowed by the
        #       inline editor (cellDoubleClicked no longer fires).
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
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
        edit_actions_btn = QPushButton("Edit actions...")
        edit_actions_btn.clicked.connect(self._edit_actions_current_row)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(up_btn)
        btn_layout.addWidget(down_btn)
        btn_layout.addWidget(edit_actions_btn)

        # v2.5: create a new role function (available in subsequent dialogs)
        new_role_btn = QPushButton("+ New Role Function")
        new_role_btn.setToolTip(
            "Create a new role function.\n"
            "It is registered into the state machine and becomes\n"
            "available in the Pre/Else action dialogs of this tab.")
        new_role_btn.clicked.connect(self._on_new_role_function)
        btn_layout.addWidget(new_role_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # v2.5: role function creation
    # ------------------------------------------------------------------
    def _get_namespace_choices(self) -> List[str]:
        """Build namespace candidates for the RoleFunctionDialog.

        Mirrors SettingsPanel._get_namespace_choices():
          1. layer_names_provider  (all tabs in the project)
          2. state_machine.layer_name
          3. state_machine.role_functions[].namespace
          4. role_function_library entries
        """
        ordered: List[str] = []

        def _add(ns):
            ns = (ns or "").strip()
            if ns and ns not in ordered:
                ordered.append(ns)

        if self.layer_names_provider is not None:
            try:
                for name in self.layer_names_provider():
                    _add(name)
            except Exception as e:
                logger.warning(f"layer_names_provider failed: {e}")

        if self.state_machine is not None:
            _add(getattr(self.state_machine, 'layer_name', ''))
            try:
                for rf in self.state_machine.role_functions.values():
                    _add(getattr(rf, 'namespace', ''))
            except Exception as e:
                logger.warning(
                    f"state_machine.role_functions iteration failed: {e}")

        if self.role_function_library is not None:
            try:
                for rf in self.role_function_library.list_all():
                    _add(getattr(rf, 'namespace', ''))
            except Exception as e:
                logger.warning(
                    f"role_function_library.list_all() failed: {e}")

        return ordered

    def _dialog_kwargs(self) -> dict:
        """Build kwargs for RoleFunctionDialog (mirrors SettingsPanel)."""
        global_vars = []
        if self.global_defs is not None:
            global_vars = [
                getattr(v, 'name', '')
                for v in (getattr(self.global_defs, 'variables', []) or [])
                if getattr(v, 'name', '')
            ]

        events = []
        if self.state_machine is not None:
            events = [
                getattr(e, 'name', '')
                for e in self.state_machine.events.values()
                if getattr(e, 'name', '')
            ]

        literals = []
        if self.literal_library is not None:
            try:
                literals = [
                    getattr(lit, 'name', '')
                    for lit in self.literal_library.list_all()
                    if getattr(lit, 'name', '')
                ]
            except Exception as e:
                logger.warning(
                    f"literal_library.list_all() failed: {e}")

        return dict(
            global_vars=global_vars,
            events=events,
            literals=literals,
            namespace_choices=self._get_namespace_choices(),
        )

    def _on_new_role_function(self):
        """v2.5: create a new role function.

        Registers the new RoleFunction into state_machine and appends
        its qualified_name to self.role_functions so that subsequent
        TransitionActionsDialog / ConditionBuilderDialog instances
        opened from this tab can reference it.
        """
        if self.state_machine is None:
            QMessageBox.information(
                self, "Information",
                "StateMachine is not available; cannot create role "
                "functions from here.")
            return

        dlg = RoleFunctionDialog(self, **self._dialog_kwargs())
        if dlg.exec() != QDialog.Accepted:
            return

        rf = dlg.get_role_function()
        if not rf.name:
            QMessageBox.warning(
                self, "Warning",
                "Role function name is required.")
            return
        if rf.name in self.state_machine.role_functions:
            QMessageBox.warning(
                self, "Warning",
                "A role function with the same name already exists.")
            return

        try:
            self.state_machine.add_role_function(rf)
        except ValueError as e:
            QMessageBox.warning(self, "Warning", str(e))
            return

        qn = _qualified_name(rf)
        if qn and qn not in self.role_functions:
            self.role_functions.append(qn)

        logger.info(
            f"Role function created: {qn} "
            f"(available in subsequent action dialogs)")

    # ------------------------------------------------------------------
    # ComboBox helpers
    # ------------------------------------------------------------------
    def _make_state_combo(self, current_value: str) -> QComboBox:
        combo = QComboBox()
        combo.addItem(NONE_LABEL)
        for s in self.states:
            combo.addItem(s)

        current = (current_value or "").strip()
        if not current:
            combo.setCurrentText(NONE_LABEL)
        elif current in self.states:
            combo.setCurrentText(current)
        else:
            combo.addItem(current)
            combo.setCurrentText(current)
        return combo

    def _make_has_else_combo(self, current: bool) -> QComboBox:
        combo = QComboBox()
        combo.addItems(["Yes", "No"])
        combo.setCurrentText("Yes" if current else "No")
        return combo

    def _refresh_state_combo(self, row: int, col: int):
        old = self.table.cellWidget(row, col)
        current_text = old.currentText() if old else ""
        new_combo = self._make_state_combo(current_text)
        self.table.setCellWidget(row, col, new_combo)
        self._wire_else_link(row)

    def _wire_else_link(self, row: int):
        """Connect has_else combo to else_target enabled state (idempotent)."""
        he = self.table.cellWidget(row, COL_HAS_ELSE)
        et = self.table.cellWidget(row, COL_ELSE_TARGET)
        if he is None or et is None:
            return

        # Initial enabled state
        et.setEnabled(he.currentText().strip().lower() == "yes")

        # Connect only once per widget (flag on the widget itself)
        if getattr(he, "_else_link_connected", False):
            return
        he.currentTextChanged.connect(self._on_has_else_changed)
        he._else_link_connected = True

    def _on_has_else_changed(self, text: str):
        """Slot for has_else combo change (uses sender() to find the row)."""
        he = self.sender()
        if he is None:
            return
        for row in range(self.table.rowCount()):
            if self.table.cellWidget(row, COL_HAS_ELSE) is he:
                et = self.table.cellWidget(row, COL_ELSE_TARGET)
                if et is not None:
                    et.setEnabled(text.strip().lower() == "yes")
                break

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
    # Double-click handling
    # ------------------------------------------------------------------
    def _on_cell_double_clicked(self, row: int, col: int):
        if col == COL_CONDITION:
            self._edit_condition(row)
        elif col in (COL_PRE, COL_ELSE):
            self._edit_actions(row)

    def _edit_condition(self, row: int):
        try:
            from statable_gui.condition_builder_dialog import (
                ConditionBuilderDialog,
            )
        except ImportError:
            logger.warning("ConditionBuilderDialog not available")
            return

        cond_item = self.table.item(row, COL_CONDITION)
        current = cond_item.text().strip() if cond_item else ""

        dlg = ConditionBuilderDialog(
            condition=current,
            global_defs=self.global_defs,
            state_machine=self.state_machine,
            states=self.states,
            literal_library=self.literal_library,
            condition_library=self.condition_library,
            parent=self.window(),
        )
        if dlg.exec() == QDialog.Accepted:
            new_cond = dlg.get_condition_text()
            if cond_item is None:
                cond_item = QTableWidgetItem(new_cond)
                cond_item.setFlags(cond_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, COL_CONDITION, cond_item)
            else:
                cond_item.setText(new_cond)
            self._emit_changed()

    def _edit_actions(self, row: int):
        label_item = self.table.item(row, COL_LABEL)
        label = label_item.text().strip() if label_item else f"T{row + 1}"

        pre_item = self.table.item(row, COL_PRE)
        else_item = self.table.item(row, COL_ELSE)
        pre = self._parse_csv(pre_item.text() if pre_item else "")
        els = self._parse_csv(else_item.text() if else_item else "")

        dlg = TransitionActionsDialog(
            parent=self.window(),
            label=label,
            pre_actions=pre,
            else_actions=els,
            role_functions=self.role_functions,
        )
        if dlg.exec() == QDialog.Accepted:
            new_pre = dlg.get_pre_actions()
            new_else = dlg.get_else_actions()
            self._set_cell_csv(row, COL_PRE, new_pre)
            self._set_cell_csv(row, COL_ELSE, new_else)
            self._emit_changed()

    def _edit_actions_current_row(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(
                self, "Info", "Please select a row first.")
            return
        self._edit_actions(row)

    # ------------------------------------------------------------------
    # CSV helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_csv(text: str) -> List[str]:
        if not text:
            return []
        return [p.strip() for p in text.split(",") if p.strip()]

    @staticmethod
    def _csv(items: List[str]) -> str:
        return ", ".join(items)

    def _set_cell_csv(self, row: int, col: int, items: List[str]):
        item = self.table.item(row, col)
        text = self._csv(items)
        if item is None:
            item = QTableWidgetItem(text)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, col, item)
        else:
            item.setText(text)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_transition(self, trans: Optional[Transition] = None) -> int:
        row = self.table.rowCount()
        self.table.insertRow(row)

        order_item = QTableWidgetItem(str(row + 1))
        order_item.setFlags(order_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, COL_ORDER, order_item)

        label = getattr(trans, 'label', '') if trans else ""
        if not label:
            label = f"T{row + 1}"
        label_item = QTableWidgetItem(label)
        # Label is intentionally non-editable inline.
        # (Reserved for future "Rename Label..." dialog.)
        label_item.setFlags(label_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, COL_LABEL, label_item)

        cond = getattr(trans, 'condition', '') if trans else ""
        cond_item = QTableWidgetItem(cond)
        # Condition is edited via dialog (double-click), not inline.
        cond_item.setFlags(cond_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, COL_CONDITION, cond_item)

        pre = getattr(trans, 'pre_actions', []) if trans else []
        pre_item = QTableWidgetItem(self._csv(list(pre)))
        pre_item.setFlags(pre_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, COL_PRE, pre_item)

        target = getattr(trans, 'target', '') if trans else ""
        self.table.setCellWidget(row, COL_TARGET,
                                 self._make_state_combo(target))

        has_else = getattr(trans, 'has_else', True) if trans else True
        self.table.setCellWidget(row, COL_HAS_ELSE,
                                 self._make_has_else_combo(has_else))

        else_target = getattr(trans, 'else_target', '') if trans else ""
        self.table.setCellWidget(row, COL_ELSE_TARGET,
                                 self._make_state_combo(else_target))

        ea = getattr(trans, 'else_actions', []) if trans else []
        else_item = QTableWidgetItem(self._csv(list(ea)))
        else_item.setFlags(else_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, COL_ELSE, else_item)

        mode_combo = QComboBox()
        mode_combo.addItems(["Commit", "Tentative"])
        if trans is not None and getattr(trans, 'early_return', False):
            mode_combo.setCurrentText("Commit")
        else:
            mode_combo.setCurrentText("Tentative")
        self.table.setCellWidget(row, COL_MODE, mode_combo)

        self._wire_else_link(row)
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
            if col in WIDGET_COLUMNS:
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
        self._wire_else_link(r1)
        self._wire_else_link(r2)

    # ------------------------------------------------------------------
    # Cell value helpers
    # ------------------------------------------------------------------
    def _item_text(self, row: int, col: int) -> str:
        it = self.table.item(row, col)
        return it.text().strip() if it else ""

    def _widget_text(self, row: int, col: int, default: str = "") -> str:
        w = self.table.cellWidget(row, col)
        if w is None:
            return default
        return w.currentText().strip()

    # ------------------------------------------------------------------
    # Public API (get / set)
    # ------------------------------------------------------------------
    def get_transitions(self) -> List[Transition]:
        result = []
        source = self.draft.source
        event = self.draft.event
        for row in range(self.table.rowCount()):
            label = self._item_text(row, COL_LABEL)
            cond = self._item_text(row, COL_CONDITION)
            pre = self._parse_csv(self._item_text(row, COL_PRE))

            target_text = self._widget_text(row, COL_TARGET, NONE_LABEL)
            target = "" if target_text == NONE_LABEL else target_text

            has_else_text = self._widget_text(row, COL_HAS_ELSE, "Yes")
            has_else = has_else_text.lower() in ("yes", "true", "1")

            else_target_text = self._widget_text(
                row, COL_ELSE_TARGET, NONE_LABEL)
            else_target = ("" if else_target_text == NONE_LABEL
                           else else_target_text)

            else_actions = self._parse_csv(self._item_text(row, COL_ELSE))

            mode_text = self._widget_text(row, COL_MODE, "Tentative")
            early_return = (mode_text == "Commit")

            result.append(Transition(
                source=source,
                event=event,
                condition=cond,
                pre_actions=pre,
                target=target,
                has_else=has_else,
                else_target=else_target,
                else_actions=else_actions,
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