"""State transition event definition dialog"""

from typing import Optional, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QMouseEvent
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QComboBox, QLineEdit,
    QFormLayout, QDialogButtonBox, QMessageBox, QAbstractItemView,
    QWidget, QRadioButton, QButtonGroup, QCheckBox, QSpinBox
)

from statable.state_machine import StateMachine
from statable.model import Event, EventDeliveryType, EventSourceLayer, EventKind
from statable.global_defs import GlobalDefinitions
from .common_widgets import TitleEditWidget, TypeComboBox
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
            row = item.row()
            self.cellDoubleClicked.emit(row, item.column())


class EventEditDialog(QDialog):
    """Edit state transition event dialog"""

    def __init__(self, parent=None, event: Optional[Event] = None, global_defs=None):
        super().__init__(parent)
        self.global_defs = global_defs if global_defs else GlobalDefinitions()
        self.setWindowTitle("Edit state transition event")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        # Title input field (required / provisional title auto-set)
        self.title_widget = TitleEditWidget(self, title=event.title if event else "")
        form.addRow("", self.title_widget)

        # Event name
        self.name_edit = QLineEdit(event.name if event else "")
        form.addRow("Event name", self.name_edit)

        # Event ID
        self.id_spin = QSpinBox()
        self.id_spin.setRange(0, 65535)
        if event and event.id is not None:
            self.id_spin.setValue(event.id)
        form.addRow("Event ID", self.id_spin)

        # description
        self.desc_edit = QLineEdit(event.description if event else "")
        form.addRow("Description", self.desc_edit)

        # Event kind
        self.kind_combo = QComboBox()
        for kind in EventKind:
            self.kind_combo.addItem(kind.value, kind)
        if event:
            idx = self.kind_combo.findData(event.kind)
            if idx >= 0:
                self.kind_combo.setCurrentIndex(idx)
        form.addRow("Event kind", self.kind_combo)

        # Source layer
        self.layer_driver = QRadioButton("Driver layer")
        self.layer_middleware = QRadioButton("Middle layer")
        group = QButtonGroup(self)
        group.addButton(self.layer_driver)
        group.addButton(self.layer_middleware)
        if event and event.source_layer == EventSourceLayer.MIDDLEWARE:
            self.layer_middleware.setChecked(True)
        else:
            self.layer_driver.setChecked(True)
        layer_layout = QHBoxLayout()
        layer_layout.addWidget(self.layer_driver)
        layer_layout.addWidget(self.layer_middleware)
        layer_layout.addStretch()
        form.addRow("Source layer", layer_layout)

        # Delivery type
        self.delivery_combo = QComboBox()
        self.delivery_combo.addItem("DIRECT", EventDeliveryType.DIRECT)
        self.delivery_combo.addItem("QUEUE", EventDeliveryType.QUEUE)
        self.delivery_combo.addItem("DOUBLE", EventDeliveryType.DOUBLE)
        if event:
            idx = self.delivery_combo.findData(event.delivery_type)
            if idx >= 0:
                self.delivery_combo.setCurrentIndex(idx)
        form.addRow("Delivery type", self.delivery_combo)

        # Attached data
        self.data_check = QCheckBox("Use attached data")
        self.data_check.setChecked(bool(event.data_type if event else False))
        form.addRow("", self.data_check)

        self.data_type_combo = TypeComboBox(self, global_defs=self.global_defs)
        if event:
            self.data_type_combo.set_current_text(event.data_type)
        form.addRow("Data type", self.data_type_combo)

        self.data_name_edit = QLineEdit(event.data_name if event else "")
        form.addRow("Data variable name", self.data_name_edit)

        self.data_check.toggled.connect(self._on_data_check_toggled)
        self._on_data_check_toggled(self.data_check.isChecked())

        # [C-51 Step 2] Trigger free-text field.
        # Enabled only for kind in {signal, call, time};
        # kind=change is handled inside transition conditions.
        self.trigger_edit = QLineEdit(
            getattr(event, 'trigger', '') if event else "")
        self.trigger_edit.setPlaceholderText(
            "e.g. GPIO edge (ISR), debounce 5ms / "
            "periodic timer 10ms / direct call from Application")
        self.trigger_edit.setToolTip(
            "Free-text description of when / from where this event fires.\n"
            "Examples:\n"
            "  signal: GPIO edge (ISR), debounce 5ms\n"
            "  signal: from Application layer via OSAL queue\n"
            "  call:   direct call from Middleware\n"
            "  time:   periodic timer (10ms)\n"
            "Not used for kind=change (use transition condition).")
        form.addRow("Trigger", self.trigger_edit)
        self.kind_combo.currentIndexChanged.connect(
            self._on_kind_changed)
        self._on_kind_changed()

        # OK/Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        StaTableLogger.debug("EventEditDialog initialized")

    def _on_data_check_toggled(self, checked: bool):
        self.data_type_combo.setEnabled(checked)
        self.data_name_edit.setEnabled(checked)

    def _on_kind_changed(self):
        # [C-51 Step 2] trigger is meaningful only for
        # signal / call / time.  kind=change uses the
        # transition condition instead.
        kind = self.kind_combo.currentData()
        enabled = kind in (
            EventKind.SIGNAL, EventKind.CALL, EventKind.TIME)
        self.trigger_edit.setEnabled(enabled)
        if not enabled:
            self.trigger_edit.setToolTip(
                "kind=change fires via the transition condition; "
                "trigger is not used.")

    def _on_accept(self):
        """OK button: auto-set provisional title if title is empty"""
        auto_title = f"Event: {self.name_edit.text().strip() or '(unnamed)'}"
        self.title_widget.ensure_title(auto_title)
        self.accept()

    def get_event(self) -> Event:
        source_layer = EventSourceLayer.MIDDLEWARE if self.layer_middleware.isChecked() else EventSourceLayer.DRIVER
        data_type = self.data_type_combo.current_text() if self.data_check.isChecked() else ""
        data_name = self.data_name_edit.text().strip() if self.data_check.isChecked() else ""
        return Event(
            name=self.name_edit.text().strip(),
            id=self.id_spin.value(),
            kind=self.kind_combo.currentData(),
            description=self.desc_edit.text().strip(),
            delivery_type=self.delivery_combo.currentData(),
            source_layer=source_layer,
            data_type=data_type,
            data_name=data_name,
            title=self.title_widget.get_title(),
            # [C-51 Step 2] Only meaningful for signal/call/time.
            # For other kinds, store "" regardless of UI state.
            trigger=(self.trigger_edit.text().strip()
                     if self.kind_combo.currentData() in (
                         EventKind.SIGNAL, EventKind.CALL,
                         EventKind.TIME)
                     else ""),
        )


