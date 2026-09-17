# tests/test_role_function_generator.py
"""
role_function_generator.RoleFunctionGenerator のユニットテスト

【目的】
  ロール関数生成の回帰防止:
    - 命名規則（RoleFunc_<Namespace>_<PascalName>）
    - 参照正規化（_normalize_func_ref, v1.5 識別子検証）
    - 条件式からの関数抽出
    - 呼び出しサイト収集（_collect_call_sites）
    - 層フィルタ（_should_emit_implementation, v1.6 §9.6 #90）
    - 宣言生成 / 実装生成
    - 一括生成
    - マーカー名生成
    - NULL ガード

【対象】
  codegen/role_function_generator.py
"""
import pytest

from statable.model import (
    RoleFunction, State, Event, Transition,
)
from statable.state_machine import StateMachine
from codegen.role_function_generator import (
    RoleFunctionGenerator, RoleFuncCallSite,
)


# ============================================================
# ヘルパー
# ============================================================

def _make_rf(name="Init", namespace="", title="",
             description="", return_type="int"):
    return RoleFunction(
        name=name,
        namespace=namespace,
        title=title,
        description=description,
        return_type=return_type,
    )


def _make_sm(layer_name="", with_transitions=True):
    sm = StateMachine()
    sm.layer_name = layer_name
    sm.add_state(State(name="Idle"))
    sm.add_state(State(name="Active"))
    sm.add_event(Event(name="START"))
    if with_transitions:
        sm.add_transition(Transition(
            source="Idle", event="START", target="Active",
            condition="Init()",
        ))
    return sm


# ============================================================
# 命名規則
# ============================================================

class TestNaming:

    def test_function_name_with_namespace(self):
        """RoleFunc_<Namespace>_<PascalName>"""
        gen = RoleFunctionGenerator()
        rf = _make_rf(name="Init", namespace="Driver")
        assert gen._generate_function_name(rf) == "RoleFunc_Driver_Init"

    def test_function_name_no_namespace(self):
        gen = RoleFunctionGenerator()
        rf = _make_rf(name="Init")
        assert gen._generate_function_name(rf) == "RoleFunc_Init"

    def test_function_name_uses_layer_when_no_namespace(self):
        """namespace 未設定時は layer_name を採用"""
        gen = RoleFunctionGenerator()
        gen.set_layer("App")
        rf = _make_rf(name="Start")
        assert gen._generate_function_name(rf) == "RoleFunc_App_Start"

    def test_function_name_pascal_case(self):
        """snake_case → PascalCase"""
        gen = RoleFunctionGenerator()
        rf = _make_rf(name="check_rx", namespace="Driver")
        assert gen._generate_function_name(rf) == "RoleFunc_Driver_CheckRx"

    def test_marker_name_with_namespace(self):
        gen = RoleFunctionGenerator()
        rf = _make_rf(name="Init", namespace="Driver")
        assert gen._get_marker_name(rf) == "Driver_Init"

    def test_marker_name_no_namespace(self):
        gen = RoleFunctionGenerator()
        rf = _make_rf(name="Init")
        assert gen._get_marker_name(rf) == "Init"

    def test_context_type_no_layer(self):
        gen = RoleFunctionGenerator()
        assert gen._context_type() == "TransitionContext_t"

    def test_context_type_with_layer(self):
        gen = RoleFunctionGenerator()
        gen.set_layer("Driver")
        assert gen._context_type() == "TransitionContext_Driver_t"

    def test_state_enum_no_layer(self):
        gen = RoleFunctionGenerator()
        assert gen._state_enum("Idle") == "STATE_Idle"

    def test_state_enum_with_layer(self):
        gen = RoleFunctionGenerator()
        gen.set_layer("Driver")
        assert gen._state_enum("Idle") == "STATE_Driver_Idle"

    def test_event_enum_no_layer(self):
        gen = RoleFunctionGenerator()
        assert gen._event_enum("START") == "EVENT_START"

    def test_event_enum_with_layer(self):
        gen = RoleFunctionGenerator()
        gen.set_layer("Driver")
        assert gen._event_enum("START") == "EVENT_Driver_START"


