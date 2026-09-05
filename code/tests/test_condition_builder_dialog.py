# tests/test_condition_builder_dialog.py
"""
条件ビルダーダイアログ単体テスト
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

from PySide6.QtWidgets import QApplication, QListWidgetItem
from PySide6.QtCore import Qt

# テスト対象
from statable_gui.condition_builder_dialog import ConditionBuilderDialog
from statable.global_defs import GlobalDefinitions
from statable.state_machine import StateMachine
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

    # 要素リストが空でないか
    check("要素リストに項目がある", dlg.element_list.count() > 0)

    # 定数シンボル: true挿入
    dlg.condition_edit.clear()
    dlg._insert_text("true")
    check("true挿入", dlg.get_condition_text() == "true")

    # 数値リテラル挿入
    dlg.condition_edit.clear()
    dlg.num_input.setText("3000")
    dlg._insert_number()
    check("数値リテラル挿入", dlg.get_condition_text() == "3000")

    # 要素リストから挿入（最初の項目をダブルクリック相当）
    first_item = dlg.element_list.item(0)
    if first_item:
        dlg.condition_edit.clear()
        dlg._insert_selected_item(first_item)
        inserted_text = first_item.data(Qt.UserRole)
        check("要素リストから挿入", dlg.get_condition_text() == inserted_text)
    else:
        check("要素リストから挿入", False, "要素リストが空")

    # 手動確認用にダイアログを表示するか？
    # 必要ならコメントを外す
    # dlg.show()
    # app.exec()

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