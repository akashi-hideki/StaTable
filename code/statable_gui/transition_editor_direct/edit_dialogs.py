# statable_gui/transition_editor_direct/edit_dialogs.py
"""\nNode edit dialog (else checkbox support, condition builder support)\n"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QLineEdit, QListWidget, QAbstractItemView, QCheckBox
)
from PySide6.QtCore import Qt


class BaseEditDialog(QDialog):
    def __init__(self, item, parent=None):
        super().__init__(parent)
        self.item = item
        self.setMinimumWidth(400)

    def _add_buttons(self, layout):
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)


class FunctionEditDialog(BaseEditDialog):
    def __init__(self, item, role_functions=None, parent=None):
        super().__init__(item, parent)
        self.setWindowTitle("Edit role function")
        self.role_functions = role_functions or []

        layout = QVBoxLayout(self)
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Function name:"))
        self.func_combo = QComboBox()
        self.func_combo.setEditable(True)
        self.func_combo.addItems(self.role_functions)
        self.func_combo.setCurrentText(item.name)
        h1.addWidget(self.func_combo)
        layout.addLayout(h1)
        self._add_buttons(layout)

    def get_result(self):
        return self.func_combo.currentText(), {}


class TransitionEditDialog(BaseEditDialog):
    def __init__(self, item, states=None, role_functions=None, global_defs=None, state_machine=None, parent=None):
        super().__init__(item, parent)
        self.setWindowTitle("Edit state transition event")
        self.states = states or []
        self.role_functions = role_functions or []
        self.global_defs = global_defs
        self.state_machine = state_machine

        layout = QVBoxLayout(self)

        h0 = QHBoxLayout()
        h0.addWidget(QLabel("Event:"))
        self.event_label = QLabel(item.params.get('event', item.name))
        h0.addWidget(self.event_label)
        layout.addLayout(h0)

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Condition:"))
        self.cond_edit = QLineEdit(item.params.get('condition', ''))
        h1.addWidget(self.cond_edit)

        cond_builder_btn = QPushButton("ConditionをEdit...")
        cond_builder_btn.clicked.connect(self._open_condition_builder)
        h1.addWidget(cond_builder_btn)
        layout.addLayout(h1)

        layout.addWidget(QLabel("Pre-transition processing:"))
        self.pre_list = QListWidget()
        self.pre_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.pre_list.setDefaultDropAction(Qt.MoveAction)
        for a in item.params.get('pre_actions', []):
            self.pre_list.addItem(a)
        layout.addWidget(self.pre_list)

        pre_btn = QHBoxLayout()
        add_pre_btn = QPushButton("Add")
        add_pre_btn.clicked.connect(self._add_pre)
        pre_btn.addWidget(add_pre_btn)
        del_pre_btn = QPushButton("Delete")
        del_pre_btn.clicked.connect(self._del_pre)
        pre_btn.addWidget(del_pre_btn)
        layout.addLayout(pre_btn)

        self.has_else_check = QCheckBox("Use else condition")
        self.has_else_check.setChecked(item.params.get('has_else', True))
        layout.addWidget(self.has_else_check)

        h3 = QHBoxLayout()
        h3.addWidget(QLabel("else target:"))
        self.else_target_combo = QComboBox()
        self.else_target_combo.setEditable(True)
        self.else_target_combo.addItems(self.states)
        self.else_target_combo.setCurrentText(item.params.get('else_target', ''))
        h3.addWidget(self.else_target_combo)
        layout.addLayout(h3)

        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Target:"))
        self.target_combo = QComboBox()
        self.target_combo.setEditable(True)
        self.target_combo.addItems(self.states)
        self.target_combo.setCurrentText(item.params.get('target', ''))
        h2.addWidget(self.target_combo)
        layout.addLayout(h2)

        self._add_buttons(layout)

    def _add_pre(self):
        if self.role_functions:
            self.pre_list.addItem(self.role_functions[0])

    def _del_pre(self):
        row = self.pre_list.currentRow()
        if row >= 0:
            self.pre_list.takeItem(row)

    def _open_condition_builder(self):
        from statable_gui.condition_builder_dialog import ConditionBuilderDialog
        dlg = ConditionBuilderDialog(
            condition=self.cond_edit.text(),
            global_defs=self.global_defs,
            state_machine=self.state_machine,
            parent=self
        )
        if dlg.exec() == QDialog.Accepted:
            self.cond_edit.setText(dlg.get_condition_text())

    def get_result(self):
        condition = self.cond_edit.text()
        pre_actions = [self.pre_list.item(i).text() for i in range(self.pre_list.count())]
        target = self.target_combo.currentText()
        has_else = self.has_else_check.isChecked()
        else_target = self.else_target_combo.currentText() if has_else else ""

        edited = f"{self.event_label.text()}: {condition} → {target}"
        if pre_actions:
            edited += f" (直前:{', '.join(pre_actions)})"
        if has_else:
            edited += f" [else→{else_target}]" if else_target else " [else]"

        params = {
            'event': self.event_label.text(),
            'condition': condition,
            'pre_actions': pre_actions,
            'target': target,
            'has_else': has_else,
            'else_target': else_target,
            'else_actions': [],   # Future support
        }
        return edited, params