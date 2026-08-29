"""イベント配送設定ダイアログを実際に開いて目視確認するためのスクリプト"""

import sys
import os

# プロジェクトルートを sys.path に追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication

from statable.sample_data import create_sample_state_machine, create_sample_global_defs
from statable_gui.event_delivery_settings_dialog import EventDeliverySettingsDialog


def main():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    sm = create_sample_state_machine()
    defs = create_sample_global_defs()

    # ダイアログを表示（auto_convert=True）
    dlg = EventDeliverySettingsDialog(sm, defs, auto_convert=True)
    dlg.show()

    print("イベント配送設定ダイアログを表示しました。")
    print("ダイアログを閉じるとスクリプトが終了します。")

    # ダイアログが閉じられるまでアプリを実行
    app.exec()


if __name__ == "__main__":
    main()