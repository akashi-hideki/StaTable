# statable_gui/layer_settings_dialog.py
"""\nLayer settings dialog\n- Batch configure execution priority and layer name for each tab (layer)\n"""

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
    """Layer settingsダイアログ"""

    def __init__(self, layers: List[Tuple[str, StateMachine]],
                 parent=None):
        """
        Args:
            layers: [(tab_name, state_machine), ...]
        """
        super().__init__(parent)
        self.layers = layers

        self.setWindowTitle("Layer settings")
        self.setMinimumSize(640, 420)

        self._setup_ui()
        self._load_layers()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # description
        info_group = QGroupBox("About settings items")
        info_layout = QVBoxLayout(info_group)

        info_label = QLabel(
            "- Layer name: used in generated code identifiers (e.g., Driver -> "
            "STATE_Driver_Idle).\n"
            "  Leaving it empty generates a version without a layer name (STATE_Idle).\n"
            "- Priority: range 1-9. 1 (low) runs / initializes first.\n"
            "- Tab name: display name (change via the tab rename menu)."
        )
        info_label.setStyleSheet("color: gray;")
        info_layout.addWidget(info_label)

        layout.addWidget(info_group)

        # Layer list table (4 columns)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Tab name", "Layer name", "Priority", "Description"]
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

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self._on_ok)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

    def _load_layers(self):
        self.table.setRowCount(len(self.layers))

        # Priorityの昇順でソート
        sorted_layers = sorted(
            self.layers,
            key=lambda x: getattr(x[1], 'layer_priority', 5)
        )

        for row, (tab_name, sm) in enumerate(sorted_layers):
            # Tab名（Edit不可）
            tab_item = QTableWidgetItem(tab_name)
            tab_item.setFlags(
                tab_item.flags() & ~Qt.ItemIsEditable
            )
            self.table.setItem(row, 0, tab_item)

            # Layer name（Edit可）
            layer_name = getattr(sm, 'layer_name', '')
            name_item = QTableWidgetItem(layer_name)
            self.table.setItem(row, 1, name_item)

            # Priority（スピンボックス）
            priority = getattr(sm, 'layer_priority', 5)
            priority_spin = QSpinBox()
            priority_spin.setRange(1, 9)
            priority_spin.setValue(priority)
            self.table.setCellWidget(row, 2, priority_spin)

            # description
            desc = getattr(sm, 'layer_description', '')
            desc_item = QTableWidgetItem(desc)
            self.table.setItem(row, 3, desc_item)

        self.table.resizeRowsToContents()

    def _on_ok(self):
        # Priorityの重複チェック
        priorities = []
        for row in range(self.table.rowCount()):
            spin = self.table.cellWidget(row, 2)
            if spin:
                priorities.append(spin.value())

        if len(priorities) != len(set(priorities)):
            reply = QMessageBox.question(
                self, "Confirm",
                "Priorityが重複していdoes。このまま続けdoesか？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        self.accept()

    def apply_settings(self):
        """Apply settings to each StateMachine"""
        for row in range(self.table.rowCount()):
            tab_name = self.table.item(row, 0).text()

            #Search for corresponding StateMachine
            target_sm = None
            for name, sm in self.layers:
                if name == tab_name:
                    target_sm = sm
                    break

            if target_sm is None:
                continue

            # Layer name
            name_item = self.table.item(row, 1)
            if name_item:
                target_sm.layer_name = name_item.text().strip()

            # Priority
            spin = self.table.cellWidget(row, 2)
            if spin:
                target_sm.layer_priority = spin.value()

            # description
            desc_item = self.table.item(row, 3)
            if desc_item:
                target_sm.layer_description = desc_item.text()

        logger.info(
            f"Layer settings applied for "
            f"{len(self.layers)} layers"
        )