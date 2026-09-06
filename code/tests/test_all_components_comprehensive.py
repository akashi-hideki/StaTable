# tests/test_all_components_comprehensive.py
"""
全コンポーネント 包括的静的テスト
- 新規追加ファイル（libcntrl）
- 既存改訂版ファイル（main_window, widgets, matrix_table, condition_builder, palette, canvas, draft, dialog）
- ファイル存在確認、インポート確認、主要メソッド検証
直接実行: python tests/test_all_components_comprehensive.py
"""

import sys
import os
import json

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
gui_dir = os.path.join(project_root, 'statable_gui')
codegen_dir = os.path.join(project_root, 'codegen')
sys.path.insert(0, project_root)
sys.path.insert(0, gui_dir)
sys.path.insert(0, codegen_dir)

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


# =========================================================
# 0. ファイル存在確認
# =========================================================
def test_file_existence():
    print("\n--- ファイル存在確認 ---")

    required_files = [
        # 新規追加（libcntrl）
        os.path.join(gui_dir, 'libcntrl', '__init__.py'),
        os.path.join(gui_dir, 'libcntrl', 'role_function_library.py'),
        os.path.join(gui_dir, 'libcntrl', 'condition_library.py'),
        os.path.join(gui_dir, 'libcntrl', 'literal_library.py'),
        os.path.join(gui_dir, 'libcntrl', 'role_function_edit_dialog.py'),
        os.path.join(gui_dir, 'libcntrl', 'literal_management_dialog.py'),

        # 既存改訂版
        os.path.join(gui_dir, 'main_window.py'),
        os.path.join(gui_dir, 'widgets.py'),
        os.path.join(gui_dir, 'matrix_table.py'),
        os.path.join(gui_dir, 'condition_builder_dialog.py'),
        os.path.join(gui_dir, 'transition_editor_direct', 'palette_widget.py'),
        os.path.join(gui_dir, 'transition_editor_direct', 'canvas_widget.py'),
        os.path.join(gui_dir, 'transition_editor_direct', 'draft.py'),
        os.path.join(gui_dir, 'transition_editor_direct', 'dialog.py'),
        os.path.join(gui_dir, 'transition_editor_direct', '__init__.py'),
    ]

    for f in required_files:
        check(f"存在: {os.path.relpath(f, project_root)}", os.path.exists(f))


# =========================================================
# 1. 共有ライブラリ（libcntrl）
# =========================================================
def test_role_function_library():
    print("\n--- ロール関数ライブラリ ---")
    from libcntrl.role_function_library import RoleFunctionLibrary, RoleFunction

    lib = RoleFunctionLibrary()
    check("初期状態は空", len(lib.list_all()) == 0)

    rf = RoleFunction(name="CheckSensor", title="センサチェック", description="センサ確認")
    lib.add(rf)
    check("追加", len(lib.list_all()) == 1)
    check("取得", lib.get("CheckSensor") == rf)

    try:
        lib.add(RoleFunction(name="CheckSensor"))
        check("重複エラー", False, "例外なし")
    except ValueError:
        check("重複エラー", True)

    rf.used_literals.append("RETRY_THRESHOLD")
    check("使用リテラル登録", "RETRY_THRESHOLD" in rf.used_literals)

    lib.remove("CheckSensor")
    check("削除", len(lib.list_all()) == 0)


def test_condition_library():
    print("\n--- 遷移条件ライブラリ ---")
    from libcntrl.condition_library import ConditionLibrary, ConditionTemplate

    lib = ConditionLibrary()
    check("初期状態は空", len(lib.list_all()) == 0)

    ct = ConditionTemplate(name="RetryCheck", condition="retry_count < RETRY_THRESHOLD")
    lib.add(ct)
    check("条件追加", len(lib.list_all()) == 1)
    check("条件取得", lib.get("RetryCheck").condition == "retry_count < RETRY_THRESHOLD")


def test_literal_library():
    print("\n--- リテラルライブラリ ---")
    from libcntrl.literal_library import LiteralLibrary, LiteralDefinition

    lib = LiteralLibrary()
    check("初期状態は空", len(lib.list_all()) == 0)

    lit1 = LiteralDefinition(name="RETRY_THRESHOLD", value="3", literal_type="int")
    lib.add(lit1)
    check("リテラル追加", len(lib.list_all()) == 1)

    lit2 = LiteralDefinition(name="MAX_RETRY_COUNT", value="3", literal_type="int")
    lib.add(lit2)
    check("同じ値で別名許可", len(lib.list_all()) == 2)

    try:
        lib.add(LiteralDefinition(name="RETRY_THRESHOLD", value="5"))
        check("同名エラー", False, "例外なし")
    except ValueError:
        check("同名エラー", True)


