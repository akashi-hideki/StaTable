# tests/test_transition_editor_direct_runner.py
"""
動作編集D&Dダイアログの動作確認テスト
直接実行: python tests/test_transition_editor_direct_runner.py

操作手順:
1. 「新規動作編集」ボタン → 空の動作編集ダイアログが開く
2. 左のパレットから右のフローエリアへドラッグ&ドロップ
   - ロール関数 → 前処理 / 実行 / 後処理ブロック
   - 状態遷移条件 → 条件ブロック
3. 条件ブロック内でD&Dして優先順位を変更
4. デフォルト遷移先をコンボボックスから選択
5. OKで編集結果を確認
6. 「既存動作の編集」ボタン → 設定済みの状態で開く
"""

import sys
import os
import logging

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
gui_dir = os.path.join(project_root, 'statable_gui')

sys.path.insert(0, project_root)
sys.path.insert(0, gui_dir)

# ロガー設定（WARNINGに抑制）
logging.basicConfig(level=logging.WARNING)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QLabel, QTextEdit, QHBoxLayout
)
from PySide6.QtCore import Qt

# 動作編集D&Dパッケージ
from statable_gui.transition_editor_direct.draft import ActionDraft, ConditionBlock
from statable_gui.transition_editor_direct.dialog import ActionEditorDialog


class ActionEditorRunner(QMainWindow):
    """動作編集ダイアログのテスト用メインウィンドウ"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("動作編集D&D 動作確認")
        self.setMinimumSize(650, 500)

        # パレットに表示するサンプルデータ
        self.variables = ["battery_voltage", "system_tick", "temperature"]
        self.flags = ["EVT_POWER_ON_REQ", "EVT_START_REQ", "EVT_STOP_REQ"]
        self.role_functions = [
            "CheckSensor", "StartMotor", "InitCounter",
            "HandleError", "LogTransition", "ApplyBrake",
            "ReleaseBrake", "ResetError",
        ]
        # 状態遷移条件（条件式の例）
        self.conditions = [
            "voltage > 800",
            "voltage <= 800",
            "temp < 50",
            "temp >= 50",
            "StartOk && EVT_START_REQ == 1",
        ]
        self.states = ["INIT", "IDLE", "RUNNING", "ERROR", "CONNECTED"]

        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 説明
        info = QLabel(
            "動作編集D&Dダイアログの動作確認\n\n"
            "■ 操作手順\n"
            "1. 左のパレットから部品をドラッグ\n"
            "2. 右のフローエリアにドロップ\n"
            "   - ロール関数 → 前処理 / 実行 / 後処理\n"
            "   - 状態遷移条件 → 条件ブロック\n"
            "3. 条件ブロック内でD&Dして優先順位を変更\n"
            "4. OKで結果を確認\n"
        )
        layout.addWidget(info)

        # ボタン
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

        # 結果表示
        result_label = QLabel("編集結果:")
        layout.addWidget(result_label)

        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setPlaceholderText("編集結果がここに表示されます")
        layout.addWidget(self.result_display)

    def _open_new(self):
        """新規動作編集（空の状態からD&Dで組み立てる）"""
        draft = ActionDraft(source="IDLE", event="START")
        dialog = ActionEditorDialog(
            draft,
            self.variables,
            self.flags,
            self.role_functions,
            self.conditions,
            self.states,
            self
        )
        if dialog.exec() == ActionEditorDialog.Accepted:
            self._display_result(draft, "新規動作編集")
        else:
            self.result_display.setPlainText("キャンセルされました")

    def _open_existing(self):
        """既存動作の編集（設定済みの状態から編集）"""
        draft = ActionDraft(source="RUNNING", event="STOP")
        draft.pre_actions = ["ApplyBrake"]
        draft.conditions = [
            ConditionBlock(priority=1, condition_expr="voltage > 800", target="IDLE", action="StopMotor"),
            ConditionBlock(priority=2, condition_expr="voltage <= 800", target="ERROR", action="HandleError"),
        ]
        draft.actions = ["StopMotor", "ReleaseBrake"]
        draft.post_actions = ["LogTransition"]
        draft.default_target = "IDLE"

        dialog = ActionEditorDialog(
            draft,
            self.variables,
            self.flags,
            self.role_functions,
            self.conditions,
            self.states,
            self
        )
        if dialog.exec() == ActionEditorDialog.Accepted:
            self._display_result(draft, "既存動作の編集")
        else:
            self.result_display.setPlainText("キャンセルされました")

    def _display_result(self, draft: ActionDraft, title: str):
        """編集結果を表示"""
        lines = []
        lines.append(f"=== {title} 結果 ===")
        lines.append(f"遷移: {draft.source} --[{draft.event}]--> ?")
        lines.append("")

        lines.append("【前処理】")
        for a in draft.pre_actions:
            lines.append(f"  - {a}()")
        if not draft.pre_actions:
            lines.append("  (なし)")

        lines.append("")
        lines.append("【条件】")
        for c in draft.conditions:
            lines.append(f"  [{c.priority}] {c.condition_expr} → {c.target} ({c.action})")
        if not draft.conditions:
            lines.append("  (なし)")
        lines.append(f"  デフォルト: → {draft.default_target}")

        lines.append("")
        lines.append("【実行処理】")
        for a in draft.actions:
            lines.append(f"  - {a}()")
        if not draft.actions:
            lines.append("  (なし)")

        lines.append("")
        lines.append("【後処理】")
        for a in draft.post_actions:
            lines.append(f"  - {a}()")
        if not draft.post_actions:
            lines.append("  (なし)")

        self.result_display.setPlainText("\n".join(lines))


def main():
    app = QApplication(sys.argv)
    window = ActionEditorRunner()
    window.show()
    print("動作編集D&Dダイアログ 動作確認ウィンドウを表示しました。")
    print("ボタンをクリックしてD&D操作をテストしてください。")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())