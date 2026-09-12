# tests/test_role_function_generator.py
"""
RoleFunctionGenerator の全機能テスト

実行方法:
    cd code
    python -m tests.test_role_function_generator
    または
    python tests/test_role_function_generator.py

実行するとテスト終了後に tests/_generated/ に生成コードが出力されます。
"""

import sys
import os
from typing import Optional          # ★ 追加

# ============================================================
# sys.path セットアップ
# ============================================================
_THIS_DIR    = os.path.dirname(os.path.abspath(__file__))
_CODE_DIR    = os.path.dirname(_THIS_DIR)
_CODEGEN_DIR = os.path.join(_CODE_DIR, 'codegen')

for _p in (_CODEGEN_DIR, _CODE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import re
import unittest
from pathlib import Path

# ============================================================
# モデルのインポート（statable が無い環境ではフォールバック）
# ============================================================
try:
    from statable.model import RoleFunction, Transition, State, Event
    from statable.state_machine import StateMachine
except ImportError:
    class RoleFunction:
        def __init__(self, name, return_type='void', description='', title=''):
            self.name = name
            self.return_type = return_type
            self.description = description
            self.title = title

    class Transition:
        def __init__(self, source, event, target,
                     condition='', pre_actions=None, else_actions=None,
                     has_else=False, else_target=''):
            self.source = source
            self.event = event
            self.target = target
            self.condition = condition
            self.pre_actions = pre_actions or []
            self.else_actions = else_actions or []
            self.has_else = has_else
            self.else_target = else_target

    class State:
        def __init__(self, name):
            self.name = name

    class Event:
        def __init__(self, name):
            self.name = name

    class StateMachine:
        def __init__(self):
            self.states = {}
            self.events = {}
            self._cells = {}

        def add_state(self, s):
            self.states[s.name] = s

        def add_event(self, e):
            self.events[e.name] = e

        def add_transition(self, t):
            key = (t.source, t.event)
            self._cells.setdefault(key, []).append(t)

        def get_transitions_for_cell(self, state, event):
            return self._cells.get((state, event), [])

from role_function_generator import (
    RoleFunctionGenerator,
    RoleFuncCallSite,
)


# ============================================================
# テスト用ヘルパー
# ============================================================
def make_func(name, description='', title=''):
    return RoleFunction(name=name, description=description, title=title)


class DummyVar:
    def __init__(self, name, type_, unit='', description='', array_size=0):
        self.name = name
        self.type = type_
        self.unit = unit
        self.description = description
        self.array_size = array_size


class DummyGlobalDefs:
    def __init__(self, variables=None):
        self.variables = variables or []


def make_state_machine():
    """
    テスト用ステートマシン

      Idle   -[START]-> Running  (condition: StartOk)
      Active -[STOP]->  Idle     (pre_actions: LogStop)
      Active -[ERROR]-> Error    (pre_actions: LogError,
                                  else_actions: Fallback, else_target: Idle)
    """
    sm = StateMachine()
    for n in ("Idle", "Active", "Running", "Error"):
        sm.add_state(State(n))
    for n in ("START", "STOP", "ERROR"):
        sm.add_event(Event(n))

    sm.add_transition(Transition(
        source="Idle", event="START", target="Running",
        condition="StartOk",
    ))
    sm.add_transition(Transition(
        source="Active", event="STOP", target="Idle",
        pre_actions=["LogStop"],
    ))
    sm.add_transition(Transition(
        source="Active", event="ERROR", target="Error",
        pre_actions=["LogError"],
        has_else=True, else_actions=["Fallback"], else_target="Idle",
    ))
    return sm


# ============================================================
# 1. 名前生成
# ============================================================
class TestNameGeneration(unittest.TestCase):
    def setUp(self):
        self.gen = RoleFunctionGenerator()

    def test_function_name_with_layer(self):
        self.gen.set_layer("Driver")
        self.assertEqual(
            self.gen._generate_function_name(make_func("CheckSensor")),
            "RoleFunc_Driver_CheckSensor",
        )

    def test_function_name_without_layer(self):
        self.assertEqual(
            self.gen._generate_function_name(make_func("CheckSensor")),
            "RoleFunc_CheckSensor",
        )

    def test_function_name_snake_case(self):
        self.gen.set_layer("Driver")
        self.assertEqual(
            self.gen._generate_function_name(make_func("check_sensor")),
            "RoleFunc_Driver_CheckSensor",
        )

    def test_marker_name_with_layer(self):
        self.gen.set_layer("Driver")
        self.assertEqual(
            self.gen._get_marker_name(make_func("CheckSensor")),
            "Driver_CheckSensor",
        )

    def test_marker_name_without_layer(self):
        self.assertEqual(
            self.gen._get_marker_name(make_func("CheckSensor")),
            "CheckSensor",
        )

    def test_short_name(self):
        self.gen.set_layer("Driver")
        self.assertEqual(
            self.gen._get_short_name(make_func("check_sensor")),
            "CheckSensor",
        )

    def test_context_type_with_layer(self):
        self.gen.set_layer("Driver")
        self.assertEqual(
            self.gen._context_type(), "TransitionContext_Driver_t",
        )

    def test_context_type_without_layer(self):
        self.assertEqual(self.gen._context_type(), "TransitionContext_t")

    def test_state_enum_with_layer(self):
        self.gen.set_layer("Driver")
        self.assertEqual(self.gen._state_enum("Idle"), "STATE_Driver_Idle")

    def test_event_enum_with_layer(self):
        self.gen.set_layer("Driver")
        self.assertEqual(self.gen._event_enum("START"), "EVENT_Driver_START")

    def test_entry_struct_type(self):
        self.gen.set_layer("Driver")
        self.assertEqual(
            self.gen._entry_struct_type(),
            "RoleFuncCallSiteEntry_Driver_t",
        )


# ============================================================
# 2. 重複除去
# ============================================================
class TestDedupe(unittest.TestCase):
    def setUp(self):
        self.gen = RoleFunctionGenerator()

    def test_removes_duplicates(self):
        funcs = [make_func("A"), make_func("B"), make_func("A"), make_func("C")]
        names = [f.name for f in self.gen._dedupe_by_name(funcs)]
        self.assertEqual(names, ["A", "B", "C"])

    def test_preserves_order(self):
        funcs = [make_func("C"), make_func("A"), make_func("B")]
        names = [f.name for f in self.gen._dedupe_by_name(funcs)]
        self.assertEqual(names, ["C", "A", "B"])

    def test_empty(self):
        self.assertEqual(self.gen._dedupe_by_name([]), [])

    def test_all_unique(self):
        funcs = [make_func("A"), make_func("B"), make_func("C")]
        self.assertEqual(len(self.gen._dedupe_by_name(funcs)), 3)

    def test_skips_no_name(self):
        funcs = [make_func("A"), make_func(""), make_func("B")]
        names = [f.name for f in self.gen._dedupe_by_name(funcs)]
        self.assertEqual(names, ["A", "B"])


# ============================================================
# 3. 宣言生成
# ============================================================
class TestDeclaration(unittest.TestCase):
    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Driver")

    def test_contains_signature(self):
        decl = self.gen.generate_declaration(
            make_func("CheckSensor", description="センサー確認")
        )
        self.assertIn("int RoleFunc_Driver_CheckSensor(", decl)
        self.assertIn("const TransitionContext_Driver_t *transition,", decl)
        self.assertIn("SystemContext_t *ctx", decl)
        self.assertIn(");", decl)

    def test_contains_comment(self):
        decl = self.gen.generate_declaration(
            make_func("CheckSensor", description="センサー確認")
        )
        self.assertIn("@brief", decl)
        self.assertIn("@param  transition", decl)
        self.assertIn("@param  ctx", decl)
        self.assertIn("@return", decl)
        self.assertIn("センサー確認", decl)

    def test_no_description(self):
        decl = self.gen.generate_declaration(make_func("CheckSensor"))
        self.assertNotIn("@note", decl)
        self.assertIn("int RoleFunc_Driver_CheckSensor(", decl)

    def test_without_layer(self):
        gen = RoleFunctionGenerator()
        decl = gen.generate_declaration(make_func("CheckSensor"))
        self.assertIn("int RoleFunc_CheckSensor(", decl)
        self.assertIn("const TransitionContext_t *transition,", decl)


# ============================================================
# 4. 実装生成（基本）
# ============================================================
class TestImplementation(unittest.TestCase):
    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Driver")

    def test_contains_signature(self):
        impl = self.gen.generate_implementation(make_func("CheckSensor"))
        self.assertIn("int RoleFunc_Driver_CheckSensor(", impl)
        self.assertIn("const TransitionContext_Driver_t *transition,", impl)
        self.assertIn("SystemContext_t *ctx", impl)

    def test_unused_ctx(self):
        impl = self.gen.generate_implementation(make_func("CheckSensor"))
        self.assertIn("(void)ctx;", impl)

    def test_markers_with_layer(self):
        impl = self.gen.generate_implementation(make_func("CheckSensor"))
        self.assertIn(
            "/* [[STABLE_USER_CODE_START:Driver_CheckSensor]] */", impl
        )
        self.assertIn(
            "/* [[STABLE_USER_CODE_END:Driver_CheckSensor]] */", impl
        )

    def test_markers_without_layer(self):
        gen = RoleFunctionGenerator()
        impl = gen.generate_implementation(make_func("CheckSensor"))
        self.assertIn("/* [[STABLE_USER_CODE_START:CheckSensor]] */", impl)
        self.assertIn("/* [[STABLE_USER_CODE_END:CheckSensor]] */", impl)

    def test_return_ret(self):
        impl = self.gen.generate_implementation(make_func("CheckSensor"))
        self.assertIn("return ret;", impl)
        self.assertNotIn("return 0;", impl)

    def test_marker_matches_merger_pattern(self):
        impl = self.gen.generate_implementation(make_func("CheckSensor"))
        m = re.search(r'RoleFunc_(\w+)\s*\(', impl)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "Driver_CheckSensor")
        self.assertIn(f"START:{m.group(1)}", impl)
        self.assertIn(f"END:{m.group(1)}", impl)


