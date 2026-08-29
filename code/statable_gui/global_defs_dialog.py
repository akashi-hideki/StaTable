"""グローバル変数・イベントフラグ定義管理画面（コンボボックス編集対応）"""

from typing import Optional, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView,
    QLabel, QMessageBox, QFormLayout, QComboBox, QSpinBox,
    QDialogButtonBox, QAbstractItemView, QWidget, QMenu,
    QStyledItemDelegate, QCompleter
)

from statable.global_defs import SystemVariable, EventFlag, GlobalDefinitions
from .logger import StaTableLogger


# ----------------------------------------------------------------------
# 編集可能コンボボックス用デリゲート
# ----------------------------------------------------------------------
class ComboBoxDelegate(QStyledItemDelegate):
    """テーブルセルに編集可能コンボボックスを提供するデリゲート"""

    def __init__(self, items=None, editable=True, parent=None):
        super().__init__(parent)
        self.items = items or []
        self.editable = editable

    def set_items(self, items):
        """候補リストを更新する"""
        self.items = items

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.setEditable(self.editable)
        combo.addItems(self.items)
        if self.editable:
            # 前方一致補完
            completer = combo.completer()
            if completer:
                completer.setFilterMode(Qt.MatchStartsWith)
        return combo

    def setEditorData(self, editor, index):
        value = index.data(Qt.EditRole)
        if value is not None:
            editor.setCurrentText(str(value))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText())


# ----------------------------------------------------------------------
# Insertキーで行追加できるテーブル
# ----------------------------------------------------------------------
class InsertableTable(QTableWidget):
    """Insertキーで現在行の下に空行を追加するテーブル"""
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
        add_action = menu.addAction("行を追加")
        add_action.triggered.connect(self.insert_requested.emit)
        menu.exec(self.viewport().mapToGlobal(pos))


# ----------------------------------------------------------------------
# 読み取り専用デリゲート（ビット幅列用）
# ----------------------------------------------------------------------
class ReadOnlyDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return None


