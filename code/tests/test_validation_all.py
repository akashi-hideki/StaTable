# tests/test_validation_all.py
"""
検証モジュール統合テスト
メソッド存在確認・機能テスト・GUIテスト・実データテストを1ファイルに統合
直接実行: python tests/test_validation_all.py
"""

import sys
import os
import json
import importlib.util
import logging

# ===== パス設定 =====
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
codegen_dir = os.path.join(project_root, 'codegen')
statable_dir = os.path.join(project_root, 'statable')
gui_dir = os.path.join(project_root, 'statable_gui')

sys.path.insert(0, project_root)
sys.path.insert(0, codegen_dir)
sys.path.insert(0, statable_dir)
sys.path.insert(0, gui_dir)

# ===== ロガー設定（ERRORに抑制） =====
logging.basicConfig(level=logging.ERROR)
for log_name in ['validate', 'validation_dialog']:
    logging.getLogger(log_name).setLevel(logging.ERROR)

# ===== QApplication（GUIテスト用） =====
app = None
PYSIDE_AVAILABLE = False
try:
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    PYSIDE_AVAILABLE = True
except ImportError:
    pass

# ===== 結果カウンタ =====
PASS_COUNT = 0
FAIL_COUNT = 0
FAILED_ITEMS = []


def log_result(name, success, detail=""):
    global PASS_COUNT, FAIL_COUNT
    if success:
        PASS_COUNT += 1
        print(f"  ✅ {name}")
    else:
        FAIL_COUNT += 1
        FAILED_ITEMS.append(name)
        print(f"  ❌ {name} {detail}")


def load_module(name, path):
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"    → ロード失敗: {e}")
        return None


def mock_message_boxes():
    try:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information = lambda *a, **k: QMessageBox.StandardButton.Ok
        QMessageBox.warning = lambda *a, **k: QMessageBox.StandardButton.Ok
        QMessageBox.critical = lambda *a, **k: QMessageBox.StandardButton.Ok
        return True
    except Exception:
        return False


def get_sample_data():
    sample_path = os.path.join(codegen_dir, "sample_data.py")
    module = load_module("all_test_sample", sample_path)
    if module is None:
        return None, None
    return module.SampleDataGenerator().get_sample_data()


