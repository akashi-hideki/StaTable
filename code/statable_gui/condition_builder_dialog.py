# statable_gui/condition_builder_dialog.py
"""
遷移条件ビルダーダイアログ（改訂版）
テキスト入力主体、左ペインからシンボル挿入、下部にCコード表示
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QTreeWidget,
    QTreeWidgetItem, QLabel, QLineEdit, QPushButton, QDialogButtonBox,
    QSplitter, QGroupBox, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics, QFont

from statable.global_defs import GlobalDefinitions
from statable.state_machine import StateMachine


class ConditionBuilderDialog(QDialog):
    """遷移条件式をGUIで構築するダイアログ"""

    def __init__(self, condition: str = "", global_defs: GlobalDefinitions = None,
                 state_machine: StateMachine = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("遷移条件ビルダー")
        self.setMinimumSize(1000, 700)

        self.global_defs = global_defs if global_defs else GlobalDefinitions()
        self.state_machine = state_machine if state_machine else StateMachine()

        self._setup_ui()
        self.condition_edit.setPlainText(condition)
        self._populate_tree()
        self._update_c_code_view()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # メイン分割（左右）
        main_splitter = QSplitter(Qt.Horizontal)

        # 左ペイン：カテゴリ別ツリー
        left_widget = QGroupBox("挿入するシンボル")
        left_layout = QVBoxLayout(left_widget)

        # 定数シンボルエリア
        self.symbol_tree = QTreeWidget()
        self.symbol_tree.setHeaderHidden(True)
        self.symbol_tree.itemDoubleClicked.connect(self._insert_symbol)
        left_layout.addWidget(self.symbol_tree)

        # 定数シンボル用の数値入力（簡易）
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

        # クリアボタン
        clear_btn = QPushButton("クリア")
        clear_btn.clicked.connect(self._clear_condition)
        right_layout.addWidget(clear_btn, alignment=Qt.AlignLeft)

        self.condition_edit = QPlainTextEdit()
        self.condition_edit.setPlaceholderText(
            "例: battery_voltage > 3000 && EVT_POWER_ON_REQ == 1"
        )
        # 最大5行程度に制限
        font_metrics = QFontMetrics(self.condition_edit.font())
        line_height = font_metrics.lineSpacing()
        self.condition_edit.setFixedHeight(line_height * 5 + 10)
        self.condition_edit.textChanged.connect(self._update_c_code_view)
        right_layout.addWidget(self.condition_edit)

        right_layout.addStretch()
        main_splitter.addWidget(right_widget)

        main_splitter.setSizes([300, 700])
        main_layout.addWidget(main_splitter)

        # 下部：ctx->形式のCコード表示
        bottom_widget = QGroupBox("生成されるCコード（ctx->形式）")
        bottom_layout = QVBoxLayout(bottom_widget)
        self.c_code_view = QPlainTextEdit()
        self.c_code_view.setReadOnly(True)
        self.c_code_view.setFixedHeight(line_height * 5 + 10)  # 同じ高さ
        bottom_layout.addWidget(self.c_code_view)
        main_layout.addWidget(bottom_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def _populate_tree(self):
        """利用可能なシンボルをカテゴリ別にツリーへ追加"""
        self.symbol_tree.clear()

        # --- グローバル変数 ---
        global_vars_item = QTreeWidgetItem(["グローバル変数"])
        for var in getattr(self.global_defs, 'variables', []):
            child = QTreeWidgetItem([var.name])
            child.setData(0, Qt.UserRole, var.name)  # シンボル名（そのまま）
            child.setToolTip(0, getattr(var, 'description', ''))
            global_vars_item.addChild(child)
        self.symbol_tree.addTopLevelItem(global_vars_item)

        # --- イベントフラグ ---
        flags_item = QTreeWidgetItem(["イベントフラグ"])
        for flag in getattr(self.global_defs, 'flags', []):
            child = QTreeWidgetItem([flag.name])
            child.setData(0, Qt.UserRole, flag.name)
            child.setToolTip(0, getattr(flag, 'description', ''))
            flags_item.addChild(child)
        self.symbol_tree.addTopLevelItem(flags_item)

        # --- イベント変数（data_nameを持つもの） ---
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

        # --- ロール関数（bool型） ---
        role_funcs_item = QTreeWidgetItem(["ロール関数（bool）"])
        for rf in self.state_machine.role_functions.values():
            if getattr(rf, 'return_type', '') == 'bool':
                symbol = f"RoleFunc_{rf.name}(...)"
                child = QTreeWidgetItem([symbol])
                child.setData(0, Qt.UserRole, symbol)
                child.setToolTip(0, getattr(rf, 'description', ''))
                role_funcs_item.addChild(child)
        self.symbol_tree.addTopLevelItem(role_funcs_item)

        # --- 定数シンボル ---
        const_item = QTreeWidgetItem(["定数シンボル"])
        true_child = QTreeWidgetItem(["true"])
        true_child.setData(0, Qt.UserRole, "true")
        false_child = QTreeWidgetItem(["false"])
        false_child.setData(0, Qt.UserRole, "false")
        const_item.addChild(true_child)
        const_item.addChild(false_child)
        self.symbol_tree.addTopLevelItem(const_item)

        # ツリーを展開
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
        """右のシンボル名テキストをctx->形式のCコードに変換して下部に表示"""
        raw_text = self.condition_edit.toPlainText()
        c_code = self._convert_to_c_code(raw_text)
        self.c_code_view.setPlainText(c_code)

    def _convert_to_c_code(self, text: str) -> str:
        """シンボル名をCコード表現に置換する"""
        # 置換マップ: シンボル -> Cコード表現
        replace_map = {}

        # グローバル変数
        for var in getattr(self.global_defs, 'variables', []):
            replace_map[var.name] = f"ctx->data.{var.name}"

        # イベントフラグ
        for flag in getattr(self.global_defs, 'flags', []):
            replace_map[flag.name] = f"ctx->flags.{flag.name}"

        # イベント変数（event.data_name はそのまま）
        for event in self.state_machine.events.values():
            data_name = getattr(event, 'data_name', '')
            if data_name:
                symbol = f"event.{data_name}"
                replace_map[symbol] = symbol  # 変更不要

        # ロール関数（そのまま、変換しない）
        # 必要ならここで追加

        # 置換実行（長いキーから先に置換）
        result = text
        for symbol in sorted(replace_map.keys(), key=len, reverse=True):
            # 単純な文字列置換（単語境界は考慮しないが、シンプルさ優先）
            result = result.replace(symbol, replace_map[symbol])
        return result

    def get_condition_text(self) -> str:
        """右ペインのシンボル名テキストを返す（呼び出し元はこれを保存）"""
        return self.condition_edit.toPlainText().strip()

    def get_c_code_text(self) -> str:
        """下部のCコードテキストを返す（確認用）"""
        return self.c_code_view.toPlainText().strip()