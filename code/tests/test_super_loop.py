# tests/test_super_loop.py
"""
スーパーループ {project_name}_run.c の単体テスト
"""

import sys
import os
import tempfile
import shutil

_THIS_DIR    = os.path.dirname(os.path.abspath(__file__))
_CODE_DIR    = os.path.dirname(_THIS_DIR)
_CODEGEN_DIR = os.path.join(_CODE_DIR, 'codegen')

for _p in (_CODEGEN_DIR, _CODE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import unittest

from sample_data import SampleDataGenerator
from c_code_generator import CCodeGenerator
from config import CodeGenerationConfig


def make_sample():
    return SampleDataGenerator().get_sample_data()


# ============================================================
# 1. ファイル名の動的決定
# ============================================================
class TestFilename(unittest.TestCase):

    def test_default_filename(self):
        gen = CCodeGenerator()
        self.assertEqual(
            gen.super_loop_filename,
            "MyProject_run.c",
        )

    def test_custom_project_name(self):
        cfg = CodeGenerationConfig(project_name="TestProject")
        gen = CCodeGenerator(config=cfg)
        self.assertEqual(
            gen.super_loop_filename,
            "TestProject_run.c",
        )

    def test_file_in_generators(self):
        gen = CCodeGenerator()
        self.assertIn(
            "MyProject_run.c",
            gen.file_generators,
        )

    def test_file_in_steps(self):
        gen = CCodeGenerator()
        self.assertIn(
            "MyProject_run.c",
            gen.FILE_STEPS,
        )

    def test_file_in_dispatch(self):
        gen = CCodeGenerator()
        self.assertIn(
            "MyProject_run.c",
            gen.FILE_DISPATCH,
        )

    def test_file_category_is_src(self):
        gen = CCodeGenerator()
        self.assertEqual(
            gen.FILE_CATEGORY.get("MyProject_run.c"),
            'src',
        )


# ============================================================
# 2. 生成内容
# ============================================================
class TestContent(unittest.TestCase):

    def setUp(self):
        self.sm, self.gd = make_sample()
        self.gen = CCodeGenerator()
        files = self.gen.generate_all(self.sm, self.gd)
        self.code = files['MyProject_run.c']

    def test_include(self):
        self.assertIn('#include "statable_all.h"', self.code)

    def test_context_var_non_static(self):
        """g_ctx は static でない（extern 対応）"""
        self.assertIn(
            '\nSystemContext_t g_ctx;', self.code
        )
        self.assertNotIn(
            'static SystemContext_t g_ctx;', self.code
        )

    def test_state_var_non_static(self):
        """g_state は static でない"""
        self.assertIn('STATE_t g_state;', self.code)
        self.assertNotIn('static STATE_t g_state;', self.code)

    def test_init_func(self):
        self.assertIn(
            'void MyProject_Init(void)', self.code
        )

    def test_run_func(self):
        self.assertIn(
            'void MyProject_Run(void)', self.code
        )

    def test_init_calls_system_context_init(self):
        self.assertIn(
            'SystemContext_Init(&g_ctx);', self.code
        )

    def test_init_sets_initial_state(self):
        """initial_state が反映される"""
        self.assertIn(
            'g_state = STATE_INIT;', self.code
        )

    def test_run_while(self):
        self.assertIn('while (1) {', self.code)

    def test_run_get_next_event(self):
        self.assertIn(
            'StateMachine_GetNextEvent(&g_ctx)', self.code
        )

    def test_run_process(self):
        self.assertIn(
            'StateMachine_Process(g_state, evt, &g_ctx)',
            self.code,
        )

    def test_run_event_none_check(self):
        self.assertIn('EVENT_NONE', self.code)

    def test_file_comment(self):
        self.assertIn('@file    MyProject_run.c', self.code)
        self.assertIn('スーパーループ', self.code)


# ============================================================
# 3. 層名付きバージョン
# ============================================================
class TestWithLayerName(unittest.TestCase):

    def setUp(self):
        self.sm, self.gd = make_sample()
        self.sm.layer_name = "Driver"
        self.gen = CCodeGenerator()
        files = self.gen.generate_all(self.sm, self.gd)
        self.code = files['MyProject_run.c']

    def test_state_var_layer(self):
        self.assertIn(
            'STATE_Driver_t g_Driver_state;', self.code
        )

    def test_init_state_layer(self):
        self.assertIn(
            'g_Driver_state = STATE_Driver_INIT;', self.code
        )

    def test_get_next_event_layer(self):
        self.assertIn(
            'StateMachine_GetNextEvent_Driver(&g_ctx)',
            self.code,
        )

    def test_process_layer(self):
        self.assertIn(
            'StateMachine_Process_Driver('
            'g_Driver_state, evt, &g_ctx)',
            self.code,
        )

    def test_event_none_layer(self):
        self.assertIn('EVENT_Driver_NONE', self.code)


# ============================================================
# 4. スーパーインクルードの extern 宣言
# ============================================================
class TestExternInSuperInclude(unittest.TestCase):

    def setUp(self):
        self.sm, self.gd = make_sample()
        self.gen = CCodeGenerator()
        files = self.gen.generate_all(self.sm, self.gd)
        self.code = files['statable_all.h']

    def test_extern_var_section(self):
        self.assertIn(
            'スーパーループ変数（extern）', self.code
        )

    def test_extern_context(self):
        self.assertIn(
            'extern SystemContext_t g_ctx;', self.code
        )

    def test_extern_state(self):
        self.assertIn(
            'extern STATE_t g_state;', self.code
        )

    def test_extern_func_section(self):
        self.assertIn(
            'スーパーループ関数', self.code
        )

    def test_extern_init(self):
        self.assertIn(
            'void MyProject_Init(void);', self.code
        )

    def test_extern_run(self):
        self.assertIn(
            'void MyProject_Run(void);', self.code
        )


# ============================================================
# 5. 層名付き extern
# ============================================================
class TestExternWithLayerName(unittest.TestCase):

    def setUp(self):
        self.sm, self.gd = make_sample()
        self.sm.layer_name = "Driver"
        self.gen = CCodeGenerator()
        files = self.gen.generate_all(self.sm, self.gd)
        self.code = files['statable_all.h']

    def test_extern_state_layer(self):
        self.assertIn(
            'extern STATE_Driver_t g_Driver_state;',
            self.code,
        )


# ============================================================
# 6. 配置（by_type / flat）
# ============================================================
class TestPlacement(unittest.TestCase):

    def setUp(self):
        self.sm, self.gd = make_sample()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_by_type_src(self):
        cfg = CodeGenerationConfig(folder_structure='by_type')
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        gen.save_generated_code(files, self.tmpdir)

        path = os.path.join(
            self.tmpdir, 'src', 'MyProject_run.c'
        )
        self.assertTrue(os.path.isfile(path))

    def test_flat_root(self):
        cfg = CodeGenerationConfig(folder_structure='flat')
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        gen.save_generated_code(files, self.tmpdir)

        path = os.path.join(self.tmpdir, 'MyProject_run.c')
        self.assertTrue(os.path.isfile(path))

    def test_by_type_total_13_files(self):
        cfg = CodeGenerationConfig(folder_structure='by_type')
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        saved = gen.save_generated_code(files, self.tmpdir)

        # 11 + super_include + super_loop = 13
        self.assertEqual(len(saved), 13)


# ============================================================
# 7. カスタム project_name
# ============================================================
class TestCustomProjectName(unittest.TestCase):

    def setUp(self):
        self.sm, self.gd = make_sample()

    def test_filename_reflects_project(self):
        cfg = CodeGenerationConfig(project_name="MyApp")
        gen = CCodeGenerator(config=cfg)
        self.assertEqual(
            gen.super_loop_filename, "MyApp_run.c"
        )

    def test_function_name_reflects_project(self):
        cfg = CodeGenerationConfig(project_name="MyApp")
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        code = files['MyApp_run.c']

        self.assertIn('void MyApp_Init(void)', code)
        self.assertIn('void MyApp_Run(void)', code)

    def test_extern_reflects_project(self):
        cfg = CodeGenerationConfig(project_name="MyApp")
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        code = files['statable_all.h']

        self.assertIn('void MyApp_Init(void);', code)
        self.assertIn('void MyApp_Run(void);', code)


# ============================================================
# 8. 統合テスト
# ============================================================
class TestIntegration(unittest.TestCase):

    def setUp(self):
        self.sm, self.gd = make_sample()

    def test_file_count_13(self):
        gen = CCodeGenerator()
        files = gen.generate_all(self.sm, self.gd)
        self.assertEqual(len(files), 13)

    def test_super_include_and_loop_both_present(self):
        gen = CCodeGenerator()
        files = gen.generate_all(self.sm, self.gd)
        self.assertIn('statable_all.h', files)
        self.assertIn('MyProject_run.c', files)

    def test_initial_state_from_sample(self):
        """sample_data の set_initial('INIT') が反映される"""
        gen = CCodeGenerator()
        files = gen.generate_all(self.sm, self.gd)
        code = files['MyProject_run.c']
        self.assertIn('g_state = STATE_INIT;', code)


# ============================================================
# 実行
# ============================================================
def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [
        TestFilename,
        TestContent,
        TestWithLayerName,
        TestExternInSuperInclude,
        TestExternWithLayerName,
        TestPlacement,
        TestCustomProjectName,
        TestIntegration,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite).wasSuccessful()


if __name__ == '__main__':
    sys.exit(0 if run_tests() else 1)