# tests/test_condition_builder_literal_gui.py
"""
条件ビルダー リテラル化GUIテスト
直接実行: python tests/test_condition_builder_literal_gui.py
"""

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'statable_gui'))

from PySide6.QtWidgets import QApplication

from statable_gui.condition_builder_dialog import ConditionBuilderDialog
from libcntrl.literal_library import LiteralLibrary
from codegen.sample_data import SampleDataGenerator


def main():
    app = QApplication(sys.argv)

    sample_gen = SampleDataGenerator()
    sm = sample_gen.create_sample_state_machine()
    gd = sample_gen.create_sample_global_defs()

    literal_lib = LiteralLibrary()

    dialog = ConditionBuilderDialog(
        condition="retry_count < 3 && voltage > 2.5",
        global_defs=gd,
        state_machine=sm,
        literal_library=literal_lib
    )
    dialog.setWindowTitle("条件ビルダー（リテラル化GUI確認）")
    dialog.show()

    print("条件ビルダーを表示しました。")
    print("「リテラル化」ボタンを押して、数値をリテラルに変換できます。")
    print("ウィンドウを閉じると終了します。")

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())