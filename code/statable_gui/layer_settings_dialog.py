# statable_gui/layer_settings_dialog.py
"""
レイヤ設定ダイアログ
- 各タブ（層）の実行優先度・層名を一括設定
"""

import logging
from typing import List, Tuple

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QPushButton,
    QSpinBox, QAbstractItemView, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt

from statable.state_machine import StateMachine

logger = logging.getLogger(__name__)


class LayerSettingsDialog(QDialog):
    """レイヤ設定ダイアログ"""

    def __init__(self, layers: List[Tuple[str, StateMachine]],
                 parent=None):
        """
        Args:
            layers: [(tab_name, state_machine), ...]
        """
        super().__init__(parent)
        self.layers = layers

        self.setWindowTitle("レイヤ設定")
        self.setMinimumSize(640, 420)

        self._setup_ui()
        self._load_layers()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 説明
        info_group = QGroupBox("設定項目について")
        info_layout = QVBoxLayout(info_group)

        info_label = QLabel(
            "・層名: 生成コードの識別子に使用（例: Driver → "
            "STATE_Driver_Idle）。\n"
            "  空欄にすると層名なし版（STATE_Idle）が生成されます。\n"
            "・優先度: 1〜9 の範囲。1（低）が最初に実行・初期化。\n"
            "・タブ名: 表示用の名前（変更はタブ名変更メニューから）。"
        )
        info_label.setStyleSheet("color: gray;")
        info_layout.addWidget(info_label)

        layout.addWidget(info_group)

        # 層一覧テーブル（4列）
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["タブ名", "層名", "優先度", "説明"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.Stretch)
        self.table.setSelectionMode(
            QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(
            QAbstractItemView.DoubleClicked
            | QAbstractItemView.EditKeyPressed
        )

        layout.addWidget(self.table)

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self._on_ok)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

    def _load_layers(self):
        self.table.setRowCount(len(self.layers))

        # 優先度の昇順でソート
        sorted_layers = sorted(
            self.layers,
            key=lambda x: getattr(x[1], 'layer_priority', 5)
        )

        for row, (tab_name, sm) in enumerate(sorted_layers):
            # タブ名（編集不可）
            tab_item = QTableWidgetItem(tab_name)
            tab_item.setFlags(
                tab_item.flags() & ~Qt.ItemIsEditable
            )
            self.table.setItem(row, 0, tab_item)

            # ★ 層名（編集可）
            layer_name = getattr(sm, 'layer_name', '')
            name_item = QTableWidgetItem(layer_name)
            self.table.setItem(row, 1, name_item)

            # 優先度（スピンボックス）
            priority = getattr(sm, 'layer_priority', 5)
            priority_spin = QSpinBox()
            priority_spin.setRange(1, 9)
            priority_spin.setValue(priority)
            self.table.setCellWidget(row, 2, priority_spin)

            # 説明
            desc = getattr(sm, 'layer_description', '')
            desc_item = QTableWidgetItem(desc)
            self.table.setItem(row, 3, desc_item)

        self.table.resizeRowsToContents()

    def _on_ok(self):
        # 優先度の重複チェック
        priorities = []
        for row in range(self.table.rowCount()):
            spin = self.table.cellWidget(row, 2)
            if spin:
                priorities.append(spin.value())

        if len(priorities) != len(set(priorities)):
            reply = QMessageBox.question(
                self, "確認",
                "優先度が重複しています。このまま続けますか？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        self.accept()

    def apply_settings(self):
        """設定を各 StateMachine に反映"""
        for row in range(self.table.rowCount()):
            tab_name = self.table.item(row, 0).text()

            # 対応する StateMachine を検索
            target_sm = None
            for name, sm in self.layers:
                if name == tab_name:
                    target_sm = sm
                    break

            if target_sm is None:
                continue

            # ★ 層名
            name_item = self.table.item(row, 1)
            if name_item:
                target_sm.layer_name = name_item.text().strip()

            # 優先度
            spin = self.table.cellWidget(row, 2)
            if spin:
                target_sm.layer_priority = spin.value()

            # 説明
            desc_item = self.table.item(row, 3)
            if desc_item:
                target_sm.layer_description = desc_item.text()

        logger.info(
            f"Layer settings applied for "
            f"{len(self.layers)} layers"
        )