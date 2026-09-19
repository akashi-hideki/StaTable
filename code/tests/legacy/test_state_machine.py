# tests/test_state_machine.py
"""
StateMachine のユニットテスト

【目的】
  コアロジックの回帰防止:
    - 状態 / イベント / 遷移 / ロール関数の追加・削除
    - 整合性チェック（未定義参照の拒否）
    - 遷移削除の連鎖（remove_event で関連遷移も削除）
    - セル単位 / イベント単位の遷移取得
    - dataclass(eq=True) の値等価性（Transition）

【対象】
  statable/state_machine.py
"""
import pytest

from statable.model import State, Event, Transition, RoleFunction
from statable.state_machine import StateMachine


# ============================================================
# ヘルパー
# ============================================================

def _make_sm_with_basic():
    """A, B 状態 + GO イベント + A→B 遷移"""
    sm = StateMachine()
    sm.add_state(State(name="A"))
    sm.add_state(State(name="B"))
    sm.add_event(Event(name="GO"))
    sm.add_transition(Transition(source="A", event="GO", target="B"))
    return sm


# ============================================================
# 状態 (State)
# ============================================================

class TestState:

    def test_add_state(self):
        sm = StateMachine()
        sm.add_state(State(name="Idle"))
        assert "Idle" in sm.states
        assert sm.states["Idle"].name == "Idle"

    def test_add_state_duplicate_raises(self):
        sm = StateMachine()
        sm.add_state(State(name="Idle"))
        with pytest.raises(ValueError, match="already exists"):
            sm.add_state(State(name="Idle"))

    def test_add_state_multiple(self):
        sm = StateMachine()
        for n in ["A", "B", "C"]:
            sm.add_state(State(name=n))
        assert set(sm.states.keys()) == {"A", "B", "C"}


# ============================================================
# イベント (Event)
# ============================================================

class TestEvent:

    def test_add_event(self):
        sm = StateMachine()
        sm.add_event(Event(name="START"))
        assert "START" in sm.events

    def test_add_event_duplicate_raises(self):
        sm = StateMachine()
        sm.add_event(Event(name="START"))
        with pytest.raises(ValueError, match="already exists"):
            sm.add_event(Event(name="START"))

    def test_remove_event(self):
        sm = StateMachine()
        sm.add_event(Event(name="START"))
        sm.remove_event("START")
        assert "START" not in sm.events

    def test_remove_event_missing_no_raise(self):
        """存在しないイベントの削除は無視される（例外なし）"""
        sm = StateMachine()
        sm.remove_event("NOT_EXIST")  # 例外が出ないこと
        assert "NOT_EXIST" not in sm.events

    def test_remove_event_cascades_transitions(self):
        """イベント削除で関連遷移も削除される"""
        sm = StateMachine()
        sm.add_state(State(name="A"))
        sm.add_state(State(name="B"))
        sm.add_event(Event(name="GO"))
        sm.add_event(Event(name="STOP"))
        sm.add_transition(Transition(source="A", event="GO", target="B"))
        sm.add_transition(Transition(source="B", event="STOP", target="A"))
        assert len(sm.transitions) == 2

        sm.remove_event("GO")

        assert "GO" not in sm.events
        assert len(sm.transitions) == 1
        assert sm.transitions[0].event == "STOP"


# ============================================================
# 遷移 (Transition)
# ============================================================

