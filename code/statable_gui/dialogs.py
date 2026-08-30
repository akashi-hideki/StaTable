from typing import Optional, List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QComboBox, QDialogButtonBox,
    QAbstractItemView
)
from PySide6.QtGui import QFont, QMouseEvent
from PySide6.QtCore import Qt, Signal

from statable.model import Transition
from .action_edit_dialog import ActionEditDialog
from .condition_edit_dialog import ConditionEditDialog
from .global_defs import GlobalDefinitions
from .logger import StaTableLogger


class TransitionTable(QTableWidget):
    """ダブルクリックイベントを確実に捕捉するためのテーブル"""
    cell_double_clicked_any = Signal(int, int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 編集トリガーを無効化して、ダブルクリックをシグナルとして扱う
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """マウスダブルクリックをログ出力し、シグナルを発火する"""
        pos = event.position().toPoint()
        item = self.itemAt(pos)
        if item:
            row, col = item.row(), item.column()
            StaTableLogger.debug(f"TransitionTable.mouseDoubleClickEvent: row={row}, col={col}")
            self.cell_double_clicked_any.emit(row, col)
        else:
            StaTableLogger.debug("TransitionTable.mouseDoubleClickEvent: no item at position")
        # 親クラスの処理は呼ばない（二重発火を防ぐ）


class TransitionListDialog(QDialog):
    """1セル内の複数の遷移を一括編集するダイアログ"""

    def __init__(self, parent=None, state_names=None, event_name="",
                 existing_transitions=None, role_functions=None, global_defs=None):
        super().__init__(parent)
        self.setWindowTitle("遷移編集（複数条件）")
        self.setMinimumSize(900, 550)
        self.state_names = state_names or []
        self.role_functions = role_functions or {}
        self.global_defs = global_defs if global_defs else GlobalDefinitions()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"イベント: {event_name if event_name else '完了遷移'}"))

        # タイトル列を含む5列テーブル
        self.table = TransitionTable(0, 5)
        self.table.setHorizontalHeaderLabels(["タイトル", "状態遷移条件", "動作", "遷移先", "表示タイトル"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setFont(QFont("Consolas", 10))
        layout.addWidget(self.table)

        # ダブルクリックシグナル接続
        self.table.cell_double_clicked_any.connect(self.on_cell_double_clicked)
        self.table.itemChanged.connect(self.on_item_changed)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("行追加")
        add_btn.clicked.connect(lambda: self.add_row())
        del_btn = QPushButton("行削除")
        del_btn.clicked.connect(lambda: self.delete_row())
        up_btn = QPushButton("上へ")
        up_btn.clicked.connect(lambda: self.move_row_up())
        down_btn = QPushButton("下へ")
        down_btn.clicked.connect(lambda: self.move_row_down())
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(up_btn)
        btn_layout.addWidget(down_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if existing_transitions:
            for trans in existing_transitions:
                self.add_row(trans)
        else:
            self.add_row()

        StaTableLogger.debug("TransitionListDialog initialization completed")

    # ------------------------------------------------------------------
    # セルダブルクリック
    # ------------------------------------------------------------------
    def on_cell_double_clicked(self, row, col):
        if col == 1:
            self.open_condition_editor(row)
        elif col == 2:
            self.open_action_editor(row)

    def on_item_changed(self, item):
        """タイトル列が直接編集されたときの処理"""
        if item.column() == 0:
            StaTableLogger.debug(f"Title edited directly: row={item.row()}, text='{item.text()}'")
            # 表示タイトル列も更新
            row = item.row()
            display_item = self.table.item(row, 4)
            if display_item:
                display_item.setText(item.text())

    def open_condition_editor(self, row):
        """状態遷移条件セルをダブルクリックしたときの処理"""
        item = self.table.item(row, 1)
        if not item:
            item = QTableWidgetItem("")
            self.table.setItem(row, 1, item)

        # 元のガード文字列を取得（UserRole に保持している）
        current_condition = item.data(Qt.UserRole) if item.data(Qt.UserRole) else ""
        title_item = self.table.item(row, 0)
        current_title = title_item.text() if title_item else ""

        dlg = ConditionEditDialog(
            self, condition_text=current_condition, title=current_title,
            global_defs=self.global_defs, role_functions=self.role_functions
        )
        if dlg.exec() == QDialog.Accepted:
            new_condition = dlg.get_condition_text()
            new_title = dlg.get_title()
            item.setText(new_condition.replace('\n', ' ; '))
            item.setData(Qt.UserRole, new_condition)
            if title_item:
                title_item.setText(new_title)
            self._update_display_title(row)

    def open_action_editor(self, row):
        """動作セルをダブルクリックしたときの処理"""
        item = self.table.item(row, 2)
        if not item:
            item = QTableWidgetItem("")
            self.table.setItem(row, 2, item)

        current_action = item.data(Qt.UserRole) if item.data(Qt.UserRole) else ""
        title_item = self.table.item(row, 0)
        current_title = title_item.text() if title_item else ""

        dlg = ActionEditDialog(
            self, action_text=current_action, title=current_title,
            role_functions=self.role_functions, global_defs=self.global_defs
        )
        if dlg.exec() == QDialog.Accepted:
            new_action = dlg.get_action_text()
            new_title = dlg.get_title()
            item.setText(new_action.replace('\n', ' ; '))
            item.setData(Qt.UserRole, new_action)
            if title_item:
                title_item.setText(new_title)
            self._update_display_title(row)

    # ------------------------------------------------------------------
    # 行追加・削除
    # ------------------------------------------------------------------
    def _update_display_title(self, row: int):
        """表示タイトル列を更新"""
        title_item = self.table.item(row, 0)
        display_item = self.table.item(row, 4)
        if title_item and display_item:
            display_item.setText(title_item.text())

    def add_row(self, trans: Optional[Transition] = None):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # タイトル（直接編集可能）
        title_text = trans.title if trans else "(無題遷移)"
        title_item = QTableWidgetItem(title_text)
        title_item.setToolTip("この遷移のタイトル。直接編集できます。")
        self.table.setItem(row, 0, title_item)

        # 状態遷移条件
        cond_item = QTableWidgetItem(trans.condition if trans else "")
        cond_item.setToolTip("ダブルクリックで状態遷移条件を編集")
        cond_item.setData(Qt.UserRole, trans.condition if trans else "")
        self.table.setItem(row, 1, cond_item)

        # 動作
        action_text = trans.action if trans else ""
        action_item = QTableWidgetItem(action_text.replace('\n', ' ; '))
        action_item.setToolTip("ダブルクリックで動作を編集")
        action_item.setData(Qt.UserRole, action_text)
        self.table.setItem(row, 2, action_item)

        # 遷移先
        target_combo = QComboBox()
        target_combo.addItem("")
        target_combo.addItems(self.state_names)
        if trans and trans.target:
            idx = target_combo.findText(trans.target)
            if idx >= 0:
                target_combo.setCurrentIndex(idx)
        self.table.setCellWidget(row, 3, target_combo)

        # 表示タイトル（自動生成された短いラベル）
        display_title = self._generate_display_title(trans) if trans else ""
        display_item = QTableWidgetItem(display_title)
        display_item.setFlags(display_item.flags() & ~Qt.ItemIsEditable)
        display_item.setToolTip("状態遷移表に表示される短いラベル（自動生成）")
        self.table.setItem(row, 4, display_item)

    def delete_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def move_row_up(self):
        row = self.table.currentRow()
        if row > 0:
            self._swap_rows(row, row - 1)

    def move_row_down(self):
        row = self.table.currentRow()
        if row >= 0 and row < self.table.rowCount() - 1:
            self._swap_rows(row, row + 1)

    def _swap_rows(self, row1: int, row2: int):
        """2行の内容を入れ替える"""
        for col in range(self.table.columnCount()):
            if col == 3:
                combo1 = self.table.cellWidget(row1, col)
                combo2 = self.table.cellWidget(row2, col)
                if combo1 and combo2:
                    text1 = combo1.currentText()
                    text2 = combo2.currentText()
                    combo1.setCurrentText(text2)
                    combo2.setCurrentText(text1)
            else:
                item1 = self.table.takeItem(row1, col)
                item2 = self.table.takeItem(row2, col)
                self.table.setItem(row1, col, item2)
                self.table.setItem(row2, col, item1)

    def _generate_display_title(self, trans: Optional[Transition]) -> str:
        """状態遷移表に表示する短いラベル"""
        if not trans:
            return ""
        if trans.title and trans.title != "(無題遷移)":
            return trans.title
        parts = [trans.target] if trans.target else ["(内部)"]
        if trans.condition:
            condition_display = trans.condition.replace('\n', ' ; ')
            parts.append(f"[{condition_display[:30]}]")
        return " ".join(parts)

    def _on_accept(self):
        """OKボタン：タイトルが空の行に仮タイトルを自動設定"""
        for row in range(self.table.rowCount()):
            title_item = self.table.item(row, 0)
            if title_item and not title_item.text().strip():
                title_item.setText("(無題遷移)")
            self._update_display_title(row)
        self.accept()

    # ------------------------------------------------------------------
    # 結果取得
    # ------------------------------------------------------------------
    def get_transitions(self) -> List[Transition]:
        transitions = []
        for row in range(self.table.rowCount()):
            title_item = self.table.item(row, 0)
            title = title_item.text().strip() if title_item else "(無題遷移)"
            condition_item = self.table.item(row, 1)
            condition = condition_item.data(Qt.UserRole) if condition_item else ""
            action_item = self.table.item(row, 2)
            action = action_item.data(Qt.UserRole) if action_item else ""
            target_widget = self.table.cellWidget(row, 3)
            target = target_widget.currentText().strip() if target_widget else ""
            transitions.append(Transition(
                source="", event="", condition=condition, action=action,
                target=target, transition_type="external", title=title,
            ))
        return transitions