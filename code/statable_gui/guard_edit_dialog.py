from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QDialogButtonBox,
    QLabel, QMessageBox, QMenu, QLineEdit, QTableWidget, QTableWidgetItem,
    QComboBox, QHeaderView, QPushButton, QWidget
)
from PySide6.QtGui import QFont

from statable.global_defs import GlobalDefinitions
from .symbol_picker import SymbolPickerWidget
from .global_defs_dialog import VariableEditDialog, FlagEditDialog
from .logger import StaTableLogger


class GuardLineEdit(QLineEdit):
    """条件式入力用のQLineEdit（右クリックで登録メニュー対応）"""
    register_variable_requested = Signal(str)
    register_flag_requested = Signal(str)

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Consolas", 10))

    def contextMenuEvent(self, event):
        selected_text = self.selectedText().strip()
        menu = self.createStandardContextMenu()
        if selected_text:
            menu.addSeparator()
            menu.addAction(f"'{selected_text}' をグローバル変数として登録",
                           lambda: self.register_variable_requested.emit(selected_text))
            menu.addAction(f"'{selected_text}' をイベントフラグとして登録",
                           lambda: self.register_flag_requested.emit(selected_text))
        menu.exec(event.globalPos())


class GuardEditDialog(QDialog):
    """遷移条件（ガード）を編集するダイアログ（複数行を論理演算子で結合）"""

    LOGICAL_OPS = ["", "AND", "OR", "XOR", "NAND", "NOR"]

    def __init__(self, parent=None, guard_text="", global_defs=None, role_functions=None):
        super().__init__(parent)
        self.setWindowTitle("遷移条件編集")
        self.setMinimumSize(900, 600)

        self.global_defs = global_defs if global_defs else GlobalDefinitions()
        self.role_functions = role_functions if role_functions is not None else {}

        layout = QVBoxLayout(self)

        # タイトル
        title = QLabel("遷移条件編集")
        title.setFont(QFont("sans-serif", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 左右分割
        h_layout = QHBoxLayout()
        layout.addLayout(h_layout)

        # 左：シンボルピッカー
        self.symbol_picker = SymbolPickerWidget(
            global_defs=self.global_defs,
            role_functions=self.role_functions
        )
        self.symbol_picker.insert_requested.connect(self.insert_symbol_to_current_row)
        h_layout.addWidget(self.symbol_picker, stretch=2)

        # 右：条件式テーブル
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("条件式（1行ずつ入力し、論理演算子で結合）:"))

        self.condition_table = QTableWidget(0, 2)
        self.condition_table.setHorizontalHeaderLabels(["論理", "条件式"])
        self.condition_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.condition_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.condition_table.setSelectionBehavior(QTableWidget.SelectRows)
        right_layout.addWidget(self.condition_table, stretch=1)

        # 行追加・削除ボタン
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("行追加")
        add_btn.clicked.connect(lambda: self.add_condition_row())
        del_btn = QPushButton("行削除")
        del_btn.clicked.connect(lambda: self.delete_condition_row())
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        right_layout.addLayout(btn_layout)

        h_layout.addWidget(right_widget, stretch=3)

        # OK/Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # 初期データ読み込み
        self.load_guard_text(guard_text)
        StaTableLogger.debug("GuardEditDialog initialized")

    # ------------------------------------------------------------------
    # 行管理
    # ------------------------------------------------------------------
    def add_condition_row(self, text="", operator="AND"):
        row = self.condition_table.rowCount()
        self.condition_table.insertRow(row)

        # 論理演算子コンボ
        combo = QComboBox()
        combo.addItems(self.LOGICAL_OPS)
        if row == 0:
            combo.setCurrentText("")
            combo.setEnabled(False)
        else:
            combo.setCurrentText(operator)
        self.condition_table.setCellWidget(row, 0, combo)

        # 条件式入力
        line_edit = GuardLineEdit(text)
        line_edit.register_variable_requested.connect(self.register_variable_from_selection)
        line_edit.register_flag_requested.connect(self.register_flag_from_selection)
        self.condition_table.setCellWidget(row, 1, line_edit)

        self._update_operator_enabled()

    def delete_condition_row(self):
        row = self.condition_table.currentRow()
        if row >= 0 and self.condition_table.rowCount() > 1:
            self.condition_table.removeRow(row)
            self._update_operator_enabled()

    def _update_operator_enabled(self):
        if self.condition_table.rowCount() > 0:
            combo = self.condition_table.cellWidget(0, 0)
            if combo:
                combo.setEnabled(False)
                combo.setCurrentText("")

    def load_guard_text(self, guard_text: str):
        """既存のガード文字列を解析してテーブルに読み込む"""
        self.condition_table.setRowCount(0)
        if not guard_text.strip():
            self.add_condition_row()
            return

        # 改行があれば行分割、なければ旧形式として1行扱い
        if '\n' in guard_text:
            lines = [line.strip() for line in guard_text.split('\n') if line.strip()]
        else:
            lines = [guard_text.strip()]

        if not lines:
            self.add_condition_row()
            return

        for i, line in enumerate(lines):
            operator = "AND"
            text = line
            upper = line.upper()
            for op in ["NAND", "NOR", "XOR", "AND", "OR"]:
                if upper.startswith(op + " "):
                    operator = op
                    text = line[len(op) + 1:].strip()
                    break
            if i == 0:
                operator = ""
            self.add_condition_row(text, operator)

        self._update_operator_enabled()

    # ------------------------------------------------------------------
    # シンボル挿入
    # ------------------------------------------------------------------
    def insert_symbol_to_current_row(self, text: str):
        """選択中の行の条件式入力欄へシンボルを挿入"""
        row = self.condition_table.currentRow()
        if row < 0:
            row = self.condition_table.rowCount() - 1
        line_edit = self.condition_table.cellWidget(row, 1)
        if line_edit:
            cursor_pos = line_edit.cursorPosition()
            current_text = line_edit.text()
            new_text = current_text[:cursor_pos] + text + current_text[cursor_pos:]
            line_edit.setText(new_text)
            line_edit.setCursorPosition(cursor_pos + len(text))
            line_edit.setFocus()
        else:
            StaTableLogger.warning("insert_symbol_to_current_row: no line edit found")

    # ------------------------------------------------------------------
    # 登録（選択文字列から）
    # ------------------------------------------------------------------
    def register_variable_from_selection(self, selected_text: str):
        StaTableLogger.debug(f"GuardEditDialog.register_variable_from_selection: '{selected_text}'")
        dlg = VariableEditDialog(self, groups=self.global_defs.variable_groups())
        dlg.name_edit.setText(selected_text)
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

    def register_flag_from_selection(self, selected_text: str):
        StaTableLogger.debug(f"GuardEditDialog.register_flag_from_selection: '{selected_text}'")
        dlg = FlagEditDialog(self, groups=self.global_defs.flag_groups())
        dlg.name_edit.setText(selected_text)
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

    # ------------------------------------------------------------------
    # 結果取得
    # ------------------------------------------------------------------
    def get_guard_text(self) -> str:
        """テーブルの内容を論理演算子で連結して返す（改行区切り）"""
        parts = []
        for row in range(self.condition_table.rowCount()):
            line_edit = self.condition_table.cellWidget(row, 1)
            if not line_edit:
                continue
            cond_text = line_edit.text().strip()
            if not cond_text:
                continue
            if row == 0:
                parts.append(cond_text)
            else:
                combo = self.condition_table.cellWidget(row, 0)
                op = combo.currentText() if combo else "AND"
                parts.append(f"{op} {cond_text}")
        return "\n".join(parts)   # ★ 改行で連結して構造を保持