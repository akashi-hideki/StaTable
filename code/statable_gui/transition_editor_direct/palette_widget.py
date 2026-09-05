# statable_gui/transition_editor_direct/palette_widget.py
"""
パーツパレット（2カテゴリ）
"""

import json
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QAbstractItemView
)


class PaletteListWidget(QListWidget):
    """ドラッグ時にアイテムタイプをMIMEデータに含めるリスト"""
    MIME_TYPE = "application/x-flow-item"

    def __init__(self, item_type: str, parent=None):
        super().__init__(parent)
        self.item_type = item_type
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def mimeData(self, items):
        """ドラッグ時のMIMEデータを生成"""
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
    """パーツパレット"""

    def __init__(self, role_functions=None, transition_events=None, parent=None):
        super().__init__(parent)
        self.role_functions = role_functions or []
        self.transition_events = transition_events or []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # 🟧 ロール関数
        layout.addWidget(QLabel("🟧 ロール関数"))
        self.function_list = PaletteListWidget("function")
        for func in self.role_functions:
            self.function_list.addItem(func)
        self.function_list.setMaximumHeight(200)
        layout.addWidget(self.function_list)

        # 🟦 状態遷移イベント
        layout.addWidget(QLabel("🟦 状態遷移イベント"))
        self.event_list = PaletteListWidget("transition")
        for event in self.transition_events:
            self.event_list.addItem(event)
        self.event_list.setMaximumHeight(200)
        layout.addWidget(self.event_list)

        layout.addStretch()