# tests/test_timer_generator.py
"""
timer_generator.TimerGenerator のユニットテスト

【目的】
  タイマ生成ロジックの回帰防止:
    - generate_struct: v1.5 以降は空を返す（TimerVariables_t 廃止）
    - generate_init_function: Timer_Init の生成
    - generate_update_function: Timer_Update + 派生タイマ計算
    - NULL チェック
    - extra_timers の取り扱い

【対象】
  codegen/timer_generator.py
"""
import pytest

from statable.global_defs import (
    GlobalDefinitions, TimerBaseDef, TimerDerivedDef,
)
from codegen.timer_generator import TimerGenerator


# ============================================================
# ヘルパー
# ============================================================

def _make_gd_with_base_timer():
    """基本タイマ（g_system_tick）を持つ GlobalDefinitions"""
    gd = GlobalDefinitions()
    gd.timer_base = TimerBaseDef(
        variable_name="g_system_tick",
        unit="1ms",
        data_type="volatile uint32_t",
    )
    return gd


def _make_gd_with_derived():
    """基本 + 派生タイマ（10ms）"""
    gd = _make_gd_with_base_timer()
    gd.timer_base.derived.append(TimerDerivedDef(
        period_name="10ms",
        multiplier=10,
        variable_name="g_tick_10ms",
        data_type="uint8_t",
    ))
    return gd


# ============================================================
# generate_struct（v1.5: 空を返す）
# ============================================================

class TestGenerateStruct:

    def test_returns_empty(self):
        """v1.5 §9.6 #83: TimerVariables_t 廃止 → 空文字を返す"""
        gen = TimerGenerator()
        gd = _make_gd_with_base_timer()
        assert gen.generate_struct(gd) == ""

    def test_empty_gd_returns_empty(self):
        gen = TimerGenerator()
        gd = GlobalDefinitions()
        assert gen.generate_struct(gd) == ""


# ============================================================
# タイマ一覧取得
# ============================================================

class TestGetAllTimers:

    def test_base_only(self):
        gen = TimerGenerator()
        gd = _make_gd_with_base_timer()
        timers = gen._get_all_timers(gd)
        assert len(timers) == 1
        assert timers[0].variable_name == "g_system_tick"

    def test_with_extra(self):
        gen = TimerGenerator()
        gd = _make_gd_with_base_timer()
        gd.extra_timers.append(TimerBaseDef(
            variable_name="g_tick_fast",
            unit="100us",
        ))
        timers = gen._get_all_timers(gd)
        assert len(timers) == 2

    def test_derived_timers_aggregated(self):
        gen = TimerGenerator()
        gd = _make_gd_with_derived()
        derived = gen._get_all_derived_timers(gd)
        assert len(derived) == 1
        assert derived[0].variable_name == "g_tick_10ms"


# ============================================================
# generate_init_function
# ============================================================

class TestInitFunction:

    def test_basic_structure(self):
        gen = TimerGenerator()
        gd = _make_gd_with_base_timer()
        result = gen.generate_init_function(gd)
        assert "void Timer_Init(SystemContext_t *ctx)" in result
        assert "ctx == NULL" in result
        assert "Enter Timer_Init" in result
        assert "Exit Timer_Init" in result

    def test_base_timer_init(self):
        gen = TimerGenerator()
        gd = _make_gd_with_base_timer()
        result = gen.generate_init_function(gd)
        assert "ctx->data.g_system_tick = 0;" in result

    def test_derived_timer_init(self):
        gen = TimerGenerator()
        gd = _make_gd_with_derived()
        result = gen.generate_init_function(gd)
        assert "ctx->data.g_system_tick = 0;" in result
        assert "ctx->data.g_tick_10ms = 0;" in result

    def test_null_check_present(self):
        gen = TimerGenerator()
        gd = _make_gd_with_base_timer()
        result = gen.generate_init_function(gd)
        assert "if (ctx == NULL)" in result


# ============================================================
# generate_update_function
# ============================================================

class TestUpdateFunction:

    def test_basic_structure(self):
        gen = TimerGenerator()
        gd = _make_gd_with_base_timer()
        result = gen.generate_update_function(gd)
        assert "void Timer_Update(SystemContext_t *ctx)" in result
        assert "ctx == NULL" in result

    def test_derived_calculation(self):
        """派生タイマ: base / multiplier"""
        gen = TimerGenerator()
        gd = _make_gd_with_derived()
        result = gen.generate_update_function(gd)
        # g_tick_10ms = (uint8_t)(g_system_tick / 10);
        assert "g_tick_10ms" in result
        assert "g_system_tick / 10" in result

    def test_no_derived_no_calc(self):
        """派生なしの場合は計算行が出力されない"""
        gen = TimerGenerator()
        gd = _make_gd_with_base_timer()
        result = gen.generate_update_function(gd)
        # 基本構造のみ（計算行なし）
        assert "g_system_tick" not in result or \
               "g_system_tick /" not in result

    def test_multiple_derived(self):
        gen = TimerGenerator()
        gd = _make_gd_with_derived()
        gd.timer_base.derived.append(TimerDerivedDef(
            period_name="100ms",
            multiplier=100,
            variable_name="g_tick_100ms",
            data_type="uint8_t",
        ))
        result = gen.generate_update_function(gd)
        assert "g_tick_10ms" in result
        assert "g_tick_100ms" in result
        assert "g_system_tick / 10" in result
        assert "g_system_tick / 100" in result


# ============================================================
# generate_all
# ============================================================

class TestGenerateAll:

    def test_all_content(self):
        gen = TimerGenerator()
        gd = _make_gd_with_derived()
        result = gen.generate_all(gd)
        # struct は空なので含まれない
        assert "TimerVariables_t" not in result
        # init / update は含まれる
        assert "void Timer_Init" in result
        assert "void Timer_Update" in result


# ============================================================
# エッジケース
# ============================================================

class TestEdgeCases:

    def test_empty_gd_init(self):
        """空の GlobalDefinitions でもエラーにならない"""
        gen = TimerGenerator()
        gd = GlobalDefinitions()
        result = gen.generate_init_function(gd)
        assert "void Timer_Init" in result

    def test_empty_gd_update(self):
        gen = TimerGenerator()
        gd = GlobalDefinitions()
        result = gen.generate_update_function(gd)
        assert "void Timer_Update" in result

    def test_multiplier_zero_skipped(self):
        """multiplier=0 の場合は除算を出力しない（ゼロ除算回避）"""
        gen = TimerGenerator()
        gd = _make_gd_with_base_timer()
        gd.timer_base.derived.append(TimerDerivedDef(
            period_name="bad",
            multiplier=0,
            variable_name="g_bad",
            data_type="uint8_t",
        ))
        result = gen.generate_update_function(gd)
        # g_bad の除算行は出力されない
        assert "/ 0" not in result