from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QComboBox,
    QPushButton, QLabel, QDialogButtonBox, QMessageBox, QLineEdit,
    QListWidget, QListWidgetItem, QSplitter, QWidget, QMenu
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from .role_function_dialog import RoleFunctionDialog
from .global_defs import GlobalDefinitions, SystemVariable, EventFlag
from .global_defs_dialog import GlobalDefinitionsDialog, VariableEditDialog, FlagEditDialog
from .logger import StaTableLogger


class ActionEditDialog(QDialog):
    """遷移の動作（ロール関数呼び出し・生コード）を編集するダイアログ"""

    def __init__(self, parent=None, action_text="", role_functions=None, global_defs=None):
        super().__init__(parent)
        self.setWindowTitle("動作編集")
        self.setMinimumSize(900, 650)
        self.role_functions = role_functions if role_functions is not None else {}
        self.global_defs = global_defs if global_defs else GlobalDefinitions()

        StaTableLogger.debug(
            f"ActionEditDialog.__init__: "
            f"action_text_len={len(action_text)}, "
            f"roles={len(self.role_functions)}, "
            f"vars={len(self.global_defs.variables)}, "
            f"flags={len(self.global_defs.flags)}"
        )

        main_layout = QVBoxLayout(self)

        # ★ 画面タイトル
        title_label = QLabel("動作編集")
        title_font = QFont("sans-serif", 14, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # ロール関数選択・挿入バー
        role_bar = QHBoxLayout()
        role_bar.addWidget(QLabel("ロール関数:"))
        self.role_combo = QComboBox()
        self.refresh_role_combo()
        role_bar.addWidget(self.role_combo)
        insert_role_btn = QPushButton("挿入")
        insert_role_btn.clicked.connect(self.insert_role_function)
        role_bar.addWidget(insert_role_btn)
        new_role_btn = QPushButton("新規ロール関数...")
        new_role_btn.clicked.connect(self.add_new_role_function)
        role_bar.addWidget(new_role_btn)
        main_layout.addLayout(role_bar)

        # シグネチャ表示
        self.signature_label = QLabel("")
        self.signature_label.setFont(QFont("Consolas", 9))
        self.signature_label.setStyleSheet("color: #555;")
        main_layout.addWidget(self.signature_label)

        # 左右分割
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 左側：検索＋定義一覧＋登録ボタン
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # ★ 一覧タイトル
        list_title_label = QLabel("グローバル変数・イベントフラグ一覧")
        list_title_font = QFont("sans-serif", 10, QFont.Bold)
        list_title_label.setFont(list_title_font)
        left_layout.addWidget(list_title_label)

        left_layout.addWidget(QLabel("検索（前方一致）:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("メンバ名・グループ名を入力")
        self.search_edit.textChanged.connect(self.on_search_text_changed)
        left_layout.addWidget(self.search_edit)

        # 一覧ボックス
        self.def_list = QListWidget()
        self.def_list.itemDoubleClicked.connect(self.insert_definition)
        left_layout.addWidget(self.def_list, stretch=1)

        # 登録ボタン
        reg_btn_layout = QHBoxLayout()
        add_var_btn = QPushButton("変数登録...")
        add_var_btn.clicked.connect(self.register_new_variable)
        reg_btn_layout.addWidget(add_var_btn)

        add_flag_btn = QPushButton("フラグ登録...")
        add_flag_btn.clicked.connect(self.register_new_flag)
        reg_btn_layout.addWidget(add_flag_btn)
        left_layout.addLayout(reg_btn_layout)

        # グローバル定義を開くボタン
        open_defs_btn = QPushButton("グローバル定義を開く...")
        open_defs_btn.clicked.connect(self.open_global_definitions)
        left_layout.addWidget(open_defs_btn)

        splitter.addWidget(left_widget)

        # 右側：動作コード編集
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("動作コード:"))
        self.action_edit = QTextEdit()
        self.action_edit.setAcceptRichText(False)
        self.action_edit.setPlainText(action_text)
        self.action_edit.setFont(QFont("Consolas", 10))
        # コンテキストメニュー（選択文字列から登録）
        self.action_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.action_edit.customContextMenuRequested.connect(self.show_action_context_menu)
        right_layout.addWidget(self.action_edit, stretch=1)
        splitter.addWidget(right_widget)

        # OK/Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        # 初期表示：全件表示
        self.refresh_def_list()
        self.update_signature_label()

        StaTableLogger.debug("ActionEditDialog.__init__ completed")

    # ------------------------------------------------------------------
    # ロール関数
    # ------------------------------------------------------------------
    def refresh_role_combo(self):
        """ロール関数コンボボックスを更新"""
        self.role_combo.clear()
        for name in self.role_functions.keys():
            self.role_combo.addItem(name)
        try:
            self.role_combo.currentTextChanged.disconnect(self.update_signature_label)
        except (RuntimeError, TypeError):
            pass
        self.role_combo.currentTextChanged.connect(self.update_signature_label)
        StaTableLogger.debug(f"refresh_role_combo: {len(self.role_functions)} roles")

    def update_signature_label(self):
        """選択中のロール関数のシグネチャを表示"""
        func_name = self.role_combo.currentText()
        if func_name:
            rf = self.role_functions.get(func_name)
            if rf:
                sig = (
                    f"{rf.return_type} {rf.name}("
                    f"{rf.arg1_type} {rf.arg1_name}, "
                    f"{rf.arg2_type} {rf.arg2_name})"
                )
                self.signature_label.setText(sig)
                return
        self.signature_label.setText("")

    def insert_role_function(self):
        """選択中のロール関数を動作コードへ挿入"""
        func_name = self.role_combo.currentText()
        StaTableLogger.debug(f"insert_role_function: '{func_name}'")
        if not func_name:
            return
        rf = self.role_functions.get(func_name)
        if not rf:
            return
        call = f"{func_name}({rf.arg1_name}, {rf.arg2_name});"
        self.action_edit.insertPlainText(call + "\n")
        StaTableLogger.debug(f"  inserted: {call}")

    def add_new_role_function(self):
        """新しいロール関数を登録"""
        StaTableLogger.debug("add_new_role_function called")
        dlg = RoleFunctionDialog(self)
        if dlg.exec() == QDialog.Accepted:
            rf = dlg.get_role_function()
            if rf.name in self.role_functions:
                QMessageBox.warning(self, "警告", "同名のロール関数が既に存在します。")
                return
            self.role_functions[rf.name] = rf
            self.refresh_role_combo()
            self.update_signature_label()
            StaTableLogger.debug(f"  new role added: {rf.name}")

    # ------------------------------------------------------------------
    # グローバル定義画面を開く
    # ------------------------------------------------------------------
    def open_global_definitions(self):
        """グローバル変数・イベントフラグ定義画面を開く"""
        StaTableLogger.debug("open_global_definitions called")
        dlg = GlobalDefinitionsDialog(self.global_defs, self)
        dlg.exec()
        # 定義画面で編集された内容を一覧に反映
        self.refresh_def_list()
        StaTableLogger.debug("  GlobalDefinitionsDialog closed, list refreshed")

    # ------------------------------------------------------------------
    # グローバル変数・イベントフラグ登録
    # ------------------------------------------------------------------
    def register_new_variable(self):
        """新しいグローバル変数を登録"""
        StaTableLogger.debug("register_new_variable called")
        dlg = VariableEditDialog(self, groups=self.global_defs.variable_groups())
        if dlg.exec() == QDialog.Accepted:
            var = dlg.get_variable()
            if not var.name:
                QMessageBox.warning(self, "警告", "名前を入力してください。")
                return
            if any(v.name == var.name for v in self.global_defs.variables):
                QMessageBox.warning(self, "警告", f"変数 '{var.name}' は既に存在します。")
                return
            self.global_defs.variables.append(var)
            self.refresh_def_list()
            StaTableLogger.debug(f"  registered variable: {var.name}")

    def register_new_flag(self):
        """新しいイベントフラグを登録"""
        StaTableLogger.debug("register_new_flag called")
        dlg = FlagEditDialog(self, groups=self.global_defs.flag_groups())
        if dlg.exec() == QDialog.Accepted:
            flag = dlg.get_flag()
            if not flag.name:
                QMessageBox.warning(self, "警告", "フラグ名を入力してください。")
                return
            if any(f.name == flag.name for f in self.global_defs.flags):
                QMessageBox.warning(self, "警告", f"フラグ '{flag.name}' は既に存在します。")
                return
            self.global_defs.flags.append(flag)
            self.refresh_def_list()
            StaTableLogger.debug(f"  registered flag: {flag.name}")

    def show_action_context_menu(self, pos):
        """動作コードの選択文字列から登録するメニュー"""
        selected_text = self.action_edit.textCursor().selectedText().strip()
        if not selected_text:
            return

        menu = QMenu(self)
        add_var_action = menu.addAction(f"'{selected_text}' をグローバル変数として登録")
        add_flag_action = menu.addAction(f"'{selected_text}' をイベントフラグとして登録")
        chosen = menu.exec(self.action_edit.viewport().mapToGlobal(pos))

        if chosen == add_var_action:
            self.register_selected_as_variable(selected_text)
        elif chosen == add_flag_action:
            self.register_selected_as_flag(selected_text)

    def register_selected_as_variable(self, name: str):
        """選択文字列を名前としてグローバル変数登録ダイアログを開く"""
        StaTableLogger.debug(f"register_selected_as_variable: '{name}'")
        dlg = VariableEditDialog(self, groups=self.global_defs.variable_groups())
        dlg.name_edit.setText(name)
        if dlg.exec() == QDialog.Accepted:
            var = dlg.get_variable()
            if not var.name:
                QMessageBox.warning(self, "警告", "名前を入力してください。")
                return
            if any(v.name == var.name for v in self.global_defs.variables):
                QMessageBox.warning(self, "警告", f"変数 '{var.name}' は既に存在します。")
                return
            self.global_defs.variables.append(var)
            self.refresh_def_list()
            StaTableLogger.debug(f"  registered variable: {var.name}")

    def register_selected_as_flag(self, name: str):
        """選択文字列を名前としてイベントフラグ登録ダイアログを開く"""
        StaTableLogger.debug(f"register_selected_as_flag: '{name}'")
        dlg = FlagEditDialog(self, groups=self.global_defs.flag_groups())
        dlg.name_edit.setText(name)
        if dlg.exec() == QDialog.Accepted:
            flag = dlg.get_flag()
            if not flag.name:
                QMessageBox.warning(self, "警告", "フラグ名を入力してください。")
                return
            if any(f.name == flag.name for f in self.global_defs.flags):
                QMessageBox.warning(self, "警告", f"フラグ '{flag.name}' は既に存在します。")
                return
            self.global_defs.flags.append(flag)
            self.refresh_def_list()
            StaTableLogger.debug(f"  registered flag: {flag.name}")

    # ------------------------------------------------------------------
    # 定義一覧（検索・絞り込み）
    # ------------------------------------------------------------------
    def on_search_text_changed(self, text: str):
        """検索文字列が変更されたら一覧を更新"""
        StaTableLogger.debug(f"on_search_text_changed: '{text}'")
        self.refresh_def_list()

    def refresh_def_list(self):
        """グローバル変数・イベントフラグの一覧を更新（初期表示は全件）"""
        query = self.search_edit.text().strip().lower() if hasattr(self, 'search_edit') else ""
        StaTableLogger.debug(f"refresh_def_list: query='{query}'")

        self.def_list.clear()

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
                self.def_list.addItem(item)

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
                self.def_list.addItem(item)

        StaTableLogger.debug(f"  displayed {self.def_list.count()} items")

    def _matches(self, name: str, group: str, query: str) -> bool:
        """前方一致検索"""
        if not query:
            return True
        q = query.lower()
        return name.lower().startswith(q) or group.lower().startswith(q)

    def insert_definition(self, item: QListWidgetItem):
        """一覧の項目をダブルクリックで動作コードへ挿入"""
        name = item.data(Qt.UserRole)
        StaTableLogger.debug(f"insert_definition: '{name}'")
        if name:
            self.action_edit.insertPlainText(name)

    def get_action_text(self) -> str:
        """編集された動作コードを返す"""
        text = self.action_edit.toPlainText().strip()
        StaTableLogger.debug(f"get_action_text: length={len(text)}")
        return text