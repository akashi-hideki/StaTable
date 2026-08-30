"""全ダイアログ表示確認プログラム"""

import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QMessageBox

from statable.sample_data import create_sample_state_machine, create_sample_global_defs


def show_dialog(app, title: str, dialog):
    """メッセージを表示してからダイアログを表示"""
    QMessageBox.information(None, "ダイアログ確認", f"次に表示するダイアログ:\n\n{title}\n\nOKを押すと表示されます。")
    dialog.show()
    app.exec()


def main():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    sm = create_sample_state_machine()
    defs = create_sample_global_defs()

    dialogs_to_show = []

    # 1. GlobalDefinitionsDialog
    from statable_gui.global_defs_dialog import GlobalDefinitionsDialog
    dialogs_to_show.append(("GlobalDefinitionsDialog（グローバル変数・イベントフラグ）", GlobalDefinitionsDialog(defs)))

    # 2. EventQueueDefsDialog
    from statable_gui.event_queue_dialog import EventQueueDefsDialog
    dialogs_to_show.append(("EventQueueDefsDialog（イベントキュー定義）", EventQueueDefsDialog(defs, event_names=list(sm.events.keys()))))

    # 3. EventDefinitionDialog
    from statable_gui.event_definition_dialog import EventDefinitionDialog
    dialogs_to_show.append(("EventDefinitionDialog（イベント定義）", EventDefinitionDialog(sm, defs)))

    # 4. EventDeliverySettingsDialog
    from statable_gui.event_delivery_settings_dialog import EventDeliverySettingsDialog
    dialogs_to_show.append(("EventDeliverySettingsDialog（イベント配送設定）", EventDeliverySettingsDialog(sm, defs)))

    # 5. InterruptHandlerEditDialog
    from statable_gui.interrupt_handler_edit_dialog import InterruptHandlerEditDialog
    dialogs_to_show.append(("InterruptHandlerEditDialog（割り込み設定）",
                             InterruptHandlerEditDialog(defs, event_names=list(sm.events.keys()), role_functions=sm.role_functions)))

    # 6. TransitionListDialog
    from statable_gui.dialogs import TransitionListDialog
    trans_list = sm.get_transitions_for_cell("Idle", "START")
    dialogs_to_show.append(("TransitionListDialog（遷移編集）",
                             TransitionListDialog(state_names=list(sm.states.keys()), event_name="START",
                                                  existing_transitions=trans_list, role_functions=sm.role_functions, global_defs=defs)))

    # 7. ConditionEditDialog
    from statable_gui.condition_edit_dialog import ConditionEditDialog
    dialogs_to_show.append(("ConditionEditDialog（状態遷移条件編集）",
                             ConditionEditDialog(condition_text="battery_voltage < 3000", title="低電圧判定", global_defs=defs, role_functions=sm.role_functions)))

    # 8. ActionEditDialog
    from statable_gui.action_edit_dialog import ActionEditDialog
    dialogs_to_show.append(("ActionEditDialog（動作編集）",
                             ActionEditDialog(action_text="start_motor();", title="モータ起動", role_functions=sm.role_functions, global_defs=defs)))

    # 9. VariableEditDialog
    from statable_gui.global_defs_dialog import VariableEditDialog
    dialogs_to_show.append(("VariableEditDialog（グローバル変数編集）",
                             VariableEditDialog(groups=defs.variable_groups(), global_defs=defs)))

    # 10. FlagEditDialog
    from statable_gui.global_defs_dialog import FlagEditDialog
    dialogs_to_show.append(("FlagEditDialog（イベントフラグ編集）",
                             FlagEditDialog(groups=defs.flag_groups())))

    # 11. BulkVariableDialog
    from statable_gui.global_defs_dialog import BulkVariableDialog
    bulk_var = BulkVariableDialog(groups=defs.variable_groups(), global_defs=defs)
    bulk_var.set_variables(defs.variables)
    dialogs_to_show.append(("BulkVariableDialog（グローバル変数一括登録）", bulk_var))

    # 12. BulkFlagDialog
    from statable_gui.global_defs_dialog import BulkFlagDialog
    bulk_flag = BulkFlagDialog(groups=defs.flag_groups())
    bulk_flag.set_flags(defs.flags)
    dialogs_to_show.append(("BulkFlagDialog（イベントフラグ一括登録）", bulk_flag))

    # 13. TypeManagerDialog
    from statable_gui.common_widgets import TypeManagerDialog
    dialogs_to_show.append(("TypeManagerDialog（ユーザー定義型管理）", TypeManagerDialog(global_defs=defs)))

    # 14. TypeEditDialog
    from statable_gui.common_widgets import TypeEditDialog
    dialogs_to_show.append(("TypeEditDialog（型編集）", TypeEditDialog()))

    # 15. StructMemberEditDialog
    from statable_gui.common_widgets import StructMemberEditDialog
    dialogs_to_show.append(("StructMemberEditDialog（構造体メンバ編集）", StructMemberEditDialog()))

    # 16. RoleFunctionDialog
    from statable_gui.role_function_dialog import RoleFunctionDialog
    dialogs_to_show.append(("RoleFunctionDialog（ロール関数編集）", RoleFunctionDialog()))

    # 17. TimerBaseEditDialog
    from statable_gui.interrupt_handler_edit_dialog import TimerBaseEditDialog
    dialogs_to_show.append(("TimerBaseEditDialog（タイマ基準編集）", TimerBaseEditDialog(timer_base=defs.timer_base)))

    # 18. TimerDerivedEditDialog
    from statable_gui.interrupt_handler_edit_dialog import TimerDerivedEditDialog
    dialogs_to_show.append(("TimerDerivedEditDialog（派生タイマ編集）", TimerDerivedEditDialog()))

    # 19. DevicePlaceholderEditDialog
    from statable_gui.interrupt_handler_edit_dialog import DevicePlaceholderEditDialog
    dialogs_to_show.append(("DevicePlaceholderEditDialog（デバイスリソース編集）", DevicePlaceholderEditDialog()))

    # 20. EventQueueEditDialog
    from statable_gui.event_queue_dialog import EventQueueEditDialog
    dialogs_to_show.append(("EventQueueEditDialog（イベントキュー編集）",
                             EventQueueEditDialog(event_names=list(sm.events.keys()), global_defs=defs)))

    # 21. EventEditDialog
    from statable_gui.event_definition_dialog import EventEditDialog
    dialogs_to_show.append(("EventEditDialog（イベント編集）", EventEditDialog(global_defs=defs)))

    # 22. GroupAddDialog
    from statable_gui.common_widgets import GroupAddDialog
    dialogs_to_show.append(("GroupAddDialog（グループ追加）", GroupAddDialog()))

    print("=" * 60)
    print("全ダイアログ表示確認")
    print("=" * 60)

    for i, (title, dlg) in enumerate(dialogs_to_show, 1):
        print(f"\n[{i}/{len(dialogs_to_show)}] {title}")
        try:
            show_dialog(app, title, dlg)
            print(f"  -> 正常に表示・終了しました")
        except Exception as e:
            print(f"  -> エラーが発生しました")
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("全ダイアログ確認終了")
    print("=" * 60)


if __name__ == "__main__":
    main()