# ============================================================
# パート1: メソッド存在確認テスト
# ============================================================
class TestMethods:
    def run(self):
        print("\n" + "=" * 50)
        print("パート1: メソッド存在確認")
        print("=" * 50)
        self._test_files()
        self._test_models()
        self._test_data_dicts()
        self._test_validator()
        self._test_item_validators()
        self._test_prompt_parser()
        self._test_change()
    
    def _test_files(self):
        print("\n--- ファイル存在確認 ---")
        validate_dir = os.path.join(codegen_dir, 'validate')
        data_dir = os.path.join(validate_dir, 'data')
        
        files = [
            (os.path.join(validate_dir, '__init__.py'), "validate/__init__.py"),
            (os.path.join(validate_dir, 'logger.py'), "logger.py"),
            (os.path.join(validate_dir, 'models.py'), "models.py"),
            (os.path.join(validate_dir, 'validator.py'), "validator.py"),
            (os.path.join(validate_dir, 'prompt_generator.py'), "prompt_generator.py"),
            (os.path.join(validate_dir, 'response_parser.py'), "response_parser.py"),
            (os.path.join(validate_dir, 'change_actions.py'), "change_actions.py"),
            (os.path.join(validate_dir, 'change_applier.py'), "change_applier.py"),
            (os.path.join(validate_dir, 'clipboard_manager.py'), "clipboard_manager.py"),
            (os.path.join(data_dir, 'validation_rules.py'), "data/validation_rules.py"),
            (os.path.join(data_dir, 'prompt_templates.py'), "data/prompt_templates.py"),
            (os.path.join(data_dir, 'action_definitions.py'), "data/action_definitions.py"),
            (os.path.join(data_dir, 'keywords.py'), "data/keywords.py"),
        ]
        for path, name in files:
            log_result(name, os.path.exists(path))
    
    def _test_models(self):
        print("\n--- モデルクラス ---")
        models_path = os.path.join(codegen_dir, 'validate', 'models.py')
        module = load_module("test_models", models_path)
        if module is None:
            log_result("models.py", False)
            return
        
        if hasattr(module, 'ValidationSeverity'):
            sev = module.ValidationSeverity
            log_result("ValidationSeverity", all(hasattr(sev, x) for x in ['ERROR', 'WARNING', 'INFO']))
            log_result("ValidationSeverity.from_string", hasattr(sev, 'from_string'))
        
        if hasattr(module, 'ValidationIssue'):
            log_result("ValidationIssue.to_dict", hasattr(module.ValidationIssue, 'to_dict'))
        
        if hasattr(module, 'ValidationResult'):
            log_result("ValidationResult", all(hasattr(module.ValidationResult, m) 
                for m in ['to_dict', 'get_errors', 'get_warnings', 'get_infos']))
        
        if hasattr(module, 'ValidationContext'):
            log_result("ValidationContext", all(hasattr(module.ValidationContext, p) 
                for p in ['states', 'events', 'transitions', 'variables', 'flags']))
    
    def _test_data_dicts(self):
        print("\n--- データ辞書 ---")
        data_dir = os.path.join(codegen_dir, 'validate', 'data')
        
        rules = load_module("test_rules", os.path.join(data_dir, 'validation_rules.py'))
        if rules and hasattr(rules, 'VALIDATION_RULES'):
            log_result("VALIDATION_RULES", True, f"({len(rules.VALIDATION_RULES)}カテゴリ)")
        
        prompt = load_module("test_prompt_data", os.path.join(data_dir, 'prompt_templates.py'))
        if prompt:
            log_result("PROMPT_TEMPLATES", hasattr(prompt, 'PROMPT_TEMPLATES'))
        
        actions = load_module("test_actions_data", os.path.join(data_dir, 'action_definitions.py'))
        if actions:
            log_result("ACTION_DEFINITIONS", hasattr(actions, 'ACTION_DEFINITIONS'))
        
        keywords = load_module("test_keywords_data", os.path.join(data_dir, 'keywords.py'))
        if keywords:
            log_result("MARKERS", hasattr(keywords, 'MARKERS'))
            log_result("PARSE_KEYWORDS", hasattr(keywords, 'PARSE_KEYWORDS'))
    
    def _test_validator(self):
        print("\n--- バリデータ ---")
        validator_path = os.path.join(codegen_dir, 'validate', 'validator.py')
        module = load_module("test_validator_main", validator_path)
        if module is None:
            log_result("validator.py", False)
            return
        
        if hasattr(module, 'CodeGenerationValidator'):
            log_result("VALIDATORS辞書", hasattr(module.CodeGenerationValidator, 'VALIDATORS'))
            log_result("validate", hasattr(module.CodeGenerationValidator, 'validate'))
    
    def _test_item_validators(self):
        print("\n--- 項目別バリデータ ---")
        items_dir = os.path.join(codegen_dir, 'validate', 'items')
        specs = [
            ('state_validator.py', 'StateValidator'),
            ('event_validator.py', 'EventValidator'),
            ('transition_validator.py', 'TransitionValidator'),
            ('role_function_validator.py', 'RoleFunctionValidator'),
            ('variable_validator.py', 'VariableValidator'),
            ('flag_validator.py', 'FlagValidator'),
            ('queue_validator.py', 'QueueValidator'),
            ('interrupt_validator.py', 'InterruptValidator'),
            ('timer_validator.py', 'TimerValidator'),
            ('custom_type_validator.py', 'CustomTypeValidator'),
        ]
        for filename, class_name in specs:
            module = load_module(f"test_{class_name}", os.path.join(items_dir, filename))
            if module and hasattr(module, class_name):
                log_result(f"{class_name}", True)
            else:
                log_result(f"{class_name}", False)
    
    def _test_prompt_parser(self):
        print("\n--- プロンプト生成・回答パーサー ---")
        prompt = load_module("test_prompt_gen", os.path.join(codegen_dir, 'validate', 'prompt_generator.py'))
        if prompt and hasattr(prompt, 'AIPromptGenerator'):
            log_result("AIPromptGenerator", True)
        
        parser = load_module("test_parser", os.path.join(codegen_dir, 'validate', 'response_parser.py'))
        if parser and hasattr(parser, 'AIResponseParser'):
            log_result("AIResponseParser", True)
    
    def _test_change(self):
        print("\n--- 変更アクション・適用 ---")
        actions = load_module("test_change_act", os.path.join(codegen_dir, 'validate', 'change_actions.py'))
        if actions and hasattr(actions, 'ChangeActionType'):
            log_result("ChangeActionType", True)
        
        applier = load_module("test_change_app", os.path.join(codegen_dir, 'validate', 'change_applier.py'))
        if applier and hasattr(applier, 'ChangeApplier'):
            log_result("ChangeApplier", True)


