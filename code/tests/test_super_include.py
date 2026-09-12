# tests/test_super_include.py
"""
スーパーインクルード statable_all.h の単体テスト
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
# 1. 生成有無の確認
# ============================================================
class TestGenerationToggle(unittest.TestCase):

    def setUp(self):
        self.sm, self.gd = make_sample()

    def test_generate_super_include_true(self):
        cfg = CodeGenerationConfig(generate_super_include=True)
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        self.assertIn('statable_all.h', files)
        self.assertEqual(len(files), 12)

    def test_generate_super_include_false(self):
        cfg = CodeGenerationConfig(generate_super_include=False)
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        self.assertNotIn('statable_all.h', files)
        self.assertEqual(len(files), 11)


# ============================================================
# 2. 生成内容の確認
# ============================================================
class TestContent(unittest.TestCase):

    def setUp(self):
        self.sm, self.gd = make_sample()
        cfg = CodeGenerationConfig(generate_super_include=True)
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        self.code = files['statable_all.h']

    def test_guard(self):
        self.assertIn('#ifndef STATABLE_ALL_H', self.code)
        self.assertIn('#define STATABLE_ALL_H', self.code)
        self.assertIn('#endif /* STATABLE_ALL_H */', self.code)

    def test_file_comment(self):
        self.assertIn('@file', self.code)
        self.assertIn('statable_all.h', self.code)
        self.assertIn('一括インクルード', self.code)

    def test_common_section(self):
        self.assertIn('共通ヘッダ', self.code)
        self.assertIn('#include "statable_types.h"', self.code)

    def test_layer_section(self):
        self.assertIn('層ごとのヘッダ', self.code)
        self.assertIn('#include "statable_transitions.h"', self.code)
        self.assertIn('#include "statable_role_functions.h"', self.code)

    def test_project_section(self):
        self.assertIn('プロジェクトヘッダ', self.code)
        self.assertIn('#include "osal.h"', self.code)

    def test_user_markers(self):
        self.assertIn('[[STABLE_USER_INCLUDES_START]]', self.code)
        self.assertIn('[[STABLE_USER_INCLUDES_END]]', self.code)

    def test_no_external_section_when_empty(self):
        self.assertNotIn('外部インクルード', self.code)


# ============================================================
# 3. 外部インクルード
# ============================================================
class TestExternalIncludes(unittest.TestCase):

    def setUp(self):
        self.sm, self.gd = make_sample()

    def test_external_includes_present(self):
        cfg = CodeGenerationConfig(
            generate_super_include=True,
            external_includes=['foo.h', 'bar.h'],
            external_includes_in_super=True,
        )
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        code = files['statable_all.h']

        self.assertIn('外部インクルード', code)
        self.assertIn('#include "foo.h"', code)
        self.assertIn('#include "bar.h"', code)

    def test_external_includes_disabled(self):
        cfg = CodeGenerationConfig(
            generate_super_include=True,
            external_includes=['foo.h'],
            external_includes_in_super=False,
        )
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        code = files['statable_all.h']

        self.assertNotIn('外部インクルード', code)
        self.assertNotIn('#include "foo.h"', code)

    def test_external_includes_full_form(self):
        """'#include <stdio.h>' 形式はそのまま出力"""
        cfg = CodeGenerationConfig(
            generate_super_include=True,
            external_includes=['#include <stdio.h>'],
            external_includes_in_super=True,
        )
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        code = files['statable_all.h']

        self.assertIn('#include <stdio.h>', code)
        # 二重 #include になっていない
        self.assertNotIn('#include "#include', code)


# ============================================================
# 4. フォルダ構成別の配置
# ============================================================
class TestPlacement(unittest.TestCase):

    def setUp(self):
        self.sm, self.gd = make_sample()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_by_type_common(self):
        cfg = CodeGenerationConfig(
            folder_structure='by_type',
            generate_super_include=True,
        )
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        gen.save_generated_code(files, self.tmpdir)

        path = os.path.join(
            self.tmpdir, 'common', 'statable_all.h'
        )
        self.assertTrue(os.path.isfile(path))

    def test_flat_root(self):
        cfg = CodeGenerationConfig(
            folder_structure='flat',
            generate_super_include=True,
        )
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        gen.save_generated_code(files, self.tmpdir)

        path = os.path.join(self.tmpdir, 'statable_all.h')
        self.assertTrue(os.path.isfile(path))

    def test_by_layer_with_layer_name(self):
        cfg = CodeGenerationConfig(
            folder_structure='by_layer',
            generate_super_include=True,
        )
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        gen.save_generated_code(files, self.tmpdir,
                                layer_name='Application')

        path = os.path.join(
            self.tmpdir, 'Application', 'statable_all.h'
        )
        self.assertTrue(os.path.isfile(path))

    def test_by_type_total_12_files(self):
        cfg = CodeGenerationConfig(
            folder_structure='by_type',
            generate_super_include=True,
        )
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        saved = gen.save_generated_code(files, self.tmpdir)

        self.assertEqual(len(saved), 12)

        count = 0
        for root, _, filenames in os.walk(self.tmpdir):
            count += len(filenames)
        self.assertEqual(count, 12)


# ============================================================
# 5. カスタムファイル名・ディレクトリ名
# ============================================================
class TestCustomNames(unittest.TestCase):

    def setUp(self):
        self.sm, self.gd = make_sample()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_custom_filename(self):
        cfg = CodeGenerationConfig(
            folder_structure='by_type',
            generate_super_include=True,
            super_include_file='my_all.h',
        )
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)

        # 生成内容にカスタム名が反映
        code = files['statable_all.h']
        self.assertIn('@file    my_all.h', code)

        # 保存先もカスタム名
        gen.save_generated_code(files, self.tmpdir)
        path = os.path.join(
            self.tmpdir, 'common', 'my_all.h'
        )
        self.assertTrue(os.path.isfile(path))

    def test_custom_dir(self):
        cfg = CodeGenerationConfig(
            folder_structure='by_type',
            generate_super_include=True,
            super_include_dir='shared',
        )
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        gen.save_generated_code(files, self.tmpdir)

        path = os.path.join(
            self.tmpdir, 'shared', 'statable_all.h'
        )
        self.assertTrue(os.path.isfile(path))


# ============================================================
# 6. 統合テスト
# ============================================================
class TestIntegration(unittest.TestCase):

    def setUp(self):
        self.sm, self.gd = make_sample()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_generate_all_default_still_works(self):
        """generate_all の基本動作は変わらない"""
        gen = CCodeGenerator()
        files = gen.generate_all(self.sm, self.gd)
        # デフォルト: generate_super_include=True → 12ファイル
        self.assertEqual(len(files), 12)

    def test_save_with_merge_super_include(self):
        """マージ保存でも statable_all.h が出力される"""
        cfg = CodeGenerationConfig(
            folder_structure='by_type',
            generate_super_include=True,
        )
        gen = CCodeGenerator(config=cfg)
        files = gen.generate_all(self.sm, self.gd)
        saved = gen.save_generated_code_with_merge(
            files, self.tmpdir
        )

        self.assertEqual(len(saved), 12)
        path = os.path.join(
            self.tmpdir, 'common', 'statable_all.h'
        )
        self.assertTrue(os.path.isfile(path))


# ============================================================
# 実行
# ============================================================
def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [
        TestGenerationToggle,
        TestContent,
        TestExternalIncludes,
        TestPlacement,
        TestCustomNames,
        TestIntegration,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite).wasSuccessful()


if __name__ == '__main__':
    sys.exit(0 if run_tests() else 1)