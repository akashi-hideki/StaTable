# tests/test_interrupt_generator.py
"""
interrupt_generator.InterruptGenerator のユニットテスト

【目的】
  ISR 生成の回帰防止:
    - アクション解析（Namespace.Name / identifier(args) / そのまま）
    - 使用ロール関数・変数の自動抽出
    - ISR 関数の完全生成
    - 層名による名前空間変換
    - マーカー名生成

【対象】
  codegen/interrupt_generator.py
"""
import pytest

from statable.global_defs import InterruptHandlerDef, InterruptAction
from codegen.interrupt_generator import InterruptGenerator


# ============================================================
# ヘルパー
# ============================================================

def _make_handler(name="TIMER0", actions=None, description=""):
    return InterruptHandlerDef(
        name=name,
        description=description,
        actions=actions or [],
    )


# ============================================================
# 名前生成
# ============================================================

class TestNaming:

    def test_isr_function_name(self):
        gen = InterruptGenerator()
        h = _make_handler(name="TIMER0")
        assert gen._get_isr_function_name(h) == "ISR_TIMER0"

    def test_isr_function_name_underscore(self):
        gen = InterruptGenerator()
        h = _make_handler(name="UART_RX")
        # PascalCase 変換でアンダースコアが除去される想定
        result = gen._get_isr_function_name(h)
        assert result.startswith("ISR_")

    def test_marker_name(self):
        gen = InterruptGenerator()
        h = _make_handler(name="TIMER0")
        assert gen._get_marker_name(h) == "TIMER0"


# ============================================================
# アクション解析
# ============================================================

class TestParseAction:

    def test_namespace_name_form(self):
        """App.Init → RoleFunc_App_Init(NULL, ctx)"""
        gen = InterruptGenerator()
        c_code, used = gen._parse_action("App.Init")
        assert c_code == "RoleFunc_App_Init(NULL, ctx)"
        assert used == ["App.Init"]

    def test_namespace_name_with_args(self):
        """App.Init(1, 2) → RoleFunc_App_Init(NULL, ctx)"""
        gen = InterruptGenerator()
        c_code, used = gen._parse_action("App.Init(1, 2)")
        assert "RoleFunc_App_Init(NULL, ctx)" in c_code
        assert "App.Init" in used

    def test_identifier_with_args(self):
        """identifier(args) → RoleFunc_Layer_PascalId(NULL, ctx)"""
        gen = InterruptGenerator()
        gen.set_layer("Driver")
        c_code, used = gen._parse_action("check_rx()")
        assert c_code == "RoleFunc_Driver_CheckRx(NULL, ctx)"

    def test_identifier_no_layer(self):
        """層なし: RoleFunc_PascalId(NULL, ctx)"""
        gen = InterruptGenerator()
        c_code, used = gen._parse_action("check_rx()")
        assert c_code == "RoleFunc_CheckRx(NULL, ctx)"

    def test_c_keyword_unchanged(self):
        """C キーワードはそのまま"""
        gen = InterruptGenerator()
        c_code, used = gen._parse_action("if(x)")
        assert c_code == "if(x)"
        assert used == []

    def test_rolefunc_prefix_unchanged(self):
        """既に RoleFunc_ で始まる場合はそのまま"""
        gen = InterruptGenerator()
        c_code, used = gen._parse_action("RoleFunc_Driver_Init()")
        assert c_code == "RoleFunc_Driver_Init()"

    def test_plain_c_statement(self):
        """その他の C 文はそのまま"""
        gen = InterruptGenerator()
        c_code, used = gen._parse_action("ctx->data.counter++")
        assert c_code == "ctx->data.counter++"

    def test_empty_action(self):
        gen = InterruptGenerator()
        c_code, used = gen._parse_action("")
        assert c_code == ""
        assert used == []

    def test_whitespace_action(self):
        gen = InterruptGenerator()
        c_code, used = gen._parse_action("   ")
        assert c_code == ""


# ============================================================
# アクション + 条件
# ============================================================

class TestParseActionWithSemicolon:

    def test_simple_action(self):
        gen = InterruptGenerator()
        action = InterruptAction(action="ctx->data.x++")
        c_code, used = gen._parse_action_with_semicolon(action)
        assert "ctx->data.x++;" in c_code

    def test_condition_action(self):
        gen = InterruptGenerator()
        action = InterruptAction(
            action="ctx->data.x++", condition="ctx->data.y > 0")
        c_code, used = gen._parse_action_with_semicolon(action)
        assert "if (ctx->data.y > 0)" in c_code
        assert "ctx->data.x++;" in c_code


# ============================================================
# 使用シンボル抽出
# ============================================================

