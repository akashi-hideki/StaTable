"""主要メソッドの存在確認プログラム"""

import sys
import os
import inspect
import traceback

# プロジェクトルートを sys.path に追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_methods(class_name, required_methods):
    """クラスに必要なメソッドが揃っているか確認"""
    print(f"\n[{class_name.__name__}]")
    missing = []
    for method_name in required_methods:
        if hasattr(class_name, method_name):
            method = getattr(class_name, method_name)
            if callable(method):
                print(f"  [OK] {method_name}")
            else:
                print(f"  [NG] {method_name} (callableではない)")
                missing.append(method_name)
        else:
            print(f"  [NG] {method_name} (存在しない)")
            missing.append(method_name)
    return missing


def main():
    all_missing = []

    # ------------------------------------------------------------------
    # GlobalDefinitionsDialog
    # ------------------------------------------------------------------
    from statable_gui.global_defs_dialog import GlobalDefinitionsDialog
    missing = check_methods(GlobalDefinitionsDialog, [
        "_create_variable_tab",
        "_create_flag_tab",
        "refresh_variables",
        "refresh_flags",
        "on_variable_item_changed",
        "on_flag_item_changed",
        "add_empty_variable_row",
        "add_empty_flag_row",
        "delete_variable",
        "delete_flag",
        "bulk_variables",
        "bulk_flags",
        "_matches",
        "on_search_changed",
    ])
    all_missing.extend([(GlobalDefinitionsDialog.__name__, m) for m in missing])

    # ------------------------------------------------------------------
    # EventQueueDefsDialog
    # ------------------------------------------------------------------
    from statable_gui.event_queue_dialog import EventQueueDefsDialog
    missing = check_methods(EventQueueDefsDialog, [
        "refresh_table",
        "_matches",
        "on_item_changed",
        "on_double_clicked",
        "add_queue",
        "delete_queue",
    ])
    all_missing.extend([(EventQueueDefsDialog.__name__, m) for m in missing])

    # ------------------------------------------------------------------
    # EventQueueEditDialog
    # ------------------------------------------------------------------
    from statable_gui.event_queue_dialog import EventQueueEditDialog
    missing = check_methods(EventQueueEditDialog, [
        "_on_accept",
        "get_queue_def",
    ])
    all_missing.extend([(EventQueueEditDialog.__name__, m) for m in missing])

    # ------------------------------------------------------------------
    # EventDefinitionDialog
    # ------------------------------------------------------------------
    from statable_gui.event_definition_dialog import EventDefinitionDialog
    missing = check_methods(EventDefinitionDialog, [
        "refresh_table",
        "on_item_changed",
        "on_double_clicked",
        "add_event",
        "delete_event",
        "_find_event_by_row",
    ])
    all_missing.extend([(EventDefinitionDialog.__name__, m) for m in missing])

    # ------------------------------------------------------------------
    # EventEditDialog
    # ------------------------------------------------------------------
    from statable_gui.event_definition_dialog import EventEditDialog
    missing = check_methods(EventEditDialog, [
        "_on_data_check_toggled",
        "_on_accept",
        "get_event",
    ])
    all_missing.extend([(EventEditDialog.__name__, m) for m in missing])

    # ------------------------------------------------------------------
    # EventDeliverySettingsDialog
    # ------------------------------------------------------------------
    from statable_gui.event_delivery_settings_dialog import EventDeliverySettingsDialog
    missing = check_methods(EventDeliverySettingsDialog, [
        "_build_table",
        "_check_isr_usage",
        "_find_row_by_event_name",
        "_on_delivery_changed",
        "_update_converted_column",
        "_on_accept",
        "get_auto_convert",
    ])
    all_missing.extend([(EventDeliverySettingsDialog.__name__, m) for m in missing])

    # ------------------------------------------------------------------
    # TransitionListDialog
    # ------------------------------------------------------------------
    from statable_gui.dialogs import TransitionListDialog
    missing = check_methods(TransitionListDialog, [
        "on_cell_double_clicked",
        "open_condition_editor",
        "open_action_editor",
        "add_row",
        "delete_row",
        "move_row_up",
        "move_row_down",
        "_generate_display_title",
        "_update_display_title",
        "_on_accept",
        "get_transitions",
    ])
    all_missing.extend([(TransitionListDialog.__name__, m) for m in missing])

    # ------------------------------------------------------------------
    # ConditionEditDialog
    # ------------------------------------------------------------------
    from statable_gui.condition_edit_dialog import ConditionEditDialog
    missing = check_methods(ConditionEditDialog, [
        "refresh_role_combo",
        "insert_role_function",
        "insert_symbol",
        "_on_accept",
        "get_condition_text",
        "get_title",
    ])
    all_missing.extend([(ConditionEditDialog.__name__, m) for m in missing])

    # ------------------------------------------------------------------
    # ActionEditDialog
    # ------------------------------------------------------------------
    from statable_gui.action_edit_dialog import ActionEditDialog
    missing = check_methods(ActionEditDialog, [
        "refresh_role_combo",
        "update_signature_label",
        "insert_role_function",
        "add_new_role_function",
        "insert_symbol",
        "show_action_context_menu",
        "register_selected_as_variable",
        "register_selected_as_flag",
        "_on_accept",
        "get_action_text",
        "get_title",
    ])
    all_missing.extend([(ActionEditDialog.__name__, m) for m in missing])

    # ------------------------------------------------------------------
    # InterruptHandlerEditDialog
    # ------------------------------------------------------------------
    from statable_gui.interrupt_handler_edit_dialog import InterruptHandlerEditDialog
    missing = check_methods(InterruptHandlerEditDialog, [
        "_create_interrupt_tab",
        "_create_placeholder_tab",
        "_create_timer_tab",
        "refresh_interrupt_table",
        "refresh_placeholder_table",
        "refresh_timer_tabs",
        "_create_timer_base_tab",
        "_refresh_derived_table",
        "add_timer_base",
        "edit_timer_base",
        "close_timer_tab",
        "rename_timer_tab",
        "add_derived",
        "delete_derived",
        "on_derived_double_clicked",
    ])
    all_missing.extend([(InterruptHandlerEditDialog.__name__, m) for m in missing])

    # ------------------------------------------------------------------
    # InterruptEditDialog
    # ------------------------------------------------------------------
    from statable_gui.interrupt_handler_edit_dialog import InterruptEditDialog
    missing = check_methods(InterruptEditDialog, [
        "add_action_row",
        "delete_action_row",
        "on_action_double_clicked",
        "_on_accept",
        "get_interrupt",
    ])
    all_missing.extend([(InterruptEditDialog.__name__, m) for m in missing])

    # ------------------------------------------------------------------
    # VariableEditDialog
    # ------------------------------------------------------------------
    from statable_gui.global_defs_dialog import VariableEditDialog
    missing = check_methods(VariableEditDialog, [
        "_on_accept",
        "get_variable",
    ])
    all_missing.extend([(VariableEditDialog.__name__, m) for m in missing])

    # ------------------------------------------------------------------
    # FlagEditDialog
    # ------------------------------------------------------------------
    from statable_gui.global_defs_dialog import FlagEditDialog
    missing = check_methods(FlagEditDialog, [
        "update_bit_width_label",
        "_on_accept",
        "get_flag",
    ])
    all_missing.extend([(FlagEditDialog.__name__, m) for m in missing])

    # ------------------------------------------------------------------
    # BulkVariableDialog
    # ------------------------------------------------------------------
    from statable_gui.global_defs_dialog import BulkVariableDialog
    missing = check_methods(BulkVariableDialog, [
        "set_variables",
        "add_row",
        "add_empty_row",
        "delete_row",
        "_on_accept",
        "get_variables",
    ])
    all_missing.extend([(BulkVariableDialog.__name__, m) for m in missing])

    # ------------------------------------------------------------------
    # BulkFlagDialog
    # ------------------------------------------------------------------
    from statable_gui.global_defs_dialog import BulkFlagDialog
    missing = check_methods(BulkFlagDialog, [
        "set_flags",
        "add_row",
        "add_empty_row",
        "delete_row",
        "on_item_changed",
        "update_bit_width",
        "_on_accept",
        "get_flags",
    ])
    all_missing.extend([(BulkFlagDialog.__name__, m) for m in missing])

    # ------------------------------------------------------------------
    # TitleEditWidget
    # ------------------------------------------------------------------
    from statable_gui.common_widgets import TitleEditWidget
    missing = check_methods(TitleEditWidget, [
        "get_title",
        "set_title",
        "ensure_title",
    ])
    all_missing.extend([(TitleEditWidget.__name__, m) for m in missing])

    # ------------------------------------------------------------------
    # TypeComboBox
    # ------------------------------------------------------------------
    from statable_gui.common_widgets import TypeComboBox
    missing = check_methods(TypeComboBox, [
        "current_text",
        "set_current_text",
    ])
    all_missing.extend([(TypeComboBox.__name__, m) for m in missing])

    # ------------------------------------------------------------------
    # GroupComboBox
    # ------------------------------------------------------------------
    from statable_gui.common_widgets import GroupComboBox
    missing = check_methods(GroupComboBox, [
        "current_text",
        "set_current_text",
    ])
    all_missing.extend([(GroupComboBox.__name__, m) for m in missing])

    # ------------------------------------------------------------------
    # 結果サマリ
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    if all_missing:
        print("不足しているメソッド:")
        for cls_name, method_name in all_missing:
            print(f"  {cls_name}.{method_name}")
    else:
        print("すべてのメソッドが存在します。")
    print("=" * 60)

    return len(all_missing)


if __name__ == "__main__":
    try:
        missing_count = main()
        sys.exit(1 if missing_count > 0 else 0)
    except Exception as e:
        print("エラーが発生しました:")
        traceback.print_exc()
        sys.exit(1)