# ============================================================
# パート2: 機能テスト
# ============================================================
class TestFunctions:
    def run(self):
        print("\n" + "=" * 50)
        print("パート2: 機能テスト")
        print("=" * 50)
        self._test_validation()
        self._test_prompt()
        self._test_parser()
        self._test_applier()
        self._test_integration()
    
    def _test_validation(self):
        print("\n--- 検証機能 ---")
        validator_path = os.path.join(codegen_dir, 'validate', 'validator.py')
        module = load_module("func_validator", validator_path)
        if module is None:
            log_result("validator.py", False)
            return
        
        sm, gd = get_sample_data()
        if sm is None:
            log_result("サンプルデータ", False)
            return
        
        validator = module.CodeGenerationValidator()
        result = validator.validate(sm, gd)
        log_result("validate()実行", result is not None)
        log_result("カテゴリ取得", len(validator.get_categories()) >= 5)
    
    def _test_prompt(self):
        print("\n--- プロンプト生成 ---")
        prompt_path = os.path.join(codegen_dir, 'validate', 'prompt_generator.py')
        module = load_module("func_prompt", prompt_path)
        if module is None:
            log_result("prompt_generator.py", False)
            return
        
        sm, gd = get_sample_data()
        generator = module.AIPromptGenerator()
        prompt = generator.generate_diagnosis_prompt(sm, gd)
        log_result("診断プロンプト", len(prompt) > 100)
        log_result("JSON含む", 'JSON' in prompt)
    
    def _test_parser(self):
        print("\n--- 回答パーサー ---")
        parser_path = os.path.join(codegen_dir, 'validate', 'response_parser.py')
        module = load_module("func_parser", parser_path)
        if module is None:
            log_result("response_parser.py", False)
            return
        
        parser = module.AIResponseParser()
        json_response = '''{"changes": [{"action": "set_initial", "params": {"state": "INIT"}, "reason": "初期状態"}]}'''
        changes = parser.parse(json_response)
        log_result("JSON解析", len(changes) == 1, f"({len(changes)}件)")
    
    def _test_applier(self):
        print("\n--- 変更適用 ---")
        applier_path = os.path.join(codegen_dir, 'validate', 'change_applier.py')
        actions_path = os.path.join(codegen_dir, 'validate', 'change_actions.py')
        applier_module = load_module("func_applier", applier_path)
        actions_module = load_module("func_actions", actions_path)
        
        if applier_module is None or actions_module is None:
            log_result("モジュールロード", False)
            return
        
        sm, gd = get_sample_data()
        applier = applier_module.ChangeApplier(sm, gd)
        
        change = actions_module.ChangeRequest(
            action=actions_module.ChangeActionType.SET_INITIAL,
            params={'state': 'INIT'}
        )
        success, msg = applier.apply(change)
        log_result("set_initial適用", success, f"({msg})")
    
    def _test_integration(self):
        print("\n--- 統合フロー ---")
        validator_path = os.path.join(codegen_dir, 'validate', 'validator.py')
        prompt_path = os.path.join(codegen_dir, 'validate', 'prompt_generator.py')
        parser_path = os.path.join(codegen_dir, 'validate', 'response_parser.py')
        applier_path = os.path.join(codegen_dir, 'validate', 'change_applier.py')
        
        val_module = load_module("int_val", validator_path)
        prm_module = load_module("int_prm", prompt_path)
        par_module = load_module("int_par", parser_path)
        apl_module = load_module("int_apl", applier_path)
        
        if None in [val_module, prm_module, par_module, apl_module]:
            log_result("モジュールロード", False)
            return
        
        sm, gd = get_sample_data()
        sm.initial_state = None
        
        validator = val_module.CodeGenerationValidator()
        result = validator.validate(sm, gd)
        log_result("Step1: 検証", result.error_count >= 1)
        
        generator = prm_module.AIPromptGenerator()
        prompt = generator.generate_diagnosis_prompt(sm, gd, result)
        log_result("Step2: プロンプト", len(prompt) > 100)
        
        ai_response = '{"changes": [{"action": "set_initial", "params": {"state": "INIT"}, "reason": "初期状態"}]}'
        parser = par_module.AIResponseParser()
        changes = parser.parse(ai_response)
        log_result("Step3: パース", len(changes) == 1)
        
        applier = apl_module.ChangeApplier(sm, gd)
        apply_result = applier.apply_all(changes)
        log_result("Step4: 適用", apply_result['applied'] == 1)
        log_result("Step5: 反映", sm.initial_state == 'INIT')


