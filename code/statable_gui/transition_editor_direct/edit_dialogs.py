# statable_gui/transition_editor_direct/edit_dialogs.py
"""
パーツ編集ダイアログ
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QLineEdit, QListWidget, QAbstractItemView
)
from PySide6.QtCore import Qt


class BaseEditDialog(QDialog):
    """材料編集の基底ダイアログ"""

    def __init__(self, item, parent=None):
        super().__init__(parent)
        self.item = item
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


class FunctionEditDialog(BaseEditDialog):
    """ロール関数編集"""

    def __init__(self, item, role_functions=None, parent=None):
        super().__init__(item, parent)
        self.setWindowTitle("ロール関数編集")
        self.role_functions = role_functions or []

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
        self.arg1_edit = QLineEdit(item.params.get('arg1', ''))
        h2.addWidget(self.arg1_edit)
        layout.addLayout(h2)

        h3 = QHBoxLayout()
        h3.addWidget(QLabel("引数2:"))
        self.arg2_edit = QLineEdit(item.params.get('arg2', ''))
        h3.addWidget(self.arg2_edit)
        layout.addLayout(h3)

        self._add_buttons(layout)

    def get_result(self):
        """編集結果を取得"""
        func = self.func_combo.currentText()
        args = [a for a in [self.arg1_edit.text(), self.arg2_edit.text()] if a]
        edited = f"{func}({', '.join(args)})" if args else f"{func}()"
        params = {}
        if self.arg1_edit.text():
            params['arg1'] = self.arg1_edit.text()
        if self.arg2_edit.text():
            params['arg2'] = self.arg2_edit.text()
        return edited, params


class TransitionEditDialog(BaseEditDialog):
    """状態遷移イベント編集"""

    def __init__(self, item, states=None, role_functions=None, parent=None):
        super().__init__(item, parent)
        self.setWindowTitle("状態遷移イベント編集")
        self.states = states or []
        self.role_functions = role_functions or []

        # 既存paramsを読み込み
        self.event = item.params.get('event', item.name)
        self.condition = item.params.get('condition', '')
        self.pre_actions = item.params.get('pre_actions', [])
        self.target = item.params.get('target', '')

        layout = QVBoxLayout(self)

        # イベント名
        h0 = QHBoxLayout()
        h0.addWidget(QLabel("イベント:"))
        self.event_label = QLabel(self.event)
        h0.addWidget(self.event_label)
        layout.addLayout(h0)

        # 条件式
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("条件式:"))
        self.cond_edit = QLineEdit(self.condition)
        h1.addWidget(self.cond_edit)
        layout.addLayout(h1)

        # 遷移直前処理リスト
        layout.addWidget(QLabel("遷移直前処理:"))
        self.pre_list = QListWidget()
        self.pre_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.pre_list.setDefaultDropAction(Qt.MoveAction)
        self.pre_list.setMaximumHeight(100)
        for a in self.pre_actions:
            self.pre_list.addItem(a)
        layout.addWidget(self.pre_list)

        pre_btn_layout = QHBoxLayout()
        add_pre_btn = QPushButton("追加")
        add_pre_btn.clicked.connect(self._add_pre_action)
        pre_btn_layout.addWidget(add_pre_btn)
        del_pre_btn = QPushButton("削除")
        del_pre_btn.clicked.connect(self._delete_pre_action)
        pre_btn_layout.addWidget(del_pre_btn)
        layout.addLayout(pre_btn_layout)

        # 遷移先
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("遷移先:"))
        self.target_combo = QComboBox()
        self.target_combo.setEditable(True)
        self.target_combo.addItems(self.states)
        self.target_combo.setCurrentText(self.target)
        h2.addWidget(self.target_combo)
        layout.addLayout(h2)

        self._add_buttons(layout)

    def _add_pre_action(self):
        if self.role_functions:
            self.pre_list.addItem(self.role_functions[0])

    def _delete_pre_action(self):
        row = self.pre_list.currentRow()
        if row >= 0:
            self.pre_list.takeItem(row)

    def get_result(self):
        condition = self.cond_edit.text()
        pre_actions = []
        for i in range(self.pre_list.count()):
            pre_actions.append(self.pre_list.item(i).text())
        target = self.target_combo.currentText()

        edited = f"{self.event}: {condition} → {target}"
        if pre_actions:
            edited += f" (直前:{', '.join(pre_actions)})"

        params = {
            'event': self.event,
            'condition': condition,
            'pre_actions': pre_actions,
            'target': target,
        }
        return edited, params