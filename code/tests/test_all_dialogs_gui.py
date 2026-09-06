# tests/test_all_dialogs_gui.py
"""
新規・改善ダイアログ GUI表示テスト
対象:
  - ConditionBuilderDialog（リテラル化対応）
  - RoleFunctionEditDialog（新規）
  - LiteralManagementDialog（新規）
  - ActionEditorDialog（共有ライブラリ対応）
  - MainWindow（共有ライブラリ統合）
直接実行: python tests/test_all_dialogs_gui.py
"""

import sys
import os
import logging
import sys
import os
import logging

# 既存のハンドラをクリアしてから設定
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)

# 該当ロガーを明示的にDEBUGに設定
for name in [
    "transition_editor_direct",
    "transition_editor_direct.canvas",
    "transition_editor_direct.palette",
    "transition_editor_direct.dialog",
    "transition_editor_direct.code",
    "transition_editor_direct.draft"
]:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = True
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
gui_dir = os.path.join(project_root, 'statable_gui')
codegen_dir = os.path.join(project_root, 'codegen')
sys.path.insert(0, project_root)
sys.path.insert(0, gui_dir)
sys.path.insert(0, codegen_dir)

from PySide6.QtWidgets import QApplication, QMessageBox

from codegen.sample_data import SampleDataGenerator

# 共有ライブラリ
from libcntrl.role_function_library import RoleFunctionLibrary, RoleFunction
from libcntrl.condition_library import ConditionLibrary, ConditionTemplate
from libcntrl.literal_library import LiteralLibrary, LiteralDefinition

# ダイアログ
from statable_gui.condition_builder_dialog import ConditionBuilderDialog
from libcntrl.role_function_edit_dialog import RoleFunctionEditDialog
from libcntrl.literal_management_dialog import LiteralManagementDialog
from statable_gui.transition_editor_direct.dialog import ActionEditorDialog
from statable_gui.transition_editor_direct.draft import ActionDraft, FlowItem, transition_to_flow_item
from statable_gui.main_window import MainWindow


def show_info(title, message):
    """情報ダイアログを表示"""
    QMessageBox.information(None, title, message)


def main():
    app = QApplication(sys.argv)

    # サンプルデータ
    sample_gen = SampleDataGenerator()
    sm = sample_gen.create_sample_state_machine()
    gd = sample_gen.create_sample_global_defs()

    # 共有ライブラリ初期化
    role_lib = RoleFunctionLibrary()
    role_lib.add(RoleFunction(name="CheckSensor", title="センサチェック", description="センサ値を確認"))
    role_lib.add(RoleFunction(name="StartMotor", title="モータ起動", description="モータを起動する"))

    condition_lib = ConditionLibrary()
    condition_lib.add(ConditionTemplate(name="RetryCheck", condition="retry_count < RETRY_THRESHOLD"))

    literal_lib = LiteralLibrary()
    literal_lib.add(LiteralDefinition(name="RETRY_THRESHOLD", value="3", literal_type="int", description="リトライ回数閾値"))
    literal_lib.add(LiteralDefinition(name="VOLTAGE_MIN", value="2.5", literal_type="float", description="最小電圧"))

    # =====================================================
    # 1. 条件ビルダー（リテラル化対応）
    # =====================================================
    show_info("テスト1", "条件ビルダー（リテラル化対応）を表示します。\n「リテラル化」ボタンを試してください。")
    dlg1 = ConditionBuilderDialog(
        condition="retry_count < 3 && voltage > 2.5",
        global_defs=gd,
        state_machine=sm,
        literal_library=literal_lib
    )
    dlg1.setWindowTitle("条件ビルダー（リテラル化対応）")
    dlg1.exec()

    # =====================================================
    # 2. ロール関数編集ダイアログ（新規）
    # =====================================================
    show_info("テスト2", "ロール関数編集ダイアログ（新規）を表示します。\n使用グローバル変数・イベント・リテラルをチェックできます。")
    rf = role_lib.get("CheckSensor")
    global_vars = [v.name for v in gd.variables]
    events = [e.name for e in sm.events.values()]
    literals = [lit.name for lit in literal_lib.list_all()]

    dlg2 = RoleFunctionEditDialog(
        rf,
        global_vars=global_vars,
        events=events,
        literals=literals
    )
    dlg2.setWindowTitle("ロール関数編集ダイアログ（新規）")
    dlg2.exec()

    # =====================================================
    # 3. リテラル管理ダイアログ（新規）
    # =====================================================
    show_info("テスト3", "リテラル管理ダイアログ（新規）を表示します。\n追加・編集・削除を試してください。")
    dlg3 = LiteralManagementDialog(literal_lib)
    dlg3.setWindowTitle("リテラル管理ダイアログ（新規）")
    dlg3.exec()

    # =====================================================
    # 4. アクションエディタ（共有ライブラリ対応）
    # =====================================================
    show_info("テスト4", "アクションエディタ（共有ライブラリ対応）を表示します。\n遷移条件ノードをダブルクリックして条件ビルダーを開けます。")

    # 既存の遷移をActionDraftに変換
    draft = ActionDraft(source="Active", event="ERROR")
    # サンプル遷移を2つ追加
    transitions = sm.get_transitions_for_cell("Active", "ERROR")
    for trans in transitions:
        draft.flow_items.append(transition_to_flow_item(trans))

    # もし遷移が空なら手動で追加
    if not draft.flow_items:
        draft.flow_items.append(FlowItem(
            item_type="transition",
            name="ERROR",
            edited_text="ERROR: err_code != 0",
            params={
                "event": "ERROR",
                "condition": "err_code != 0",
                "pre_actions": [],
                "target": "Error",
                "has_else": True,
                "else_target": "",
                "else_actions": []
            }
        ))

    role_func_names = [rf.name for rf in role_lib.list_all()]
    states = list(sm.states.keys())

    dlg4 = ActionEditorDialog(
        draft,
        role_functions=role_func_names,
        transition_events=["ERROR"],
        states=states,
        global_defs=gd,
        state_machine=sm,
        role_function_library=role_lib,
        condition_library=condition_lib,
        literal_library=literal_lib
    )
    dlg4.setWindowTitle("アクションエディタ（共有ライブラリ対応）")
    dlg4.exec()

    # =====================================================
    # 5. メインウィンドウ（共有ライブラリ統合）
    # =====================================================
    show_info("テスト5", "メインウィンドウ（共有ライブラリ統合）を表示します。\n状態遷移表のセルをダブルクリックしてアクションエディタを開けます。")
    win = MainWindow()
    win.show()
    app.exec()

    print("すべてのダイアログ表示テストが完了しました。")


if __name__ == "__main__":
    main()