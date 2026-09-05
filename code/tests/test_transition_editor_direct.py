# tests/test_transition_editor_direct.py
"""
動作編集D&Dパッケージのメソッドテスト
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


def test_data_model():
    print("\n--- データモデル ---")
    from statable_gui.transition_editor_direct.draft import (
        FlowItem, TransitionParams, ActionDraft
    )

    # FlowItem
    item = FlowItem(item_type="function", name="CheckSensor")
    check("FlowItem作成", item.item_type == "function")
    check("表示テキスト", item.display_text() == "CheckSensor")

    # TransitionParams
    tp = TransitionParams(
        event="START",
        condition="voltage > 800",
        pre_actions=["SaveLog", "ClearCounter"],
        target="RUNNING"
    )
    check("TransitionParams", tp.event == "START" and tp.target == "RUNNING")
    check("直前処理", tp.pre_actions == ["SaveLog", "ClearCounter"])

    # ActionDraft
    draft = ActionDraft(source="IDLE", event="START")
    draft.flow_items = [item]
    draft.default_target = "IDLE"
    check("ActionDraft", len(draft.flow_items) == 1)

    data = draft.to_dict()
    restored = ActionDraft.from_dict(data)
    check("to_dict/from_dict", restored.source == "IDLE")


def test_gui_classes():
    print("\n--- GUIクラス ---")
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
    role_functions = ["CheckSensor", "StartMotor", "LogTransition"]
    transition_events = ["START", "STOP"]
    states = ["INIT", "IDLE", "RUNNING", "ERROR"]

    # Palette
    palette = PaletteWidget(role_functions, transition_events)
    check("パレット作成", palette is not None)
    check("関数リスト", palette.function_list.count() == 3)
    check("イベントリスト", palette.event_list.count() == 2)

    # Flow
    flow = FlowWidget(draft, role_functions, states)
    check("フロー作成", flow is not None)
    check("フローリスト", flow.flow_list is not None)
    check("デフォルトコンボ", flow.default_target_combo is not None)

    # Dialog
    dialog = ActionEditorDialog(
        draft, role_functions, transition_events, states
    )
    check("ダイアログ作成", dialog is not None)
    check("コードプレビュー", dialog.code_preview is not None)
    check("タイトル", "動作編集" in dialog.windowTitle())
    dialog.close()


def run_all():
    global PASS, FAIL, FAILED
    PASS = 0
    FAIL = 0
    FAILED = []

    print("=" * 50)
    print("動作編集D&D メソッドテスト")
    print("=" * 50)

    test_data_model()
    test_gui_classes()

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