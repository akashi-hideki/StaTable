# tests/test_transition_generator.py
"""
transition_generator.TransitionGenerator のユニットテスト

【目的】
  遷移生成ロジックの回帰防止:
    - セル単位の遷移関数（前方宣言 + 実装）
    - 遷移テーブル（array / switch / dictionary dispatch）
    - 関数ディクショナリ
    - StateMachine_Process_<Layer> 関数
    - StateMachine_GetNextEvent_<Layer> 関数
    - 層名プレフィックス命名規則
    - 短縮セル関数名（SHORT_CELL_NAMES）

【対象】
  codegen/transition_generator.py
"""
import pytest

from statable.model import State, Event, Transition
from statable.state_machine import StateMachine
from codegen.transition_generator import TransitionGenerator


# ============================================================
# ヘルパー
# ============================================================

def _make_sm(layer_name="", with_transitions=True):
    """基本構造の StateMachine を生成"""
    sm = StateMachine()
    sm.layer_name = layer_name
    sm.add_state(State(name="Idle"))
    sm.add_state(State(name="Active"))
    sm.add_event(Event(name="START"))
    sm.add_event(Event(name="STOP"))
    if with_transitions:
        sm.add_transition(Transition(
            source="Idle", event="START", target="Active", title="起動"))
        sm.add_transition(Transition(
            source="Active", event="STOP", target="Idle", title="停止"))
    return sm


# ============================================================
# 命名規則
# ============================================================

class TestNaming:

    def test_state_enum_no_layer(self):
        gen = TransitionGenerator()
        assert gen._state_enum("Idle") == "STATE_Idle"

    def test_state_enum_with_layer(self):
        gen = TransitionGenerator()
        gen.set_layer("Driver")
        assert gen._state_enum("Idle") == "STATE_Driver_Idle"

    def test_event_enum_no_layer(self):
        gen = TransitionGenerator()
        assert gen._event_enum("START") == "EVENT_START"

    def test_event_enum_with_layer(self):
        gen = TransitionGenerator()
        gen.set_layer("Driver")
        assert gen._event_enum("START") == "EVENT_Driver_START"

    def test_event_enum_empty_is_none(self):
        gen = TransitionGenerator()
        assert gen._event_enum("") == "EVENT_NONE"

    def test_state_type_no_layer(self):
        gen = TransitionGenerator()
        assert gen._state_type() == "STATE_t"

    def test_state_type_with_layer(self):
        gen = TransitionGenerator()
        gen.set_layer("Driver")
        assert gen._state_type() == "STATE_Driver_t"

    def test_context_type_no_layer(self):
        gen = TransitionGenerator()
        assert gen._context_type() == "TransitionContext_t"

    def test_context_type_with_layer(self):
        gen = TransitionGenerator()
        gen.set_layer("Driver")
        assert gen._context_type() == "TransitionContext_Driver_t"

    def test_table_name_with_layer(self):
        gen = TransitionGenerator()
        gen.set_layer("Driver")
        assert gen._table_name() == "transition_table_Driver"


# ============================================================
# セル単位の遷移関数
# ============================================================

class TestCellFunctions:

    def test_empty_sm_no_transitions(self):
        sm = _make_sm(with_transitions=False)
        gen = TransitionGenerator()
        result = gen.generate_transition_cell_functions(sm)
        assert result == ""

    def test_cell_function_generated(self):
        sm = _make_sm()
        gen = TransitionGenerator()
        result = gen.generate_transition_cell_functions(sm)
        # t_Idle_START などが生成される
        assert "t_Idle_START" in result
        assert "static STATE_t" in result
        assert "next_state = STATE_Active" in result

    def test_cell_function_with_layer(self):
        sm = _make_sm(layer_name="Driver")
        gen = TransitionGenerator()
        gen.set_layer("Driver")
        result = gen.generate_transition_cell_functions(sm)
        assert "STATE_Driver_t" in result
        assert "STATE_Driver_Active" in result

    def test_prototypes_generated(self):
        sm = _make_sm()
        gen = TransitionGenerator()
        result = gen.generate_transition_cell_prototypes(sm)
        assert "static STATE_t t_Idle_START" in result
        assert "const TransitionContext_t *transition" in result

    def test_pre_actions_in_cell(self):
        sm = StateMachine()
        sm.add_state(State(name="A"))
        sm.add_state(State(name="B"))
        sm.add_event(Event(name="GO"))
        sm.add_transition(Transition(
            source="A", event="GO", target="B",
            pre_actions=["App.Init"]))
        gen = TransitionGenerator()
        result = gen.generate_transition_cell_functions(sm)
        # RoleFunc_App_Init(transition, ctx) が含まれる
        assert "RoleFunc_App_Init" in result


# ============================================================
# 遷移テーブル
# ============================================================

