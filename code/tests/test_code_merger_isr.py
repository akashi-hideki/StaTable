# tests/test_code_merger_isr.py
"""
CodeMerger の ISR マーカー対応テスト（H1 Stage 2）

命名規則:
  - ISR 関数名: ISR_{PascalCase(handler.name)}
  - マーカー名: {PascalCase(handler.name)}
  例: handler.name="UART_RX" → ISR_UARTRX / [[STABLE_USER_CODE_START:UARTRX]]
"""

import sys
import os

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_DIR = os.path.dirname(_THIS_DIR)
_CODEGEN_DIR = os.path.join(_CODE_DIR, 'codegen')

for _p in (_CODEGEN_DIR, _CODE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import unittest

from code_merger import CodeMerger


# ============================================================
# 1. ISR マーカー抽出
# ============================================================
class TestIsrMarkerExtraction(unittest.TestCase):

    def setUp(self):
        self.merger = CodeMerger()

    def test_extract_isr_user_code(self):
        content = """
void ISR_TIMER0(void)
{
    LOG_DEBUG("Enter ISR");
    /* [[STABLE_USER_CODE_START:TIMER0]] */
    user_edited_code();
    counter++;
    /* [[STABLE_USER_CODE_END:TIMER0]] */
    LOG_DEBUG("Exit ISR");
}
"""
        code = self.merger.extract_func_user_code(content, "TIMER0")
        self.assertIn("user_edited_code();", code)
        self.assertIn("counter++;", code)

    def test_extract_all_includes_isr(self):
        content = """
int RoleFunc_Driver_Init(...)
{
    /* [[STABLE_USER_CODE_START:Driver_Init]] */
    init_body();
    /* [[STABLE_USER_CODE_END:Driver_Init]] */
    return ret;
}

void ISR_TIMER0(void)
{
    /* [[STABLE_USER_CODE_START:TIMER0]] */
    isr_body();
    /* [[STABLE_USER_CODE_END:TIMER0]] */
}
"""
        codes = self.merger.extract_all_func_user_codes(content)
        self.assertIn("Driver_Init", codes)
        self.assertIn("TIMER0", codes)
        self.assertIn("init_body();", codes["Driver_Init"])
        self.assertIn("isr_body();", codes["TIMER0"])

    def test_extract_all_multiple_isrs(self):
        """
        複数 ISR の抽出。命名規則は PascalCase に統一。
        - ISR_TIMER0  : "TIMER0"（元から PascalCase）
        - ISR_UARTRX  : "UARTRX"（"UART_RX" の PascalCase）
        """
        content = """
void ISR_TIMER0(void) {
    /* [[STABLE_USER_CODE_START:TIMER0]] */
    t0_body();
    /* [[STABLE_USER_CODE_END:TIMER0]] */
}
void ISR_UARTRX(void) {
    /* [[STABLE_USER_CODE_START:UARTRX]] */
    rx_body();
    /* [[STABLE_USER_CODE_END:UARTRX]] */
}
"""
        codes = self.merger.extract_all_func_user_codes(content)
        self.assertEqual(len(codes), 2)
        self.assertIn("TIMER0", codes)
        self.assertIn("UARTRX", codes)
        self.assertIn("t0_body();", codes["TIMER0"])
        self.assertIn("rx_body();", codes["UARTRX"])


# ============================================================
# 2. ISR マーカー注入
# ============================================================
class TestIsrMarkerInjection(unittest.TestCase):

    def setUp(self):
        self.merger = CodeMerger()

    def test_inject_isr_user_code(self):
        generated = """
void ISR_TIMER0(void)
{
    LOG_DEBUG("Enter ISR");
    /* [[STABLE_USER_CODE_START:TIMER0]] */
    /* ユーザー実装コードをここに記述 */
    /* [[STABLE_USER_CODE_END:TIMER0]] */
    LOG_DEBUG("Exit ISR");
}
"""
        result = self.merger.inject_func_user_code(
            generated, "TIMER0", "my_custom_code();"
        )
        self.assertIn("my_custom_code();", result)
        self.assertNotIn(
            "/* ユーザー実装コードをここに記述 */", result
        )

    def test_inject_no_marker_returns_unchanged(self):
        generated = "void foo(void) {}\n"
        result = self.merger.inject_func_user_code(
            generated, "TIMER0", "code();"
        )
        self.assertEqual(result, generated)


# ============================================================
# 3. ISR を含むファイル全体のマージ
# ============================================================
class TestIsrMergeFile(unittest.TestCase):

    def setUp(self):
        self.merger = CodeMerger()

    def test_merge_preserves_isr_user_code(self):
        generated = """#include "statable_all.h"

void ISR_TIMER0(void)
{
    SystemContext_t *ctx = &g_ctx;
    (void)ctx;
    LOG_DEBUG("Enter ISR");

    /* [[STABLE_USER_CODE_START:TIMER0]] */
    /* ユーザー実装コードをここに記述 */
    /* [[STABLE_USER_CODE_END:TIMER0]] */

    LOG_DEBUG("Exit ISR");
}
"""
        existing = """#include "statable_all.h"

void ISR_TIMER0(void)
{
    SystemContext_t *ctx = &g_ctx;
    (void)ctx;
    LOG_DEBUG("Enter ISR");

    /* [[STABLE_USER_CODE_START:TIMER0]] */
    counter++;
    if (counter > 100) {
        counter = 0;
    }
    /* [[STABLE_USER_CODE_END:TIMER0]] */

    LOG_DEBUG("Exit ISR");
}
"""
        merged = self.merger.merge_file(generated, existing)
        self.assertIn("counter++;", merged)
        self.assertIn("counter = 0;", merged)
        self.assertNotIn(
            "/* ユーザー実装コードをここに記述 */", merged
        )

    def test_merge_both_rolfunc_and_isr(self):
        """RoleFunc と ISR が同じファイル内で共存"""
        generated = """#include "statable_all.h"

int RoleFunc_Driver_Init(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx)
{
    /* [[STABLE_USER_CODE_START:Driver_Init]] */
    /* ユーザー実装コードをここに記述 */
    /* [[STABLE_USER_CODE_END:Driver_Init]] */
    return 0;
}

void ISR_TIMER0(void)
{
    /* [[STABLE_USER_CODE_START:TIMER0]] */
    /* ユーザー実装コードをここに記述 */
    /* [[STABLE_USER_CODE_END:TIMER0]] */
}
"""
        existing = """#include "statable_all.h"

int RoleFunc_Driver_Init(...)
{
    /* [[STABLE_USER_CODE_START:Driver_Init]] */
    init_body();
    /* [[STABLE_USER_CODE_END:Driver_Init]] */
    return 0;
}

void ISR_TIMER0(void)
{
    /* [[STABLE_USER_CODE_START:TIMER0]] */
    isr_body();
    /* [[STABLE_USER_CODE_END:TIMER0]] */
}
"""
        merged = self.merger.merge_file(generated, existing)
        self.assertIn("init_body();", merged)
        self.assertIn("isr_body();", merged)


# ============================================================
# 4. get_user_code_summary
# ============================================================
class TestUserCodeSummary(unittest.TestCase):

    def setUp(self):
        self.merger = CodeMerger()

    def test_summary_counts_isr(self):
        content = """
int RoleFunc_Driver_Init(...)
{
    /* [[STABLE_USER_CODE_START:Driver_Init]] */
    x();
    /* [[STABLE_USER_CODE_END:Driver_Init]] */
}

void ISR_TIMER0(void)
{
    /* [[STABLE_USER_CODE_START:TIMER0]] */
    y();
    /* [[STABLE_USER_CODE_END:TIMER0]] */
}
"""
        summary = self.merger.get_user_code_summary(content)
        # func_user_codes に Driver_Init と TIMER0 の 2 件
        self.assertEqual(summary['func_user_codes'], 2)


# ============================================================
# 実行
# ============================================================
def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [
        TestIsrMarkerExtraction,
        TestIsrMarkerInjection,
        TestIsrMergeFile,
        TestUserCodeSummary,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite).wasSuccessful()


if __name__ == '__main__':
    sys.exit(0 if run_tests() else 1)