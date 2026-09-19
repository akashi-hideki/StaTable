# tests/test_variable_generator.py
"""
variable_generator.VariableGenerator のユニットテスト

【目的】
  C コード生成（変数マクロ・初期化関数）の回帰防止:
    - v1.6 §9.8 #92: DATA_COUNTER(ctx) → data.counter（フィールド名 snake）
    - カスタム型の memset 初期化（v1.5 修正）
    - 配列変数の memset 初期化
    - フラグアクセスマクロ
    - init 関数の構造

【対象】
  codegen/variable_generator.py
"""
import pytest

from statable.global_defs import (
    GlobalDefinitions, SystemVariable, EventFlag,
)
from codegen.variable_generator import VariableGenerator


# ============================================================
# ヘルパー
# ============================================================

def _make_gd(vars=(), flags=()):
    gd = GlobalDefinitions()
    for v in vars:
        gd.variables.append(v)
    for f in flags:
        gd.flags.append(f)
    return gd


# ============================================================
# データアクセスマクロ（v1.6 修正の回帰防止）
# ============================================================

class TestDataMacro:

    def test_macro_name_upper(self):
        """マクロ名は UPPER_SNAKE"""
        gen = VariableGenerator()
        var = SystemVariable(name="counter", type="uint32_t")
        result = gen._generate_data_macro(var)
        assert "DATA_COUNTER" in result

    def test_field_name_snake(self):
        """
        v1.6 §9.8 #92 修正: フィールド名は snake_case のまま
          （旧バグ: DATA_COUNTER(ctx) → ((ctx)->data.COUNTER)）
        """
        gen = VariableGenerator()
        var = SystemVariable(name="counter", type="uint32_t")
        result = gen._generate_data_macro(var)
        assert "data.counter" in result
        assert "data.COUNTER" not in result

    def test_camel_case_var(self):
        """キャメルケースの変数 → マクロ UPPER、フィールドは snake"""
        gen = VariableGenerator()
        var = SystemVariable(name="retryCount", type="uint8_t")
        result = gen._generate_data_macro(var)
        assert "DATA_RETRY_COUNT" in result
        # sanitize_identifier の実装次第だが、フィールドは snake 系
        assert "data." in result


class TestFlagMacro:

    def test_flag_macro_name(self):
        gen = VariableGenerator()
        flag = EventFlag(name="EVT_INIT_DONE", min_value=0, max_value=1)
        result = gen._generate_flag_macro(flag)
        assert "FLAG_EVT_INIT_DONE" in result

    def test_flag_field_name(self):
        gen = VariableGenerator()
        flag = EventFlag(name="EVT_INIT_DONE", min_value=0, max_value=1)
        result = gen._generate_flag_macro(flag)
        assert "flags.EVT_INIT_DONE" in result


# ============================================================
# generate_all_macros
# ============================================================

class TestGenerateAllMacros:

    def test_empty(self):
        gen = VariableGenerator()
        gd = GlobalDefinitions()
        assert gen.generate_all_macros(gd) == ""

    def test_variables_only(self):
        gen = VariableGenerator()
        gd = _make_gd(vars=[
            SystemVariable(name="counter", type="uint32_t"),
            SystemVariable(name="error_code", type="uint8_t"),
        ])
        result = gen.generate_all_macros(gd)
        assert "DATA_COUNTER" in result
        assert "DATA_ERROR_CODE" in result

    def test_flags_only(self):
        gen = VariableGenerator()
        gd = _make_gd(flags=[
            EventFlag(name="EVT_INIT", min_value=0, max_value=1),
        ])
        result = gen.generate_all_macros(gd)
        assert "FLAG_EVT_INIT" in result

    def test_mixed(self):
        gen = VariableGenerator()
        gd = _make_gd(
            vars=[SystemVariable(name="counter", type="uint32_t")],
            flags=[EventFlag(name="EVT_INIT", min_value=0, max_value=1)],
        )
        result = gen.generate_all_macros(gd)
        assert "DATA_COUNTER" in result
        assert "FLAG_EVT_INIT" in result


