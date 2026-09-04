# tests/test_transition_editor_direct.py
"""
動作編集D&Dパッケージの単体テスト
直接実行: python tests/test_transition_editor_direct.py
"""

import sys
import os

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


def test_draft():
    print("\n--- ActionDraft ---")
    from statable_gui.transition_editor_direct.draft import ActionDraft, ConditionBlock

    draft = ActionDraft(source="IDLE", event="START")
    check("初期化", draft.source == "IDLE" and draft.event == "START")

    draft.pre_actions.append("CheckSensor")
    draft.conditions.append(ConditionBlock(priority=1, condition_expr="voltage > 800", target="RUNNING", action="Start"))
    draft.actions.append("StartMotor")
    draft.post_actions.append("LogTransition")
    draft.default_target = "IDLE"

    check("前処理", draft.pre_actions == ["CheckSensor"])
    check("条件", len(draft.conditions) == 1)
    check("条件式", draft.conditions[0].condition_expr == "voltage > 800")
    check("遷移先", draft.conditions[0].target == "RUNNING")
    check("実行処理", draft.actions == ["StartMotor"])
    check("後処理", draft.post_actions == ["LogTransition"])

    data = draft.to_dict()
    restored = ActionDraft.from_dict(data)
    check("to_dict/from_dict", restored.conditions[0].condition_expr == "voltage > 800")

    draft.clear()
    check("クリア", len(draft.pre_actions) == 0 and len(draft.conditions) == 0)


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

    from statable_gui.transition_editor_direct.draft import ActionDraft
    from statable_gui.transition_editor_direct.palette_widget import PaletteWidget
    from statable_gui.transition_editor_direct.flow_widget import FlowWidget
    from statable_gui.transition_editor_direct.dialog import ActionEditorDialog

    draft = ActionDraft(source="IDLE", event="START")

    variables = ["battery_voltage", "system_tick"]
    flags = ["EVT_POWER_ON_REQ", "EVT_START_REQ"]
    role_functions = ["CheckSensor", "StartMotor", "InitCounter", "HandleError", "LogTransition"]
    conditions = ["voltage > 800", "voltage <= 800", "temp < 50"]
    states = ["INIT", "IDLE", "RUNNING", "ERROR"]

    # パレット
    palette = PaletteWidget(variables, flags, role_functions, conditions)
    check("パレット作成", palette is not None)
    check("パレット変数", palette.variable_list.count() == 2)
    check("パレットフラグ", palette.flag_list.count() == 2)
    check("パレット関数", palette.function_list.count() == 5)
    check("パレット条件", palette.condition_list.count() == 3)

    # フロー
    flow = FlowWidget(draft, states)
    check("フロー作成", flow is not None)
    check("前処理リスト", flow.pre_list is not None)
    check("条件リスト", flow.condition_list is not None)
    check("実行リスト", flow.action_list is not None)
    check("後処理リスト", flow.post_list is not None)

    # ダイアログ
    dialog = ActionEditorDialog(draft, variables, flags, role_functions, conditions, states)
    check("ダイアログ作成", dialog is not None)
    check("ダイアログタイトル", "動作編集" in dialog.windowTitle())
    dialog.close()


def run_all():
    global PASS, FAIL, FAILED
    PASS = 0
    FAIL = 0
    FAILED = []

    print("=" * 50)
    print("動作編集D&Dパッケージ 単体テスト")
    print("=" * 50)

    test_draft()
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