# ============================================================
# パート3: 実データテスト
# ============================================================
class TestRealData:
    def run(self):
        print("\n" + "=" * 50)
        print("パート3: 実データテスト")
        print("=" * 50)
        
        from statable.state_machine import StateMachine
        from statable.model import State, Event, Transition, RoleFunction, StateType, EventKind
        from statable.global_defs import GlobalDefinitions, SystemVariable, EventFlag
        
        validator_path = os.path.join(codegen_dir, 'validate', 'validator.py')
        module = load_module("real_validator", validator_path)
        if module is None:
            log_result("validator.py", False)
            return
        validator = module.CodeGenerationValidator()
        
        # 正常データ
        sm = self._create_valid_sm()
        gd = self._create_valid_gd()
        result = validator.validate(sm, gd)
        log_result("正常データ: エラーなし", result.error_count == 0)
        
        # 初期状態なし
        sm2 = self._create_valid_sm()
        sm2.initial_state = None
        result2 = validator.validate(sm2, gd)
        log_result("初期状態なし検出", any(i.code == 'STATE_NO_INITIAL' for i in result2.issues))
        
        # 到達不能状態（直接リストに追加）
        sm3 = self._create_valid_sm()
        sm3.states["ISOLATED"] = State(name="ISOLATED", type=StateType.NORMAL)
        result3 = validator.validate(sm3, gd)
        log_result("到達不能状態検出", any(i.code == 'STATE_UNREACHABLE' for i in result3.issues))
        
        # 未定義遷移先（直接リストに追加）
        sm4 = self._create_valid_sm()
        sm4.transitions.append(Transition(source="IDLE", event="START", target="UNDEFINED"))
        result4 = validator.validate(sm4, gd)
        log_result("未定義遷移先検出", any(i.code == 'TRANSITION_TARGET_UNDEFINED' for i in result4.issues))
        
        # 未定義イベント（直接リストに追加）
        sm5 = self._create_valid_sm()
        sm5.transitions.append(Transition(source="IDLE", event="UNDEFINED_EVENT", target="RUNNING"))
        result5 = validator.validate(sm5, gd)
        log_result("未定義イベント検出", any(i.code == 'TRANSITION_EVENT_UNDEFINED' for i in result5.issues))
        
        # 重複遷移（直接リストに追加）
        sm6 = self._create_valid_sm()
        sm6.transitions.append(Transition(source="INIT", event="POWER_ON", target="IDLE"))
        result6 = validator.validate(sm6, gd)
        log_result("重複遷移検出", any(i.code == 'TRANSITION_DUPLICATE' for i in result6.issues))
        
        # 自己遷移（直接リストに追加）
        sm7 = self._create_valid_sm()
        sm7.transitions.append(Transition(source="IDLE", event="START", target="IDLE"))
        result7 = validator.validate(sm7, gd)
        log_result("自己遷移検出", any(i.code == 'TRANSITION_SELF_LOOP' for i in result7.issues))
        
        # 未使用イベント
        sm8 = self._create_valid_sm()
        sm8.events["UNUSED"] = Event(name="UNUSED", kind=EventKind.SIGNAL)
        result8 = validator.validate(sm8, gd)
        log_result("未使用イベント検出", any(i.code == 'EVENT_UNUSED' for i in result8.issues))
        
        # 重複変数
        gd2 = self._create_valid_gd()
        gd2.variables.append(SystemVariable(name="battery_voltage", type="uint16"))
        result9 = validator.validate(sm, gd2)
        log_result("重複変数検出", any(i.code == 'VAR_DUPLICATE_NAME' for i in result9.issues))
        
        # 重複フラグ
        gd3 = self._create_valid_gd()
        gd3.flags.append(EventFlag(name="EVT_POWER_ON_REQ", min_value=0, max_value=1))
        result10 = validator.validate(sm, gd3)
        log_result("重複フラグ検出", any(i.code == 'FLAG_DUPLICATE_NAME' for i in result10.issues))
    
    def _create_valid_sm(self):
        from statable.state_machine import StateMachine
        from statable.model import State, Event, Transition, RoleFunction, StateType, EventKind
        
        sm = StateMachine()
        sm.add_state(State(name="INIT", type=StateType.INITIAL))
        sm.add_state(State(name="IDLE", type=StateType.NORMAL))
        sm.add_state(State(name="RUNNING", type=StateType.NORMAL))
        sm.add_state(State(name="ERROR", type=StateType.NORMAL))
        sm.set_initial("INIT")
        
        sm.add_event(Event(name="POWER_ON", kind=EventKind.SIGNAL))
        sm.add_event(Event(name="START", kind=EventKind.SIGNAL))
        sm.add_event(Event(name="STOP", kind=EventKind.SIGNAL))
        sm.add_event(Event(name="RESET", kind=EventKind.SIGNAL))
        sm.add_event(Event(name="ERROR_DETECTED", kind=EventKind.SIGNAL))
        
        sm.add_transition(Transition(source="INIT", event="POWER_ON", target="IDLE", action="PowerOn"))
        sm.add_transition(Transition(source="IDLE", event="START", target="RUNNING", action="Start"))
        sm.add_transition(Transition(source="RUNNING", event="STOP", target="IDLE", action="Stop"))
        sm.add_transition(Transition(source="ERROR", event="RESET", target="IDLE", action="ResetError"))
        sm.add_transition(Transition(source="IDLE", event="ERROR_DETECTED", target="ERROR", action="HandleError"))
        
        sm.add_role_function(RoleFunction(name="PowerOn", return_type="void"))
        sm.add_role_function(RoleFunction(name="Start", return_type="void"))
        sm.add_role_function(RoleFunction(name="Stop", return_type="void"))
        sm.add_role_function(RoleFunction(name="ResetError", return_type="void"))
        sm.add_role_function(RoleFunction(name="HandleError", return_type="void"))
        
        return sm
    
    def _create_valid_gd(self):
        from statable.global_defs import GlobalDefinitions, SystemVariable, EventFlag
        
        gd = GlobalDefinitions()
        gd.variables = [
            SystemVariable(name="battery_voltage", type="uint16", group="Power"),
            SystemVariable(name="system_tick", type="uint32", group="Timer"),
        ]
        gd.flags = [
            EventFlag(name="EVT_POWER_ON_REQ", min_value=0, max_value=1),
            EventFlag(name="EVT_START_REQ", min_value=0, max_value=1),
        ]
        return gd


