# tests/test_folder_structure.py
"""
フォルダ構成反映の単体テスト
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


# 期待ファイル数（スーパーインクルード含む）
EXPECTED_FILE_COUNT = 12


def make_sample():
    return SampleDataGenerator().get_sample_data()


# ============================================================
# 1. _resolve_output_path のテスト
# ============================================================
class TestResolveOutputPath(unittest.TestCase):

    def test_flat(self):
        cfg = CodeGenerationConfig(folder_structure='flat')
        gen = CCodeGenerator(config=cfg)
        for name in ['statable_types.h',
                     'statable_transitions.c',
                     'osal.h']:
            self.assertEqual(
                gen._resolve_output_path(name),
                name,
            )

    def test_by_type_include(self):
        cfg = CodeGenerationConfig(folder_structure='by_type')
        gen = CCodeGenerator(config=cfg)
        self.assertEqual(
            gen._resolve_output_path('statable_types.h'),
            os.path.join('include', 'statable_types.h'),
        )
        self.assertEqual(
            gen._resolve_output_path('statable_transitions.h'),
            os.path.join('include', 'statable_transitions.h'),
        )
        self.assertEqual(
            gen._resolve_output_path('statable_role_functions.h'),
            os.path.join('include', 'statable_role_functions.h'),
        )

    def test_by_type_src(self):
        cfg = CodeGenerationConfig(folder_structure='by_type')
        gen = CCodeGenerator(config=cfg)
        for name in ['statable_transitions.c',
                     'statable_role_functions.c',
                     'statable_init.c',
                     'statable_event_queue.c',
                     'statable_interrupt.c',
                     'statable_timer.c']:
            self.assertEqual(
                gen._resolve_output_path(name),
                os.path.join('src', name),
            )

    def test_by_type_common(self):
        cfg = CodeGenerationConfig(folder_structure='by_type')
        gen = CCodeGenerator(config=cfg)
        self.assertEqual(
            gen._resolve_output_path('osal.h'),
            os.path.join('common', 'osal.h'),
        )
        self.assertEqual(
            gen._resolve_output_path('osal.c'),
            os.path.join('common', 'osal.c'),
        )

    def test_by_type_super_include(self):
        """statable_all.h は common/ に配置"""
        cfg = CodeGenerationConfig(folder_structure='by_type')
        gen = CCodeGenerator(config=cfg)
        self.assertEqual(
            gen._resolve_output_path('statable_all.h'),
            os.path.join('common', 'statable_all.h'),
        )

    def test_by_type_custom_dir_names(self):
        cfg = CodeGenerationConfig(
            folder_structure='by_type',
            include_dir_name='inc',
            source_dir_name='source',
            common_dir_name='shared',
        )
        gen = CCodeGenerator(config=cfg)
        self.assertEqual(
            gen._resolve_output_path('statable_types.h'),
            os.path.join('inc', 'statable_types.h'),
        )
        self.assertEqual(
            gen._resolve_output_path('statable_init.c'),
            os.path.join('source', 'statable_init.c'),
        )
        self.assertEqual(
            gen._resolve_output_path('osal.h'),
            os.path.join('shared', 'osal.h'),
        )

    def test_by_layer_with_layer_name(self):
        cfg = CodeGenerationConfig(folder_structure='by_layer')
        gen = CCodeGenerator(config=cfg)
        self.assertEqual(
            gen._resolve_output_path('statable_types.h', 'Application'),
            os.path.join('Application', 'statable_types.h'),
        )

    def test_by_layer_without_layer_name(self):
        """by_layer + 空 layer → flat フォールバック"""
        cfg = CodeGenerationConfig(folder_structure='by_layer')
        gen = CCodeGenerator(config=cfg)
        self.assertEqual(
            gen._resolve_output_path('statable_types.h', ''),
            'statable_types.h',
        )

    def test_unknown_structure(self):
        """未知の値 → flat フォールバック"""
        cfg = CodeGenerationConfig(folder_structure='unknown')
        gen = CCodeGenerator(config=cfg)
        self.assertEqual(
            gen._resolve_output_path('statable_types.h'),
            'statable_types.h',
        )


# ============================================================
# 2. save_generated_code のテスト
# ============================================================
class TestSaveGeneratedCode(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.sm, self.gd = make_sample()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_flat_saves_to_root(self):
        cfg = CodeGenerationConfig(folder_structure='flat')
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        saved = gen.save_generated_code(files, self.tmpdir)

        # ★ 12 に変更（statable_all.h 含む）
        self.assertEqual(len(saved), EXPECTED_FILE_COUNT)
        for path in saved:
            self.assertTrue(os.path.isfile(path))
            self.assertEqual(
                os.path.dirname(path), self.tmpdir
            )

    def test_by_type_creates_folders(self):
        cfg = CodeGenerationConfig(folder_structure='by_type')
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        gen.save_generated_code(files, self.tmpdir)

        for d in ['include', 'src', 'common']:
            self.assertTrue(
                os.path.isdir(
                    os.path.join(self.tmpdir, d)
                ),
                f"missing folder: {d}",
            )

    def test_by_type_include_files(self):
        cfg = CodeGenerationConfig(folder_structure='by_type')
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        gen.save_generated_code(files, self.tmpdir)

        for name in ['statable_types.h',
                     'statable_transitions.h',
                     'statable_role_functions.h']:
            path = os.path.join(self.tmpdir, 'include', name)
            self.assertTrue(os.path.isfile(path),
                            f"missing: {path}")

    def test_by_type_src_files(self):
        cfg = CodeGenerationConfig(folder_structure='by_type')
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        gen.save_generated_code(files, self.tmpdir)

        for name in ['statable_transitions.c',
                     'statable_role_functions.c',
                     'statable_init.c',
                     'statable_event_queue.c',
                     'statable_interrupt.c',
                     'statable_timer.c']:
            path = os.path.join(self.tmpdir, 'src', name)
            self.assertTrue(os.path.isfile(path),
                            f"missing: {path}")

    def test_by_type_common_files(self):
        cfg = CodeGenerationConfig(folder_structure='by_type')
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        gen.save_generated_code(files, self.tmpdir)

        for name in ['osal.h', 'osal.c', 'statable_all.h']:
            path = os.path.join(self.tmpdir, 'common', name)
            self.assertTrue(os.path.isfile(path),
                            f"missing: {path}")

    def test_by_type_total_12_files(self):
        """★ 11 → 12 に変更"""
        cfg = CodeGenerationConfig(folder_structure='by_type')
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        saved = gen.save_generated_code(files, self.tmpdir)

        self.assertEqual(len(saved), EXPECTED_FILE_COUNT)

        count = 0
        for root, _, filenames in os.walk(self.tmpdir):
            count += len(filenames)
        self.assertEqual(count, EXPECTED_FILE_COUNT)

    def test_by_type_content_preserved(self):
        cfg = CodeGenerationConfig(folder_structure='by_type')
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        gen.save_generated_code(files, self.tmpdir)

        with open(os.path.join(
            self.tmpdir, 'include', 'statable_types.h'
        ), 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content,
                         files['statable_types.h'])


# ============================================================
# 3. save_generated_code_with_merge のテスト
# ============================================================
class TestSaveWithMerge(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.sm, self.gd = make_sample()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_merge_by_type(self):
        """★ 11 → 12 に変更"""
        cfg = CodeGenerationConfig(
            folder_structure='by_type',
            save_with_merge=True,
        )
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        saved = gen.save_generated_code_with_merge(
            files, self.tmpdir
        )

        self.assertEqual(len(saved), EXPECTED_FILE_COUNT)
        for path in saved:
            self.assertTrue(os.path.isfile(path))

    def test_merge_preserves_user_code_by_type(self):
        """by_type でもユーザーコードが保持される"""
        cfg = CodeGenerationConfig(folder_structure='by_type')
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)

        gen.save_generated_code_with_merge(files, self.tmpdir)

        types_path = os.path.join(
            self.tmpdir, 'include', 'statable_types.h'
        )
        with open(types_path, 'r', encoding='utf-8') as f:
            content = f.read()

        content = content.replace(
            '#include <stdint.h>',
            '#include <stdint.h>\n'
            '/* [[STABLE_USER_CODE_START]] */\n'
            '#define USER_DEFINE 42\n'
            '/* [[STABLE_USER_CODE_END]] */',
        )
        with open(types_path, 'w', encoding='utf-8') as f:
            f.write(content)

        files2 = gen.generate_all(self.sm, self.gd)
        gen.save_generated_code_with_merge(files2, self.tmpdir)

        with open(types_path, 'r', encoding='utf-8') as f:
            result = f.read()
        self.assertIn('#define USER_DEFINE 42', result)


# ============================================================
# 4. 統合テスト
# ============================================================
class TestIntegrationWithExisting(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.sm, self.gd = make_sample()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_generate_all_still_works(self):
        """generate_all が 12ファイル生成する"""
        gen = CCodeGenerator()
        files = gen.generate_all(self.sm, self.gd)
        # ★ 11 → 12 に変更
        self.assertEqual(len(files), EXPECTED_FILE_COUNT)

    def test_backward_compatible_flat(self):
        """デフォルト config + flat 相当の動作互換"""
        cfg = CodeGenerationConfig(folder_structure='flat')
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        saved = gen.save_generated_code(files, self.tmpdir)

        # ★ 11 → 12 に変更
        top_level = os.listdir(self.tmpdir)
        self.assertEqual(len(top_level), EXPECTED_FILE_COUNT)


# ============================================================
# 実行
# ============================================================
def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [
        TestResolveOutputPath,
        TestSaveGeneratedCode,
        TestSaveWithMerge,
        TestIntegrationWithExisting,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite).wasSuccessful()


if __name__ == '__main__':
    sys.exit(0 if run_tests() else 1)