class TestExtractSymbols:

    def test_used_role_functions(self):
        gen = InterruptGenerator()
        h = _make_handler(actions=[
            InterruptAction(action="App.HandleTick"),
            InterruptAction(action="Driver.CheckRx"),
        ])
        used_rfs, used_vars = gen.extract_used_symbols(h)
        assert "App.HandleTick" in used_rfs
        assert "Driver.CheckRx" in used_rfs

    def test_used_variables(self):
        gen = InterruptGenerator()
        h = _make_handler(actions=[
            InterruptAction(action="ctx->data.counter++"),
            InterruptAction(action="ctx->data.rx_ready = true"),
        ])
        used_rfs, used_vars = gen.extract_used_symbols(h)
        assert "counter" in used_vars
        assert "rx_ready" in used_vars

    def test_used_flags(self):
        gen = InterruptGenerator()
        h = _make_handler(actions=[
            InterruptAction(action="ctx->flags.EVT_INIT = 1"),
        ])
        _, used_vars = gen.extract_used_symbols(h)
        assert "EVT_INIT" in used_vars

    def test_no_duplicates(self):
        gen = InterruptGenerator()
        h = _make_handler(actions=[
            InterruptAction(action="ctx->data.x++"),
            InterruptAction(action="ctx->data.x--"),
        ])
        _, used_vars = gen.extract_used_symbols(h)
        assert used_vars.count("x") == 1

    def test_update_handler_symbols(self):
        gen = InterruptGenerator()
        h = _make_handler(actions=[
            InterruptAction(action="App.HandleTick"),
            InterruptAction(action="ctx->data.counter++"),
        ])
        gen.update_handler_symbols(h)
        assert "App.HandleTick" in h.used_role_functions
        assert "counter" in h.used_variables


# ============================================================
# ISR 完全生成
# ============================================================

class TestGenerateISR:

    def test_basic_structure(self):
        gen = InterruptGenerator()
        h = _make_handler(name="TIMER0", actions=[
            InterruptAction(action="ctx->data.counter++"),
        ])
        result = gen.generate_isr(h)
        assert "void ISR_TIMER0(void)" in result
        assert "SystemContext_t *ctx = &g_ctx" in result
        assert "Enter ISR: TIMER0" in result
        assert "Exit ISR: TIMER0" in result
        assert "ctx->data.counter++;" in result

    def test_role_func_call_in_isr(self):
        """App.HandleTick → RoleFunc_App_HandleTick(NULL, ctx)"""
        gen = InterruptGenerator()
        h = _make_handler(actions=[
            InterruptAction(action="App.HandleTick"),
        ])
        result = gen.generate_isr(h)
        assert "RoleFunc_App_HandleTick(NULL, ctx)" in result

    def test_user_marker(self):
        gen = InterruptGenerator()
        h = _make_handler(name="TIMER0")
        result = gen.generate_isr(h)
        assert "[[STABLE_USER_CODE_START:TIMER0]]" in result
        assert "[[STABLE_USER_CODE_END:TIMER0]]" in result

    def test_condition_in_action(self):
        gen = InterruptGenerator()
        h = _make_handler(actions=[
            InterruptAction(
                action="ctx->data.x++",
                condition="ctx->data.y > 0"),
        ])
        result = gen.generate_isr(h)
        assert "if (ctx->data.y > 0)" in result

    def test_layer_name_used(self):
        gen = InterruptGenerator()
        gen.set_layer("Driver")
        h = _make_handler(actions=[
            InterruptAction(action="check_rx()"),
        ])
        result = gen.generate_isr(h)
        assert "RoleFunc_Driver_CheckRx" in result


# ============================================================
# 空ハンドラ
# ============================================================

class TestEmptyHandler:

    def test_no_actions(self):
        """
        アクションが空の場合の ISR 生成

        実装仕様:
          - actions が空なら _execute_actions_step は空リストを返す
          - → アクション部分はセクションごと出力されない
          - 「アクション未定義」コメントは、actions が非空だが
            全アクションがパース失敗した場合にのみ出力される
        """
        gen = InterruptGenerator()
        h = _make_handler(name="EMPTY")
        result = gen.generate_isr(h)
        # 基本構造は生成される
        assert "void ISR_EMPTY(void)" in result
        assert "SystemContext_t *ctx = &g_ctx" in result
        # アクションが空 → アクションセクションが出力されない
        assert "アクション（自動生成）" not in result
        # ユーザーマーカーは存在する
        assert "[[STABLE_USER_CODE_START:EMPTY]]" in result

    def test_invalid_actions_shows_undefined_comment(self):
        """
        actions が非空だが全て無効（空文字）な場合:
          → 「（アクション未定義）」コメントが出力される
        """
        gen = InterruptGenerator()
        h = _make_handler(name="INVALID", actions=[
            InterruptAction(action=""),      # 空 → パース結果空
        ])
        result = gen.generate_isr(h)
        # アクションセクション自体は出力される（actions が非空のため）
        assert "アクション（自動生成）" in result
        # 有効なアクションが 1 つもないので未定義コメント
        assert "アクション未定義" in result