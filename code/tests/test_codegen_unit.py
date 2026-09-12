# tests/test_codegen_unit.py
"""
codegen モジュールの単体テスト

対象:
  - code_templates.CodeTemplates （多層対応テンプレート）
  - role_function_generator.RoleFunctionGenerator （新シグネチャ）
  - codegen.config.CodeGenerationConfig / ConfigManager

実行方法:
    python code/tests/test_codegen_unit.py
"""

import sys
import os
import unittest
import logging

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
codegen_dir = os.path.join(project_root, 'codegen')
statable_dir = os.path.join(project_root, 'statable')
sys.path.insert(0, project_root)
sys.path.insert(0, codegen_dir)
sys.path.insert(0, statable_dir)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# テスト対象のインポート
from codegen.code_templates import CodeTemplates
from codegen.role_function_generator import RoleFunctionGenerator
from codegen.config import CodeGenerationConfig, ConfigManager
from codegen.naming_convention import CNamingConvention

# statable.model からのインポート（RoleFunction 生成に使用）
try:
    from statable.model import RoleFunction
except ImportError:
    # ダミー RoleFunction を作成
    class RoleFunction:
        def __init__(self, name="", title="", description="",
                     return_type="int", arg1_type="", arg1_name="",
                     arg2_type="", arg2_name=""):
            self.name = name
            self.title = title or f"ロール関数: {name}"
            self.description = description
            self.return_type = return_type
            self.arg1_type = arg1_type
            self.arg1_name = arg1_name
            self.arg2_type = arg2_type
            self.arg2_name = arg2_name


