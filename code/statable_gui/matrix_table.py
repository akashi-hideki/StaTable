# statable_gui/matrix_table.py
"""State transition table widget (D&D editor direct launch support / v2.2 multi-transition).

[R-6 change]
  MatrixTableWidget now accepts `layer_names_provider` and forwards
  it to ActionEditorDialog, completing the all-tabs namespace wiring.
"""

from typing import List, Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QDialog
)

from statable.model import Transition, EventDeliveryType
from statable.state_machine import StateMachine

from .logger import StaTableLogger
from .config import MAX_COLUMN_WIDTH, MIN_ROW_HEIGHT, MAX_ROW_HEIGHT
from .global_defs import GlobalDefinitions

from .transition_editor_direct.dialog import ActionEditorDialog
from .transition_editor_direct.draft import (
    ActionDraft, transition_to_flow_item, flow_item_to_transition,
)

from statable_gui.libcntrl.role_function_library import RoleFunctionLibrary
from statable_gui.libcntrl.condition_library import ConditionLibrary
from statable_gui.libcntrl.literal_library import LiteralLibrary


# ======================================================================
# Helpers
# ======================================================================
def _truncate_text(text: str, max_chars: int = 40) -> str:
    if not text:
        return ""
    lines = text.split('\n')
    first_line = lines[0].strip() if lines else ""
    if len(first_line) > max_chars:
        return first_line[:max_chars].rstrip() + "..."
    if len(lines) > 1:
        return first_line + " ..."
    return first_line


def _mode_marker(trans: Transition) -> str:
    """Return the mode marker for a transition.

      " [C]" -> Commit    (early_return=True)
      " [T]" -> Tentative (early_return=False)
      ""     -> not specified (backward compat)
    """
    er = getattr(trans, 'early_return', None)
    if er is True:
        return " [C]"
    if er is False:
        return " [T]"
    return ""


def _mode_label(trans: Transition) -> str:
    """Human-readable mode label for tooltips."""
    er = getattr(trans, 'early_return', None)
    if er is True:
        return "Commit"
    if er is False:
        return "Tentative"
    return "(unset)"


def _build_transition_tooltip(trans: Transition) -> str:
    parts = []
    parts.append(f"Title: {trans.title}")
    parts.append(f"Target: {trans.target if trans.target else '(internal)'}")
    if trans.event:
        parts.append(f"Event: {trans.event}")
    else:
        parts.append("Event: Completion transition")
    if trans.condition:
        parts.append(f"State transition condition:\n{trans.condition}")
    parts.append(f"Mode: {_mode_label(trans)}")
    if getattr(trans, 'has_else', False):
        else_t = getattr(trans, 'else_target', '') or '(not set)'
        parts.append(f"else target: {else_t}")
    lbl = getattr(trans, 'label', '')
    if lbl:
        parts.append(f"Label: {lbl}")
    return "\n".join(parts)


def _event_header_label(event_name: str, delivery_type) -> str:
    if delivery_type == EventDeliveryType.QUEUE:
        return f"[Q] {event_name}"
    elif delivery_type == EventDeliveryType.DOUBLE:
        return f"[D] {event_name}"
    return event_name