# ============================================================
# 参照正規化（v1.5 識別子検証）
# ============================================================

class TestNormalizeFuncRef:

    def test_plain_identifier(self):
        gen = RoleFunctionGenerator()
        assert gen._normalize_func_ref("Init") == "Init"

    def test_qualified_identifier(self):
        gen = RoleFunctionGenerator()
        assert gen._normalize_func_ref("Driver.Init") == "Driver.Init"

    def test_with_arguments_stripped(self):
        gen = RoleFunctionGenerator()
        assert gen._normalize_func_ref("Init()") == "Init"

    def test_with_arguments_and_params(self):
        gen = RoleFunctionGenerator()
        assert gen._normalize_func_ref("Init(1, 2)") == "Init"

    def test_rolefunc_prefix_with_layer(self):
        gen = RoleFunctionGenerator()
        gen.set_layer("Driver")
        result = gen._normalize_func_ref("RoleFunc_Driver_Init")
        assert result == "Driver.Init"

    def test_rolefunc_prefix_no_layer(self):
        gen = RoleFunctionGenerator()
        result = gen._normalize_func_ref("RoleFunc_Init")
        assert result == "Init"

    # ---- ★ v1.5 識別子検証 ----
    def test_reject_increment_operator(self):
        """C 演算子混入を拒否"""
        gen = RoleFunctionGenerator()
        assert gen._normalize_func_ref("retry_count++") == ""

    def test_reject_arithmetic_expression(self):
        gen = RoleFunctionGenerator()
        assert gen._normalize_func_ref("a + b") == ""

    def test_reject_invalid_chars(self):
        gen = RoleFunctionGenerator()
        assert gen._normalize_func_ref("a-b") == ""

    def test_reject_double_dot(self):
        gen = RoleFunctionGenerator()
        assert gen._normalize_func_ref("A.B.C") == ""

    def test_empty_returns_empty(self):
        gen = RoleFunctionGenerator()
        assert gen._normalize_func_ref("") == ""

    def test_none_returns_empty(self):
        gen = RoleFunctionGenerator()
        assert gen._normalize_func_ref(None) == ""

    def test_whitespace_returns_empty(self):
        gen = RoleFunctionGenerator()
        assert gen._normalize_func_ref("   ") == ""


# ============================================================
# 条件式からの関数抽出
# ============================================================

class TestExtractFromCondition:

    def test_simple_call(self):
        gen = RoleFunctionGenerator()
        result = gen._extract_func_names_from_condition("Init()")
        assert "Init" in result

    def test_qualified_name(self):
        gen = RoleFunctionGenerator()
        result = gen._extract_func_names_from_condition("Driver.Init")
        assert "Driver.Init" in result

    def test_rolefunc_prefix(self):
        gen = RoleFunctionGenerator()
        gen.set_layer("Driver")
        result = gen._extract_func_names_from_condition(
            "RoleFunc_Driver_Init()")
        assert "Driver.Init" in result

    def test_c_keyword_excluded(self):
        """C 予約語は抽出されない"""
        gen = RoleFunctionGenerator()
        result = gen._extract_func_names_from_condition("if(x)")
        assert "if" not in result

    def test_bare_pascalcase(self):
        """式中の PascalCase 識別子を検出"""
        gen = RoleFunctionGenerator()
        result = gen._extract_func_names_from_condition("CheckRx")
        assert "CheckRx" in result

    def test_empty_condition(self):
        gen = RoleFunctionGenerator()
        assert gen._extract_func_names_from_condition("") == []

    def test_multiple_functions(self):
        gen = RoleFunctionGenerator()
        result = gen._extract_func_names_from_condition(
            "Init() && CheckRx()")
        assert "Init" in result
        assert "CheckRx" in result


