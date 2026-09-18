# statable_gui/transition_editor_direct/system_global_dialog.py
"""
システムグローバル変数 別画面
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QInputDialog

from .draft import SystemGlobal


class SystemGlobalDialog(QDialog):
    def __init__(self, draft, parent=None):
        super().__init__(parent)
        self.draft = draft
        self.setWindowTitle("システムグローバル変数")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("追加")
        add_btn.clicked.connect(self._add)
        btn_layout.addWidget(add_btn)
        del_btn = QPushButton("削除")
        del_btn.clicked.connect(self._delete)
        btn_layout.addWidget(del_btn)
        layout.addLayout(btn_layout)

        close_btn = QPushButton("閉じる")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self._load()

    def _load(self):
        self.list_widget.clear()
        for g in self.draft.system_globals:
            self.list_widget.addItem(f"{g.name} : {g.type} = {g.initial_value}")

    def _add(self):
        name, ok = QInputDialog.getText(self, "追加", "変数名:")
        if ok and name:
            self.draft.system_globals.append(SystemGlobal(name=name))
            self._load()

    def _delete(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            del self.draft.system_globals[row]
            self._load()