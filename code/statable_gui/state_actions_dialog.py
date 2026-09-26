# statable_gui/state_actions_dialog.py
"""
State actions (Entry / Exit / Do) editing dialog.

Version: 1.0 (2026-09-26 / Phase 4a)

Provides StateActionsDialog: a 4-tab editor for per-state actions.

Tabs:
  - Entry:   actions executed once when entering the state
  - Exit:    actions executed once when leaving the state
  - Do:      actions executed every loop while in the state
  - Preview: generated C code preview

Each action tab contains:
  - Action list (QTableWidget: Type / Target / Condition)
  - Add / Delete / Up / Down buttons
  - Custom code marker hint (read-only)

On OK, updates State.entry / State.exit / State.do_actions.

Design notes:
  - Uses statable.model.ActionStep.
  - action_type: "role" (default) or "fire_event".
  - Empty Target rows are dropped on OK.
  - Custom code editing is done in the generated file
    (marker: [[STABLE_USER_CODE_START:<Layer>_<Kind>_<State>_custom]]).
"""

from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QDialogButtonBox, QTabWidget, QWidget,
    QLabel, QGroupBox, QHeaderView, QPlainTextEdit,
)

from statable.model import State, ActionStep
from statable.state_machine import StateMachine

from .logger import StaTableLogger


KIND_ENTRY = "Entry"
KIND_EXIT = "Exit"
KIND_DO = "Do"


