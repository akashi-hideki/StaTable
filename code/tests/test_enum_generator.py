# tests/test_enum_generator.py
"""
CEnumGenerator（多層ステートマシン対応）の単体テスト

実行方法:
    python code/tests/test_enum_generator.py
"""

import sys
import os
import unittest
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'codegen'))
sys.path.insert(0, os.path.join(project_root, 'statable'))

logging.basicConfig(level=logging.INFO)

from codegen.enum_generator import CEnumGenerator
from statable.model import State, Event, StateType, EventKind
from statable.global_defs import EventFlag


def build_test_items():
    """テスト用の状態・イベント・フラグ"""
    states = [
        State(name="Idle", type=StateType.INITIAL, description="初期状態"),
        State(name="Active", description="動作中"),
        State(name="Error", description="エラー状態"),
    ]
    events = [
        Event(name="START", description="起動要求"),
        Event(name="STOP", description="停止要求"),
        Event(name="ERROR", kind=EventKind.SIGNAL, description="エラー通知"),
    ]
    flags = [
        EventFlag(
            name="EVT_START_REQ",
            min_value=0,
            max_value=1,
            description="起動要求フラグ",
        ),
        EventFlag(
            name="EVT_MODE",
            min_value=0,
            max_value=3,
            description="モード指示",
        ),
    ]
    return states, events, flags