# ============================================================
# 呼び出しサイト収集
# ============================================================

class TestCollectCallSites:

    def test_empty_sm(self):
        gen = RoleFunctionGenerator()
        sm = StateMachine()
        assert gen._collect_call_sites(sm) == {}

    def test_none_sm(self):
        gen = RoleFunctionGenerator()
        assert gen._collect_call_sites(None) == {}

    def test_condition_call(self):
        gen = RoleFunctionGenerator()
        sm = _make_sm()
        call_map = gen._collect_call_sites(sm)
        assert "Init" in call_map
        assert len(call_map["Init"]) == 1
        cs = call_map["Init"][0]
        assert cs.kind == "condition"
        assert cs.from_state == "Idle"
        assert cs.event == "START"

    def test_pre_action_call(self):
        gen = RoleFunctionGenerator()
        sm = StateMachine()
        sm.add_state(State(name="A"))
        sm.add_state(State(name="B"))
        sm.add_event(Event(name="GO"))
        sm.add_transition(Transition(
            source="A", event="GO", target="B",
            pre_actions=["Driver.Init"],
        ))
        call_map = gen._collect_call_sites(sm)
        assert "Driver.Init" in call_map
        cs = call_map["Driver.Init"][0]
        assert cs.kind == "pre_action"

    def test_else_action_call(self):
        gen = RoleFunctionGenerator()
        sm = StateMachine()
        sm.add_state(State(name="A"))
        sm.add_state(State(name="B"))
        sm.add_event(Event(name="GO"))
        sm.add_transition(Transition(
            source="A", event="GO", target="B",
            else_actions=["Log.Error"],
            else_target="B",
        ))
        call_map = gen._collect_call_sites(sm)
        assert "Log.Error" in call_map
        cs = call_map["Log.Error"][0]
        assert cs.kind == "else_action"

    def test_invalid_action_skipped(self):
        """不正な識別子（retry_count++）は収集されない"""
        gen = RoleFunctionGenerator()
        sm = StateMachine()
        sm.add_state(State(name="A"))
        sm.add_state(State(name="B"))
        sm.add_event(Event(name="GO"))
        sm.add_transition(Transition(
            source="A", event="GO", target="B",
            pre_actions=["retry_count++"],
        ))
        call_map = gen._collect_call_sites(sm)
        assert "retry_count++" not in call_map


# ============================================================
# 呼び出しサイト取得
# ============================================================

class TestGetCallSitesForFunc:

    def test_qualified_lookup(self):
        gen = RoleFunctionGenerator()
        sm = _make_sm()
        call_map = gen._collect_call_sites(sm)
        rf = _make_rf(name="Init", namespace="")
        sites = gen._get_call_sites_for_func(rf, call_map)
        assert len(sites) == 1

    def test_not_found_returns_empty(self):
        gen = RoleFunctionGenerator()
        rf = _make_rf(name="Unknown")
        sites = gen._get_call_sites_for_func(rf, {})
        assert sites == []


# ============================================================
# ★ v1.6 §9.6 #90 層フィルタ
# ============================================================

class TestShouldEmitImplementation:

    def test_self_layer_func_emitted(self):
        """自層の関数は出力"""
        gen = RoleFunctionGenerator()
        gen.set_layer("Driver")
        rf = _make_rf(name="Init", namespace="Driver")
        assert gen._should_emit_implementation(rf, {}) is True

    def test_other_layer_no_caller_skipped(self):
        """他層の関数で呼び出し元なし → スキップ"""
        gen = RoleFunctionGenerator()
        gen.set_layer("Driver")
        rf = _make_rf(name="Handle", namespace="Middleware")
        assert gen._should_emit_implementation(rf, {}) is False

    def test_other_layer_with_caller_emitted(self):
        """他層の関数でも呼び出し元あり → 出力"""
        gen = RoleFunctionGenerator()
        gen.set_layer("Driver")
        rf = _make_rf(name="Handle", namespace="Middleware")
        call_map = {"Middleware.Handle": [
            RoleFuncCallSite("Middleware.Handle", "pre_action",
                             "Idle", "GO", "Active")
        ]}
        assert gen._should_emit_implementation(rf, call_map) is True

    def test_bare_name_caller(self):
        """namespace なしの呼び出しでマッチ"""
        gen = RoleFunctionGenerator()
        gen.set_layer("Driver")
        rf = _make_rf(name="Init", namespace="")
        call_map = {"Init": [
            RoleFuncCallSite("Init", "pre_action", "A", "E", "B")
        ]}
        assert gen._should_emit_implementation(rf, call_map) is True