class TestTransitionTable:

    def test_array_table_generated(self):
        sm = _make_sm()
        gen = TransitionGenerator()
        result = gen.generate_transition_table(sm)
        assert "typedef STATE_t (*TransitionFunc_t)" in result
        assert "transition_matrix" in result
        assert "STATE_MAX" in result
        assert "EVENT_MAX" in result

    def test_array_table_with_layer(self):
        sm = _make_sm(layer_name="Driver")
        gen = TransitionGenerator()
        gen.set_layer("Driver")
        result = gen.generate_transition_table(sm)
        assert "transition_table_Driver" in result
        assert "STATE_Driver_MAX" in result

    def test_table_type_dispatch_array(self):
        sm = _make_sm()
        gen = TransitionGenerator()
        result = gen.generate_transition_table(sm, table_type='array')
        assert "transition_matrix" in result

    def test_table_type_unknown_falls_back(self):
        sm = _make_sm()
        gen = TransitionGenerator()
        # 未実装の switch でも array にフォールバック
        result = gen.generate_transition_table(sm, table_type='unknown')
        assert "transition_matrix" in result

    def test_header_extern_declaration(self):
        sm = _make_sm(layer_name="Driver")
        gen = TransitionGenerator()
        gen.set_layer("Driver")
        result = gen.generate_transition_table_header(sm)
        assert "extern const TransitionFunc_Driver_t" in result
        assert "transition_table_Driver" in result


# ============================================================
# 関数ディクショナリ
# ============================================================

class TestFunctionDictionary:

    def test_dictionary_generated(self):
        sm = _make_sm()
        gen = TransitionGenerator()
        result = gen.generate_function_dictionary(sm)
        assert "typedef struct" in result
        assert "transition_dict" in result
        assert "TRANSITION_DICT_SIZE" in result

    def test_dictionary_with_layer(self):
        sm = _make_sm(layer_name="Driver")
        gen = TransitionGenerator()
        gen.set_layer("Driver")
        result = gen.generate_function_dictionary(sm)
        assert "TransitionDictEntry_Driver_t" in result
        assert "transition_dict_Driver" in result
        assert "TRANSITION_DICT_DRIVER_SIZE" in result


# ============================================================
# Process 関数
# ============================================================

class TestProcessFunction:

    def test_table_driven_generated(self):
        sm = _make_sm()
        gen = TransitionGenerator()
        result = gen.generate_process_function(sm)
        assert "StateMachine_Process" in result
        assert "STATE_t StateMachine_Process" in result
        assert "func != NULL" in result

    def test_process_with_layer(self):
        sm = _make_sm(layer_name="Driver")
        gen = TransitionGenerator()
        gen.set_layer("Driver")
        result = gen.generate_process_function(sm)
        assert "StateMachine_Process_Driver" in result

    def test_process_style_dispatch(self):
        sm = _make_sm()
        gen = TransitionGenerator()
        result = gen.generate_process_function(sm, generation_style='table_driven')
        assert "StateMachine_Process" in result

    def test_process_unknown_style_falls_back(self):
        sm = _make_sm()
        gen = TransitionGenerator()
        result = gen.generate_process_function(sm, generation_style='unknown')
        assert "StateMachine_Process" in result


# ============================================================
# GetNextEvent 関数
# ============================================================

class TestGetNextEvent:

    def test_basic_generated(self):
        sm = _make_sm()
        gen = TransitionGenerator()
        result = gen.generate_get_next_event_function(sm)
        assert "StateMachine_GetNextEvent" in result
        assert "pending_event_valid" in result
        assert "MAX_CONSECUTIVE_PENDING_EVENTS" in result

    def test_with_layer(self):
        sm = _make_sm(layer_name="Driver")
        gen = TransitionGenerator()
        gen.set_layer("Driver")
        result = gen.generate_get_next_event_function(sm)
        assert "StateMachine_GetNextEvent_Driver" in result
        assert "EVENT_Driver_t" in result


# ============================================================
# generate_all (dict 形式)
# ============================================================

class TestGenerateAll:

    def test_all_keys(self):
        sm = _make_sm()
        gen = TransitionGenerator()
        result = gen.generate_all(sm)
        expected_keys = {
            'cell_prototypes', 'cell_functions', 'transition_table',
            'transition_table_header', 'function_dict',
            'process_func', 'get_next_event',
        }
        assert set(result.keys()) == expected_keys

    def test_all_content(self):
        sm = _make_sm()
        gen = TransitionGenerator()
        result = gen.generate_all(sm)
        assert "static STATE_t t_Idle_START" in result['cell_prototypes']
        assert "transition_matrix" in result['transition_table']
        assert "StateMachine_Process" in result['process_func']


# ============================================================
# 後方互換 API
# ============================================================

class TestLegacyAPI:

    def test_generate_all_transitions(self):
        sm = _make_sm()
        gen = TransitionGenerator()
        result = gen.generate_all_transitions(sm)
        # 前方宣言 + テーブル + 実装 + Process が含まれる
        assert "t_Idle_START" in result
        assert "transition_matrix" in result
        assert "StateMachine_Process" in result


# ============================================================
# エッジケース
# ============================================================

class TestEdgeCases:

    def test_empty_sm(self):
        sm = StateMachine()
        gen = TransitionGenerator()
        result = gen.generate_all(sm)
        # 空でも例外が出ない
        assert isinstance(result, dict)
        assert 'process_func' in result

    def test_internal_transition_no_target(self):
        sm = StateMachine()
        sm.add_state(State(name="A"))
        sm.add_event(Event(name="E"))
        sm.add_transition(Transition(
            source="A", event="E", target="", title="内部"))
        gen = TransitionGenerator()
        result = gen.generate_transition_cell_functions(sm)
        # target なしでも生成される
        assert "t_A_E" in result