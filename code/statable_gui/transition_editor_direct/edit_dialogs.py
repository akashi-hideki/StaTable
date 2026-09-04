# statable_gui/transition_editor_direct/edit_dialogs.py
"""
材料タイプ別の編集ダイアログ
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QLineEdit
)


class FlowItemEditDialog(QDialog):
    """材料編集の基底ダイアログ"""

    def __init__(self, item, role_functions=None, states=None, parent=None):
        super().__init__(parent)
        self.item = item
        self.role_functions = role_functions or []
        self.states = states or []
        self.setWindowTitle("材料の編集")
        self.setMinimumWidth(350)

    def _add_buttons(self, layout):
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)


class FunctionEditDialog(FlowItemEditDialog):
    """ロール関数の編集"""

    def __init__(self, item, role_functions=None, parent=None):
        super().__init__(item, role_functions=role_functions, parent=parent)
        self.setWindowTitle("ロール関数の編集")

        layout = QVBoxLayout(self)

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("関数名:"))
        self.func_combo = QComboBox()
        self.func_combo.setEditable(True)
        self.func_combo.addItems(self.role_functions)
        self.func_combo.setCurrentText(item.name)
        h1.addWidget(self.func_combo)
        layout.addLayout(h1)

        h2 = QHBoxLayout()
        h2.addWidget(QLabel("引数1:"))
        self.arg1_edit = QLineEdit()
        self.arg1_edit.setText(item.params.get('arg1', ''))
        h2.addWidget(self.arg1_edit)
        layout.addLayout(h2)

        h3 = QHBoxLayout()
        h3.addWidget(QLabel("引数2:"))
        self.arg2_edit = QLineEdit()
        self.arg2_edit.setText(item.params.get('arg2', ''))
        h3.addWidget(self.arg2_edit)
        layout.addLayout(h3)

        self._add_buttons(layout)

    def get_result(self):
        """編集結果を取得"""
        func_name = self.func_combo.currentText()
        arg1 = self.arg1_edit.text()
        arg2 = self.arg2_edit.text()

        params = {}
        if arg1:
            params['arg1'] = arg1
        if arg2:
            params['arg2'] = arg2

        edited = func_name
        if arg1 or arg2:
            args = [a for a in [arg1, arg2] if a]
            edited = f"{func_name}({', '.join(args)})"

        return edited, params


class ConditionEditDialog(FlowItemEditDialog):
    """状態遷移条件の編集"""

    def __init__(self, item, states=None, role_functions=None, parent=None):
        super().__init__(item, role_functions=role_functions, parent=parent)
        self.setWindowTitle("状態遷移条件の編集")

        layout = QVBoxLayout(self)

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("条件式:"))
        self.cond_edit = QLineEdit()
        self.cond_edit.setText(item.name)
        h1.addWidget(self.cond_edit)
        layout.addLayout(h1)

        h2 = QHBoxLayout()
        h2.addWidget(QLabel("遷移先:"))
        self.target_combo = QComboBox()
        self.target_combo.setEditable(True)
        self.target_combo.addItems(self.states)
        if 'target' in item.params:
            self.target_combo.setCurrentText(item.params['target'])
        h2.addWidget(self.target_combo)
        layout.addLayout(h2)

        h3 = QHBoxLayout()
        h3.addWidget(QLabel("アクション:"))
        self.action_combo = QComboBox()
        self.action_combo.setEditable(True)
        self.action_combo.addItems(self.role_functions)
        if 'action' in item.params:
            self.action_combo.setCurrentText(item.params['action'])
        h3.addWidget(self.action_combo)
        layout.addLayout(h3)

        self._add_buttons(layout)

    def get_result(self):
        """編集結果を取得"""
        cond = self.cond_edit.text()
        target = self.target_combo.currentText()
        action = self.action_combo.currentText()

        params = {'target': target}
        if action:
            params['action'] = action

        edited = cond
        if target:
            edited = f"{cond} → {target}"
        if action:
            edited = f"{edited} ({action})"

        return edited, params


class VariableEditDialog(FlowItemEditDialog):
    """グローバル変数の編集"""

    def __init__(self, item, parent=None):
        super().__init__(item, parent=parent)
        self.setWindowTitle("変数の編集")

        layout = QVBoxLayout(self)

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("変数名:"))
        self.var_edit = QLineEdit()
        self.var_edit.setText(item.name)
        h1.addWidget(self.var_edit)
        layout.addLayout(h1)

        h2 = QHBoxLayout()
        h2.addWidget(QLabel("比較演算子:"))
        self.op_combo = QComboBox()
        self.op_combo.addItems([">", "<", "==", "!=", ">=", "<="])
        if 'op' in item.params:
            self.op_combo.setCurrentText(item.params['op'])
        h2.addWidget(self.op_combo)
        layout.addLayout(h2)

        h3 = QHBoxLayout()
        h3.addWidget(QLabel("比較値:"))
        self.value_edit = QLineEdit()
        self.value_edit.setText(item.params.get('value', ''))
        h3.addWidget(self.value_edit)
        layout.addLayout(h3)

        self._add_buttons(layout)

    def get_result(self):
        """編集結果を取得"""
        var = self.var_edit.text()
        op = self.op_combo.currentText()
        value = self.value_edit.text()

        params = {}
        if op:
            params['op'] = op
        if value:
            params['value'] = value

        edited = var
        if op and value:
            edited = f"{var} {op} {value}"

        return edited, params