"""共通UIコンポーネント"""

from typing import Optional, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox, QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QLabel,
    QPushButton, QDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QAbstractItemView, QFormLayout, QDialogButtonBox,
    QSpinBox, QCheckBox
)

from statable.global_defs import GlobalDefinitions, CustomTypeDef, StructMemberDef
from .logger import StaTableLogger


class TitleEditWidget(QWidget):
    """Title入力ウィジェット"""

    def __init__(self, parent=None, title="", placeholder="Label shown in the list (auto-set if empty)"):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel("Title *")
        self.label.setFont(QFont("sans-serif", 10, QFont.Bold))
        layout.addWidget(self.label)

        self.edit = QLineEdit()
        self.edit.setText(title)
        self.edit.setPlaceholderText(placeholder)
        self.edit.setToolTip("Enter the title of this item. If empty, a provisional title is set automatically.")
        layout.addWidget(self.edit, stretch=1)

    def get_title(self) -> str:
        return self.edit.text().strip()

    def set_title(self, title: str):
        self.edit.setText(title)

    def ensure_title(self, auto_title: str) -> str:
        if not self.edit.text().strip():
            self.edit.setText(auto_title)
        return self.edit.text().strip()


class TypeComboBox(QWidget):
    """TypeSelection用コンボボックス"""

    def __init__(self, parent=None, global_defs: Optional[GlobalDefinitions] = None):
        super().__init__(parent)
        self.global_defs = global_defs if global_defs else GlobalDefinitions()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.combo = QComboBox()
        self.combo.setEditable(True)
        self._refresh_types()
        layout.addWidget(self.combo, stretch=1)

        add_btn = QPushButton("Add...")
        add_btn.setToolTip("ユーザー定義TypeをAdd・Edit")
        add_btn.clicked.connect(self._open_type_manager)
        layout.addWidget(add_btn)

    def _refresh_types(self):
        current = self.combo.currentText()
        self.combo.clear()
        basic_types = [
            "uint8_t", "uint16_t", "uint32_t", "uint64_t",
            "int8_t", "int16_t", "int32_t", "int64_t",
            "float", "double", "bool", "char", "void",
            "volatile uint8_t", "volatile uint16_t",
            "volatile uint32_t", "volatile uint64_t",
        ]
        self.combo.addItems(basic_types)
        for ct in self.global_defs.custom_types:
            self.combo.addItem(ct.name)
        if current:
            idx = self.combo.findText(current)
            if idx >= 0:
                self.combo.setCurrentIndex(idx)

    def _open_type_manager(self):
        dlg = TypeManagerDialog(self, self.global_defs)
        dlg.exec()
        self._refresh_types()

    def current_text(self) -> str:
        return self.combo.currentText().strip()

    def set_current_text(self, text: str):
        idx = self.combo.findText(text)
        if idx >= 0:
            self.combo.setCurrentIndex(idx)
        else:
            self.combo.setCurrentText(text)


class GroupComboBox(QWidget):
    """GroupSelection用コンボボックス"""

    def __init__(self, parent=None, groups: Optional[List[str]] = None):
        super().__init__(parent)
        self.groups = groups or []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.combo = QComboBox()
        self.combo.setEditable(True)
        self._refresh_groups()
        layout.addWidget(self.combo, stretch=1)

        add_btn = QPushButton("Add...")
        add_btn.setToolTip("新しいGroupをAdd")
        add_btn.clicked.connect(self._add_group)
        layout.addWidget(add_btn)

    def _refresh_groups(self):
        current = self.combo.currentText()
        self.combo.clear()
        self.combo.addItem("")
        self.combo.addItems(self.groups)
        if current:
            idx = self.combo.findText(current)
            if idx >= 0:
                self.combo.setCurrentIndex(idx)

    def _add_group(self):
        dialog = GroupAddDialog(self)
        if dialog.exec() == QDialog.Accepted:
            new_group = dialog.get_group_name()
            if new_group and new_group not in self.groups:
                self.groups.append(new_group)
                self._refresh_groups()
                self.combo.setCurrentText(new_group)

    def current_text(self) -> str:
        return self.combo.currentText().strip()

    def set_current_text(self, text: str):
        idx = self.combo.findText(text)
        if idx >= 0:
            self.combo.setCurrentIndex(idx)
        else:
            self.combo.setCurrentText(text)


