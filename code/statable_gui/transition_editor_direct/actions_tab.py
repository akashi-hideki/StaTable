# statable_gui/transition_editor_direct/actions_tab.py
"""Pre / Post Actions tab widget (v2.2, v2.5 role-func management).

Two groups:
  - Pre  : before_transitions (executed before the transition chain)
  - Post : after_transitions  (executed after the transition chain)

[v2.2 change]
  - `always` trigger removed; old data migrated to `before_transitions`.
  - Role function input is an editable ComboBox.

[v2.5 change]
  - Each _ActionGroup gains three buttons:
      + New Role Function  -> RoleFunctionDialog, registers into
                              state_machine.role_functions and
                              appends a row to the group table.
      Edit Role Function   -> edits the role function bound to the
                              currently selected row.
      Delete Role Function -> removes it from state_machine and
                              deletes all rows referencing it.
  - New constructor args: role_function_library, literal_library,
    layer_names_provider (all optional / keyword).

[v2.5 fix]
  - StateMachine.role_functions is keyed by *bare* name (rf.name),
    but this tab displays the *qualified* name (rf.namespace + '.' +
    rf.name). Edit / Delete previously looked up the dict with the
    qualified name and therefore always failed with "not registered".
    The new helper _find_rf_by_display() resolves qualified_name ->
    RoleFunction object, and the caller uses rf.name for the dict
    operations.
  - Extensive debug logging added to _on_new / _on_edit / _on_delete
    so that failures can be diagnosed from the log alone.
"""

import logging
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QHeaderView, QAbstractItemView, QLabel,
    QGroupBox, QMessageBox, QDialog,
)

from statable.model import ActionStep
from statable_gui.role_function_dialog import RoleFunctionDialog
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


def _qualified_name(rf) -> str:
    """Return qualified_name if available, else fall back to name."""
    qn = getattr(rf, 'qualified_name', None)
    if qn:
        return qn
    return getattr(rf, 'name', '') or ''


