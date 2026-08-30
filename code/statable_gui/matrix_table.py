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
from .dialogs import TransitionListDialog
from .global_defs import GlobalDefinitions


def _truncate_text(text: str, max_chars: int = 40) -> str:
    """長いテキストを省略表示する"""
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
    """遷移の完全な情報をツールチップ用に整形"""
    parts = []
    parts.append(f"タイトル: {trans.title}")
    parts.append(f"遷移先: {trans.target if trans.target else '(内部)'}")
    if trans.event:
        parts.append(f"イベント: {trans.event}")
    else:
        parts.append("イベント: 完了遷移")
    if trans.condition:
        parts.append(f"状態遷移条件:\n{trans.condition}")
    if trans.action:
        parts.append(f"動作:\n{trans.action}")
    return "\n".join(parts)


def _event_header_label(event_name: str, delivery_type) -> str:
    """イベント名に配送タイプのプレフィックスを付ける"""
    if delivery_type == EventDeliveryType.QUEUE:
        return f"[Q] {event_name}"
    elif delivery_type == EventDeliveryType.DOUBLE:
        return f"[D] {event_name}"
    return event_name


class MatrixTableWidget(QTableWidget):
    """状態遷移マトリックス表示・編集テーブル（行=イベント、列=状態）"""
    transition_changed = Signal()

    def __init__(self, sm: StateMachine, global_defs: GlobalDefinitions = None, parent=None):
        super().__init__(0, 0, parent)
        self.sm = sm
        self.global_defs = global_defs if global_defs else GlobalDefinitions()

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

        # イベントヘッダに配送タイプを含める
        event_labels = []
        for event_name in events:
            event_obj = self.sm.events.get(event_name)
            delivery = event_obj.delivery_type if event_obj else EventDeliveryType.DIRECT
            event_labels.append(_event_header_label(event_name if event_name else "完了", delivery))
        self.setVerticalHeaderLabels(event_labels)

        for row, event in enumerate(events):
            for col, state in enumerate(states):
                trans_list = self._find_transitions(state, event)
                if trans_list:
                    # タイトル＋イベント名の形式で表示
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
                    item.setToolTip("遷移なし")
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
        """セル表示用ラベル（タイトル＋イベント名）"""
        parts = []

        # タイトル（無題遷移以外）
        if trans.title and trans.title != "(無題遷移)":
            parts.append(trans.title)
        else:
            # 遷移先を表示
            if trans.target:
                parts.append(trans.target)
            else:
                parts.append("(内部)")

        # イベント名
        if event:
            parts.append(f"({event})")

        # 状態遷移条件（短縮）
        if trans.condition:
            condition_display = _truncate_text(trans.condition, 30)
            parts.append(f"[{condition_display}]")

        return " ".join(parts)

    def _generate_title(self, trans: Transition) -> str:
        """旧タイトル生成（互換用）"""
        parts = []
        if trans.target:
            parts.append(trans.target)
        else:
            parts.append("(内部)")
        if trans.condition:
            condition_display = _truncate_text(trans.condition, 30)
            parts.append(f"[{condition_display}]")
        if trans.action:
            action_display = _truncate_text(trans.action, 30)
            parts.append(f"/ {action_display}")
        return " ".join(parts)

    def open_transition_dialog(self, row: int, col: int):
        state = self.horizontalHeaderItem(col).text() if self.horizontalHeaderItem(col) else ""
        raw_event = self.verticalHeaderItem(row).text() if self.verticalHeaderItem(row) else ""
        event_name = raw_event
        if event_name.startswith("[Q] "):
            event_name = event_name[4:]
        elif event_name.startswith("[D] "):
            event_name = event_name[4:]
        if event_name == "完了":
            event_name = ""

        StaTableLogger.debug(f"MatrixTableWidget.open_transition_dialog: row={row}, col={col}, state='{state}', event='{event_name}'")

        item = self.item(row, col)
        existing_list = item.data(Qt.UserRole) if item else []
        StaTableLogger.debug(f"  -> existing transitions: {len(existing_list)}")

        dlg = TransitionListDialog(
            self,
            state_names=list(self.sm.states.keys()),
            event_name=event_name,
            existing_transitions=existing_list,
            role_functions=self.sm.role_functions,
            global_defs=self.global_defs
        )

        if dlg.exec() == QDialog.Accepted:
            new_transitions = dlg.get_transitions()
            StaTableLogger.debug(f"  -> TransitionListDialog accepted, {len(new_transitions)} transitions")
            self.sm.transitions = [t for t in self.sm.transitions
                                   if not (t.source == state and t.event == event_name)]
            for trans in new_transitions:
                trans.source = state
                trans.event = event_name
                self.sm.add_transition(trans)
            self.populate()
            self.transition_changed.emit()
            StaTableLogger.info(f"Transition updated: {state} -{event_name or '完了'}-> {len(new_transitions)} transition(s)")
        else:
            StaTableLogger.debug("  -> TransitionListDialog cancelled")

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