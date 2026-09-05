# statable_gui/condition_builder_dialog.py
"""
遷移条件ビルダーダイアログ（レイアウト修正＋デバッグ出力版）
テキスト入力主体、左ペインからシンボル挿入、下部にCコード表示
"""

import re
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QTreeWidget,
    QTreeWidgetItem, QLabel, QLineEdit, QPushButton, QDialogButtonBox,
    QSplitter, QGroupBox, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics

from statable.global_defs import GlobalDefinitions
from statable.state_machine import StateMachine


class ConditionBuilderDialog(QDialog):
    """遷移条件式をGUIで構築するダイアログ"""

    def __init__(self, condition: str = "", global_defs: GlobalDefinitions = None,
                 state_machine: StateMachine = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("遷移条件ビルダー")
        self.setMinimumSize(900, 450)

        self.global_defs = global_defs if global_defs else GlobalDefinitions()
        self.state_machine = state_machine if state_machine else StateMachine()

        self._setup_ui()
        self.condition_edit.setPlainText(condition)
        self._populate_tree()
        self._update_c_code_view()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # 左ペイン：カテゴリ別ツリー
        left_widget = QGroupBox("挿入するシンボル")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(4, 4, 4, 4)
        left_layout.setSpacing(2)

        self.symbol_tree = QTreeWidget()
        self.symbol_tree.setHeaderHidden(True)
        self.symbol_tree.setMinimumHeight(120)
        self.symbol_tree.itemDoubleClicked.connect(self._insert_symbol)
        left_layout.addWidget(self.symbol_tree)

        # 数値リテラル入力
        num_layout = QHBoxLayout()
        self.num_input = QLineEdit()
        self.num_input.setPlaceholderText("数値リテラル")
        num_insert_btn = QPushButton("挿入")
        num_insert_btn.clicked.connect(self._insert_number)
        num_layout.addWidget(self.num_input)
        num_layout.addWidget(num_insert_btn)
        left_layout.addLayout(num_layout)

        main_splitter.addWidget(left_widget)

        # 右ペイン：シンボル名で編集するテキストエリア
        right_widget = QGroupBox("条件式（シンボル名で記述）")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(4, 4, 4, 4)
        right_layout.setSpacing(2)

        self.condition_edit = QPlainTextEdit()
        self.condition_edit.setPlaceholderText(
            "例: battery_voltage > 3000 && EVT_POWER_ON_REQ == 1"
        )
        self.condition_edit.setFrameStyle(QFrame.NoFrame)
        self.condition_edit.setStyleSheet(
            "QPlainTextEdit { padding: 0px; color: black; background: white; }"
        )
        self.condition_edit.document().setDocumentMargin(0)
        self.condition_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        fm = QFontMetrics(self.condition_edit.font())
        row_height = fm.height()
        # 高さを2倍程度（10行分）に設定
        self.condition_edit.setMinimumHeight(row_height * 10 + 4)
        self.condition_edit.textChanged.connect(self._update_c_code_view)
        right_layout.addWidget(self.condition_edit, 1)

        # クリアボタンを右下に配置
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
        bottom_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(4, 4, 4, 4)
        bottom_layout.setSpacing(2)

        self.c_code_view = QPlainTextEdit()
        self.c_code_view.setReadOnly(True)
        self.c_code_view.setFrameStyle(QFrame.NoFrame)
        self.c_code_view.setStyleSheet(
            "QPlainTextEdit { padding: 0px; color: black; background: #f5f5f5; }"
        )
        self.c_code_view.document().setDocumentMargin(0)
        self.c_code_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.c_code_view.setFixedHeight(row_height * 2 + 4)  # 2行分

        bottom_layout.addWidget(self.c_code_view, 1)
        main_layout.addWidget(bottom_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        # デバッグ出力用にウィジェット参照を保存
        self.right_widget = right_widget
        self.bottom_widget = bottom_widget
        self.left_widget = left_widget

    def _populate_tree(self):
        self.symbol_tree.clear()

        global_vars_item = QTreeWidgetItem(["グローバル変数"])
        for var in getattr(self.global_defs, 'variables', []):
            child = QTreeWidgetItem([var.name])
            child.setData(0, Qt.UserRole, var.name)
            child.setToolTip(0, getattr(var, 'description', ''))
            global_vars_item.addChild(child)
        self.symbol_tree.addTopLevelItem(global_vars_item)

        flags_item = QTreeWidgetItem(["イベントフラグ"])
        for flag in getattr(self.global_defs, 'flags', []):
            child = QTreeWidgetItem([flag.name])
            child.setData(0, Qt.UserRole, flag.name)
            child.setToolTip(0, getattr(flag, 'description', ''))
            flags_item.addChild(child)
        self.symbol_tree.addTopLevelItem(flags_item)

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

        role_funcs_item = QTreeWidgetItem(["ロール関数（bool）"])
        for rf in self.state_machine.role_functions.values():
            if getattr(rf, 'return_type', '') == 'bool':
                symbol = f"RoleFunc_{rf.name}(...)"
                child = QTreeWidgetItem([symbol])
                child.setData(0, Qt.UserRole, symbol)
                child.setToolTip(0, getattr(rf, 'description', ''))
                role_funcs_item.addChild(child)
        self.symbol_tree.addTopLevelItem(role_funcs_item)

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
        """シンボル名をCコード表現に置換し、比較演算に括弧を付ける"""
        replace_map = {}

        for var in getattr(self.global_defs, 'variables', []):
            replace_map[var.name] = f"ctx->data.{var.name}"

        for flag in getattr(self.global_defs, 'flags', []):
            replace_map[flag.name] = f"ctx->flags.{flag.name}"

        for event in self.state_machine.events.values():
            data_name = getattr(event, 'data_name', '')
            if data_name:
                symbol = f"event.{data_name}"
                replace_map[symbol] = symbol

        result = text
        for symbol in sorted(replace_map.keys(), key=len, reverse=True):
            result = result.replace(symbol, replace_map[symbol])

        result = self._add_parentheses_to_comparisons(result)
        return result

    def _add_parentheses_to_comparisons(self, text: str) -> str:
        """&& や || で区切られた各比較式に括弧を付ける"""
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
        """式全体が一つの括弧で包まれているか判定"""
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

    def get_condition_text(self) -> str:
        """右ペインのシンボル名テキストを返す"""
        return self.condition_edit.toPlainText().strip()

    def get_c_code_text(self) -> str:
        """下部のCコードテキストを返す"""
        return self.c_code_view.toPlainText().strip()

    def _debug_layout(self):
        """レイアウトデバッグ出力"""
        print("=== Layout Debug ===")
        print(f"Dialog size: {self.size()}")
        print(f"condition_edit size: {self.condition_edit.size()}")
        print(f"condition_edit height: {self.condition_edit.height()}")
        print(f"c_code_view size: {self.c_code_view.size()}")
        print(f"c_code_view height: {self.c_code_view.height()}")
        print(f"bottom_widget size: {self.bottom_widget.size()}")
        print(f"right_widget size: {self.right_widget.size()}")
        print(f"symbol_tree size: {self.symbol_tree.size()}")
        print("====================")