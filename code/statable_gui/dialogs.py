from typing import Optional, List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QComboBox, QTextEdit, QDialogButtonBox,
    QMessageBox, QAbstractItemView
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
    """1セル内の複数の遷移を一括編集するダイアログ（状態遷移条件対応版）"""
    def __init__(self, parent=None, state_names=None, event_name="",
                 existing_transitions=None, role_functions=None, global_defs=None):
        super().__init__(parent)
        self.setWindowTitle("遷移編集（複数条件）")
        self.setMinimumSize(800, 500)
        self.state_names = state_names or []
        self.role_functions = role_functions or {}
        self.global_defs = global_defs if global_defs else GlobalDefinitions()

        StaTableLogger.debug(
            f"TransitionListDialog.__init__: event='{event_name}', "
            f"states={len(self.state_names)}, roles={len(self.role_functions)}, "
            f"global_defs={len(self.global_defs.variables)} vars, {len(self.global_defs.flags)} flags"
        )

        layout = QVBoxLayout(self)

        event_label = QLabel(f"イベント: {event_name if event_name else '完了遷移'}")
        layout.addWidget(event_label)

        self.table = TransitionTable(0, 4)
        self.table.setHorizontalHeaderLabels(["状態遷移条件", "動作（複数行可）", "遷移先", "表示タイトル"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setFont(QFont("Consolas", 10))
        layout.addWidget(self.table)

        # ダブルクリックシグナル接続
        self.table.cell_double_clicked_any.connect(self.on_cell_double_clicked)

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
        buttons.accepted.connect(self.accept)
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
        StaTableLogger.debug(f"TransitionListDialog.on_cell_double_clicked: row={row}, col={col}")

        if col == 0:   # 遷移条件
            self.open_condition_editor(row)
        elif col == 1:
            self.open_action_editor(row)
        else:
            StaTableLogger.debug("  -> Ignored (not editable column)")

    def open_condition_editor(self, row):
        """状態遷移条件セルをダブルクリックしたときの処理"""
        item = self.table.item(row, 0)
        if not item:
            item = QTableWidgetItem("")
            self.table.setItem(row, 0, item)

        # 元のガード文字列を取得（UserRole に保持している）
        current_condition = item.data(Qt.UserRole) if item.data(Qt.UserRole) else ""
        StaTableLogger.debug(f"  -> Opening GuardEditDialog (condition='{current_condition[:50]}...')")

        dlg = GuardEditDialog(
            self,
            guard_text=current_condition,
            global_defs=self.global_defs,
            role_functions=self.role_functions
        )
        if dlg.exec() == QDialog.Accepted:
            new_condition = dlg.get_guard_text()
            item.setText(new_condition.replace('\n', ' ; '))
            item.setData(Qt.UserRole, new_condition)
            StaTableLogger.debug(f"  -> Condition updated: '{new_condition[:50]}...'")

    def open_action_editor(self, row):
        """動作セルをダブルクリックしたときの処理"""
        item = self.table.item(row, 1)
        if not item:
            item = QTableWidgetItem("")
            self.table.setItem(row, 1, item)

        # 元のアクション文字列を取得（UserRole に保持している）
        current_action = item.data(Qt.UserRole) if item.data(Qt.UserRole) else ""
        StaTableLogger.debug(f"  -> Opening ActionEditDialog (action='{current_action[:50]}...')")

        dlg = ActionEditDialog(
            self,
            action_text=current_action,
            role_functions=self.role_functions,
            global_defs=self.global_defs
        )
        if dlg.exec() == QDialog.Accepted:
            new_action = dlg.get_action_text()
            # 表示用テキスト（改行を ; に置換）と元テキストを更新
            item.setText(new_action.replace('\n', ' ; '))
            item.setData(Qt.UserRole, new_action)
            StaTableLogger.debug(f"  -> Action updated: '{new_action[:50]}...'")

    # ------------------------------------------------------------------
    # 行追加・削除
    # ------------------------------------------------------------------
    def add_row(self, trans: Optional[Transition] = None):
        row = self.table.rowCount()
        self.table.insertRow(row)
        StaTableLogger.debug(f"TransitionListDialog.add_row: row={row}")

        # 状態遷移条件（旧 guard）
        cond_item = QTableWidgetItem(trans.condition if trans else "")
        cond_item.setToolTip("ダブルクリックで状態遷移条件を編集")
        cond_item.setData(Qt.UserRole, trans.condition if trans else "")
        self.table.setItem(row, 0, cond_item)

        # 動作
        action_text = trans.action if trans else ""
        action_display = action_text.replace('\n', ' ; ')
        action_item = QTableWidgetItem(action_display)
        action_item.setToolTip("ダブルクリックで動作を編集")
        action_item.setData(Qt.UserRole, action_text)
        self.table.setItem(row, 1, action_item)

        # 遷移先
        target_combo = QComboBox()
        target_combo.addItem("")
        target_combo.addItems(self.state_names)
        if trans and trans.target:
            idx = target_combo.findText(trans.target)
            if idx >= 0:
                target_combo.setCurrentIndex(idx)
        self.table.setCellWidget(row, 2, target_combo)

        # 表示タイトル
        title = self._generate_title(trans) if trans else ""
        title_item = QTableWidgetItem(title)
        title_item.setToolTip("表に表示する短いラベル（空なら自動生成）")
        self.table.setItem(row, 3, title_item)

    def delete_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            StaTableLogger.debug(f"TransitionListDialog.delete_row: row={row}")

    def move_row_up(self):
        row = self.table.currentRow()
        if row > 0:
            self._swap_rows(row, row - 1)
            StaTableLogger.debug(f"TransitionListDialog.move_row_up: row={row} -> {row-1}")

    def move_row_down(self):
        row = self.table.currentRow()
        if row >= 0 and row < self.table.rowCount() - 1:
            self._swap_rows(row, row + 1)
            StaTableLogger.debug(f"TransitionListDialog.move_row_down: row={row} -> {row+1}")

    def _swap_rows(self, row1: int, row2: int):
        """2行の内容を入れ替える"""
        for col in range(self.table.columnCount()):
            if col == 2:  # コンボボックス列
                combo1 = self.table.cellWidget(row1, col)
                combo2 = self.table.cellWidget(row2, col)
                if combo1 and combo2:
                    data1 = combo1.currentData() or combo1.currentText()
                    data2 = combo2.currentData() or combo2.currentText()
                    combo1.setCurrentText(data2)
                    combo2.setCurrentText(data1)
            else:
                item1 = self.table.takeItem(row1, col)
                item2 = self.table.takeItem(row2, col)
                self.table.setItem(row1, col, item2)
                self.table.setItem(row2, col, item1)

    def _generate_title(self, trans: Optional[Transition]) -> str:
        """セルに表示する短いタイトル（改行は ; に置換）"""
        if not trans:
            return ""
        parts = [trans.target] if trans.target else ["(内部)"]
        if trans.condition:
            condition_display = trans.condition.replace('\n', ' ; ')
            parts.append(f"[{condition_display}]")
        if trans.action:
            action_display = trans.action.replace('\n', ' ; ')
            parts.append(f"/ {action_display}")
        return " ".join(parts)

    # ------------------------------------------------------------------
    # 結果取得
    # ------------------------------------------------------------------
    def get_transitions(self) -> List[Transition]:
        StaTableLogger.debug("TransitionListDialog.get_transitions called")
        transitions = []
        for row in range(self.table.rowCount()):
            # ガードは UserRole から取得（改行維持）
            condition_item = self.table.item(row, 0)
            condition = condition_item.data(Qt.UserRole) if condition_item else ""

            # アクションも UserRole から取得（改行維持）
            action_item = self.table.item(row, 1)
            action = action_item.data(Qt.UserRole) if action_item else ""

            target_widget = self.table.cellWidget(row, 2)
            target = target_widget.currentText().strip() if target_widget else ""
            title_item = self.table.item(row, 3)
            title = title_item.text().strip() if title_item else ""
            if not title and (condition or action or target):
                title = self._generate_title(Transition(source="", event="", condition=condition, action=action, target=target))
            transitions.append(Transition(
                source="",
                event="",
                condition=condition,
                action=action,
                target=target,
                transition_type="external",
                title=title
            ))
        StaTableLogger.debug(f"  -> {len(transitions)} transitions collected")
        return transitions