# ======================================================================
# Test 1: CodeTemplates の新テンプレート
# ======================================================================
class TestCodeTemplatesLayerSupport(unittest.TestCase):
    """CodeTemplates の多層対応テンプレートのテスト"""

    def setUp(self):
        self.templates = CodeTemplates()

    def test_layer_templates_exist(self):
        """多層対応テンプレートが存在するか"""
        self.assertTrue(hasattr(self.templates, 'LAYER_TEMPLATES'))
        self.assertIsInstance(self.templates.LAYER_TEMPLATES, dict)
        print(f"  LAYER_TEMPLATES keys: {list(self.templates.LAYER_TEMPLATES.keys())}")

    def test_common_types_templates_exist(self):
        """共通型テンプレートが存在するか"""
        self.assertTrue(hasattr(self.templates, 'COMMON_TYPES_TEMPLATES'))
        ct = self.templates.COMMON_TYPES_TEMPLATES
        self.assertIn('system_context', ct)
        self.assertIn('fire_event_macro', ct)
        self.assertIn('max_consecutive_pending_events', ct)

        # SystemContext に pending_event が含まれるか
        self.assertIn('pending_event', ct['system_context'])
        self.assertIn('pending_event_valid', ct['system_context'])

        # FIRE_EVENT マクロが含まれるか
        self.assertIn('FIRE_EVENT', ct['fire_event_macro'])

        # MAX_CONSECUTIVE_PENDING_EVENTS が含まれるか
        self.assertIn('MAX_CONSECUTIVE_PENDING_EVENTS',
                      ct['max_consecutive_pending_events'])
        print("  COMMON_TYPES_TEMPLATES: OK")

    def test_transition_cell_templates_exist(self):
        """セル単位遷移関数テンプレートが存在するか"""
        self.assertTrue(hasattr(self.templates, 'TRANSITION_CELL_TEMPLATES'))
        tct = self.templates.TRANSITION_CELL_TEMPLATES
        self.assertIn('cell_func_signature', tct)
        self.assertIn('pre_actions', tct)
        self.assertIn('else_block', tct)
        print(f"  TRANSITION_CELL_TEMPLATES keys: {list(tct.keys())}")

    def test_transition_table_templates_exist(self):
        """遷移テーブルテンプレートが存在するか"""
        self.assertTrue(hasattr(self.templates, 'TRANSITION_TABLE_TEMPLATES'))
        ttt = self.templates.TRANSITION_TABLE_TEMPLATES
        self.assertIn('table_typedef', ttt)
        self.assertIn('table_start', ttt)
        self.assertIn('table_entry', ttt)
        self.assertIn('table_end', ttt)
        print(f"  TRANSITION_TABLE_TEMPLATES keys: {list(ttt.keys())}")

    def test_process_func_templates_exist(self):
        """状態遷移関数テンプレートが存在するか"""
        self.assertTrue(hasattr(self.templates, 'PROCESS_FUNC_TEMPLATES'))
        pft = self.templates.PROCESS_FUNC_TEMPLATES
        self.assertIn('func_signature', pft)
        self.assertIn('func_args', pft)
        self.assertIn('func_open', pft)
        print("  PROCESS_FUNC_TEMPLATES: OK")

    def test_get_next_event_templates_exist(self):
        """GetNextEvent テンプレートが存在するか"""
        self.assertTrue(hasattr(self.templates, 'GET_NEXT_EVENT_TEMPLATES'))
        gnt = self.templates.GET_NEXT_EVENT_TEMPLATES
        self.assertIn('func_signature', gnt)
        self.assertIn('pending_check', gnt)
        self.assertIn('MAX_CONSECUTIVE_PENDING_EVENTS', gnt['pending_check'])
        print("  GET_NEXT_EVENT_TEMPLATES: OK")

    def test_role_func_templates_exist(self):
        """ロール関数テンプレートが存在するか"""
        self.assertTrue(hasattr(self.templates, 'ROLE_FUNC_TEMPLATES'))
        rft = self.templates.ROLE_FUNC_TEMPLATES
        self.assertIn('decl_signature', rft)
        self.assertIn('decl_args', rft)
        self.assertIn('TransitionContext_', rft['decl_args'])
        self.assertIn('SystemContext_t *ctx', rft['decl_args'])
        print("  ROLE_FUNC_TEMPLATES: OK")

    def test_super_include_templates_exist(self):
        """スーパーインクルードテンプレートが存在するか"""
        self.assertTrue(hasattr(self.templates, 'SUPER_INCLUDE_TEMPLATES'))
        sit = self.templates.SUPER_INCLUDE_TEMPLATES
        self.assertIn('file_comment', sit)
        self.assertIn('user_marker_start', sit)
        self.assertIn('user_marker_end', sit)
        print("  SUPER_INCLUDE_TEMPLATES: OK")

    def test_super_loop_templates_exist(self):
        """スーパーループテンプレートが存在するか"""
        self.assertTrue(hasattr(self.templates, 'SUPER_LOOP_TEMPLATES'))
        slt = self.templates.SUPER_LOOP_TEMPLATES
        self.assertIn('init_func_signature', slt)
        self.assertIn('run_layer_block', slt)
        self.assertIn('static_context', slt)
        print("  SUPER_LOOP_TEMPLATES: OK")

    def test_type_names_have_layer_prefixes(self):
        """TYPE_NAMES に層プレフィックスが定義されているか"""
        tn = self.templates.TYPE_NAMES
        self.assertIn('layer_state_prefix', tn)
        self.assertIn('layer_event_prefix', tn)
        self.assertIn('layer_transition_context_prefix', tn)
        self.assertIn('layer_process_prefix', tn)
        self.assertEqual(tn['layer_state_prefix'], 'STATE_')
        self.assertEqual(tn['layer_event_prefix'], 'EVENT_')
        print("  TYPE_NAMES layer prefixes: OK")

    def test_format_template(self):
        """FORMMATS テンプレートの動作確認"""
        result = self.templates.FORMATS['enum_value_with_comment'].format(
            name='STATE_Idle', value=0, comment='初期状態'
        )
        self.assertIn('STATE_Idle', result)
        self.assertIn('初期状態', result)
        print(f"  enum_value_with_comment: '{result}'")