class TestTransition:

    def test_add_transition_valid(self):
        sm = _make_sm_with_basic()
        assert len(sm.transitions) == 1

    def test_add_transition_undefined_source_raises(self):
        sm = StateMachine()
        sm.add_state(State(name="B"))
        sm.add_event(Event(name="GO"))
        with pytest.raises(ValueError, match="Source state"):
            sm.add_transition(Transition(source="A", event="GO", target="B"))

    def test_add_transition_undefined_target_raises(self):
        sm = StateMachine()
        sm.add_state(State(name="A"))
        sm.add_event(Event(name="GO"))
        with pytest.raises(ValueError, match="Target state"):
            sm.add_transition(Transition(source="A", event="GO", target="B"))

    def test_add_transition_undefined_event_raises(self):
        sm = StateMachine()
        sm.add_state(State(name="A"))
        sm.add_state(State(name="B"))
        with pytest.raises(ValueError, match="Event"):
            sm.add_transition(Transition(source="A", event="GO", target="B"))

    def test_add_transition_empty_target_ok(self):
        """target が空（内部遷移）でも登録可能"""
        sm = StateMachine()
        sm.add_state(State(name="A"))
        sm.add_event(Event(name="E"))
        sm.add_transition(Transition(source="A", event="E", target=""))
        assert len(sm.transitions) == 1

    def test_add_transition_empty_event_ok(self):
        """event が空（完了遷移）でも登録可能"""
        sm = StateMachine()
        sm.add_state(State(name="A"))
        sm.add_state(State(name="B"))
        sm.add_transition(Transition(source="A", event="", target="B"))
        assert len(sm.transitions) == 1

    def test_remove_transition(self):
        sm = _make_sm_with_basic()
        trans = sm.transitions[0]
        sm.remove_transition(trans)
        assert len(sm.transitions) == 0

    def test_remove_transition_missing_no_raise(self):
        """
        値が異なる遷移を渡しても、何も削除されない

        注: Transition は dataclass(eq=True) のため、
            値が等しい 2 つのインスタンスは == で等価と見なされる。
            よって「存在しない」を検証するには、
            値が異なる遷移を渡す必要がある。
        """
        sm = _make_sm_with_basic()
        # 値が異なる遷移（target が違う）
        other = Transition(source="A", event="GO", target="A")
        sm.remove_transition(other)  # 例外なし
        assert len(sm.transitions) == 1

    def test_remove_transition_by_value(self):
        """
        値が等しい遷移を渡すと、既存の遷移が削除される

        （dataclass(eq=True) の意図的な動作）
        """
        sm = _make_sm_with_basic()
        # 値が同じ別インスタンス
        same_value = Transition(source="A", event="GO", target="B")
        sm.remove_transition(same_value)
        assert len(sm.transitions) == 0

    def test_multiple_transitions_same_cell(self):
        """同じセルに複数遷移を登録可能（条件分岐）"""
        sm = StateMachine()
        sm.add_state(State(name="A"))
        sm.add_state(State(name="B"))
        sm.add_state(State(name="C"))
        sm.add_event(Event(name="GO"))
        sm.add_transition(Transition(
            source="A", event="GO", target="B", condition="x > 0"))
        sm.add_transition(Transition(
            source="A", event="GO", target="C", condition="x <= 0"))
        assert len(sm.transitions) == 2


# ============================================================
# 初期状態 (Initial State)
# ============================================================

class TestInitialState:

    def test_set_initial(self):
        sm = StateMachine()
        sm.add_state(State(name="Idle"))
        sm.set_initial("Idle")
        assert sm.initial_state == "Idle"

    def test_set_initial_undefined_raises(self):
        sm = StateMachine()
        with pytest.raises(ValueError, match="not defined"):
            sm.set_initial("Ghost")

    def test_initial_state_default_none(self):
        sm = StateMachine()
        assert sm.initial_state is None


# ============================================================
# ロール関数 (RoleFunction)
# ============================================================

class TestRoleFunction:

    def test_add_role_function(self):
        sm = StateMachine()
        sm.add_role_function(RoleFunction(name="Init"))
        assert "Init" in sm.role_functions

    def test_add_role_function_with_namespace(self):
        sm = StateMachine()
        sm.add_role_function(RoleFunction(
            name="Init", namespace="Driver"))
        rf = sm.role_functions["Init"]
        assert rf.namespace == "Driver"
        assert rf.qualified_name == "Driver.Init"

    def test_add_role_function_duplicate_raises(self):
        sm = StateMachine()
        sm.add_role_function(RoleFunction(name="Init"))
        with pytest.raises(ValueError, match="already exists"):
            sm.add_role_function(RoleFunction(name="Init"))

    def test_remove_role_function(self):
        sm = StateMachine()
        sm.add_role_function(RoleFunction(name="Init"))
        sm.remove_role_function("Init")
        assert "Init" not in sm.role_functions

    def test_remove_role_function_missing_no_raise(self):
        sm = StateMachine()
        sm.remove_role_function("Ghost")  # 例外なし


