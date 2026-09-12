# tests/test_c_code_generator.py
"""
CCodeGenerator の全機能テスト
（ステップテーブル駆動版）

実行方法:
    cd code
    python -m tests.test_c_code_generator
    または
    python tests/test_c_code_generator.py
"""

import sys
import os

# ============================================================
# sys.path セットアップ
# ============================================================
_THIS_DIR    = os.path.dirname(
    os.path.abspath(__file__)
)
_CODE_DIR    = os.path.dirname(_THIS_DIR)
_CODEGEN_DIR = os.path.join(_CODE_DIR, 'codegen')

for _p in (_CODEGEN_DIR, _CODE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import unittest
from pathlib import Path
from typing import Optional

# ============================================================
# サンプルデータ
# ============================================================
try:
    from codegen.sample_data import (
        SampleDataGenerator,
    )
except ImportError:
    from sample_data import SampleDataGenerator

from c_code_generator import CCodeGenerator
from config import CodeGenerationConfig


# ============================================================
# テスト用ヘルパー
# ============================================================
def make_sample():
    gen = SampleDataGenerator()
    return gen.get_sample_data()


# ============================================================
# 1. ステップテーブルの整合性
# ============================================================
class TestStepTables(unittest.TestCase):
    """ステップテーブルと実行辞書の整合性"""

    def setUp(self):
        self.gen = CCodeGenerator()

    def test_all_file_steps_actions_resolvable(self):
        """全 FILE_STEPS の action が
           step_executors に存在すること"""
        for filename, steps in (
            self.gen.FILE_STEPS.items()
        ):
            for step in steps:
                action = step.get('action', '')
                self.assertIn(
                    action,
                    self.gen.step_executors,
                    f"{filename}: "
                    f"unknown action '{action}'",
                )

    def test_all_files_have_steps(self):
        """全 file_generators に対応する
           FILE_STEPS があること"""
        for filename in self.gen.file_generators:
            self.assertIn(
                filename,
                self.gen.FILE_STEPS,
                f"missing FILE_STEPS: {filename}",
            )

    def test_all_files_have_dispatch(self):
        """全 file_generators に対応する
           FILE_DISPATCH があること"""
        for filename in self.gen.file_generators:
            self.assertIn(
                filename,
                self.gen.FILE_DISPATCH,
                f"missing FILE_DISPATCH: {filename}",
            )

    def test_dispatch_methods_exist(self):
        """FILE_DISPATCH のメソッドが存在すること"""
        for filename, method_name in (
            self.gen.FILE_DISPATCH.items()
        ):
            self.assertTrue(
                hasattr(self.gen, method_name),
                f"missing method: {method_name}",
            )

    def test_struct_dispatch_has_all_kinds(self):
        """STRUCT_KIND_DISPATCH に
           3種類が登録されていること"""
        for kind in (
            'system_data',
            'event_flags',
            'system_context',
        ):
            self.assertIn(
                kind,
                self.gen.STRUCT_KIND_DISPATCH,
            )


# ============================================================
# 2. 単一ファイル生成
# ============================================================
class TestSingleFileGeneration(unittest.TestCase):
    """個別ファイル生成の疎通"""

    def setUp(self):
        self.gen = CCodeGenerator()
        self.sm, self.gd = make_sample()

    def test_generate_types_header(self):
        code = self.gen._generate_types_header(
            self.sm, self.gd
        )
        self.assertIn(
            '#ifndef STATABLE_TYPES_H', code
        )
        self.assertIn(
            '#endif /* STATABLE_TYPES_H */', code
        )
        self.assertIn('typedef enum', code)
        self.assertIn('SystemContext_t', code)

    def test_generate_transitions_header(self):
        code = self.gen._generate_transitions_header(
            self.sm, self.gd
        )
        self.assertIn(
            '#ifndef STATABLE_TRANSITIONS_H', code
        )
        self.assertIn(
            'STATE_t StateMachine_Process(', code
        )
    def test_generate_transitions_source(self):
        code = self.gen._generate_transitions_source(
            self.sm, self.gd
        )
        self.assertIn(
            'static STATE_t t_', code,
            "cell prototypes missing"
        )
        self.assertIn(
            'transition_matrix', code,
        )
        self.assertIn(
            'StateMachine_Process', code,
        )
        count = code.count('static STATE_t t_')
        self.assertGreaterEqual(
            count, 8,
            f"expected >= 8 cell func lines, "
            f"got {count}",
        )

    def test_generate_role_functions_header(self):
        code = self.gen._generate_role_functions_header(
            self.sm, self.gd
        )
        self.assertIn(
            '#ifndef STATABLE_ROLE_FUNCTIONS_H', code
        )
        self.assertIn('RoleFunc_', code)

    def test_generate_role_functions_source(self):
        code = self.gen._generate_role_functions_source(
            self.sm, self.gd
        )
        self.assertIn('RoleFunc_', code)
        self.assertIn('return ret;', code)

    def test_generate_init_source(self):
        code = self.gen._generate_init_source(
            self.sm, self.gd
        )
        self.assertIn('SystemContext_Init', code)

    def test_generate_event_queue_source(self):
        code = self.gen._generate_event_queue_source(
            self.sm, self.gd
        )
        # キューあり or なしコメントのどちらか
        self.assertTrue(
            'EventQueue' in code
            or 'イベントキュー' in code
        )

    def test_generate_interrupt_source(self):
        code = self.gen._generate_interrupt_source(
            self.sm, self.gd
        )
        self.assertTrue(
            'ISR_' in code
            or '割り込み' in code
        )

    def test_generate_timer_source(self):
        code = self.gen._generate_timer_source(
            self.sm, self.gd
        )
        self.assertIn('TimerVariables_t', code)
        self.assertIn('Timer_Init', code)
        self.assertIn('Timer_Update', code)

    def test_generate_osal_header(self):
        code = self.gen._generate_osal_header(
            self.sm, self.gd
        )
        self.assertIn('OSAL', code)

    def test_generate_osal_source(self):
        code = self.gen._generate_osal_source(
            self.sm, self.gd
        )
        self.assertIn('OSAL', code)


# ============================================================
# 3. 一括生成
# ============================================================
class TestGenerateAll(unittest.TestCase):
    """generate_all の網羅性"""

    def setUp(self):
        self.gen = CCodeGenerator()
        self.sm, self.gd = make_sample()

    def test_all_files_generated(self):
        files = self.gen.generate_all(
            self.sm, self.gd
        )
        for filename in self.gen.file_generators:
            self.assertIn(filename, files)
            self.assertTrue(
                len(files[filename]) > 0,
                f"{filename} is empty",
            )

    def test_file_count(self):
        files = self.gen.generate_all(
            self.sm, self.gd
        )
        self.assertEqual(
            len(files),
            len(self.gen.file_generators),
        )

    def test_with_role_function_library(self):
        """共有ライブラリを渡した場合"""

        class DummyRF:
            def __init__(self, name):
                self.name = name
                self.title = name
                self.description = ""

        class DummyLib:
            def list_all(self):
                return [
                    DummyRF("SharedOnlyFunc")
                ]

        files = self.gen.generate_all(
            self.sm, self.gd,
            role_function_library=DummyLib(),
        )
        rc = files['statable_role_functions.c']
        self.assertIn(
            'SharedOnlyFunc', rc,
            "共有ライブラリの関数が含まれない",
        )

    def test_without_role_function_library(self):
        files = self.gen.generate_all(
            self.sm, self.gd
        )
        rc = files['statable_role_functions.c']
        self.assertNotIn('SharedOnlyFunc', rc)

    def test_state_machine_roles_preserved(self):
        """state_machine 側の関数が消えないこと"""
        files = self.gen.generate_all(
            self.sm, self.gd
        )
        rc = files['statable_role_functions.c']
        # サンプルに登録されている関数の1つ
        self.assertIn('RoleFunc_', rc)


# ============================================================
# 4. 設定反映
# ============================================================
class TestConfigApplied(unittest.TestCase):
    """設定が生成に反映されること"""

    def setUp(self):
        self.sm, self.gd = make_sample()

    def test_os_type_non_rtos(self):
        cfg = CodeGenerationConfig(os_type='non_rtos')
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        self.assertIn('osal.h', files)

    def test_generation_style_switch_case(self):
        cfg = CodeGenerationConfig(
            generation_style='switch_case'
        )
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        self.assertIn(
            'statable_transitions.c', files
        )

    def test_table_type_array(self):
        cfg = CodeGenerationConfig(table_type='array')
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        self.assertIn(
            'statable_transitions.c', files
        )


# ============================================================
# 5. 生成コードの品質確認
# ============================================================
class TestGeneratedCodeQuality(unittest.TestCase):
    """生成コードに必要な要素が含まれること"""

    def setUp(self):
        self.gen = CCodeGenerator()
        self.sm, self.gd = make_sample()
        self.files = self.gen.generate_all(
            self.sm, self.gd
        )

    def test_no_trailing_whitespace(self):
        """各行末に不要な空白がない"""
        for filename, code in self.files.items():
            for i, line in enumerate(
                code.split('\n'), 1
            ):
                self.assertEqual(
                    line, line.rstrip(),
                    f"{filename}:{i} trailing space",
                )

    def test_no_tabs(self):
        """タブ文字が含まれない"""
        for filename, code in self.files.items():
            self.assertNotIn(
                '\t', code,
                f"{filename} contains tab",
            )

    def test_file_header_present(self):
        """全ファイルに @file がある"""
        for filename, code in self.files.items():
            self.assertIn(
                '@file', code,
                f"{filename} has no @file",
            )

    def test_include_guards_paired(self):
        """#ifndef と #endif の対応"""
        for filename, code in self.files.items():
            ifndef_count = code.count('#ifndef')
            endif_count = code.count('#endif')
            self.assertEqual(
                ifndef_count, endif_count,
                f"{filename}: "
                f"ifndef={ifndef_count}, "
                f"endif={endif_count}",
            )


# ============================================================
# 6. 生成順序（ステップテーブル通り）
# ============================================================
class TestGenerationOrder(unittest.TestCase):
    """ステップテーブルの順序確認"""

    def setUp(self):
        self.gen = CCodeGenerator()
        self.sm, self.gd = make_sample()

    def test_types_header_order(self):
        code = self.gen._generate_types_header(
            self.sm, self.gd
        )
        pos_guard  = code.index('#ifndef')
        pos_enum   = code.index('typedef enum')
        pos_ctx    = code.index('SystemContext_t')
        pos_endif  = code.index('#endif')

        self.assertLess(pos_guard, pos_enum)
        self.assertLess(pos_enum, pos_ctx)
        self.assertLess(pos_ctx, pos_endif)

    def test_transitions_header_order(self):
        code = self.gen._generate_transitions_header(
            self.sm, self.gd
        )
        pos_guard = code.index('#ifndef')
        pos_func  = code.index('StateMachine_Process')
        pos_endif = code.index('#endif')

        self.assertLess(pos_guard, pos_func)
        self.assertLess(pos_func, pos_endif)


# ============================================================
# 7. 生成コードのダンプ
# ============================================================
def dump_generated_code(
    output_dir: Optional[str] = None,
    full_preview: bool = True,
) -> str:
    """
    生成コードをファイルと
    コンソールに出力
    """
    if output_dir is None:
        output_dir = os.path.join(
            _THIS_DIR, '_generated_ccodegen'
        )
    Path(output_dir).mkdir(
        parents=True, exist_ok=True
    )

    gen = CCodeGenerator()
    sm, gd = make_sample()
    files = gen.generate_all(sm, gd)

    # ファイル出力
    for filename, content in files.items():
        path = os.path.join(output_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    sep = "=" * 70
    print(f"\n{sep}")
    print(f"  生成コード出力: {output_dir}")
    print(sep)
    for filename in files:
        print(f"  - {filename}")

    if not full_preview:
        return output_dir

    # コンソール出力
    for filename, content in files.items():
        print(f"\n{sep}")
        print(f"  {filename} （全文）")
        print(sep)
        print(content)

    return output_dir


# ============================================================
# テスト実行
# ============================================================
def run_tests(dump: bool = True,
              full_preview: bool = False):
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestStepTables,
        TestSingleFileGeneration,
        TestGenerateAll,
        TestConfigApplied,
        TestGeneratedCodeQuality,
        TestGenerationOrder,
    ]
    for cls in test_classes:
        suite.addTests(
            loader.loadTestsFromTestCase(cls)
        )

    runner = unittest.TextTestRunner(verbosity=2)
    ok = runner.run(suite).wasSuccessful()

    if dump:
        try:
            dump_generated_code(
                full_preview=full_preview
            )
        except Exception as e:
            print(f"\n[ダンプ失敗] {e}")

    return ok


if __name__ == '__main__':
    sys.exit(0 if run_tests() else 1)