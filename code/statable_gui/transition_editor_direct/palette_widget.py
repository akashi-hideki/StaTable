# statable_gui/transition_editor_direct/palette_widget.py
"""
パーツパレットウィジェット
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt


class PaletteWidget(QWidget):
    """パーツパレット"""

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

        # グローバル変数
        layout.addWidget(QLabel("🟦 グローバル変数"))
        self.variable_list = QListWidget()
        self.variable_list.setDragEnabled(True)
        self.variable_list.setMaximumHeight(100)
        for var in self.variables:
            self.variable_list.addItem(var)
        layout.addWidget(self.variable_list)

        # イベントフラグ
        layout.addWidget(QLabel("🟩 イベントフラグ"))
        self.flag_list = QListWidget()
        self.flag_list.setDragEnabled(True)
        self.flag_list.setMaximumHeight(100)
        for flag in self.flags:
            self.flag_list.addItem(flag)
        layout.addWidget(self.flag_list)

        # ロール関数
        layout.addWidget(QLabel("🟧 ロール関数"))
        self.function_list = QListWidget()
        self.function_list.setDragEnabled(True)
        self.function_list.setMaximumHeight(150)
        for func in self.role_functions:
            self.function_list.addItem(func)
        layout.addWidget(self.function_list)

        # 状態遷移条件
        layout.addWidget(QLabel("🟥 状態遷移条件"))
        self.condition_list = QListWidget()
        self.condition_list.setDragEnabled(True)
        self.condition_list.setMaximumHeight(150)
        for cond in self.conditions:
            self.condition_list.addItem(cond)
        layout.addWidget(self.condition_list)

        layout.addStretch()