class MatrixTableWidget(QTableWidget):
    transition_changed = Signal()

    def __init__(self, sm: StateMachine, global_defs: GlobalDefinitions = None,
                 role_function_library: RoleFunctionLibrary = None,
                 condition_library: ConditionLibrary = None,
                 literal_library: LiteralLibrary = None,
                 layer_names_provider: Callable[[], List[str]] = None,
                 parent=None):
        super().__init__(0, 0, parent)
        self.sm = sm
        self.global_defs = global_defs if global_defs else GlobalDefinitions()

        self.role_function_library = role_function_library if role_function_library else RoleFunctionLibrary()
        self.condition_library = condition_library if condition_library else ConditionLibrary()
        self.literal_library = literal_library if literal_library else LiteralLibrary()
        # [R-6] All-tabs namespace provider (forwarded to ActionEditorDialog).
        self.layer_names_provider = layer_names_provider

        StaTableLogger.debug(
            f"MatrixTableWidget.__init__: roles={len(self.role_function_library.list_all())}, "
            f"conditions={len(self.condition_library.list_all())}, "
            f"literals={len(self.literal_library.list_all())}, "
            f"has_lnp={layer_names_provider is not None}"
        )

        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setMinimumWidth(120)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cellDoubleClicked.connect(self.open_transition_dialog)
        self.setFont(QFont("Consolas", 10))

        self.populate()
        StaTableLogger.debug("MatrixTableWidget initialized")

    def populate(self):
        states = list(self.sm.states.keys())
        events = list(self.sm.events.keys())
        self.clear()
        self.setRowCount(len(events))
        self.setColumnCount(len(states))
        self.setHorizontalHeaderLabels(states)

        event_labels = []
        for event_name in events:
            event_obj = self.sm.events.get(event_name)
            delivery = event_obj.delivery_type if event_obj else EventDeliveryType.DIRECT
            event_labels.append(_event_header_label(
                event_name if event_name else "Completion", delivery))
        self.setVerticalHeaderLabels(event_labels)

        for row, event in enumerate(events):
            for col, state in enumerate(states):
                trans_list = self._find_transitions(state, event)
                if trans_list:
                    titles = [self._generate_cell_label(t, event) for t in trans_list]
                    display = "\n".join(titles)
                    item = QTableWidgetItem(display)
                    item.setData(Qt.UserRole, trans_list)
                    tooltips = [_build_transition_tooltip(t) for t in trans_list]
                    full_tooltip = "\n\n".join(tooltips)
                    item.setToolTip(full_tooltip)
                    self.setItem(row, col, item)
                else:
                    item = QTableWidgetItem("")
                    item.setData(Qt.UserRole, [])
                    item.setToolTip("TransitionNone")
                    self.setItem(row, col, item)

        self.resizeColumnsToContents()
        self.resizeRowsToContents()

        for col in range(self.columnCount()):
            current_width = self.columnWidth(col)
            if current_width > MAX_COLUMN_WIDTH:
                self.setColumnWidth(col, MAX_COLUMN_WIDTH)

        for row in range(self.rowCount()):
            current_height = self.rowHeight(row)
            if current_height < MIN_ROW_HEIGHT:
                self.setRowHeight(row, MIN_ROW_HEIGHT)
            elif current_height > MAX_ROW_HEIGHT:
                self.setRowHeight(row, MAX_ROW_HEIGHT)

        StaTableLogger.debug(
            f"MatrixTable populated: {len(events)} events, {len(states)} states")

    def _find_transitions(self, state: str, event: str) -> List[Transition]:
        return self.sm.get_transitions_for_cell(state, event)

    def _generate_cell_label(self, trans: Transition, event: str) -> str:
        parts = []
        if trans.title and trans.title != "(untitled transition)":
            parts.append(trans.title)
        else:
            if trans.target:
                parts.append(trans.target)
            else:
                parts.append("(internal)")
        if event:
            parts.append(f"({event})")
        if trans.condition:
            condition_display = _truncate_text(trans.condition, 30)
            parts.append(f"[{condition_display}]")

        marker = _mode_marker(trans)
        if marker:
            parts.append(marker.strip())

        lbl = getattr(trans, 'label', '')
        if lbl:
            parts.append(f"<{lbl}>")

        return " ".join(parts)

    def _generate_title(self, trans: Transition) -> str:
        parts = []
        if trans.target:
            parts.append(trans.target)
        else:
            parts.append("(internal)")
        if trans.condition:
            condition_display = _truncate_text(trans.condition, 30)
            parts.append(f"[{condition_display}]")
        marker = _mode_marker(trans)
        if marker:
            parts.append(marker.strip())
        return " ".join(parts)

    def open_transition_dialog(self, row: int, col: int):
        """Open the transition edit dialog."""
        state = self.horizontalHeaderItem(col).text() if self.horizontalHeaderItem(col) else ""
        raw_event = self.verticalHeaderItem(row).text() if self.verticalHeaderItem(row) else ""
        event_name = raw_event
        if event_name.startswith("[Q] "):
            event_name = event_name[4:]
        elif event_name.startswith("[D] "):
            event_name = event_name[4:]
        if event_name == "Completion":
            event_name = ""

        StaTableLogger.debug(f"=== MatrixTableWidget.open_transition_dialog ===")
        StaTableLogger.debug(f"state={state}, event={event_name}")

        existing_list = self._find_transitions(state, event_name)
        StaTableLogger.debug(f"existing transitions count = {len(existing_list)}")

        layer_name = getattr(self.sm, 'layer_name', '') or ''

        draft = ActionDraft(
            source=state,
            event=event_name,
            layer_name=layer_name,
        )
        for trans in existing_list:
            fi = transition_to_flow_item(trans)
            draft.flow_items.append(fi)

        # === v2.2: populate cell_actions / cell_relations from SM ===
        draft.cell_actions = list(
            self.sm.get_actions_for_cell(state, event_name)
        )
        draft.cell_relations = list(
            self.sm.get_relations_for_cell(state, event_name)
        )

        # Merge shared library and current SM role functions
        role_func_names = []
        _seen = set()
        for rf in self.role_function_library.list_all():
            qn = getattr(rf, 'qualified_name', None) or rf.name
            if qn and qn not in _seen:
                _seen.add(qn)
                role_func_names.append(qn)
        for rf in self.sm.role_functions.values():
            qn = getattr(rf, 'qualified_name', None) or rf.name
            if qn and qn not in _seen:
                _seen.add(qn)
                role_func_names.append(qn)

        states = list(self.sm.states.keys())

        StaTableLogger.debug(
            f"open_transition_dialog: merged roles={len(role_func_names)} "
            f"(library={len(self.role_function_library.list_all())}, "
            f"sm={len(self.sm.role_functions)}), "
            f"conditions={len(self.condition_library.list_all())}, "
            f"literals={len(self.literal_library.list_all())}, "
            f"has_lnp={self.layer_names_provider is not None}"
        )

        dialog = ActionEditorDialog(
            draft,
            role_functions=role_func_names,
            transition_events=[event_name] if event_name else [],
            states=states,
            global_defs=self.global_defs,
            state_machine=self.sm,
            role_function_library=self.role_function_library,
            condition_library=self.condition_library,
            literal_library=self.literal_library,
            # [R-6] Forward provider so TransitionsTab / ActionsTab
            #       inside the dialog list every layer in the project.
            layer_names_provider=self.layer_names_provider,
            parent=self
        )

        if dialog.exec() == QDialog.Accepted:
            new_transitions = []
            for item in draft.flow_items:
                if item.item_type == "transition":
                    new_transitions.append(
                        flow_item_to_transition(item, state, event_name)
                    )

            StaTableLogger.debug(
                f"  -> D&D editor accepted, {len(new_transitions)} transitions")

            # === v2.2: write back cell metadata from draft ===
            self.sm.set_actions_for_cell(state, event_name,
                                          list(draft.cell_actions))
            self.sm.set_relations_for_cell(state, event_name,
                                            list(draft.cell_relations))

            # Replace transitions in the cell
            self.sm.transitions = [
                t for t in self.sm.transitions
                if not (t.source == state and t.event == event_name)
            ]
            for trans in new_transitions:
                self.sm.add_transition(trans)

            self.populate()
            self.transition_changed.emit()
            StaTableLogger.info(
                f"Transition updated: {state} -{event_name or 'Completion'}-> "
                f"{len(new_transitions)} transition(s), "
                f"actions={len(draft.cell_actions)}, "
                f"relations={len(draft.cell_relations)}")
        else:
            StaTableLogger.debug("  -> D&D editor cancelled")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_F2):
            current = self.currentItem()
            if current:
                self.open_transition_dialog(current.row(), current.column())
            return
        elif event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            current = self.currentItem()
            if current:
                trans_list = current.data(Qt.UserRole)
                if trans_list:
                    for trans in trans_list:
                        self.sm.remove_transition(trans)
                    state = self.horizontalHeaderItem(
                        current.column()).text() if self.horizontalHeaderItem(current.column()) else ""
                    raw_event = self.verticalHeaderItem(
                        current.row()).text() if self.verticalHeaderItem(current.row()) else ""
                    event_name = raw_event
                    if event_name.startswith("[Q] "):
                        event_name = event_name[4:]
                    elif event_name.startswith("[D] "):
                        event_name = event_name[4:]
                    if event_name == "Completion":
                        event_name = ""
                    self.sm.remove_cell_metadata(state, event_name)

                    self.populate()
                    self.transition_changed.emit()
                    StaTableLogger.info(
                        f"Transition deleted: {len(trans_list)} transition(s)")
            return
        super().keyPressEvent(event)