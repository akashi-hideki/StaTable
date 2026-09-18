"""Global variables・Event flag definition管理画面"""

from typing import Optional, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView,
    QLabel, QMessageBox, QFormLayout, QComboBox, QSpinBox,
    QDialogButtonBox, QAbstractItemView, QWidget, QMenu,
    QStyledItemDelegate, QCheckBox
)

from statable.global_defs import SystemVariable, EventFlag, GlobalDefinitions
from .common_widgets import TitleEditWidget, TypeComboBox, GroupComboBox
from .logger import StaTableLogger


class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, items=None, editable=True, parent=None):
        super().__init__(parent)
        self.items = items or []
        self.editable = editable

    def set_items(self, items):
        self.items = items

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.setEditable(self.editable)
        combo.addItems(self.items)
        return combo

    def setEditorData(self, editor, index):
        value = index.data(Qt.EditRole)
        if value is not None:
            editor.setCurrentText(str(value))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText())


class InsertableTable(QTableWidget):
    insert_requested = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Insert:
            self.insert_requested.emit()
            return
        super().keyPressEvent(event)

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        add_action = menu.addAction("行をAdd")
        add_action.triggered.connect(self.insert_requested.emit)
        menu.exec(self.viewport().mapToGlobal(pos))


class ReadOnlyDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return None


