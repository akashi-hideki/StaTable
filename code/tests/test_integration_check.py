"""一括整合性チェックテスト

新設計（タイトル対応含む）への変更後、インポートエラーや基本的な不整合を検出する。
"""

import sys
import os
import traceback

# プロジェクトルートを sys.path に追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    yield application


# ----------------------------------------------------------------------
# 1. ビジネスロジック層のインポート確認
# ----------------------------------------------------------------------
def test_import_model():
    """statable.model のインポートと新属性を確認"""
    from statable.model import (
        State, Event, Transition, StateType, EventKind, RoleFunction,
        EventDeliveryType, EventSourceLayer,
    )
    assert EventDeliveryType.DIRECT.value == "direct"
    assert EventDeliveryType.QUEUE.value == "queue"
    assert EventDeliveryType.DOUBLE.value == "double"

    assert EventSourceLayer.DRIVER.value == "driver"
    assert EventSourceLayer.MIDDLEWARE.value == "middleware"

    # Transition は condition と title を持つ
    t = Transition(source="Idle", event="START", condition="x > 0")
    assert t.condition == "x > 0"
    assert t.title != ""  # 仮タイトルが自動設定される

    # Event は新属性と title を持つ
    e = Event(
        name="TEST",
        delivery_type=EventDeliveryType.QUEUE,
        source_layer=EventSourceLayer.DRIVER,
        data_type="uint8_t",
        data_name="err_code",
        title="テストイベント",
    )
    assert e.delivery_type == EventDeliveryType.QUEUE
    assert e.source_layer == EventSourceLayer.DRIVER
    assert e.data_type == "uint8_t"
    assert e.data_name == "err_code"
    assert e.title == "テストイベント"

    # RoleFunction も title を持つ
    rf = RoleFunction(name="Func1")
    assert rf.title != ""


def test_import_global_defs():
    """statable.global_defs のインポートと新データ構造を確認"""
    from statable.global_defs import (
        GlobalDefinitions, SystemVariable, EventFlag,
        InterruptHandlerDef, InterruptAction,
        DevicePlaceholderDef, TimerBaseDef, TimerDerivedDef,
        EventQueueDef,
    )
    defs = GlobalDefinitions()
    assert hasattr(defs, "event_queues")

    # InterruptHandlerDef は event_names と title を持つ
    intr = InterruptHandlerDef(
        name="TEST_ISR",
        event_names=["EVENT_A", "EVENT_B"],
        actions=[InterruptAction(condition="x > 0", action="foo();")],
    )
    assert intr.event_names == ["EVENT_A", "EVENT_B"]
    assert intr.actions[0].condition == "x > 0"
    assert intr.title != ""

    # EventQueueDef は event_ids と title を持つ
    q = EventQueueDef(
        name="Queue1",
        size=8,
        element_type="uint8_t",
        event_ids=["EVENT_A"],
    )
    assert q.event_ids == ["EVENT_A"]
    assert q.title != ""

    # SystemVariable も title を持つ
    var = SystemVariable(name="temp", type="uint16_t")
    assert var.title != ""

    # EventFlag も title を持つ
    flag = EventFlag(name="FLAG1", min_value=0, max_value=1)
    assert flag.title != ""


def test_import_state_machine():
    """statable.state_machine のインポートと新メソッドを確認"""
    from statable.state_machine import StateMachine
    from statable.model import State, Event, Transition

    sm = StateMachine()
    sm.add_state(State("Idle"))
    sm.add_state(State("Active"))
    sm.add_event(Event("START"))

    trans = Transition(source="Idle", event="START", target="Active")
    sm.add_transition(trans)

    assert sm.get_transitions_for_cell("Idle", "START") == [trans]
    assert sm.get_transitions_for_event("START") == [trans]

    sm.remove_transition(trans)
    assert len(sm.transitions) == 0

    sm.add_transition(trans)
    sm.remove_event("START")
    assert "START" not in sm.events
    assert len(sm.transitions) == 0


