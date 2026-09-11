# statable_gui/layer_settings_dialog.py
"""
レイヤ設定ダイアログ
- 各タブ（層）の実行優先度を一括設定
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
    
    def __init__(self, layers: List[Tuple[str, StateMachine]], parent=None):
        """
        Args:
            layers: [(layer_name, state_machine), ...]
        """
        super().__init__(parent)
        self.layers = layers
        
        self.setWindowTitle("レイヤ設定")
        self.setMinimumSize(500, 400)
        
        self._setup_ui()
        self._load_layers()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 説明
        info_group = QGroupBox("優先度について")
        info_layout = QVBoxLayout(info_group)
        
        info_label = QLabel(
            "優先度は 1〜9 の範囲で設定します。\n"
            "  • 優先度 1（低）: 最初に実行・最初に初期化\n"
            "  • 優先度 9（高）: 最後に実行・最後に初期化\n"
            "実行順序と初期化順序は、優先度の昇順で統一されます。"
        )
        info_label.setStyleSheet("color: gray;")
        info_layout.addWidget(info_label)
        
        layout.addWidget(info_group)
        
        # 層一覧テーブル
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["層名", "優先度", "説明"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
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
        
        for row, (name, sm) in enumerate(sorted_layers):
            # 層名
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)  # 編集不可
            self.table.setItem(row, 0, name_item)
            
            # 優先度（スピンボックス）
            priority = getattr(sm, 'layer_priority', 5)
            priority_spin = QSpinBox()
            priority_spin.setRange(1, 9)
            priority_spin.setValue(priority)
            self.table.setCellWidget(row, 1, priority_spin)
            
            # 説明
            desc = getattr(sm, 'layer_description', '')
            desc_item = QTableWidgetItem(desc)
            self.table.setItem(row, 2, desc_item)
        
        self.table.resizeRowsToContents()
    
    def _on_ok(self):
        # 優先度の重複チェック
        priorities = []
        for row in range(self.table.rowCount()):
            spin = self.table.cellWidget(row, 1)
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
            name = self.table.item(row, 0).text()
            
            # 対応する StateMachine を検索
            target_sm = None
            for layer_name, sm in self.layers:
                if layer_name == name:
                    target_sm = sm
                    break
            
            if target_sm is None:
                continue
            
            # 優先度
            spin = self.table.cellWidget(row, 1)
            if spin:
                target_sm.layer_priority = spin.value()
            
            # 説明
            desc_item = self.table.item(row, 2)
            if desc_item:
                target_sm.layer_description = desc_item.text()
        
        logger.info(f"Layer settings applied for {len(self.layers)} layers")