# ----------------------------------------------------------------------
# グローバル変数編集ダイアログ（単一編集用）
# ----------------------------------------------------------------------
class VariableEditDialog(QDialog):
    def __init__(self, parent=None, groups=None, variable: Optional[SystemVariable] = None):
        super().__init__(parent)
        self.setWindowTitle("グローバル変数編集")
        self.setMinimumWidth(400)
        self.groups = groups or []

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        if variable:
            self.name_edit.setText(variable.name)
        layout.addRow("名前", self.name_edit)

        # 型（編集可能コンボ）
        self.type_combo = QComboBox()
        self.type_combo.setEditable(True)
        self.type_combo.addItems([
            "uint8_t", "uint16_t", "uint32_t", "uint64_t",
            "int8_t", "int16_t", "int32_t", "int64_t",
            "float", "double", "bool"
        ])
        if variable:
            self.type_combo.setCurrentText(variable.type)
        else:
            self.type_combo.setCurrentText("uint16_t")
        layout.addRow("型", self.type_combo)

        self.unit_edit = QLineEdit()
        if variable:
            self.unit_edit.setText(variable.unit)
        layout.addRow("単位", self.unit_edit)

        self.default_edit = QLineEdit()
        if variable:
            self.default_edit.setText(variable.default_value)
        layout.addRow("初期値", self.default_edit)

        # グループ（編集可能コンボ）
        self.group_combo = QComboBox()
        self.group_combo.setEditable(True)
        self.group_combo.addItems(self.groups)
        if variable:
            self.group_combo.setCurrentText(variable.group)
        layout.addRow("グループ", self.group_combo)

        self.desc_edit = QLineEdit()
        if variable:
            self.desc_edit.setText(variable.description)
        layout.addRow("説明", self.desc_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_variable(self) -> SystemVariable:
        return SystemVariable(
            name=self.name_edit.text().strip(),
            type=self.type_combo.currentText().strip(),
            unit=self.unit_edit.text().strip(),
            default_value=self.default_edit.text().strip(),
            group=self.group_combo.currentText().strip(),
            description=self.desc_edit.text().strip(),
        )


# ----------------------------------------------------------------------
# イベントフラグ編集ダイアログ（最小値・最大値方式）
# ----------------------------------------------------------------------
class FlagEditDialog(QDialog):
    def __init__(self, parent=None, groups=None, flag: Optional[EventFlag] = None):
        super().__init__(parent)
        self.setWindowTitle("イベントフラグ編集")
        self.setMinimumWidth(400)
        self.groups = groups or []

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        if flag:
            self.name_edit.setText(flag.name)
        layout.addRow("フラグ名", self.name_edit)

        self.min_spin = QSpinBox()
        self.min_spin.setRange(0, 2**31 - 1)
        if flag:
            self.min_spin.setValue(flag.min_value)
        layout.addRow("最小値", self.min_spin)

        self.max_spin = QSpinBox()
        self.max_spin.setRange(0, 2**31 - 1)
        if flag:
            self.max_spin.setValue(flag.max_value)
        else:
            self.max_spin.setValue(3)
        layout.addRow("最大値", self.max_spin)

        self.bit_width_label = QLabel()
        self.update_bit_width_label()
        self.min_spin.valueChanged.connect(self.update_bit_width_label)
        self.max_spin.valueChanged.connect(self.update_bit_width_label)
        layout.addRow("ビット幅", self.bit_width_label)

        # グループ（編集可能コンボ）
        self.group_combo = QComboBox()
        self.group_combo.setEditable(True)
        self.group_combo.addItems(self.groups)
        if flag:
            self.group_combo.setCurrentText(flag.group)
        layout.addRow("グループ", self.group_combo)

        self.desc_edit = QLineEdit()
        if flag:
            self.desc_edit.setText(flag.description)
        layout.addRow("説明", self.desc_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def update_bit_width_label(self):
        min_val = self.min_spin.value()
        max_val = self.max_spin.value()
        if max_val < min_val:
            self.bit_width_label.setText("エラー: 最大値 < 最小値")
            self.bit_width_label.setStyleSheet("color: red;")
        else:
            width = (max_val - min_val).bit_length()
            self.bit_width_label.setText(f"{width} bit")
            self.bit_width_label.setStyleSheet("")

    def get_flag(self) -> EventFlag:
        return EventFlag(
            name=self.name_edit.text().strip(),
            min_value=self.min_spin.value(),
            max_value=self.max_spin.value(),
            group=self.group_combo.currentText().strip(),
            description=self.desc_edit.text().strip(),
        )


# ----------------------------------------------------------------------
# 一括登録ダイアログ（グローバル変数）
# ----------------------------------------------------------------------
class BulkVariableDialog(QDialog):
    def __init__(self, parent=None, groups=None):
        super().__init__(parent)
        self.setWindowTitle("グローバル変数 一括登録")
        self.setMinimumSize(700, 400)
        self.groups = groups or []

        layout = QVBoxLayout(self)
        self.table = InsertableTable(0, 6)
        self.table.setHorizontalHeaderLabels(["名前", "型", "単位", "初期値", "グループ", "説明"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        layout.addWidget(self.table)

        # ★ 型列（1列目）にコンボボックスデリゲート
        self.type_delegate = ComboBoxDelegate(items=[
            "uint8_t", "uint16_t", "uint32_t", "uint64_t",
            "int8_t", "int16_t", "int32_t", "int64_t",
            "float", "double", "bool"
        ], editable=True)
        self.table.setItemDelegateForColumn(1, self.type_delegate)

        # ★ グループ列（4列目）にコンボボックスデリゲート
        self.group_delegate = ComboBoxDelegate(items=self.groups, editable=True)
        self.table.setItemDelegateForColumn(4, self.group_delegate)

        btn_layout = QHBoxLayout()
        del_btn = QPushButton("行削除")
        del_btn.clicked.connect(self.delete_row)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.table.insert_requested.connect(self.add_empty_row)

    def set_variables(self, variables: List[SystemVariable]):
        """既存の変数一覧をテーブルに読み込む"""
        self.table.setRowCount(0)
        for var in variables:
            self.add_row(var)

    def add_row(self, variable: Optional[SystemVariable] = None):
        row = self.table.rowCount()
        self.table.insertRow(row)
        if variable:
            values = [variable.name, variable.type, variable.unit,
                      variable.default_value, variable.group, variable.description]
        else:
            values = ["", "uint16_t", "", "", "", ""]
        for col, text in enumerate(values):
            self.table.setItem(row, col, QTableWidgetItem(text))

    def add_empty_row(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            current_row = self.table.rowCount() - 1
        self.table.insertRow(current_row + 1)
        for col in range(6):
            if col == 1:
                self.table.setItem(current_row + 1, col, QTableWidgetItem("uint16_t"))
            else:
                self.table.setItem(current_row + 1, col, QTableWidgetItem(""))

    def delete_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def get_variables(self) -> List[SystemVariable]:
        variables = []
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text().strip() if self.table.item(row, 0) else ""
            if not name:
                continue
            typ = self.table.item(row, 1).text().strip() if self.table.item(row, 1) else ""
            unit = self.table.item(row, 2).text().strip() if self.table.item(row, 2) else ""
            default = self.table.item(row, 3).text().strip() if self.table.item(row, 3) else ""
            group = self.table.item(row, 4).text().strip() if self.table.item(row, 4) else ""
            desc = self.table.item(row, 5).text().strip() if self.table.item(row, 5) else ""
            variables.append(SystemVariable(name, typ, unit, default, group, desc))
        return variables


# ----------------------------------------------------------------------
# 一括登録ダイアログ（イベントフラグ）
# ----------------------------------------------------------------------
class BulkFlagDialog(QDialog):
    def __init__(self, parent=None, groups=None):
        super().__init__(parent)
        self.setWindowTitle("イベントフラグ 一括登録")
        self.setMinimumSize(700, 400)
        self.groups = groups or []

        layout = QVBoxLayout(self)
        self.table = InsertableTable(0, 6)
        self.table.setHorizontalHeaderLabels(["フラグ名", "最小値", "最大値", "ビット幅", "グループ", "説明"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        layout.addWidget(self.table)

        # ★ グループ列（4列目）にコンボボックスデリゲート
        self.group_delegate = ComboBoxDelegate(items=self.groups, editable=True)
        self.table.setItemDelegateForColumn(4, self.group_delegate)

        # ビット幅列は読み取り専用
        self.table.setItemDelegateForColumn(3, ReadOnlyDelegate(self.table))

        btn_layout = QHBoxLayout()
        del_btn = QPushButton("行削除")
        del_btn.clicked.connect(self.delete_row)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.table.itemChanged.connect(self.on_item_changed)
        self.table.insert_requested.connect(self.add_empty_row)

    def set_flags(self, flags: List[EventFlag]):
        """既存のフラグ一覧をテーブルに読み込む"""
        self.table.setRowCount(0)
        for flag in flags:
            self.add_row(flag)

    def add_row(self, flag: Optional[EventFlag] = None):
        row = self.table.rowCount()
        self.table.insertRow(row)
        if flag:
            values = [flag.name, str(flag.min_value), str(flag.max_value),
                      str(flag.bit_width), flag.group, flag.description]
        else:
            values = ["", "0", "3", "2", "", ""]
        for col, text in enumerate(values):
            item = QTableWidgetItem(text)
            if col == 3:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, col, item)
        self.update_bit_width(row)

    def add_empty_row(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            current_row = self.table.rowCount() - 1
        self.table.insertRow(current_row + 1)
        for col in range(6):
            if col == 1:
                self.table.setItem(current_row + 1, col, QTableWidgetItem("0"))
            elif col == 2:
                self.table.setItem(current_row + 1, col, QTableWidgetItem("3"))
            elif col == 3:
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
        if item.column() in (1, 2):
            self.update_bit_width(item.row())

    def update_bit_width(self, row):
        min_item = self.table.item(row, 1)
        max_item = self.table.item(row, 2)
        if not min_item or not max_item:
            return
        try:
            min_val = int(min_item.text())
            max_val = int(max_item.text())
            if max_val < min_val:
                width = "エラー"
            else:
                width = str((max_val - min_val).bit_length())
        except ValueError:
            width = "?"
        width_item = self.table.item(row, 3)
        if width_item:
            width_item.setText(width)

    def get_flags(self) -> List[EventFlag]:
        flags = []
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text().strip() if self.table.item(row, 0) else ""
            if not name:
                continue
            min_str = self.table.item(row, 1).text().strip() if self.table.item(row, 1) else "0"
            max_str = self.table.item(row, 2).text().strip() if self.table.item(row, 2) else "0"
            try:
                min_val = int(min_str)
                max_val = int(max_str)
            except ValueError:
                min_val, max_val = 0, 0
            group = self.table.item(row, 4).text().strip() if self.table.item(row, 4) else ""
            desc = self.table.item(row, 5).text().strip() if self.table.item(row, 5) else ""
            flags.append(EventFlag(name, min_val, max_val, group, desc))
        return flags


# ----------------------------------------------------------------------
# 定義管理画面（メインダイアログ）
# ----------------------------------------------------------------------
class GlobalDefinitionsDialog(QDialog):
    def __init__(self, defs: GlobalDefinitions, parent=None):
        super().__init__(parent)
        self.defs = defs
        self._updating = False
        self.setWindowTitle("グローバル変数 & イベントフラグ定義")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)

        # 検索ボックス
        search_layout = QHBoxLayout()
        search_label = QLabel("検索（前方一致）:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("メンバ名・グループ名")
        self.search_edit.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # タブ
        self.tab = QTabWidget()
        layout.addWidget(self.tab)

        # グローバル変数タブ
        var_tab = self._create_variable_tab()
        self.tab.addTab(var_tab, "グローバル変数")

        # イベントフラグタブ
        flag_tab = self._create_flag_tab()
        self.tab.addTab(flag_tab, "イベントフラグ")

        # 閉じるボタン
        close_btn = QPushButton("閉じる")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

        self.refresh_variables()
        self.refresh_flags()
        StaTableLogger.debug("GlobalDefinitionsDialog initialized")

    def _create_variable_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.var_table = InsertableTable(0, 6)
        self.var_table.setHorizontalHeaderLabels(["名前", "型", "単位", "初期値", "グループ", "説明"])
        self.var_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.var_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.var_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        layout.addWidget(self.var_table)

        # ★ 型列（1列目）にコンボボックスデリゲート
        self.type_delegate = ComboBoxDelegate(items=[
            "uint8_t", "uint16_t", "uint32_t", "uint64_t",
            "int8_t", "int16_t", "int32_t", "int64_t",
            "float", "double", "bool"
        ], editable=True)
        self.var_table.setItemDelegateForColumn(1, self.type_delegate)

        # ★ グループ列（4列目）にコンボボックスデリゲート
        self.group_delegate = ComboBoxDelegate(items=self.defs.variable_groups(), editable=True)
        self.var_table.setItemDelegateForColumn(4, self.group_delegate)

        btn_layout = QHBoxLayout()
        del_btn = QPushButton("削除")
        del_btn.clicked.connect(self.delete_variable)
        bulk_btn = QPushButton("一括登録...")
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

        self.flag_table = InsertableTable(0, 6)
        self.flag_table.setHorizontalHeaderLabels(["フラグ名", "最小値", "最大値", "ビット幅", "グループ", "説明"])
        self.flag_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.flag_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.flag_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.flag_table.setItemDelegateForColumn(3, ReadOnlyDelegate(self.flag_table))
        layout.addWidget(self.flag_table)

        # ★ グループ列（4列目）にコンボボックスデリゲート
        self.flag_group_delegate = ComboBoxDelegate(items=self.defs.flag_groups(), editable=True)
        self.flag_table.setItemDelegateForColumn(4, self.flag_group_delegate)

        btn_layout = QHBoxLayout()
        del_btn = QPushButton("削除")
        del_btn.clicked.connect(self.delete_flag)
        bulk_btn = QPushButton("一括登録...")
        bulk_btn.clicked.connect(self.bulk_flags)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(bulk_btn)
        layout.addLayout(btn_layout)

        self.flag_table.insert_requested.connect(self.add_empty_flag_row)
        self.flag_table.itemChanged.connect(self.on_flag_item_changed)

        return widget

    # ------------------------------------------------------------------
    # 検索
    # ------------------------------------------------------------------
    def on_search_changed(self, text):
        self.refresh_variables()
        self.refresh_flags()

    def _matches(self, name: str, group: str, query: str) -> bool:
        if not query:
            return True
        q = query.lower()
        return name.lower().startswith(q) or group.lower().startswith(q)

    # ------------------------------------------------------------------
    # グローバル変数
    # ------------------------------------------------------------------
    def refresh_variables(self):
        self._updating = True
        query = self.search_edit.text().strip().lower()
        self.var_table.setRowCount(0)
        for var in self.defs.variables:
            if self._matches(var.name, var.group, query):
                row = self.var_table.rowCount()
                self.var_table.insertRow(row)
                values = [var.name, var.type, var.unit, var.default_value, var.group, var.description]
                for col, text in enumerate(values):
                    item = QTableWidgetItem(text)
                    item.setData(Qt.UserRole, var)
                    self.var_table.setItem(row, col, item)
        # 末尾に空行を追加
        self.var_table.insertRow(self.var_table.rowCount())
        for col in range(6):
            item = QTableWidgetItem("")
            self.var_table.setItem(self.var_table.rowCount() - 1, col, item)
        # グループ候補を更新
        self.group_delegate.set_items(self.defs.variable_groups())
        self._updating = False

    def on_variable_item_changed(self, item):
        if self._updating:
            return
        var = item.data(Qt.UserRole)
        if var:
            row = item.row()
            name = self.var_table.item(row, 0).text().strip() if self.var_table.item(row, 0) else ""
            typ = self.var_table.item(row, 1).text().strip() if self.var_table.item(row, 1) else ""
            unit = self.var_table.item(row, 2).text().strip() if self.var_table.item(row, 2) else ""
            default = self.var_table.item(row, 3).text().strip() if self.var_table.item(row, 3) else ""
            group = self.var_table.item(row, 4).text().strip() if self.var_table.item(row, 4) else ""
            desc = self.var_table.item(row, 5).text().strip() if self.var_table.item(row, 5) else ""
            var.name = name
            var.type = typ
            var.unit = unit
            var.default_value = default
            var.group = group
            var.description = desc
        else:
            row = item.row()
            name_item = self.var_table.item(row, 0)
            if name_item and name_item.text().strip():
                new_var = self._read_variable_row(row)
                if new_var:
                    self.defs.variables.append(new_var)
                    self.refresh_variables()

    def _read_variable_row(self, row) -> Optional[SystemVariable]:
        name = self.var_table.item(row, 0).text().strip() if self.var_table.item(row, 0) else ""
        if not name:
            return None
        typ = self.var_table.item(row, 1).text().strip() if self.var_table.item(row, 1) else ""
        unit = self.var_table.item(row, 2).text().strip() if self.var_table.item(row, 2) else ""
        default = self.var_table.item(row, 3).text().strip() if self.var_table.item(row, 3) else ""
        group = self.var_table.item(row, 4).text().strip() if self.var_table.item(row, 4) else ""
        desc = self.var_table.item(row, 5).text().strip() if self.var_table.item(row, 5) else ""
        return SystemVariable(name, typ, unit, default, group, desc)

    def add_empty_variable_row(self):
        current_row = self.var_table.currentRow()
        if current_row < 0:
            current_row = self.var_table.rowCount() - 2
        self.var_table.insertRow(current_row + 1)
        for col in range(6):
            if col == 1:
                item = QTableWidgetItem("uint16_t")
            else:
                item = QTableWidgetItem("")
            self.var_table.setItem(current_row + 1, col, item)

    def delete_variable(self):
        row = self.var_table.currentRow()
        if row < 0:
            return
        item = self.var_table.item(row, 0)
        if item:
            var = item.data(Qt.UserRole)
            if var:
                self.defs.variables.remove(var)
        self.var_table.removeRow(row)
        if self.var_table.rowCount() == 0 or self.var_table.item(self.var_table.rowCount()-1, 0).text() != "":
            self.refresh_variables()

    def bulk_variables(self):
        dlg = BulkVariableDialog(self, groups=self.defs.variable_groups())
        dlg.set_variables(self.defs.variables)
        if dlg.exec() == QDialog.Accepted:
            self.defs.variables = dlg.get_variables()
            self.refresh_variables()

    # ------------------------------------------------------------------
    # イベントフラグ
    # ------------------------------------------------------------------
    def refresh_flags(self):
        self._updating = True
        query = self.search_edit.text().strip().lower()
        self.flag_table.setRowCount(0)
        for flag in self.defs.flags:
            if self._matches(flag.name, flag.group, query):
                row = self.flag_table.rowCount()
                self.flag_table.insertRow(row)
                values = [flag.name, str(flag.min_value), str(flag.max_value),
                          str(flag.bit_width), flag.group, flag.description]
                for col, text in enumerate(values):
                    item = QTableWidgetItem(text)
                    if col == 3:
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setData(Qt.UserRole, flag)
                    self.flag_table.setItem(row, col, item)
        # 末尾に空行を追加
        self.flag_table.insertRow(self.flag_table.rowCount())
        for col in range(6):
            item = QTableWidgetItem("")
            if col == 3:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.flag_table.setItem(self.flag_table.rowCount() - 1, col, item)
        # グループ候補を更新
        self.flag_group_delegate.set_items(self.defs.flag_groups())
        self._updating = False

    def on_flag_item_changed(self, item):
        if self._updating:
            return
        flag = item.data(Qt.UserRole)
        if flag:
            row = item.row()
            name = self.flag_table.item(row, 0).text().strip() if self.flag_table.item(row, 0) else ""
            min_str = self.flag_table.item(row, 1).text().strip() if self.flag_table.item(row, 1) else "0"
            max_str = self.flag_table.item(row, 2).text().strip() if self.flag_table.item(row, 2) else "0"
            try:
                min_val = int(min_str)
                max_val = int(max_str)
            except ValueError:
                min_val, max_val = 0, 0
            group = self.flag_table.item(row, 4).text().strip() if self.flag_table.item(row, 4) else ""
            desc = self.flag_table.item(row, 5).text().strip() if self.flag_table.item(row, 5) else ""
            flag.name = name
            flag.min_value = min_val
            flag.max_value = max_val
            flag.group = group
            flag.description = desc
            width_item = self.flag_table.item(row, 3)
            if width_item:
                width_item.setText(str(flag.bit_width))
        else:
            row = item.row()
            name_item = self.flag_table.item(row, 0)
            if name_item and name_item.text().strip():
                new_flag = self._read_flag_row(row)
                if new_flag:
                    self.defs.flags.append(new_flag)
                    self.refresh_flags()

    def _read_flag_row(self, row) -> Optional[EventFlag]:
        name = self.flag_table.item(row, 0).text().strip() if self.flag_table.item(row, 0) else ""
        if not name:
            return None
        min_str = self.flag_table.item(row, 1).text().strip() if self.flag_table.item(row, 1) else "0"
        max_str = self.flag_table.item(row, 2).text().strip() if self.flag_table.item(row, 2) else "0"
        try:
            min_val = int(min_str)
            max_val = int(max_str)
        except ValueError:
            min_val, max_val = 0, 0
        group = self.flag_table.item(row, 4).text().strip() if self.flag_table.item(row, 4) else ""
        desc = self.flag_table.item(row, 5).text().strip() if self.flag_table.item(row, 5) else ""
        return EventFlag(name, min_val, max_val, group, desc)

    def add_empty_flag_row(self):
        current_row = self.flag_table.currentRow()
        if current_row < 0:
            current_row = self.flag_table.rowCount() - 2
        self.flag_table.insertRow(current_row + 1)
        for col in range(6):
            if col == 1:
                self.flag_table.setItem(current_row + 1, col, QTableWidgetItem("0"))
            elif col == 2:
                self.flag_table.setItem(current_row + 1, col, QTableWidgetItem("3"))
            elif col == 3:
                item = QTableWidgetItem("2")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.flag_table.setItem(current_row + 1, col, item)
            else:
                self.flag_table.setItem(current_row + 1, col, QTableWidgetItem(""))

    def delete_flag(self):
        row = self.flag_table.currentRow()
        if row < 0:
            return
        item = self.flag_table.item(row, 0)
        if item:
            flag = item.data(Qt.UserRole)
            if flag:
                self.defs.flags.remove(flag)
        self.flag_table.removeRow(row)
        if self.flag_table.rowCount() == 0 or self.flag_table.item(self.flag_table.rowCount()-1, 0).text() != "":
            self.refresh_flags()

    def bulk_flags(self):
        dlg = BulkFlagDialog(self, groups=self.defs.flag_groups())
        dlg.set_flags(self.defs.flags)
        if dlg.exec() == QDialog.Accepted:
            self.defs.flags = dlg.get_flags()
            self.refresh_flags()