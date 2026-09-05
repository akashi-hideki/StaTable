# statable_gui/condition_builder_dialog.py
"""
遷移条件ビルダーダイアログ
テキスト入力主体、左ペインから要素を挿入
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QListWidget,
    QListWidgetItem, QLabel, QLineEdit, QPushButton, QDialogButtonBox,
    QSplitter, QGroupBox
)
from PySide6.QtCore import Qt

from statable.global_defs import GlobalDefinitions
from statable.state_machine import StateMachine


class ConditionBuilderDialog(QDialog):
    """遷移条件式をGUIで構築するダイアログ"""

    def __init__(self, condition: str = "", global_defs: GlobalDefinitions = None,
                 state_machine: StateMachine = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("遷移条件ビルダー")
        self.setMinimumSize(900, 600)

        self.global_defs = global_defs if global_defs else GlobalDefinitions()
        self.state_machine = state_machine if state_machine else StateMachine()

        self._setup_ui()
        self.condition_edit.setPlainText(condition)
        self._populate_lists()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Horizontal)

        # 左ペイン：要素リスト
        left_widget = QGroupBox("挿入する要素")
        left_layout = QVBoxLayout(left_widget)
        self.element_list = QListWidget()
        self.element_list.itemDoubleClicked.connect(self._insert_selected_item)
        left_layout.addWidget(self.element_list)

        # 定数シンボルエリア
        const_group = QGroupBox("定数シンボル")
        const_layout = QVBoxLayout(const_group)
        true_btn = QPushButton("true")
        true_btn.clicked.connect(lambda: self._insert_text("true"))
        false_btn = QPushButton("false")
        false_btn.clicked.connect(lambda: self._insert_text("false"))
        const_layout.addWidget(true_btn)
        const_layout.addWidget(false_btn)

        num_layout = QHBoxLayout()
        self.num_input = QLineEdit()
        self.num_input.setPlaceholderText("数値リテラル")
        num_insert_btn = QPushButton("挿入")
        num_insert_btn.clicked.connect(self._insert_number)
        num_layout.addWidget(self.num_input)
        num_layout.addWidget(num_insert_btn)
        const_layout.addLayout(num_layout)

        left_layout.addWidget(const_group)
        splitter.addWidget(left_widget)

        # 中央：テキストエリア
        right_widget = QGroupBox("条件式")
        right_layout = QVBoxLayout(right_widget)
        self.condition_edit = QPlainTextEdit()
        self.condition_edit.setPlaceholderText("ここに条件式を入力してください。\n例: ctx->data.battery_voltage > 3000")
        right_layout.addWidget(self.condition_edit)

        # プレビュー
        self.preview_label = QLabel("")
        right_layout.addWidget(self.preview_label)

        splitter.addWidget(right_widget)
        splitter.setSizes([300, 600])

        main_layout.addWidget(splitter)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def _populate_lists(self):
        """利用可能な要素をリストに追加"""
        self.element_list.clear()

        # グローバル変数
        for var in getattr(self.global_defs, 'variables', []):
            item = QListWidgetItem(f"ctx->data.{var.name}")
            item.setData(Qt.UserRole, f"ctx->data.{var.name}")
            item.setToolTip(getattr(var, 'description', ''))
            self.element_list.addItem(item)

        # イベントフラグ
        for flag in getattr(self.global_defs, 'flags', []):
            item = QListWidgetItem(f"ctx->flags.{flag.name}")
            item.setData(Qt.UserRole, f"ctx->flags.{flag.name}")
            item.setToolTip(getattr(flag, 'description', ''))
            self.element_list.addItem(item)

        # イベント変数（イベント定義から）
        if hasattr(self.state_machine, 'events'):
            for event in self.state_machine.events.values():
                if getattr(event, 'data_name', ''):
                    text = f"event.{event.data_name}"
                    item = QListWidgetItem(text)
                    item.setData(Qt.UserRole, text)
                    item.setToolTip(getattr(event, 'description', ''))
                    self.element_list.addItem(text)

        # ロール関数（戻り値がboolのもの）
        for rf in self.state_machine.role_functions.values():
            if getattr(rf, 'return_type', '') == 'bool':
                func_name = f"RoleFunc_{rf.name}(...)"
                item = QListWidgetItem(func_name)
                item.setData(Qt.UserRole, func_name)
                item.setToolTip(getattr(rf, 'description', ''))
                self.element_list.addItem(item)

    def _insert_selected_item(self, item):
        text = item.data(Qt.UserRole)
        if text:
            self._insert_text(text)

    def _insert_text(self, text: str):
        cursor = self.condition_edit.textCursor()
        cursor.insertText(text)
        self.condition_edit.setTextCursor(cursor)
        self.condition_edit.setFocus()

    def _insert_number(self):
        num = self.num_input.text().strip()
        if num:
            self._insert_text(num)

    def get_condition_text(self) -> str:
        return self.condition_edit.toPlainText().strip()