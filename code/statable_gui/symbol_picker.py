from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QLabel
)
from PySide6.QtGui import QFont

from statable.global_defs import GlobalDefinitions
from .global_defs_dialog import VariableEditDialog, FlagEditDialog, GlobalDefinitionsDialog
from .logger import StaTableLogger


class SymbolPickerWidget(QWidget):
    """グローバル変数・イベントフラグ・ロール関数戻り値を選択する共通ウィジェット"""

    insert_requested = Signal(str)   # ダブルクリック時に挿入する文字列を通知

    def __init__(self, parent=None, global_defs=None, role_functions=None):
        super().__init__(parent)
        self.global_defs = global_defs if global_defs else GlobalDefinitions()
        self.role_functions = role_functions if role_functions is not None else {}

        layout = QVBoxLayout(self)

        # タイトル
        title = QLabel("グローバル変数・イベントフラグ・戻り値一覧")
        title.setFont(QFont("sans-serif", 10, QFont.Bold))
        layout.addWidget(title)

        # 検索
        search_label = QLabel("検索（前方一致）:")
        layout.addWidget(search_label)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("メンバ名・グループ名を入力")
        self.search_edit.textChanged.connect(self.refresh_list)
        layout.addWidget(self.search_edit)

        # 一覧
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.list_widget, stretch=1)

        # 登録ボタン
        btn_layout = QHBoxLayout()
        add_var_btn = QPushButton("変数登録...")
        add_var_btn.clicked.connect(self.register_variable)
        btn_layout.addWidget(add_var_btn)

        add_flag_btn = QPushButton("フラグ登録...")
        add_flag_btn.clicked.connect(self.register_flag)
        btn_layout.addWidget(add_flag_btn)
        layout.addLayout(btn_layout)

        # グローバル定義を開く
        open_defs_btn = QPushButton("グローバル定義を開く...")
        open_defs_btn.clicked.connect(self.open_global_definitions)
        layout.addWidget(open_defs_btn)

        self.refresh_list()
        StaTableLogger.debug("SymbolPickerWidget initialized")

    # ------------------------------------------------------------------
    # 一覧更新
    # ------------------------------------------------------------------
    def refresh_list(self):
        query = self.search_edit.text().strip().lower() if hasattr(self, 'search_edit') else ""
        StaTableLogger.debug(f"SymbolPickerWidget.refresh_list: query='{query}'")

        self.list_widget.clear()

        # グローバル変数
        for var in self.global_defs.variables:
            if self._matches(var.name, var.group, query):
                item = QListWidgetItem(f"変数: {var.name}")
                item.setData(Qt.UserRole, var.name)
                item.setToolTip(
                    f"種別: グローバル変数\n"
                    f"型: {var.type}\n"
                    f"単位: {var.unit}\n"
                    f"初期値: {var.default_value}\n"
                    f"グループ: {var.group}\n"
                    f"説明: {var.description}"
                )
                self.list_widget.addItem(item)

        # イベントフラグ
        for flag in self.global_defs.flags:
            if self._matches(flag.name, flag.group, query):
                item = QListWidgetItem(f"フラグ: {flag.name}")
                item.setData(Qt.UserRole, flag.name)
                item.setToolTip(
                    f"種別: イベントフラグ\n"
                    f"最小値: {flag.min_value}\n"
                    f"最大値: {flag.max_value}\n"
                    f"ビット幅: {flag.bit_width} bit\n"
                    f"グループ: {flag.group}\n"
                    f"説明: {flag.description}"
                )
                self.list_widget.addItem(item)

        # ロール関数戻り値（一時変数）
        for func_name in self.role_functions.keys():
            temp_var = f"rv_{func_name}"
            if self._matches(temp_var, "", query) or self._matches(func_name, "", query):
                item = QListWidgetItem(f"戻り値: {temp_var}")
                item.setData(Qt.UserRole, temp_var)
                item.setToolTip(
                    f"種別: ロール関数戻り値\n"
                    f"関数: {func_name}\n"
                    f"一時変数: {temp_var}"
                )
                self.list_widget.addItem(item)

        StaTableLogger.debug(f"SymbolPickerWidget: {self.list_widget.count()} items displayed")

    def _matches(self, name: str, group: str, query: str) -> bool:
        if not query:
            return True
        q = query.lower()
        return name.lower().startswith(q) or group.lower().startswith(q)

    # ------------------------------------------------------------------
    # ダブルクリック
    # ------------------------------------------------------------------
    def _on_item_double_clicked(self, item: QListWidgetItem):
        insertion_text = item.data(Qt.UserRole)
        StaTableLogger.debug(f"SymbolPickerWidget double-click: '{insertion_text}'")
        if insertion_text:
            self.insert_requested.emit(insertion_text)

    # ------------------------------------------------------------------
    # 登録
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