# ============================================================
# 初期化コード生成
# ============================================================

class TestInitCode:

    def test_normal_variable_init(self):
        gen = VariableGenerator()
        var = SystemVariable(name="counter", type="uint32_t")
        result = gen._generate_normal_init(var)
        assert "ctx->data.counter" in result
        assert "= 0" in result

    def test_custom_type_uses_memset(self):
        """v1.5 修正: カスタム型は memset で初期化"""
        gen = VariableGenerator()
        var = SystemVariable(name="my_struct", type="MyCustomType")
        result = gen._generate_normal_init(var)
        assert "memset" in result
        assert "ctx->data.my_struct" in result

    def test_array_init_uses_memset(self):
        gen = VariableGenerator()
        var = SystemVariable(name="buffer", type="uint8_t", array_size=16)
        result = gen._generate_array_init(var)
        assert "memset" in result
        assert "buffer" in result

    def test_bool_default(self):
        gen = VariableGenerator()
        var = SystemVariable(name="flag", type="bool", default_value="false")
        result = gen._generate_normal_init(var)
        assert "= false" in result

    def test_flag_init(self):
        gen = VariableGenerator()
        flag = EventFlag(name="EVT_INIT", min_value=0, max_value=1)
        result = gen._generate_flag_init(flag)
        assert "ctx->flags.EVT_INIT" in result
        assert "= 0" in result


# ============================================================
# init 関数
# ============================================================

class TestInitFunction:

    def test_basic_structure(self):
        gen = VariableGenerator()
        gd = GlobalDefinitions()
        result = gen.generate_init_function(gd)
        # void <name>(SystemContext_t *ctx) が含まれる
        assert "SystemContext_t *ctx" in result
        assert "NULL" in result  # NULL チェック
        assert "pending_event" in result  # pending_event 初期化

    def test_with_variables(self):
        gen = VariableGenerator()
        gd = _make_gd(vars=[
            SystemVariable(name="counter", type="uint32_t"),
        ])
        result = gen.generate_init_function(gd)
        assert "ctx->data.counter" in result

    def test_with_flags(self):
        gen = VariableGenerator()
        gd = _make_gd(flags=[
            EventFlag(name="EVT_INIT", min_value=0, max_value=1),
        ])
        result = gen.generate_init_function(gd)
        assert "ctx->flags.EVT_INIT" in result

    def test_pending_event_init(self):
        """pending_event / pending_event_valid の初期化"""
        gen = VariableGenerator()
        gd = GlobalDefinitions()
        result = gen.generate_init_function(gd)
        assert "ctx->pending_event = 0" in result
        assert "ctx->pending_event_valid = false" in result


# ============================================================
# generate_all (dict 形式)
# ============================================================

class TestGenerateAll:

    def test_all_keys(self):
        gen = VariableGenerator()
        gd = GlobalDefinitions()
        result = gen.generate_all(gd)
        assert "init_function" in result
        assert "macros" in result

    def test_init_function_key(self):
        gen = VariableGenerator()
        gd = GlobalDefinitions()
        result = gen.generate_all(gd)
        assert "SystemContext_t *ctx" in result["init_function"]


# ============================================================
# generate_variable (後方互換 API)
# ============================================================

class TestLegacyAPI:

    def test_dispatch_macro(self):
        gen = VariableGenerator()
        var = SystemVariable(name="counter", type="uint32_t")
        result = gen.generate_variable("macro", var)
        assert "DATA_COUNTER" in result

    def test_dispatch_init(self):
        gen = VariableGenerator()
        var = SystemVariable(name="counter", type="uint32_t")
        result = gen.generate_variable("init", var)
        assert "counter" in result

    def test_dispatch_flag(self):
        gen = VariableGenerator()
        flag = EventFlag(name="EVT_INIT", min_value=0, max_value=1)
        result = gen.generate_variable("flag", flag)
        assert "EVT_INIT" in result

    def test_unknown_raises(self):
        gen = VariableGenerator()
        with pytest.raises(ValueError, match="Unknown variable type"):
            gen.generate_variable("unknown", None)