# ============================================================
# 5. 呼び出し生成
# ============================================================
class TestCall(unittest.TestCase):
    def test_with_layer(self):
        gen = RoleFunctionGenerator()
        gen.set_layer("Driver")
        self.assertEqual(
            gen.generate_call("CheckSensor"),
            "RoleFunc_Driver_CheckSensor(transition, ctx)",
        )

    def test_without_layer(self):
        gen = RoleFunctionGenerator()
        self.assertEqual(
            gen.generate_call("CheckSensor"),
            "RoleFunc_CheckSensor(transition, ctx)",
        )

    def test_full_name(self):
        gen = RoleFunctionGenerator()
        gen.set_layer("Driver")
        self.assertEqual(
            gen.generate_call("RoleFunc_Driver_CheckSensor"),
            "RoleFunc_Driver_CheckSensor(transition, ctx)",
        )

    def test_snake_case(self):
        gen = RoleFunctionGenerator()
        gen.set_layer("Driver")
        self.assertEqual(
            gen.generate_call("check_sensor"),
            "RoleFunc_Driver_CheckSensor(transition, ctx)",
        )


# ============================================================
# 6. 一括宣言生成
# ============================================================
class TestAllDeclarations(unittest.TestCase):
    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Driver")

    def test_dedup(self):
        funcs = [make_func("A"), make_func("B"), make_func("A")]
        result = self.gen.generate_all_declarations(funcs)
        self.assertEqual(result.count("int RoleFunc_Driver_A("), 1)
        self.assertEqual(result.count("int RoleFunc_Driver_B("), 1)

    def test_empty(self):
        self.assertEqual(self.gen.generate_all_declarations([]), "")

    def test_multiple(self):
        funcs = [make_func("A"), make_func("B"), make_func("C")]
        result = self.gen.generate_all_declarations(funcs)
        for name in ["A", "B", "C"]:
            self.assertIn(f"int RoleFunc_Driver_{name}(", result)