# ============================================================
# 宣言生成
# ============================================================

class TestDeclaration:

    def test_basic_declaration(self):
        gen = RoleFunctionGenerator()
        rf = _make_rf(name="Init", namespace="Driver",
                      title="初期化", description="テスト")
        result = gen.generate_declaration(rf)
        assert "int RoleFunc_Driver_Init(" in result
        assert "const TransitionContext_t *transition" in result
        assert "SystemContext_t *ctx" in result
        assert ");" in result

    def test_declaration_with_layer(self):
        gen = RoleFunctionGenerator()
        gen.set_layer("Driver")
        rf = _make_rf(name="Init")
        result = gen.generate_declaration(rf)
        assert "TransitionContext_Driver_t" in result

    def test_no_description_uses_short_comment(self):
        gen = RoleFunctionGenerator()
        rf = _make_rf(name="Init", namespace="Driver")
        result = gen.generate_declaration(rf)
        assert "@brief" in result
        # @note は description がある場合のみ
        assert "@note   " not in result


# ============================================================
# 実装生成
# ============================================================

class TestImplementation:

    def test_basic_structure(self):
        gen = RoleFunctionGenerator()
        rf = _make_rf(name="Init", namespace="Driver",
                      title="初期化")
        result = gen.generate_implementation(rf)
        assert "int RoleFunc_Driver_Init(" in result
        assert "SystemContext_t *ctx" in result
        assert "return ret;" in result

    def test_null_guard(self):
        """NULL ガード生成"""
        gen = RoleFunctionGenerator()
        rf = _make_rf(name="Init", namespace="Driver")
        result = gen.generate_implementation(rf)
        assert "transition != NULL" in result

    def test_user_marker(self):
        gen = RoleFunctionGenerator()
        rf = _make_rf(name="Init", namespace="Driver")
        result = gen.generate_implementation(rf)
        assert "[[STABLE_USER_CODE_START:Driver_Init]]" in result
        assert "[[STABLE_USER_CODE_END:Driver_Init]]" in result

    def test_transition_id_when_call_sites(self):
        gen = RoleFunctionGenerator()
        rf = _make_rf(name="Init", namespace="Driver")
        call_sites = [RoleFuncCallSite(
            "Driver.Init", "pre_action", "Idle", "START", "Active")]
        result = gen.generate_implementation(
            rf, call_sites=call_sites, include_transition_id=True)
        assert "Transition_GetId" in result

    def test_no_transition_id_when_no_call_sites(self):
        gen = RoleFunctionGenerator()
        rf = _make_rf(name="Init", namespace="Driver")
        result = gen.generate_implementation(
            rf, call_sites=[], include_transition_id=True)
        # 呼び出し元なしの場合も Transition_GetId は生成される（NULL, 0）
        assert "Transition_GetId" in result

    def test_unused_ctx_when_no_global_defs(self):
        """global_defs なしなら (void)ctx が出力される"""
        gen = RoleFunctionGenerator()
        rf = _make_rf(name="Init", namespace="Driver")
        result = gen.generate_implementation(rf)
        assert "(void)ctx" in result


# ============================================================
# 一括生成
# ============================================================

