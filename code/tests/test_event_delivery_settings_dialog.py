"""EventDeliverySettingsDialog の単体テスト（pytest / 直接実行 両対応）"""

import sys
import os
import traceback
import pytest

# プロジェクトルートを sys.path に追加（tests フォルダの親）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication

from statable.state_machine import StateMachine
from statable.model import Event, EventDeliveryType
from statable.global_defs import GlobalDefinitions, InterruptHandlerDef, InterruptAction
from statable.sample_data import create_sample_state_machine, create_sample_global_defs
from statable_gui.event_delivery_settings_dialog import EventDeliverySettingsDialog


# ----------------------------------------------------------------------
# pytest フィクスチャ：QApplication をモジュール全体で共有
# ----------------------------------------------------------------------
@pytest.fixture(scope="module")
def app():
    """QApplication を一度だけ生成し、テスト全体で共有する"""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    yield application


def _find_row_by_event_name(dlg: EventDeliverySettingsDialog, event_name: str) -> int:
    """イベント名から行番号を探す"""
    for row in range(dlg.table.rowCount()):
        item = dlg.table.item(row, 0)
        if item and item.text() == event_name:
            return row
    return -1


def test_dialog_initialization(app):
    """ダイアログが正しく初期化されることを確認"""
    sm = create_sample_state_machine()
    defs = create_sample_global_defs()

    dlg = EventDeliverySettingsDialog(sm, defs, auto_convert=True)
    assert dlg is not None
    assert dlg.table.rowCount() == len(sm.events)
    assert dlg.auto_convert_check.isChecked() == True

    event_names = [dlg.table.item(row, 0).text() for row in range(dlg.table.rowCount())]
    assert "start" in event_names
    assert "error" in event_names
    assert "（完了）" in event_names

    dlg.close()


def test_isr_usage_detection(app):
    """ISR使用イベントが自動的にDOUBLEへ変換されることを確認"""
    sm = create_sample_state_machine()
    defs = create_sample_global_defs()

    # 割り込みに "start" イベントを関連付ける
    defs.interrupts.append(InterruptHandlerDef(
        name="TEST_ISR",
        event_name="start",
        actions=[InterruptAction(action="start_motor();")]
    ))

    dlg = EventDeliverySettingsDialog(sm, defs, auto_convert=True)

    row = _find_row_by_event_name(dlg, "start")
    assert row >= 0

    combo = dlg.table.cellWidget(row, 1)
    assert combo.currentData() == EventDeliveryType.DIRECT
    assert dlg.table.item(row, 2).text() == "あり"
    assert dlg.table.item(row, 3).text() == EventDeliveryType.DOUBLE.value

    dlg.close()


def test_delivery_type_update_and_save(app):
    """配送タイプの変更と保存が正しく反映されることを確認"""
    sm = create_sample_state_machine()
    defs = create_sample_global_defs()

    # 自動変換OFFで、DIRECTのまま保存できるか確認
    dlg = EventDeliverySettingsDialog(sm, defs, auto_convert=False)

    # "error" イベント（デフォルトは QUEUE）を DIRECT に変更
    row = _find_row_by_event_name(dlg, "error")
    assert row >= 0

    combo = dlg.table.cellWidget(row, 1)
    combo.setCurrentIndex(combo.findData(EventDeliveryType.DIRECT))
    dlg._update_converted_column()

    # 自動変換OFFなので、変換後も DIRECT のまま
    assert dlg.table.item(row, 3).text() == EventDeliveryType.DIRECT.value

    # OKで保存
    dlg._on_accept()

    # モデル側の delivery_type が更新されている
    assert sm.events["error"].delivery_type == EventDeliveryType.DIRECT

    dlg.close()


# ----------------------------------------------------------------------
# 直接実行時のテストランナー
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    print("=" * 60)
    print("EventDeliverySettingsDialog テスト開始")
    print("=" * 60)

    test_functions = [
        ("test_dialog_initialization", test_dialog_initialization),
        ("test_isr_usage_detection", test_isr_usage_detection),
        ("test_delivery_type_update_and_save", test_delivery_type_update_and_save),
    ]

    for name, func in test_functions:
        try:
            func(app)
            print(f"  [PASS] {name}")
        except Exception as e:
            print(f"  [FAIL] {name}")
            traceback.print_exc()

    print("=" * 60)
    print("テスト終了")
    print("=" * 60)