# ============================================================
# 7. 一括実装生成（基本）
# ============================================================
class TestAllImplementations(unittest.TestCase):
    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Driver")

    def test_dedup(self):
        funcs = [make_func("A"), make_func("B"), make_func("A")]
        result = self.gen.generate_all_implementations(funcs)
        self.assertEqual(
            result.count("[[STABLE_USER_CODE_START:Driver_A]]"), 1
        )
        self.assertEqual(
            result.count("[[STABLE_USER_CODE_START:Driver_B]]"), 1
        )

    def test_empty(self):
        result = self.gen.generate_all_implementations([])
        # 空でも末尾のユーザー追加領域は出力される
        self.assertIn("STABLE_USER_CODE_TAIL_START", result)

    def test_markers(self):
        funcs = [make_func("A"), make_func("B")]
        result = self.gen.generate_all_implementations(funcs)
        self.assertIn("[[STABLE_USER_CODE_START:Driver_A]]", result)
        self.assertIn("[[STABLE_USER_CODE_END:Driver_A]]", result)

    def test_uses_ret(self):
        funcs = [make_func("A"), make_func("B")]
        result = self.gen.generate_all_implementations(funcs)
        self.assertEqual(result.count("int ret = 0;"), 2)
        self.assertEqual(result.count("return ret;"), 2)
        self.assertNotIn("return 0;", result)


# ============================================================
# 8. 往復テスト
# ============================================================
class TestRoundTrip(unittest.TestCase):
    def test_marker_round_trip(self):
        gen = RoleFunctionGenerator()
        gen.set_layer("Driver")
        funcs = [make_func("CheckSensor"), make_func("InitSensor")]
        impl = gen.generate_all_implementations(funcs)

        from code_merger import CodeMerger
        merger = CodeMerger()
        extracted = merger.extract_all_func_user_codes(impl)
        self.assertIn("Driver_CheckSensor", extracted)
        self.assertIn("Driver_InitSensor", extracted)


