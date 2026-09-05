# tests/test_transition_editor_direct_runner.py
"""
動作編集D&Dダイアログ GUI操作テスト
直接実行: python tests/test_transition_editor_direct_runner.py
"""

import sys
import os
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
gui_dir = os.path.join(project_root, 'statable_gui')
sys.path.insert(0, project_root)
sys.path.insert(0, gui_dir)

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTextEdit

from statable_gui.transition_editor_direct.draft import ActionDraft, FlowItem
from statable_gui.transition_editor_direct.dialog import ActionEditorDialog


class Runner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("動作編集D&D 動作確認")
        self.setMinimumSize(650, 500)

        self.role_functions = ["CheckSensor", "StartMotor", "LogTransition", "SaveLog", "ClearCounter"]
        self.transition_events = ["START", "STOP"]
        self.states = ["INIT", "IDLE", "RUNNING", "ERROR"]

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        new_btn = QPushButton("新規動作編集")
        new_btn.setMinimumHeight(40)
        new_btn.clicked.connect(self._open_new)
        layout.addWidget(new_btn)

        existing_btn = QPushButton("既存動作の編集")
        existing_btn.setMinimumHeight(40)
        existing_btn.clicked.connect(self._open_existing)
        layout.addWidget(existing_btn)

        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        layout.addWidget(self.result_display)

    def _open_new(self):
        draft = ActionDraft(source="IDLE", event="START")
        dialog = ActionEditorDialog(
            draft, self.role_functions, self.transition_events, self.states, self
        )
        if dialog.exec() == ActionEditorDialog.Accepted:
            self._show_result(draft)

    def _open_existing(self):
        draft = ActionDraft(source="IDLE", event="START")
        draft.flow_items.append(FlowItem(item_type="function", name="CheckSensor", edited_text="CheckSensor()"))
        draft.flow_items.append(FlowItem(
            item_type="transition",
            name="START",
            edited_text="START: voltage > 800 → RUNNING",
            params={
                "event": "START",
                "condition": "voltage > 800",
                "pre_actions": ["SaveLog", "ClearCounter"],
                "target": "RUNNING"
            }
        ))
        draft.default_target = "IDLE"

        dialog = ActionEditorDialog(
            draft, self.role_functions, self.transition_events, self.states, self
        )
        if dialog.exec() == ActionEditorDialog.Accepted:
            self._show_result(draft)

    def _show_result(self, draft):
        lines = ["=== 動作編集結果 ==="]
        for item in draft.flow_items:
            lines.append(f"  [{item.item_type}] {item.display_text()}")
        lines.append("")
        lines.append("--- 生成コード ---")
        lines.append(draft.generated_code)
        self.result_display.setPlainText("\n".join(lines))


def main():
    app = QApplication(sys.argv)
    window = Runner()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())