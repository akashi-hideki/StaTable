# tests/test_enum_generator.py
"""
enum_generator.CEnumGenerator のユニットテスト

【目的】
  C コード生成（enum 部分）の回帰防止:
    - 状態 / イベント / フラグの enum 生成
    - 層名プレフィックス（v1.5 修正の回帰防止）
    - 空名イベントの除外（v1.5 修正の回帰防止）
    - NONE 値（完了イベント）の自動挿入

【対象】
  codegen/enum_generator.py
"""
import pytest

from statable.model import State, Event, StateType, EventKind
from statable.global_defs import EventFlag
from codegen.enum_generator import CEnumGenerator


# ============================================================
# ヘルパー
# ============================================================

def _make_states(*names):
    return [State(name=n) for n in names]


def _make_events(*names, kind=EventKind.SIGNAL):
    return [Event(name=n, kind=kind) for n in names]


def _make_flags(*names):
    return [EventFlag(name=n, min_value=0, max_value=1) for n in names]


# ============================================================
# 状態 enum
# ============================================================

class TestStateEnum:

    def test_empty_states_returns_empty(self):
        gen = CEnumGenerator()
        assert gen.generate_state_enum([]) == ""

    def test_single_state(self):
        gen = CEnumGenerator()
        result = gen.generate_state_enum(_make_states("Idle"))
        assert "typedef enum" in result
        assert "Idle" in result or "IDLE" in result
        assert "} STATE_t;" in result

    def test_multiple_states_values_increment(self):
        gen = CEnumGenerator()
        result = gen.generate_state_enum(_make_states("A", "B", "C"))
        # = 0, = 1, = 2 が含まれる
        assert "= 0" in result
        assert "= 1" in result
        assert "= 2" in result

    def test_max_value_appended(self):
        gen = CEnumGenerator()
        result = gen.generate_state_enum(_make_states("A", "B"))
        assert "STATE_MAX" in result

    def test_layer_name_prefix(self):
        """v1.5: 層名が enum 名にプレフィックスされる"""
        gen = CEnumGenerator()
        gen.set_layer("Driver")
        result = gen.generate_state_enum(_make_states("Idle"))
        assert "STATE_Driver_Idle" in result
        assert "STATE_Driver_MAX" in result
        assert "STATE_Driver_t" in result

    def test_layer_name_no_prefix_when_empty(self):
        """層名なしの場合はプレフィックスなし"""
        gen = CEnumGenerator()
        gen.set_layer("")
        result = gen.generate_state_enum(_make_states("Idle"))
        assert "STATE_Idle" in result
        assert "STATE_t" in result


# ============================================================
# イベント enum
# ============================================================

class TestEventEnum:

    def test_empty_events_returns_empty(self):
        gen = CEnumGenerator()
        assert gen.generate_event_enum([]) == ""

    def test_none_value_inserted(self):
        """NONE = 0 が必ず挿入される"""
        gen = CEnumGenerator()
        result = gen.generate_event_enum(_make_events("START"))
        assert "EVENT_NONE" in result
        assert "= 0" in result

    def test_empty_name_event_filtered(self):
        """
        v1.5 修正: 空名イベントは本処理から除外される
          （NONE と二重定義になるため）
        """
        gen = CEnumGenerator()
        events = [Event(name="START"), Event(name="")]
        result = gen.generate_event_enum(events)
        # EVENT_NONE は 1 回だけ（= 0）
        assert result.count("EVENT_NONE") == 1

    def test_multiple_events(self):
        gen = CEnumGenerator()
        result = gen.generate_event_enum(_make_events("START", "STOP"))
        assert "START" in result
        assert "STOP" in result

    def test_layer_name_prefix(self):
        gen = CEnumGenerator()
        gen.set_layer("Middleware")
        result = gen.generate_event_enum(_make_events("CONNECT"))
        assert "EVENT_Middleware_NONE" in result
        assert "EVENT_Middleware_CONNECT" in result
        assert "EVENT_Middleware_t" in result


# ============================================================
# フラグ enum
# ============================================================

class TestFlagEnum:

    def test_empty_flags_returns_empty(self):
        gen = CEnumGenerator()
        assert gen.generate_flag_enum([]) == ""

    def test_single_flag(self):
        gen = CEnumGenerator()
        result = gen.generate_flag_enum(_make_flags("EVT_INIT"))
        assert "typedef enum" in result
        assert "EVT_INIT" in result or "FLAG_EVT_INIT" in result
        assert "FLAG_t" in result

    def test_no_layer_prefix(self):
        """フラグは層名プレフィックスなし（共通型）"""
        gen = CEnumGenerator()
        gen.set_layer("Driver")
        result = gen.generate_flag_enum(_make_flags("EVT_INIT"))
        # フラグには層名が付かない
        assert "FLAG_Driver" not in result


# ============================================================
# generate_all_enums
# ============================================================

class TestGenerateAllEnums:

    def test_empty_inputs(self):
        gen = CEnumGenerator()
        result = gen.generate_all_enums([], [])
        assert result == ""

    def test_all_sections(self):
        gen = CEnumGenerator()
        result = gen.generate_all_enums(
            _make_states("Idle", "Active"),
            _make_events("START", "STOP"),
            _make_flags("EVT_INIT"),
        )
        assert "STATE_t" in result
        assert "EVENT_t" in result
        assert "FLAG_t" in result

    def test_flags_optional(self):
        gen = CEnumGenerator()
        result = gen.generate_all_enums(
            _make_states("Idle"), _make_events("START"), flags=None)
        assert "STATE_t" in result
        assert "EVENT_t" in result
        # フラグなし


# ============================================================
# ビットマスク enum
# ============================================================

class TestBitMaskEnum:

    def test_empty_returns_empty(self):
        gen = CEnumGenerator()
        assert gen.generate_bit_mask_enum([]) == ""

    def test_bit_values(self):
        gen = CEnumGenerator()
        result = gen.generate_bit_mask_enum(_make_flags("F0", "F1", "F2"))
        assert "0x01" in result
        assert "0x02" in result
        assert "0x04" in result

    def test_type_name(self):
        gen = CEnumGenerator()
        result = gen.generate_bit_mask_enum(_make_flags("F0"))
        assert "FLAG_MASK_t" in result


# ============================================================
# generate_enum (dispatch)
# ============================================================

class TestGenerateEnumDispatch:

    def test_state_dispatch(self):
        gen = CEnumGenerator()
        result = gen.generate_enum("state", _make_states("Idle"))
        assert "STATE_t" in result

    def test_event_dispatch(self):
        gen = CEnumGenerator()
        result = gen.generate_enum("event", _make_events("GO"))
        assert "EVENT_t" in result

    def test_flag_dispatch(self):
        gen = CEnumGenerator()
        result = gen.generate_enum("flag", _make_flags("F0"))
        assert "FLAG_t" in result

    def test_unknown_type_returns_empty(self):
        gen = CEnumGenerator()
        assert gen.generate_enum("unknown", []) == ""