# ============================================================
# 9. ローカル変数展開
# ============================================================
class TestLocalVariableExpansion(unittest.TestCase):
    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Driver")

    def test_transition_members_with_layer(self):
        impl = self.gen.generate_implementation(make_func("CheckSensor"))
        self.assertIn(
            "const STATE_Driver_t from_state = transition->from_state;", impl
        )
        self.assertIn(
            "const EVENT_Driver_t event = transition->event;", impl
        )

    def test_transition_members_without_layer(self):
        gen = RoleFunctionGenerator()
        impl = gen.generate_implementation(make_func("CheckSensor"))
        self.assertIn(
            "const STATE_t from_state = transition->from_state;", impl
        )
        self.assertIn(
            "const EVENT_t event = transition->event;", impl
        )

    def test_no_void_transition(self):
        impl = self.gen.generate_implementation(make_func("CheckSensor"))
        self.assertNotIn("(void)transition;", impl)

    def test_void_ctx_without_global_defs(self):
        impl = self.gen.generate_implementation(make_func("CheckSensor"))
        self.assertIn("(void)ctx;", impl)
        self.assertNotIn("&ctx->data.", impl)

    def test_empty_variables(self):
        gd = DummyGlobalDefs(variables=[])
        impl = self.gen.generate_implementation(make_func("CheckSensor"), gd)
        self.assertIn("(void)ctx;", impl)
        self.assertNotIn("&ctx->data.", impl)

    def test_scalar_pointer(self):
        gd = DummyGlobalDefs(variables=[
            DummyVar('battery_voltage', 'uint16', 'mV', 'バッテリー電圧'),
        ])
        impl = self.gen.generate_implementation(make_func("CheckSensor"), gd)
        self.assertIn(
            "uint16_t *const battery_voltage = &ctx->data.battery_voltage;",
            impl,
        )
        self.assertNotIn("(void)ctx;", impl)

    def test_multiple_pointers(self):
        gd = DummyGlobalDefs(variables=[
            DummyVar('battery_voltage', 'uint16', 'mV', 'バッテリー電圧'),
            DummyVar('system_tick', 'uint32', 'ms', 'システムタイマ'),
            DummyVar('temperature', 'int16', '', '温度'),
        ])
        impl = self.gen.generate_implementation(make_func("CheckSensor"), gd)
        self.assertIn(
            "uint16_t *const battery_voltage = &ctx->data.battery_voltage;",
            impl,
        )
        self.assertIn(
            "uint32_t *const system_tick = &ctx->data.system_tick;",
            impl,
        )
        self.assertIn(
            "int16_t *const temperature = &ctx->data.temperature;",
            impl,
        )

    def test_array_pointer(self):
        gd = DummyGlobalDefs(variables=[
            DummyVar('data_buffer', 'uint8', '', 'データバッファ', array_size=64),
        ])
        impl = self.gen.generate_implementation(make_func("CheckSensor"), gd)
        self.assertIn(
            "uint8_t *const data_buffer = ctx->data.data_buffer;",
            impl,
        )
        self.assertNotIn("&ctx->data.data_buffer", impl)

    def test_comment_with_unit(self):
        gd = DummyGlobalDefs(variables=[
            DummyVar('battery_voltage', 'uint16', 'mV', 'バッテリー電圧'),
        ])
        impl = self.gen.generate_implementation(make_func("CheckSensor"), gd)
        self.assertIn("/* バッテリー電圧 [mV] */", impl)

    def test_comment_without_unit(self):
        gd = DummyGlobalDefs(variables=[
            DummyVar('flag', 'bool', '', 'フラグ'),
        ])
        impl = self.gen.generate_implementation(make_func("CheckSensor"), gd)
        self.assertIn("/* フラグ */", impl)


# ============================================================
# 10. 戻り値用ローカル変数
# ============================================================
class TestLocalReturnVariable(unittest.TestCase):
    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Driver")

    def test_ret_declared(self):
        impl = self.gen.generate_implementation(make_func("CheckSensor"))
        self.assertIn("int ret = 0;", impl)

    def test_return_uses_ret(self):
        impl = self.gen.generate_implementation(make_func("CheckSensor"))
        self.assertIn("return ret;", impl)
        self.assertNotIn("return 0;", impl)

    def test_ret_section_comment(self):
        impl = self.gen.generate_implementation(make_func("CheckSensor"))
        self.assertIn("/* ===== 戻り値 ===== */", impl)

    def test_ret_without_layer(self):
        gen = RoleFunctionGenerator()
        impl = gen.generate_implementation(make_func("CheckSensor"))
        self.assertIn("int ret = 0;", impl)
        self.assertIn("return ret;", impl)

    def test_ret_after_data_pointers(self):
        gd = DummyGlobalDefs(variables=[
            DummyVar('battery_voltage', 'uint16', 'mV', 'バッテリー電圧'),
        ])
        impl = self.gen.generate_implementation(make_func("CheckSensor"), gd)
        pos_ret = impl.index("int ret = 0;")
        pos_data = impl.index("&ctx->data.battery_voltage")
        self.assertGreater(pos_ret, pos_data)


# ============================================================
# 11. 呼び出しサイト収集
# ============================================================
class TestCallSiteCollection(unittest.TestCase):
    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Driver")

    def test_extract_bare(self):
        self.assertIn("StartOk",
                      self.gen._extract_func_names_from_condition("StartOk"))

    def test_extract_call(self):
        self.assertIn("StartOk",
                      self.gen._extract_func_names_from_condition("StartOk()"))

    def test_extract_rolefunc(self):
        names = self.gen._extract_func_names_from_condition(
            "RoleFunc_Driver_StartOk(transition, ctx)"
        )
        self.assertIn("StartOk", names)

    def test_extract_expression(self):
        names = self.gen._extract_func_names_from_condition("CheckA() && CheckB()")
        self.assertIn("CheckA", names)
        self.assertIn("CheckB", names)

    def test_extract_empty(self):
        self.assertEqual(self.gen._extract_func_names_from_condition(""), [])

    def test_collect_pre_actions(self):
        sm = make_state_machine()
        cm = self.gen._collect_call_sites(sm)
        self.assertIn("LogStop", cm)
        self.assertEqual(cm["LogStop"][0].kind, "pre_action")

    def test_collect_else_actions(self):
        sm = make_state_machine()
        cm = self.gen._collect_call_sites(sm)
        self.assertIn("Fallback", cm)
        self.assertEqual(cm["Fallback"][0].kind, "else_action")

    def test_collect_condition(self):
        sm = make_state_machine()
        cm = self.gen._collect_call_sites(sm)
        self.assertIn("StartOk", cm)
        self.assertEqual(cm["StartOk"][0].kind, "condition")

    def test_collect_none(self):
        self.assertEqual(self.gen._collect_call_sites(None), {})


