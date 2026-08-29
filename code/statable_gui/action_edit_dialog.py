from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QComboBox, QLineEdit,
    QPushButton, QLabel, QDialogButtonBox, QMessageBox,
    QSplitter, QWidget, QMenu
)

from .role_function_dialog import RoleFunctionDialog
from .global_defs import GlobalDefinitions
from .global_defs_dialog import VariableEditDialog, FlagEditDialog
from .symbol_picker import SymbolPickerWidget
from .logger import StaTableLogger


class ActionEditDialog(QDialog):
    """遷移の動作（ロール関数呼び出し・生コード）を編集するダイアログ"""

    def __init__(self, parent=None, action_text="", title="", role_functions=None, global_defs=None):
        super().__init__(parent)
        self.setWindowTitle("動作編集")
        self.setMinimumSize(900, 650)
        self.role_functions = role_functions if role_functions is not None else {}
        self.global_defs = global_defs if global_defs else GlobalDefinitions()

        StaTableLogger.debug(
            f"ActionEditDialog.__init__: action_text_len={len(action_text)}, "
            f"title='{title}', roles={len(self.role_functions)}, "
            f"vars={len(self.global_defs.variables)}, flags={len(self.global_defs.flags)}"
        )

        main_layout = QVBoxLayout(self)

        # タイトル入力欄（必須・仮タイトル自動設定）
        title_layout = QHBoxLayout()
        title_label = QLabel("タイトル *")
        title_label.setFont(QFont("sans-serif", 10, QFont.Bold))
        self.title_edit = QLineEdit()
        self.title_edit.setText(title)
        self.title_edit.setPlaceholderText("一覧に表示されるラベル（空なら自動設定）")
        self.title_edit.setToolTip("この動作のタイトルを入力してください。空の場合は自動で仮タイトルが設定されます。")
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_edit, stretch=1)
        main_layout.addLayout(title_layout)

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

        self.signature_label = QLabel("")
        self.signature_label.setFont(QFont("Consolas", 9))
        self.signature_label.setStyleSheet("color: #555;")
        main_layout.addWidget(self.signature_label)

        # 左右分割
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 左側：シンボルピッカー
        self.symbol_picker = SymbolPickerWidget(
            global_defs=self.global_defs,
            role_functions=self.role_functions
        )
        self.symbol_picker.insert_requested.connect(self.insert_symbol)
        splitter.addWidget(self.symbol_picker)

        # 右側：動作コード編集
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("動作コード:"))
        self.action_edit = QTextEdit()
        self.action_edit.setAcceptRichText(False)
        self.action_edit.setPlainText(action_text)
        self.action_edit.setFont(QFont("Consolas", 10))
        self.action_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.action_edit.customContextMenuRequested.connect(self.show_action_context_menu)
        right_layout.addWidget(self.action_edit, stretch=1)
        splitter.addWidget(right_widget)

        # OK/Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        self.update_signature_label()
        StaTableLogger.debug("ActionEditDialog.__init__ completed")

    # ------------------------------------------------------------------
    # ロール関数
    # ------------------------------------------------------------------
    def refresh_role_combo(self):
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
    # シンボル挿入
    # ------------------------------------------------------------------
    def insert_symbol(self, text: str):
        StaTableLogger.debug(f"ActionEditDialog.insert_symbol: '{text}'")
        self.action_edit.insertPlainText(text)

    # ------------------------------------------------------------------
    # コンテキストメニュー（選択文字列から登録）
    # ------------------------------------------------------------------
    def show_action_context_menu(self, pos):
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
            self.symbol_picker.refresh_list()

    def register_selected_as_flag(self, name: str):
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
            self.symbol_picker.refresh_list()

    def _on_accept(self):
        """OKボタン：タイトルが空なら仮タイトルを自動設定"""
        if not self.title_edit.text().strip():
            action_text = self.action_edit.toPlainText().strip()
            if action_text:
                first_line = action_text.split('\n')[0].strip()
                auto_title = first_line[:20] + ("..." if len(first_line) > 20 else "")
            else:
                auto_title = "(無題動作)"
            self.title_edit.setText(auto_title)
            StaTableLogger.debug(f"Auto title generated: '{auto_title}'")
        self.accept()

    def get_action_text(self) -> str:
        text = self.action_edit.toPlainText().strip()
        StaTableLogger.debug(f"get_action_text: length={len(text)}")
        return text

    def get_title(self) -> str:
        title = self.title_edit.text().strip()
        StaTableLogger.debug(f"get_title: '{title}'")
        return title