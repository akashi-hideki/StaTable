"""イベント配送設定ダイアログ（タイトル表示対応版）"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QComboBox, QDialogButtonBox,
    QCheckBox, QAbstractItemView, QWidget
)
from PySide6.QtGui import QFont, QMouseEvent

from statable.state_machine import StateMachine
from statable.model import Event, EventDeliveryType
from statable.global_defs import GlobalDefinitions
from .logger import StaTableLogger


class DoubleClickTable(QTableWidget):
    """ダブルクリックを捕捉するテーブル"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        pos = event.position().toPoint()
        item = self.itemAt(pos)
        if item:
            row = item.row()
            StaTableLogger.debug(f"DoubleClickTable.mouseDoubleClickEvent: row={row}")
            self.cellDoubleClicked.emit(row, item.column())
        else:
            StaTableLogger.debug("DoubleClickTable.mouseDoubleClickEvent: no item")


class EventDeliverySettingsDialog(QDialog):
    """イベント配送タイプ（DIRECT/QUEUE）を設定し、ISR使用状況に応じてDOUBLE自動変換を表示するダイアログ"""

    def __init__(
        self,
        sm: StateMachine,
        global_defs: GlobalDefinitions,
        auto_convert: bool = True,
        parent=None
    ):
        super().__init__(parent)
        self.sm = sm
        self.global_defs = global_defs
        self.auto_convert = auto_convert

        self.setWindowTitle("イベント配送設定")
        self.setMinimumSize(900, 500)

        layout = QVBoxLayout(self)

        # グローバル設定チェックボックス
        self.auto_convert_check = QCheckBox("ISRで使用されるDIRECTイベントをDOUBLEに自動変換する")
        self.auto_convert_check.setChecked(self.auto_convert)
        layout.addWidget(self.auto_convert_check)

        # イベント一覧テーブル
        self.table = DoubleClickTable(0, 6)
        self.table.setHorizontalHeaderLabels(["タイトル", "イベント名", "発生源", "配送タイプ", "ISR使用", "変換後"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setFont(QFont("Consolas", 10))
        layout.addWidget(self.table, stretch=1)

        # ヘルプ
        help_label = QLabel(
            "DIRECTイベントがISRから通知される場合、自動的にDOUBLEへ変換されます。\n"
            "イベントの回数やデータが必要な場合はQUEUEを選択してください。"
        )
        help_label.setStyleSheet("color: gray;")
        layout.addWidget(help_label)

        # OK/Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._build_table()
        self.auto_convert_check.stateChanged.connect(self._update_converted_column)

        StaTableLogger.debug("EventDeliverySettingsDialog initialized")

    def _build_table(self):
        """テーブルを構築する"""
        self.table.setRowCount(0)
        events = list(self.sm.events.values())
        for event in events:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # タイトル（読み取り専用）
            title_item = QTableWidgetItem(event.title)
            title_item.setFlags(title_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, title_item)

            # イベント名（読み取り専用）
            name_item = QTableWidgetItem(event.name if event.name else "（完了）")
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, name_item)

            # 発生源（読み取り専用）
            source_item = QTableWidgetItem(event.source_layer.value)
            source_item.setFlags(source_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, source_item)

            # 配送タイプコンボ
            combo = QComboBox()
            combo.addItem("DIRECT", EventDeliveryType.DIRECT)
            combo.addItem("QUEUE", EventDeliveryType.QUEUE)
            combo.addItem("DOUBLE", EventDeliveryType.DOUBLE)
            idx = combo.findData(event.delivery_type)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            combo.currentIndexChanged.connect(lambda _index, r=row: self._on_delivery_changed(r))
            self.table.setCellWidget(row, 3, combo)

            # ISR使用列（読み取り専用）
            isr_used = self._check_isr_usage(event.name)
            isr_item = QTableWidgetItem("あり" if isr_used else "")
            isr_item.setFlags(isr_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 4, isr_item)

            # 変換後列（読み取り専用）
            converted_item = QTableWidgetItem()
            converted_item.setFlags(converted_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 5, converted_item)

            StaTableLogger.debug(
                f"  Event: '{event.name}' -> ISR used: {isr_used}"
            )

        self._update_converted_column()

    def _check_isr_usage(self, event_name: str) -> bool:
        """割り込み処理からイベントが使用されているか判定する"""
        if not event_name:
            return False

        for intr in self.global_defs.interrupts:
            # event_names リストをチェック
            if event_name in intr.event_names:
                StaTableLogger.debug(f"  '{event_name}' found in interrupt '{intr.name}' event_names")
                return True

            # actions 内のコードをチェック
            for act in intr.actions:
                combined = act.condition + "\n" + act.action
                if event_name in combined:
                    StaTableLogger.debug(f"  '{event_name}' found in interrupt '{intr.name}' action code")
                    return True

        return False

    def _find_row_by_event_name(self, event_name: str) -> int:
        """イベント名から行番号を探す"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)
            if item and item.text() == event_name:
                return row
        return -1

    def _on_delivery_changed(self, row: int):
        """配送タイプコンボ変更時に変換後列を更新"""
        self._update_converted_column()

    def _update_converted_column(self):
        """変換後列を現在の設定から再計算して表示する"""
        auto = self.auto_convert_check.isChecked()
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 1)
            event_name = name_item.text() if name_item else ""
            if event_name == "（完了）":
                event_name = ""

            combo = self.table.cellWidget(row, 3)
            if not combo:
                continue
            current_type = combo.currentData()
            isr_used = self.table.item(row, 4).text() == "あり"
            converted = current_type
            if auto and isr_used and current_type == EventDeliveryType.DIRECT:
                converted = EventDeliveryType.DOUBLE
            converted_item = self.table.item(row, 5)
            if converted_item:
                converted_item.setText(converted.value if converted else "")

    def _on_accept(self):
        """OKボタン：各イベントの配送タイプを更新して閉じる"""
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 1)
            event_name = name_item.text() if name_item else ""
            if event_name == "（完了）":
                event_name = ""
            combo = self.table.cellWidget(row, 3)
            if combo and event_name in self.sm.events:
                self.sm.events[event_name].delivery_type = combo.currentData()
        self.accept()

    def get_auto_convert(self) -> bool:
        """チェックボックスの状態を返す"""
        return self.auto_convert_check.isChecked()