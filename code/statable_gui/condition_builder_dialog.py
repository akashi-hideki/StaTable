# statable_gui/condition_builder_dialog.py
"""
遷移条件ビルダーダイアログ（リテラル化対応・イベント名編集欄追加）
"""

import re
import sys
import os

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QTreeWidget,
    QTreeWidgetItem, QLabel, QLineEdit, QPushButton, QDialogButtonBox,
    QSplitter, QGroupBox, QFrame, QSizePolicy, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics

from statable.global_defs import GlobalDefinitions
from statable.state_machine import StateMachine

# 共有リテラルライブラリ
try:
    from libcntrl.literal_library import LiteralLibrary, LiteralDefinition
except ImportError:
    from statable_gui.libcntrl.literal_library import LiteralLibrary, LiteralDefinition


class ConditionBuilderDialog(QDialog):
    """遷移条件式をGUIで構築するダイアログ"""

    def __init__(self, condition: str = "", event_name: str = "",
                 global_defs: GlobalDefinitions = None,
                 state_machine: StateMachine = None,
                 literal_library: LiteralLibrary = None,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("遷移条件ビルダー")
        self.setMinimumSize(1000, 700)

        self.global_defs = global_defs if global_defs else GlobalDefinitions()
        self.state_machine = state_machine if state_machine else StateMachine()
        self.literal_library = literal_library if literal_library else LiteralLibrary()
        self.event_name = event_name

        self._setup_ui()
        self.condition_edit.setPlainText(condition)
        self.event_name_edit.setText(event_name)
        self._populate_tree()
        self._update_c_code_view()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # イベント名編集欄
        event_layout = QHBoxLayout()
        event_layout.addWidget(QLabel("イベント名:"))
        self.event_name_edit = QLineEdit()
        event_layout.addWidget(self.event_name_edit)
        main_layout.addLayout(event_layout)

        main_splitter = QSplitter(Qt.Horizontal)

        # 左ペイン
        left_widget = QGroupBox("挿入するシンボル")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(4, 4, 4, 4)
        left_layout.setSpacing(2)

        self.symbol_tree = QTreeWidget()
        self.symbol_tree.setHeaderHidden(True)
        self.symbol_tree.itemDoubleClicked.connect(self._insert_symbol)
        left_layout.addWidget(self.symbol_tree)

        num_layout = QHBoxLayout()
        self.num_input = QLineEdit()
        self.num_input.setPlaceholderText("数値リテラル")
        num_insert_btn = QPushButton("挿入")
        num_insert_btn.clicked.connect(self._insert_number)
        num_layout.addWidget(self.num_input)
        num_layout.addWidget(num_insert_btn)
        left_layout.addLayout(num_layout)

        main_splitter.addWidget(left_widget)

        # 右ペイン
        right_widget = QGroupBox("条件式（シンボル名で記述）")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(4, 4, 4, 4)
        right_layout.setSpacing(2)

        # リテラル化ボタン
        literal_btn = QPushButton("リテラル化")
        literal_btn.clicked.connect(self._open_literalization)
        right_layout.addWidget(literal_btn, alignment=Qt.AlignLeft)

        self.condition_edit = QPlainTextEdit()
        self.condition_edit.setPlaceholderText("例: battery_voltage > 3000")
        self.condition_edit.setFrameStyle(QFrame.NoFrame)
        self.condition_edit.setStyleSheet("QPlainTextEdit { padding: 0px; color: black; background: white; }")
        self.condition_edit.document().setDocumentMargin(0)
        self.condition_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        fm = QFontMetrics(self.condition_edit.font())
        row_height = fm.height()
        self.condition_edit.setMinimumHeight(row_height * 10 + 4)
        self.condition_edit.textChanged.connect(self._update_c_code_view)
        right_layout.addWidget(self.condition_edit, 1)

        # クリアボタン
        clear_btn = QPushButton("クリア")
        clear_btn.clicked.connect(self._clear_condition)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(clear_btn)
        right_layout.addLayout(btn_layout)

        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([300, 700])
        main_layout.addWidget(main_splitter)

        # 下部：ctx->形式のCコード表示
        bottom_widget = QGroupBox("生成されるCコード（ctx->形式）")
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(4, 4, 4, 4)
        bottom_layout.setSpacing(2)

        self.c_code_view = QPlainTextEdit()
        self.c_code_view.setReadOnly(True)
        self.c_code_view.setFrameStyle(QFrame.NoFrame)
        self.c_code_view.setStyleSheet("QPlainTextEdit { padding: 0px; color: black; background: #f5f5f5; }")
        self.c_code_view.document().setDocumentMargin(0)
        self.c_code_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.c_code_view.setFixedHeight(row_height * 2 + 4)
        bottom_layout.addWidget(self.c_code_view, 1)
        main_layout.addWidget(bottom_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def _populate_tree(self):
        """利用可能なシンボルをカテゴリ別にツリーへ追加"""
        self.symbol_tree.clear()

        # グローバル変数
        global_vars_item = QTreeWidgetItem(["グローバル変数"])
        for var in getattr(self.global_defs, 'variables', []):
            child = QTreeWidgetItem([var.name])
            child.setData(0, Qt.UserRole, var.name)
            child.setToolTip(0, getattr(var, 'description', ''))
            global_vars_item.addChild(child)
        self.symbol_tree.addTopLevelItem(global_vars_item)

        # イベントフラグ
        flags_item = QTreeWidgetItem(["イベントフラグ"])
        for flag in getattr(self.global_defs, 'flags', []):
            child = QTreeWidgetItem([flag.name])
            child.setData(0, Qt.UserRole, flag.name)
            child.setToolTip(0, getattr(flag, 'description', ''))
            flags_item.addChild(child)
        self.symbol_tree.addTopLevelItem(flags_item)

        # イベント変数
        event_vars_item = QTreeWidgetItem(["イベント変数"])
        for event in self.state_machine.events.values():
            data_name = getattr(event, 'data_name', '')
            if data_name:
                symbol = f"event.{data_name}"
                child = QTreeWidgetItem([symbol])
                child.setData(0, Qt.UserRole, symbol)
                child.setToolTip(0, getattr(event, 'description', ''))
                event_vars_item.addChild(child)
        self.symbol_tree.addTopLevelItem(event_vars_item)

        # ロール関数（bool）
        role_funcs_item = QTreeWidgetItem(["ロール関数（bool）"])
        for rf in self.state_machine.role_functions.values():
            if getattr(rf, 'return_type', '') == 'bool':
                symbol = f"RoleFunc_{rf.name}(...)"
                child = QTreeWidgetItem([symbol])
                child.setData(0, Qt.UserRole, symbol)
                role_funcs_item.addChild(child)
        self.symbol_tree.addTopLevelItem(role_funcs_item)

        # リテラル
        literal_item = QTreeWidgetItem(["リテラル"])
        for lit in self.literal_library.list_all():
            child = QTreeWidgetItem([lit.name])
            child.setData(0, Qt.UserRole, lit.name)
            child.setToolTip(0, f"{lit.name} = {lit.value} ({lit.literal_type})")
            literal_item.addChild(child)
        self.symbol_tree.addTopLevelItem(literal_item)

        # 定数シンボル
        const_item = QTreeWidgetItem(["定数シンボル"])
        true_child = QTreeWidgetItem(["true"])
        true_child.setData(0, Qt.UserRole, "true")
        false_child = QTreeWidgetItem(["false"])
        false_child.setData(0, Qt.UserRole, "false")
        const_item.addChild(true_child)
        const_item.addChild(false_child)
        self.symbol_tree.addTopLevelItem(const_item)

        self.symbol_tree.expandAll()

    def _insert_symbol(self, item, column):
        symbol = item.data(0, Qt.UserRole)
        if symbol:
            self._insert_text(symbol)

    def _insert_text(self, text: str):
        cursor = self.condition_edit.textCursor()
        cursor.insertText(text)
        self.condition_edit.setTextCursor(cursor)
        self.condition_edit.setFocus()
        self._update_c_code_view()

    def _insert_number(self):
        num = self.num_input.text().strip()
        if num:
            self._insert_text(num)

    def _clear_condition(self):
        self.condition_edit.clear()
        self._update_c_code_view()

    def _update_c_code_view(self):
        raw_text = self.condition_edit.toPlainText()
        c_code = self._convert_to_c_code(raw_text)
        self.c_code_view.setPlainText(c_code)

    def _convert_to_c_code(self, text: str) -> str:
        replace_map = {}
        for var in getattr(self.global_defs, 'variables', []):
            replace_map[var.name] = f"ctx->data.{var.name}"
        for flag in getattr(self.global_defs, 'flags', []):
            replace_map[flag.name] = f"ctx->flags.{flag.name}"
        result = text
        for symbol in sorted(replace_map.keys(), key=len, reverse=True):
            result = result.replace(symbol, replace_map[symbol])
        result = self._add_parentheses_to_comparisons(result)
        return result

    def _add_parentheses_to_comparisons(self, text: str) -> str:
        text = text.replace('\n', ' ')
        parts = []
        depth = 0
        start = 0
        i = 0
        while i < len(text):
            ch = text[i]
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth = max(0, depth - 1)
            elif depth == 0 and i + 1 < len(text) and text[i:i+2] in ('&&', '||'):
                part = text[start:i].strip()
                if part:
                    parts.append(part)
                parts.append(text[i:i+2])
                i += 2
                start = i
                continue
            i += 1
        last_part = text[start:].strip()
        if last_part:
            parts.append(last_part)

        result_parts = []
        for part in parts:
            if part in ('&&', '||'):
                result_parts.append(f" {part} ")
            else:
                if re.search(r'==|!=|>=|<=|>|<', part):
                    if not self._is_fully_parenthesized(part):
                        part = f"({part})"
                result_parts.append(part)
        return ''.join(result_parts).strip()

    def _is_fully_parenthesized(self, expr: str) -> bool:
        expr = expr.strip()
        if not (expr.startswith('(') and expr.endswith(')')):
            return False
        depth = 0
        for i, ch in enumerate(expr):
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    return i == len(expr) - 1
            if depth < 0:
                return False
        return False

    def _open_literalization(self):
        text = self.condition_edit.toPlainText()
        if not text.strip():
            QMessageBox.information(self, "情報", "条件式が入力されていません。")
            return

        dialog = LiteralizationDialog(text, self.literal_library, self)
        if dialog.exec() == QDialog.Accepted:
            new_text = dialog.get_updated_condition_text()
            self.condition_edit.setPlainText(new_text)
            self._populate_tree()
            self._update_c_code_view()

    def get_condition_text(self) -> str:
        return self.condition_edit.toPlainText().strip()

    def get_event_name(self) -> str:
        return self.event_name_edit.text().strip()

    def get_c_code_text(self) -> str:
        return self.c_code_view.toPlainText().strip()


class LiteralizationDialog(QDialog):
    """条件式中の数値をリテラル化するダイアログ"""

    def __init__(self, condition_text: str, literal_library: LiteralLibrary, parent=None):
        super().__init__(parent)
        self.condition_text = condition_text
        self.literal_library = literal_library
        self.updated_condition_text = condition_text

        self.setWindowTitle("リテラル化")
        self.setMinimumSize(600, 400)

        self._setup_ui()
        self._scan_numbers()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("条件式中の数値をリテラル化します。各行の数値に名前を付けてください。"))

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["行", "数値", "リテラル名"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _scan_numbers(self):
        lines = self.condition_text.splitlines()
        for line_no, line in enumerate(lines):
            for match in re.finditer(r'\b\d+(\.\d+)?\b', line):
                value = match.group()
                self.table.insertRow(self.table.rowCount())
                row = self.table.rowCount() - 1
                self.table.setItem(row, 0, QTableWidgetItem(str(line_no + 1)))
                self.table.setItem(row, 1, QTableWidgetItem(value))
                self.table.setItem(row, 2, QTableWidgetItem(f"LITERAL_{row + 1}"))

    def _on_accept(self):
        replace_map = {}
        for row in range(self.table.rowCount()):
            line_no = self.table.item(row, 0).text().strip()
            value = self.table.item(row, 1).text().strip()
            literal_name = self.table.item(row, 2).text().strip()

            if not literal_name:
                continue

            try:
                lit = LiteralDefinition(name=literal_name, value=value, literal_type="int")
                self.literal_library.add(lit)
            except ValueError:
                pass

            replace_map[(line_no, value)] = literal_name

        lines = self.condition_text.splitlines()
        updated_lines = []
        for line_no, line in enumerate(lines):
            updated_line = line
            for (target_line, value), literal_name in replace_map.items():
                if int(target_line) == line_no + 1:
                    updated_line = updated_line.replace(value, literal_name)
            updated_lines.append(updated_line)

        self.updated_condition_text = '\n'.join(updated_lines)
        self.accept()

    def get_updated_condition_text(self) -> str:
        return self.updated_condition_text