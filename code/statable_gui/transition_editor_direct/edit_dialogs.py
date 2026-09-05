# statable_gui/transition_editor_direct/edit_dialogs.py
"""
ノード編集ダイアログ
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QLineEdit, QListWidget, QAbstractItemView
)
from PySide6.QtCore import Qt


class BaseEditDialog(QDialog):
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
        self._add_buttons(layout)

    def get_result(self):
        return self.func_combo.currentText(), {}


class TransitionEditDialog(BaseEditDialog):
    def __init__(self, item, states=None, role_functions=None, parent=None):
        super().__init__(item, parent)
        self.setWindowTitle("状態遷移イベント編集")
        self.states = states or []
        self.role_functions = role_functions or []

        layout = QVBoxLayout(self)

        # イベント名
        h0 = QHBoxLayout()
        h0.addWidget(QLabel("イベント:"))
        self.event_label = QLabel(item.params.get('event', item.name))
        h0.addWidget(self.event_label)
        layout.addLayout(h0)

        # 条件式
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("条件式:"))
        self.cond_edit = QLineEdit(item.params.get('condition', ''))
        h1.addWidget(self.cond_edit)
        layout.addLayout(h1)

        # 遷移直前処理
        layout.addWidget(QLabel("遷移直前処理:"))
        self.pre_list = QListWidget()
        self.pre_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.pre_list.setDefaultDropAction(Qt.MoveAction)
        for a in item.params.get('pre_actions', []):
            self.pre_list.addItem(a)
        layout.addWidget(self.pre_list)

        pre_btn = QHBoxLayout()
        add_btn = QPushButton("追加")
        add_btn.clicked.connect(lambda: self.pre_list.addItem(self.role_functions[0] if self.role_functions else ""))
        pre_btn.addWidget(add_btn)
        del_btn = QPushButton("削除")
        del_btn.clicked.connect(lambda: self.pre_list.takeItem(self.pre_list.currentRow()) if self.pre_list.currentRow() >= 0 else None)
        pre_btn.addWidget(del_btn)
        layout.addLayout(pre_btn)

        # 遷移先
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("遷移先:"))
        self.target_combo = QComboBox()
        self.target_combo.setEditable(True)
        self.target_combo.addItems(self.states)
        self.target_combo.setCurrentText(item.params.get('target', ''))
        h2.addWidget(self.target_combo)
        layout.addLayout(h2)

        self._add_buttons(layout)

    def get_result(self):
        condition = self.cond_edit.text()
        pre_actions = [self.pre_list.item(i).text() for i in range(self.pre_list.count())]
        target = self.target_combo.currentText()
        edited = f"{self.event_label.text()}: {condition} → {target}"
        if pre_actions:
            edited += f" (直前:{', '.join(pre_actions)})"
        params = {
            'event': self.event_label.text(),
            'condition': condition,
            'pre_actions': pre_actions,
            'target': target,
        }
        return edited, params