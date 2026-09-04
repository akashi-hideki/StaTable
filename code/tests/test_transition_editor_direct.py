# tests/test_transition_editor_direct.py
"""
動作編集D&Dパッケージの単体テスト（FlowItem対応版）
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
    print("\n--- FlowItem / ActionDraft ---")
    from statable_gui.transition_editor_direct.draft import FlowItem, ActionDraft

    item1 = FlowItem(item_type="function", name="CheckSensor")
    item2 = FlowItem(item_type="condition", name="voltage > 800")
    item2.params = {"target": "RUNNING", "action": "Start"}
    item2.edited_text = "voltage > 800 → RUNNING (Start)"

    check("FlowItem作成", item1.item_type == "function" and item1.name == "CheckSensor")
    check("表示テキスト", item2.display_text() == "voltage > 800 → RUNNING (Start)")

    draft = ActionDraft(source="IDLE", event="START")
    draft.flow_items = [item1, item2]
    draft.default_target = "IDLE"

    check("フロー項目数", len(draft.flow_items) == 2)
    check("デフォルト遷移先", draft.default_target == "IDLE")

    data = draft.to_dict()
    restored = ActionDraft.from_dict(data)
    check("to_dict/from_dict", len(restored.flow_items) == 2)
    check("復元された名前", restored.flow_items[1].name == "voltage > 800")


def test_gui_creation():
    print("\n--- GUIウィジェット作成 ---")
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
    flags = ["EVT_POWER_ON_REQ"]
    role_functions = ["CheckSensor", "StartMotor", "InitCounter", "LogTransition"]
    conditions = ["voltage > 800", "voltage <= 800"]
    states = ["INIT", "IDLE", "RUNNING", "ERROR"]

    palette = PaletteWidget(variables, flags, role_functions, conditions)
    check("パレット作成", palette is not None)
    check("パレット変数", palette.variable_list.count() == 2)
    check("パレット関数", palette.function_list.count() == 4)
    check("パレット条件", palette.condition_list.count() == 2)

    flow = FlowWidget(draft, role_functions, states)
    check("フロー作成", flow is not None)
    check("フローリスト", flow.flow_list is not None)
    check("デフォルトコンボ", flow.default_target_combo is not None)

    dialog = ActionEditorDialog(
        draft, variables, flags, role_functions, conditions, states
    )
    check("ダイアログ作成", dialog is not None)
    check("タイトル", "動作編集" in dialog.windowTitle())
    dialog.close()


def run_all():
    global PASS, FAIL, FAILED
    PASS = 0
    FAIL = 0
    FAILED = []

    print("=" * 50)
    print("動作編集D&D（材料編集方式）単体テスト")
    print("=" * 50)

    test_draft()
    test_gui_creation()

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