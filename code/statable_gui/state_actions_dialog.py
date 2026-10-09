# statable_gui/state_actions_dialog.py
"""State actions (Entry / Exit / Do) editing dialog.

Version: 2.0 (2026-10-10)

Changes from v1.0:
  - Target column: QLineEdit -> QComboBox (Type-dependent candidates)
    * Type="role"       -> qualified_name from RoleFunctionLibrary +
                           state_machine.role_functions
    * Type="fire_event" -> EVENT_<Layer>_<Name> from state_machine.events
  - Role function management buttons:
      + New Role Function / Edit Role Function / Delete Role Function
  - Event management buttons:
      + New Event / Edit Event / Delete Event
  - Condition column: QLineEdit + "[...]" button that opens
      ConditionBuilderDialog (same UX as ActionEditorDialog)
  - Constructor accepts role_function_library / literal_library /
      condition_library / layer_names_provider / global_defs

Design notes:
  - ActionStep.event_name stores the BARE event name (e.g. "STAGE_START").
    The display in the combo is "EVENT_<Layer>_<Name>".
  - ActionStep.role_function stores the qualified name (e.g. "DriverOutput.SetHeaterPwm").
"""

from __future__ import annotations

from typing import List, Optional, Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QPushButton,
    QDialogButtonBox, QTabWidget, QWidget, QLabel, QHeaderView,
    QPlainTextEdit, QComboBox, QLineEdit, QAbstractItemView,
    QMessageBox,
)

from statable.model import State, ActionStep
from statable.state_machine import StateMachine

from .logger import StaTableLogger
from .role_function_dialog import RoleFunctionDialog
from .event_definition_dialog import EventEditDialog
from .condition_builder_dialog import ConditionBuilderDialog


KIND_ENTRY = "Entry"
KIND_EXIT = "Exit"
KIND_DO = "Do"


