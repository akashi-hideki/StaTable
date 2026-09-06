# statable_gui/transition_editor_direct/palette_widget.py
"""
カテゴリ別折りたたみパレット（D&D・ボタン追加・デバッグログ強化版）
"""

import json
import logging

from PySide6.QtCore import Qt, QMimeData
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QAbstractItemView, QPushButton, QLabel, QGroupBox
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
            logger.debug(f"PaletteListWidget.mimeData: type={self.item_type}, name='{items[0].text()}'")
        return mime


class PaletteWidget(QWidget):
    """カテゴリ別折りたたみパレット（イベント選択画面）"""

    def __init__(self, role_functions=None, parent=None):
        super().__init__(parent)
        self.role_functions = role_functions or []
        self._setup_ui()
        logger.debug("PaletteWidget initialized")

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # タイトル
        title_label = QLabel("イベント選択画面")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # ロール関数セクション
        func_group = QGroupBox("ロール関数")
        v1 = QVBoxLayout(func_group)
        v1.setContentsMargins(4, 4, 4, 4)
        v1.setSpacing(2)

        self.function_list = PaletteListWidget("function")
        for func in self.role_functions:
            self.function_list.addItem(func)

        add_func_btn = QPushButton("+ ロール関数追加")
        add_func_btn.clicked.connect(self._add_function)

        v1.addWidget(self.function_list)
        v1.addWidget(add_func_btn)

        # 遷移条件セクション
        transition_group = QGroupBox("遷移条件")
        v2 = QVBoxLayout(transition_group)
        v2.setContentsMargins(4, 4, 4, 4)
        v2.setSpacing(2)

        self.transition_list = PaletteListWidget("transition")
        self.transition_list.addItem("＋ 新しい条件")

        add_transition_btn = QPushButton("+ 遷移条件追加")
        add_transition_btn.clicked.connect(self._add_transition)

        v2.addWidget(self.transition_list)
        v2.addWidget(add_transition_btn)

        layout.addWidget(func_group)
        layout.addWidget(transition_group)
        layout.addStretch()

        logger.debug(f"Palette items: functions={self.function_list.count()}, "
                     f"transitions={self.transition_list.count()}")

    def _add_function(self):
        name = "NewFunction"
        self.function_list.addItem(name)
        self.role_functions.append(name)
        logger.debug(f"Added function: {name}")

    def _add_transition(self):
        """遷移条件追加ボタン：既存の「＋ 新しい条件」を維持しつつ、ログを出力"""
        # 既に「＋ 新しい条件」がある場合は何もしない
        for i in range(self.transition_list.count()):
            if self.transition_list.item(i).text() == "＋ 新しい条件":
                logger.debug("Transition placeholder already exists")
                return
        self.transition_list.addItem("＋ 新しい条件")
        logger.debug("Added transition placeholder")