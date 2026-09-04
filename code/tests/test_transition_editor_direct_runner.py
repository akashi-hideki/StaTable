# tests/test_transition_editor_direct_runner.py
"""
動作編集D&DダイアログのGUI動作確認（FlowItem対応版）
直接実行: python tests/test_transition_editor_direct_runner.py

操作手順:
1. 「新規動作編集」→ 空のダイアログが開く
2. 左パレットから右フローリストへD&Dで配置
3. ドロップ位置に応じて行が挿入される
4. 項目をダブルクリックで編集
5. OKで結果を確認
"""

import sys
import os
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
gui_dir = os.path.join(project_root, 'statable_gui')
sys.path.insert(0, project_root)
sys.path.insert(0, gui_dir)

logging.basicConfig(level=logging.WARNING)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QLabel, QTextEdit, QHBoxLayout
)
from PySide6.QtCore import Qt

from statable_gui.transition_editor_direct.draft import ActionDraft, FlowItem
from statable_gui.transition_editor_direct.dialog import ActionEditorDialog


class ActionEditorRunner(QMainWindow):
    """動作編集ダイアログのテスト用メインウィンドウ"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("動作編集D&D 動作確認")
        self.setMinimumSize(650, 500)

        self.variables = ["battery_voltage", "system_tick", "temperature"]
        self.flags = ["EVT_POWER_ON_REQ", "EVT_START_REQ"]
        self.role_functions = [
            "CheckSensor", "StartMotor", "InitCounter",
            "HandleError", "LogTransition", "ApplyBrake",
        ]
        self.conditions = [
            "voltage > 800",
            "voltage <= 800",
            "temp < 50",
        ]
        self.states = ["INIT", "IDLE", "RUNNING", "ERROR"]

        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        info = QLabel(
            "動作編集D&Dダイアログの動作確認\n\n"
            "1. 左のパレットから右のフローリストへD&D\n"
            "2. ドロップ位置に応じて行が挿入される\n"
            "3. 項目をダブルクリックで編集\n"
            "4. OKで結果を確認\n"
        )
        layout.addWidget(info)

        btn_layout = QHBoxLayout()

        new_btn = QPushButton("新規動作編集")
        new_btn.setMinimumHeight(40)
        new_btn.clicked.connect(self._open_new)
        btn_layout.addWidget(new_btn)

        existing_btn = QPushButton("既存動作の編集")
        existing_btn.setMinimumHeight(40)
        existing_btn.clicked.connect(self._open_existing)
        btn_layout.addWidget(existing_btn)

        layout.addLayout(btn_layout)

        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setPlaceholderText("編集結果がここに表示されます")
        layout.addWidget(self.result_display)

    def _open_new(self):
        draft = ActionDraft(source="IDLE", event="START")
        dialog = ActionEditorDialog(
            draft, self.variables, self.flags,
            self.role_functions, self.conditions, self.states, self
        )
        if dialog.exec() == ActionEditorDialog.Accepted:
            self._display_result(draft)

    def _open_existing(self):
        draft = ActionDraft(source="RUNNING", event="STOP")
        draft.flow_items = [
            FlowItem(item_type="function", name="ApplyBrake", edited_text="ApplyBrake()"),
            FlowItem(
                item_type="condition",
                name="voltage > 800",
                edited_text="voltage > 800 → IDLE (StopMotor)",
                params={"target": "IDLE", "action": "StopMotor"}
            ),
            FlowItem(item_type="function", name="LogTransition", edited_text="LogTransition()"),
        ]
        draft.default_target = "IDLE"

        dialog = ActionEditorDialog(
            draft, self.variables, self.flags,
            self.role_functions, self.conditions, self.states, self
        )
        if dialog.exec() == ActionEditorDialog.Accepted:
            self._display_result(draft)

    def _display_result(self, draft: ActionDraft):
        lines = ["=== 動作編集結果 ==="]
        lines.append(f"遷移: {draft.source} --[{draft.event}]--> ?")
        lines.append("")
        lines.append("動作フロー:")
        for i, item in enumerate(draft.flow_items, 1):
            lines.append(f"  {i}. [{item.item_type}] {item.display_text()}")
        if not draft.flow_items:
            lines.append("  (空)")
        lines.append("")
        lines.append(f"デフォルト遷移先: {draft.default_target}")
        self.result_display.setPlainText("\n".join(lines))


def main():
    app = QApplication(sys.argv)
    window = ActionEditorRunner()
    window.show()
    print("動作編集D&Dダイアログ 動作確認ウィンドウを表示しました。")
    print("ボタンをクリックしてD&D操作・ダブルクリック編集をテストしてください。")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())