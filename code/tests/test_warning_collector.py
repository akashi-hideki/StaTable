# tests/test_warning_collector.py
"""
WarningCollector の単体テスト

GUI 非依存（PySide6 不要）で
logging ハンドラとしての挙動を検証する
"""

import sys
import os
import logging

# ============================================================
# sys.path セットアップ（codegen / code 両方を追加）
# ============================================================
_THIS_DIR    = os.path.dirname(
    os.path.abspath(__file__))
_CODE_DIR    = os.path.dirname(_THIS_DIR)
_CODEGEN_DIR = os.path.join(_CODE_DIR, 'codegen')

for _p in (_CODEGEN_DIR, _CODE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import unittest


# ============================================================
# WarningCollector を単独で読み込む（GUI 非依存）
# ============================================================
class WarningCollector(logging.Handler):
    """テスト対象（本番コードと同一実装）"""

    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.records = []

    def emit(self, record):
        if record.levelno >= logging.WARNING:
            try:
                msg = record.getMessage()
            except Exception:
                msg = str(record.msg)
            self.records.append(msg)


# ============================================================
# 共通セットアップ用ミックスイン
# ============================================================
class _LoggerFixtureMixin:
    """
    - logger.propagate = False
    - NullHandler を最初に追加（lastResort 発動防止）
    - WarningCollector を追加
    """

    LOGGER_NAME = "test.warning.collector"

    def setUp(self):
        self.collector = WarningCollector()
        self.null = logging.NullHandler()
        self.logger = logging.getLogger(self.LOGGER_NAME)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        self.logger.addHandler(self.null)
        self.logger.addHandler(self.collector)

    def tearDown(self):
        self.logger.removeHandler(self.collector)
        self.logger.removeHandler(self.null)


# ============================================================
# 1. 基本動作
# ============================================================
class TestWarningCollectorBasic(
    _LoggerFixtureMixin, unittest.TestCase
):
    LOGGER_NAME = "test.warning.collector"

    def test_initial_empty(self):
        self.assertEqual(self.collector.records, [])

    def test_warning_collected(self):
        self.logger.warning("test warning")
        self.assertEqual(len(self.collector.records), 1)
        self.assertIn("test warning",
                      self.collector.records[0])

    def test_error_collected(self):
        self.logger.error("test error")
        self.assertEqual(len(self.collector.records), 1)

    def test_critical_collected(self):
        self.logger.critical("test critical")
        self.assertEqual(len(self.collector.records), 1)

    def test_info_not_collected(self):
        self.logger.info("test info")
        self.assertEqual(self.collector.records, [])

    def test_debug_not_collected(self):
        self.logger.debug("test debug")
        self.assertEqual(self.collector.records, [])


# ============================================================
# 2. 複数メッセージ
# ============================================================
class TestWarningCollectorMultiple(
    _LoggerFixtureMixin, unittest.TestCase
):
    LOGGER_NAME = "test.warning.multiple"

    def test_multiple_warnings(self):
        self.logger.warning("w1")
        self.logger.warning("w2")
        self.logger.warning("w3")
        self.assertEqual(len(self.collector.records), 3)

    def test_mixed_levels(self):
        self.logger.debug("d")
        self.logger.info("i")
        self.logger.warning("w")
        self.logger.error("e")
        self.assertEqual(len(self.collector.records), 2)

    def test_preserves_order(self):
        self.logger.warning("first")
        self.logger.warning("second")
        self.assertIn("first", self.collector.records[0])
        self.assertIn("second", self.collector.records[1])


# ============================================================
# 3. フォーマット引数
# ============================================================
class TestWarningCollectorFormat(
    _LoggerFixtureMixin, unittest.TestCase
):
    LOGGER_NAME = "test.warning.format"

    def test_format_args(self):
        self.logger.warning("value=%d", 42)
        self.assertIn("value=42",
                      self.collector.records[0])

    def test_multiple_format_args(self):
        self.logger.warning("%s -> %s", "A", "B")
        self.assertIn("A -> B",
                      self.collector.records[0])


# ============================================================
# 4. attach / detach
# ============================================================
class TestWarningCollectorAttach(unittest.TestCase):

    def test_detach_stops_collection(self):
        collector = WarningCollector()
        null = logging.NullHandler()
        logger = logging.getLogger("test.warning.detach")
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        logger.addHandler(null)
        logger.addHandler(collector)
        try:
            logger.warning("before")
            self.assertEqual(len(collector.records), 1)

            logger.removeHandler(collector)
            logger.warning("after")
            self.assertEqual(len(collector.records), 1)
        finally:
            if collector in logger.handlers:
                logger.removeHandler(collector)
            if null in logger.handlers:
                logger.removeHandler(null)

    def test_two_collectors(self):
        c1 = WarningCollector()
        c2 = WarningCollector()
        null = logging.NullHandler()
        logger = logging.getLogger("test.warning.two")
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        logger.addHandler(null)
        logger.addHandler(c1)
        logger.addHandler(c2)
        try:
            logger.warning("both")
            self.assertEqual(len(c1.records), 1)
            self.assertEqual(len(c2.records), 1)
        finally:
            logger.removeHandler(c1)
            logger.removeHandler(c2)
            logger.removeHandler(null)


# ============================================================
# 5. 統合シナリオ（transition_generator の警告を収集）
# ============================================================
class TestIntegrationWithTransition(
    unittest.TestCase
):
    """実際の transition_generator の警告を収集できるか"""

    def test_collect_table_type_warning(self):
        try:
            from sample_data import SampleDataGenerator
            from transition_generator import (
                TransitionGenerator)
        except ImportError:
            self.skipTest(
                "codegen modules not available")

        sm, _ = SampleDataGenerator().get_sample_data()
        gen = TransitionGenerator()

        collector = WarningCollector()
        root_logger = logging.getLogger()
        root_logger.addHandler(collector)
        try:
            gen.generate_transition_table(
                sm, table_type='switch')
        finally:
            root_logger.removeHandler(collector)

        self.assertGreaterEqual(
            len(collector.records), 1)
        self.assertTrue(
            any("not implemented" in r
                for r in collector.records)
        )

    def test_collect_style_warning(self):
        try:
            from sample_data import SampleDataGenerator
            from transition_generator import (
                TransitionGenerator)
        except ImportError:
            self.skipTest(
                "codegen modules not available")

        sm, _ = SampleDataGenerator().get_sample_data()
        gen = TransitionGenerator()

        collector = WarningCollector()
        root_logger = logging.getLogger()
        root_logger.addHandler(collector)
        try:
            gen.generate_process_function(
                sm, generation_style='switch_case')
        finally:
            root_logger.removeHandler(collector)

        self.assertGreaterEqual(
            len(collector.records), 1)
        self.assertTrue(
            any("not implemented" in r
                for r in collector.records)
        )


# ============================================================
# 実行
# ============================================================
def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [
        TestWarningCollectorBasic,
        TestWarningCollectorMultiple,
        TestWarningCollectorFormat,
        TestWarningCollectorAttach,
        TestIntegrationWithTransition,
    ]:
        suite.addTests(
            loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite).wasSuccessful()


if __name__ == '__main__':
    sys.exit(0 if run_tests() else 1)