# ----------------------------------------------------------------------
# 2. XML I/O のインポート確認
# ----------------------------------------------------------------------
def test_import_xml_io():
    """statable.xml_io のインポートと保存/読込の基本動作を確認"""
    from statable.xml_io import (
        state_machine_to_element, state_machine_from_element,
        global_defs_to_element, global_defs_from_element,
        project_to_xml, project_from_xml,
    )
    from statable.state_machine import StateMachine
    from statable.model import State, Event, Transition, EventDeliveryType, EventSourceLayer
    from statable.global_defs import GlobalDefinitions, SystemVariable

    sm = StateMachine()
    sm.add_state(State("Idle"))
    sm.add_state(State("Active"))
    sm.add_event(Event(
        name="START",
        delivery_type=EventDeliveryType.QUEUE,
        source_layer=EventSourceLayer.DRIVER,
        data_type="uint8_t",
        data_name="param",
        title="起動イベント",
    ))
    sm.add_transition(Transition(source="Idle", event="START", target="Active", title="起動遷移"))
    sm.set_initial("Idle")

    elem = state_machine_to_element(sm)
    sm2 = state_machine_from_element(elem)

    assert sm2.initial_state == "Idle"
    assert "START" in sm2.events
    assert sm2.events["START"].delivery_type == EventDeliveryType.QUEUE
    assert sm2.events["START"].source_layer == EventSourceLayer.DRIVER
    assert sm2.events["START"].data_type == "uint8_t"
    assert sm2.events["START"].data_name == "param"
    assert sm2.events["START"].title == "起動イベント"
    assert sm2.transitions[0].title == "起動遷移"

    defs = GlobalDefinitions()
    defs.variables.append(SystemVariable(name="temp", type="uint16_t", title="温度"))
    defs_elem = global_defs_to_element(defs)
    defs2 = global_defs_from_element(defs_elem)
    assert len(defs2.variables) > 0

    import tempfile
    import os
    fd, path = tempfile.mkstemp(suffix=".xml")
    os.close(fd)
    try:
        project_to_xml([("Tab1", sm)], defs, path)
        tabs, loaded_defs = project_from_xml(path)
        assert len(tabs) == 1
        assert tabs[0][0] == "Tab1"
    finally:
        os.remove(path)


# ----------------------------------------------------------------------
# 3. Mermaid生成の確認
# ----------------------------------------------------------------------
def test_import_mermaid_gen():
    """statable.mermaid_gen のインポートと condition 対応を確認"""
    from statable.mermaid_gen import generate_mermaid
    from statable.state_machine import StateMachine
    from statable.model import State, Event, Transition

    sm = StateMachine()
    sm.add_state(State("Idle"))
    sm.add_state(State("Active"))
    sm.add_event(Event("START"))
    sm.add_transition(Transition(source="Idle", event="START", condition="x > 0", target="Active"))

    code = generate_mermaid(sm)
    assert "Idle --> Active" in code
    assert "START" in code
    assert "x > 0" in code


# ----------------------------------------------------------------------
# 4. GUI層のインポート確認
# ----------------------------------------------------------------------
def test_import_gui_dialogs():
    """GUIダイアログのインポート確認"""
    from statable_gui.event_definition_dialog import EventDefinitionDialog, EventEditDialog
    from statable_gui.event_delivery_settings_dialog import EventDeliverySettingsDialog
    from statable_gui.event_queue_dialog import EventQueueDefsDialog, EventQueueEditDialog
    from statable_gui.global_defs_dialog import GlobalDefinitionsDialog, VariableEditDialog, FlagEditDialog
    from statable_gui.role_function_dialog import RoleFunctionDialog
    from statable_gui.symbol_picker import SymbolPickerWidget
    from statable_gui.condition_edit_dialog import ConditionEditDialog
    from statable_gui.action_edit_dialog import ActionEditDialog
    from statable_gui.dialogs import TransitionListDialog
    from statable_gui.interrupt_handler_edit_dialog import InterruptHandlerEditDialog
    from statable_gui.matrix_table import MatrixTableWidget
    from statable_gui.widgets import StateMachineTab, SettingsPanel, MermaidWidget

    assert True


# ----------------------------------------------------------------------
# 5. GUIダイアログの基本動作確認
# ----------------------------------------------------------------------
def test_event_definition_dialog_creation(app):
    """EventDefinitionDialog の生成と基本動作"""
    from statable_gui.event_definition_dialog import EventDefinitionDialog
    from statable.sample_data import create_sample_state_machine

    sm = create_sample_state_machine()
    dlg = EventDefinitionDialog(sm)
    assert dlg is not None
    assert dlg.table.rowCount() == len(sm.events)
    dlg.close()


def test_event_delivery_settings_creation(app):
    """EventDeliverySettingsDialog の生成と基本動作"""
    from statable_gui.event_delivery_settings_dialog import EventDeliverySettingsDialog
    from statable.sample_data import create_sample_state_machine, create_sample_global_defs

    sm = create_sample_state_machine()
    defs = create_sample_global_defs()
    dlg = EventDeliverySettingsDialog(sm, defs, auto_convert=True)
    assert dlg is not None
    assert dlg.table.rowCount() == len(sm.events)
    assert dlg.auto_convert_check.isChecked() == True
    dlg.close()


