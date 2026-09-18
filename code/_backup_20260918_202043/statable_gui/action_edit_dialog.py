from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QComboBox,
    QPushButton, QLabel, QDialogButtonBox, QMessageBox,
    QSplitter, QWidget, QMenu
)

from .role_function_dialog import RoleFunctionDialog
from .global_defs import GlobalDefinitions
from .global_defs_dialog import VariableEditDialog, FlagEditDialog
from .common_widgets import TitleEditWidget
from .symbol_picker import SymbolPickerWidget
from .logger import StaTableLogger


class ActionEditDialog(QDialog):
    """遷移の動作を編集するダイアログ（H3: qualified_name 挿入対応）"""

    def __init__(self, parent=None, action_text="", title="",
                 role_functions=None, global_defs=None):
        super().__init__(parent)
        self.setWindowTitle("動作編集")
        self.setMinimumSize(900, 650)
        self.role_functions = role_functions if role_functions is not None else {}
        self.global_defs = global_defs if global_defs else GlobalDefinitions()

        StaTableLogger.debug(
            f"ActionEditDialog.__init__: action_text_len={len(action_text)}, "
            f"title='{title}', roles={len(self.role_functions)}, "
            f"vars={len(self.global_defs.variables)}, "
            f"flags={len(self.global_defs.flags)}"
        )

        main_layout = QVBoxLayout(self)

        self.title_widget = TitleEditWidget(self, title=title)
        main_layout.addWidget(self.title_widget)

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

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        self.symbol_picker = SymbolPickerWidget(
            global_defs=self.global_defs,
            role_functions=self.role_functions
        )
        self.symbol_picker.insert_requested.connect(self.insert_symbol)
        splitter.addWidget(self.symbol_picker)

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

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        self.update_signature_label()
        StaTableLogger.debug("ActionEditDialog.__init__ completed")

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
                # ★ qualified_name を優先表示
                display = getattr(rf, 'qualified_name', rf.name)
                arg1 = getattr(rf, 'arg1_type', '') or ''
                arg1n = getattr(rf, 'arg1_name', '') or ''
                arg2 = getattr(rf, 'arg2_type', '') or ''
                arg2n = getattr(rf, 'arg2_name', '') or ''
                ret = getattr(rf, 'return_type', 'void') or 'void'
                sig = f"{ret} {display}({arg1} {arg1n}, {arg2} {arg2n})"
                self.signature_label.setText(sig)
                return
        self.signature_label.setText("")

    # ★ 変更: qualified_name を使用
    def insert_role_function(self):
        """
        ロール関数を動作欄に挿入

        - namespace あり: "Driver.Init" の参照形式（引数なし）
        - namespace なし: 旧形式 "Sensor_Init(arg1, arg2);" を維持
        """
        func_name = self.role_combo.currentText()
        StaTableLogger.debug(f"insert_role_function: '{func_name}'")
        if not func_name:
            return
        rf = self.role_functions.get(func_name)
        if not rf:
            return

        qualified = getattr(rf, 'qualified_name', func_name)

        if '.' in qualified:
            # ★ Namespace.Name 形式: 参照のみ挿入
            call = qualified
        else:
            # ★ 旧形式: 引数付き呼び出しを維持
            arg1 = getattr(rf, 'arg1_name', '') or ''
            arg2 = getattr(rf, 'arg2_name', '') or ''
            call = f"{qualified}({arg1}, {arg2});"

        self.action_edit.insertPlainText(call + "\n")

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

    def insert_symbol(self, text: str):
        self.action_edit.insertPlainText(text)

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
        dlg = VariableEditDialog(self, groups=self.global_defs.variable_groups())
        dlg.name_edit.setText(name)
        if dlg.exec() == QDialog.Accepted:
            var = dlg.get_variable()
            if not var.name:
                return
            if any(v.name == var.name for v in self.global_defs.variables):
                return
            self.global_defs.variables.append(var)
            self.symbol_picker.refresh_list()

    def register_selected_as_flag(self, name: str):
        dlg = FlagEditDialog(self, groups=self.global_defs.flag_groups())
        dlg.name_edit.setText(name)
        if dlg.exec() == QDialog.Accepted:
            flag = dlg.get_flag()
            if not flag.name:
                return
            if any(f.name == flag.name for f in self.global_defs.flags):
                return
            self.global_defs.flags.append(flag)
            self.symbol_picker.refresh_list()

    def _on_accept(self):
        action_text = self.action_edit.toPlainText().strip()
        if action_text:
            first_line = action_text.split('\n')[0].strip()
            auto_title = first_line[:20] + ("..." if len(first_line) > 20 else "")
        else:
            auto_title = "(無題動作)"
        self.title_widget.ensure_title(auto_title)
        self.accept()

    def get_action_text(self) -> str:
        return self.action_edit.toPlainText().strip()

    def get_title(self) -> str:
        return self.title_widget.get_title()