# ============================================================
# 12. TRANSITION_ID_NONE / 共通構造体
# ============================================================
class TestNoneAndStruct(unittest.TestCase):
    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Driver")

    def test_none_define(self):
        code = self.gen.generate_none_define()
        self.assertIn("#define TRANSITION_ID_NONE", code)
        self.assertIn("((uint16_t)0xFFFF)", code)

    def test_entry_struct_with_layer(self):
        code = self.gen.generate_entry_struct()
        self.assertIn("typedef struct", code)
        self.assertIn("STATE_Driver_t from_state;", code)
        self.assertIn("EVENT_Driver_t event;", code)
        self.assertIn("} RoleFuncCallSiteEntry_Driver_t;", code)

    def test_entry_struct_without_layer(self):
        gen = RoleFunctionGenerator()
        code = gen.generate_entry_struct()
        self.assertIn("STATE_t from_state;", code)
        self.assertIn("EVENT_t event;", code)
        self.assertIn("} RoleFuncCallSiteEntry_t;", code)


# ============================================================
# 13. call_sites テーブル
# ============================================================
class TestCallSitesTable(unittest.TestCase):
    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Driver")

    def test_generated(self):
        func = make_func("CheckSensor")
        cs = [
            RoleFuncCallSite("CheckSensor", "condition", "Idle", "START", "Running"),
            RoleFuncCallSite("CheckSensor", "condition", "Active", "ERROR", "Error"),
        ]
        code = self.gen.generate_call_sites_table(func, cs)
        self.assertIn("/* --- CheckSensor の呼び出し元テーブル --- */", code)
        self.assertIn(
            "static const RoleFuncCallSiteEntry_Driver_t call_sites_CheckSensor[]",
            code,
        )
        # 整列後の形式（カンマ + 可変空白 + event）
        self.assertIn("STATE_Driver_Idle", code)
        self.assertIn("EVENT_Driver_START", code)
        self.assertIn("STATE_Driver_Active", code)
        self.assertIn("EVENT_Driver_ERROR", code)
        self.assertIn("#define CALL_SITES_CheckSensor_COUNT", code)

    def test_dedup_same_state_event(self):
        func = make_func("Multi")
        cs = [
            RoleFuncCallSite("Multi", "condition",  "Idle", "START", "Running"),
            RoleFuncCallSite("Multi", "pre_action", "Idle", "START", "Running"),
        ]
        code = self.gen.generate_call_sites_table(func, cs)
        self.assertEqual(code.count("STATE_Driver_Idle"), 1)

    def test_empty_returns_empty(self):
        code = self.gen.generate_call_sites_table(make_func("Foo"), [])
        self.assertEqual(code, "")

    def test_multiple_entries(self):
        func = make_func("Foo")
        cs = [
            RoleFuncCallSite("Foo", "condition", "Idle",   "START", "Running"),
            RoleFuncCallSite("Foo", "condition", "Active", "STOP",  "Idle"),
            RoleFuncCallSite("Foo", "condition", "Active", "ERROR", "Error"),
        ]
        code = self.gen.generate_call_sites_table(func, cs)
        self.assertIn("STATE_Driver_Idle", code)
        self.assertIn("STATE_Driver_Active", code)
        self.assertIn("EVENT_Driver_START", code)
        self.assertIn("EVENT_Driver_STOP", code)
        self.assertIn("EVENT_Driver_ERROR", code)


# ============================================================
# 14. Transition_GetId プロトタイプ / 本体
# ============================================================
class TestTransitionIdFunction(unittest.TestCase):
    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Driver")

    def test_prototype(self):
        code = self.gen.generate_transition_id_prototype()
        self.assertIn("static uint16_t Transition_GetId(", code)
        self.assertIn("const TransitionContext_Driver_t *transition,", code)
        self.assertIn("const RoleFuncCallSiteEntry_Driver_t *table,", code)
        self.assertIn("uint16_t table_size);", code)

    def test_definition(self):
        code = self.gen.generate_transition_id_function()
        self.assertIn("static uint16_t Transition_GetId(", code)
        self.assertIn("if (table == NULL)", code)
        self.assertIn("return TRANSITION_ID_NONE;", code)
        self.assertIn("for (i = 0; i < table_size; i++)", code)
        self.assertIn("table[i].from_state == transition->from_state", code)
        self.assertIn("table[i].event      == transition->event", code)
        self.assertIn("return i;", code)

    def test_definition_without_layer(self):
        gen = RoleFunctionGenerator()
        code = gen.generate_transition_id_function()
        self.assertIn("const TransitionContext_t *transition,", code)
        self.assertIn("const RoleFuncCallSiteEntry_t *table,", code)


