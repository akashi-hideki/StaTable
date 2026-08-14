from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QDialog
)

from statable.model import Transition
from statable.state_machine import StateMachine

from .logger import StaTableLogger
from .config import MAX_COLUMN_WIDTH, MIN_ROW_HEIGHT, MAX_ROW_HEIGHT
from .dialogs import TransitionListDialog


class MatrixTableWidget(QTableWidget):
    """状態遷移マトリックス表示・編集テーブル（行=イベント、列=状態）"""
    transition_changed = Signal()

    def __init__(self, sm: StateMachine, parent=None):
        super().__init__(0, 0, parent)
        self.sm = sm

        # 列幅・行高さをユーザーがドラッグで調整可能に
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)

        # 最後の列を伸縮させて余白を埋める
        self.horizontalHeader().setStretchLastSection(True)

        # 垂直ヘッダー（イベント名）の最小幅を設定
        self.verticalHeader().setMinimumWidth(120)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cellDoubleClicked.connect(self.open_transition_dialog)
        self.setFont(QFont("Consolas", 10))

        self.populate()
        StaTableLogger.debug("MatrixTableWidget initialized")

    def populate(self):
        """状態遷移マトリックスを再構築（行=イベント、列=状態）"""
        states = list(self.sm.states.keys())
        events = list(self.sm.events.keys())
        self.clear()
        self.setRowCount(len(events))
        self.setColumnCount(len(states))
        self.setHorizontalHeaderLabels(states)
        self.setVerticalHeaderLabels([e if e else "完了" for e in events])

        for row, event in enumerate(events):
            for col, state in enumerate(states):
                trans_list = self._find_transitions(state, event)
                if trans_list:
                    titles = [self._generate_title(t) for t in trans_list]
                    display = "\n".join(titles)
                    item = QTableWidgetItem(display)
                    item.setData(Qt.UserRole, trans_list)
                    item.setToolTip("ダブルクリックまたは Enter で編集")
                    self.setItem(row, col, item)
                else:
                    item = QTableWidgetItem("")
                    item.setData(Qt.UserRole, [])
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
        return [t for t in self.sm.transitions if t.source == state and t.event == event]

    def _generate_title(self, trans: Transition) -> str:
        if trans.target:
            parts = [trans.target]
            if trans.guard:
                parts.append(f"[{trans.guard}]")
            if trans.action:
                parts.append(f"/ {trans.action}")
            return " ".join(parts)
        else:
            return f"internal: {trans.event or '完了'} / {trans.action}".strip()

    def open_transition_dialog(self, row: int, col: int):
        """行=イベント、列=状態として遷移編集ダイアログを開く"""
        state = self.horizontalHeaderItem(col).text() if self.horizontalHeaderItem(col) else ""
        event = self.verticalHeaderItem(row).text() if self.verticalHeaderItem(row) else ""
        if event == "完了":
            event_name = ""
        else:
            event_name = event

        item = self.item(row, col)
        existing_list = item.data(Qt.UserRole) if item else []

        dlg = TransitionListDialog(
            self,
            state_names=list(self.sm.states.keys()),
            event_name=event_name,
            existing_transitions=existing_list,
            role_functions=self.sm.role_functions
        )

        if dlg.exec() == QDialog.Accepted:
            new_transitions = dlg.get_transitions()
            self.sm.transitions = [t for t in self.sm.transitions
                                   if not (t.source == state and t.event == event_name)]
            for trans in new_transitions:
                trans.source = state
                trans.event = event_name
                self.sm.add_transition(trans)
            self.populate()
            self.transition_changed.emit()
            StaTableLogger.info(f"Transition updated: {state} -{event_name or '完了'}-> {len(new_transitions)} transition(s)")

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
                        self.sm.transitions.remove(trans)
                    self.populate()
                    self.transition_changed.emit()
                    StaTableLogger.info(f"Transition deleted: {len(trans_list)} transition(s)")
            return
        super().keyPressEvent(event)