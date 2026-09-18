from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QLabel, QDialog
)
from PySide6.QtGui import QFont

from statable.global_defs import GlobalDefinitions
from .global_defs_dialog import VariableEditDialog, FlagEditDialog, GlobalDefinitionsDialog
from .logger import StaTableLogger


class SymbolPickerWidget(QWidget):
    """Common widget for selecting global variables, event flags, and role function return values"""

    insert_requested = Signal(str)

    def __init__(self, parent=None, global_defs=None, role_functions=None):
        super().__init__(parent)
        self.global_defs = global_defs if global_defs else GlobalDefinitions()
        self.role_functions = role_functions if role_functions is not None else {}

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Global variables・Event flags・戻りValue一覧")
        title.setFont(QFont("sans-serif", 10, QFont.Bold))
        layout.addWidget(title)

        # Search
        search_label = QLabel("Search (prefix match):")
        layout.addWidget(search_label)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Title・Member name・Group名を入力")
        self.search_edit.textChanged.connect(self.refresh_list)
        layout.addWidget(self.search_edit)

        # List
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.list_widget, stretch=1)

        # Register button
        btn_layout = QHBoxLayout()
        add_var_btn = QPushButton("Register variable...")
        add_var_btn.clicked.connect(self.register_variable)
        btn_layout.addWidget(add_var_btn)

        add_flag_btn = QPushButton("Register flag...")
        add_flag_btn.clicked.connect(self.register_flag)
        btn_layout.addWidget(add_flag_btn)
        layout.addLayout(btn_layout)

        # Open global definitions
        open_defs_btn = QPushButton("Open global definitions...")
        open_defs_btn.clicked.connect(self.open_global_definitions)
        layout.addWidget(open_defs_btn)

        self.refresh_list()
        StaTableLogger.debug("SymbolPickerWidget initialized")

    # ------------------------------------------------------------------
    # Refresh list
    # ------------------------------------------------------------------
    def refresh_list(self):
        query = self.search_edit.text().strip().lower() if hasattr(self, 'search_edit') else ""
        StaTableLogger.debug(f"SymbolPickerWidget.refresh_list: query='{query}'")

        self.list_widget.clear()

        # Global variables
        for var in self.global_defs.variables:
            if self._matches(var.title, var.name, var.group, query):
                item = QListWidgetItem(f"変数: {var.title}")
                item.setData(Qt.UserRole, var.name)
                item.setToolTip(
                    f"種別: グローバル変数\n"
                    f"タイトル: {var.title}\n"
                    f"名前: {var.name}\n"
                    f"型: {var.type}\n"
                    f"単位: {var.unit}\n"
                    f"初期値: {var.default_value}\n"
                    f"グループ: {var.group}\n"
                    f"説明: {var.description}"
                )
                self.list_widget.addItem(item)

        # Event flags
        for flag in self.global_defs.flags:
            if self._matches(flag.title, flag.name, flag.group, query):
                item = QListWidgetItem(f"フラグ: {flag.title}")
                item.setData(Qt.UserRole, flag.name)
                item.setToolTip(
                    f"種別: イベントフラグ\n"
                    f"タイトル: {flag.title}\n"
                    f"名前: {flag.name}\n"
                    f"最小値: {flag.min_value}\n"
                    f"最大値: {flag.max_value}\n"
                    f"ビット幅: {flag.bit_width} bit\n"
                    f"グループ: {flag.group}\n"
                    f"説明: {flag.description}"
                )
                self.list_widget.addItem(item)

        # Role function戻りValue（一時Variable）
        for func_name in self.role_functions.keys():
            temp_var = f"rv_{func_name}"
            if self._matches(temp_var, func_name, "", query):
                item = QListWidgetItem(f"戻り値: {temp_var}")
                item.setData(Qt.UserRole, temp_var)
                item.setToolTip(
                    f"種別: ロール関数戻り値\n"
                    f"関数: {func_name}\n"
                    f"一時変数: {temp_var}"
                )
                self.list_widget.addItem(item)

        StaTableLogger.debug(f"SymbolPickerWidget: {self.list_widget.count()} items displayed")

    def _matches(self, title: str, name: str, group: str, query: str) -> bool:
        if not query:
            return True
        q = query.lower()
        return (
            title.lower().startswith(q) or
            name.lower().startswith(q) or
            group.lower().startswith(q)
        )

    # ------------------------------------------------------------------
    # Double-click
    # ------------------------------------------------------------------
    def _on_item_double_clicked(self, item: QListWidgetItem):
        insertion_text = item.data(Qt.UserRole)
        StaTableLogger.debug(f"SymbolPickerWidget double-click: '{insertion_text}'")
        if insertion_text:
            self.insert_requested.emit(insertion_text)

    # ------------------------------------------------------------------
    # Register
    # ------------------------------------------------------------------
    def register_variable(self):
        StaTableLogger.debug("SymbolPickerWidget.register_variable called")
        dlg = VariableEditDialog(self, groups=self.global_defs.variable_groups())
        if dlg.exec() == QDialog.Accepted:
            var = dlg.get_variable()
            if not var.name:
                return
            if any(v.name == var.name for v in self.global_defs.variables):
                return
            self.global_defs.variables.append(var)
            self.refresh_list()

    def register_flag(self):
        StaTableLogger.debug("SymbolPickerWidget.register_flag called")
        dlg = FlagEditDialog(self, groups=self.global_defs.flag_groups())
        if dlg.exec() == QDialog.Accepted:
            flag = dlg.get_flag()
            if not flag.name:
                return
            if any(f.name == flag.name for f in self.global_defs.flags):
                return
            self.global_defs.flags.append(flag)
            self.refresh_list()

    def open_global_definitions(self):
        StaTableLogger.debug("SymbolPickerWidget.open_global_definitions called")
        dlg = GlobalDefinitionsDialog(self.global_defs, self)
        dlg.exec()
        self.refresh_list()