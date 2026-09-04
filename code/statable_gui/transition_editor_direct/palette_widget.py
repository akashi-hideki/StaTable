# statable_gui/transition_editor_direct/palette_widget.py
"""
パーツパレットウィジェット（修正版）
ドラッグ時にアイテムタイプをMIMEデータとして渡す
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
    """パーツパレット（ドラッグ元）"""

    def __init__(self, variables=None, flags=None, role_functions=None, conditions=None, parent=None):
        super().__init__(parent)
        self.variables = variables or []
        self.flags = flags or []
        self.role_functions = role_functions or []
        self.conditions = conditions or []

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # 🟦 変数
        layout.addWidget(QLabel("🟦 変数"))
        self.variable_list = PaletteListWidget("variable")
        for var in self.variables:
            self.variable_list.addItem(var)
        self.variable_list.setMaximumHeight(100)
        layout.addWidget(self.variable_list)

        # 🟩 フラグ
        layout.addWidget(QLabel("🟩 フラグ"))
        self.flag_list = PaletteListWidget("flag")
        for flag in self.flags:
            self.flag_list.addItem(flag)
        self.flag_list.setMaximumHeight(100)
        layout.addWidget(self.flag_list)

        # 🟧 関数
        layout.addWidget(QLabel("🟧 関数"))
        self.function_list = PaletteListWidget("function")
        for func in self.role_functions:
            self.function_list.addItem(func)
        self.function_list.setMaximumHeight(150)
        layout.addWidget(self.function_list)

        # 🟥 状態遷移条件
        layout.addWidget(QLabel("🟥 状態遷移条件"))
        self.condition_list = PaletteListWidget("condition")
        for cond in self.conditions:
            self.condition_list.addItem(cond)
        self.condition_list.setMaximumHeight(150)
        layout.addWidget(self.condition_list)

        layout.addStretch()