# ======================================================================
# Action list widget
# ======================================================================
class _ActionListWidget(QWidget):
    """Reusable action list editor with combobox-based Target column."""

    COL_TYPE = 0
    COL_TARGET = 1
    COL_CONDITION = 2

    VALID_TYPES = ("role", "fire_event")

    def __init__(self, parent=None, state_machine=None,
                 role_function_library=None, literal_library=None,
                 condition_library=None, layer_names_provider=None,
                 global_defs=None):
        super().__init__(parent)

        self.state_machine = state_machine
        self.role_function_library = role_function_library
        self.literal_library = literal_library
        self.condition_library = condition_library
        self.layer_names_provider = layer_names_provider
        self.global_defs = global_defs

        layer = (getattr(state_machine, 'layer_name', '')
                 if state_machine else '')
        self.layer_name = layer or "Layer"

        # Row data store: list of dicts {type, target, condition}
        self._rows: List[dict] = []

        self._setup_ui()
        self._rebuild_table()

    # ------------------------------------------------------------------
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Type", "Target", "Condition"])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(self.COL_TYPE, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(self.COL_TARGET, QHeaderView.Stretch)
        hdr.setSectionResizeMode(self.COL_CONDITION, QHeaderView.Stretch)
        self.table.setFont(QFont("Consolas", 10))
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setDefaultSectionSize(28)
        layout.addWidget(self.table)

        # Row 1: row operations
        row1 = QHBoxLayout()
        self.add_btn = QPushButton(self.tr("+ Add"))
        self.add_btn.clicked.connect(self._on_add)
        self.del_btn = QPushButton(self.tr("Delete"))
        self.del_btn.clicked.connect(self._on_delete)
        self.up_btn = QPushButton(self.tr("Up"))
        self.up_btn.clicked.connect(self._on_up)
        self.down_btn = QPushButton(self.tr("Down"))
        self.down_btn.clicked.connect(self._on_down)
        row1.addWidget(self.add_btn)
        row1.addWidget(self.del_btn)
        row1.addStretch()
        row1.addWidget(self.up_btn)
        row1.addWidget(self.down_btn)
        layout.addLayout(row1)

        # Row 2: Role function management
        row2 = QHBoxLayout()
        self.new_role_btn = QPushButton(self.tr("+ New Role Function"))
        self.new_role_btn.clicked.connect(self._on_new_role_function)
        self.edit_role_btn = QPushButton(self.tr("Edit Role Function"))
        self.edit_role_btn.clicked.connect(self._on_edit_role_function)
        self.del_role_btn = QPushButton(self.tr("Delete Role Function"))
        self.del_role_btn.clicked.connect(self._on_delete_role_function)
        row2.addWidget(self.new_role_btn)
        row2.addWidget(self.edit_role_btn)
        row2.addWidget(self.del_role_btn)
        row2.addStretch()
        layout.addLayout(row2)

        # Row 3: Event management
        row3 = QHBoxLayout()
        self.new_event_btn = QPushButton(self.tr("+ New Event"))
        self.new_event_btn.clicked.connect(self._on_new_event)
        self.edit_event_btn = QPushButton(self.tr("Edit Event"))
        self.edit_event_btn.clicked.connect(self._on_edit_event)
        self.del_event_btn = QPushButton(self.tr("Delete Event"))
        self.del_event_btn.clicked.connect(self._on_delete_event)
        row3.addWidget(self.new_event_btn)
        row3.addWidget(self.edit_event_btn)
        row3.addWidget(self.del_event_btn)
        row3.addStretch()
        layout.addLayout(row3)

    # ------------------------------------------------------------------
    def _rebuild_table(self):
        current_row = self.table.currentRow()
        self.table.setRowCount(0)
        for row, data in enumerate(self._rows):
            self.table.insertRow(row)
            self._create_type_combo(row, data.get("type", "role"))
            self._create_target_combo(
                row, data.get("type", "role"), data.get("target", ""))
            self._create_condition_widget(
                row, data.get("condition", ""))
        if 0 <= current_row < self.table.rowCount():
            self.table.setCurrentCell(current_row, 0)

    def _create_type_combo(self, row, current_type):
        combo = QComboBox()
        for t in self.VALID_TYPES:
            combo.addItem(t, t)
        idx = combo.findData(current_type)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        combo.currentIndexChanged.connect(self._on_type_combo_changed)
        self.table.setCellWidget(row, self.COL_TYPE, combo)

    def _create_target_combo(self, row, action_type, current_target):
        combo = QComboBox()
        candidates = self._get_target_candidates(action_type)
        combo.addItems(candidates)
        if current_target:
            idx = combo.findText(current_target)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        combo.currentTextChanged.connect(self._on_target_changed)
        self.table.setCellWidget(row, self.COL_TARGET, combo)

    def _create_condition_widget(self, row, current_cond):
        container = QWidget()
        hl = QHBoxLayout(container)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(2)
        edit = QLineEdit(current_cond)
        edit.setFont(QFont("Consolas", 10))
        edit.textChanged.connect(self._on_condition_changed)
        build_btn = QPushButton("...")
        build_btn.setMaximumWidth(30)
        build_btn.setToolTip(self.tr("Open condition builder"))
        build_btn.clicked.connect(self._open_condition_builder)
        hl.addWidget(edit, 1)
        hl.addWidget(build_btn)
        self.table.setCellWidget(row, self.COL_CONDITION, container)

    # ------------------------------------------------------------------
    # Change handlers
    # ------------------------------------------------------------------
    def _find_row_by_widget(self, widget, col):
        for row in range(self.table.rowCount()):
            if self.table.cellWidget(row, col) is widget:
                return row
        return -1

    def _on_type_combo_changed(self, _index):
        combo = self.sender()
        row = self._find_row_by_widget(combo, self.COL_TYPE)
        if row < 0 or row >= len(self._rows):
            return
        new_type = combo.currentData()
        self._rows[row]["type"] = new_type
        self._refresh_target_combo(row)

    def _refresh_target_combo(self, row):
        data = self._rows[row]
        atype = data.get("type", "role")
        current = data.get("target", "")
        combo = self.table.cellWidget(row, self.COL_TARGET)
        if combo is None:
            return
        candidates = self._get_target_candidates(atype)
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(candidates)
        idx = combo.findText(current)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        elif candidates:
            combo.setCurrentIndex(0)
            data["target"] = combo.currentText()
        else:
            data["target"] = ""
        combo.blockSignals(False)

    def _on_target_changed(self, _text):
        combo = self.sender()
        row = self._find_row_by_widget(combo, self.COL_TARGET)
        if 0 <= row < len(self._rows):
            self._rows[row]["target"] = combo.currentText()

    def _on_condition_changed(self, text):
        edit = self.sender()
        for row in range(self.table.rowCount()):
            container = self.table.cellWidget(row, self.COL_CONDITION)
            if container is None:
                continue
            if container.findChild(QLineEdit) is edit:
                if row < len(self._rows):
                    self._rows[row]["condition"] = text
                return

    # ------------------------------------------------------------------
    # Row operations
    # ------------------------------------------------------------------
    def _on_add(self):
        self._rows.append({"type": "role", "target": "", "condition": ""})
        self._rebuild_table()
        self.table.setCurrentCell(self.table.rowCount() - 1, self.COL_TARGET)

    def _on_delete(self):
        row = self.table.currentRow()
        if 0 <= row < len(self._rows):
            del self._rows[row]
            self._rebuild_table()

    def _on_up(self):
        row = self.table.currentRow()
        if row > 0:
            self._rows[row - 1], self._rows[row] = (
                self._rows[row], self._rows[row - 1])
            self._rebuild_table()
            self.table.setCurrentCell(row - 1, 0)

    def _on_down(self):
        row = self.table.currentRow()
        if 0 <= row < len(self._rows) - 1:
            self._rows[row], self._rows[row + 1] = (
                self._rows[row + 1], self._rows[row])
            self._rebuild_table()
            self.table.setCurrentCell(row + 1, 0)

    # ------------------------------------------------------------------
    # Data binding
    # ------------------------------------------------------------------
    def set_actions(self, actions):
        self._rows = []
        for a in (actions or []):
            atype = getattr(a, "action_type", "role") or "role"
            if atype not in self.VALID_TYPES:
                atype = "role"
            if atype == "fire_event":
                target = self._make_event_display(
                    getattr(a, "event_name", "") or "")
            else:
                target = getattr(a, "role_function", "") or ""
            cond = getattr(a, "condition", "") or ""
            self._rows.append({"type": atype, "target": target, "condition": cond})
        self._rebuild_table()

    def get_actions(self):
        result = []
        for data in self._rows:
            atype = data.get("type", "role")
            target = data.get("target", "").strip()
            cond = data.get("condition", "").strip()
            if not target:
                continue
            if atype == "fire_event":
                bare = self._extract_event_bare_name(target)
                result.append(ActionStep(
                    action_type="fire_event", event_name=bare, condition=cond))
            else:
                result.append(ActionStep(
                    action_type="role", role_function=target, condition=cond))
        return result

    # ------------------------------------------------------------------
    # Candidates
    # ------------------------------------------------------------------
    def _get_target_candidates(self, action_type):
        if action_type == "fire_event":
            return self._event_candidates()
        return self._role_candidates()

    def _role_candidates(self):
        seen = set()
        result = []
        if self.role_function_library is not None:
            try:
                for rf in self.role_function_library.list_all():
                    qn = (getattr(rf, 'qualified_name', None)
                          or getattr(rf, 'name', ''))
                    if qn and qn not in seen:
                        seen.add(qn)
                        result.append(qn)
            except Exception as e:
                StaTableLogger.warning(f"list_all failed: {e}")
        if self.state_machine is not None:
            for rf in self.state_machine.role_functions.values():
                qn = (getattr(rf, 'qualified_name', None)
                      or getattr(rf, 'name', ''))
                if qn and qn not in seen:
                    seen.add(qn)
                    result.append(qn)
        return result

    def _event_candidates(self):
        if self.state_machine is None:
            return []
        result = []
        for ev in self.state_machine.events.values():
            if ev.name:
                result.append(f"EVENT_{self.layer_name}_{ev.name}")
        return result

    def _make_event_display(self, event_name):
        if not event_name:
            return ""
        bare = self._extract_event_bare_name(event_name)
        return f"EVENT_{self.layer_name}_{bare}"

    def _extract_event_bare_name(self, display):
        if not display:
            return ""
        if not display.startswith("EVENT_"):
            return display
        prefix = f"EVENT_{self.layer_name}_"
        if display.startswith(prefix):
            return display[len(prefix):]
        if self.state_machine is not None:
            for ev in self.state_machine.events.values():
                if ev.name and f"EVENT_{self.layer_name}_{ev.name}" == display:
                    return ev.name
        return display[6:]

    # ------------------------------------------------------------------
    # Role function management
    # ------------------------------------------------------------------
    def _find_rf_by_display(self, display_name):
        if self.state_machine is None or not display_name:
            return None
        for rf in self.state_machine.role_functions.values():
            qn = getattr(rf, 'qualified_name', None) or ''
            bare = getattr(rf, 'name', '') or ''
            if qn == display_name or bare == display_name:
                return rf
        return None

    def _get_namespace_choices(self):
        ordered = []
        def _add(ns):
            ns = (ns or "").strip()
            if ns and ns not in ordered:
                ordered.append(ns)
        if self.layer_names_provider is not None:
            try:
                for name in self.layer_names_provider():
                    _add(name)
            except Exception:
                pass
        if self.state_machine is not None:
            _add(getattr(self.state_machine, 'layer_name', ''))
            for rf in self.state_machine.role_functions.values():
                _add(getattr(rf, 'namespace', ''))
        if self.role_function_library is not None:
            try:
                for rf in self.role_function_library.list_all():
                    _add(getattr(rf, 'namespace', ''))
            except Exception:
                pass
        return ordered

    def _dialog_kwargs(self):
        global_vars = []
        if self.global_defs is not None:
            global_vars = [
                getattr(v, 'name', '')
                for v in (getattr(self.global_defs, 'variables', []) or [])
                if getattr(v, 'name', '')
            ]
        events = []
        if self.state_machine is not None:
            events = [getattr(e, 'name', '')
                      for e in self.state_machine.events.values()
                      if getattr(e, 'name', '')]
        literals = []
        if self.literal_library is not None:
            try:
                literals = [getattr(lit, 'name', '')
                            for lit in self.literal_library.list_all()
                            if getattr(lit, 'name', '')]
            except Exception:
                pass
        return dict(
            global_vars=global_vars,
            events=events,
            literals=literals,
            namespace_choices=self._get_namespace_choices(),
            literal_library=self.literal_library,
        )

    def _refresh_all_target_combos(self):
        for row in range(self.table.rowCount()):
            self._refresh_target_combo(row)

    def _on_new_role_function(self):
        if self.state_machine is None:
            QMessageBox.information(self, self.tr("Information"),
                self.tr("StateMachine is not available."))
            return
        dlg = RoleFunctionDialog(self, **self._dialog_kwargs())
        if dlg.exec() != QDialog.Accepted:
            return
        rf = dlg.get_role_function()
        if not rf.name:
            QMessageBox.warning(self, self.tr("Warning"),
                self.tr("Role function name is required."))
            return
        if rf.name in self.state_machine.role_functions:
            QMessageBox.warning(self, self.tr("Warning"),
                self.tr("A role function with the same name already exists."))
            return
        try:
            self.state_machine.add_role_function(rf)
        except ValueError as e:
            QMessageBox.warning(self, self.tr("Warning"), str(e))
            return
        row = self.table.currentRow()
        if 0 <= row < len(self._rows):
            self._rows[row]["type"] = "role"
            self._rows[row]["target"] = rf.qualified_name
        self._rebuild_table()
        StaTableLogger.info(f"Role function created: {rf.qualified_name}")

    def _on_edit_role_function(self):
        row = self.table.currentRow()
        if not (0 <= row < len(self._rows)):
            QMessageBox.information(self, self.tr("Information"),
                self.tr("Please select a row first."))
            return
        data = self._rows[row]
        if data.get("type") != "role":
            QMessageBox.information(self, self.tr("Information"),
                self.tr("Selected row is not a role function call."))
            return
        display_name = data.get("target", "").strip()
        if not display_name:
            return
        rf = self._find_rf_by_display(display_name)
        if rf is None:
            QMessageBox.information(self, self.tr("Information"),
                self.tr(f"'{display_name}' is not registered in this "
                "state machine."))
            return
        pure_name = rf.name
        dlg = RoleFunctionDialog(
            self, role_function=rf, **self._dialog_kwargs())
        if dlg.exec() != QDialog.Accepted:
            return
        updated = dlg.get_role_function()
        if (updated.name != pure_name and
                updated.name in self.state_machine.role_functions):
            QMessageBox.warning(self, self.tr("Warning"),
                self.tr("A role function with the same name already exists."))
            return
        old_qn = rf.qualified_name
        new_qn = updated.qualified_name
        self.state_machine.remove_role_function(pure_name)
        try:
            self.state_machine.add_role_function(updated)
        except ValueError as e:
            try:
                self.state_machine.add_role_function(rf)
            except Exception:
                pass
            QMessageBox.warning(self, self.tr("Warning"), str(e))
            return
        for r_data in self._rows:
            if r_data.get("target") == old_qn:
                r_data["target"] = new_qn
        self._rebuild_table()
        StaTableLogger.info(f"Role function updated: {old_qn} -> {new_qn}")

    def _on_delete_role_function(self):
        row = self.table.currentRow()
        if not (0 <= row < len(self._rows)):
            QMessageBox.information(self, self.tr("Information"),
                self.tr("Please select a row first."))
            return
        data = self._rows[row]
        if data.get("type") != "role":
            return
        display_name = data.get("target", "").strip()
        if not display_name:
            return
        rf = self._find_rf_by_display(display_name)
        if rf is None:
            QMessageBox.information(self, self.tr("Information"),
                self.tr(f"'{display_name}' is not registered."))
            return
        pure_name = rf.name
        reply = QMessageBox.question(
            self, self.tr("Confirm delete"),
            self.tr(f"Delete role function '{display_name}' from "
            "the state machine?"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.state_machine.remove_role_function(pure_name)
        for r_data in self._rows:
            if r_data.get("target") == display_name:
                r_data["target"] = ""
        self._rebuild_table()
        StaTableLogger.info(f"Role function deleted: {display_name}")

    # ------------------------------------------------------------------
    # Event management
    # ------------------------------------------------------------------
    def _on_new_event(self):
        if self.state_machine is None:
            return
        dlg = EventEditDialog(
            self, event=None,
            global_defs=self.global_defs,
            state_machine=self.state_machine)
        if dlg.exec() != QDialog.Accepted:
            return
        new_event = dlg.get_event()
        if not new_event.name:
            QMessageBox.warning(self, self.tr("Warning"),
                self.tr("Please enter an event name."))
            return
        if new_event.name in self.state_machine.events:
            QMessageBox.warning(self, self.tr("Warning"),
                self.tr(f"Event '{new_event.name}' already exists."))
            return
        self.state_machine.add_event(new_event)
        row = self.table.currentRow()
        if 0 <= row < len(self._rows):
            self._rows[row]["type"] = "fire_event"
            self._rows[row]["target"] = self._make_event_display(new_event.name)
        self._rebuild_table()
        StaTableLogger.info(f"Event created: {new_event.name}")

    def _on_edit_event(self):
        row = self.table.currentRow()
        if not (0 <= row < len(self._rows)):
            QMessageBox.information(self, self.tr("Information"),
                self.tr("Please select a row first."))
            return
        data = self._rows[row]
        if data.get("type") != "fire_event":
            QMessageBox.information(self, self.tr("Information"),
                self.tr("Selected row is not an event call."))
            return
        target_display = data.get("target", "").strip()
        bare = self._extract_event_bare_name(target_display)
        if bare not in self.state_machine.events:
            QMessageBox.information(self, self.tr("Information"),
                self.tr(f"Event '{bare}' is not registered."))
            return
        event = self.state_machine.events[bare]
        dlg = EventEditDialog(
            self, event=event,
            global_defs=self.global_defs,
            state_machine=self.state_machine)
        if dlg.exec() != QDialog.Accepted:
            return
        updated = dlg.get_event()
        if not updated.name:
            QMessageBox.warning(self, self.tr("Warning"),
                self.tr("Event name is required."))
            return
        old_name = event.name
        if old_name != updated.name:
            if updated.name in self.state_machine.events:
                QMessageBox.warning(self, self.tr("Warning"),
                    self.tr(f"Event '{updated.name}' already exists."))
                return
            new_events = {}
            for key, value in self.state_machine.events.items():
                if key == old_name:
                    new_events[updated.name] = updated
                else:
                    new_events[key] = value
            self.state_machine.events = new_events
            for trans in self.state_machine.transitions:
                if trans.event == old_name:
                    trans.event = updated.name
        else:
            self.state_machine.events[old_name] = updated
        old_display = self._make_event_display(old_name)
        new_display = self._make_event_display(updated.name)
        for r_data in self._rows:
            if r_data.get("target") == old_display:
                r_data["target"] = new_display
        self._rebuild_table()
        StaTableLogger.info(f"Event updated: {old_name} -> {updated.name}")

    def _on_delete_event(self):
        row = self.table.currentRow()
        if not (0 <= row < len(self._rows)):
            QMessageBox.information(self, self.tr("Information"),
                self.tr("Please select a row first."))
            return
        data = self._rows[row]
        if data.get("type") != "fire_event":
            return
        target_display = data.get("target", "").strip()
        bare = self._extract_event_bare_name(target_display)
        if bare not in self.state_machine.events:
            return
        transitions = self.state_machine.get_transitions_for_event(bare)
        if transitions:
            QMessageBox.warning(self, self.tr("Warning"),
                self.tr(f"Cannot delete: event '{bare}' is used by "
                f"{len(transitions)} transition(s)."))
            return
        reply = QMessageBox.question(
            self, self.tr("Confirm delete"),
            self.tr(f"Delete event '{bare}'?"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.state_machine.remove_event(bare)
        for r_data in self._rows:
            if r_data.get("target") == target_display:
                r_data["target"] = ""
        self._rebuild_table()
        StaTableLogger.info(f"Event deleted: {bare}")

    # ------------------------------------------------------------------
    # Condition builder
    # ------------------------------------------------------------------
    def _open_condition_builder(self):
        btn = self.sender()
        row = -1
        for r in range(self.table.rowCount()):
            container = self.table.cellWidget(r, self.COL_CONDITION)
            if container is None:
                continue
            if container.findChild(QPushButton) is btn:
                row = r
                break
        if not (0 <= row < len(self._rows)):
            return
        container = self.table.cellWidget(row, self.COL_CONDITION)
        edit = container.findChild(QLineEdit)
        current_cond = edit.text() if edit else ""
        states = (list(self.state_machine.states.keys())
                  if self.state_machine is not None else [])
        dlg = ConditionBuilderDialog(
            condition=current_cond,
            event_name="",
            global_defs=self.global_defs,
            state_machine=self.state_machine,
            literal_library=self.literal_library,
            states=states,
            condition_library=self.condition_library,
            parent=self,
        )
        if dlg.exec() == QDialog.Accepted:
            new_cond = dlg.get_condition_text()
            if edit:
                edit.setText(new_cond)
            self._rows[row]["condition"] = new_cond


# ======================================================================
# Main dialog
# ======================================================================
class StateActionsDialog(QDialog):
    """State actions (Entry / Exit / Do) editor."""

    KIND_TO_ATTR = {
        KIND_ENTRY: "entry",
        KIND_EXIT: "exit",
        KIND_DO: "do_actions",
    }

    @staticmethod
    def _to_pascal(name: str) -> str:
        if not name:
            return ""
        parts = [p for p in name.replace("-", "_").split("_") if p]
        return "".join(p[:1].upper() + p[1:] for p in parts)

    @classmethod
    def _rf_call_preview(cls, layer: str, role_function: str) -> str:
        if not role_function:
            return ""
        rf = role_function.strip()
        if rf.startswith("RoleFunc_"):
            full = rf
        elif "." in rf:
            ns, name = rf.split(".", 1)
            full = f"RoleFunc_{ns}_{name}"
        else:
            full = (f"RoleFunc_{layer}_{cls._to_pascal(rf)}"
                    if layer else f"RoleFunc_{cls._to_pascal(rf)}")
        return f"(void){full}(NULL, ctx)"

    def __init__(
        self,
        parent=None,
        state: Optional[State] = None,
        state_machine: Optional[StateMachine] = None,
        role_function_library=None,
        literal_library=None,
        condition_library=None,
        layer_names_provider=None,
        global_defs=None,
    ):
        super().__init__(parent)
        self.state = state
        self.state_machine = state_machine
        self.role_function_library = role_function_library
        self.literal_library = literal_library
        self.condition_library = condition_library
        self.layer_names_provider = layer_names_provider
        self.global_defs = global_defs

        title_state = state.name if state is not None else "(unknown)"
        self.setWindowTitle(f"State actions - {title_state}")
        self.setMinimumSize(950, 720)

        self._setup_ui()
        self._load_state()
        StaTableLogger.debug(
            f"StateActionsDialog initialized: state={title_state}")

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            self.tr("Entry / Exit / Do actions for this state.\n"
            "Custom C code is edited in the generated file "
            "([[STABLE_USER_CODE_..._custom]] marker)."))
        info.setWordWrap(True)
        layout.addWidget(info)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        ctx = dict(
            state_machine=self.state_machine,
            role_function_library=self.role_function_library,
            literal_library=self.literal_library,
            condition_library=self.condition_library,
            layer_names_provider=self.layer_names_provider,
            global_defs=self.global_defs,
        )

        self.entry_widget = _ActionListWidget(**ctx)
        self.exit_widget = _ActionListWidget(**ctx)
        self.do_widget = _ActionListWidget(**ctx)

        self.tabs.addTab(self.entry_widget, KIND_ENTRY)
        self.tabs.addTab(self.exit_widget, KIND_EXIT)
        self.tabs.addTab(self.do_widget, KIND_DO)

        # Preview tab
        self.preview_widget = QPlainTextEdit()
        self.preview_widget.setReadOnly(True)
        self.preview_widget.setFont(QFont("Consolas", 10))
        preview_container = QWidget()
        pl = QVBoxLayout(preview_container)
        refresh_btn = QPushButton(self.tr("Refresh preview"))
        refresh_btn.clicked.connect(self._refresh_preview)
        pl.addWidget(refresh_btn)
        pl.addWidget(self.preview_widget)
        self.tabs.addTab(preview_container, self.tr("Preview"))

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_state(self):
        if self.state is None:
            return
        self.entry_widget.set_actions(
            list(getattr(self.state, "entry", []) or []))
        self.exit_widget.set_actions(
            list(getattr(self.state, "exit", []) or []))
        self.do_widget.set_actions(
            list(getattr(self.state, "do_actions", []) or []))

    def _on_accept(self):
        if self.state is not None:
            self.state.entry = self.entry_widget.get_actions()
            self.state.exit = self.exit_widget.get_actions()
            self.state.do_actions = self.do_widget.get_actions()
        self.accept()

    def _refresh_preview(self):
        if self.state is None:
            self.preview_widget.setPlainText("(no state)")
            return
        state_name = self.state.name
        layer = (getattr(self.state_machine, "layer_name", "")
                 if self.state_machine else "") or "Layer"

        lines = []
        for kind, actions in (
            (KIND_ENTRY, self.entry_widget.get_actions()),
            (KIND_EXIT, self.exit_widget.get_actions()),
            (KIND_DO, self.do_widget.get_actions()),
        ):
            func_name = f"{layer}_{kind}_{state_name}"
            marker = f"{layer}_{kind}_{state_name}_custom"
            lines.append(f"static void {func_name}(SystemContext_t *ctx)")
            lines.append("{")
            if actions:
                lines.append("    /* --- GUI-edited actions (regenerated) --- */")
                for a in actions:
                    atype = getattr(a, "action_type", "role") or "role"
                    cond = (getattr(a, "condition", "") or "").strip()
                    if atype == "fire_event":
                        bare = getattr(a, "event_name", "") or ""
                        call = f"FIRE_EVENT_{layer}(ctx, EVENT_{layer}_{bare})"
                    else:
                        rf = getattr(a, "role_function", "") or ""
                        call = self._rf_call_preview(layer, rf)
                    if cond:
                        lines.append(f"    if ({cond}) {{")
                        lines.append(f"        {call};")
                        lines.append("    }")
                    else:
                        lines.append(f"    {call};")
                lines.append("    /* --- end GUI-edited actions --- */")
            lines.append("")
            lines.append("    /* --- user custom code (preserved) --- */")
            lines.append(f"    /* [[STABLE_USER_CODE_START:{marker}]] */")
            lines.append("    (void)ctx;")
            lines.append(f"    /* [[STABLE_USER_CODE_END:{marker}]] */")
            lines.append("}")
            lines.append("")
        self.preview_widget.setPlainText("\n".join(lines))


def open_state_actions_dialog(parent, state, state_machine):
    dlg = StateActionsDialog(
        parent=parent, state=state, state_machine=state_machine)
    return dlg.exec() == QDialog.Accepted