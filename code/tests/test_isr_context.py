# tests/test_isr_context.py
"""
ISR コンテキスト対応テスト（H3 Stage 3）

テスト対象: codegen/interrupt_generator.py
  1. ISR 関数名 / マーカー名生成
  2. ctx 自動挿入
  3. アクション パース（Namespace.Name / 関数呼び出し / そのまま）
  4. used_role_functions / used_variables 抽出
  5. 完全な ISR 生成
  6. マージ往復（ユーザーコード保持）
"""

import sys
import os
import re

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_DIR = os.path.dirname(_THIS_DIR)
_CODEGEN_DIR = os.path.join(_CODE_DIR, 'codegen')

for _p in (_CODEGEN_DIR, _CODE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import unittest

from statable.global_defs import (
    InterruptHandlerDef, InterruptAction, GlobalDefinitions,
)
from interrupt_generator import InterruptGenerator
from code_merger import CodeMerger


# ============================================================
# ヘルパー
# ============================================================
def make_handler(name, actions=None, description=''):
    return InterruptHandlerDef(
        name=name,
        description=description,
        actions=[
            InterruptAction(condition=c, action=a)
            for c, a in (actions or [])
        ],
    )


# ============================================================
# 1. ISR 関数名 / マーカー名
# ============================================================
class TestIsrNames(unittest.TestCase):
    def setUp(self):
        self.gen = InterruptGenerator()

    def test_simple_name(self):
        h = make_handler("TIMER0")
        self.assertEqual(self.gen._get_isr_function_name(h), "ISR_TIMER0")
        self.assertEqual(self.gen._get_marker_name(h), "TIMER0")

    def test_snake_case_name(self):
        h = make_handler("UART_RX")
        self.assertEqual(self.gen._get_isr_function_name(h), "ISR_UARTRX")
        self.assertEqual(self.gen._get_marker_name(h), "UARTRX")

    def test_lowercase_name(self):
        h = make_handler("timer0")
        self.assertEqual(self.gen._get_isr_function_name(h), "ISR_Timer0")
        self.assertEqual(self.gen._get_marker_name(h), "Timer0")

    def test_empty_name_fallback(self):
        h = make_handler("")
        self.assertEqual(self.gen._get_isr_function_name(h), "ISR_Unnamed")
        self.assertEqual(self.gen._get_marker_name(h), "Unnamed")


# ============================================================
# 2. ctx 自動挿入
# ============================================================
class TestContextInsert(unittest.TestCase):
    def setUp(self):
        self.gen = InterruptGenerator()

    def test_ctx_decl_present(self):
        h = make_handler("TIMER0")
        code = self.gen.generate_isr(h)
        self.assertIn("SystemContext_t *ctx = &g_ctx;", code)

    def test_ctx_void_suppress(self):
        h = make_handler("TIMER0")
        code = self.gen.generate_isr(h)
        self.assertIn("(void)ctx;", code)

    def test_ctx_section_comment(self):
        h = make_handler("TIMER0")
        code = self.gen.generate_isr(h)
        self.assertIn("コンテキスト参照", code)


# ============================================================
# 3. アクション パース
# ============================================================
class TestActionParse(unittest.TestCase):
    def setUp(self):
        self.gen = InterruptGenerator()
        self.gen.set_layer("Driver")

    def test_namespace_name(self):
        code, used = self.gen._parse_action("Application.HandleTick")
        self.assertEqual(code, "RoleFunc_Application_HandleTick(NULL, ctx)")
        self.assertEqual(used, ["Application.HandleTick"])

    def test_namespace_name_with_empty_parens(self):
        code, used = self.gen._parse_action("Driver.Init()")
        self.assertEqual(code, "RoleFunc_Driver_Init(NULL, ctx)")
        self.assertEqual(used, ["Driver.Init"])

    def test_namespace_name_with_args(self):
        code, used = self.gen._parse_action("Driver.Init(arg1, arg2)")
        self.assertEqual(code, "RoleFunc_Driver_Init(NULL, ctx)")
        self.assertEqual(used, ["Driver.Init"])

    def test_bare_call_with_layer(self):
        code, used = self.gen._parse_action("Sensor_Init(arg1, arg2)")
        self.assertEqual(code, "RoleFunc_Driver_SensorInit(NULL, ctx)")
        self.assertEqual(used, ["Driver.SensorInit"])

    def test_bare_call_without_layer(self):
        gen = InterruptGenerator()
        code, used = gen._parse_action("Sensor_Init(arg1, arg2)")
        self.assertEqual(code, "RoleFunc_SensorInit(NULL, ctx)")
        self.assertEqual(used, ["SensorInit"])

    def test_verbatim_counter_increment(self):
        code, used = self.gen._parse_action("counter++")
        self.assertEqual(code, "counter++")
        self.assertEqual(used, [])

    def test_verbatim_ctx_data(self):
        code, used = self.gen._parse_action("ctx->data.counter++")
        self.assertEqual(code, "ctx->data.counter++")
        self.assertEqual(used, [])

    def test_verbatim_flag_assign(self):
        code, used = self.gen._parse_action("EVT_START_REQ = 1")
        self.assertEqual(code, "EVT_START_REQ = 1")
        self.assertEqual(used, [])

    def test_rolefunc_passthrough(self):
        code, used = self.gen._parse_action("RoleFunc_Driver_Init(NULL, ctx)")
        self.assertEqual(code, "RoleFunc_Driver_Init(NULL, ctx)")
        self.assertEqual(used, [])

    def test_c_keyword_verbatim(self):
        code, used = self.gen._parse_action("if (x)")
        self.assertEqual(code, "if (x)")
        self.assertEqual(used, [])

    def test_empty(self):
        code, used = self.gen._parse_action("")
        self.assertEqual(code, "")
        self.assertEqual(used, [])

    def test_whitespace_only(self):
        code, used = self.gen._parse_action("   ")
        self.assertEqual(code, "")
        self.assertEqual(used, [])


# ============================================================
# 4. used_role_functions / used_variables 抽出
# ============================================================
class TestUsedSymbols(unittest.TestCase):
    def setUp(self):
        self.gen = InterruptGenerator()

    def test_extract_single_rf(self):
        h = make_handler("TIMER0", actions=[("", "Driver.Init")])
        rfs, vars_ = self.gen.extract_used_symbols(h)
        self.assertEqual(rfs, ["Driver.Init"])

    def test_extract_multiple_rfs(self):
        h = make_handler("TIMER0", actions=[
            ("", "Driver.Init"),
            ("", "Application.HandleTick"),
        ])
        rfs, _ = self.gen.extract_used_symbols(h)
        self.assertEqual(
            rfs, ["Driver.Init", "Application.HandleTick"],
        )

    def test_extract_dedup_rfs(self):
        h = make_handler("TIMER0", actions=[
            ("", "Driver.Init"),
            ("cond", "Driver.Init"),
        ])
        rfs, _ = self.gen.extract_used_symbols(h)
        self.assertEqual(rfs, ["Driver.Init"])

    def test_extract_variables_data(self):
        h = make_handler("TIMER0", actions=[
            ("", "ctx->data.counter++"),
        ])
        _, vars_ = self.gen.extract_used_symbols(h)
        self.assertEqual(vars_, ["counter"])

    def test_extract_variables_flags(self):
        h = make_handler("TIMER0", actions=[
            ("", "ctx->flags.EVT_START = 1"),
        ])
        _, vars_ = self.gen.extract_used_symbols(h)
        self.assertEqual(vars_, ["EVT_START"])

    def test_extract_variables_mixed(self):
        h = make_handler("TIMER0", actions=[
            ("", "ctx->data.counter++"),
            ("", "ctx->data.tick = 0"),
            ("", "ctx->flags.EVT_A = 1"),
        ])
        _, vars_ = self.gen.extract_used_symbols(h)
        self.assertIn("counter", vars_)
        self.assertIn("tick", vars_)
        self.assertIn("EVT_A", vars_)

    def test_empty_actions(self):
        h = make_handler("TIMER0", actions=[])
        rfs, vars_ = self.gen.extract_used_symbols(h)
        self.assertEqual(rfs, [])
        self.assertEqual(vars_, [])


# ============================================================
# 5. 完全な ISR 生成
# ============================================================
class TestFullIsrGeneration(unittest.TestCase):
    def setUp(self):
        self.gen = InterruptGenerator()

    def test_basic_structure(self):
        h = make_handler("TIMER0", actions=[("", "Driver.Init")])
        code = self.gen.generate_isr(h)
        self.assertIn("void ISR_TIMER0(void)", code)
        self.assertIn("SystemContext_t *ctx = &g_ctx;", code)
        self.assertIn("(void)ctx;", code)
        self.assertIn("RoleFunc_Driver_Init(NULL, ctx);", code)
        self.assertIn("[[STABLE_USER_CODE_START:TIMER0]]", code)
        self.assertIn("[[STABLE_USER_CODE_END:TIMER0]]", code)

    def test_comment_with_used_rfs(self):
        h = make_handler(
            "TIMER0",
            actions=[("", "Driver.Init"), ("", "Application.HandleTick")],
        )
        code = self.gen.generate_isr(h)
        self.assertIn("使用ロール関数", code)
        self.assertIn("- Driver.Init", code)
        self.assertIn("- Application.HandleTick", code)

    def test_comment_with_description(self):
        h = make_handler(
            "TIMER0", actions=[("", "Driver.Init")],
            description="タイマ満了時の処理",
        )
        code = self.gen.generate_isr(h)
        self.assertIn("タイマ満了時の処理", code)

    def test_condition_wrapped(self):
        h = make_handler("TIMER0", actions=[
            ("ctx->data.counter > 100", "Driver.HandleOverflow"),
        ])
        code = self.gen.generate_isr(h)
        self.assertIn("if (ctx->data.counter > 100) {", code)
        self.assertIn("RoleFunc_Driver_HandleOverflow(NULL, ctx);", code)

    def test_multiple_actions(self):
        h = make_handler("TIMER0", actions=[
            ("", "ctx->data.counter++"),
            ("", "Driver.Tick"),
            ("ctx->data.counter > 100", "Driver.Overflow"),
        ])
        code = self.gen.generate_isr(h)
        self.assertIn("ctx->data.counter++;", code)
        self.assertIn("RoleFunc_Driver_Tick(NULL, ctx);", code)
        self.assertIn("if (ctx->data.counter > 100) {", code)
        self.assertIn("RoleFunc_Driver_Overflow(NULL, ctx);", code)

    def test_enter_exit_logs(self):
        h = make_handler("TIMER0")
        code = self.gen.generate_isr(h)
        self.assertIn('LOG_DEBUG("Enter ISR: TIMER0");', code)
        self.assertIn('LOG_DEBUG("Exit ISR: TIMER0");', code)

    def test_empty_actions(self):
        h = make_handler("TIMER0")
        code = self.gen.generate_isr(h)
        self.assertIn("void ISR_TIMER0(void)", code)
        self.assertNotIn("（アクション未定義）", code)  # 空actions は section ごと省略

    def test_no_marker_duplication(self):
        h = make_handler("TIMER0", actions=[("", "Driver.Init")])
        code = self.gen.generate_isr(h)
        self.assertEqual(code.count("[[STABLE_USER_CODE_START:TIMER0]]"), 1)
        self.assertEqual(code.count("[[STABLE_USER_CODE_END:TIMER0]]"), 1)


# ============================================================
# 6. update_handler_symbols
# ============================================================
class TestUpdateHandler(unittest.TestCase):
    def test_updates_used_rfs(self):
        gen = InterruptGenerator()
        h = make_handler("TIMER0", actions=[("", "Driver.Init")])
        gen.update_handler_symbols(h)
        self.assertEqual(h.used_role_functions, ["Driver.Init"])

    def test_updates_used_vars(self):
        gen = InterruptGenerator()
        h = make_handler("TIMER0", actions=[
            ("", "ctx->data.counter++"),
        ])
        gen.update_handler_symbols(h)
        self.assertIn("counter", h.used_variables)

    def test_clears_previous(self):
        gen = InterruptGenerator()
        h = make_handler("TIMER0", actions=[("", "Driver.Init")])
        h.used_role_functions = ["OLD.Name"]
        gen.update_handler_symbols(h)
        self.assertEqual(h.used_role_functions, ["Driver.Init"])
        self.assertNotIn("OLD.Name", h.used_role_functions)


# ============================================================
# 7. generate_all_isrs
# ============================================================
class TestGenerateAll(unittest.TestCase):
    def test_multiple_handlers(self):
        gen = InterruptGenerator()
        gd = GlobalDefinitions()
        gd.interrupts.append(make_handler("TIMER0", [("", "Driver.Init")]))
        gd.interrupts.append(make_handler("UART_RX", [("", "Driver.Rx")]))
        code = gen.generate_all_isrs(gd)
        self.assertIn("void ISR_TIMER0(void)", code)
        self.assertIn("void ISR_UARTRX(void)", code)

    def test_update_handlers_flag(self):
        gen = InterruptGenerator()
        gd = GlobalDefinitions()
        h = make_handler("TIMER0", [("", "Driver.Init")])
        gd.interrupts.append(h)
        gen.generate_all_isrs(gd, update_handlers=True)
        self.assertEqual(h.used_role_functions, ["Driver.Init"])


# ============================================================
# 8. マージ往復（ユーザーコード保持）
# ============================================================
class TestIsrMergeRoundTrip(unittest.TestCase):
    def setUp(self):
        self.gen = InterruptGenerator()
        self.merger = CodeMerger()

    def test_user_code_preserved(self):
        h = make_handler("TIMER0", actions=[("", "Driver.Init")])
        generated = self.gen.generate_isr(h)

        user_edited = generated.replace(
            "    /* ユーザー追加コードをここに記述 */",
            "    counter = 0;",
        )
        regenerated = self.gen.generate_isr(h)
        merged = self.merger.merge_file(regenerated, user_edited)
        self.assertIn("counter = 0;", merged)
        self.assertNotIn(
            "/* ユーザー追加コードをここに記述 */", merged
        )

    def test_marker_matches_merger_pattern(self):
        """生成マーカーが CodeMerger の抽出パターンと一致"""
        h = make_handler("TIMER0", actions=[("", "Driver.Init")])
        code = self.gen.generate_isr(h)
        # ISR_(\w+)\s*\( の抽出
        m = re.search(r'ISR_(\w+)\s*\(', code)
        self.assertIsNotNone(m)
        extracted_name = m.group(1)
        self.assertEqual(extracted_name, "TIMER0")
        self.assertIn(
            f"[[STABLE_USER_CODE_START:{extracted_name}]]", code,
        )

    def test_marker_matches_merger_pattern_snake(self):
        """UART_RX → ISR_UARTRX / マーカー UARTRX の整合"""
        h = make_handler("UART_RX", actions=[("", "Driver.Rx")])
        code = self.gen.generate_isr(h)
        m = re.search(r'ISR_(\w+)\s*\(', code)
        self.assertEqual(m.group(1), "UARTRX")
        self.assertIn("[[STABLE_USER_CODE_START:UARTRX]]", code)

    def test_no_merge_preserves_generated(self):
        h = make_handler("TIMER0", actions=[("", "Driver.Init")])
        generated = self.gen.generate_isr(h)
        merged = self.merger.merge_file(generated, None)
        self.assertIn("void ISR_TIMER0(void)", merged)
        self.assertIn("RoleFunc_Driver_Init(NULL, ctx);", merged)


# ============================================================
# 実行
# ============================================================
def run_tests(dump: bool = False):
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [
        TestIsrNames,
        TestContextInsert,
        TestActionParse,
        TestUsedSymbols,
        TestFullIsrGeneration,
        TestUpdateHandler,
        TestGenerateAll,
        TestIsrMergeRoundTrip,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    ok = runner.run(suite).wasSuccessful()

    if dump:
        _dump_sample_isr()

    return ok


def _dump_sample_isr(output_dir=None):
    if output_dir is None:
        output_dir = os.path.join(_THIS_DIR, '_generated')
    os.makedirs(output_dir, exist_ok=True)

    gen = InterruptGenerator()
    handlers = [
        make_handler("TIMER0", actions=[
            ("", "ctx->data.counter++"),
            ("", "Driver.Init"),
            ("ctx->data.counter > 100", "Application.HandleOverflow"),
        ], description="タイマ満了時の処理"),
        make_handler("UART_RX", actions=[
            ("", "Driver.Rx"),
        ], description="UART 受信割り込み"),
    ]
    lines = []
    for h in handlers:
        lines.append(gen.generate_isr(h))
        lines.append("")
    output = '\n'.join(lines)
    path = os.path.join(output_dir, 'isr_sample.c')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(output)
    print(f"\n[ダンプ] {path} に ISR 生成サンプルを出力しました")


if __name__ == '__main__':
    sys.exit(0 if run_tests(dump=True) else 1)