# ============================================================
# 15. 実装内の transition_id
# ============================================================
class TestTransitionIdInImplementation(unittest.TestCase):
    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Driver")

    def test_with_call_sites(self):
        func = make_func("CheckSensor")
        cs = [RoleFuncCallSite("CheckSensor", "condition",
                               "Idle", "START", "Running")]
        impl = self.gen.generate_implementation(func, call_sites=cs)
        self.assertIn("const uint16_t transition_id = Transition_GetId(", impl)
        self.assertIn("call_sites_CheckSensor,", impl)
        self.assertIn("(uint16_t)CALL_SITES_CheckSensor_COUNT", impl)

    def test_without_call_sites(self):
        impl = self.gen.generate_implementation(make_func("Foo"), call_sites=[])
        # 複数行に分かれるため、部分一致で確認
        self.assertIn("Transition_GetId(", impl)
        self.assertIn("transition, NULL, 0", impl)

    def test_disabled(self):
        impl = self.gen.generate_implementation(
            make_func("Foo"), include_transition_id=False,
        )
        self.assertNotIn("transition_id", impl)
        self.assertNotIn("Transition_GetId", impl)

    def test_order_after_members(self):
        func = make_func("Foo")
        cs = [RoleFuncCallSite("Foo", "condition", "Idle", "START", "Running")]
        impl = self.gen.generate_implementation(func, call_sites=cs)
        pos_m = impl.index("const EVENT_Driver_t event")
        pos_id = impl.index("transition_id =")
        self.assertGreater(pos_id, pos_m)

    def test_order_before_data_pointers(self):
        gd = DummyGlobalDefs(variables=[
            DummyVar('battery_voltage', 'uint16', 'mV', 'バッテリー電圧'),
        ])
        func = make_func("Foo")
        cs = [RoleFuncCallSite("Foo", "condition", "Idle", "START", "Running")]
        impl = self.gen.generate_implementation(func, global_defs=gd, call_sites=cs)
        pos_id = impl.index("transition_id =")
        pos_data = impl.index("&ctx->data.battery_voltage")
        self.assertLess(pos_id, pos_data)


# ============================================================
# 16. ファイル末尾ユーザー追加領域
# ============================================================
class TestTailUserSection(unittest.TestCase):
    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Driver")

    def test_generated(self):
        code = self.gen.generate_tail_user_section()
        # 空白数を問わない部分一致
        self.assertIn("ユーザー追加領域", code)
        self.assertIn("/* [[STABLE_USER_CODE_TAIL_START]] */", code)
        self.assertIn("/* [[STABLE_USER_CODE_TAIL_END]] */", code)

    def test_at_file_end_with_state_machine(self):
        sm = make_state_machine()
        funcs = [make_func("StartOk")]
        result = self.gen.generate_all_implementations(funcs, state_machine=sm)
        pos_def  = result.rindex("static uint16_t Transition_GetId(")
        pos_tail = result.index("STABLE_USER_CODE_TAIL_START")
        self.assertGreater(pos_tail, pos_def)

    def test_present_without_state_machine(self):
        funcs = [make_func("Foo")]
        result = self.gen.generate_all_implementations(funcs)
        self.assertIn("STABLE_USER_CODE_TAIL_START", result)
        self.assertIn("STABLE_USER_CODE_TAIL_END", result)


