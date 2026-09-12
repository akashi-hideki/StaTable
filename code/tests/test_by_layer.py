# tests/test_by_layer.py
"""
by_layer フォルダ構成の単体テスト（(c) 段階）
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

from statable.state_machine import StateMachine
from statable.model import State, Event, Transition

from sample_data import SampleDataGenerator
from c_code_generator import CCodeGenerator
from config import CodeGenerationConfig


# ============================================================
# 定数
# ============================================================
PROJECT_NAME = "MultiLayerTest"
RUN_C_FILE = f"{PROJECT_NAME}_run.c"
LAYER_SPECIFIC_COUNT = 5   # types.h/transitions.h/c, role.h/c
COMMON_COUNT = 7           # init, event_queue, interrupt, timer, osal.h, osal.c, statable_all.h
LAYER_COUNT = 3            # Driver / Middleware / Application
TOTAL_FILE_COUNT = (LAYER_SPECIFIC_COUNT * LAYER_COUNT) + COMMON_COUNT + 1


def make_sm(layer_name, priority=5):
    sm = StateMachine()
    sm.add_state(State(name="Idle"))
    sm.add_state(State(name="Active"))
    sm.add_event(Event(name="START"))
    sm.add_transition(Transition(
        source="Idle", event="START", target="Active",
    ))
    sm.set_initial("Idle")
    sm.layer_name = layer_name
    sm.layer_priority = priority
    return sm


def make_layers():
    d = make_sm("Driver",      priority=1)
    m = make_sm("Middleware",  priority=3)
    a = make_sm("Application", priority=5)
    return [("Driver", d), ("Middleware", m), ("Application", a)]


def make_gd():
    _, gd = SampleDataGenerator().get_sample_data()
    return gd


def make_config(**kwargs):
    """テスト用 config（project_name を明示）"""
    return CodeGenerationConfig(
        folder_structure='by_layer',
        project_name=PROJECT_NAME,
        **kwargs
    )


# ============================================================
# 1. _resolve_output_path（by_layer）
# ============================================================
class TestResolvePathByLayer(unittest.TestCase):

    def setUp(self):
        cfg = make_config()
        self.gen = CCodeGenerator(config=cfg)

    def test_layer_specific_with_layer(self):
        """層固有ファイルは層フォルダ"""
        for name in ['statable_types.h',
                     'statable_transitions.h',
                     'statable_transitions.c',
                     'statable_role_functions.h',
                     'statable_role_functions.c']:
            self.assertEqual(
                self.gen._resolve_output_path(name, "Driver"),
                os.path.join("Driver", name),
            )

    def test_common_file_no_layer(self):
        """共通ファイルはルート直下"""
        for name in ['statable_init.c',
                     'osal.h',
                     'osal.c']:
            self.assertEqual(
                self.gen._resolve_output_path(name, "Driver"),
                name,
            )

    def test_empty_layer_falls_back(self):
        """層名なし → flat"""
        self.assertEqual(
            self.gen._resolve_output_path('statable_types.h', ''),
            'statable_types.h',
        )

    def test_path_passthrough(self):
        """'layer/file' 形式はそのまま"""
        self.assertEqual(
            self.gen._resolve_output_path(
                'Driver/statable_types.h'
            ),
            'Driver/statable_types.h',
        )


# ============================================================
# 2. generate_all_layers（by_layer）
# ============================================================
class TestGenerateAllLayersByLayer(unittest.TestCase):

    def setUp(self):
        self.gd = make_gd()
        self.layers = make_layers()
        cfg = make_config()
        self.gen = CCodeGenerator(config=cfg)

    def test_layer_specific_keys(self):
        """層固有ファイルのキーが 'layer/file'"""
        result = self.gen.generate_all_layers(
            self.layers, self.gd
        )

        for layer in ['Driver', 'Middleware', 'Application']:
            self.assertIn(
                f'{layer}/statable_types.h', result
            )
            self.assertIn(
                f'{layer}/statable_transitions.c', result
            )
            self.assertIn(
                f'{layer}/statable_role_functions.c', result
            )

    def test_common_keys(self):
        """共通ファイルはルート直下"""
        result = self.gen.generate_all_layers(
            self.layers, self.gd
        )
        self.assertIn('statable_init.c', result)
        self.assertIn('osal.h', result)
        self.assertIn('osal.c', result)
        self.assertIn('statable_all.h', result)
        # ★ project_name 明示により正しいファイル名
        self.assertIn(RUN_C_FILE, result)

    def test_layer_file_content_layer_specific(self):
        """Driver/statable_types.h に Driver 層のみ"""
        result = self.gen.generate_all_layers(
            self.layers, self.gd
        )
        driver_types = result['Driver/statable_types.h']

        self.assertIn('STATE_Driver_', driver_types)
        self.assertNotIn('STATE_Middleware_', driver_types)
        self.assertNotIn('STATE_Application_', driver_types)

    def test_layer_transitions_content(self):
        result = self.gen.generate_all_layers(
            self.layers, self.gd
        )
        driver_c = result['Driver/statable_transitions.c']

        self.assertIn('StateMachine_Process_Driver', driver_c)
        self.assertNotIn(
            'StateMachine_Process_Middleware', driver_c
        )

    def test_super_include_all_layers(self):
        """statable_all.h に全層の extern"""
        result = self.gen.generate_all_layers(
            self.layers, self.gd
        )
        h = result['statable_all.h']

        self.assertIn('extern STATE_Driver_t g_Driver_state;', h)
        self.assertIn('extern STATE_Middleware_t g_Middleware_state;', h)
        self.assertIn('extern STATE_Application_t g_Application_state;', h)

    def test_super_include_layer_paths(self):
        """statable_all.h のインクルードパスが層フォルダ付き"""
        result = self.gen.generate_all_layers(
            self.layers, self.gd
        )
        h = result['statable_all.h']

        self.assertIn('#include "Driver/statable_types.h"', h)
        self.assertIn('#include "Driver/statable_transitions.h"', h)
        self.assertIn('#include "Middleware/statable_types.h"', h)

    def test_run_c_priority_order(self):
        """スーパーループは優先度順"""
        result = self.gen.generate_all_layers(
            self.layers, self.gd
        )
        run_c = result[RUN_C_FILE]

        pos_d = run_c.index('StateMachine_Process_Driver')
        pos_m = run_c.index('StateMachine_Process_Middleware')
        pos_a = run_c.index('StateMachine_Process_Application')
        self.assertLess(pos_d, pos_m)
        self.assertLess(pos_m, pos_a)


# ============================================================
# 3. save_generated_code（by_layer）
# ============================================================
class TestSaveByLayer(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.gd = make_gd()
        self.layers = make_layers()
        cfg = make_config()
        self.gen = CCodeGenerator(config=cfg)
        self.files = self.gen.generate_all_layers(
            self.layers, self.gd
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_layer_folders_created(self):
        self.gen.save_generated_code(self.files, self.tmpdir)

        for layer in ['Driver', 'Middleware', 'Application']:
            path = os.path.join(self.tmpdir, layer)
            self.assertTrue(
                os.path.isdir(path),
                f"missing folder: {path}"
            )

    def test_layer_files_present(self):
        self.gen.save_generated_code(self.files, self.tmpdir)

        for layer in ['Driver', 'Middleware', 'Application']:
            for name in ['statable_types.h',
                         'statable_transitions.c',
                         'statable_role_functions.c']:
                path = os.path.join(
                    self.tmpdir, layer, name
                )
                self.assertTrue(
                    os.path.isfile(path),
                    f"missing: {path}"
                )

    def test_common_files_at_root(self):
        self.gen.save_generated_code(self.files, self.tmpdir)

        for name in ['statable_init.c',
                     'statable_event_queue.c',
                     'statable_interrupt.c',
                     'statable_timer.c',
                     'osal.h',
                     'osal.c',
                     'statable_all.h',
                     RUN_C_FILE]:
            path = os.path.join(self.tmpdir, name)
            self.assertTrue(
                os.path.isfile(path),
                f"missing: {path}"
            )

    def test_total_file_count(self):
        """層固有 5 × 3層 + 共通 7 + スーパーループ 1 = 23"""
        self.gen.save_generated_code(self.files, self.tmpdir)

        count = 0
        for root, _, filenames in os.walk(self.tmpdir):
            count += len(filenames)
        self.assertEqual(count, TOTAL_FILE_COUNT)


# ============================================================
# 4. マージ対応
# ============================================================
class TestMergeByLayer(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.gd = make_gd()
        self.layers = make_layers()
        cfg = make_config()
        self.gen = CCodeGenerator(config=cfg)
        self.files = self.gen.generate_all_layers(
            self.layers, self.gd
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_merge_saves_layer_files(self):
        saved = self.gen.save_generated_code_with_merge(
            self.files, self.tmpdir
        )
        self.assertEqual(len(saved), TOTAL_FILE_COUNT)
        for path in saved:
            self.assertTrue(os.path.isfile(path))


# ============================================================
# 5. 空層混在
# ============================================================
class TestMixedEmptyLayer(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.gd = make_gd()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_mixed_empty_and_named(self):
        """空層 + 命名層の混在"""
        cfg = make_config()
        gen = CCodeGenerator(config=cfg)

        d = make_sm("Driver")
        e = make_sm("")  # 層名なし

        files = gen.generate_all_layers(
            [("Driver", d), ("", e)], self.gd
        )

        # Driver 層は層フォルダ
        self.assertIn('Driver/statable_types.h', files)
        # 空層はルート直下
        self.assertIn('statable_types.h', files)


# ============================================================
# 実行
# ============================================================
def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [
        TestResolvePathByLayer,
        TestGenerateAllLayersByLayer,
        TestSaveByLayer,
        TestMergeByLayer,
        TestMixedEmptyLayer,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite).wasSuccessful()


if __name__ == '__main__':
    sys.exit(0 if run_tests() else 1)