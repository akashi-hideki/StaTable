"""イベントキュー定義ダイアログ（一覧テーブル→ダブルクリックで編集）"""

from typing import Optional, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QMouseEvent
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QComboBox, QLineEdit, QSpinBox,
    QCheckBox, QFormLayout, QDialogButtonBox, QMessageBox, QAbstractItemView,
    QWidget
)

from statable.global_defs import GlobalDefinitions, EventQueueDef
from .logger import StaTableLogger


class DoubleClickTable(QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        pos = event.position().toPoint()
        item = self.itemAt(pos)
        if item:
            row = item.row()
            StaTableLogger.debug(f"DoubleClickTable.mouseDoubleClickEvent: row={row}")
            self.cellDoubleClicked.emit(row, item.column())
        else:
            StaTableLogger.debug("DoubleClickTable.mouseDoubleClickEvent: no item")


class EventQueueEditDialog(QDialog):
    """イベントキュー編集ダイアログ"""

    def __init__(self, parent=None, queue_def: Optional[EventQueueDef] = None):
        super().__init__(parent)
        self.setWindowTitle("イベントキュー編集")
        self.setMinimumWidth(450)

        form = QFormLayout(self)

        # キュー名
        self.name_edit = QLineEdit()
        if queue_def:
            self.name_edit.setText(queue_def.name)
        form.addRow("キュー名", self.name_edit)

        # サイズ
        self.size_spin = QSpinBox()
        self.size_spin.setRange(2, 256)
        if queue_def:
            self.size_spin.setValue(queue_def.size)
        else:
            self.size_spin.setValue(8)
        form.addRow("サイズ", self.size_spin)

        # 要素型
        self.type_combo = QComboBox()
        self.type_combo.setEditable(True)
        self.type_combo.addItems(["uint8_t", "uint16_t", "uint32_t", "uint64_t"])
        if queue_def:
            self.type_combo.setCurrentText(queue_def.element_type)
        form.addRow("要素型", self.type_combo)

        # 優先度付き
        self.priority_check = QCheckBox()
        self.priority_check.setChecked(queue_def.priority_enabled if queue_def else False)
        form.addRow("優先度付き", self.priority_check)

        # 割込保護
        self.safe_check = QCheckBox()
        self.safe_check.setChecked(queue_def.interrupt_safe if queue_def else True)
        form.addRow("割込保護", self.safe_check)

        # RTOS使用（将来拡張）
        self.rtos_check = QCheckBox()
        self.rtos_check.setChecked(queue_def.rtos_enabled if queue_def else False)
        form.addRow("RTOS使用", self.rtos_check)

        # 説明
        self.desc_edit = QLineEdit()
        if queue_def:
            self.desc_edit.setText(queue_def.description)
        form.addRow("説明", self.desc_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def get_queue_def(self) -> EventQueueDef:
        return EventQueueDef(
            name=self.name_edit.text().strip(),
            size=self.size_spin.value(),
            element_type=self.type_combo.currentText().strip(),
            priority_enabled=self.priority_check.isChecked(),
            interrupt_safe=self.safe_check.isChecked(),
            rtos_enabled=self.rtos_check.isChecked(),
            description=self.desc_edit.text().strip(),
        )


class EventQueueDefsDialog(QDialog):
    """イベントキュー定義一覧ダイアログ"""

    def __init__(self, global_defs: GlobalDefinitions, parent=None):
        super().__init__(parent)
        self.global_defs = global_defs
        self.setWindowTitle("イベントキュー定義")
        self.setMinimumSize(900, 600)

        layout = QVBoxLayout(self)

        # 検索
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("検索（前方一致）:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("キュー名・説明")
        self.search_edit.textChanged.connect(self.refresh_table)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # 一覧テーブル
        self.table = DoubleClickTable(0, 7)
        self.table.setHorizontalHeaderLabels([
            "キュー名", "サイズ", "要素型", "優先度", "割込保護", "RTOS", "説明"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.cellDoubleClicked.connect(self.on_double_clicked)
        layout.addWidget(self.table)

        # ボタン
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("追加")
        add_btn.clicked.connect(self.add_queue)
        del_btn = QPushButton("削除")
        del_btn.clicked.connect(self.delete_queue)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 閉じる
        close_btn = QPushButton("閉じる")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

        self.refresh_table()
        StaTableLogger.debug("EventQueueDefsDialog initialized")

    def refresh_table(self):
        query = self.search_edit.text().strip().lower() if hasattr(self, 'search_edit') else ""
        self.table.setRowCount(0)
        for q in self.global_defs.event_queues:
            if self._matches(q, query):
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(q.name))
                self.table.setItem(row, 1, QTableWidgetItem(str(q.size)))
                self.table.setItem(row, 2, QTableWidgetItem(q.element_type))
                self.table.setItem(row, 3, QTableWidgetItem("あり" if q.priority_enabled else "なし"))
                self.table.setItem(row, 4, QTableWidgetItem("あり" if q.interrupt_safe else "なし"))
                self.table.setItem(row, 5, QTableWidgetItem("あり" if q.rtos_enabled else "なし"))
                self.table.setItem(row, 6, QTableWidgetItem(q.description))

    def _matches(self, q: EventQueueDef, query: str) -> bool:
        if not query:
            return True
        return q.name.lower().startswith(query) or q.description.lower().startswith(query)

    def on_double_clicked(self, row, col):
        StaTableLogger.debug(f"on_double_clicked: row={row}, col={col}")
        if row < 0 or row >= len(self.global_defs.event_queues):
            return
        target = self.global_defs.event_queues[row]
        dlg = EventQueueEditDialog(self, queue_def=target)
        if dlg.exec() == QDialog.Accepted:
            new_q = dlg.get_queue_def()
            if not new_q.name:
                QMessageBox.warning(self, "警告", "キュー名を入力してください。")
                return
            self.global_defs.event_queues[row] = new_q
            self.refresh_table()

    def add_queue(self):
        dlg = EventQueueEditDialog(self)
        if dlg.exec() == QDialog.Accepted:
            q = dlg.get_queue_def()
            if not q.name:
                QMessageBox.warning(self, "警告", "キュー名を入力してください。")
                return
            self.global_defs.event_queues.append(q)
            self.refresh_table()

    def delete_queue(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.global_defs.event_queues):
            self.global_defs.event_queues.pop(row)
            self.refresh_table()