# ======================================================================
# Test 2: RoleFunctionGenerator の新シグネチャ
# ======================================================================
class TestRoleFunctionGeneratorLayer(unittest.TestCase):
    """RoleFunctionGenerator の層対応テスト"""

    def setUp(self):
        self.gen = RoleFunctionGenerator()

    def test_default_layer_name(self):
        """層名未設定時は空文字列"""
        self.assertEqual(self.gen.layer_name, "")
        print(f"  default layer_name: '{self.gen.layer_name}'")

    def test_set_layer(self):
        """set_layer で層名を設定できるか"""
        self.gen.set_layer("Driver")
        self.assertEqual(self.gen.layer_name, "Driver")
        print(f"  set_layer('Driver') -> layer_name='{self.gen.layer_name}'")

    def test_function_name_with_layer(self):
        """層名付きの関数名生成"""
        self.gen.set_layer("Driver")
        func = RoleFunction(name="CheckSensor", title="センサチェック")
        name = self.gen._generate_function_name(func)
        self.assertEqual(name, "RoleFunc_Driver_CheckSensor")
        print(f"  function name: {name}")

    def test_function_name_without_layer(self):
        """層名なしの関数名生成（後方互換）"""
        func = RoleFunction(name="CheckSensor", title="センサチェック")
        name = self.gen._generate_function_name(func)
        self.assertEqual(name, "RoleFunc_CheckSensor")
        print(f"  function name (no layer): {name}")

    def test_declaration_signature_with_layer(self):
        """層名付き宣言のシグネチャ確認"""
        self.gen.set_layer("Driver")
        func = RoleFunction(name="CheckSensor", title="センサチェック")
        decl = self.gen.generate_declaration(func)

        # 期待される要素
        self.assertIn("int RoleFunc_Driver_CheckSensor(", decl)
        self.assertIn("const TransitionContext_Driver_t *transition", decl)
        self.assertIn("SystemContext_t *ctx", decl)
        self.assertIn(");", decl)
        print(f"  --- declaration ---")
        print(decl)
        print("  -------------------")

    def test_declaration_signature_without_layer(self):
        """層名なし宣言のシグネチャ確認（後方互換）"""
        func = RoleFunction(name="CheckSensor", title="センサチェック")
        decl = self.gen.generate_declaration(func)

        self.assertIn("int RoleFunc_CheckSensor(", decl)
        self.assertIn("const TransitionContext_t *transition", decl)
        self.assertIn("SystemContext_t *ctx", decl)
        print(f"  --- declaration (no layer) ---")
        print(decl)

    def test_implementation_body(self):
        """実装の内容確認"""
        self.gen.set_layer("Middle")
        func = RoleFunction(name="ProcessData", title="データ処理")
        impl = self.gen.generate_implementation(func)

        # 期待される要素
        self.assertIn("int RoleFunc_Middle_ProcessData(", impl)
        self.assertIn("const TransitionContext_Middle_t *transition", impl)
        self.assertIn("SystemContext_t *ctx", impl)
        self.assertIn("(void)transition;", impl)
        self.assertIn("(void)ctx;", impl)
        self.assertIn("return 0;", impl)
        self.assertIn("STABLE_USER_CODE_START:ProcessData", impl)
        self.assertIn("STABLE_USER_CODE_END:ProcessData", impl)
        print(f"  --- implementation ---")
        print(impl)
        print("  ----------------------")

    def test_generate_call(self):
        """呼び出し文の生成"""
        self.gen.set_layer("Driver")
        call = self.gen.generate_call("CheckSensor")
        self.assertEqual(call, "RoleFunc_Driver_CheckSensor(transition, ctx)")
        print(f"  call: {call}")

    def test_generate_call_with_full_name(self):
        """完全名を渡した場合"""
        self.gen.set_layer("Driver")
        call = self.gen.generate_call("RoleFunc_Driver_CheckSensor")
        self.assertEqual(call, "RoleFunc_Driver_CheckSensor(transition, ctx)")
        print(f"  call (full name): {call}")

    def test_generate_all_declarations(self):
        """複数の宣言を一括生成"""
        self.gen.set_layer("Application")
        funcs = [
            RoleFunction(name="StartMotor"),
            RoleFunction(name="StopMotor"),
            RoleFunction(name="ErrorLog"),
        ]
        result = self.gen.generate_all_declarations(funcs)

        self.assertIn("RoleFunc_Application_StartMotor", result)
        self.assertIn("RoleFunc_Application_StopMotor", result)
        self.assertIn("RoleFunc_Application_ErrorLog", result)
        print(f"  generated {len(funcs)} declarations, total {len(result)} chars")

    def test_args_str_with_layer(self):
        """引数文字列の確認"""
        self.gen.set_layer("Driver")
        args = self.gen._generate_args_str()

        self.assertIn("const TransitionContext_Driver_t *transition", args)
        self.assertIn("SystemContext_t *ctx", args)
        print(f"  args:\n{args}")

    def test_args_str_without_layer(self):
        """引数文字列（層なし）"""
        args = self.gen._generate_args_str()

        self.assertIn("const TransitionContext_t *transition", args)
        self.assertIn("SystemContext_t *ctx", args)
        print(f"  args (no layer):\n{args}")