# ============================================================
# パート4: GUIテスト
# ============================================================
class TestGUI:
    def run(self):
        print("\n" + "=" * 50)
        print("パート4: GUIテスト")
        print("=" * 50)
        
        if not PYSIDE_AVAILABLE:
            log_result("PySide6", False, "(利用不可)")
            return
        
        mock_message_boxes()
        
        dialog_path = os.path.join(gui_dir, "validation_dialog.py")
        module = load_module("gui_dialog", dialog_path)
        if module is None:
            log_result("validation_dialog.py", False)
            return
        
        sm, gd = get_sample_data()
        if sm is None:
            log_result("サンプルデータ", False)
            return
        
        dlg = module.ValidationDialog(sm, gd)
        log_result("ダイアログ作成", dlg is not None)
        log_result("タイトル", dlg.windowTitle() == "コード生成前検証・AI診断")
        log_result("タブ数", dlg.tab_widget.count() == 4)
        log_result("検証結果あり", dlg.validation_result is not None)
        log_result("プロンプト生成", len(dlg.prompt_preview.toPlainText()) > 100)
        
        dlg.close()


# ============================================================
# メイン実行
# ============================================================
def run_all_tests():
    global PASS_COUNT, FAIL_COUNT, FAILED_ITEMS
    PASS_COUNT = 0
    FAIL_COUNT = 0
    FAILED_ITEMS = []
    
    print("=" * 60)
    print("検証モジュール 統合テスト")
    print("=" * 60)
    
    TestMethods().run()
    TestFunctions().run()
    TestRealData().run()
    TestGUI().run()
    
    print("\n" + "=" * 60)
    print("テスト結果")
    print("=" * 60)
    print(f"  合格: {PASS_COUNT}")
    print(f"  失敗: {FAIL_COUNT}")
    
    if FAILED_ITEMS:
        print("\n  失敗項目:")
        for item in FAILED_ITEMS:
            print(f"    - {item}")
    
    print("=" * 60)
    
    if FAIL_COUNT == 0:
        print("🎉 全テスト成功！")
        return True
    else:
        print("❌ 失敗したテストがあります")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)