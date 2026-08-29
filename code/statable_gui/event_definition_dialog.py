"""状態遷移イベント定義ダイアログ"""

from typing import Optional, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QMouseEvent
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QComboBox, QLineEdit,
    QFormLayout, QDialogButtonBox, QMessageBox, QAbstractItemView,
    QWidget, QRadioButton, QButtonGroup, QCheckBox, QSpinBox
)

from statable.state_machine import StateMachine
from statable.model import Event, EventDeliveryType, EventSourceLayer, EventKind
from .logger import StaTableLogger


class DoubleClickTable(QTableWidget):
    """ダブルクリックを捕捉するテーブル"""
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


class EventEditDialog(QDialog):
    """状態遷移イベント編集ダイアログ"""

    def __init__(self, parent=None, event: Optional[Event] = None):
        super().__init__(parent)
        self.setWindowTitle("状態遷移イベント編集")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        # イベント名
        self.name_edit = QLineEdit()
        if event:
            self.name_edit.setText(event.name)
        form.addRow("イベント名", self.name_edit)

        # イベントID（数値）
        self.id_spin = QSpinBox()
        self.id_spin.setRange(0, 65535)
        if event and event.id is not None:
            self.id_spin.setValue(event.id)
        form.addRow("イベントID", self.id_spin)

        # 説明
        self.desc_edit = QLineEdit()
        if event:
            self.desc_edit.setText(event.description)
        form.addRow("説明", self.desc_edit)

        # イベント種類
        self.kind_combo = QComboBox()
        for kind in EventKind:
            self.kind_combo.addItem(kind.value, kind)
        if event:
            idx = self.kind_combo.findData(event.kind)
            if idx >= 0:
                self.kind_combo.setCurrentIndex(idx)
        form.addRow("イベント種類", self.kind_combo)

        # 発生源レイヤ
        self.layer_driver = QRadioButton("ドライバ層")
        self.layer_middleware = QRadioButton("ミドル層")
        layer_group = QButtonGroup(self)
        layer_group.addButton(self.layer_driver)
        layer_group.addButton(self.layer_middleware)
        if event and event.source_layer == EventSourceLayer.MIDDLEWARE:
            self.layer_middleware.setChecked(True)
        else:
            self.layer_driver.setChecked(True)
        layer_layout = QHBoxLayout()
        layer_layout.addWidget(self.layer_driver)
        layer_layout.addWidget(self.layer_middleware)
        layer_layout.addStretch()
        form.addRow("発生源レイヤ", layer_layout)

        # 配送タイプ
        self.delivery_combo = QComboBox()
        self.delivery_combo.addItem("DIRECT", EventDeliveryType.DIRECT)
        self.delivery_combo.addItem("QUEUE", EventDeliveryType.QUEUE)
        self.delivery_combo.addItem("DOUBLE", EventDeliveryType.DOUBLE)
        if event:
            idx = self.delivery_combo.findData(event.delivery_type)
            if idx >= 0:
                self.delivery_combo.setCurrentIndex(idx)
        form.addRow("配送タイプ", self.delivery_combo)

        # 付随データ
        self.data_check = QCheckBox("付随データを使用する")
        self.data_check.setChecked(bool(event.data_type if event else False))
        form.addRow("", self.data_check)

        self.data_type_combo = QComboBox()
        self.data_type_combo.setEditable(True)
        self.data_type_combo.addItems(["uint8_t", "uint16_t", "uint32_t", "uint64_t", "int8_t", "int16_t", "int32_t"])
        if event:
            self.data_type_combo.setCurrentText(event.data_type)
        form.addRow("データ型", self.data_type_combo)

        self.data_name_edit = QLineEdit()
        if event:
            self.data_name_edit.setText(event.data_name)
        form.addRow("データ変数名", self.data_name_edit)

        self.data_check.toggled.connect(self._on_data_check_toggled)
        self._on_data_check_toggled(self.data_check.isChecked())

        # OK/Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        StaTableLogger.debug("EventEditDialog initialized")

    def _on_data_check_toggled(self, checked: bool):
        self.data_type_combo.setEnabled(checked)
        self.data_name_edit.setEnabled(checked)

    def get_event(self) -> Event:
        source_layer = EventSourceLayer.MIDDLEWARE if self.layer_middleware.isChecked() else EventSourceLayer.DRIVER
        data_type = self.data_type_combo.currentText().strip() if self.data_check.isChecked() else ""
        data_name = self.data_name_edit.text().strip() if self.data_check.isChecked() else ""
        return Event(
            name=self.name_edit.text().strip(),
            id=self.id_spin.value(),
            kind=self.kind_combo.currentData(),
            description=self.desc_edit.text().strip(),
            delivery_type=self.delivery_combo.currentData(),
            source_layer=source_layer,
            data_type=data_type,
            data_name=data_name,
        )


