# tests/test_condition_builder_gui.py
"""
条件ビルダーダイアログ GUI確認用
直接実行: python tests/test_condition_builder_gui.py
"""

import sys
import os

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'statable_gui'))
sys.path.insert(0, os.path.join(project_root, 'codegen'))

from PySide6.QtWidgets import QApplication

from statable_gui.condition_builder_dialog import ConditionBuilderDialog
from codegen.sample_data import SampleDataGenerator


def main():
    app = QApplication(sys.argv)

    # サンプルデータ生成
    sample_gen = SampleDataGenerator()
    sm = sample_gen.create_sample_state_machine()
    gd = sample_gen.create_sample_global_defs()

    # 条件ビルダーダイアログを表示
    dialog = ConditionBuilderDialog(
        condition="ctx->data.battery_voltage > 3000 && ctx->flags.EVT_POWER_ON_REQ == 1",
        global_defs=gd,
        state_machine=sm
    )
    dialog.setWindowTitle("遷移条件ビルダー（GUI確認）")
    dialog.show()

    print("条件ビルダーダイアログを表示しました。")
    print("操作が終わったらウィンドウを閉じてください。")

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())