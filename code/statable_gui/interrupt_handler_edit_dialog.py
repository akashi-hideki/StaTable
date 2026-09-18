"""Management dialog for interrupt handlers, device resources, timer settings (multi-timer support / ISR support)"""

from typing import Optional, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QMouseEvent
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QHeaderView,
    QComboBox, QLineEdit, QDialogButtonBox, QMessageBox,
    QAbstractItemView, QSpinBox, QCheckBox, QFormLayout,
    QInputDialog
)

from statable.global_defs import (
    GlobalDefinitions,
    InterruptHandlerDef,
    InterruptAction,
    DevicePlaceholderDef,
    TimerBaseDef,
    TimerDerivedDef,
)

from .condition_edit_dialog import ConditionEditDialog
from .action_edit_dialog import ActionEditDialog
from .logger import StaTableLogger


class DoubleClickTable(QTableWidget):
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


class InterruptEditDialog(QDialog):
    def __init__(
        self,
        parent=None,
        event_names=None,
        interrupt: Optional[InterruptHandlerDef] = None,
        global_defs: Optional[GlobalDefinitions] = None,
        role_functions: Optional[dict] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Edit interrupt handler")
        self.setMinimumSize(1100, 800)
        self.event_names = event_names or []
        self.global_defs = global_defs if global_defs else GlobalDefinitions()
        self.role_functions = role_functions if role_functions is not None else {}

        layout = QVBoxLayout(self)

        title = QLabel("Edit interrupt handler")
        title.setFont(QFont("sans-serif", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form = QFormLayout()
        layout.addLayout(form)

        self.title_edit = QLineEdit()
        if interrupt:
            self.title_edit.setText(interrupt.title)
        self.title_edit.setPlaceholderText("Label shown in the list (auto-set if empty)")
        self.title_edit.setToolTip("Enter the title of this interrupt handler. If empty, a provisional title is set automatically.")
        form.addRow("Title *", self.title_edit)

        self.name_edit = QLineEdit()
        if interrupt:
            self.name_edit.setText(interrupt.name)
        self.name_edit.setToolTip("Please enter an interrupt name (e.g., TIMER0_IRQHandler)")
        form.addRow("Interrupt name", self.name_edit)

        self.desc_edit = QLineEdit()
        if interrupt:
            self.desc_edit.setText(interrupt.description)
        self.desc_edit.setToolTip("Enter the description of this interrupt handler")
        form.addRow("Description", self.desc_edit)

        self.event_combo = QComboBox()
        self.event_combo.setEditable(True)
        self.event_combo.setInsertPolicy(QComboBox.NoInsert)
        self.event_combo.addItem("")
        self.event_combo.addItems(self.event_names)
        if interrupt and interrupt.event_names:
            self.event_combo.setCurrentText(interrupt.event_names[0])
        self.event_combo.setToolTip(
            "Select or enter the state transition event name to notify from the ISR.\n"
            "Entering a new event name registers it as-is."
        )
        form.addRow("Event name", self.event_combo)

        self.timer_check = QCheckBox()
        self.timer_check.setChecked(interrupt.is_timer if interrupt else False)
        self.timer_check.setToolTip("Check this if it is a timer interrupt")
        form.addRow("Timer interrupt", self.timer_check)

        layout.addWidget(QLabel("Conditional action list:"))
        help_label = QLabel(
            "Describe \"state transition condition\" and \"action code\" in each row.\n"
            "If the state transition condition is empty, the action is executed unconditionally.\n"
            "Double-click to edit each cell."
        )
        help_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(help_label)

        self.action_table = DoubleClickTable(0, 2)
        self.action_table.setHorizontalHeaderLabels(["State transition condition", "Action code"])
        self.action_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.action_table.cellDoubleClicked.connect(self.on_action_double_clicked)
        layout.addWidget(self.action_table, stretch=1)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add row")
        add_btn.clicked.connect(lambda: self.add_action_row())
        del_btn = QPushButton("Delete row")
        del_btn.clicked.connect(lambda: self.delete_action_row())
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if interrupt and interrupt.actions:
            for act in interrupt.actions:
                self.add_action_row(act.condition, act.action)
        else:
            self.add_action_row()

        StaTableLogger.debug("InterruptEditDialog initialized")

    def add_action_row(self, condition: str = "", action: str = ""):
        row = self.action_table.rowCount()
        self.action_table.insertRow(row)

        condition_item = QTableWidgetItem(condition.replace('\n', ' ; ') if condition else "")
        condition_item.setToolTip("Double-click to edit the state transition condition")
        condition_item.setData(Qt.UserRole, condition)
        self.action_table.setItem(row, 0, condition_item)

        action_item = QTableWidgetItem(action.replace('\n', ' ; ') if action else "")
        action_item.setToolTip("Double-click to edit the action code")
        action_item.setData(Qt.UserRole, action)
        self.action_table.setItem(row, 1, action_item)

    def delete_action_row(self):
        row = self.action_table.currentRow()
        if row >= 0:
            self.action_table.removeRow(row)

    def on_action_double_clicked(self, row, col):
        StaTableLogger.debug(f"on_action_double_clicked: row={row}, col={col}")

        if col == 0:
            item = self.action_table.item(row, 0)
            if not item:
                return
            current_condition = item.data(Qt.UserRole) if item.data(Qt.UserRole) else ""
            dlg = ConditionEditDialog(
                self,
                condition_text=current_condition,
                global_defs=self.global_defs,
                role_functions=self.role_functions
            )
            if dlg.exec() == QDialog.Accepted:
                new_condition = dlg.get_condition_text()
                item.setText(new_condition.replace('\n', ' ; '))
                item.setData(Qt.UserRole, new_condition)

        elif col == 1:
            item = self.action_table.item(row, 1)
            if not item:
                return
            current_action = item.data(Qt.UserRole) if item.data(Qt.UserRole) else ""
            dlg = ActionEditDialog(
                self,
                action_text=current_action,
                role_functions=self.role_functions,
                global_defs=self.global_defs
            )
            if dlg.exec() == QDialog.Accepted:
                new_action = dlg.get_action_text()
                item.setText(new_action.replace('\n', ' ; '))
                item.setData(Qt.UserRole, new_action)

    def _on_accept(self):
        if not self.title_edit.text().strip():
            auto_title = f"Interrupt: {self.name_edit.text().strip() or '(unnamed)'}"
            self.title_edit.setText(auto_title)
            StaTableLogger.debug(f"Auto title generated: '{auto_title}'")
        self.accept()

    # Stage 3: auto-extract used_role_functions / used_variables
    def get_interrupt(self) -> InterruptHandlerDef:
        actions = []
        for row in range(self.action_table.rowCount()):
            condition_item = self.action_table.item(row, 0)
            action_item = self.action_table.item(row, 1)
            if not condition_item or not action_item:
                continue
            condition = condition_item.data(Qt.UserRole) if condition_item.data(Qt.UserRole) else ""
            action = action_item.data(Qt.UserRole) if action_item.data(Qt.UserRole) else ""
            if not condition and not action:
                continue
            actions.append(InterruptAction(condition=condition, action=action))

        event_names = []
        if self.event_combo.currentText().strip():
            event_names.append(self.event_combo.currentText().strip())

        handler = InterruptHandlerDef(
            name=self.name_edit.text().strip(),
            description=self.desc_edit.text().strip(),
            event_names=event_names,
            is_timer=self.timer_check.isChecked(),
            actions=actions,
            title=self.title_edit.text().strip(),
        )

        # Auto-extract used role functions and variables
        try:
            from codegen.interrupt_generator import InterruptGenerator
            gen = InterruptGenerator()
            gen.update_handler_symbols(handler)
            StaTableLogger.debug(
                f"InterruptEditDialog.get_interrupt: "
                f"used_rfs={handler.used_role_functions}, "
                f"used_vars={handler.used_variables}"
            )
        except Exception as e:
            StaTableLogger.debug(
                f"InterruptEditDialog.get_interrupt: "
                f"symbol extraction skipped: {e}"
            )

        return handler


class DevicePlaceholderEditDialog(QDialog):
    def __init__(self, parent=None, placeholder: Optional[DevicePlaceholderDef] = None):
        super().__init__(parent)
        self.setWindowTitle("Device resource placeholder definitionEdit")
        self.setMinimumWidth(450)

        form = QFormLayout(self)

        self.title_edit = QLineEdit()
        if placeholder:
            self.title_edit.setText(placeholder.title)
        self.title_edit.setPlaceholderText("Label shown in the list (auto-set if empty)")
        form.addRow("Title *", self.title_edit)

        self.name_edit = QLineEdit()
        if placeholder:
            self.name_edit.setText(placeholder.name)
        form.addRow("Placeholder name", self.name_edit)

        self.desc_edit = QLineEdit()
        if placeholder:
            self.desc_edit.setText(placeholder.description)
        form.addRow("Description", self.desc_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _on_accept(self):
        if not self.title_edit.text().strip():
            auto_title = f"Device: {self.name_edit.text().strip() or '(unnamed)'}"
            self.title_edit.setText(auto_title)
        self.accept()

    def get_placeholder(self) -> DevicePlaceholderDef:
        return DevicePlaceholderDef(
            name=self.name_edit.text().strip(),
            description=self.desc_edit.text().strip(),
            title=self.title_edit.text().strip(),
        )


class TimerBaseEditDialog(QDialog):
    def __init__(self, parent=None, timer_base: TimerBaseDef = None):
        super().__init__(parent)
        self.setWindowTitle("Timer base variableEdit")
        self.setMinimumWidth(450)

        form = QFormLayout(self)

        self.title_edit = QLineEdit()
        if timer_base:
            self.title_edit.setText(timer_base.title)
        self.title_edit.setPlaceholderText("Label shown in the list (auto-set if empty)")
        form.addRow("Title *", self.title_edit)

        self.var_edit = QLineEdit()
        if timer_base:
            self.var_edit.setText(timer_base.variable_name)
        form.addRow("Base variable name", self.var_edit)

        self.unit_edit = QLineEdit()
        if timer_base:
            self.unit_edit.setText(timer_base.unit)
        form.addRow("Unit", self.unit_edit)

        self.type_edit = QLineEdit()
        if timer_base:
            self.type_edit.setText(timer_base.data_type)
        form.addRow("Type", self.type_edit)

        self.interrupt_edit = QLineEdit()
        if timer_base:
            self.interrupt_edit.setText(timer_base.interrupt_name)
        self.interrupt_edit.setPlaceholderText("Interrupt name driving this timer (optional)")
        form.addRow("Interrupt name", self.interrupt_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _on_accept(self):
        if not self.title_edit.text().strip():
            auto_title = f"Timer base: {self.var_edit.text().strip() or '(unnamed)'}"
            self.title_edit.setText(auto_title)
        self.accept()

    def get_timer_base(self) -> TimerBaseDef:
        return TimerBaseDef(
            variable_name=self.var_edit.text().strip(),
            unit=self.unit_edit.text().strip(),
            data_type=self.type_edit.text().strip(),
            title=self.title_edit.text().strip(),
            interrupt_name=self.interrupt_edit.text().strip(),
        )


class TimerDerivedEditDialog(QDialog):
    def __init__(self, parent=None, derived: Optional[TimerDerivedDef] = None):
        super().__init__(parent)
        self.setWindowTitle("Edit derived timer variable")
        self.setMinimumWidth(450)

        form = QFormLayout(self)

        self.title_edit = QLineEdit()
        if derived:
            self.title_edit.setText(derived.title)
        self.title_edit.setPlaceholderText("Label shown in the list (auto-set if empty)")
        form.addRow("Title *", self.title_edit)

        self.period_edit = QLineEdit()
        if derived:
            self.period_edit.setText(derived.period_name)
        form.addRow("Period name", self.period_edit)

        self.mult_spin = QSpinBox()
        self.mult_spin.setRange(1, 1000000)
        if derived:
            self.mult_spin.setValue(derived.multiplier)
        form.addRow("Multiplier", self.mult_spin)

        self.var_edit = QLineEdit()
        if derived:
            self.var_edit.setText(derived.variable_name)
        form.addRow("Variable name", self.var_edit)

        self.type_edit = QLineEdit()
        if derived:
            self.type_edit.setText(derived.data_type)
        form.addRow("Type", self.type_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _on_accept(self):
        if not self.title_edit.text().strip():
            auto_title = f"Timer: {self.var_edit.text().strip() or '(unnamed)'}"
            self.title_edit.setText(auto_title)
        self.accept()

    def get_derived(self) -> TimerDerivedDef:
        return TimerDerivedDef(
            period_name=self.period_edit.text().strip(),
            multiplier=self.mult_spin.value(),
            variable_name=self.var_edit.text().strip(),
            data_type=self.type_edit.text().strip(),
            title=self.title_edit.text().strip(),
        )


class InterruptHandlerEditDialog(QDialog):
    """Dialog to manage interrupt handlers, device resources, and timer settings together"""

    def __init__(
        self,
        global_defs: GlobalDefinitions,
        event_names: Optional[List[str]] = None,
        role_functions: Optional[dict] = None,
        parent=None
    ):
        super().__init__(parent)
        self.global_defs = global_defs
        self.event_names = event_names or []
        self.role_functions = role_functions if role_functions is not None else {}

        self.setWindowTitle("Interrupt handlers, device resources, timer settings")
        self.setMinimumSize(1200, 800)

        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tabs.addTab(self._create_interrupt_tab(), "Interrupt handler")
        self.tabs.addTab(self._create_placeholder_tab(), "Device resource")
        self.tabs.addTab(self._create_timer_tab(), "Timer settings")

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

        self.refresh_interrupt_table()
        self.refresh_placeholder_table()
        self.refresh_timer_tabs()

        StaTableLogger.debug("InterruptHandlerEditDialog initialized")

    # ------------------------------------------------------------------
    # Interrupt handler tab
    # ------------------------------------------------------------------
    def _create_interrupt_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.interrupt_table = DoubleClickTable(0, 6)
        self.interrupt_table.setHorizontalHeaderLabels([
            "Title", "Interrupt name", "Description", "Event name", "Timer", "Number of conditional actions"
        ])
        self.interrupt_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.interrupt_table.cellDoubleClicked.connect(self.on_interrupt_double_clicked)
        layout.addWidget(self.interrupt_table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_interrupt)
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self.delete_interrupt)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    def refresh_interrupt_table(self):
        self.interrupt_table.setRowCount(0)
        for intr in self.global_defs.interrupts:
            row = self.interrupt_table.rowCount()
            self.interrupt_table.insertRow(row)
            self.interrupt_table.setItem(row, 0, QTableWidgetItem(intr.title))
            self.interrupt_table.setItem(row, 1, QTableWidgetItem(intr.name))
            self.interrupt_table.setItem(row, 2, QTableWidgetItem(intr.description))
            self.interrupt_table.setItem(row, 3, QTableWidgetItem(", ".join(intr.event_names)))
            self.interrupt_table.setItem(row, 4, QTableWidgetItem("✔" if intr.is_timer else ""))
            self.interrupt_table.setItem(row, 5, QTableWidgetItem(str(len(intr.actions))))

    def on_interrupt_double_clicked(self, row, col):
        StaTableLogger.debug(f"on_interrupt_double_clicked: row={row}, col={col}")
        if row < 0 or row >= len(self.global_defs.interrupts):
            return
        target = self.global_defs.interrupts[row]
        dlg = InterruptEditDialog(
            self,
            event_names=self.event_names,
            interrupt=target,
            global_defs=self.global_defs,
            role_functions=self.role_functions
        )
        if dlg.exec() == QDialog.Accepted:
            new_intr = dlg.get_interrupt()
            if not new_intr.name:
                QMessageBox.warning(self, "Warning", "Please enter an interrupt name.")
                return
            self.global_defs.interrupts[row] = new_intr
            self.refresh_interrupt_table()

    def add_interrupt(self):
        dlg = InterruptEditDialog(
            self,
            event_names=self.event_names,
            global_defs=self.global_defs,
            role_functions=self.role_functions
        )
        if dlg.exec() == QDialog.Accepted:
            intr = dlg.get_interrupt()
            if not intr.name:
                QMessageBox.warning(self, "Warning", "Please enter an interrupt name.")
                return
            self.global_defs.interrupts.append(intr)
            self.refresh_interrupt_table()

    def delete_interrupt(self):
        row = self.interrupt_table.currentRow()
        if 0 <= row < len(self.global_defs.interrupts):
            self.global_defs.interrupts.pop(row)
            self.refresh_interrupt_table()

    # ------------------------------------------------------------------
    # Device resource tab
    # ------------------------------------------------------------------
    def _create_placeholder_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.placeholder_table = DoubleClickTable(0, 3)
        self.placeholder_table.setHorizontalHeaderLabels(["Title", "Placeholder name", "Description"])
        self.placeholder_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.placeholder_table.cellDoubleClicked.connect(self.on_placeholder_double_clicked)
        layout.addWidget(self.placeholder_table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_placeholder)
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self.delete_placeholder)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    def refresh_placeholder_table(self):
        self.placeholder_table.setRowCount(0)
        for ph in self.global_defs.placeholders:
            row = self.placeholder_table.rowCount()
            self.placeholder_table.insertRow(row)
            self.placeholder_table.setItem(row, 0, QTableWidgetItem(ph.title))
            self.placeholder_table.setItem(row, 1, QTableWidgetItem(ph.name))
            self.placeholder_table.setItem(row, 2, QTableWidgetItem(ph.description))

    def on_placeholder_double_clicked(self, row, col):
        StaTableLogger.debug(f"on_placeholder_double_clicked: row={row}, col={col}")
        if row < 0 or row >= len(self.global_defs.placeholders):
            return
        target = self.global_defs.placeholders[row]
        dlg = DevicePlaceholderEditDialog(self, placeholder=target)
        if dlg.exec() == QDialog.Accepted:
            new_ph = dlg.get_placeholder()
            if not new_ph.name:
                QMessageBox.warning(self, "Warning", "Please enter a placeholder name.")
                return
            self.global_defs.placeholders[row] = new_ph
            self.refresh_placeholder_table()

    def add_placeholder(self):
        dlg = DevicePlaceholderEditDialog(self)
        if dlg.exec() == QDialog.Accepted:
            ph = dlg.get_placeholder()
            if not ph.name:
                QMessageBox.warning(self, "Warning", "Please enter a placeholder name.")
                return
            self.global_defs.placeholders.append(ph)
            self.refresh_placeholder_table()

    def delete_placeholder(self):
        row = self.placeholder_table.currentRow()
        if 0 <= row < len(self.global_defs.placeholders):
            self.global_defs.placeholders.pop(row)
            self.refresh_placeholder_table()

    # ------------------------------------------------------------------
    # Timer settings tab (multi-base-timer support)
    # ------------------------------------------------------------------
    def _create_timer_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Base timer tab
        self.timer_tabs = QTabWidget()
        self.timer_tabs.setTabsClosable(True)
        self.timer_tabs.tabCloseRequested.connect(self.close_timer_tab)
        self.timer_tabs.tabBarDoubleClicked.connect(self.rename_timer_tab)
        layout.addWidget(self.timer_tabs)

        # \"+\" button
        add_timer_btn = QPushButton("+")
        add_timer_btn.setFixedWidth(30)
        add_timer_btn.setToolTip("Add base timer")
        add_timer_btn.clicked.connect(self.add_timer_base)
        layout.addWidget(add_timer_btn, alignment=Qt.AlignRight)

        return widget

    def refresh_timer_tabs(self):
        """Display all base timers as tabs"""
        self.timer_tabs.clear()

        all_timers = [self.global_defs.timer_base] + self.global_defs.extra_timers
        for timer in all_timers:
            tab = self._create_timer_base_tab(timer)
            self.timer_tabs.addTab(tab, timer.title)

    def _create_timer_base_tab(self, timer: TimerBaseDef) -> QWidget:
        """Create an edit tab for one base timer"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        form = QFormLayout()
        layout.addLayout(form)

        # Title (editable, linked to tab name)
        title_edit = QLineEdit(timer.title)
        title_edit.textChanged.connect(lambda text, t=timer: self._on_timer_title_changed(t, text))
        form.addRow("Title *", title_edit)

        var_edit = QLineEdit(timer.variable_name)
        var_edit.textChanged.connect(lambda text, t=timer: self._on_timer_var_changed(t, text))
        form.addRow("Base variable name", var_edit)

        unit_edit = QLineEdit(timer.unit)
        unit_edit.textChanged.connect(lambda text, t=timer: self._on_timer_unit_changed(t, text))
        form.addRow("Unit", unit_edit)

        type_edit = QLineEdit(timer.data_type)
        type_edit.textChanged.connect(lambda text, t=timer: self._on_timer_type_changed(t, text))
        form.addRow("Type", type_edit)

        interrupt_edit = QLineEdit(timer.interrupt_name)
        interrupt_edit.textChanged.connect(lambda text, t=timer: self._on_timer_interrupt_changed(t, text))
        interrupt_edit.setPlaceholderText("Interrupt name (optional)")
        form.addRow("Interrupt name", interrupt_edit)

        # Edit button
        edit_btn = QPushButton("Edit base timer...")
        edit_btn.clicked.connect(lambda _checked, t=timer: self.edit_timer_base(t))
        form.addRow("", edit_btn)

        layout.addWidget(QLabel("Derived timer variable:"))
        derived_table = DoubleClickTable(0, 5)
        derived_table.setHorizontalHeaderLabels(["Title", "Period name", "Multiplier", "Variable name", "Type"])
        derived_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        derived_table.cellDoubleClicked.connect(lambda row, col, t=timer: self.on_derived_double_clicked(t, row, col))
        layout.addWidget(derived_table)

        # Derived timer button
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(lambda _checked, t=timer: self.add_derived(t))
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(lambda _checked, t=timer: self.delete_derived(t))
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self._refresh_derived_table(derived_table, timer)

        return widget

    def _refresh_derived_table(self, table: DoubleClickTable, timer: TimerBaseDef):
        """Display derived timers of the specified timer in the table"""
        table.setRowCount(0)
        for d in timer.derived:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(d.title))
            table.setItem(row, 1, QTableWidgetItem(d.period_name))
            table.setItem(row, 2, QTableWidgetItem(str(d.multiplier)))
            table.setItem(row, 3, QTableWidgetItem(d.variable_name))
            table.setItem(row, 4, QTableWidgetItem(d.data_type))

    def _on_timer_title_changed(self, timer: TimerBaseDef, text: str):
        timer.title = text.strip() or f"Timer base: {timer.variable_name}"
        all_timers = [self.global_defs.timer_base] + self.global_defs.extra_timers
        for i, t in enumerate(all_timers):
            if t is timer:
                self.timer_tabs.setTabText(i, timer.title)
                break

    def _on_timer_var_changed(self, timer: TimerBaseDef, text: str):
        timer.variable_name = text.strip()
        self.global_defs.add_timer_variables()

    def _on_timer_unit_changed(self, timer: TimerBaseDef, text: str):
        timer.unit = text.strip()
        self.global_defs.add_timer_variables()

    def _on_timer_type_changed(self, timer: TimerBaseDef, text: str):
        timer.data_type = text.strip()
        self.global_defs.add_timer_variables()

    def _on_timer_interrupt_changed(self, timer: TimerBaseDef, text: str):
        timer.interrupt_name = text.strip()

    def add_timer_base(self):
        dlg = TimerBaseEditDialog(self)
        if dlg.exec() == QDialog.Accepted:
            new_timer = dlg.get_timer_base()
            if not new_timer.variable_name:
                QMessageBox.warning(self, "Warning", "Please enter a base variable name.")
                return
            self.global_defs.extra_timers.append(new_timer)
            self.global_defs.add_timer_variables()
            self.refresh_timer_tabs()
            StaTableLogger.info(f"Timer base added: {new_timer.title}")

    def edit_timer_base(self, timer: TimerBaseDef):
        dlg = TimerBaseEditDialog(self, timer_base=timer)
        if dlg.exec() == QDialog.Accepted:
            new_timer = dlg.get_timer_base()
            if not new_timer.variable_name:
                QMessageBox.warning(self, "Warning", "Please enter a base variable name.")
                return
            timer.variable_name = new_timer.variable_name
            timer.unit = new_timer.unit
            timer.data_type = new_timer.data_type
            timer.title = new_timer.title
            timer.interrupt_name = new_timer.interrupt_name
            self.global_defs.add_timer_variables()
            self.refresh_timer_tabs()
            StaTableLogger.info(f"Timer base updated: {timer.title}")

    def close_timer_tab(self, index: int):
        if index == 0:
            QMessageBox.warning(self, "Warning", "The main timer cannot be deleted.")
            return
        all_timers = [self.global_defs.timer_base] + self.global_defs.extra_timers
        if 0 <= index < len(all_timers):
            timer = all_timers[index]
            reply = QMessageBox.question(
                self, "Confirm",
                f"Base timer '{timer.title}': confirm delete?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.global_defs.extra_timers.pop(index - 1)
                self.global_defs.add_timer_variables()
                self.refresh_timer_tabs()
                StaTableLogger.info(f"Timer base deleted: {timer.title}")

    def rename_timer_tab(self, index: int):
        all_timers = [self.global_defs.timer_base] + self.global_defs.extra_timers
        if 0 <= index < len(all_timers):
            current = all_timers[index]
            new_name, ok = QInputDialog.getText(
                self, "Rename timer", "Enter a new timer name:",
                text=current.title
            )
            if ok and new_name.strip():
                current.title = new_name.strip()
                self.timer_tabs.setTabText(index, current.title)
                self.global_defs.add_timer_variables()
                StaTableLogger.info(f"Timer tab renamed: {current.title}")

    def on_derived_double_clicked(self, timer: TimerBaseDef, row: int, col: int):
        StaTableLogger.debug(f"on_derived_double_clicked: timer='{timer.title}', row={row}, col={col}")
        if row < 0 or row >= len(timer.derived):
            return
        target = timer.derived[row]
        dlg = TimerDerivedEditDialog(self, derived=target)
        if dlg.exec() == QDialog.Accepted:
            new_d = dlg.get_derived()
            if not new_d.period_name:
                QMessageBox.warning(self, "Warning", "Please enter a period name.")
                return
            timer.derived[row] = new_d
            self.global_defs.add_timer_variables()
            self.refresh_timer_tabs()

    def add_derived(self, timer: TimerBaseDef):
        dlg = TimerDerivedEditDialog(self)
        if dlg.exec() == QDialog.Accepted:
            d = dlg.get_derived()
            if not d.period_name:
                QMessageBox.warning(self, "Warning", "Please enter a period name.")
                return
            timer.derived.append(d)
            self.global_defs.add_timer_variables()
            self.refresh_timer_tabs()

    def delete_derived(self, timer: TimerBaseDef):
        current_widget = self.timer_tabs.currentWidget()
        if current_widget:
            table = current_widget.findChild(DoubleClickTable)
            if table:
                row = table.currentRow()
                if 0 <= row < len(timer.derived):
                    timer.derived.pop(row)
                    self.global_defs.add_timer_variables()
                    self.refresh_timer_tabs()