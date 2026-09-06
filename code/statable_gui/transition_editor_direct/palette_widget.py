# statable_gui/transition_editor_direct/palette_widget.py
"""
カテゴリ別折りたたみパレット（ドラッグ開始処理・デバッグログ強化版）
"""

import json
import logging

from PySide6.QtCore import Qt, QMimeData, QPoint
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QAbstractItemView, QPushButton, QApplication
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
        self._drag_start_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.position().toPoint()
            logger.debug(f"PaletteListWidget.mousePressEvent: pos={self._drag_start_pos}")
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self._drag_start_pos is not None:
            distance = (event.position().toPoint() - self._drag_start_pos).manhattanLength()
            if distance >= QApplication.startDragDistance():
                logger.debug(f"PaletteListWidget.mouseMoveEvent: drag threshold exceeded, distance={distance}")
                self._start_drag()
                self._drag_start_pos = None
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    def _start_drag(self):
        item = self.currentItem()
        if item is None:
            logger.debug("PaletteListWidget._start_drag: no current item")
            return

        logger.debug(f"PaletteListWidget._start_drag: type={self.item_type}, text='{item.text()}'")

        mime_data = QMimeData()
        data = {
            "item_type": self.item_type,
            "name": item.text(),
        }
        mime_data.setData(self.MIME_TYPE, json.dumps(data).encode("utf-8"))
        mime_data.setText(item.text())

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        result = drag.exec_(Qt.CopyAction)
        logger.debug(f"PaletteListWidget._start_drag: drag exec result={result}")

    # 念のため startDrag もオーバーライド（使われない可能性が高い）
    def startDrag(self, supported_actions):
        logger.debug("PaletteListWidget.startDrag called (fallback)")
        self._start_drag()


class PaletteWidget(QWidget):
    """カテゴリ別折りたたみパレット（ロール関数＋遷移条件）"""

    def __init__(self, role_functions=None, parent=None):
        super().__init__(parent)
        self.role_functions = role_functions or []
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

        # 🟦 遷移条件
        transition_container = QWidget()
        v2 = QVBoxLayout(transition_container)
        v2.setContentsMargins(0, 0, 0, 0)

        self.transition_list = PaletteListWidget("transition")
        # 固定で「＋ 新しい条件」を追加
        self.transition_list.addItem("＋ 新しい条件")

        v2.addWidget(self.transition_list)

        layout.addWidget(func_container)
        layout.addWidget(transition_container)
        layout.addStretch()

        logger.debug(f"Palette items: functions={self.function_list.count()}, "
                     f"transitions={self.transition_list.count()}")

    def _add_function(self):
        name = "NewFunction"
        self.function_list.addItem(name)
        self.role_functions.append(name)
        logger.debug(f"Added function: {name}")