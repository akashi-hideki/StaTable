# statable_gui/transition_editor_direct/palette_widget.py
"""
カテゴリ別折りたたみパレット（共有ライブラリ対応・ドラッグ全段階ログ版）
"""

import json
import logging

from PySide6.QtCore import Qt, QMimeData, Signal
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QAbstractItemView, QPushButton, QLabel, QGroupBox
)

logger = logging.getLogger("transition_editor_direct.palette")


class PaletteListWidget(QListWidget):
    MIME_TYPE = "application/x-flow-item"
    item_edit_requested = Signal(str)

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

    def startDrag(self, supported_actions):
        item = self.currentItem()
        if item is None:
            logger.debug("PaletteListWidget.startDrag: no current item")
            return

        logger.debug(f"PaletteListWidget.startDrag START: type={self.item_type}, name='{item.text()}'")

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
        logger.debug(f"PaletteListWidget.startDrag END: result={result}")

    def mouseDoubleClickEvent(self, event):
        logger.debug(f"PaletteListWidget.mouseDoubleClickEvent: type={self.item_type}")
        item = self.itemAt(event.position().toPoint())
        if item:
            text = item.text()
            logger.debug(f"  item text = '{text}'")
            logger.debug(f"  emitting item_edit_requested('{text}')")
            self.item_edit_requested.emit(text)
            event.accept()
            return
        logger.debug("  no item at click position")
        super().mouseDoubleClickEvent(event)


class PaletteWidget(QWidget):
    """カテゴリ別折りたたみパレット（イベント選択画面）"""

    edit_function_requested = Signal(str)
    edit_transition_requested = Signal(str)

    def __init__(self, role_function_library=None, condition_library=None, parent=None):
        super().__init__(parent)
        self.role_function_library = role_function_library
        self.condition_library = condition_library
        self._setup_ui()
        self.refresh_lists()
        logger.debug("PaletteWidget initialized")

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

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
        self.function_list.item_edit_requested.connect(self._on_function_item_edit_requested)
        v1.addWidget(self.function_list)

        add_func_btn = QPushButton("+ ロール関数追加")
        add_func_btn.clicked.connect(self._add_function)
        v1.addWidget(add_func_btn)

        # 遷移条件セクション
        transition_group = QGroupBox("遷移条件")
        v2 = QVBoxLayout(transition_group)
        v2.setContentsMargins(4, 4, 4, 4)
        v2.setSpacing(2)

        self.transition_list = PaletteListWidget("transition")
        self.transition_list.item_edit_requested.connect(self._on_transition_item_edit_requested)
        v2.addWidget(self.transition_list)

        add_transition_btn = QPushButton("+ 遷移条件追加")
        add_transition_btn.clicked.connect(self._add_transition)
        v2.addWidget(add_transition_btn)

        layout.addWidget(func_group)
        layout.addWidget(transition_group)
        layout.addStretch()

    def _generate_unique_name(self, base_name: str, library) -> str:
        existing_names = set()
        if hasattr(library, 'role_functions'):
            existing_names = set(library.role_functions.keys())
        elif hasattr(library, 'condition_templates'):
            existing_names = set(library.condition_templates.keys())

        if base_name not in existing_names:
            return base_name

        index = 2
        while f"{base_name}_{index}" in existing_names:
            index += 1
        return f"{base_name}_{index}"

    def _add_function(self):
        from libcntrl.role_function_library import RoleFunction
        base_name = "NewFunction"
        name = self._generate_unique_name(base_name, self.role_function_library)
        try:
            self.role_function_library.add(RoleFunction(name=name, title=name))
            logger.debug(f"Added new role function to library: {name}")
        except ValueError as e:
            logger.warning(f"Failed to add role function: {e}")
        self.refresh_lists()

    def _add_transition(self):
        from libcntrl.condition_library import ConditionTemplate
        base_name = "NewEvent"
        name = self._generate_unique_name(base_name, self.condition_library)
        try:
            self.condition_library.add(ConditionTemplate(name=name, condition=""))
            logger.debug(f"Added new condition template to library: {name}")
        except ValueError as e:
            logger.warning(f"Failed to add condition template: {e}")
        self.refresh_lists()

    def _on_function_item_edit_requested(self, name: str):
        logger.debug(f"PaletteWidget._on_function_item_edit_requested: name='{name}'")
        self.edit_function_requested.emit(name)

    def _on_transition_item_edit_requested(self, name: str):
        logger.debug(f"PaletteWidget._on_transition_item_edit_requested: name='{name}'")
        self.edit_transition_requested.emit(name)

    def refresh_lists(self):
        logger.debug("PaletteWidget.refresh_lists called")
        if self.role_function_library:
            self.function_list.clear()
            for rf in self.role_function_library.list_all():
                self.function_list.addItem(rf.name)
            logger.debug(f"Function list refreshed: {self.function_list.count()} items")

        if self.condition_library:
            self.transition_list.clear()
            for ct in self.condition_library.list_all():
                self.transition_list.addItem(ct.name)
            logger.debug(f"Transition list refreshed: {self.transition_list.count()} items")