class _ActionGroup(QGroupBox):
    """A QGroupBox containing a role function list for one trigger."""

    changed = Signal()

    def __init__(self, title: str, trigger: str,
                 role_functions: List[str],
                 role_function_library=None,
                 literal_library=None,
                 layer_names_provider=None,
                 global_defs=None,
                 state_machine=None,
                 parent=None):
        super().__init__(title, parent)
        self.trigger = trigger
        self.role_functions = list(role_functions or [])

        # v2.5: context for RoleFunctionDialog
        self.role_function_library = role_function_library
        self.literal_library = literal_library
        self.layer_names_provider = layer_names_provider
        self.global_defs = global_defs
        self.state_machine = state_machine

        logger.debug(
            f"_ActionGroup.__init__: title='{title}', trigger='{trigger}', "
            f"role_functions={len(self.role_functions)}, "
            f"has_sm={state_machine is not None}, "
            f"has_rflib={role_function_library is not None}, "
            f"has_litlib={literal_library is not None}, "
            f"has_lnp={layer_names_provider is not None}")

        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 1)
        self.table.setHorizontalHeaderLabels(["Role function"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.table)

        # ---- Row 1: combo + row operations ----
        btn_layout = QHBoxLayout()
        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.combo.addItems(self.role_functions)
        btn_layout.addWidget(self.combo, stretch=1)

        add_btn = QPushButton("+ Add")
        add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(add_btn)

        del_btn = QPushButton("Delete")
        del_btn.setToolTip("Remove the selected row from this list "
                           "(does not delete the role function itself)")
        del_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(del_btn)

        up_btn = QPushButton("Up")
        up_btn.clicked.connect(self._on_move_up)
        btn_layout.addWidget(up_btn)

        down_btn = QPushButton("Down")
        down_btn.clicked.connect(self._on_move_down)
        btn_layout.addWidget(down_btn)

        layout.addLayout(btn_layout)

        # ---- Row 2 (v2.5): role function management ----
        role_btn_layout = QHBoxLayout()

        self.new_role_btn = QPushButton("+ New Role Function")
        self.new_role_btn.setToolTip(
            "Create a new role function and add it to this list")
        self.new_role_btn.clicked.connect(self._on_new_role_function)
        role_btn_layout.addWidget(self.new_role_btn)

        self.edit_role_btn = QPushButton("Edit Role Function")
        self.edit_role_btn.setToolTip(
            "Edit the role function bound to the selected row")
        self.edit_role_btn.clicked.connect(self._on_edit_role_function)
        role_btn_layout.addWidget(self.edit_role_btn)

        self.delete_role_btn = QPushButton("Delete Role Function")
        self.delete_role_btn.setToolTip(
            "Delete the selected role function from the state machine")
        self.delete_role_btn.clicked.connect(self._on_delete_role_function)
        role_btn_layout.addWidget(self.delete_role_btn)

        role_btn_layout.addStretch()
        layout.addLayout(role_btn_layout)

    # ------------------------------------------------------------------
    # Public setters
    # ------------------------------------------------------------------
    def set_role_functions(self, names: List[str]):
        self.role_functions = list(names or [])
        current = self.combo.currentText()
        self.combo.clear()
        self.combo.addItems(self.role_functions)
        if current:
            self.combo.setCurrentText(current)
        logger.debug(
            f"set_role_functions: {len(self.role_functions)} candidates")

    def set_actions(self, actions: List[ActionStep]):
        """Replace the list (filtered by trigger)."""
        self.table.setRowCount(0)
        for a in actions:
            if _migrate_trigger(a.trigger) != self.trigger:
                continue
            self._append_row(a.role_function)
        logger.debug(
            f"set_actions: table rows={self.table.rowCount()}, "
            f"trigger={self.trigger}")

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
    # Slots (row operations - existing)
    # ------------------------------------------------------------------
    def _append_row(self, role_function: str):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(role_function))
        logger.debug(
            f"_append_row: '{role_function}' -> row {row}")

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

    # ------------------------------------------------------------------
    # v2.5: debug helper
    # ------------------------------------------------------------------
    def _dump_sm_roles(self, label: str):
        """Log the current StateMachine.role_functions contents.

        Useful for diagnosing qualified-vs-bare name mismatches.
        """
        if self.state_machine is None:
            logger.debug(f"[{label}] state_machine is None")
            return
        try:
            items = list(self.state_machine.role_functions.items())
        except Exception as e:
            logger.warning(f"[{label}] cannot list role_functions: {e}")
            return
        logger.debug(f"[{label}] state_machine.role_functions: "
                     f"{len(items)} entries")
        for key, rf in items:
            logger.debug(
                f"[{label}]   key='{key}' "
                f"name='{getattr(rf, 'name', '?')}' "
                f"namespace='{getattr(rf, 'namespace', '?')}' "
                f"qualified='{_qualified_name(rf)}'")

    # ------------------------------------------------------------------
    # v2.5: role-function lookup
    # ------------------------------------------------------------------
    def _find_rf_by_display(self, display_name: str):
        """Find a StateMachine role function whose qualified_name
        (or bare name) matches `display_name`.

        The StateMachine keys role functions by *bare* name
        (`rf.name`), but this tab displays the qualified name
        (`rf.namespace + '.' + rf.name`). This helper bridges the
        two so that Edit / Delete can locate the correct entry.

        Returns the RoleFunction object, or None if not found.
        """
        if self.state_machine is None:
            logger.warning(
                f"_find_rf_by_display('{display_name}'): "
                "state_machine is None")
            return None
        if not display_name:
            logger.debug("_find_rf_by_display: empty display_name")
            return None

        entries = list(self.state_machine.role_functions.values())
        logger.debug(
            f"_find_rf_by_display('{display_name}'): "
            f"scanning {len(entries)} entries")

        for rf in entries:
            qn = _qualified_name(rf)
            bare = getattr(rf, 'name', '') or ''
            logger.debug(
                f"  candidate: bare='{bare}', qualified='{qn}'")
            if qn == display_name:
                logger.debug(
                    f"  -> matched by qualified_name: '{qn}'")
                return rf
            if bare == display_name:
                logger.debug(
                    f"  -> matched by bare name: '{bare}'")
                return rf

        logger.warning(
            f"_find_rf_by_display('{display_name}'): NOT FOUND "
            f"among {len(entries)} entries")
        return None

    # ------------------------------------------------------------------
    # v2.5: namespace / dialog helpers
    # ------------------------------------------------------------------
    def _get_namespace_choices(self) -> List[str]:
        """Build namespace candidates for the RoleFunctionDialog.

        Order:
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

        logger.debug(
            f"_get_namespace_choices: {len(ordered)} candidates "
            f"{ordered}")
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

        kwargs = dict(
            global_vars=global_vars,
            events=events,
            literals=literals,
            namespace_choices=self._get_namespace_choices(),
        )
        logger.debug(
            f"_dialog_kwargs: global_vars={len(global_vars)}, "
            f"events={len(events)}, literals={len(literals)}, "
            f"namespace_choices={len(kwargs['namespace_choices'])}")
        return kwargs

    def _sync_combo(self):
        """Rebuild the editable combo from self.role_functions."""
        current = self.combo.currentText()
        self.combo.clear()
        self.combo.addItems(self.role_functions)
        if current:
            self.combo.setCurrentText(current)
        logger.debug(
            f"_sync_combo: {len(self.role_functions)} items, "
            f"current='{current}'")

    # ------------------------------------------------------------------
    # v2.5: slot implementations
    # ------------------------------------------------------------------
    def _on_new_role_function(self):
        """v2.5: create a new role function and append it to the list."""
        logger.debug("=== _on_new_role_function: ENTER ===")
        if self.state_machine is None:
            logger.warning(
                "_on_new_role_function: state_machine is None -> abort")
            QMessageBox.information(
                self, "Information",
                "StateMachine is not available; cannot create role "
                "functions from here.")
            return

        self._dump_sm_roles("_on_new_role_function/before")

        dlg = RoleFunctionDialog(self, **self._dialog_kwargs())
        logger.debug("_on_new_role_function: dialog opened")
        if dlg.exec() != QDialog.Accepted:
            logger.debug("_on_new_role_function: dialog cancelled")
            return

        rf = dlg.get_role_function()
        logger.debug(
            f"_on_new_role_function: got rf "
            f"name='{rf.name}', namespace='{rf.namespace}', "
            f"title='{rf.title}', qualified='{_qualified_name(rf)}'")

        if not rf.name:
            logger.warning(
                "_on_new_role_function: empty name -> abort")
            QMessageBox.warning(
                self, "Warning",
                "Role function name is required.")
            return
        if rf.name in self.state_machine.role_functions:
            logger.warning(
                f"_on_new_role_function: duplicate bare name "
                f"'{rf.name}' in state_machine")
            QMessageBox.warning(
                self, "Warning",
                "A role function with the same name already exists.")
            return

        try:
            self.state_machine.add_role_function(rf)
            logger.debug(
                f"_on_new_role_function: added to sm key='{rf.name}'")
        except ValueError as e:
            logger.warning(
                f"_on_new_role_function: add_role_function failed: {e}")
            QMessageBox.warning(self, "Warning", str(e))
            return

        self._dump_sm_roles("_on_new_role_function/after_add")

        qn = _qualified_name(rf)
        if qn and qn not in self.role_functions:
            self.role_functions.append(qn)
            self._sync_combo()
            logger.debug(
                f"_on_new_role_function: appended '{qn}' to local "
                f"role_functions (now {len(self.role_functions)})")

        self._append_row(qn)
        last_row = self.table.rowCount() - 1
        self.table.setCurrentCell(last_row, 0)
        self.changed.emit()
        logger.info(f"Role function created: {qn}")
        logger.debug("=== _on_new_role_function: EXIT (ok) ===")

    def _on_edit_role_function(self):
        """v2.5: edit the role function bound to the selected row."""
        logger.debug("=== _on_edit_role_function: ENTER ===")
        row = self.table.currentRow()
        logger.debug(f"_on_edit_role_function: currentRow={row}")
        if row < 0:
            QMessageBox.information(
                self, "Information", "Please select a row first.")
            return
        item = self.table.item(row, 0)
        if item is None:
            logger.warning(
                f"_on_edit_role_function: no item at row {row}")
            return
        display_name = item.text().strip()
        logger.debug(
            f"_on_edit_role_function: display_name='{display_name}'")
        if not display_name:
            logger.warning(
                "_on_edit_role_function: empty display_name")
            return

        if self.state_machine is None:
            logger.warning(
                "_on_edit_role_function: state_machine is None")
            QMessageBox.information(
                self, "Information",
                "StateMachine is not available.")
            return

        self._dump_sm_roles("_on_edit_role_function/before_lookup")

        # [fix] Resolve via qualified_name -> RoleFunction object,
        #       then use its bare name as the StateMachine dict key.
        rf = self._find_rf_by_display(display_name)
        if rf is None:
            logger.warning(
                f"_on_edit_role_function: could not resolve "
                f"'{display_name}'")
            QMessageBox.information(
                self, "Information",
                f"Role function '{display_name}' is not registered in "
                "this state machine.\nOnly state-machine-owned role "
                "functions can be edited here.")
            return
        pure_name = rf.name
        logger.debug(
            f"_on_edit_role_function: resolved '{display_name}' -> "
            f"pure_name='{pure_name}'")

        dlg = RoleFunctionDialog(
            self, role_function=rf, **self._dialog_kwargs())
        logger.debug("_on_edit_role_function: dialog opened")
        if dlg.exec() != QDialog.Accepted:
            logger.debug("_on_edit_role_function: dialog cancelled")
            return

        updated = dlg.get_role_function()
        logger.debug(
            f"_on_edit_role_function: updated "
            f"name='{updated.name}', namespace='{updated.namespace}', "
            f"qualified='{_qualified_name(updated)}'")

        if (updated.name != pure_name
                and updated.name in self.state_machine.role_functions):
            logger.warning(
                f"_on_edit_role_function: rename to '{updated.name}' "
                f"collides with existing entry")
            QMessageBox.warning(
                self, "Warning",
                "A role function with the same name already exists.")
            return

        # [fix] remove_role_function takes the BARE name (dict key).
        logger.debug(
            f"_on_edit_role_function: removing old key '{pure_name}'")
        self.state_machine.remove_role_function(pure_name)
        try:
            self.state_machine.add_role_function(updated)
            logger.debug(
                f"_on_edit_role_function: added new key "
                f"'{updated.name}'")
        except ValueError as e:
            logger.warning(
                f"_on_edit_role_function: add_role_function failed: {e} "
                f"-> rollback")
            # Roll back: re-add the original to avoid losing it
            try:
                self.state_machine.add_role_function(rf)
                logger.debug(
                    "_on_edit_role_function: rollback succeeded")
            except Exception as e2:
                logger.error(
                    f"_on_edit_role_function: rollback failed: {e2}")
            QMessageBox.warning(self, "Warning", str(e))
            return

        self._dump_sm_roles("_on_edit_role_function/after_update")

        new_qn = _qualified_name(updated)
        item.setText(new_qn)
        logger.debug(
            f"_on_edit_role_function: row {row} text -> '{new_qn}'")

        # Keep the combo / role_functions list in sync
        for i, n in enumerate(self.role_functions):
            if n == display_name:
                self.role_functions[i] = new_qn
                logger.debug(
                    f"_on_edit_role_function: role_functions[{i}] "
                    f"'{n}' -> '{new_qn}'")
                break
        else:
            if new_qn and new_qn not in self.role_functions:
                self.role_functions.append(new_qn)
                logger.debug(
                    f"_on_edit_role_function: appended '{new_qn}' "
                    f"to role_functions")
        self._sync_combo()

        # Also rewrite any other rows referencing the old name
        for r in range(self.table.rowCount()):
            if r == row:
                continue
            it = self.table.item(r, 0)
            if it is not None and it.text().strip() == display_name:
                it.setText(new_qn)
                logger.debug(
                    f"_on_edit_role_function: row {r} also updated "
                    f"-> '{new_qn}'")

        self.changed.emit()
        logger.info(
            f"Role function updated: '{display_name}' -> '{new_qn}' "
            f"(pure name: '{pure_name}' -> '{updated.name}')")
        logger.debug("=== _on_edit_role_function: EXIT (ok) ===")

    def _on_delete_role_function(self):
        """v2.5: delete the selected role function from the state machine."""
        logger.debug("=== _on_delete_role_function: ENTER ===")
        row = self.table.currentRow()
        logger.debug(f"_on_delete_role_function: currentRow={row}")
        if row < 0:
            QMessageBox.information(
                self, "Information", "Please select a row first.")
            return
        item = self.table.item(row, 0)
        if item is None:
            logger.warning(
                f"_on_delete_role_function: no item at row {row}")
            return
        display_name = item.text().strip()
        logger.debug(
            f"_on_delete_role_function: display_name='{display_name}'")
        if not display_name:
            logger.warning(
                "_on_delete_role_function: empty display_name")
            return

        if self.state_machine is None:
            logger.warning(
                "_on_delete_role_function: state_machine is None")
            QMessageBox.information(
                self, "Information",
                "StateMachine is not available.")
            return

        self._dump_sm_roles("_on_delete_role_function/before_lookup")

        # [fix] Resolve via qualified_name -> RoleFunction object.
        rf = self._find_rf_by_display(display_name)
        if rf is None:
            logger.warning(
                f"_on_delete_role_function: could not resolve "
                f"'{display_name}'")
            QMessageBox.information(
                self, "Information",
                f"Role function '{display_name}' is not registered in "
                "this state machine.")
            return
        pure_name = rf.name
        logger.debug(
            f"_on_delete_role_function: resolved '{display_name}' -> "
            f"pure_name='{pure_name}'")

        reply = QMessageBox.question(
            self, "Confirm delete",
            f"Delete role function '{display_name}' from the state "
            "machine?\nThis removes it from all cells in this layer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No)
        if reply != QMessageBox.Yes:
            logger.debug(
                "_on_delete_role_function: user declined -> abort")
            return

        # [fix] remove_role_function takes the BARE name.
        logger.debug(
            f"_on_delete_role_function: removing key '{pure_name}'")
        self.state_machine.remove_role_function(pure_name)

        self._dump_sm_roles("_on_delete_role_function/after_remove")

        # Remove all rows referencing this display name
        removed_rows = 0
        for r in range(self.table.rowCount() - 1, -1, -1):
            it = self.table.item(r, 0)
            if it is not None and it.text().strip() == display_name:
                self.table.removeRow(r)
                removed_rows += 1
        logger.debug(
            f"_on_delete_role_function: removed {removed_rows} row(s) "
            f"from table")

        if display_name in self.role_functions:
            self.role_functions.remove(display_name)
            logger.debug(
                f"_on_delete_role_function: removed '{display_name}' "
                f"from role_functions (now {len(self.role_functions)})")
        self._sync_combo()

        self.changed.emit()
        logger.info(
            f"Role function deleted: '{display_name}' "
            f"(pure name: '{pure_name}')")
        logger.debug("=== _on_delete_role_function: EXIT (ok) ===")


class ActionsTab(QWidget):
    """Pre / Post Actions tab."""

    actions_changed = Signal()

    def __init__(self, draft: ActionDraft,
                 role_functions: Optional[List[str]] = None,
                 global_defs=None, state_machine=None,
                 role_function_library=None,
                 literal_library=None,
                 layer_names_provider=None,
                 parent=None):
        super().__init__(parent)
        self.draft = draft
        self.role_functions = list(role_functions or [])
        self.global_defs = global_defs
        self.state_machine = state_machine
        # v2.5: context for RoleFunctionDialog
        self.role_function_library = role_function_library
        self.literal_library = literal_library
        self.layer_names_provider = layer_names_provider

        logger.debug(
            f"ActionsTab.__init__: role_functions={len(self.role_functions)}, "
            f"has_sm={state_machine is not None}, "
            f"has_rflib={role_function_library is not None}, "
            f"has_litlib={literal_library is not None}, "
            f"has_lnp={layer_names_provider is not None}")

        self._build_ui()

    def set_role_functions(self, names: List[str]):
        self.role_functions = list(names or [])
        self.pre_group.set_role_functions(self.role_functions)
        self.post_group.set_role_functions(self.role_functions)
        logger.debug(
            f"ActionsTab.set_role_functions: {len(self.role_functions)} "
            f"candidates")

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Cell-level actions:\n"
            "  Pre  = before the transition chain (runs even if no transition fires)\n"
            "  Post = after the transition chain (runs even after early return)"))

        self.pre_group = _ActionGroup(
            "Pre (before transitions)", TRIGGER_PRE, self.role_functions,
            role_function_library=self.role_function_library,
            literal_library=self.literal_library,
            layer_names_provider=self.layer_names_provider,
            global_defs=self.global_defs,
            state_machine=self.state_machine,
        )
        self.pre_group.changed.connect(self._on_changed)
        layout.addWidget(self.pre_group)

        self.post_group = _ActionGroup(
            "Post (after transitions)", TRIGGER_POST, self.role_functions,
            role_function_library=self.role_function_library,
            literal_library=self.literal_library,
            layer_names_provider=self.layer_names_provider,
            global_defs=self.global_defs,
            state_machine=self.state_machine,
        )
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