# statable_gui/transition_editor_direct/palette_widget.py
"""
カテゴリ別折りたたみパレット（elseパーツ削除版）
"""

import json
import logging

from PySide6.QtCore import Qt, QMimeData
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QAbstractItemView, QPushButton
)

logger = logging.getLogger("transition_editor_direct.palette")


class PaletteListWidget(QListWidget):
    MIME_TYPE = "application/x-flow-item"

    def __init__(self, item_type: str, parent=None):
        super().__init__(parent)
        self.item_type = item_type
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def mimeData(self, items):
        mime = QMimeData()
        if items:
            data = {
                "item_type": self.item_type,
                "name": items[0].text(),
            }
            mime.setData(self.MIME_TYPE, json.dumps(data).encode("utf-8"))
            mime.setText(items[0].text())
        return mime


class PaletteWidget(QWidget):
    """カテゴリ別折りたたみパレット"""

    def __init__(self, role_functions=None, transition_events=None, parent=None):
        super().__init__(parent)
        self.role_functions = role_functions or []
        self.transition_events = transition_events or []
        self._setup_ui()
        logger.debug("PaletteWidget initialized")

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # 🟧 ロール関数
        func_container = QWidget()
        v1 = QVBoxLayout(func_container)
        v1.setContentsMargins(0, 0, 0, 0)

        self.function_list = PaletteListWidget("function")
        for func in self.role_functions:
            self.function_list.addItem(func)

        add_func_btn = QPushButton("+ ロール関数追加")
        add_func_btn.clicked.connect(self._add_function)
        v1.addWidget(self.function_list)
        v1.addWidget(add_func_btn)

        # 🟦 状態遷移イベント
        event_container = QWidget()
        v2 = QVBoxLayout(event_container)
        v2.setContentsMargins(0, 0, 0, 0)

        self.event_list = PaletteListWidget("transition")
        for event in self.transition_events:
            self.event_list.addItem(event)

        add_event_btn = QPushButton("+ イベント追加")
        add_event_btn.clicked.connect(self._add_event)
        v2.addWidget(self.event_list)
        v2.addWidget(add_event_btn)

        layout.addWidget(func_container)
        layout.addWidget(event_container)
        layout.addStretch()

        logger.debug(f"Palette items: functions={self.function_list.count()}, "
                     f"events={self.event_list.count()}")

    def _add_function(self):
        name = "NewFunction"
        self.function_list.addItem(name)
        self.role_functions.append(name)
        logger.debug(f"Added function: {name}")

    def _add_event(self):
        name = "NewEvent"
        self.event_list.addItem(name)
        self.transition_events.append(name)
        logger.debug(f"Added event: {name}")