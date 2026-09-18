# statable_gui/matrix_table.py
"""\nState transition table widget (D&D editor direct launch support)\n"""

from typing import List

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
from .transition_editor_direct.draft import ActionDraft, transition_to_flow_item, flow_item_to_transition

from statable_gui.libcntrl.role_function_library import RoleFunctionLibrary
from statable_gui.libcntrl.condition_library import ConditionLibrary
from statable_gui.libcntrl.literal_library import LiteralLibrary
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


def _build_transition_tooltip(trans: Transition) -> str:
    parts = []
    parts.append(f"タイトル: {trans.title}")
    parts.append(f"遷移先: {trans.target if trans.target else '(internal)'}")
    if trans.event:
        parts.append(f"イベント: {trans.event}")
    else:
        parts.append("Event: Completion transition")
    if trans.condition:
        parts.append(f"状態遷移条件:\n{trans.condition}")
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
                 parent=None):
        super().__init__(0, 0, parent)
        self.sm = sm
        self.global_defs = global_defs if global_defs else GlobalDefinitions()

        self.role_function_library = role_function_library if role_function_library else RoleFunctionLibrary()
        self.condition_library = condition_library if condition_library else ConditionLibrary()
        self.literal_library = literal_library if literal_library else LiteralLibrary()

        # Debug log: shared library content at MatrixTableWidget initialization
        StaTableLogger.debug(
            f"MatrixTableWidget.__init__: roles={len(self.role_function_library.list_all())}, "
            f"conditions={len(self.condition_library.list_all())}, "
            f"literals={len(self.literal_library.list_all())}"
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
            event_labels.append(_event_header_label(event_name if event_name else "Completion", delivery))
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

        StaTableLogger.debug(f"MatrixTable populated: {len(events)} events, {len(states)} states")

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
        return " ".join(parts)
    def open_transition_dialog(self, row: int, col: int):
        """\n        Open the transition edit dialog\n\n        [v1.6 change] pass layer_name to ActionDraft (section 11.2 #4)\n          code_widget._get_layer_name() gives this the highest priority,\n          so explicitly propagate the SM's layer name here.\n        """
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
        for i, t in enumerate(existing_list):
            StaTableLogger.debug(f"  existing[{i}]: condition='{t.condition}', pre_actions={t.pre_actions}, target={t.target}, title={t.title}")

        # v1.6: get SM's layer_name (if empty, defer to code_widget's fallback)
        layer_name = getattr(self.sm, 'layer_name', '') or ''

        draft = ActionDraft(
            source=state,
            event=event_name,
            layer_name=layer_name,   # v1.6 added
        )
        for trans in existing_list:
            fi = transition_to_flow_item(trans)
            StaTableLogger.debug(f"  converted flow_item: {fi}")
            draft.flow_items.append(fi)

        # Merge shared library and current SM role functions
        #    (Allow selecting SM's local functions even when the shared library is empty)
        #   From Stage 1/4, role functions are handled by qualified_name (e.g., 'Driver.Init')
        role_func_names = []
        _seen = set()

        # 1. From shared library
        for rf in self.role_function_library.list_all():
            qn = getattr(rf, 'qualified_name', None) or rf.name
            if qn and qn not in _seen:
                _seen.add(qn)
                role_func_names.append(qn)

        # 2. 現在の SM のRole functionから
        for rf in self.sm.role_functions.values():
            qn = getattr(rf, 'qualified_name', None) or rf.name
            if qn and qn not in _seen:
                _seen.add(qn)
                role_func_names.append(qn)

        states = list(self.sm.states.keys())

        # Debug log: content passed to ActionEditorDialog
        StaTableLogger.debug(
            f"open_transition_dialog: merged roles={len(role_func_names)} "
            f"(library={len(self.role_function_library.list_all())}, "
            f"sm={len(self.sm.role_functions)}), "
            f"conditions={len(self.condition_library.list_all())}, "
            f"literals={len(self.literal_library.list_all())}"
        )
        for qn in role_func_names:
            StaTableLogger.debug(f"  role to dialog: {qn}")
        for ct in self.condition_library.list_all():
            StaTableLogger.debug(f"  condition to dialog: {ct.name}")

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
            parent=self
        )

        if dialog.exec() == QDialog.Accepted:
            new_transitions = []
            for item in draft.flow_items:
                if item.item_type == "transition":
                    new_transitions.append(flow_item_to_transition(item, state, event_name))

            StaTableLogger.debug(f"  -> D&D editor accepted, {len(new_transitions)} transitions")
            self.sm.transitions = [t for t in self.sm.transitions
                                   if not (t.source == state and t.event == event_name)]
            for trans in new_transitions:
                self.sm.add_transition(trans)
            self.populate()
            self.transition_changed.emit()
            StaTableLogger.info(f"Transition updated: {state} -{event_name or 'Completion'}-> {len(new_transitions)} transition(s)")
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
                    self.populate()
                    self.transition_changed.emit()
                    StaTableLogger.info(f"Transition deleted: {len(trans_list)} transition(s)")
            return
        super().keyPressEvent(event)