# =========================================================
# 2. Draft変換ヘルパー
# =========================================================
def test_draft_helpers():
    print("\n--- Draft変換ヘルパー ---")
    from statable_gui.transition_editor_direct.draft import (
        transition_to_flow_item, flow_item_to_transition, ensure_list
    )
    from statable.model import Transition

    check("ensure_list(list)", ensure_list(["a", "b"]) == ["a", "b"])
    check("ensure_list(str)", ensure_list("abc") == [])
    check("ensure_list(None)", ensure_list(None) == [])

    trans = Transition(
        source="Error",
        event="",
        condition="retry_count < 3",
        pre_actions=[],
        target="Active",
        has_else=True,
        else_target="",
        else_actions=[],
        title="リトライ"
    )
    fi = transition_to_flow_item(trans)
    check("イベント名がNewEvent", fi.params['event'] == "NewEvent")
    check("条件式が保持", fi.params['condition'] == "retry_count < 3")

    trans2 = flow_item_to_transition(fi, "Error", "")
    check("書き戻し条件一致", trans2.condition == "retry_count < 3")
    check("書き戻しイベントは空のまま", trans2.event == "")


# =========================================================
# 3. 条件ビルダー（ロジック部分）
# =========================================================
def test_condition_builder_logic():
    print("\n--- 条件ビルダー ロジック ---")
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)

    from statable_gui.condition_builder_dialog import ConditionBuilderDialog, LiteralizationDialog
    from libcntrl.literal_library import LiteralLibrary
    from codegen.sample_data import SampleDataGenerator

    sample_gen = SampleDataGenerator()
    sm = sample_gen.create_sample_state_machine()
    gd = sample_gen.create_sample_global_defs()
    literal_lib = LiteralLibrary()

    dlg = ConditionBuilderDialog(
        condition="battery_voltage > 3000 && EVT_POWER_ON_REQ == 1",
        global_defs=gd,
        state_machine=sm,
        literal_library=literal_lib
    )

    c_code = dlg._convert_to_c_code("battery_voltage > 3000 && EVT_POWER_ON_REQ == 1")
    check("Cコード変換", "(ctx->data.battery_voltage > 3000) && (ctx->flags.EVT_POWER_ON_REQ == 1)" in c_code)

    parenthesized = dlg._add_parentheses_to_comparisons("a > 1 && b < 2")
    check("括弧補完", parenthesized == "(a > 1) && (b < 2)")

    text = "retry_count < 3 && voltage > 2.5"
    lit_dlg = LiteralizationDialog(text, literal_lib)
    check("リテラル化テーブル行数", lit_dlg.table.rowCount() == 2)
    lit_dlg.table.item(0, 2).setText("RETRY_THRESHOLD")
    lit_dlg.table.item(1, 2).setText("VOLTAGE_MIN")
    lit_dlg._on_accept()
    updated = lit_dlg.get_updated_condition_text()
    check("置換結果", "RETRY_THRESHOLD" in updated and "VOLTAGE_MIN" in updated)
    check("リテラル登録数", len(literal_lib.list_all()) == 2)

    dlg.close()


# =========================================================
# 4. パレット MIMEデータ
# =========================================================
def test_palette_mime():
    print("\n--- パレット MIMEデータ ---")
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)

    from statable_gui.transition_editor_direct.palette_widget import PaletteListWidget, PaletteWidget

    list_widget = PaletteListWidget("function")
    list_widget.addItem("CheckSensor")
    list_widget.setCurrentRow(0)

    items = [list_widget.item(0)]
    mime = list_widget.mimeData(items)
    check("MIMEタイプ", mime.hasFormat("application/x-flow-item"))
    data = json.loads(bytes(mime.data("application/x-flow-item")).decode("utf-8"))
    check("MIME item_type", data["item_type"] == "function")
    check("MIME name", data["name"] == "CheckSensor")

    pw = PaletteWidget(role_functions=["FuncA", "FuncB"])
    check("パレット関数リスト", pw.function_list.count() == 2)
    check("遷移条件リスト", pw.transition_list.count() == 1)


