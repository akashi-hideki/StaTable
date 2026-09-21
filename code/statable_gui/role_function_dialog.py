"""
statable_gui/role_function_dialog.py
Role function create / edit dialog.

Version History
---------------
v1.0  - Initial dialog (name / description / return_type / arg1_* /
        arg2_* / title).
v1.5  - Added namespace field; all arguments passed as kwargs (model
        RoleFunction became kw_only=True).
v3.7  - Removed reserved fields (return_type / arg1_* / arg2_*) from
        the UI. Their values were carried forward from the original
        object through `self._original`.
v3.8  - Layout restructured to mirror
        statable_gui/libcntrl/role_function_edit_dialog.py:
          * Top:    QFormLayout (Function name / Namespace /
                    Display name / Description)
          * Middle: three QGroupBox sections with checkable
                    QListWidgets (Used global variables / Used events /
                    Used literals)
          * Bottom: QDialogButtonBox (OK / Cancel)
        Reserved fields are still preserved via _original for XML
        round-trip. New fields used_global_vars / used_events /
        used_literals are persisted.
v3.9  - Namespace field changed from QLineEdit to QComboBox
        (editable). Candidates are supplied by the caller through
        `namespace_choices`; custom values remain possible via the
        editable combo box.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QListWidget, QListWidgetItem, QDialogButtonBox, QGroupBox
)
from PySide6.QtCore import Qt

from statable.model import RoleFunction
from .logger import StaTableLogger


class RoleFunctionDialog(QDialog):
    """Dialog for creating / editing role functions.

    [v3.9 - Namespace as combo box]
      The namespace field is now an editable QComboBox populated
      with `namespace_choices`. Users can still type a new
      namespace if needed.

    [v3.8 - Layout restructure]
      Mirrors the structure of
      statable_gui/libcntrl/role_function_edit_dialog.py:

        - Top:    QFormLayout
                    * Function name
                    * Namespace (combo box)
                    * Display name
                    * Description
        - Middle: Three QGroupBox sections, each with a checkable
                  QListWidget:
                    * Used global variables
                    * Used events
                    * Used literals (select from existing)
        - Bottom: QDialogButtonBox (OK / Cancel)

      The reserved signature fields (return_type / arg1_* / arg2_*)
      are NOT shown. Their previous values are carried forward from
      `role_function` so that an XML round-trip remains lossless.

      Callers may pass `global_vars`, `events`, `literals` to
      populate the checkable lists, and `namespace_choices` to
      populate the namespace combo box. If omitted, sections appear
      empty (still visible, so the layout matches exactly).
    """

    def __init__(self, parent=None, role_function=None,
                 global_vars=None, events=None, literals=None,
                 namespace_choices=None):
        super().__init__(parent)
        self.setWindowTitle("Edit role function")
        self.setMinimumWidth(500)

        self._original = role_function
        self._global_vars = list(global_vars or [])
        self._events = list(events or [])
        self._literals = list(literals or [])
        self._namespace_choices = list(namespace_choices or [])

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

        # [v3.9] namespace as editable combo box
        self.namespace_combo = QComboBox()
        self.namespace_combo.setEditable(True)
        self.namespace_combo.setInsertPolicy(QComboBox.NoInsert)
        # First entry: empty (no layer). The user can type freely.
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

        # ---- Bottom: buttons ----
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    @staticmethod
    def _make_check_list(parent_layout, title, items):
        """Build one QGroupBox + checkable QListWidget, add to layout."""
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

        # [v3.9] Set namespace on the combo box. If the value isn't
        #        in the list, add it so the user still sees the
        #        current value.
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
    # OK / Cancel
    # ------------------------------------------------------------------
    def _on_accept(self):
        """OK: auto-set provisional title if title is empty."""
        if not self.title_edit.text().strip():
            auto_title = (
                f"Role function: "
                f"{self.name_edit.text().strip() or '(unnamed)'}")
            self.title_edit.setText(auto_title)
            StaTableLogger.debug(f"Auto title generated: '{auto_title}'")
        self.accept()

    # ------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------
    def get_role_function(self) -> RoleFunction:
        """Return the edited RoleFunction.

        [v3.7]
          Reserved fields (return_type / arg1_* / arg2_*) are not
          edited here; they are carried forward from `_original`.

        [v3.8]
          Used global vars / events / literals collected from the
          checkable lists.

        [v3.9]
          Namespace read from the editable combo box.
        """
        orig = self._original

        # v3.9: read from combo box (works whether selected or typed)
        namespace = self.namespace_combo.currentText().strip()

        return RoleFunction(
            name=self.name_edit.text().strip(),
            namespace=namespace,
            description=self.desc_edit.text().strip(),
            title=self.title_edit.text().strip(),
            # [Reserved] carried forward for XML round-trip
            return_type=orig.return_type if orig else "void",
            arg1_type=orig.arg1_type if orig else "",
            arg1_name=orig.arg1_name if orig else "",
            arg2_type=orig.arg2_type if orig else "",
            arg2_name=orig.arg2_name if orig else "",
            # [v3.8] newly tracked symbol references
            used_global_vars=self._collect_checked(self.global_list),
            used_events=self._collect_checked(self.event_list),
            used_literals=self._collect_checked(self.literal_list),
        )