# ============================================================
# 17. 全体構成（順序確認）
# ============================================================
class TestAllImplementationsOrder(unittest.TestCase):
    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Driver")

    def test_order_with_state_machine(self):
        sm = make_state_machine()
        funcs = [make_func("StartOk"), make_func("LogStop")]
        result = self.gen.generate_all_implementations(funcs, state_machine=sm)

        pos_define = result.index("#define TRANSITION_ID_NONE")
        pos_struct = result.index("} RoleFuncCallSiteEntry_Driver_t;")
        pos_proto  = result.index("static uint16_t Transition_GetId(")
        pos_table  = result.index("call_sites_StartOk[]")
        pos_func   = result.index("int RoleFunc_Driver_StartOk(")
        pos_def    = result.rindex("static uint16_t Transition_GetId(")
        pos_tail   = result.index("STABLE_USER_CODE_TAIL_START")

        self.assertLess(pos_define, pos_struct)
        self.assertLess(pos_struct, pos_proto)
        self.assertLess(pos_proto, pos_table)
        self.assertLess(pos_table, pos_func)
        self.assertLess(pos_func, pos_def)
        self.assertLess(pos_def, pos_tail)

    def test_no_state_machine(self):
        funcs = [make_func("Foo")]
        result = self.gen.generate_all_implementations(funcs)
        self.assertNotIn("Transition_GetId", result)
        self.assertNotIn("transition_id", result)
        self.assertNotIn("TRANSITION_ID_NONE", result)

    def test_table_per_func(self):
        sm = make_state_machine()
        funcs = [make_func("StartOk"), make_func("LogStop")]
        result = self.gen.generate_all_implementations(funcs, state_machine=sm)
        self.assertIn("call_sites_StartOk[]", result)
        self.assertIn("call_sites_LogStop[]", result)
        self.assertIn("CALL_SITES_StartOk_COUNT", result)
        self.assertIn("CALL_SITES_LogStop_COUNT", result)

    def test_id_in_each_func(self):
        sm = make_state_machine()
        funcs = [make_func("A"), make_func("B"), make_func("C")]
        result = self.gen.generate_all_implementations(funcs, state_machine=sm)
        self.assertEqual(result.count("transition_id = Transition_GetId("), 3)

    def test_call_sites_comment_in_func(self):
        sm = make_state_machine()
        funcs = [make_func("StartOk")]
        result = self.gen.generate_all_implementations(funcs, state_machine=sm)
        self.assertIn("@note   呼び出し元:", result)
        self.assertIn("STATE_Driver_Idle", result)
        self.assertIn("EVENT_Driver_START", result)


# ============================================================
# 18. 完全パイプライン（生成 → マージ）
# ============================================================
class TestFullPipeline(unittest.TestCase):
    def test_generate_and_merge_round_trip(self):
        """生成 → マージ後もユーザーコード（関数単位）が保持される"""
        from code_merger import CodeMerger
        merger = CodeMerger()

        gen = RoleFunctionGenerator()
        gen.set_layer("Driver")

        funcs = [make_func("CheckSensor"), make_func("InitSensor")]
        generated = gen.generate_all_implementations(funcs)

        # ユーザーが CheckSensor のマーカー内にコードを書いた状態を擬似
        user_edited = generated.replace(
            "    /* ユーザー実装コードをここに記述 */\n"
            "    /* [[STABLE_USER_CODE_END:Driver_CheckSensor]] */",
            "    ret = 1;\n"
            "    /* [[STABLE_USER_CODE_END:Driver_CheckSensor]] */",
        )

        regenerated = gen.generate_all_implementations(funcs)
        merged = merger.merge_file(regenerated, user_edited)

        self.assertIn("ret = 1;", merged)

    def test_tail_user_code_preserved(self):
        """末尾ユーザー領域が再生成後も保持される"""
        from code_merger import CodeMerger
        merger = CodeMerger()

        gen = RoleFunctionGenerator()
        gen.set_layer("Driver")
        funcs = [make_func("Foo")]

        generated = gen.generate_all_implementations(funcs)
        user_edited = generated.replace(
            "/* ユーザー追加コードをここに記述（ヘルパー関数など） */",
            "static int my_helper(void) { return 42; }",
        )
        regenerated = gen.generate_all_implementations(funcs)
        merged = merger.merge_file(regenerated, user_edited)

        self.assertIn("static int my_helper(void)", merged)
        self.assertNotIn("/* ユーザー追加コードをここに記述（ヘルパー関数など） */",
                         merged)


# ============================================================
# 19. 統合: 全機能を含む出力の内容確認
# ============================================================
class TestIntegratedOutput(unittest.TestCase):
    def test_full_output_contains_all_elements(self):
        """全機能を有効にしたときの出力に、必要な要素が全て含まれること"""
        gen = RoleFunctionGenerator()
        gen.set_layer("Driver")

        sm = make_state_machine()
        gd = DummyGlobalDefs(variables=[
            DummyVar('battery_voltage', 'uint16', 'mV', 'バッテリー電圧'),
            DummyVar('system_tick', 'uint32', 'ms', 'システムタイマ'),
            DummyVar('data_buffer', 'uint8', '', 'データバッファ', array_size=64),
        ])
        funcs = [
            make_func("StartOk",   description="開始条件チェック"),
            make_func("LogStop",   description="停止ログ"),
            make_func("LogError",  description="エラーログ"),
            make_func("Fallback",  description="フォールバック"),
        ]

        out = gen.generate_all_implementations(
            funcs, state_machine=sm, global_defs=gd,
        )

        # 1. TRANSITION_ID_NONE 定数
        self.assertIn("#define TRANSITION_ID_NONE", out)
        # 2. 共通構造体
        self.assertIn("RoleFuncCallSiteEntry_Driver_t", out)
        # 3. プロトタイプ
        self.assertIn("static uint16_t Transition_GetId(", out)
        # 4. 各関数の call_sites テーブル
        self.assertIn("call_sites_StartOk[]", out)
        self.assertIn("call_sites_LogStop[]", out)
        self.assertIn("call_sites_LogError[]", out)
        self.assertIn("call_sites_Fallback[]", out)
        # 5. 各関数の transition メンバー展開
        self.assertIn(
            "const STATE_Driver_t from_state = transition->from_state;", out
        )
        self.assertIn("const EVENT_Driver_t event = transition->event;", out)
        # 6. transition_id
        self.assertEqual(
            out.count("const uint16_t transition_id = Transition_GetId("), 4,
        )
        # 7. ctx->data ポインタ
        self.assertIn(
            "uint16_t *const battery_voltage = &ctx->data.battery_voltage;",
            out,
        )
        self.assertIn(
            "uint32_t *const system_tick = &ctx->data.system_tick;", out,
        )
        self.assertIn(
            "uint8_t *const data_buffer = ctx->data.data_buffer;", out,
        )
        # 8. ret
        self.assertEqual(out.count("int ret = 0;"), 4)
        self.assertEqual(out.count("return ret;"), 4)
        # 9. ユーザーコードマーカー
        self.assertIn("[[STABLE_USER_CODE_START:Driver_StartOk]]", out)
        self.assertIn("[[STABLE_USER_CODE_END:Driver_StartOk]]", out)
        # 10. Transition_GetId 本体（末尾）
        self.assertIn("if (table == NULL)", out)
        # 11. 末尾ユーザー領域
        self.assertIn("STABLE_USER_CODE_TAIL_START", out)
        self.assertIn("STABLE_USER_CODE_TAIL_END", out)
        # 12. 呼び出し元コメント
        self.assertIn("@note   呼び出し元:", out)