# ======================================================================
# Test 3: CodeGenerationConfig / ConfigManager
# ======================================================================
class TestCodeGenerationConfig(unittest.TestCase):
    """CodeGenerationConfig の新フィールドのテスト"""

    def test_default_values(self):
        """デフォルト値の確認"""
        config = CodeGenerationConfig()

        # 既存フィールド
        self.assertEqual(config.generation_style, "table_driven")
        self.assertEqual(config.table_type, "array")
        self.assertEqual(config.os_type, "non_rtos")

        # ★ 新フィールド
        self.assertEqual(config.project_name, "MyProject")
        self.assertEqual(config.folder_structure, "by_type")
        self.assertEqual(config.include_dir_name, "include")
        self.assertEqual(config.source_dir_name, "src")
        self.assertEqual(config.common_dir_name, "common")
        self.assertEqual(config.project_dir_name, "project")
        self.assertEqual(config.super_include_file, "statable_all.h")
        self.assertTrue(config.generate_super_include)
        self.assertEqual(config.external_includes, [])
        self.assertTrue(config.external_includes_in_super)
        self.assertTrue(config.external_includes_in_role)
        self.assertFalse(config.external_includes_in_transitions)
        self.assertFalse(config.external_includes_in_common)
        self.assertEqual(config.max_consecutive_pending_events, 16)
        print("  default values: OK")

    def test_to_dict_and_from_dict(self):
        """辞書変換と復元"""
        config = CodeGenerationConfig()
        config.project_name = "TestProject"
        config.external_includes = ["hal_data.h", "r_typedefs.h"]

        data = config.to_dict()
        self.assertIn("project_name", data)
        self.assertEqual(data["project_name"], "TestProject")
        self.assertEqual(data["external_includes"], ["hal_data.h", "r_typedefs.h"])

        # 復元
        restored = CodeGenerationConfig.from_dict(data)
        self.assertEqual(restored.project_name, "TestProject")
        self.assertEqual(restored.external_includes, ["hal_data.h", "r_typedefs.h"])
        print("  to_dict/from_dict: OK")

    def test_from_dict_ignores_unknown_keys(self):
        """未知のキーは無視される"""
        data = {
            "project_name": "P",
            "unknown_key": "value",
            "another_unknown": 123,
        }
        config = CodeGenerationConfig.from_dict(data)
        self.assertEqual(config.project_name, "P")
        print("  from_dict ignores unknown keys: OK")

    def test_config_manager(self):
        """ConfigManager の基本動作"""
        mgr = ConfigManager()
        config = mgr.get_config()
        self.assertEqual(config.project_name, "MyProject")

        config.project_name = "Updated"
        mgr.set_config(config)

        config2 = mgr.get_config()
        self.assertEqual(config2.project_name, "Updated")

        mgr.update(project_name="Updated2", table_type="array")
        config3 = mgr.get_config()
        self.assertEqual(config3.project_name, "Updated2")

        mgr.reset()
        config4 = mgr.get_config()
        self.assertEqual(config4.project_name, "MyProject")
        print("  ConfigManager: OK")


# ======================================================================
# Test 4: 統合テスト（層名付きの完全な生成）
# ======================================================================
class TestIntegrationLayerGeneration(unittest.TestCase):
    """層名付きの完全生成フロー"""

    def test_full_flow_driver_layer(self):
        """Driver層のロール関数を一括生成"""
        gen = RoleFunctionGenerator()
        gen.set_layer("Driver")

        funcs = [
            RoleFunction(name="InitSensor", title="センサ初期化"),
            RoleFunction(name="ReadVoltage", title="電圧読み取り"),
        ]

        print("\n  === Driver層の宣言 ===")
        decls = gen.generate_all_declarations(funcs)
        print(decls)

        print("\n  === Driver層の実装 ===")
        impls = gen.generate_all_implementations(funcs)
        print(impls)

        # 検証
        self.assertIn("RoleFunc_Driver_InitSensor", decls)
        self.assertIn("RoleFunc_Driver_ReadVoltage", decls)
        self.assertIn("RoleFunc_Driver_InitSensor", impls)
        self.assertIn("RoleFunc_Driver_ReadVoltage", impls)

    def test_full_flow_application_layer(self):
        """Application層のロール関数を一括生成"""
        gen = RoleFunctionGenerator()
        gen.set_layer("Application")

        funcs = [
            RoleFunction(name="StartMotor", title="モータ起動"),
            RoleFunction(name="StopMotor", title="モータ停止"),
        ]

        print("\n  === Application層の宣言 ===")
        decls = gen.generate_all_declarations(funcs)
        print(decls)

        # 検証
        self.assertIn("int RoleFunc_Application_StartMotor(", decls)
        self.assertIn("const TransitionContext_Application_t *transition", decls)


# ======================================================================
# メイン
# ======================================================================
def main():
    """テストランナー"""
    print("=" * 70)
    print("  codegen 単体テスト")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # テストクラスを登録
    suite.addTests(loader.loadTestsFromTestCase(TestCodeTemplatesLayerSupport))
    suite.addTests(loader.loadTestsFromTestCase(TestRoleFunctionGeneratorLayer))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeGenerationConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationLayerGeneration))

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