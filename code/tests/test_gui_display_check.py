"""GUI表示確認プログラム

各ダイアログを順番に表示し、目視確認する。
ウィンドウを閉じると次のダイアログが表示される。
"""

import sys
import os

# プロジェクトルートを sys.path に追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QMessageBox

from statable.sample_data import create_sample_state_machine, create_sample_global_defs
from statable.state_machine import StateMachine


def show_message_and_wait(app, title: str, dialog):
    """メッセージを表示してからダイアログを表示し、閉じるまで待機"""
    QMessageBox.information(None, "表示確認", f"次に表示するダイアログ:\n\n{title}\n\nOKを押すと表示されます。")
    dialog.show()
    app.exec()  # ダイアログが閉じられるまで待機


def main():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    sm = create_sample_state_machine()
    defs = create_sample_global_defs()

    # ------------------------------------------------------------------
    # 1. 状態遷移イベント定義ダイアログ
    # ------------------------------------------------------------------
    from statable_gui.event_definition_dialog import EventDefinitionDialog
    dlg = EventDefinitionDialog(sm, defs)
    show_message_and_wait(app, "状態遷移イベント定義ダイアログ", dlg)

    # ------------------------------------------------------------------
    # 2. イベント配送設定ダイアログ
    # ------------------------------------------------------------------
    from statable_gui.event_delivery_settings_dialog import EventDeliverySettingsDialog
    dlg = EventDeliverySettingsDialog(sm, defs, auto_convert=True)
    show_message_and_wait(app, "イベント配送設定ダイアログ", dlg)

    # ------------------------------------------------------------------
    # 3. イベントキュー定義ダイアログ
    # ------------------------------------------------------------------
    from statable_gui.event_queue_dialog import EventQueueDefsDialog
    dlg = EventQueueDefsDialog(defs, event_names=list(sm.events.keys()))
    show_message_and_wait(app, "イベントキュー定義ダイアログ", dlg)

    # ------------------------------------------------------------------
    # 4. グローバル定義ダイアログ
    # ------------------------------------------------------------------
    from statable_gui.global_defs_dialog import GlobalDefinitionsDialog
    dlg = GlobalDefinitionsDialog(defs)
    show_message_and_wait(app, "グローバル変数・イベントフラグ定義ダイアログ", dlg)

    # ------------------------------------------------------------------
    # 5. 割り込み処理設定ダイアログ
    # ------------------------------------------------------------------
    from statable_gui.interrupt_handler_edit_dialog import InterruptHandlerEditDialog
    dlg = InterruptHandlerEditDialog(
        global_defs=defs,
        event_names=list(sm.events.keys()),
        role_functions=sm.role_functions,
    )
    show_message_and_wait(app, "割り込み処理・デバイスリソース・タイマ設定ダイアログ", dlg)

    # ------------------------------------------------------------------
    # 6. ロール関数編集ダイアログ
    # ------------------------------------------------------------------
    from statable_gui.role_function_dialog import RoleFunctionDialog
    dlg = RoleFunctionDialog()
    show_message_and_wait(app, "ロール関数編集ダイアログ", dlg)

    # ------------------------------------------------------------------
    # 7. 状態遷移条件編集ダイアログ
    # ------------------------------------------------------------------
    from statable_gui.condition_edit_dialog import ConditionEditDialog
    dlg = ConditionEditDialog(
        condition_text="battery_voltage < 3000",
        title="低電圧判定",
        global_defs=defs,
        role_functions=sm.role_functions,
    )
    show_message_and_wait(app, "状態遷移条件編集ダイアログ", dlg)

    # ------------------------------------------------------------------
    # 8. 動作編集ダイアログ
    # ------------------------------------------------------------------
    from statable_gui.action_edit_dialog import ActionEditDialog
    dlg = ActionEditDialog(
        action_text="start_motor();",
        title="モータ起動",
        role_functions=sm.role_functions,
        global_defs=defs,
    )
    show_message_and_wait(app, "動作編集ダイアログ", dlg)

    # ------------------------------------------------------------------
    # 9. 遷移編集ダイアログ
    # ------------------------------------------------------------------
    from statable_gui.dialogs import TransitionListDialog
    trans_list = sm.get_transitions_for_cell("Idle", "START")
    dlg = TransitionListDialog(
        state_names=list(sm.states.keys()),
        event_name="START",
        existing_transitions=trans_list,
        role_functions=sm.role_functions,
        global_defs=defs,
    )
    show_message_and_wait(app, "遷移編集ダイアログ", dlg)

    # ------------------------------------------------------------------
    # 10. 状態遷移マトリックスウィジェット
    # ------------------------------------------------------------------
    from statable_gui.matrix_table import MatrixTableWidget
    table = MatrixTableWidget(sm, global_defs=defs)
    table.setWindowTitle("状態遷移マトリックス")
    table.resize(900, 600)
    show_message_and_wait(app, "状態遷移マトリックス", table)

    # ------------------------------------------------------------------
    # 11. 設定パネル（状態一覧・ロール関数）
    # ------------------------------------------------------------------
    from statable_gui.widgets import SettingsPanel
    panel = SettingsPanel(sm, global_defs=defs)
    panel.setWindowTitle("設定パネル（状態一覧・ロール関数）")
    panel.resize(600, 700)
    show_message_and_wait(app, "設定パネル", panel)

    print("すべてのGUI表示確認が終了しました。")


if __name__ == "__main__":
    main()