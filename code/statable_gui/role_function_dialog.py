"""
statable_gui/role_function_dialog.py
Role function create / edit dialog.

Version History
---------------
v1.0  - Initial dialog.
v1.5  - Added namespace field.
v3.7  - Removed reserved fields from the UI.
v3.8  - Layout restructured (3 QGroupBox sections).
v3.9  - Namespace field as editable QComboBox.

[R-7]
  - Added "+ New Literal" button below the "Used literals" group.
    Opens NewLiteralDialog, adds the new LiteralDefinition to the
    shared literal_library, and appends it (pre-checked) to the
    list widget.
  - New constructor argument `literal_library=None`. When None, the
    button is hidden and behavior is unchanged (backward compat).
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QListWidget, QListWidgetItem, QDialogButtonBox, QGroupBox,
    QPushButton, QMessageBox,
)
from PySide6.QtCore import Qt

from statable.model import RoleFunction
from .logger import StaTableLogger

try:
    from .literal_definition_dialog import NewLiteralDialog
except ImportError:
    from literal_definition_dialog import NewLiteralDialog


class RoleFunctionDialog(QDialog):
    """Dialog for creating / editing role functions."""

    def __init__(self, parent=None, role_function=None,
                 global_vars=None, events=None, literals=None,
                 namespace_choices=None,
                 literal_library=None):
        super().__init__(parent)
        self.setWindowTitle("Edit role function")
        self.setMinimumWidth(500)

        self._original = role_function
        self._global_vars = list(global_vars or [])
        self._events = list(events or [])
        self._literals = list(literals or [])
        self._namespace_choices = list(namespace_choices or [])
        # [R-7] shared library for creating new literals
        self._literal_library = literal_library

        self._setup_ui()
        self._load_data()
        StaTableLogger.debug("RoleFunctionDialog initialized")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # ---- Top: form fields ----
        form = QFormLayout()

        self.name_edit = QLineEdit()
        form.addRow("Function name:", self.name_edit)

        self.namespace_combo = QComboBox()
        self.namespace_combo.setEditable(True)
        self.namespace_combo.setInsertPolicy(QComboBox.NoInsert)
        self.namespace_combo.addItem("")
        for ns in self._namespace_choices:
            if ns and ns != "":
                self.namespace_combo.addItem(ns)
        self.namespace_combo.setToolTip(
            "Namespace (layer name / feature group name).\n"
            "If specified, it can be referenced as 'Driver.Init'.\n"
            "If empty, it is treated as having no layer ('Init').\n"
            "Select from the list, or type a new value."
        )
        form.addRow("Namespace:", self.namespace_combo)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText(
            "Label shown in the list (auto-set if empty)")
        form.addRow("Display name:", self.title_edit)

        self.desc_edit = QLineEdit()
        form.addRow("Description:", self.desc_edit)

        main_layout.addLayout(form)

        # ---- Middle: three checkbox groups ----
        self.global_list = self._make_check_list(
            main_layout, "Used global variables", self._global_vars)
        self.event_list = self._make_check_list(
            main_layout, "Used events", self._events)
        self.literal_list = self._make_check_list(
            main_layout, "Used literals (select from existing)",
            self._literals)

        # [R-7] "+ New Literal" button (only when library available)
        if self._literal_library is not None:
            btn_row = QHBoxLayout()
            btn_row.addStretch()
            self.new_literal_btn = QPushButton("+ New Literal")
            self.new_literal_btn.setToolTip(
                "Create a new literal and add it to the list above")
            self.new_literal_btn.clicked.connect(self._on_new_literal)
            btn_row.addWidget(self.new_literal_btn)
            main_layout.addLayout(btn_row)

        # ---- Bottom: buttons ----
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    @staticmethod
    def _make_check_list(parent_layout, title, items):
        group = QGroupBox(title)
        group_layout = QVBoxLayout(group)
        lst = QListWidget()
        lst.setSelectionMode(QListWidget.NoSelection)
        for text in items:
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            lst.addItem(item)
        group_layout.addWidget(lst)
        parent_layout.addWidget(group)
        return lst

    # ------------------------------------------------------------------
    # Data binding
    # ------------------------------------------------------------------
    def _load_data(self):
        rf = self._original
        if rf is None:
            return

        self.name_edit.setText(rf.name)
        self.title_edit.setText(rf.title)
        self.desc_edit.setText(rf.description)

        ns = getattr(rf, 'namespace', '') or ''
        idx = self.namespace_combo.findText(ns)
        if idx >= 0:
            self.namespace_combo.setCurrentIndex(idx)
        else:
            self.namespace_combo.setEditText(ns)

        self._check_items(
            self.global_list,
            getattr(rf, 'used_global_vars', []) or [])
        self._check_items(
            self.event_list,
            getattr(rf, 'used_events', []) or [])
        self._check_items(
            self.literal_list,
            getattr(rf, 'used_literals', []) or [])

    @staticmethod
    def _check_items(lst, selected):
        sel = set(selected)
        for i in range(lst.count()):
            item = lst.item(i)
            if item.text() in sel:
                item.setCheckState(Qt.Checked)

    @staticmethod
    def _collect_checked(lst):
        result = []
        for i in range(lst.count()):
            item = lst.item(i)
            if item.checkState() == Qt.Checked:
                result.append(item.text())
        return result

    # ------------------------------------------------------------------
    # [R-7] New literal handler
    # ------------------------------------------------------------------
    def _on_new_literal(self):
        if self._literal_library is None:
            return

        dlg = NewLiteralDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return

        lit = dlg.get_literal()
        try:
            self._literal_library.add(lit)
        except ValueError:
            QMessageBox.warning(
                self, "Warning",
                f"A literal named '{lit.name}' already exists.")
            return

        # Append to the list widget, pre-checked
        item = QListWidgetItem(lit.name)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked)
        self.literal_list.addItem(item)
        StaTableLogger.info(f"New literal created: {lit.name}")

    # ------------------------------------------------------------------
    # OK / Cancel
    # ------------------------------------------------------------------
    def _on_accept(self):
        if not self.title_edit.text().strip():
            auto_title = (
                f"Role function: "
                f"{self.name_edit.text().strip() or '(unnamed)'}")
            self.title_edit.setText(auto_title)
        self.accept()

    # ------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------
    def get_role_function(self) -> RoleFunction:
        orig = self._original
        namespace = self.namespace_combo.currentText().strip()

        return RoleFunction(
            name=self.name_edit.text().strip(),
            namespace=namespace,
            description=self.desc_edit.text().strip(),
            title=self.title_edit.text().strip(),
            return_type=orig.return_type if orig else "void",
            arg1_type=orig.arg1_type if orig else "",
            arg1_name=orig.arg1_name if orig else "",
            arg2_type=orig.arg2_type if orig else "",
            arg2_name=orig.arg2_name if orig else "",
            used_global_vars=self._collect_checked(self.global_list),
            used_events=self._collect_checked(self.event_list),
            used_literals=self._collect_checked(self.literal_list),
        )