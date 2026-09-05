# statable_gui/transition_editor_direct/palette_widget.py
"""
カテゴリ別折りたたみパレット
"""

import json
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QToolBox, QListWidget, QListWidgetItem,
    QAbstractItemView, QPushButton
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

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.toolbox = QToolBox()
        layout.addWidget(self.toolbox)

        # 🟧 ロール関数
        self.function_list = PaletteListWidget("function")
        for func in self.role_functions:
            self.function_list.addItem(func)
        self._wrap_with_add_button(self.function_list, "🟧 ロール関数", self._add_function)
        self.toolbox.addItem(self.function_list, "🟧 ロール関数")

        # 🟦 状態遷移イベント
        self.event_list = PaletteListWidget("transition")
        for event in self.transition_events:
            self.event_list.addItem(event)
        self._wrap_with_add_button(self.event_list, "🟦 状態遷移イベント", self._add_event)
        self.toolbox.addItem(self.event_list, "🟦 状態遷移イベント")

    def _wrap_with_add_button(self, list_widget, title, add_handler):
        """リストの上に追加ボタンを付ける"""
        container = QWidget()
        v = QVBoxLayout(container)
        btn = QPushButton("+ 追加")
        btn.clicked.connect(add_handler)
        v.addWidget(btn)
        v.addWidget(list_widget)
        self.toolbox.addItem(container, title)

    def _add_function(self):
        # 簡易追加（実際はダイアログで入力）
        name = "NewFunction"
        self.function_list.addItem(name)
        self.role_functions.append(name)

    def _add_event(self):
        # 簡易追加（実際はダイアログで入力）
        name = "NewEvent"
        self.event_list.addItem(name)
        self.transition_events.append(name)