class EventComboBox(QComboBox):
    """イベントSelection用コンボボックス"""

    def __init__(self, parent=None, event_names: Optional[List[str]] = None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.addItem("")
        if event_names:
            self.addItems(event_names)


class StateComboBox(QComboBox):
    """状態Selection用コンボボックス"""

    def __init__(self, parent=None, state_names: Optional[List[str]] = None):
        super().__init__(parent)
        self.setEditable(False)
        self.addItem("")
        if state_names:
            self.addItems(state_names)


class GroupAddDialog(QDialog):
    """GroupAddダイアログ"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GroupAdd")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("新しいGroup名を入力")
        form.addRow("Group名", self.name_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Warning", "Group名を入力してください。")
            return
        self.accept()

    def get_group_name(self) -> str:
        return self.name_edit.text().strip()


class TypeManagerDialog(QDialog):
    """ユーザー定義Type管理ダイアログ"""

    def __init__(self, parent=None, global_defs: Optional[GlobalDefinitions] = None):
        super().__init__(parent)
        self.global_defs = global_defs if global_defs else GlobalDefinitions()
        self.setWindowTitle("ユーザー定義Type管理")
        self.setMinimumSize(800, 500)

        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Title", "Type name", "メンバ数"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.cellDoubleClicked.connect(self._on_double_clicked)
        layout.addWidget(self.table, stretch=1)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_type)
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._edit_type)
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self._delete_type)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

        self._refresh_table()
        StaTableLogger.debug("TypeManagerDialog initialized")

    def _refresh_table(self):
        self.table.setRowCount(0)
        for ct in self.global_defs.custom_types:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(ct.title))
            self.table.setItem(row, 1, QTableWidgetItem(ct.name))
            self.table.setItem(row, 2, QTableWidgetItem(str(len(ct.members))))

    def _get_selected_type(self) -> Optional[CustomTypeDef]:
        row = self.table.currentRow()
        if 0 <= row < len(self.global_defs.custom_types):
            return self.global_defs.custom_types[row]
        return None

    def _on_double_clicked(self, row, col):
        self._edit_type()

    def _add_type(self):
        dlg = TypeEditDialog(self)
        if dlg.exec() == QDialog.Accepted:
            new_type = dlg.get_custom_type()
            if not new_type.name:
                QMessageBox.warning(self, "Warning", "Please enter a type name.")
                return
            if any(t.name == new_type.name for t in self.global_defs.custom_types):
                QMessageBox.warning(self, "Warning", f"型 '{new_type.name}' は既に存在します。")
                return
            self.global_defs.custom_types.append(new_type)
            self._refresh_table()
            StaTableLogger.info(f"Custom type added: {new_type.name}")

    def _edit_type(self):
        target = self._get_selected_type()
        if not target:
            return
        dlg = TypeEditDialog(self, custom_type=target)
        if dlg.exec() == QDialog.Accepted:
            new_type = dlg.get_custom_type()
            if not new_type.name:
                QMessageBox.warning(self, "Warning", "Please enter a type name.")
                return
            target.name = new_type.name
            target.description = new_type.description
            target.title = new_type.title
            target.members = new_type.members
            self._refresh_table()
            StaTableLogger.info(f"Custom type updated: {target.name}")

    def _delete_type(self):
        target = self._get_selected_type()
        if not target:
            return
        reply = QMessageBox.question(
            self, "Confirm", f"型 '{target.title}' を削除しますか？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.global_defs.custom_types.remove(target)
            self._refresh_table()
            StaTableLogger.info(f"Custom type deleted: {target.name}")


class TypeEditDialog(QDialog):
    """ユーザー定義TypeEditダイアログ"""

    def __init__(self, parent=None, custom_type: Optional[CustomTypeDef] = None):
        super().__init__(parent)
        self.custom_type = custom_type if custom_type else CustomTypeDef(name="", title="")
        self.setWindowTitle("ユーザー定義TypeEdit")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self.title_edit = QLineEdit(self.custom_type.title)
        self.title_edit.setPlaceholderText("Label shown in the list (auto-set if empty)")
        form.addRow("Title *", self.title_edit)

        self.name_edit = QLineEdit(self.custom_type.name)
        form.addRow("Type name", self.name_edit)

        self.desc_edit = QLineEdit(self.custom_type.description)
        form.addRow("Description", self.desc_edit)

        layout.addWidget(QLabel("メンバ一覧:"))
        self.member_table = QTableWidget(0, 5)
        self.member_table.setHorizontalHeaderLabels(["Member name", "Type", "Bit width", "Array", "Description"])
        self.member_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.member_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.member_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.member_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.member_table.cellDoubleClicked.connect(self._edit_member)
        layout.addWidget(self.member_table, stretch=1)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("メンバAdd")
        add_btn.clicked.connect(self._add_member)
        edit_btn = QPushButton("メンバEdit")
        edit_btn.clicked.connect(self._edit_member)
        del_btn = QPushButton("メンバDelete")
        del_btn.clicked.connect(self._delete_member)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._refresh_member_table()
        StaTableLogger.debug("TypeEditDialog initialized")

    def _refresh_member_table(self):
        self.member_table.setRowCount(0)
        for m in self.custom_type.members:
            row = self.member_table.rowCount()
            self.member_table.insertRow(row)
            self.member_table.setItem(row, 0, QTableWidgetItem(m.name))
            self.member_table.setItem(row, 1, QTableWidgetItem(m.data_type))
            self.member_table.setItem(row, 2, QTableWidgetItem(str(m.bit_width) if m.bit_width > 0 else "-"))
            self.member_table.setItem(row, 3, QTableWidgetItem(str(m.array_size) if m.array_size > 0 else "-"))
            self.member_table.setItem(row, 4, QTableWidgetItem(m.description))

    def _get_selected_member(self) -> Optional[StructMemberDef]:
        row = self.member_table.currentRow()
        if 0 <= row < len(self.custom_type.members):
            return self.custom_type.members[row]
        return None

    def _add_member(self):
        dlg = StructMemberEditDialog(self)
        if dlg.exec() == QDialog.Accepted:
            member = dlg.get_member()
            if not member.name:
                QMessageBox.warning(self, "Warning", "Please enter a member name.")
                return
            if any(m.name == member.name for m in self.custom_type.members):
                QMessageBox.warning(self, "Warning", f"メンバ '{member.name}' は既に存在します。")
                return
            self.custom_type.members.append(member)
            self._refresh_member_table()
            StaTableLogger.info(f"Member added: {member.name}")

    def _edit_member(self):
        target = self._get_selected_member()
        if not target:
            return
        dlg = StructMemberEditDialog(self, member=target)
        if dlg.exec() == QDialog.Accepted:
            new_member = dlg.get_member()
            if not new_member.name:
                QMessageBox.warning(self, "Warning", "Please enter a member name.")
                return
            target.name = new_member.name
            target.data_type = new_member.data_type
            target.bit_width = new_member.bit_width
            target.description = new_member.description
            target.title = new_member.title
            target.array_size = new_member.array_size
            self._refresh_member_table()
            StaTableLogger.info(f"Member updated: {target.name}")

    def _delete_member(self):
        target = self._get_selected_member()
        if not target:
            return
        self.custom_type.members.remove(target)
        self._refresh_member_table()
        StaTableLogger.info(f"Member deleted: {target.name}")

    def _on_accept(self):
        if not self.title_edit.text().strip():
            self.title_edit.setText(f"型: {self.name_edit.text().strip() or '(unnamed)'}")
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Warning", "Please enter a type name.")
            return
        self.accept()

    def get_custom_type(self) -> CustomTypeDef:
        return CustomTypeDef(
            name=self.name_edit.text().strip(),
            description=self.desc_edit.text().strip(),
            members=list(self.custom_type.members),
            title=self.title_edit.text().strip(),
        )


class StructMemberEditDialog(QDialog):
    """構造体メンバEditダイアログ"""

    def __init__(self, parent=None, member: Optional[StructMemberDef] = None):
        super().__init__(parent)
        self.member = member if member else StructMemberDef(name="", data_type="uint8_t")
        self.setWindowTitle("構造体メンバEdit")
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self.title_edit = QLineEdit(self.member.title)
        self.title_edit.setPlaceholderText("Label shown in the list (auto-set if empty)")
        form.addRow("Title *", self.title_edit)

        self.name_edit = QLineEdit(self.member.name)
        form.addRow("Member name", self.name_edit)

        self.type_combo = QComboBox()
        self.type_combo.setEditable(True)
        self.type_combo.addItems([
            "uint8_t", "uint16_t", "uint32_t", "uint64_t",
            "int8_t", "int16_t", "int32_t", "int64_t",
            "float", "double", "bool", "char",
        ])
        idx = self.type_combo.findText(self.member.data_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        else:
            self.type_combo.setCurrentText(self.member.data_type)
        form.addRow("Type", self.type_combo)

        # ビットフィールド
        self.bitfield_check = QCheckBox("ビットフィールドを使用する")
        self.bitfield_check.setChecked(self.member.bit_width > 0)
        form.addRow("", self.bitfield_check)

        self.bit_width_spin = QSpinBox()
        self.bit_width_spin.setRange(1, 64)
        self.bit_width_spin.setValue(self.member.bit_width if self.member.bit_width > 0 else 1)
        form.addRow("Bit width", self.bit_width_spin)

        # Array
        self.array_check = QCheckBox("Use array")
        self.array_check.setChecked(self.member.array_size > 0)
        form.addRow("", self.array_check)

        self.array_size_spin = QSpinBox()
        self.array_size_spin.setRange(1, 65536)
        self.array_size_spin.setValue(self.member.array_size if self.member.array_size > 0 else 1)
        form.addRow("Array size", self.array_size_spin)

        self.bitfield_check.toggled.connect(self._on_bitfield_toggled)
        self.array_check.toggled.connect(self._on_array_toggled)
        self._on_bitfield_toggled(self.bitfield_check.isChecked())
        self._on_array_toggled(self.array_check.isChecked())

        self.desc_edit = QLineEdit(self.member.description)
        form.addRow("Description", self.desc_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        StaTableLogger.debug("StructMemberEditDialog initialized")

    def _on_bitfield_toggled(self, checked: bool):
        self.bit_width_spin.setEnabled(checked)
        if checked:
            self.array_check.setChecked(False)

    def _on_array_toggled(self, checked: bool):
        self.array_size_spin.setEnabled(checked)
        if checked:
            self.bitfield_check.setChecked(False)

    def _on_accept(self):
        if not self.title_edit.text().strip():
            if self.bitfield_check.isChecked():
                self.title_edit.setText(f"{self.name_edit.text().strip() or '(unnamed)'}:{self.bit_width_spin.value()}")
            elif self.array_check.isChecked():
                self.title_edit.setText(f"{self.name_edit.text().strip() or '(unnamed)'}[{self.array_size_spin.value()}]")
            else:
                self.title_edit.setText(f"メンバ: {self.name_edit.text().strip() or '(unnamed)'}")
        self.accept()

    def get_member(self) -> StructMemberDef:
        bit_width = self.bit_width_spin.value() if self.bitfield_check.isChecked() else 0
        array_size = self.array_size_spin.value() if self.array_check.isChecked() else 0
        return StructMemberDef(
            name=self.name_edit.text().strip(),
            data_type=self.type_combo.currentText().strip(),
            bit_width=bit_width,
            description=self.desc_edit.text().strip(),
            title=self.title_edit.text().strip(),
            array_size=array_size,
        )