# ============================================================
# セル単位 / イベント単位の遷移取得
# ============================================================

class TestGetTransitions:

    def test_get_transitions_for_cell_basic(self):
        sm = _make_sm_with_basic()
        result = sm.get_transitions_for_cell("A", "GO")
        assert len(result) == 1
        assert result[0].source == "A"
        assert result[0].event == "GO"

    def test_get_transitions_for_cell_empty(self):
        sm = _make_sm_with_basic()
        assert sm.get_transitions_for_cell("B", "GO") == []
        assert sm.get_transitions_for_cell("A", "STOP") == []

    def test_get_transitions_for_cell_multiple(self):
        """同セルに複数遷移"""
        sm = StateMachine()
        sm.add_state(State(name="A"))
        sm.add_state(State(name="B"))
        sm.add_state(State(name="C"))
        sm.add_event(Event(name="GO"))
        sm.add_transition(Transition(
            source="A", event="GO", target="B", condition="x > 0"))
        sm.add_transition(Transition(
            source="A", event="GO", target="C", condition="x <= 0"))
        result = sm.get_transitions_for_cell("A", "GO")
        assert len(result) == 2

    def test_get_transitions_for_event(self):
        """イベント単位の取得（複数 source にまたがる）"""
        sm = StateMachine()
        sm.add_state(State(name="A"))
        sm.add_state(State(name="B"))
        sm.add_state(State(name="C"))
        sm.add_event(Event(name="GO"))
        sm.add_transition(Transition(source="A", event="GO", target="B"))
        sm.add_transition(Transition(source="B", event="GO", target="C"))

        result = sm.get_transitions_for_event("GO")
        assert len(result) == 2
        assert all(t.event == "GO" for t in result)

    def test_get_transitions_for_event_empty(self):
        sm = _make_sm_with_basic()
        assert sm.get_transitions_for_event("STOP") == []


# ============================================================
# レイヤ設定（属性）
# ============================================================

class TestLayerAttributes:

    def test_layer_defaults(self):
        sm = StateMachine()
        assert sm.layer_priority == 5
        assert sm.layer_description == ""
        assert sm.layer_name == ""

    def test_layer_override(self):
        sm = StateMachine()
        sm.layer_priority = 1
        sm.layer_description = "ドライバ層"
        sm.layer_name = "Driver"
        assert sm.layer_priority == 1
        assert sm.layer_description == "ドライバ層"
        assert sm.layer_name == "Driver"


# ============================================================
# 統合シナリオ
# ============================================================

class TestIntegration:

    def test_full_lifecycle(self):
        """状態 → イベント → 遷移 → 初期状態 → ロール関数の一連"""
        sm = StateMachine()
        sm.add_state(State(name="Idle"))
        sm.add_state(State(name="Active"))
        sm.add_event(Event(name="START"))
        sm.add_transition(Transition(source="Idle", event="START", target="Active"))
        sm.set_initial("Idle")
        sm.add_role_function(RoleFunction(name="Init", namespace="App"))

        assert sm.initial_state == "Idle"
        assert len(sm.states) == 2
        assert len(sm.events) == 1
        assert len(sm.transitions) == 1
        assert len(sm.role_functions) == 1

    def test_event_removal_cascade(self):
        """イベント削除 → 関連遷移すべて削除"""
        sm = StateMachine()
        for n in ["A", "B", "C"]:
            sm.add_state(State(name=n))
        sm.add_event(Event(name="GO"))
        sm.add_event(Event(name="STOP"))
        sm.add_transition(Transition(source="A", event="GO", target="B"))
        sm.add_transition(Transition(source="B", event="GO", target="C"))
        sm.add_transition(Transition(source="C", event="STOP", target="A"))
        assert len(sm.transitions) == 3

        sm.remove_event("GO")

        assert len(sm.events) == 1
        assert len(sm.transitions) == 1
        assert sm.transitions[0].event == "STOP"