class EventDefinitionDialog(QDialog):
    """State transition event definition list dialog"""

    def __init__(self, sm: StateMachine, global_defs: Optional[GlobalDefinitions] = None, parent=None):
        super().__init__(parent)
        self.sm = sm
        self.global_defs = global_defs if global_defs else GlobalDefinitions()
        self.setWindowTitle("StateTransitionEvent definitions")
        self.setMinimumSize(1100, 650)

        layout = QVBoxLayout(self)

        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search (prefix match):"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Title, event name, description")
        self.search_edit.textChanged.connect(self.refresh_table)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # Event list table (title column added / direct edit)
        self.table = DoubleClickTable(0, 7)
        self.table.setHorizontalHeaderLabels(["Title", "Event name", "ID", "Source", "Delivery type", "Attached data", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setFont(QFont("Consolas", 10))
        self.table.cellDoubleClicked.connect(self.on_double_clicked)
        self.table.itemChanged.connect(self.on_item_changed)
        layout.addWidget(self.table, stretch=1)

        # Buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_event)
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self.delete_event)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Close
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

        self.refresh_table()
        StaTableLogger.debug("EventDefinitionDialog initialized")

    def refresh_table(self):
        query = self.search_edit.text().strip().lower() if hasattr(self, 'search_edit') else ""
        self.table.setRowCount(0)
        for event in self.sm.events.values():
            name = event.name if event.name else "(completion)"
            desc = event.description
            title = event.title
            if query and not (title.lower().startswith(query) or name.lower().startswith(query) or desc.lower().startswith(query)):
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Title (directly editable)
            title_item = QTableWidgetItem(title)
            title_item.setToolTip("Title of this event. Can be edited directly.")
            self.table.setItem(row, 0, title_item)

            self.table.setItem(row, 1, QTableWidgetItem(name))
            self.table.setItem(row, 2, QTableWidgetItem(str(event.id) if event.id is not None else ""))
            self.table.setItem(row, 3, QTableWidgetItem(event.source_layer.value))
            self.table.setItem(row, 4, QTableWidgetItem(event.delivery_type.value))
            data_text = f"{event.data_type} {event.data_name}" if event.data_type else ""
            self.table.setItem(row, 5, QTableWidgetItem(data_text))
            self.table.setItem(row, 6, QTableWidgetItem(event.description))

    def on_item_changed(self, item):
        """Handler when the title column is edited directly"""
        if item.column() == 0:
            row = item.row()
            name_item = self.table.item(row, 1)
            if name_item:
                name = name_item.text()
                if name == "(completion)":
                    name = ""
                if name in self.sm.events:
                    new_title = item.text().strip() or f"Event: {name or '(Completion)'}"
                    self.sm.events[name].title = new_title

    def _find_event_by_row(self, row: int) -> Optional[Event]:
        name_item = self.table.item(row, 1)
        if not name_item:
            return None
        name = name_item.text()
        if name == "(completion)":
            name = ""
        return self.sm.events.get(name)

    def on_double_clicked(self, row, col):
        if col == 0:
            return
        event = self._find_event_by_row(row)
        if not event:
            return
        dlg = EventEditDialog(self, event=event, global_defs=self.global_defs)
        if dlg.exec() == QDialog.Accepted:
            new_event = dlg.get_event()
            if not new_event.name:
                QMessageBox.warning(self, "Warning", "Please enter an event name.")
                return
            # Handler when the name changes
            old_name = event.name
            if old_name != new_event.name:
                if new_event.name in self.sm.events:
                    QMessageBox.warning(self, "Warning", f"Event '{new_event.name}' already exists.")
                    return
                #Rebuild dict preserving original positions
                new_events = {}
                for key, value in self.sm.events.items():
                    if key == old_name:
                        new_events[new_event.name] = new_event
                    else:
                        new_events[key] = value
                self.sm.events = new_events
                for trans in self.sm.transitions:
                    if trans.event == old_name:
                        trans.event = new_event.name
            else:
                self.sm.events[old_name] = new_event

            self.refresh_table()
            StaTableLogger.info(f"Event updated: {new_event.name}")

    def add_event(self):
        dlg = EventEditDialog(self, global_defs=self.global_defs)
        if dlg.exec() == QDialog.Accepted:
            event = dlg.get_event()
            if not event.name:
                QMessageBox.warning(self, "Warning", "Please enter an event name.")
                return
            if event.name in self.sm.events:
                QMessageBox.warning(self, "Warning", f"Event '{event.name}' already exists.")
                return
            self.sm.add_event(event)
            self.refresh_table()
            StaTableLogger.info(f"Event added: {event.name}")

    def delete_event(self):
        row = self.table.currentRow()
        if row < 0:
            return
        event = self._find_event_by_row(row)
        if not event:
            return

        # Dependency check
        transitions = self.sm.get_transitions_for_event(event.name)
        if transitions:
            msg = f"Event '{event.title}'  cannot be deleted.\n\nUsed by the following transitions:\n\n"
            for trans in transitions:
                msg += f"  - {trans.source} → {trans.target}\n"
            msg += "\nPlease delete these transitions first."
            QMessageBox.warning(self, "Warning", msg)
            return

        # Interrupt handler check
        for intr in self.global_defs.interrupts:
            if event.name in intr.event_names:
                QMessageBox.warning(self, "Warning", f"Event '{event.title}' is used by interrupt handler '{intr.title}'.")
                return
        reply = QMessageBox.question(self, "Confirm", f"Event '{event.title}': confirm delete?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.sm.remove_event(event.name)
            self.refresh_table()
            StaTableLogger.info(f"Event deleted: {event.name}")