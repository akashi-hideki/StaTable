# tests/test_condition_builder_dialog.py
"""
条件ビルダーダイアログ単体テスト（改訂版UI対応）
直接実行: python tests/test_condition_builder_dialog.py
"""

import sys
import os

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'statable_gui'))
sys.path.insert(0, os.path.join(project_root, 'codegen'))

from PySide6.QtWidgets import QApplication, QTreeWidgetItem
from PySide6.QtCore import Qt

# テスト対象
from statable_gui.condition_builder_dialog import ConditionBuilderDialog
from codegen.sample_data import SampleDataGenerator

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

def main():
    global PASS, FAIL, FAILED
    app = QApplication.instance() or QApplication(sys.argv)

    # サンプルデータ生成
    sample_gen = SampleDataGenerator()
    sm = sample_gen.create_sample_state_machine()
    gd = sample_gen.create_sample_global_defs()

    # ダイアログ作成
    initial_condition = "ctx->data.battery_voltage > 3000"
    dlg = ConditionBuilderDialog(
        condition=initial_condition,
        global_defs=gd,
        state_machine=sm
    )

    # 初期状態チェック
    check("初期条件式が設定されている", dlg.get_condition_text() == initial_condition)

    # シンボルツリーに項目があるか
    check("シンボルツリーに項目がある", dlg.symbol_tree.topLevelItemCount() > 0)

    # 定数シンボル: true挿入
    dlg.condition_edit.clear()
    dlg._insert_text("true")
    check("true挿入", dlg.get_condition_text() == "true")

    # 数値リテラル挿入
    dlg.condition_edit.clear()
    dlg.num_input.setText("3000")
    dlg._insert_number()
    check("数値リテラル挿入", dlg.get_condition_text() == "3000")

    # シンボルツリーから挿入（最初のグローバル変数を探して挿入）
    dlg.condition_edit.clear()
    inserted = False
    # トップレベルを走査
    for i in range(dlg.symbol_tree.topLevelItemCount()):
        top_item = dlg.symbol_tree.topLevelItem(i)
        if top_item.text(0) == "グローバル変数" and top_item.childCount() > 0:
            child = top_item.child(0)
            symbol = child.data(0, Qt.UserRole)
            dlg._insert_symbol(child, 0)
            inserted = (dlg.get_condition_text() == symbol)
            break
    check("シンボルツリーから挿入", inserted, "グローバル変数が見つからない")

    # Cコード変換の確認（グローバル変数とフラグ）
    dlg.condition_edit.setPlainText("battery_voltage > 3000 && EVT_POWER_ON_REQ == 1")
    dlg._update_c_code_view()
    expected_c_code = "(ctx->data.battery_voltage > 3000) && (ctx->flags.EVT_POWER_ON_REQ == 1)"
    check("Cコード変換", dlg.get_c_code_text() == expected_c_code)

    dlg.close()

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
        sys.exit(1)

if __name__ == "__main__":
    main()