def test_event_queue_dialog_creation(app):
    """EventQueueDefsDialog の生成"""
    from statable_gui.event_queue_dialog import EventQueueDefsDialog
    from statable.sample_data import create_sample_global_defs

    defs = create_sample_global_defs()
    dlg = EventQueueDefsDialog(defs)
    assert dlg is not None
    dlg.close()


def test_condition_edit_dialog_creation(app):
    """ConditionEditDialog の生成（タイトル自動設定）"""
    from statable_gui.condition_edit_dialog import ConditionEditDialog
    dlg = ConditionEditDialog(condition_text="x > 0")
    assert dlg.get_condition_text() == "x > 0"
    dlg._on_accept()  # タイトル自動設定
    assert dlg.get_title() != ""
    dlg.close()


def test_transition_list_dialog_creation(app):
    """TransitionListDialog の生成（condition 対応）"""
    from statable_gui.dialogs import TransitionListDialog
    from statable.model import Transition

    trans = Transition(source="Idle", event="START", condition="x > 0", target="Active", title="起動")
    dlg = TransitionListDialog(
        state_names=["Idle", "Active"],
        event_name="START",
        existing_transitions=[trans],
    )
    assert dlg.table.rowCount() == 1
    result = dlg.get_transitions()
    assert result[0].condition == "x > 0"
    assert result[0].title == "起動"
    dlg.close()


def test_interrupt_handler_dialog_creation(app):
    """InterruptHandlerEditDialog の生成"""
    from statable_gui.interrupt_handler_edit_dialog import InterruptHandlerEditDialog
    from statable.sample_data import create_sample_global_defs

    defs = create_sample_global_defs()
    dlg = InterruptHandlerEditDialog(
        global_defs=defs,
        event_names=["START", "STOP"],
    )
    assert dlg is not None
    dlg.close()


def test_matrix_table_creation(app):
    """MatrixTableWidget の生成と配送タイプ表示"""
    from statable_gui.matrix_table import MatrixTableWidget
    from statable.sample_data import create_sample_state_machine

    sm = create_sample_state_machine()
    table = MatrixTableWidget(sm)
    assert table.rowCount() == len(sm.events)
    assert table.columnCount() == len(sm.states)
    table.close()


def test_settings_panel_creation(app):
    """SettingsPanel の生成（イベント辞書タブが無いこと）"""
    from statable_gui.widgets import SettingsPanel
    from statable.sample_data import create_sample_state_machine

    sm = create_sample_state_machine()
    panel = SettingsPanel(sm)
    tab_texts = [panel.tab.tabText(i) for i in range(panel.tab.count())]
    assert "状態一覧" in tab_texts
    assert "ロール関数" in tab_texts
    assert "イベント辞書" not in tab_texts
    panel.close()


# ----------------------------------------------------------------------
# 6. サンプルデータの整合性確認
# ----------------------------------------------------------------------
def test_sample_data_consistency():
    """サンプルデータに矛盾がないこと"""
    from statable.sample_data import create_sample_state_machine, create_sample_global_defs

    sm = create_sample_state_machine()
    defs = create_sample_global_defs()

    for trans in sm.transitions:
        if trans.event:
            assert trans.event in sm.events, f"Undefined event: {trans.event}"

    for trans in sm.transitions:
        assert trans.source in sm.states, f"Undefined source: {trans.source}"
        if trans.target:
            assert trans.target in sm.states, f"Undefined target: {trans.target}"

    assert len(defs.event_queues) > 0

    for queue in defs.event_queues:
        for event_id in queue.event_ids:
            if event_id:
                assert event_id in sm.events, f"Queue event undefined: {event_id}"


# ----------------------------------------------------------------------
# 直接実行用ランナー
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    print("=" * 60)
    print("StaTable 一括整合性チェック")
    print("=" * 60)

    test_functions = [
        test_import_model,
        test_import_global_defs,
        test_import_state_machine,
        test_import_xml_io,
        test_import_mermaid_gen,
        test_import_gui_dialogs,
        lambda: test_event_definition_dialog_creation(app),
        lambda: test_event_delivery_settings_creation(app),
        lambda: test_event_queue_dialog_creation(app),
        lambda: test_condition_edit_dialog_creation(app),
        lambda: test_transition_list_dialog_creation(app),
        lambda: test_interrupt_handler_dialog_creation(app),
        lambda: test_matrix_table_creation(app),
        lambda: test_settings_panel_creation(app),
        test_sample_data_consistency,
    ]

    passed = 0
    failed = 0
    for func in test_functions:
        name = func.__name__ if hasattr(func, "__name__") else "lambda"
        try:
            func()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}")
            traceback.print_exc()
            failed += 1

    print("=" * 60)
    print(f"結果: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)