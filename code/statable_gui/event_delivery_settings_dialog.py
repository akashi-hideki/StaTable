"""Event delivery settingsダイアログ"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QComboBox, QDialogButtonBox,
    QCheckBox, QAbstractItemView
)
from PySide6.QtGui import QFont, QMouseEvent

from statable.state_machine import StateMachine
from statable.model import EventDeliveryType
from statable.global_defs import GlobalDefinitions
from .logger import StaTableLogger


class DoubleClickTable(QTableWidget):
    """Table that reliably captures double-click events"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        pos = event.position().toPoint()
        item = self.itemAt(pos)
        if item:
            self.cellDoubleClicked.emit(item.row(), item.column())


class EventDeliverySettingsDialog(QDialog):
    """Dialog to configure event delivery type (DIRECT/QUEUE) and display automatic DOUBLE conversion based on ISR usage"""
    def __init__(self, sm: StateMachine, global_defs: GlobalDefinitions, auto_convert: bool = True, parent=None):
        super().__init__(parent)
        self.sm = sm
        self.global_defs = global_defs
        self.auto_convert = auto_convert

        self.setWindowTitle("Event delivery settings")
        self.setMinimumSize(900, 500)

        layout = QVBoxLayout(self)

        #Global settings checkbox
        self.auto_convert_check = QCheckBox("Automatically convert DIRECT events used in ISR to DOUBLE")
        self.auto_convert_check.setChecked(self.auto_convert)
        layout.addWidget(self.auto_convert_check)

        # Event list table
        self.table = DoubleClickTable(0, 6)
        self.table.setHorizontalHeaderLabels(["Title", "Event name", "Source", "Delivery type", "ISR usage", "Converted"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setFont(QFont("Consolas", 10))
        layout.addWidget(self.table, stretch=1)

        # Help
        help_label = QLabel(
            "If a DIRECT event is notified from an ISR, it is automatically converted to DOUBLE.\n"
            "Select QUEUE if you need event counts or data."
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
        """Build the table"""
        self.table.setRowCount(0)
        for event in self.sm.events.values():
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Title（読み取り専用）
            title_item = QTableWidgetItem(event.title)
            title_item.setFlags(title_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, title_item)

            # Event name（読み取り専用）
            name_item = QTableWidgetItem(event.name if event.name else "(completion)")
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, name_item)

            # Source（読み取り専用）
            source_item = QTableWidgetItem(event.source_layer.value)
            source_item.setFlags(source_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, source_item)

            # Delivery typeコンボ
            combo = QComboBox()
            combo.addItem("DIRECT", EventDeliveryType.DIRECT)
            combo.addItem("QUEUE", EventDeliveryType.QUEUE)
            combo.addItem("DOUBLE", EventDeliveryType.DOUBLE)
            idx = combo.findData(event.delivery_type)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            combo.currentIndexChanged.connect(lambda _index, r=row: self._on_delivery_changed(r))
            self.table.setCellWidget(row, 3, combo)

            #ISR usage column (read-only)
            isr_used = self._check_isr_usage(event.name)
            isr_item = QTableWidgetItem("Yes" if isr_used else "")
            isr_item.setFlags(isr_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 4, isr_item)

            # Conversion column (read-only)
            converted_item = QTableWidgetItem()
            converted_item.setFlags(converted_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 5, converted_item)

            StaTableLogger.debug(f"  Event: '{event.name}' -> ISR used: {isr_used}")

        self._update_converted_column()

    def _check_isr_usage(self, event_name: str) -> bool:
        """Determine if event used from interrupt handler"""
        if not event_name:
            return False

        for intr in self.global_defs.interrupts:
            #Check event_names list
            if event_name in intr.event_names:
                StaTableLogger.debug(f"  '{event_name}' found in interrupt '{intr.name}' event_names")
                return True

            #Check the code in actions
            for act in intr.actions:
                combined = act.condition + "\n" + act.action
                if event_name in combined:
                    StaTableLogger.debug(f"  '{event_name}' found in interrupt '{intr.name}' action code")
                    return True

        return False

    def _find_row_by_event_name(self, event_name: str) -> int:
        """Event nameからRow番号を探す"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)
            if item and item.text() == event_name:
                return row
        return -1

    def _on_delivery_changed(self, row: int):
        """Delivery typeコンボ変更時にConverted列を更新"""
        self._update_converted_column()

    def _update_converted_column(self):
        """Recompute conversion column from settings"""
        auto = self.auto_convert_check.isChecked()
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 1)
            event_name = name_item.text() if name_item else ""
            if event_name == "(completion)":
                event_name = ""

            combo = self.table.cellWidget(row, 3)
            if not combo:
                continue
            current_type = combo.currentData()
            isr_used = self.table.item(row, 4).text() == "Yes"
            converted = current_type
            if auto and isr_used and current_type == EventDeliveryType.DIRECT:
                converted = EventDeliveryType.DOUBLE
            converted_item = self.table.item(row, 5)
            if converted_item:
                converted_item.setText(converted.value if converted else "")

    def _on_accept(self):
        """OK button: update each event's delivery type and close"""
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 1)
            event_name = name_item.text() if name_item else ""
            if event_name == "(completion)":
                event_name = ""
            combo = self.table.cellWidget(row, 3)
            if combo and event_name in self.sm.events:
                self.sm.events[event_name].delivery_type = combo.currentData()
        self.accept()

    def get_auto_convert(self) -> bool:
        """Return the checkbox state"""
        return self.auto_convert_check.isChecked()