class _ActionListWidget(QWidget):
    """Reusable action list editor.

    Columns:
      0: Type      ("role" or "fire_event")
      1: Target    (RoleFunc name, or Event name)
      2: Condition (C expression; empty = unconditional)
    """

    COL_TYPE = 0
    COL_TARGET = 1
    COL_CONDITION = 2

    VALID_TYPES = ("role", "fire_event")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Type", "Target", "Condition"])
        self.table.horizontalHeader().setSectionResizeMode(
            self.COL_TYPE, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(
            self.COL_TARGET, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            self.COL_CONDITION, QHeaderView.Stretch)
        self.table.setFont(QFont("Consolas", 10))
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("+ Add")
        self.add_btn.clicked.connect(self._on_add)
        self.del_btn = QPushButton("Delete")
        self.del_btn.clicked.connect(self._on_delete)
        self.up_btn = QPushButton("Up")
        self.up_btn.clicked.connect(self._on_up)
        self.down_btn = QPushButton("Down")
        self.down_btn.clicked.connect(self._on_down)
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.del_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.up_btn)
        btn_row.addWidget(self.down_btn)
        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _on_add(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, self.COL_TYPE,
                           QTableWidgetItem("role"))
        self.table.setItem(row, self.COL_TARGET,
                           QTableWidgetItem(""))
        self.table.setItem(row, self.COL_CONDITION,
                           QTableWidgetItem(""))
        self.table.editItem(self.table.item(row, self.COL_TARGET))

    def _on_delete(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def _on_up(self):
        row = self.table.currentRow()
        if row > 0:
            self._swap_rows(row, row - 1)
            self.table.selectRow(row - 1)

    def _on_down(self):
        row = self.table.currentRow()
        if 0 <= row < self.table.rowCount() - 1:
            self._swap_rows(row, row + 1)
            self.table.selectRow(row + 1)

    def _swap_rows(self, r1: int, r2: int):
        for col in range(self.table.columnCount()):
            i1 = self.table.takeItem(r1, col)
            i2 = self.table.takeItem(r2, col)
            self.table.setItem(r1, col, i2)
            self.table.setItem(r2, col, i1)

    # ------------------------------------------------------------------
    # Data binding
    # ------------------------------------------------------------------
    def set_actions(self, actions: List[ActionStep]):
        """Populate the table from a List[ActionStep]."""
        self.table.setRowCount(0)
        for a in (actions or []):
            row = self.table.rowCount()
            self.table.insertRow(row)

            atype = (getattr(a, "action_type", "role") or "role")
            if atype not in self.VALID_TYPES:
                atype = "role"

            if atype == "fire_event":
                target = getattr(a, "event_name", "") or ""
            else:
                target = getattr(a, "role_function", "") or ""

            cond = getattr(a, "condition", "") or ""

            self.table.setItem(row, self.COL_TYPE,
                               QTableWidgetItem(atype))
            self.table.setItem(row, self.COL_TARGET,
                               QTableWidgetItem(target))
            self.table.setItem(row, self.COL_CONDITION,
                               QTableWidgetItem(cond))

    def get_actions(self) -> List[ActionStep]:
        """Return the current table contents as List[ActionStep]."""
        result: List[ActionStep] = []
        for row in range(self.table.rowCount()):
            type_item = self.table.item(row, self.COL_TYPE)
            target_item = self.table.item(row, self.COL_TARGET)
            cond_item = self.table.item(row, self.COL_CONDITION)

            atype = (type_item.text().strip()
                     if type_item else "role") or "role"
            if atype not in self.VALID_TYPES:
                atype = "role"
            target = target_item.text().strip() if target_item else ""
            cond = cond_item.text().strip() if cond_item else ""

            if not target:
                # Empty target rows are dropped
                continue

            if atype == "fire_event":
                result.append(ActionStep(
                    action_type="fire_event",
                    event_name=target,
                    condition=cond,
                ))
            else:
                result.append(ActionStep(
                    action_type="role",
                    role_function=target,
                    condition=cond,
                ))
        return result


class StateActionsDialog(QDialog):
    """State actions (Entry / Exit / Do) editor.

    [Phase 4a]
      4 tabs: Entry / Exit / Do / Preview.
      Each action tab hosts an _ActionListWidget.
      On OK, updates State.entry / State.exit / State.do_actions.
    """

    KIND_TO_ATTR = {
        KIND_ENTRY: "entry",
        KIND_EXIT: "exit",
        KIND_DO: "do_actions",
    }

    def __init__(self, parent=None, state: Optional[State] = None,
                 state_machine: Optional[StateMachine] = None):
        super().__init__(parent)
        self.state = state
        self.state_machine = state_machine

        title_state = state.name if state is not None else "(unknown)"
        self.setWindowTitle(f"State actions - {title_state}")
        self.setMinimumSize(800, 600)

        self._setup_ui()
        self._load_state()
        StaTableLogger.debug(
            f"StateActionsDialog initialized: state={title_state}")

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Info label
        info = QLabel(
            "Entry / Exit / Do actions for this state.\n"
            "Custom C code can be edited in the generated file "
            "([[STABLE_USER_CODE_..._custom]] marker)."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Entry / Exit / Do tabs
        self.entry_widget = _ActionListWidget()
        self.exit_widget = _ActionListWidget()
        self.do_widget = _ActionListWidget()

        self.tabs.addTab(self.entry_widget, KIND_ENTRY)
        self.tabs.addTab(self.exit_widget, KIND_EXIT)
        self.tabs.addTab(self.do_widget, KIND_DO)

        # Preview tab
        self.preview_widget = QPlainTextEdit()
        self.preview_widget.setReadOnly(True)
        self.preview_widget.setFont(QFont("Consolas", 10))
        self.preview_widget.setPlaceholderText(
            "Click 'Refresh' to preview the generated C code.")
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        refresh_btn = QPushButton("Refresh preview")
        refresh_btn.clicked.connect(self._refresh_preview)
        preview_layout.addWidget(refresh_btn)
        preview_layout.addWidget(self.preview_widget)
        self.tabs.addTab(preview_container, "Preview")

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ------------------------------------------------------------------
    # Data binding
    # ------------------------------------------------------------------
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
            StaTableLogger.debug(
                f"StateActionsDialog OK: state={self.state.name}, "
                f"entry={len(self.state.entry)}, "
                f"exit={len(self.state.exit)}, "
                f"do={len(self.state.do_actions)}")
        self.accept()

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------
    def _refresh_preview(self):
        """Generate a small preview of what would be emitted for this state."""
        if self.state is None:
            self.preview_widget.setPlainText("(no state)")
            return

        state_name = self.state.name
        layer = "Layer"
        if self.state_machine is not None:
            layer = getattr(self.state_machine, "layer_name", "") or "Layer"

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
                        evt = getattr(a, "event_name", "") or ""
                        call = f"FIRE_EVENT_{layer}({evt})"
                    else:
                        rf = getattr(a, "role_function", "") or ""
                        call = f"(void)RoleFunc_{rf}(NULL, ctx)"
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


# ======================================================================
# Convenience entry point
# ======================================================================
def open_state_actions_dialog(parent, state, state_machine):
    """Open the dialog and return True if the user accepted."""
    dlg = StateActionsDialog(
        parent=parent, state=state, state_machine=state_machine)
    return dlg.exec() == QDialog.Accepted