class TestEnumGeneratorLayer(unittest.TestCase):
    """CEnumGenerator の多層対応テスト"""

    def setUp(self):
        self.gen = CEnumGenerator()

    # ------------------------------------------------------------------
    # 基本機能
    # ------------------------------------------------------------------
    def test_set_layer(self):
        self.gen.set_layer("Driver")
        self.assertEqual(self.gen.layer_name, "Driver")

    def test_state_value_name_with_layer(self):
        self.gen.set_layer("Driver")
        self.assertEqual(
            self.gen._state_value_name("Idle"),
            "STATE_Driver_Idle"
        )

    def test_state_value_name_without_layer(self):
        self.assertEqual(self.gen._state_value_name("Idle"), "STATE_Idle")

    def test_event_value_name_with_layer(self):
        self.gen.set_layer("Driver")
        self.assertEqual(
            self.gen._event_value_name("START"),
            "EVENT_Driver_START"
        )

    def test_event_value_name_empty(self):
        self.gen.set_layer("Driver")
        self.assertEqual(
            self.gen._event_value_name(""),
            "EVENT_Driver_NONE"
        )

    def test_state_type_name(self):
        self.gen.set_layer("Driver")
        self.assertEqual(self.gen._state_type_name(), "STATE_Driver_t")

    def test_state_type_name_no_layer(self):
        self.assertEqual(self.gen._state_type_name(), "STATE_t")

    # ------------------------------------------------------------------
    # 状態 enum 生成
    # ------------------------------------------------------------------
    def test_generate_state_enum_with_layer(self):
        self.gen.set_layer("Driver")
        states, _, _ = build_test_items()
        result = self.gen.generate_state_enum(states)

        print("\n=== State Enum (Driver) ===")
        print(result)

        # 検証
        self.assertIn("/* Driver層の状態定義 */", result)
        self.assertIn("STATE_Driver_Idle = 0,", result)
        self.assertIn("STATE_Driver_Active = 1,", result)
        self.assertIn("STATE_Driver_Error = 2,", result)
        self.assertIn("STATE_Driver_MAX", result)
        self.assertIn("} STATE_Driver_t;", result)

    def test_generate_state_enum_without_layer(self):
        states, _, _ = build_test_items()
        result = self.gen.generate_state_enum(states)

        print("\n=== State Enum (no layer) ===")
        print(result)

        self.assertIn("/* 状態定義 */", result)
        self.assertIn("STATE_Idle = 0,", result)
        self.assertIn("STATE_MAX", result)
        self.assertIn("} STATE_t;", result)

    def test_state_enum_empty(self):
        result = self.gen.generate_state_enum([])
        self.assertEqual(result, "")

    # ------------------------------------------------------------------
    # イベント enum 生成
    # ------------------------------------------------------------------
    def test_generate_event_enum_with_layer(self):
        self.gen.set_layer("Driver")
        _, events, _ = build_test_items()
        result = self.gen.generate_event_enum(events)

        print("\n=== Event Enum (Driver) ===")
        print(result)

        # 検証
        self.assertIn("/* Driver層のイベント定義 */", result)
        self.assertIn("EVENT_Driver_NONE = 0,", result)  # NONE が先頭
        self.assertIn("EVENT_Driver_START = 1,", result)
        self.assertIn("EVENT_Driver_STOP = 2,", result)
        self.assertIn("EVENT_Driver_ERROR = 3,", result)
        self.assertIn("EVENT_Driver_MAX", result)
        self.assertIn("} EVENT_Driver_t;", result)

    def test_generate_event_enum_without_layer(self):
        _, events, _ = build_test_items()
        result = self.gen.generate_event_enum(events)

        print("\n=== Event Enum (no layer) ===")
        print(result)

        self.assertIn("EVENT_NONE = 0,", result)
        self.assertIn("EVENT_START = 1,", result)
        self.assertIn("EVENT_MAX", result)
        self.assertIn("} EVENT_t;", result)

    # ------------------------------------------------------------------
    # フラグ enum 生成
    # ------------------------------------------------------------------
    def test_generate_flag_enum(self):
        _, _, flags = build_test_items()
        result = self.gen.generate_flag_enum(flags)

        print("\n=== Flag Enum ===")
        print(result)

        # フラグは層名に依存しない
        self.assertIn("/* イベントフラグ定義 */", result)
        self.assertIn("FLAG_EVT_START_REQ = 0,", result)
        self.assertIn("FLAG_EVT_MODE = 1,", result)
        self.assertIn("FLAG_MAX", result)
        self.assertIn("} FLAG_t;", result)

    def test_flag_enum_with_layer_ignored(self):
        """フラグは層名を無視する"""
        self.gen.set_layer("Driver")
        _, _, flags = build_test_items()
        result = self.gen.generate_flag_enum(flags)

        self.assertIn("FLAG_EVT_START_REQ", result)
        self.assertNotIn("FLAG_Driver_", result)

    # ------------------------------------------------------------------
    # 一括生成
    # ------------------------------------------------------------------
    def test_generate_all_enums_with_layer(self):
        self.gen.set_layer("Driver")
        states, events, flags = build_test_items()
        result = self.gen.generate_all_enums(states, events, flags)

        print("\n=== All Enums (Driver) ===")
        print(result)

        # 3つの enum すべて含まれる
        self.assertIn("STATE_Driver_t", result)
        self.assertIn("EVENT_Driver_t", result)
        self.assertIn("FLAG_t", result)

    def test_generate_all_enums_no_flags(self):
        self.gen.set_layer("Driver")
        states, events, _ = build_test_items()
        result = self.gen.generate_all_enums(states, events, flags=None)

        self.assertIn("STATE_Driver_t", result)
        self.assertIn("EVENT_Driver_t", result)
        self.assertNotIn("FLAG_t", result)

    # ------------------------------------------------------------------
    # ビットマスク enum
    # ------------------------------------------------------------------
    def test_generate_bit_mask_enum(self):
        _, _, flags = build_test_items()
        result = self.gen.generate_bit_mask_enum(flags)

        print("\n=== Bit Mask Enum ===")
        print(result)

        self.assertIn("FLAG_MASK_EVT_START_REQ = 0x01,", result)
        self.assertIn("FLAG_MASK_EVT_MODE = 0x02,", result)
        self.assertIn("} FLAG_MASK_t;", result)

    # ------------------------------------------------------------------
    # 統合テスト: 複数層
    # ------------------------------------------------------------------
    def test_multiple_layers(self):
        """複数の層で同じ状態名が衝突しない"""
        states, events, _ = build_test_items()

        gen_driver = CEnumGenerator()
        gen_driver.set_layer("Driver")
        driver_result = gen_driver.generate_state_enum(states)

        gen_app = CEnumGenerator()
        gen_app.set_layer("Application")
        app_result = gen_app.generate_state_enum(states)

        # 衝突しないことを確認
        self.assertIn("STATE_Driver_Idle", driver_result)
        self.assertIn("STATE_Application_Idle", app_result)
        self.assertNotIn("STATE_Application_Idle", driver_result)
        self.assertNotIn("STATE_Driver_Idle", app_result)


def main():
    print("=" * 70)
    print("  CEnumGenerator 単体テスト（多層ステートマシン対応）")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestEnumGeneratorLayer)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("=" * 70)
    if result.wasSuccessful():
        print("  ✅ すべてのテストが成功しました")
    else:
        print(f"  ❌ 失敗: {len(result.failures)}, エラー: {len(result.errors)}")
    print("=" * 70)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())