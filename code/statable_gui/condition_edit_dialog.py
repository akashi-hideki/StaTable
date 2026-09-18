from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox,
    QPushButton, QLabel, QDialogButtonBox, QPlainTextEdit, QSplitter,
    QWidget
)

from statable.global_defs import GlobalDefinitions
from .common_widgets import TitleEditWidget
from .symbol_picker import SymbolPickerWidget
from .logger import StaTableLogger


class ConditionEditDialog(QDialog):
    """State transition conditionをEditするダイアログ"""

    def __init__(self, parent=None, condition_text="", title="", global_defs=None, role_functions=None):
        super().__init__(parent)
        self.setWindowTitle("State transition conditionEdit")
        self.setMinimumSize(900, 650)
        self.global_defs = global_defs if global_defs else GlobalDefinitions()
        self.role_functions = role_functions if role_functions is not None else {}

        StaTableLogger.debug(
            f"ConditionEditDialog.__init__: condition_text_len={len(condition_text)}, "
            f"title='{title}', vars={len(self.global_defs.variables)}, flags={len(self.global_defs.flags)}"
        )

        main_layout = QVBoxLayout(self)

        # Title入力ウィジェット
        self.title_widget = TitleEditWidget(self, title=title)
        main_layout.addWidget(self.title_widget)

        # Role functionSelection・Insertバー
        role_bar = QHBoxLayout()
        role_bar.addWidget(QLabel("Role function:"))
        self.role_combo = QComboBox()
        self.refresh_role_combo()
        role_bar.addWidget(self.role_combo)
        insert_role_btn = QPushButton("Insert")
        insert_role_btn.clicked.connect(self.insert_role_function)
        role_bar.addWidget(insert_role_btn)
        main_layout.addLayout(role_bar)

        # Left/right split
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left: symbol picker
        self.symbol_picker = SymbolPickerWidget(
            global_defs=self.global_defs,
            role_functions=self.role_functions
        )
        self.symbol_picker.insert_requested.connect(self.insert_symbol)
        splitter.addWidget(self.symbol_picker)

        # 右側:Condition式Edit
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("Condition:"))
        self.condition_edit = QPlainTextEdit()
        self.condition_edit.setPlainText(condition_text)
        self.condition_edit.setFont(QFont("Consolas", 10))
        right_layout.addWidget(self.condition_edit, stretch=1)
        splitter.addWidget(right_widget)

        # Logical operator combo
        op_layout = QHBoxLayout()
        op_layout.addWidget(QLabel("Logical operator:"))
        self.op_combo = QComboBox()
        self.op_combo.addItems(["AND", "OR", "XOR", "NAND", "NOR"])
        op_layout.addWidget(self.op_combo)
        op_layout.addStretch()
        main_layout.addLayout(op_layout)

        # OK/Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        StaTableLogger.debug("ConditionEditDialog.__init__ completed")

    def refresh_role_combo(self):
        self.role_combo.clear()
        for name in self.role_functions.keys():
            self.role_combo.addItem(name)
        StaTableLogger.debug(f"refresh_role_combo: {len(self.role_functions)} roles")

    def insert_role_function(self):
        func_name = self.role_combo.currentText()
        StaTableLogger.debug(f"insert_role_function: '{func_name}'")
        if not func_name:
            return
        self.condition_edit.insertPlainText(f"{func_name}()")

    def insert_symbol(self, text: str):
        StaTableLogger.debug(f"ConditionEditDialog.insert_symbol: '{text}'")
        self.condition_edit.insertPlainText(text)

    def _on_accept(self):
        """OK button: auto-set provisional title if title is empty"""
        condition_text = self.condition_edit.toPlainText().strip()
        if condition_text:
            # Condition式の先頭20文字を仮Titleに
            first_line = condition_text.split('\n')[0].strip()
            auto_title = first_line[:20] + ("..." if len(first_line) > 20 else "")
        else:
            auto_title = "(untitled condition)"
        self.title_widget.ensure_title(auto_title)
        self.accept()

    def get_condition_text(self) -> str:
        text = self.condition_edit.toPlainText().strip()
        StaTableLogger.debug(f"get_condition_text: length={len(text)}")
        return text

    def get_title(self) -> str:
        title = self.title_widget.get_title()
        StaTableLogger.debug(f"get_title: '{title}'")
        return title