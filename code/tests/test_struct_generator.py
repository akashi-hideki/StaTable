# tests/test_struct_generator.py
"""
CStructGenerator（多層ステートマシン対応）の単体テスト

実行方法:
    python code/tests/test_struct_generator.py
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

from codegen.struct_generator import CStructGenerator
from statable.global_defs import (
    GlobalDefinitions, SystemVariable, EventFlag,
    CustomTypeDef, StructMemberDef,
)


def build_test_global_defs():
    """テスト用の GlobalDefinitions"""
    gd = GlobalDefinitions()
    gd.variables = [
        SystemVariable(name="battery_voltage", type="uint16", unit="mV",
                       group="Power", description="バッテリー電圧"),
        SystemVariable(name="system_tick", type="uint32", unit="ms",
                       group="Timer", description="システムタイマ"),
    ]
    gd.flags = [
        EventFlag(name="EVT_START_REQ", min_value=0, max_value=1,
                  group="System", description="起動要求"),
        EventFlag(name="EVT_MODE", min_value=0, max_value=3,
                  group="System", description="モード指示"),
    ]
    gd.custom_types = [
        CustomTypeDef(
            name="SystemStatus",
            description="システム状態管理構造体",
            members=[
                StructMemberDef(name="power_on", data_type="bool",
                                bit_width=1, description="電源ON状態"),
                StructMemberDef(name="error_code", data_type="uint8",
                                description="エラーコード"),
            ],
        ),
    ]
    return gd


class TestStructGeneratorLayer(unittest.TestCase):
    """CStructGenerator の多層対応テスト"""

    def setUp(self):
        self.gen = CStructGenerator()

    # ------------------------------------------------------------------
    # 基本機能
    # ------------------------------------------------------------------
    def test_set_layer(self):
        self.gen.set_layer("Driver")
        self.assertEqual(self.gen.layer_name, "Driver")

    # ------------------------------------------------------------------
    # SystemContext_t（pending_event 追加）
    # ------------------------------------------------------------------
    def test_system_context_has_pending_event(self):
        """SystemContext_t に pending_event / pending_event_valid が含まれる"""
        gd = build_test_global_defs()
        result = self.gen._generate_system_context(gd)

        print("\n=== SystemContext_t ===")
        print(result)

        self.assertIn("typedef struct {", result)
        self.assertIn("SystemData_t data;", result)
        self.assertIn("EventFlags_t flags;", result)
        self.assertIn("uint16_t pending_event;", result)
        self.assertIn("bool pending_event_valid;", result)
        self.assertIn("} SystemContext_t;", result)
        # `}}` になっていないこと
        self.assertNotIn("}}", result)

    # ------------------------------------------------------------------
    # 共通 TransitionContext_t
    # ------------------------------------------------------------------
    def test_common_transition_context(self):
        """共通の基底型 TransitionContext_t が生成される"""
        result = self.gen.generate_common_transition_context()

        print("\n=== Common TransitionContext_t ===")
        print(result)

        self.assertIn("typedef struct {", result)
        self.assertIn("uint16_t from_state;", result)
        self.assertIn("uint16_t event;", result)
        self.assertIn("} TransitionContext_t;", result)
        self.assertNotIn("}}", result)

    # ------------------------------------------------------------------
    # 層ごとの TransitionContext_<Layer>_t
    # ------------------------------------------------------------------
    def test_layer_transition_context(self):
        """層ごとの TransitionContext_<Layer>_t が生成される"""
        self.gen.set_layer("Driver")
        result = self.gen.generate_layer_transition_context(
            state_type="STATE_Driver_t",
            event_type="EVENT_Driver_t",
        )

        print("\n=== Layer TransitionContext (Driver) ===")
        print(result)

        self.assertIn("/* Driver層の遷移コンテキスト */", result)
        self.assertIn("STATE_Driver_t from_state;", result)
        self.assertIn("EVENT_Driver_t event;", result)
        self.assertIn("} TransitionContext_Driver_t;", result)
        self.assertNotIn("}}", result)

    def test_layer_transition_context_no_layer(self):
        """層名未設定時は空文字列"""
        result = self.gen.generate_layer_transition_context(
            state_type="STATE_t",
            event_type="EVENT_t",
        )
        self.assertEqual(result, "")

    # ------------------------------------------------------------------
    # pending_event マクロ
    # ------------------------------------------------------------------
    def test_pending_event_macros(self):
        """FIRE_EVENT / MAX_CONSECUTIVE_PENDING_EVENTS マクロが生成される"""
        result = self.gen.generate_pending_event_macros()

        print("\n=== Pending Event Macros ===")
        print(result)

        # FIRE_EVENT マクロ
        self.assertIn("#define FIRE_EVENT(ctx, evt)", result)
        self.assertIn("(ctx)->pending_event = (uint16_t)(evt);", result)
        self.assertIn("(ctx)->pending_event_valid = true;", result)
        self.assertIn("} while(0)", result)

        # MAX_CONSECUTIVE_PENDING_EVENTS マクロ
        self.assertIn("#ifndef MAX_CONSECUTIVE_PENDING_EVENTS", result)
        self.assertIn("#define MAX_CONSECUTIVE_PENDING_EVENTS 16", result)
        self.assertIn("#endif", result)

    # ------------------------------------------------------------------
    # 既存機能
    # ------------------------------------------------------------------
    def test_system_data_struct(self):
        """SystemData_t が生成される（既存機能）"""
        gd = build_test_global_defs()
        result = self.gen._generate_system_data(gd)

        print("\n=== SystemData_t ===")
        print(result)

        self.assertIn("uint16_t battery_voltage;", result)
        self.assertIn("uint32_t system_tick;", result)
        self.assertIn("} SystemData_t;", result)

    def test_event_flags_struct(self):
        """EventFlags_t が生成される（既存機能）"""
        gd = build_test_global_defs()
        result = self.gen._generate_event_flags(gd)

        print("\n=== EventFlags_t ===")
        print(result)

        self.assertIn("uint8_t EVT_START_REQ;", result)
        self.assertIn("uint8_t EVT_MODE;", result)
        self.assertIn("} EventFlags_t;", result)

    def test_custom_type_struct(self):
        """ユーザー定義型が生成される（既存機能）"""
        gd = build_test_global_defs()
        ct = gd.custom_types[0]
        result = self.gen._generate_custom_type(ct)

        print("\n=== Custom Type ===")
        print(result)

        self.assertIn("bool power_on : 1;", result)
        self.assertIn("uint8_t error_code;", result)
        self.assertIn("} SystemStatus_t;", result)

    # ------------------------------------------------------------------
    # 一括生成
    # ------------------------------------------------------------------
    def test_generate_all(self):
        """全生成物を辞書で返す"""
        gd = build_test_global_defs()
        result = self.gen.generate_all(gd)

        print("\n=== generate_all summary ===")
        for key, val in result.items():
            print(f"  {key}: {len(val)} chars")

        # 必須キー
        self.assertIn('custom_types', result)
        self.assertIn('system_data', result)
        self.assertIn('event_flags', result)
        self.assertIn('system_context', result)
        self.assertIn('common_transition_context', result)
        self.assertIn('pending_event_macros', result)

        # 二重波括弧がないこと
        for key, val in result.items():
            self.assertNotIn("}}", val, f"'{key}' contains '}}'")


def main():
    print("=" * 70)
    print("  CStructGenerator 単体テスト（多層ステートマシン対応）")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestStructGeneratorLayer)
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