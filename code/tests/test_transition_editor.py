# tests/test_transition_editor.py
"""
遷移編集パッケージの単体テスト
直接実行: python tests/test_transition_editor.py
"""

import sys
import os
import importlib.util

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
gui_dir = os.path.join(project_root, 'statable_gui')
sys.path.insert(0, project_root)
sys.path.insert(0, gui_dir)

PASS = 0
FAIL = 0
FAILED = []

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        FAILED.append(name)
        print(f"  ❌ {name} {detail}")

# データモデルのテスト
def test_draft():
    print("\n--- TransitionDraft ---")
    from statable_gui.transition_editor.draft import TransitionDraft, ConditionEntry, ActionEntry

    draft = TransitionDraft(source="IDLE", event="START")
    check("初期化", draft.source == "IDLE" and draft.event == "START")
    check("空判定", draft.is_empty())

    draft.title = "テスト"
    draft.use_pre_action = True
    draft.pre_action = "CheckSensor"
    draft.pre_result_var = "sensor_ok"
    draft.conditions = [ConditionEntry(priority=1, condition="sensor_ok==1", target="RUNNING", action="Start")]
    draft.actions = [ActionEntry(order=1, action="StartMotor")]
    draft.use_post_action = True
    draft.post_action = "LogTransition"
    check("設定後は空でない", not draft.is_empty())

    data = draft.to_dict()
    restored = TransitionDraft.from_dict(data)
    check("to_dict/from_dict", restored.title == "テスト" and restored.pre_action == "CheckSensor")

    draft.clear()
    check("クリア", draft.is_empty())

# 付帯条件のテスト
def test_guard():
    print("\n--- 付帯条件 ---")
    from statable_gui.transition_editor.draft import TransitionDraft

    draft = TransitionDraft(source="IDLE", event="START")
    draft.use_transition_guard = True
    draft.transition_guard = "motor_started == 1"
    draft.guard_success_target = "RUNNING"
    draft.guard_fail_mode = "target"
    draft.guard_fail_target = "ERROR"
    draft.guard_fail_action = "HandleMotorError"

    check("付帯条件ON", draft.use_transition_guard)
    check("条件式", draft.transition_guard == "motor_started == 1")
    check("成立時遷移先", draft.guard_success_target == "RUNNING")
    check("不成立モード", draft.guard_fail_mode == "target")
    check("不成立時遷移先", draft.guard_fail_target == "ERROR")

# GUIテスト
def test_gui():
    print("\n--- GUI ---")
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        PYSIDE = True
    except ImportError:
        PYSIDE = False

    if not PYSIDE:
        check("PySide6", False, "(利用不可)")
        return

    from statable_gui.transition_editor.draft import TransitionDraft
    from statable_gui.transition_editor.wizard_widget import TransitionWizardWidget
    from statable_gui.transition_editor.edit_widget import TransitionEditWidget
    from statable_gui.transition_editor.dialog import TransitionEditorDialog

    draft = TransitionDraft(source="IDLE", event="START")
    role_functions = ["CheckSensor", "StartMotor", "InitCounter", "HandleError"]
    states = ["IDLE", "RUNNING", "ERROR"]

    # ウィザード
    wizard = TransitionWizardWidget(draft, role_functions, states)
    check("ウィザード作成", wizard is not None)
    check("ウィザード4ステップ", wizard.step_content.count() == 4)
    wizard._go_to_step(3)
    check("ステップ移動", wizard.current_step == 3)
    wizard.reset_to_step(0)
    check("ステップリセット", wizard.current_step == 0)

    # 編集
    edit = TransitionEditWidget(draft, role_functions, states)
    check("編集作成", edit is not None)
    check("編集5タブ", edit.tab_widget.count() == 5)

    # ダイアログ（新規→ウィザード開始）
    new_draft = TransitionDraft(source="IDLE", event="START")
    dialog = TransitionEditorDialog(new_draft, role_functions, states)
    check("新規はウィザード", dialog.mode_tabs.currentIndex() == 0)
    dialog.close()

    # ダイアログ（既存→編集開始）
    existing_draft = TransitionDraft(source="IDLE", event="START")
    existing_draft.title = "既存遷移"
    dialog2 = TransitionEditorDialog(existing_draft, role_functions, states)
    check("既存は編集", dialog2.mode_tabs.currentIndex() == 1)
    dialog2.close()

def run_all():
    global PASS, FAIL, FAILED
    PASS = 0
    FAIL = 0
    FAILED = []

    print("=" * 50)
    print("遷移編集パッケージ 単体テスト")
    print("=" * 50)

    test_draft()
    test_guard()
    test_gui()

    print("\n" + "=" * 50)
    print(f"合格: {PASS}")
    print(f"失敗: {FAIL}")
    if FAILED:
        print("失敗項目:")
        for f in FAILED:
            print(f"  - {f}")
    print("=" * 50)

    if FAIL == 0:
        print("🎉 全テスト成功！")
    else:
        print("❌ 失敗あり")

if __name__ == "__main__":
    run_all()