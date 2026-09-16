# tests/test_struct_generator.py
"""
struct_generator.CStructGenerator のユニットテスト

【目的】
  C コード生成（struct 部分）の回帰防止:
    - SystemData_t / EventFlags_t / SystemContext_t の生成
    - pending_event / pending_event_valid の追加（v1.5）
    - 共通 TransitionContext_t と層別 TransitionContext_<Layer>_t の分離
    - pending_event マクロ（FIRE_EVENT / MAX_CONSECUTIVE_PENDING_EVENTS）
    - カスタム型 / ビットフィールド / 配列メンバー

【対象】
  codegen/struct_generator.py
"""
import pytest

from statable.global_defs import (
    GlobalDefinitions, SystemVariable, EventFlag,
    CustomTypeDef, StructMemberDef,
)
from codegen.struct_generator import CStructGenerator


# ============================================================
# ヘルパー
# ============================================================

def _make_gd(vars=(), flags=(), custom_types=()):
    gd = GlobalDefinitions()
    for v in vars:
        gd.variables.append(v)
    for f in flags:
        gd.flags.append(f)
    for ct in custom_types:
        gd.custom_types.append(ct)
    return gd


# ============================================================
# SystemData_t
# ============================================================

class TestSystemData:

    def test_empty_gd(self):
        gen = CStructGenerator()
        gd = GlobalDefinitions()
        result = gen._generate_system_data(gd)
        assert "typedef struct" in result
        assert "} SystemData_t;" in result

    def test_single_variable(self):
        gen = CStructGenerator()
        gd = _make_gd(vars=[
            SystemVariable(name="counter", type="uint32_t", description="カウンタ")
        ])
        result = gen._generate_system_data(gd)
        assert "counter" in result
        assert "uint32_t" in result

    def test_array_variable(self):
        gen = CStructGenerator()
        gd = _make_gd(vars=[
            SystemVariable(name="buffer", type="uint8_t", array_size=10)
        ])
        result = gen._generate_system_data(gd)
        assert "buffer[10]" in result

    def test_multiple_variables(self):
        gen = CStructGenerator()
        gd = _make_gd(vars=[
            SystemVariable(name="a", type="uint8_t"),
            SystemVariable(name="b", type="uint16_t"),
        ])
        result = gen._generate_system_data(gd)
        assert "a" in result
        assert "b" in result


# ============================================================
# EventFlags_t
# ============================================================

class TestEventFlags:

    def test_empty_flags(self):
        gen = CStructGenerator()
        gd = GlobalDefinitions()
        result = gen._generate_event_flags(gd)
        assert "} EventFlags_t;" in result

    def test_single_flag(self):
        gen = CStructGenerator()
        gd = _make_gd(flags=[
            EventFlag(name="EVT_INIT", min_value=0, max_value=1)
        ])
        result = gen._generate_event_flags(gd)
        assert "EVT_INIT" in result
        assert "uint8_t" in result


# ============================================================
# SystemContext_t
# ============================================================

class TestSystemContext:

    def test_pending_event_added(self):
        """v1.5: pending_event / pending_event_valid が追加される"""
        gen = CStructGenerator()
        gd = GlobalDefinitions()
        result = gen._generate_system_context(gd)
        assert "SystemContext_t" in result
        assert "pending_event" in result
        assert "pending_event_valid" in result

    def test_data_and_flags_members(self):
        gen = CStructGenerator()
        gd = GlobalDefinitions()
        result = gen._generate_system_context(gd)
        assert "SystemData_t data" in result
        assert "EventFlags_t flags" in result


# ============================================================
# 共通 TransitionContext_t
# ============================================================

class TestCommonTransitionContext:

    def test_common_context_generated(self):
        gen = CStructGenerator()
        result = gen.generate_common_transition_context()
        assert "TransitionContext_t" in result
        assert "from_state" in result
        assert "event" in result
        assert "uint16_t" in result


# ============================================================
# 層別 TransitionContext_<Layer>_t
# ============================================================