# =========================================================
# 5. キャンバス ノード
# =========================================================
def test_canvas_node():
    print("\n--- キャンバス ノード ---")
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)

    from statable_gui.transition_editor_direct.canvas_widget import FlowNodeItem, FlowCanvas
    from statable_gui.transition_editor_direct.draft import ActionDraft, FlowItem

    node = FlowNodeItem("transition", "START: voltage > 800")
    check("ノードタイプ", node.item_type == "transition")
    check("ノードテキスト", "START" in node.text_item.toPlainText())

    draft = ActionDraft(source="Idle", event="START")
    draft.flow_items.append(FlowItem(item_type="transition", name="START", params={
        "event": "START", "condition": "voltage > 800", "pre_actions": [], "target": "Active",
        "has_else": True, "else_target": "", "else_actions": []
    }))
    canvas = FlowCanvas(draft)
    check("キャンバス作成", canvas is not None)
    check("キャンバスアイテム数", len(canvas.scene.items()) > 0)


# =========================================================
# 6. MatrixTable 遷移取得
# =========================================================
def test_matrix_table():
    print("\n--- MatrixTable 遷移取得 ---")
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)

    from statable_gui.matrix_table import MatrixTableWidget
    from statable.state_machine import StateMachine
    from statable.model import State, Event, Transition
    from libcntrl.role_function_library import RoleFunctionLibrary
    from libcntrl.condition_library import ConditionLibrary
    from libcntrl.literal_library import LiteralLibrary

    sm = StateMachine()
    sm.add_state(State(name="Idle"))
    sm.add_state(State(name="Active"))
    sm.add_event(Event(name="START"))
    sm.add_transition(Transition(source="Idle", event="START", condition="voltage > 800", target="Active"))
    sm.add_transition(Transition(source="Idle", event="START", condition="voltage <= 800", target="Idle"))

    table = MatrixTableWidget(
        sm,
        role_function_library=RoleFunctionLibrary(),
        condition_library=ConditionLibrary(),
        literal_library=LiteralLibrary()
    )
    check("テーブル行数", table.rowCount() == 1)
    check("テーブル列数", table.columnCount() == 2)

    trans_list = table._find_transitions("Idle", "START")
    check("遷移リスト取得", len(trans_list) == 2)


# =========================================================
# 7. MainWindow / StateMachineTab 共有ライブラリ受け渡し
# =========================================================
def test_shared_library_integration():
    print("\n--- MainWindow / StateMachineTab 共有ライブラリ受け渡し ---")
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)

    from statable_gui.main_window import MainWindow
    from statable_gui.widgets import StateMachineTab
    from statable.state_machine import StateMachine
    from statable.global_defs import GlobalDefinitions

    # MainWindowの属性確認
    win = MainWindow()
    check("MainWindow.role_function_library", hasattr(win, 'role_function_library'))
    check("MainWindow.condition_library", hasattr(win, 'condition_library'))
    check("MainWindow.literal_library", hasattr(win, 'literal_library'))

    # StateMachineTabに共有ライブラリが渡るか
    sm = StateMachine()
    gd = GlobalDefinitions()
    tab = StateMachineTab(
        sm,
        global_defs=gd,
        role_function_library=win.role_function_library,
        condition_library=win.condition_library,
        literal_library=win.literal_library
    )
    check("StateMachineTab.role_function_library", hasattr(tab, 'role_function_library'))
    check("StateMachineTab.condition_library", hasattr(tab, 'condition_library'))
    check("StateMachineTab.literal_library", hasattr(tab, 'literal_library'))

    # 後始末
    tab.close()
    win.close()


# =========================================================
# メイン実行
# =========================================================
def run_all():
    global PASS, FAIL, FAILED
    PASS = 0
    FAIL = 0
    FAILED = []

    print("=" * 60)
    print("全コンポーネント 包括的静的テスト")
    print("=" * 60)

    test_file_existence()
    test_role_function_library()
    test_condition_library()
    test_literal_library()
    test_draft_helpers()
    test_condition_builder_logic()
    test_palette_mime()
    test_canvas_node()
    test_matrix_table()
    test_shared_library_integration()

    print("\n" + "=" * 60)
    print(f"合格: {PASS}")
    print(f"失敗: {FAIL}")
    if FAILED:
        print("失敗項目:")
        for f in FAILED:
            print(f"  - {f}")
    print("=" * 60)

    if FAIL == 0:
        print("🎉 全テスト成功！")
    else:
        print("❌ 失敗あり")

if __name__ == "__main__":
    run_all()