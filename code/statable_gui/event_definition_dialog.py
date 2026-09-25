"""State transition event definition dialog"""

from typing import Optional, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QMouseEvent
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QComboBox, QLineEdit,
    QFormLayout, QDialogButtonBox, QMessageBox, QAbstractItemView,
    QWidget, QRadioButton, QButtonGroup, QCheckBox, QSpinBox,
    QGroupBox
)

from statable.state_machine import StateMachine
from statable.model import (Event, EventDeliveryType, EventSourceLayer,
                            EventKind, EventTrigger)
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

    def __init__(self, parent=None, event: Optional[Event] = None,
                 global_defs=None, state_machine=None):
        super().__init__(parent)
        self.global_defs = global_defs if global_defs else GlobalDefinitions()
        self.state_machine = state_machine
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
        # [C-51 Step 3] Structured trigger detail section
        self._build_trigger_detail_section(layout, event)
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
        # [C-51 Step 3] keep the structured trigger section in sync
        trig_group = getattr(self, 'trig_group', None)
        if trig_group is not None:
            trig_group.setEnabled(enabled)

    # ------------------------------------------------------------------
    # [C-51 Step 3] Structured trigger detail
    # ------------------------------------------------------------------
    def _build_trigger_detail_section(self, parent_layout, event):
        """Add collapsible Trigger detail QGroupBox."""
        group = QGroupBox("Trigger detail (structured)")
        group.setCheckable(True)
        group_layout = QFormLayout(group)

        td = getattr(event, 'trigger_detail', None) if event else None
        group.setChecked(td is not None)

        # Type
        self.trig_type_combo = QComboBox()
        for t in ("manual", "edge", "polling", "timer",
                  "call", "comparison"):
            self.trig_type_combo.addItem(t, t)
        if td is not None:
            idx = self.trig_type_combo.findData(td.type)
            if idx >= 0:
                self.trig_type_combo.setCurrentIndex(idx)
        group_layout.addRow("Type", self.trig_type_combo)

        # Source (editable: allows custom entry)
        self.trig_source_combo = QComboBox()
        self.trig_source_combo.setEditable(True)
        self.trig_source_combo.setInsertPolicy(QComboBox.NoInsert)
        if td is not None and td.source:
            self.trig_source_combo.setCurrentText(td.source)
        group_layout.addRow("Source", self.trig_source_combo)

        # Edge (edge type)
        self.trig_edge_combo = QComboBox()
        for e in ("rising", "falling", "both"):
            self.trig_edge_combo.addItem(e, e)
        if td is not None and td.edge:
            idx = self.trig_edge_combo.findData(td.edge)
            if idx >= 0:
                self.trig_edge_combo.setCurrentIndex(idx)
        self.trig_edge_row = self._register_row(
            group_layout, "Edge", self.trig_edge_combo)

        # Debounce (edge type)
        self.trig_debounce_spin = QSpinBox()
        self.trig_debounce_spin.setRange(0, 100000)
        self.trig_debounce_spin.setSuffix(" ms")
        if td is not None:
            self.trig_debounce_spin.setValue(td.debounce_ms)
        self.trig_debounce_row = self._register_row(
            group_layout, "Debounce", self.trig_debounce_spin)

        # Period (polling / timer)
        self.trig_period_spin = QSpinBox()
        self.trig_period_spin.setRange(0, 10000000)
        self.trig_period_spin.setSuffix(" ms")
        if td is not None:
            self.trig_period_spin.setValue(td.period_ms)
        self.trig_period_row = self._register_row(
            group_layout, "Period", self.trig_period_spin)

        # Auto reload (timer)
        self.trig_autoreload_check = QCheckBox("Auto reload")
        self.trig_autoreload_check.setChecked(
            td.auto_reload if td is not None else True)
        self.trig_autoreload_row = self._register_row(
            group_layout, "Timer", self.trig_autoreload_check)

        # Caller (call)
        self.trig_caller_combo = QComboBox()
        self.trig_caller_combo.setEditable(True)
        self.trig_caller_combo.setInsertPolicy(QComboBox.NoInsert)
        if td is not None and td.caller:
            self.trig_caller_combo.setCurrentText(td.caller)
        self.trig_caller_row = self._register_row(
            group_layout, "Caller", self.trig_caller_combo)

        # Condition + Build (comparison)
        self.trig_condition_edit = QLineEdit()
        self.trig_condition_build_btn = QPushButton("Build...")
        self.trig_condition_build_btn.clicked.connect(
            self._open_trigger_condition_builder)
        cond_widget = QWidget()
        cond_layout = QHBoxLayout(cond_widget)
        cond_layout.setContentsMargins(0, 0, 0, 0)
        cond_layout.addWidget(self.trig_condition_edit, 1)
        cond_layout.addWidget(self.trig_condition_build_btn)
        if td is not None:
            self.trig_condition_edit.setText(td.condition)
        self.trig_condition_row = self._register_row(
            group_layout, "Condition", cond_widget)

        # Poll period (comparison)
        self.trig_pollperiod_spin = QSpinBox()
        self.trig_pollperiod_spin.setRange(0, 10000000)
        self.trig_pollperiod_spin.setSuffix(" ms")
        if td is not None:
            self.trig_pollperiod_spin.setValue(td.poll_period_ms)
        self.trig_pollperiod_row = self._register_row(
            group_layout, "Poll period", self.trig_pollperiod_spin)

        # Description (optional)
        self.trig_desc_edit = QLineEdit()
        if td is not None:
            self.trig_desc_edit.setText(td.description)
        group_layout.addRow("Description", self.trig_desc_edit)

        # Wire up
        self.trig_type_combo.currentIndexChanged.connect(
            self._on_trigger_type_changed)
        group.toggled.connect(lambda _c: self._on_trigger_type_changed())

        parent_layout.addWidget(group)
        self.trig_group = group

        # Initial state
        self._on_trigger_type_changed()

    def _register_row(self, layout, label_text, widget):
        """Add a QFormLayout row; return (label, widget) for visibility."""
        layout.addRow(label_text, widget)
        label = layout.labelForField(widget)
        return (label, widget)

    def _set_row_visible(self, row, visible):
        lbl, w = row
        if lbl is not None:
            lbl.setVisible(visible)
        w.setVisible(visible)

    def _on_trigger_type_changed(self):
        """Show/hide dynamic fields based on Type; refresh Source choices."""
        t = self.trig_type_combo.currentData()

        self._set_row_visible(self.trig_edge_row, t == "edge")
        self._set_row_visible(self.trig_debounce_row, t == "edge")
        self._set_row_visible(self.trig_period_row,
                              t in ("polling", "timer"))
        self._set_row_visible(self.trig_autoreload_row, t == "timer")
        self._set_row_visible(self.trig_caller_row, t == "call")
        self._set_row_visible(self.trig_condition_row, t == "comparison")
        self._set_row_visible(self.trig_pollperiod_row, t == "comparison")

        self._populate_source_choices(t)

    def _populate_source_choices(self, trigger_type):
        """Populate Source dropdown from GlobalDefinitions / role_functions."""
        current = self.trig_source_combo.currentText().strip()
        self.trig_source_combo.blockSignals(True)
        self.trig_source_combo.clear()
        self.trig_source_combo.addItem("")

        candidates = []
        if trigger_type == "edge":
            for intr in getattr(self.global_defs, 'interrupts', []) or []:
                if getattr(intr, 'name', ''):
                    candidates.append(intr.name)
        elif trigger_type in ("polling", "timer"):
            tb = getattr(self.global_defs, 'timer_base', None)
            if tb is not None and getattr(tb, 'variable_name', ''):
                candidates.append(tb.variable_name)
            for t in getattr(self.global_defs, 'extra_timers', []) or []:
                if getattr(t, 'variable_name', ''):
                    candidates.append(t.variable_name)
        elif trigger_type == "call":
            if self.state_machine is not None:
                for rf in self.state_machine.role_functions.values():
                    ns = getattr(rf, 'namespace', '')
                    n = getattr(rf, 'name', '')
                    qn = f"{ns}.{n}" if ns else n
                    if qn:
                        candidates.append(qn)
        # comparison: no candidates (use Build button)

        for c in candidates:
            self.trig_source_combo.addItem(c)

        if current:
            self.trig_source_combo.setCurrentText(current)
        self.trig_source_combo.blockSignals(False)

    def _open_trigger_condition_builder(self):
        """Open ConditionBuilderDialog for comparison-type condition."""
        try:
            from .condition_builder_dialog import ConditionBuilderDialog
        except ImportError:
            return
        dlg = ConditionBuilderDialog(
            condition=self.trig_condition_edit.text(),
            event_name=self.name_edit.text().strip(),
            global_defs=self.global_defs,
            state_machine=self.state_machine,
            parent=self,
        )
        if dlg.exec() == QDialog.Accepted:
            self.trig_condition_edit.setText(dlg.get_condition_text())

    def _get_trigger_detail(self):
        """Build EventTrigger from UI, or None if section unchecked."""
        if not self.trig_group.isChecked():
            return None
        t = self.trig_type_combo.currentData()
        kwargs = {
            "type": t,
            "source": self.trig_source_combo.currentText().strip(),
            "description": self.trig_desc_edit.text().strip(),
        }
        if t == "edge":
            kwargs["edge"] = self.trig_edge_combo.currentData()
            kwargs["debounce_ms"] = self.trig_debounce_spin.value()
        elif t == "polling":
            kwargs["period_ms"] = self.trig_period_spin.value()
        elif t == "timer":
            kwargs["period_ms"] = self.trig_period_spin.value()
            kwargs["auto_reload"] = self.trig_autoreload_check.isChecked()
        elif t == "call":
            kwargs["caller"] = self.trig_caller_combo.currentText().strip()
        elif t == "comparison":
            kwargs["condition"] = self.trig_condition_edit.text().strip()
            kwargs["poll_period_ms"] = self.trig_pollperiod_spin.value()
        return EventTrigger(**kwargs)

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
            # [C-51 Step 3] Structured trigger detail
            trigger_detail=self._get_trigger_detail(),
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
        dlg = EventEditDialog(self, event=event,
                              global_defs=self.global_defs,
                              state_machine=self.sm)
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