class EventDefinitionDialog(QDialog):
    """状態遷移イベント定義一覧ダイアログ"""

    def __init__(self, sm: StateMachine, parent=None):
        super().__init__(parent)
        self.sm = sm
        self.setWindowTitle("状態遷移イベント定義")
        self.setMinimumSize(1000, 650)

        layout = QVBoxLayout(self)

        # 検索
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("検索（前方一致）:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("イベント名・説明")
        self.search_edit.textChanged.connect(self.refresh_table)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # イベント一覧テーブル
        self.table = DoubleClickTable(0, 6)
        self.table.setHorizontalHeaderLabels([
            "イベント名", "ID", "発生源", "配送タイプ", "付随データ", "説明"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setFont(QFont("Consolas", 10))
        self.table.cellDoubleClicked.connect(self.on_double_clicked)
        layout.addWidget(self.table, stretch=1)

        # ボタン
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("追加")
        add_btn.clicked.connect(self.add_event)
        del_btn = QPushButton("削除")
        del_btn.clicked.connect(self.delete_event)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 閉じる
        close_btn = QPushButton("閉じる")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

        self.refresh_table()
        StaTableLogger.debug("EventDefinitionDialog initialized")

    def refresh_table(self):
        query = self.search_edit.text().strip().lower() if hasattr(self, 'search_edit') else ""
        self.table.setRowCount(0)
        events = list(self.sm.events.values())
        for event in events:
            name = event.name if event.name else "（完了）"
            desc = event.description
            if query and not (name.lower().startswith(query) or desc.lower().startswith(query)):
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(str(event.id) if event.id is not None else ""))
            self.table.setItem(row, 2, QTableWidgetItem(event.source_layer.value))
            self.table.setItem(row, 3, QTableWidgetItem(event.delivery_type.value))
            data_text = f"{event.data_type} {event.data_name}" if event.data_type else ""
            self.table.setItem(row, 4, QTableWidgetItem(data_text))
            self.table.setItem(row, 5, QTableWidgetItem(event.description))

    def _find_event_by_row(self, row: int) -> Optional[Event]:
        name_item = self.table.item(row, 0)
        if not name_item:
            return None
        name = name_item.text()
        if name == "（完了）":
            name = ""
        return self.sm.events.get(name)

    def on_double_clicked(self, row, col):
        StaTableLogger.debug(f"on_double_clicked: row={row}, col={col}")
        event = self._find_event_by_row(row)
        if not event:
            return
        dlg = EventEditDialog(self, event=event)
        if dlg.exec() == QDialog.Accepted:
            new_event = dlg.get_event()
            if not new_event.name:
                QMessageBox.warning(self, "警告", "イベント名を入力してください。")
                return
            # 名前が変わった場合の処理
            old_name = event.name
            if old_name != new_event.name:
                if new_event.name in self.sm.events:
                    QMessageBox.warning(self, "警告", f"イベント '{new_event.name}' は既に存在します。")
                    return
                del self.sm.events[old_name]
                # 遷移のイベント名も更新
                for trans in self.sm.transitions:
                    if trans.event == old_name:
                        trans.event = new_event.name
            self.sm.events[new_event.name] = new_event
            self.refresh_table()
            StaTableLogger.info(f"Event updated: {new_event.name}")

    def add_event(self):
        dlg = EventEditDialog(self)
        if dlg.exec() == QDialog.Accepted:
            event = dlg.get_event()
            if not event.name:
                QMessageBox.warning(self, "警告", "イベント名を入力してください。")
                return
            if event.name in self.sm.events:
                QMessageBox.warning(self, "警告", f"イベント '{event.name}' は既に存在します。")
                return
            self.sm.add_event(event)
            self.refresh_table()
            StaTableLogger.info(f"Event added: {event.name}")

    def delete_event(self):
        row = self.table.currentRow()
        if row < 0:
            return
        event = self._find_event_by_row(row)
        if not event:
            return

        # 依存チェック
        transitions = self.sm.get_transitions_for_event(event.name)
        if transitions:
            msg = f"イベント '{event.name or '(完了)'}' は削除できません。\n\n以下の遷移で使用されています：\n\n"
            for trans in transitions:
                msg += f"  - {trans.source} → {trans.target} [条件: {trans.condition or 'なし'}]\n"
            msg += "\n先にこれらの遷移を削除してください。"
            QMessageBox.warning(self, "警告", msg)
            return

        # 割り込み処理のチェック
        for intr in self.global_defs.interrupts:
            if event.name in intr.event_names:
                QMessageBox.warning(
                    self, "警告",
                    f"イベント '{event.name}' は割り込み処理 '{intr.name}' で使用されています。\n先に割り込み処理の定義を変更してください。"
                )
                return

        reply = QMessageBox.question(
            self, "確認",
            f"イベント '{event.name or '(完了)'}' を削除しますか？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.sm.remove_event(event.name)
            self.refresh_table()
            StaTableLogger.info(f"Event deleted: {event.name}")