# ============================================================
# 生成コードのダンプ（目視確認用）
# ============================================================
def dump_generated_code(output_dir: Optional[str] = None) -> str:
    """
    生成コードをファイルに出力して目視確認できるようにする

    Output:
        <tests>/_generated/role_functions.h
        <tests>/_generated/role_functions.c
        <tests>/_generated/role_functions_no_sm.c
    """
    if output_dir is None:
        output_dir = os.path.join(_THIS_DIR, '_generated')
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    gen = RoleFunctionGenerator()
    gen.set_layer("Driver")

    sm = make_state_machine()
    gd = DummyGlobalDefs(variables=[
        DummyVar('battery_voltage', 'uint16', 'mV', 'バッテリー電圧'),
        DummyVar('system_tick',    'uint32', 'ms', 'システムタイマ'),
        DummyVar('temperature',    'int16',  '0.1℃', '温度センサ値'),
        DummyVar('data_buffer',    'uint8',  '',     'データバッファ',
                 array_size=64),
    ])
    funcs = [
        make_func("StartOk",   description="開始条件チェック"),
        make_func("LogStop",   description="停止ログ"),
        make_func("LogError",  description="エラーログ"),
        make_func("Fallback",  description="フォールバック処理"),
    ]

    # --- 宣言ヘッダ ---
    decl = gen.generate_all_declarations(funcs)
    h_path = os.path.join(output_dir, 'role_functions.h')
    with open(h_path, 'w', encoding='utf-8') as f:
        f.write(decl)

    # --- 実装ソース（全機能有効） ---
    impl = gen.generate_all_implementations(
        funcs, state_machine=sm, global_defs=gd,
    )
    c_path = os.path.join(output_dir, 'role_functions.c')
    with open(c_path, 'w', encoding='utf-8') as f:
        f.write(impl)

    # --- 実装ソース（state_machine 未指定） ---
    impl_no_sm = gen.generate_all_implementations(funcs)
    c_no_sm_path = os.path.join(output_dir, 'role_functions_no_sm.c')
    with open(c_no_sm_path, 'w', encoding='utf-8') as f:
        f.write(impl_no_sm)

    # --- コンソールにもプレビュー出力 ---
    print("\n" + "=" * 70)
    print(f"  生成コードを出力しました: {output_dir}")
    print("=" * 70)
    print(f"  - role_functions.h        ({len(decl)} bytes)")
    print(f"  - role_functions.c        ({len(impl)} bytes)")
    print(f"  - role_functions_no_sm.c  ({len(impl_no_sm)} bytes)")

    print("\n" + "-" * 70)
    print("  role_functions.c の先頭 60 行プレビュー")
    print("-" * 70)
    for line in impl.split('\n')[:60]:
        print(f"  {line}")

    return output_dir


# ============================================================
# テスト実行
# ============================================================
def run_tests(dump: bool = True):
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestNameGeneration,
        TestDedupe,
        TestDeclaration,
        TestImplementation,
        TestCall,
        TestAllDeclarations,
        TestAllImplementations,
        TestRoundTrip,
        TestLocalVariableExpansion,
        TestLocalReturnVariable,
        TestCallSiteCollection,
        TestNoneAndStruct,
        TestCallSitesTable,
        TestTransitionIdFunction,
        TestTransitionIdInImplementation,
        TestTailUserSection,
        TestAllImplementationsOrder,
        TestFullPipeline,
        TestIntegratedOutput,
    ]
    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    ok = runner.run(suite).wasSuccessful()

    if dump:
        try:
            dump_generated_code()
        except Exception as e:
            print(f"\n[ダンプ失敗] {e}")

    return ok


if __name__ == '__main__':
    sys.exit(0 if run_tests() else 1)