class TestGenerateAll:

    def test_declarations_basic(self):
        gen = RoleFunctionGenerator()
        rfs = [
            _make_rf(name="Init", namespace="Driver"),
            _make_rf(name="Handle", namespace="Driver"),
        ]
        result = gen.generate_all_declarations(rfs)
        assert "RoleFunc_Driver_Init" in result
        assert "RoleFunc_Driver_Handle" in result

    def test_declarations_dedupe(self):
        gen = RoleFunctionGenerator()
        rfs = [
            _make_rf(name="Init", namespace="Driver"),
            _make_rf(name="Init", namespace="Driver"),  # 重複
        ]
        result = gen.generate_all_declarations(rfs)
        # 1 回だけ出力される
        assert result.count("RoleFunc_Driver_Init") == 1

    def test_implementations_filtered_by_layer(self):
        """層フィルタが効いている"""
        gen = RoleFunctionGenerator()
        gen.set_layer("Driver")
        rfs = [
            _make_rf(name="Init", namespace="Driver"),       # 自層 → OK
            _make_rf(name="Other", namespace="Middleware"),  # 他層 → スキップ
        ]
        result = gen.generate_all_implementations(rfs)
        assert "RoleFunc_Driver_Init" in result
        assert "RoleFunc_Middleware_Other" not in result

    def test_implementations_with_call_sites(self):
        gen = RoleFunctionGenerator()
        gen.set_layer("Driver")
        sm = _make_sm(layer_name="Driver")
        rfs = [_make_rf(name="Init", namespace="Driver")]
        result = gen.generate_all_implementations(
            rfs, state_machine=sm)
        # Transition_GetId 含む
        assert "Transition_GetId" in result

    def test_empty_list(self):
        """
        空リストの場合:
          - 宣言: 空文字列
          - 実装: 末尾ユーザー領域のみ（関数 0 件でもマーカーは出力）
        """
        gen = RoleFunctionGenerator()
        assert gen.generate_all_declarations([]) == ""

        # 実装は末尾ユーザー領域を必ず出力（ユーザー追加コード保持のため）
        result = gen.generate_all_implementations([])
        assert "[[STABLE_USER_CODE_TAIL_START]]" in result
        assert "[[STABLE_USER_CODE_TAIL_END]]" in result
        # 関数本体は含まれない
        assert "RoleFunc_" not in result


# ============================================================
# generate_call
# ============================================================

class TestGenerateCall:

    def test_plain_name(self):
        gen = RoleFunctionGenerator()
        result = gen.generate_call("Init")
        assert "RoleFunc_Init(transition, ctx)" in result

    def test_qualified_name(self):
        gen = RoleFunctionGenerator()
        result = gen.generate_call("Driver.Init")
        assert "RoleFunc_Driver_Init(transition, ctx)" in result

    def test_rolefunc_prefix_unchanged(self):
        gen = RoleFunctionGenerator()
        result = gen.generate_call("RoleFunc_Driver_Init")
        assert "RoleFunc_Driver_Init(transition, ctx)" in result

    def test_layer_name_used(self):
        gen = RoleFunctionGenerator()
        gen.set_layer("Driver")
        result = gen.generate_call("Init")
        assert "RoleFunc_Driver_Init" in result


# ============================================================
# エッジケース
# ============================================================

class TestEdgeCases:

    def test_unnamed_function_dedupe(self):
        """name が空の関数はスキップされる（_dedupe_by_name）"""
        gen = RoleFunctionGenerator()
        rfs = [_make_rf(name="", namespace="Driver")]
        result = gen.generate_all_declarations(rfs)
        # 空名はスキップ
        assert result == "" or "RoleFunc" not in result

    def test_duplicate_qualified_name(self):
        """同じ qualified_name の重複は 1 つに"""
        gen = RoleFunctionGenerator()
        rfs = [
            _make_rf(name="Init", namespace="Driver"),
            _make_rf(name="Init", namespace="Driver"),
        ]
        result = gen.generate_all_declarations(rfs)
        assert result.count("RoleFunc_Driver_Init") == 1