class TestLayerTransitionContext:

    def test_no_layer_returns_empty(self):
        gen = CStructGenerator()
        result = gen.generate_layer_transition_context("STATE_t", "EVENT_t")
        assert result == ""

    def test_layer_context_generated(self):
        gen = CStructGenerator()
        gen.set_layer("Driver")
        result = gen.generate_layer_transition_context(
            "STATE_Driver_t", "EVENT_Driver_t")
        assert "TransitionContext_Driver_t" in result
        assert "STATE_Driver_t from_state" in result
        assert "EVENT_Driver_t event" in result


# ============================================================
# pending_event マクロ
# ============================================================

class TestPendingEventMacros:

    def test_fire_event_macro(self):
        gen = CStructGenerator()
        result = gen.generate_pending_event_macros()
        assert "#define FIRE_EVENT" in result
        assert "pending_event" in result
        assert "pending_event_valid" in result

    def test_max_consecutive_macro(self):
        gen = CStructGenerator()
        result = gen.generate_pending_event_macros()
        assert "MAX_CONSECUTIVE_PENDING_EVENTS" in result
        assert "#ifndef" in result
        assert "#endif" in result


# ============================================================
# カスタム型
# ============================================================

class TestCustomType:

    def test_empty_members(self):
        gen = CStructGenerator()
        ct = CustomTypeDef(name="MyType")
        result = gen._generate_custom_type(ct)
        assert "typedef struct" in result
        # create_type_name の実装により MyType_t などになる想定

    def test_normal_member(self):
        gen = CStructGenerator()
        ct = CustomTypeDef(name="MyType", members=[
            StructMemberDef(name="x", data_type="int"),
        ])
        result = gen._generate_custom_type(ct)
        assert "int x;" in result

    def test_bit_field_member(self):
        gen = CStructGenerator()
        ct = CustomTypeDef(name="Flags", members=[
            StructMemberDef(name="f1", data_type="uint8_t", bit_width=1),
            StructMemberDef(name="f2", data_type="uint8_t", bit_width=3),
        ])
        result = gen._generate_custom_type(ct)
        assert "f1 : 1" in result
        assert "f2 : 3" in result

    def test_array_member(self):
        gen = CStructGenerator()
        ct = CustomTypeDef(name="Buf", members=[
            StructMemberDef(name="data", data_type="uint8_t", array_size=16),
        ])
        result = gen._generate_custom_type(ct)
        assert "data[16]" in result


# ============================================================
# generate_all_structs
# ============================================================

class TestGenerateAllStructs:

    def test_basic_output(self):
        gen = CStructGenerator()
        gd = _make_gd(
            vars=[SystemVariable(name="counter", type="uint32_t")],
            flags=[EventFlag(name="EVT_INIT", min_value=0, max_value=1)],
        )
        result = gen.generate_all_structs(gd)
        assert "SystemData_t" in result
        assert "EventFlags_t" in result
        assert "SystemContext_t" in result

    def test_custom_types_included(self):
        gen = CStructGenerator()
        gd = _make_gd(custom_types=[
            CustomTypeDef(name="MyType", members=[
                StructMemberDef(name="x", data_type="int"),
            ]),
        ])
        result = gen.generate_all_structs(gd)
        assert "MyType" in result


# ============================================================
# generate_all (dict 形式)
# ============================================================

class TestGenerateAll:

    def test_all_keys_present(self):
        gen = CStructGenerator()
        gd = GlobalDefinitions()
        result = gen.generate_all(gd)
        expected_keys = {
            "custom_types", "system_data", "event_flags",
            "system_context", "common_transition_context",
            "pending_event_macros",
        }
        assert set(result.keys()) == expected_keys

    def test_system_context_content(self):
        gen = CStructGenerator()
        gd = GlobalDefinitions()
        result = gen.generate_all(gd)
        assert "SystemContext_t" in result["system_context"]
        assert "pending_event" in result["system_context"]


# ============================================================
# 後方互換 API
# ============================================================

class TestLegacyAPI:

    def test_generate_struct_dispatch(self):
        gen = CStructGenerator()
        gd = GlobalDefinitions()
        assert "SystemData_t" in gen.generate_struct("system_data", gd)
        assert "EventFlags_t" in gen.generate_struct("event_flags", gd)
        assert "SystemContext_t" in gen.generate_struct("system_context", gd)

    def test_generate_struct_unknown_raises(self):
        gen = CStructGenerator()
        with pytest.raises(ValueError, match="Unknown struct type"):
            gen.generate_struct("unknown", None)