class VariableEditDialog(QDialog):
    def __init__(self, parent=None, groups=None, variable: Optional[SystemVariable] = None, global_defs=None):
        super().__init__(parent)
        self.global_defs = global_defs if global_defs else GlobalDefinitions()
        self.groups = groups or []
        self.setWindowTitle("Global variablesEdit")
        self.setMinimumWidth(500)

        layout = QFormLayout(self)

        self.title_widget = TitleEditWidget(self, title=variable.title if variable else "")
        layout.addRow("", self.title_widget)

        self.name_edit = QLineEdit(variable.name if variable else "")
        layout.addRow("Name", self.name_edit)

        self.type_combo = TypeComboBox(self, global_defs=self.global_defs)
        if variable:
            self.type_combo.set_current_text(variable.type)
        layout.addRow("Type", self.type_combo)

        self.array_check = QCheckBox("Use array")
        self.array_check.setChecked(variable.array_size > 0 if variable else False)
        layout.addRow("", self.array_check)

        self.array_size_spin = QSpinBox()
        self.array_size_spin.setRange(1, 65536)
        self.array_size_spin.setValue(variable.array_size if variable and variable.array_size > 0 else 1)
        layout.addRow("Array size", self.array_size_spin)

        self.array_check.toggled.connect(self._on_array_toggled)
        self._on_array_toggled(self.array_check.isChecked())

        self.unit_edit = QLineEdit(variable.unit if variable else "")
        layout.addRow("Unit", self.unit_edit)

        self.default_edit = QLineEdit(variable.default_value if variable else "")
        layout.addRow("Initial value", self.default_edit)

        self.group_combo = GroupComboBox(self, groups=self.groups)
        if variable:
            self.group_combo.set_current_text(variable.group)
        layout.addRow("Group", self.group_combo)

        self.desc_edit = QLineEdit(variable.description if variable else "")
        layout.addRow("Description", self.desc_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _on_array_toggled(self, checked: bool):
        self.array_size_spin.setEnabled(checked)

    def _on_accept(self):
        auto_title = f"変数: {self.name_edit.text().strip() or '(unnamed)'}"
        if self.array_check.isChecked():
            auto_title = f"{self.name_edit.text().strip() or '(unnamed)'}[{self.array_size_spin.value()}]"
        self.title_widget.ensure_title(auto_title)
        self.accept()

    def get_variable(self) -> SystemVariable:
        array_size = self.array_size_spin.value() if self.array_check.isChecked() else 0
        return SystemVariable(
            name=self.name_edit.text().strip(),
            type=self.type_combo.current_text(),
            unit=self.unit_edit.text().strip(),
            default_value=self.default_edit.text().strip(),
            group=self.group_combo.current_text(),
            description=self.desc_edit.text().strip(),
            title=self.title_widget.get_title(),
            array_size=array_size,
        )


class FlagEditDialog(QDialog):
    def __init__(self, parent=None, groups=None, flag: Optional[EventFlag] = None):
        super().__init__(parent)
        self.groups = groups or []
        self.setWindowTitle("Event flagsEdit")
        self.setMinimumWidth(500)

        layout = QFormLayout(self)

        self.title_widget = TitleEditWidget(self, title=flag.title if flag else "")
        layout.addRow("", self.title_widget)

        self.name_edit = QLineEdit(flag.name if flag else "")
        layout.addRow("Flag name", self.name_edit)

        self.min_spin = QSpinBox()
        self.min_spin.setRange(0, 2**31 - 1)
        self.min_spin.setValue(flag.min_value if flag else 0)
        layout.addRow("Min value", self.min_spin)

        self.max_spin = QSpinBox()
        self.max_spin.setRange(0, 2**31 - 1)
        self.max_spin.setValue(flag.max_value if flag else 3)
        layout.addRow("Max value", self.max_spin)

        self.bit_width_label = QLabel()
        self.update_bit_width_label()
        self.min_spin.valueChanged.connect(self.update_bit_width_label)
        self.max_spin.valueChanged.connect(self.update_bit_width_label)
        layout.addRow("Bit width", self.bit_width_label)

        self.group_combo = GroupComboBox(self, groups=self.groups)
        if flag:
            self.group_combo.set_current_text(flag.group)
        layout.addRow("Group", self.group_combo)

        self.desc_edit = QLineEdit(flag.description if flag else "")
        layout.addRow("Description", self.desc_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def update_bit_width_label(self):
        min_val = self.min_spin.value()
        max_val = self.max_spin.value()
        if max_val < min_val:
            self.bit_width_label.setText("Error: Max value < Min value")
            self.bit_width_label.setStyleSheet("color: red;")
        else:
            width = (max_val - min_val).bit_length()
            self.bit_width_label.setText(f"{width} bit")
            self.bit_width_label.setStyleSheet("")

    def _on_accept(self):
        auto_title = f"フラグ: {self.name_edit.text().strip() or '(unnamed)'}"
        self.title_widget.ensure_title(auto_title)
        self.accept()

    def get_flag(self) -> EventFlag:
        return EventFlag(
            name=self.name_edit.text().strip(),
            min_value=self.min_spin.value(),
            max_value=self.max_spin.value(),
            group=self.group_combo.current_text(),
            description=self.desc_edit.text().strip(),
            title=self.title_widget.get_title(),
        )


class BulkVariableDialog(QDialog):
    """Global variables 一括登録ダイアログ"""

    def __init__(self, parent=None, groups=None, global_defs=None):
        super().__init__(parent)
        self.global_defs = global_defs if global_defs else GlobalDefinitions()
        self.groups = groups or []
        self.setWindowTitle("Global variables 一括登録")
        self.setMinimumSize(900, 400)

        layout = QVBoxLayout(self)
        self.table = InsertableTable(0, 8)
        self.table.setHorizontalHeaderLabels(["Title", "Name", "Type", "Array", "Unit", "Initial value", "Group", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        layout.addWidget(self.table)

        self.type_delegate = ComboBoxDelegate(items=self._type_list(), editable=True)
        self.table.setItemDelegateForColumn(2, self.type_delegate)

        self.group_delegate = ComboBoxDelegate(items=self.groups, editable=True)
        self.table.setItemDelegateForColumn(6, self.group_delegate)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add row")
        add_btn.clicked.connect(self.add_empty_row)
        del_btn = QPushButton("Delete row")
        del_btn.clicked.connect(self.delete_row)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.table.insert_requested.connect(self.add_empty_row)

    def _type_list(self):
        types = ["uint8_t", "uint16_t", "uint32_t", "uint64_t",
                 "int8_t", "int16_t", "int32_t", "int64_t",
                 "float", "double", "bool"]
        types.extend([t.name for t in self.global_defs.custom_types])
        return types

    def set_variables(self, variables: List[SystemVariable]):
        self.table.setRowCount(0)
        for var in variables:
            self.add_row(var)

    def add_row(self, variable: Optional[SystemVariable] = None):
        row = self.table.rowCount()
        self.table.insertRow(row)
        if variable:
            values = [variable.title, variable.name, variable.type,
                      str(variable.array_size) if variable.array_size > 0 else "",
                      variable.unit, variable.default_value,
                      variable.group, variable.description]
        else:
            values = ["", "", "uint16_t", "", "", "", "", ""]
        for col, text in enumerate(values):
            self.table.setItem(row, col, QTableWidgetItem(text))

    def add_empty_row(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            current_row = self.table.rowCount() - 1
        self.table.insertRow(current_row + 1)
        for col in range(8):
            if col == 2:
                self.table.setItem(current_row + 1, col, QTableWidgetItem("uint16_t"))
            else:
                self.table.setItem(current_row + 1, col, QTableWidgetItem(""))

    def delete_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def _on_accept(self):
        for row in range(self.table.rowCount()):
            title_item = self.table.item(row, 0)
            name_item = self.table.item(row, 1)
            if title_item and name_item and not title_item.text().strip() and name_item.text().strip():
                arr_item = self.table.item(row, 3)
                arr_str = arr_item.text().strip() if arr_item else ""
                if arr_str:
                    title_item.setText(f"{name_item.text().strip()}[{arr_str}]")
                else:
                    title_item.setText(f"変数: {name_item.text().strip()}")
        self.accept()

    def get_variables(self) -> List[SystemVariable]:
        variables = []
        for row in range(self.table.rowCount()):
            title = self.table.item(row, 0).text().strip() if self.table.item(row, 0) else ""
            name = self.table.item(row, 1).text().strip() if self.table.item(row, 1) else ""
            if not name:
                continue
            typ = self.table.item(row, 2).text().strip() if self.table.item(row, 2) else ""
            arr_str = self.table.item(row, 3).text().strip() if self.table.item(row, 3) else "0"
            try:
                arr = int(arr_str) if arr_str else 0
            except ValueError:
                arr = 0
            unit = self.table.item(row, 4).text().strip() if self.table.item(row, 4) else ""
            default = self.table.item(row, 5).text().strip() if self.table.item(row, 5) else ""
            group = self.table.item(row, 6).text().strip() if self.table.item(row, 6) else ""
            desc = self.table.item(row, 7).text().strip() if self.table.item(row, 7) else ""
            if not title:
                if arr > 0:
                    title = f"{name}[{arr}]"
                else:
                    title = f"変数: {name}"
            variables.append(SystemVariable(name, typ, unit, default, group, desc, title, arr))
        return variables


class BulkFlagDialog(QDialog):
    """Event flags 一括登録ダイアログ"""

    def __init__(self, parent=None, groups=None):
        super().__init__(parent)
        self.groups = groups or []
        self.setWindowTitle("Event flags 一括登録")
        self.setMinimumSize(900, 400)

        layout = QVBoxLayout(self)
        self.table = InsertableTable(0, 7)
        self.table.setHorizontalHeaderLabels(["Title", "Flag name", "Min value", "Max value", "Bit width", "Group", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        layout.addWidget(self.table)

        self.group_delegate = ComboBoxDelegate(items=self.groups, editable=True)
        self.table.setItemDelegateForColumn(5, self.group_delegate)
        self.table.setItemDelegateForColumn(4, ReadOnlyDelegate(self.table))

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add row")
        add_btn.clicked.connect(self.add_empty_row)
        del_btn = QPushButton("Delete row")
        del_btn.clicked.connect(self.delete_row)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.table.itemChanged.connect(self.on_item_changed)
        self.table.insert_requested.connect(self.add_empty_row)

    def set_flags(self, flags: List[EventFlag]):
        self.table.setRowCount(0)
        for flag in flags:
            self.add_row(flag)

    def add_row(self, flag: Optional[EventFlag] = None):
        row = self.table.rowCount()
        self.table.insertRow(row)
        if flag:
            values = [flag.title, flag.name, str(flag.min_value), str(flag.max_value),
                      str(flag.bit_width), flag.group, flag.description]
        else:
            values = ["", "", "0", "3", "2", "", ""]
        for col, text in enumerate(values):
            item = QTableWidgetItem(text)
            if col == 4:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, col, item)
        self.update_bit_width(row)

    def add_empty_row(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            current_row = self.table.rowCount() - 1
        self.table.insertRow(current_row + 1)
        for col in range(7):
            if col == 2:
                self.table.setItem(current_row + 1, col, QTableWidgetItem("0"))
            elif col == 3:
                self.table.setItem(current_row + 1, col, QTableWidgetItem("3"))
            elif col == 4:
                item = QTableWidgetItem("2")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(current_row + 1, col, item)
            else:
                self.table.setItem(current_row + 1, col, QTableWidgetItem(""))

    def delete_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def on_item_changed(self, item):
        if item.column() in (2, 3):
            self.update_bit_width(item.row())

    def update_bit_width(self, row):
        min_item = self.table.item(row, 2)
        max_item = self.table.item(row, 3)
        if not min_item or not max_item:
            return
        try:
            min_val = int(min_item.text())
            max_val = int(max_item.text())
            if max_val < min_val:
                width = "Error"
            else:
                width = str((max_val - min_val).bit_length())
        except ValueError:
            width = "?"
        width_item = self.table.item(row, 4)
        if width_item:
            width_item.setText(width)

    def _on_accept(self):
        for row in range(self.table.rowCount()):
            title_item = self.table.item(row, 0)
            name_item = self.table.item(row, 1)
            if title_item and name_item and not title_item.text().strip() and name_item.text().strip():
                title_item.setText(f"フラグ: {name_item.text().strip()}")
        self.accept()

    def get_flags(self) -> List[EventFlag]:
        flags = []
        for row in range(self.table.rowCount()):
            title = self.table.item(row, 0).text().strip() if self.table.item(row, 0) else ""
            name = self.table.item(row, 1).text().strip() if self.table.item(row, 1) else ""
            if not name:
                continue
            min_str = self.table.item(row, 2).text().strip() if self.table.item(row, 2) else "0"
            max_str = self.table.item(row, 3).text().strip() if self.table.item(row, 3) else "0"
            try:
                min_val = int(min_str)
                max_val = int(max_str)
            except ValueError:
                min_val, max_val = 0, 0
            group = self.table.item(row, 5).text().strip() if self.table.item(row, 5) else ""
            desc = self.table.item(row, 6).text().strip() if self.table.item(row, 6) else ""
            if not title:
                title = f"フラグ: {name}"
            flags.append(EventFlag(name, min_val, max_val, group, desc, title))
        return flags


class GlobalDefinitionsDialog(QDialog):
    def __init__(self, defs: GlobalDefinitions, parent=None):
        super().__init__(parent)
        self.defs = defs
        self._updating = False
        self.setWindowTitle("Global variables & Event flag definition")
        self.setMinimumSize(900, 600)

        layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search (prefix match):"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Title・Member name・Group名")
        self.search_edit.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        self.tab = QTabWidget()
        layout.addWidget(self.tab)

        self.tab.addTab(self._create_variable_tab(), "Global variables")
        self.tab.addTab(self._create_flag_tab(), "Event flags")

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

        self.refresh_variables()
        self.refresh_flags()
        StaTableLogger.debug("GlobalDefinitionsDialog initialized")

    def _create_variable_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.var_table = InsertableTable(0, 8)
        self.var_table.setHorizontalHeaderLabels(["Title", "Name", "Type", "Array", "Unit", "Initial value", "Group", "Description"])
        self.var_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.var_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.var_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        layout.addWidget(self.var_table)

        self.type_delegate = ComboBoxDelegate(items=self._type_list(), editable=True)
        self.var_table.setItemDelegateForColumn(2, self.type_delegate)

        self.group_delegate = ComboBoxDelegate(items=self.defs.variable_groups(), editable=True)
        self.var_table.setItemDelegateForColumn(6, self.group_delegate)

        btn_layout = QHBoxLayout()
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self.delete_variable)
        bulk_btn = QPushButton("Register in bulk...")
        bulk_btn.clicked.connect(self.bulk_variables)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(bulk_btn)
        layout.addLayout(btn_layout)

        self.var_table.insert_requested.connect(self.add_empty_variable_row)
        self.var_table.itemChanged.connect(self.on_variable_item_changed)

        return widget

    def _create_flag_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.flag_table = InsertableTable(0, 7)
        self.flag_table.setHorizontalHeaderLabels(["Title", "Flag name", "Min value", "Max value", "Bit width", "Group", "Description"])
        self.flag_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.flag_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.flag_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.flag_table.setItemDelegateForColumn(4, ReadOnlyDelegate(self.flag_table))
        layout.addWidget(self.flag_table)

        self.flag_group_delegate = ComboBoxDelegate(items=self.defs.flag_groups(), editable=True)
        self.flag_table.setItemDelegateForColumn(5, self.flag_group_delegate)

        btn_layout = QHBoxLayout()
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self.delete_flag)
        bulk_btn = QPushButton("Register in bulk...")
        bulk_btn.clicked.connect(self.bulk_flags)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(bulk_btn)
        layout.addLayout(btn_layout)

        self.flag_table.insert_requested.connect(self.add_empty_flag_row)
        self.flag_table.itemChanged.connect(self.on_flag_item_changed)

        return widget

    def _type_list(self):
        types = ["uint8_t", "uint16_t", "uint32_t", "uint64_t",
                 "int8_t", "int16_t", "int32_t", "int64_t",
                 "float", "double", "bool"]
        types.extend([t.name for t in self.defs.custom_types])
        return types

    def on_search_changed(self, text):
        self.refresh_variables()
        self.refresh_flags()

    def _matches(self, title: str, name: str, group: str, query: str) -> bool:
        if not query:
            return True
        q = query.lower()
        return title.lower().startswith(q) or name.lower().startswith(q) or group.lower().startswith(q)

    def refresh_variables(self):
        self._updating = True
        query = self.search_edit.text().strip().lower()
        self.var_table.setRowCount(0)
        for var in self.defs.variables:
            if self._matches(var.title, var.name, var.group, query):
                row = self.var_table.rowCount()
                self.var_table.insertRow(row)
                values = [var.title, var.name, var.type,
                          str(var.array_size) if var.array_size > 0 else "",
                          var.unit, var.default_value, var.group, var.description]
                for col, text in enumerate(values):
                    item = QTableWidgetItem(text)
                    item.setData(Qt.UserRole, var)
                    self.var_table.setItem(row, col, item)
        self.var_table.insertRow(self.var_table.rowCount())
        for col in range(8):
            self.var_table.setItem(self.var_table.rowCount() - 1, col, QTableWidgetItem(""))
        self.type_delegate.set_items(self._type_list())
        self.group_delegate.set_items(self.defs.variable_groups())
        self._updating = False

    def on_variable_item_changed(self, item):
        if self._updating:
            return
        var = item.data(Qt.UserRole)
        if var:
            row = item.row()
            var.title = self.var_table.item(row, 0).text().strip() if self.var_table.item(row, 0) else ""
            var.name = self.var_table.item(row, 1).text().strip() if self.var_table.item(row, 1) else ""
            var.type = self.var_table.item(row, 2).text().strip() if self.var_table.item(row, 2) else ""
            arr_str = self.var_table.item(row, 3).text().strip() if self.var_table.item(row, 3) else "0"
            try:
                var.array_size = int(arr_str) if arr_str else 0
            except ValueError:
                var.array_size = 0
            var.unit = self.var_table.item(row, 4).text().strip() if self.var_table.item(row, 4) else ""
            var.default_value = self.var_table.item(row, 5).text().strip() if self.var_table.item(row, 5) else ""
            var.group = self.var_table.item(row, 6).text().strip() if self.var_table.item(row, 6) else ""
            var.description = self.var_table.item(row, 7).text().strip() if self.var_table.item(row, 7) else ""
            if not var.title and var.name:
                if var.array_size > 0:
                    var.title = f"{var.name}[{var.array_size}]"
                else:
                    var.title = f"変数: {var.name}"
        else:
            row = item.row()
            name_item = self.var_table.item(row, 1)
            if name_item and name_item.text().strip():
                new_var = self._read_variable_row(row)
                if new_var:
                    self.defs.variables.append(new_var)
                    self.refresh_variables()

    def _read_variable_row(self, row) -> Optional[SystemVariable]:
        title = self.var_table.item(row, 0).text().strip() if self.var_table.item(row, 0) else ""
        name = self.var_table.item(row, 1).text().strip() if self.var_table.item(row, 1) else ""
        if not name:
            return None
        typ = self.var_table.item(row, 2).text().strip() if self.var_table.item(row, 2) else ""
        arr_str = self.var_table.item(row, 3).text().strip() if self.var_table.item(row, 3) else "0"
        try:
            arr = int(arr_str) if arr_str else 0
        except ValueError:
            arr = 0
        unit = self.var_table.item(row, 4).text().strip() if self.var_table.item(row, 4) else ""
        default = self.var_table.item(row, 5).text().strip() if self.var_table.item(row, 5) else ""
        group = self.var_table.item(row, 6).text().strip() if self.var_table.item(row, 6) else ""
        desc = self.var_table.item(row, 7).text().strip() if self.var_table.item(row, 7) else ""
        if not title:
            if arr > 0:
                title = f"{name}[{arr}]"
            else:
                title = f"変数: {name}"
        return SystemVariable(name, typ, unit, default, group, desc, title, arr)

    def add_empty_variable_row(self):
        current_row = self.var_table.currentRow()
        if current_row < 0:
            current_row = self.var_table.rowCount() - 2
        self.var_table.insertRow(current_row + 1)
        for col in range(8):
            if col == 2:
                self.var_table.setItem(current_row + 1, col, QTableWidgetItem("uint16_t"))
            else:
                self.var_table.setItem(current_row + 1, col, QTableWidgetItem(""))

    def delete_variable(self):
        row = self.var_table.currentRow()
        if row < 0:
            return
        item = self.var_table.item(row, 1)
        if item:
            var = item.data(Qt.UserRole)
            if var:
                self.defs.variables.remove(var)
        self.var_table.removeRow(row)
        if self.var_table.rowCount() == 0 or self.var_table.item(self.var_table.rowCount()-1, 1).text() != "":
            self.refresh_variables()

    def bulk_variables(self):
        dlg = BulkVariableDialog(self, groups=self.defs.variable_groups(), global_defs=self.defs)
        dlg.set_variables(self.defs.variables)
        if dlg.exec() == QDialog.Accepted:
            self.defs.variables = dlg.get_variables()
            self.refresh_variables()

    def refresh_flags(self):
        self._updating = True
        query = self.search_edit.text().strip().lower()
        self.flag_table.setRowCount(0)
        for flag in self.defs.flags:
            if self._matches(flag.title, flag.name, flag.group, query):
                row = self.flag_table.rowCount()
                self.flag_table.insertRow(row)
                values = [flag.title, flag.name, str(flag.min_value), str(flag.max_value),
                          str(flag.bit_width), flag.group, flag.description]
                for col, text in enumerate(values):
                    item = QTableWidgetItem(text)
                    if col == 4:
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setData(Qt.UserRole, flag)
                    self.flag_table.setItem(row, col, item)
        self.flag_table.insertRow(self.flag_table.rowCount())
        for col in range(7):
            item = QTableWidgetItem("")
            if col == 4:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.flag_table.setItem(self.flag_table.rowCount() - 1, col, item)
        self.flag_group_delegate.set_items(self.defs.flag_groups())
        self._updating = False

    def on_flag_item_changed(self, item):
        if self._updating:
            return
        flag = item.data(Qt.UserRole)
        if flag:
            row = item.row()
            flag.title = self.flag_table.item(row, 0).text().strip() if self.flag_table.item(row, 0) else ""
            flag.name = self.flag_table.item(row, 1).text().strip() if self.flag_table.item(row, 1) else ""
            min_str = self.flag_table.item(row, 2).text().strip() if self.flag_table.item(row, 2) else "0"
            max_str = self.flag_table.item(row, 3).text().strip() if self.flag_table.item(row, 3) else "0"
            try:
                flag.min_value = int(min_str)
                flag.max_value = int(max_str)
            except ValueError:
                flag.min_value, flag.max_value = 0, 0
            flag.group = self.flag_table.item(row, 5).text().strip() if self.flag_table.item(row, 5) else ""
            flag.description = self.flag_table.item(row, 6).text().strip() if self.flag_table.item(row, 6) else ""
            if not flag.title and flag.name:
                flag.title = f"フラグ: {flag.name}"
            width_item = self.flag_table.item(row, 4)
            if width_item:
                width_item.setText(str(flag.bit_width))
        else:
            row = item.row()
            name_item = self.flag_table.item(row, 1)
            if name_item and name_item.text().strip():
                new_flag = self._read_flag_row(row)
                if new_flag:
                    self.defs.flags.append(new_flag)
                    self.refresh_flags()

    def _read_flag_row(self, row) -> Optional[EventFlag]:
        title = self.flag_table.item(row, 0).text().strip() if self.flag_table.item(row, 0) else ""
        name = self.flag_table.item(row, 1).text().strip() if self.flag_table.item(row, 1) else ""
        if not name:
            return None
        min_str = self.flag_table.item(row, 2).text().strip() if self.flag_table.item(row, 2) else "0"
        max_str = self.flag_table.item(row, 3).text().strip() if self.flag_table.item(row, 3) else "0"
        try:
            min_val = int(min_str)
            max_val = int(max_str)
        except ValueError:
            min_val, max_val = 0, 0
        group = self.flag_table.item(row, 5).text().strip() if self.flag_table.item(row, 5) else ""
        desc = self.flag_table.item(row, 6).text().strip() if self.flag_table.item(row, 6) else ""
        if not title:
            title = f"フラグ: {name}"
        return EventFlag(name, min_val, max_val, group, desc, title)

    def add_empty_flag_row(self):
        current_row = self.flag_table.currentRow()
        if current_row < 0:
            current_row = self.flag_table.rowCount() - 2
        self.flag_table.insertRow(current_row + 1)
        for col in range(7):
            if col == 2:
                self.flag_table.setItem(current_row + 1, col, QTableWidgetItem("0"))
            elif col == 3:
                self.flag_table.setItem(current_row + 1, col, QTableWidgetItem("3"))
            elif col == 4:
                item = QTableWidgetItem("2")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.flag_table.setItem(current_row + 1, col, item)
            else:
                self.flag_table.setItem(current_row + 1, col, QTableWidgetItem(""))

    def delete_flag(self):
        row = self.flag_table.currentRow()
        if row < 0:
            return
        item = self.flag_table.item(row, 1)
        if item:
            flag = item.data(Qt.UserRole)
            if flag:
                self.defs.flags.remove(flag)
        self.flag_table.removeRow(row)
        if self.flag_table.rowCount() == 0 or self.flag_table.item(self.flag_table.rowCount()-1, 1).text() != "":
            self.refresh_flags()

    def bulk_flags(self):
        dlg = BulkFlagDialog(self, groups=self.defs.flag_groups())
        dlg.set_flags(self.defs.flags)
        if dlg.exec() == QDialog.Accepted:
            self.defs.flags = dlg.get_flags()
            self.refresh_flags()