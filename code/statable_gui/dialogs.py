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
from .global_defs import GlobalDefinitions
from .logger import StaTableLogger


class TransitionTable(QTableWidget):
    """ダブルクリックイベントを確実に捕捉するためのテーブル"""
    cell_double_clicked_any = Signal(int, int)   # 行, 列

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
        # 親クラスの処理は呼ばない（シグナルを二重に発火させない）
        # super().mouseDoubleClickEvent(event)  # 必要なら呼んでも良い


class TransitionListDialog(QDialog):
    """1セル内の複数の遷移条件を一括編集するダイアログ"""
    def __init__(self, parent=None, state_names=None, event_name="",
                 existing_transitions=None, role_functions=None, global_defs=None):
        super().__init__(parent)
        self.setWindowTitle("遷移編集（複数条件）")
        self.setMinimumSize(800, 500)
        self.state_names = state_names or []
        self.role_functions = role_functions or {}
        self.global_defs = global_defs if global_defs else GlobalDefinitions()

        StaTableLogger.debug(f"TransitionListDialog __init__: event='{event_name}', states={len(self.state_names)}, roles={len(self.role_functions)}, global_defs={len(self.global_defs.variables)} vars, {len(self.global_defs.flags)} flags")

        layout = QVBoxLayout(self)

        event_label = QLabel(f"イベント: {event_name if event_name else '完了遷移'}")
        layout.addWidget(event_label)

        self.table = TransitionTable(0, 4)
        self.table.setHorizontalHeaderLabels(["遷移条件", "動作（複数行可）", "遷移先", "表示タイトル"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setFont(QFont("Consolas", 10))
        layout.addWidget(self.table)

        # ダブルクリックシグナル接続
        self.table.cell_double_clicked_any.connect(self.on_cell_double_clicked)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("行追加")
        add_btn.clicked.connect(self.add_row)
        del_btn = QPushButton("行削除")
        del_btn.clicked.connect(self.delete_row)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
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

    def on_cell_double_clicked(self, row, col):
        StaTableLogger.debug(f"TransitionListDialog.on_cell_double_clicked: row={row}, col={col}")
        if col != 1:  # 動作列のみ
            StaTableLogger.debug("  -> Ignored (not action column)")
            return

        item = self.table.item(row, 1)
        if item:
            current_action = item.text()
            StaTableLogger.debug(f"  -> Reading action from QTableWidgetItem: '{current_action[:50]}...'")
        else:
            current_action = ""
            StaTableLogger.debug("  -> No action item found")

        StaTableLogger.debug(f"  -> Opening ActionEditDialog (roles={len(self.role_functions)}, global_defs={len(self.global_defs.variables)} vars, {len(self.global_defs.flags)} flags)")
        dlg = ActionEditDialog(
            self,
            action_text=current_action,
            role_functions=self.role_functions,
            global_defs=self.global_defs
        )
        if dlg.exec() == QDialog.Accepted:
            new_action = dlg.get_action_text()
            StaTableLogger.debug(f"  -> ActionEditDialog accepted. New action length={len(new_action)}")
            if item:
                item.setText(new_action)
                StaTableLogger.debug("  -> Updated QTableWidgetItem with new action")
            else:
                new_item = QTableWidgetItem(new_action)
                self.table.setItem(row, 1, new_item)
                StaTableLogger.debug("  -> Created new QTableWidgetItem for action")
        else:
            StaTableLogger.debug("  -> ActionEditDialog cancelled")

    def add_row(self, trans: Optional[Transition] = None):
        row = self.table.rowCount()
        self.table.insertRow(row)
        StaTableLogger.debug(f"TransitionListDialog.add_row: row={row}")

        # 遷移条件
        cond_item = QTableWidgetItem(trans.guard if trans else "")
        cond_item.setToolTip("C言語式（例：err_code != 0）")
        self.table.setItem(row, 0, cond_item)

        # 動作（QTableWidgetItem を使用）
        action_item = QTableWidgetItem(trans.action if trans else "")
        action_item.setToolTip("ダブルクリックで編集ダイアログを開きます")
        display_text = action_item.text().replace('\n', ' ; ')
        action_item.setText(display_text)
        self.table.setItem(row, 1, action_item)

        # 遷移先（ドロップダウン）
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

    def _generate_title(self, trans: Optional[Transition]) -> str:
        if not trans:
            return ""
        parts = [trans.target] if trans.target else ["(内部)"]
        if trans.guard:
            parts.append(f"[{trans.guard}]")
        if trans.action:
            parts.append(f"/ {trans.action}")
        return " ".join(parts)

    def delete_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            StaTableLogger.debug(f"TransitionListDialog.delete_row: row={row}")

    def get_transitions(self) -> List[Transition]:
        StaTableLogger.debug("TransitionListDialog.get_transitions called")
        transitions = []
        for row in range(self.table.rowCount()):
            guard = self.table.item(row, 0).text().strip() if self.table.item(row, 0) else ""
            action_item = self.table.item(row, 1)
            action = action_item.text().strip() if action_item else ""
            target_widget = self.table.cellWidget(row, 2)
            target = target_widget.currentText().strip() if target_widget else ""
            title_item = self.table.item(row, 3)
            title = title_item.text().strip() if title_item else ""
            if not title and (guard or action or target):
                title = self._generate_title(Transition(source="", event="", guard=guard, action=action, target=target))
            transitions.append(Transition(
                source="",
                event="",
                guard=guard,
                action=action,
                target=target,
                transition_type="external"
            ))
        StaTableLogger.debug(f"  -> {len(transitions)} transitions collected")
        return transitions