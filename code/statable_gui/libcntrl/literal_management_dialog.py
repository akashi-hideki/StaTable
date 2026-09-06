# statable_gui/libcntrl/literal_management_dialog.py
"""
リテラル管理ダイアログ（表形式・編集修正版）
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QLineEdit, QFormLayout, QDialogButtonBox,
    QHeaderView
)
from PySide6.QtCore import Qt

from .literal_library import LiteralLibrary, LiteralDefinition


class LiteralManagementDialog(QDialog):
    """共有リテラルの管理ダイアログ（表形式）"""

    def __init__(self, literal_library: LiteralLibrary, parent=None):
        super().__init__(parent)
        self.literal_library = literal_library

        self.setWindowTitle("リテラル管理")
        self.setMinimumSize(600, 400)

        self._setup_ui()
        self._load_table()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["名前", "値", "型", "説明"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        main_layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("追加")
        add_btn.clicked.connect(self._add_literal)
        edit_btn = QPushButton("編集")
        edit_btn.clicked.connect(self._edit_literal)
        delete_btn = QPushButton("削除")
        delete_btn.clicked.connect(self._delete_literal)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        main_layout.addLayout(btn_layout)

        close_btn = QPushButton("閉じる")
        close_btn.clicked.connect(self.accept)
        main_layout.addWidget(close_btn)

    def _load_table(self):
        self.table.setRowCount(0)
        for lit in self.literal_library.list_all():
            row = self.table.rowCount()
            self.table.insertRow(row)

            name_item = QTableWidgetItem(lit.name)
            name_item.setData(Qt.UserRole, lit.name)
            self.table.setItem(row, 0, name_item)

            self.table.setItem(row, 1, QTableWidgetItem(lit.value))
            self.table.setItem(row, 2, QTableWidgetItem(lit.literal_type))
            self.table.setItem(row, 3, QTableWidgetItem(lit.description))

    def _get_selected_literal_name(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if item:
            return item.data(Qt.UserRole)
        return None

    def _add_literal(self):
        dialog = LiteralEditDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            lit = dialog.get_literal()
            try:
                self.literal_library.add(lit)
                self._load_table()
            except ValueError as e:
                QMessageBox.warning(self, "警告", str(e))

    def _edit_literal(self):
        name = self._get_selected_literal_name()
        if name is None:
            QMessageBox.information(self, "情報", "編集するリテラルを選択してください。")
            return

        lit = self.literal_library.get(name)
        if lit is None:
            return

        dialog = LiteralEditDialog(literal=lit, parent=self)
        if dialog.exec() == QDialog.Accepted:
            new_lit = dialog.get_literal()

            # 編集時は常に旧エントリを削除してから追加する
            self.literal_library.remove(name)
            try:
                self.literal_library.add(new_lit)
                self._load_table()
            except ValueError as e:
                # 失敗した場合は元に戻す
                self.literal_library.add(lit)
                QMessageBox.warning(self, "警告", str(e))

    def _delete_literal(self):
        name = self._get_selected_literal_name()
        if name is None:
            QMessageBox.information(self, "情報", "削除するリテラルを選択してください。")
            return

        ret = QMessageBox.warning(
            self,
            "確認",
            f"リテラル '{name}' を削除しますか？\n"
            "このリテラルを使用している遷移条件がある場合は、\n"
            "該当の条件式からも削除する必要があります。",
            QMessageBox.Yes | QMessageBox.No
        )
        if ret == QMessageBox.Yes:
            self.literal_library.remove(name)
            self._load_table()


class LiteralEditDialog(QDialog):
    """リテラルの追加・編集用ダイアログ"""

    def __init__(self, literal: LiteralDefinition = None, parent=None):
        super().__init__(parent)
        self.literal = literal

        self.setWindowTitle("リテラル編集" if literal else "リテラル追加")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        if literal:
            self.name_edit.setText(literal.name)
        form.addRow("名前:", self.name_edit)

        self.value_edit = QLineEdit()
        if literal:
            self.value_edit.setText(literal.value)
        form.addRow("値:", self.value_edit)

        self.type_edit = QLineEdit("int")
        if literal:
            self.type_edit.setText(literal.literal_type)
        form.addRow("型:", self.type_edit)

        self.desc_edit = QLineEdit()
        if literal:
            self.desc_edit.setText(literal.description)
        form.addRow("説明:", self.desc_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "名前を入力してください。")
            return
        self.accept()

    def get_literal(self) -> LiteralDefinition:
        return LiteralDefinition(
            name=self.name_edit.text().strip(),
            value=self.value_edit.text().strip(),
            literal_type=self.type_edit.text().strip() or "int",
            description=self.desc_edit.text().strip(),
        )