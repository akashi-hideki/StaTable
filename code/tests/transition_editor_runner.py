# tests/test_transition_editor_runner.py
"""
遷移編集ダイアログの単体動作確認テスト
直接実行: python tests/test_transition_editor_runner.py
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
    QLabel, QTextEdit, QMessageBox, QHBoxLayout
)
from PySide6.QtCore import Qt

# 遷移編集パッケージ
from statable_gui.transition_editor.draft import TransitionDraft, ConditionEntry, ActionEntry
from statable_gui.transition_editor.dialog import TransitionEditorDialog


class TransitionEditorRunner(QMainWindow):
    """遷移編集ダイアログのテスト用メインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("遷移編集ダイアログ 動作確認")
        self.setMinimumSize(600, 450)
        
        self.role_functions = [
            "PowerOn", "StartOk", "Start", "Stop", "HandleError",
            "CheckSensor", "StartMotor", "InitCounter", "LogTransition",
            "ApplyBrake", "ReleaseBrake", "ResetError",
        ]
        self.states = ["INIT", "IDLE", "RUNNING", "ERROR", "CONNECTED"]
        
        self._setup_ui()
    
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 説明ラベル
        info = QLabel(
            "遷移編集ダイアログの動作確認\n\n"
            "1. 「新規遷移」→ ウィザードモードで開始\n"
            "2. 「既存遷移の編集」→ 編集モードで開始\n"
            "3. 「複雑な遷移」→ 全機能設定済み\n"
            "4. ドラッグアンドドロップで並べ替え\n"
            "5. 付帯条件（遷移ガード）の設定\n"
            "6. クリアボタンでウィザードへ切替"
        )
        layout.addWidget(info)
        
        # ボタン
        btn_layout = QHBoxLayout()
        
        new_btn = QPushButton("新規遷移")
        new_btn.setMinimumHeight(40)
        new_btn.clicked.connect(self._open_new_transition)
        btn_layout.addWidget(new_btn)
        
        edit_btn = QPushButton("既存遷移")
        edit_btn.setMinimumHeight(40)
        edit_btn.clicked.connect(self._open_existing_transition)
        btn_layout.addWidget(edit_btn)
        
        complex_btn = QPushButton("複雑な遷移")
        complex_btn.setMinimumHeight(40)
        complex_btn.clicked.connect(self._open_complex_transition)
        btn_layout.addWidget(complex_btn)
        
        layout.addLayout(btn_layout)
        
        # 結果表示
        result_label = QLabel("編集結果:")
        layout.addWidget(result_label)
        
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setPlaceholderText("編集結果がここに表示されます")
        layout.addWidget(self.result_display)
    
    def _open_new_transition(self):
        """新規遷移（ウィザードモード開始）"""
        draft = TransitionDraft(source="IDLE", event="START")
        
        dialog = TransitionEditorDialog(
            draft, self.role_functions, self.states, self
        )
        
        if dialog.exec() == TransitionEditorDialog.Accepted:
            self._display_result(draft, "新規遷移")
        else:
            self.result_display.setPlainText("キャンセルされました")
    
    def _open_existing_transition(self):
        """既存遷移（編集モード開始）"""
        draft = TransitionDraft(source="IDLE", event="START")
        draft.title = "開始遷移"
        draft.description = "IDLEからRUNNINGへの遷移"
        draft.use_pre_action = True
        draft.pre_action = "CheckSensor"
        draft.pre_result_var = "sensor_ok"
        draft.conditions = [
            ConditionEntry(priority=1, condition="sensor_ok == 1", target="RUNNING", action="Start"),
        ]
        draft.actions = [
            ActionEntry(order=1, action="StartMotor"),
            ActionEntry(order=2, action="InitCounter"),
        ]
        draft.use_post_action = True
        draft.post_action = "LogTransition"
        
        dialog = TransitionEditorDialog(
            draft, self.role_functions, self.states, self
        )
        
        if dialog.exec() == TransitionEditorDialog.Accepted:
            self._display_result(draft, "既存遷移")
        else:
            self.result_display.setPlainText("キャンセルされました")
    
    def _open_complex_transition(self):
        """複雑な遷移（全機能設定済み）"""
        draft = TransitionDraft(source="RUNNING", event="STOP")
        draft.title = "停止遷移"
        draft.description = "RUNNINGからIDLEへの複雑な遷移"
        
        draft.use_pre_action = True
        draft.pre_action = "ApplyBrake"
        draft.pre_result_var = "brake_ok"
        draft.conditions = [
            ConditionEntry(priority=1, condition="brake_ok == 1", target="IDLE", action="StopMotor"),
            ConditionEntry(priority=2, condition="brake_ok == 0", target="ERROR", action="HandleError"),
        ]
        draft.default_target = "IDLE"
        draft.actions = [
            ActionEntry(order=1, action="StopMotor"),
            ActionEntry(order=2, action="ReleaseBrake"),
        ]
        draft.use_transition_guard = True
        draft.transition_guard = "motor_stopped == 1"
        draft.guard_success_target = "IDLE"
        draft.guard_fail_mode = "target"
        draft.guard_fail_target = "ERROR"
        draft.guard_fail_action = "HandleError"
        draft.use_post_action = True
        draft.post_action = "LogTransition"
        draft.use_fallback = True
        draft.fallback_action = "ResetError"
        
        dialog = TransitionEditorDialog(
            draft, self.role_functions, self.states, self
        )
        
        if dialog.exec() == TransitionEditorDialog.Accepted:
            self._display_result(draft, "複雑な遷移")
        else:
            self.result_display.setPlainText("キャンセルされました")
    
    def _display_result(self, draft: TransitionDraft, title: str):
        """編集結果を表示"""
        lines = []
        lines.append(f"=== {title} 編集結果 ===")
        lines.append(f"遷移: {draft.source} --[{draft.event}]--> ?")
        lines.append(f"タイトル: {draft.title}")
        lines.append(f"説明: {draft.description}")
        lines.append("")
        
        if draft.use_pre_action:
            lines.append(f"前処理: {draft.pre_action}() → {draft.pre_result_var}")
        
        if draft.conditions:
            lines.append("条件:")
            for c in draft.conditions:
                lines.append(f"  [{c.priority}] {c.condition} → {c.target} ({c.action})")
        
        if draft.use_default_condition:
            lines.append(f"デフォルト: → {draft.default_target}")
        
        if draft.actions:
            lines.append("実行処理:")
            for a in draft.actions:
                lines.append(f"  [{a.order}] {a.action}()")
        
        if draft.use_transition_guard:
            lines.append(f"付帯条件: {draft.transition_guard}")
            lines.append(f"  成立時: → {draft.guard_success_target}")
            if draft.guard_fail_mode == "target":
                lines.append(f"  不成立時: → {draft.guard_fail_target} ({draft.guard_fail_action})")
            else:
                lines.append("  不成立時: 現状維持")
        
        if draft.use_post_action:
            lines.append(f"後処理: {draft.post_action}()")
        
        if draft.use_fallback:
            lines.append(f"フォールバック: {draft.fallback_action}()")
        
        self.result_display.setPlainText("\n".join(lines))


def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    window = TransitionEditorRunner()
    window.show()
    print("遷移編集ダイアログ 動作確認ウィンドウを表示しました。")
    print("ボタンをクリックして各モードをテストしてください。")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())