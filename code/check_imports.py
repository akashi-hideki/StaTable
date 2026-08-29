"""StaTable のインポート関係を調査するためのテストプログラム"""

import sys
import os
import traceback

# スクリプトの場所をプロジェクトルートとして sys.path に追加
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

print("=" * 60)
print("StaTable インポート関係調査")
print("プロジェクトルート:", PROJECT_ROOT)
print("sys.path 先頭:", sys.path[:3])
print("=" * 60)

# ----------------------------------------------------------------------
# 1. statable.model に定義されている名前
# ----------------------------------------------------------------------
print("\n[1] statable.model の確認")
try:
    import statable.model as model
    print("  import statable.model -> OK")
    print("  model.__file__:", model.__file__)

    names = [name for name in dir(model) if not name.startswith("_")]
    print("  定義されている名前:", names)

    # StateMachine があるか？
    if hasattr(model, "StateMachine"):
        print("  -> StateMachine は model に存在します")
    else:
        print("  -> StateMachine は model に存在しません（正常）")

    # EventDeliveryType があるか？
    if hasattr(model, "EventDeliveryType"):
        print("  -> EventDeliveryType は model に存在します")
        print("     DIRECT =", model.EventDeliveryType.DIRECT)
        print("     QUEUE  =", model.EventDeliveryType.QUEUE)
        print("     DOUBLE =", model.EventDeliveryType.DOUBLE)
    else:
        print("  -> EventDeliveryType が model に存在しません（エラー）")

except Exception:
    print("  !!! statable.model のインポートに失敗")
    traceback.print_exc()

# ----------------------------------------------------------------------
# 2. statable.state_machine に StateMachine があるか
# ----------------------------------------------------------------------
print("\n[2] statable.state_machine の確認")
try:
    from statable.state_machine import StateMachine
    print("  from statable.state_machine import StateMachine -> OK")
    print("  StateMachine:", StateMachine)
except Exception:
    print("  !!! statable.state_machine からの StateMachine インポートに失敗")
    traceback.print_exc()

# ----------------------------------------------------------------------
# 3. statable.global_defs の確認
# ----------------------------------------------------------------------
print("\n[3] statable.global_defs の確認")
try:
    import statable.global_defs as gd
    print("  import statable.global_defs -> OK")
    print("  global_defs.__file__:", gd.__file__)

    if hasattr(gd, "EventQueueDef"):
        print("  -> EventQueueDef は存在します")
    else:
        print("  -> EventQueueDef が存在しません（エラー）")

    if hasattr(gd, "GlobalDefinitions"):
        gd_obj = gd.GlobalDefinitions()
        print("  -> GlobalDefinitions インスタンス生成 OK")
        print("     event_queues 属性:", hasattr(gd_obj, "event_queues"))
    else:
        print("  -> GlobalDefinitions が存在しません（エラー）")

except Exception:
    print("  !!! statable.global_defs のインポートに失敗")
    traceback.print_exc()

# ----------------------------------------------------------------------
# 4. statable_gui.event_delivery_settings_dialog の確認
# ----------------------------------------------------------------------
print("\n[4] statable_gui.event_delivery_settings_dialog の確認")
try:
    from statable_gui.event_delivery_settings_dialog import EventDeliverySettingsDialog
    print("  from statable_gui.event_delivery_settings_dialog import EventDeliverySettingsDialog -> OK")
    print("  EventDeliverySettingsDialog:", EventDeliverySettingsDialog)
except Exception:
    print("  !!! event_delivery_settings_dialog のインポートに失敗")
    traceback.print_exc()

# ----------------------------------------------------------------------
# 5. サンプルデータの確認
# ----------------------------------------------------------------------
print("\n[5] サンプルデータの確認")
try:
    from statable.sample_data import create_sample_state_machine, create_sample_global_defs
    sm = create_sample_state_machine()
    defs = create_sample_global_defs()
    print("  サンプルデータ生成 OK")
    print("  状態数:", len(sm.states))
    print("  イベント数:", len(sm.events))
    print("  グローバル変数数:", len(defs.variables))
    print("  イベントキュー数:", len(defs.event_queues) if hasattr(defs, "event_queues") else "event_queuesなし")

    # イベントの配送タイプ表示
    print("  イベント配送タイプ:")
    for ev_name, ev_obj in sm.events.items():
        print(f"    {ev_name or '(完了)':10s} -> {ev_obj.delivery_type}")
except Exception:
    print("  !!! サンプルデータの生成に失敗")
    traceback.print_exc()

print("\n" + "=" * 60)
print("調査終了")
print("=" * 60)