# tests/test_validation_methods.py
"""
検証モジュールのメソッド存在確認テスト
すべてのクラスとメソッド・辞書が正しく実装されているかを確認する
"""

import sys
import os
import importlib.util
import inspect

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
codegen_dir = os.path.join(project_root, 'codegen')
statable_dir = os.path.join(project_root, 'statable')
gui_dir = os.path.join(project_root, 'statable_gui')

sys.path.insert(0, codegen_dir)
sys.path.insert(0, statable_dir)
sys.path.insert(0, gui_dir)
sys.path.insert(0, project_root)


def load_module(name, path):
    """モジュールをファイルパスからロード"""
    if not os.path.exists(path):
        print(f"  ❌ ファイルが存在しません: {path}")
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"  ❌ モジュールロード失敗: {e}")
        return None


def check_class_methods(class_obj, required_methods, class_name):
    """クラスのメソッド存在確認"""
    missing = []
    for method_name in required_methods:
        if not hasattr(class_obj, method_name):
            missing.append(method_name)
        elif not callable(getattr(class_obj, method_name)):
            missing.append(f"{method_name}(callableではない)")
    
    if missing:
        print(f"  ❌ {class_name}: 不足メソッド: {missing}")
        return False
    else:
        print(f"  ✅ {class_name}: 全{len(required_methods)}メソッド存在")
        return True


def check_dict_attributes(obj, required_dicts, obj_name):
    """辞書属性の存在確認"""
    missing = []
    for dict_name in required_dicts:
        if not hasattr(obj, dict_name):
            missing.append(dict_name)
        elif not isinstance(getattr(obj, dict_name), dict):
            missing.append(f"{dict_name}(dictではない)")
    
    if missing:
        print(f"  ❌ {obj_name}: 不足辞書: {missing}")
        return False
    else:
        print(f"  ✅ {obj_name}: 全{len(required_dicts)}辞書存在")
        return True


# ===== モデルテスト =====
def test_models():
    """モデルクラスのテスト"""
    print("\n--- モデルクラス ---")
    
    models_path = os.path.join(codegen_dir, 'validate', 'models.py')
    models_module = load_module("test_models", models_path)
    if models_module is None:
        return False
    
    all_ok = True
    
    # ValidationSeverity
    if hasattr(models_module, 'ValidationSeverity'):
        severity = models_module.ValidationSeverity
        if hasattr(severity, 'ERROR') and hasattr(severity, 'WARNING') and hasattr(severity, 'INFO'):
            print("  ✅ ValidationSeverity: ERROR/WARNING/INFO 存在")
        else:
            print("  ❌ ValidationSeverity: 列挙値不足")
            all_ok = False
        
        if hasattr(severity, 'from_string'):
            print("  ✅ ValidationSeverity.from_string: 存在")
        else:
            print("  ❌ ValidationSeverity.from_string: 不足")
            all_ok = False
    else:
        print("  ❌ ValidationSeverity: クラスが存在しない")
        all_ok = False
    
    # ValidationIssue
    if hasattr(models_module, 'ValidationIssue'):
        issue = models_module.ValidationIssue
        required = ['to_dict', 'from_dict']
        all_ok &= check_class_methods(issue, required, "ValidationIssue")
    else:
        print("  ❌ ValidationIssue: クラスが存在しない")
        all_ok = False
    
    # ValidationResult
    if hasattr(models_module, 'ValidationResult'):
        result = models_module.ValidationResult
        required = ['to_dict', 'from_dict', 'get_errors', 'get_warnings', 'get_infos', 'get_by_category']
        all_ok &= check_class_methods(result, required, "ValidationResult")
    else:
        print("  ❌ ValidationResult: クラスが存在しない")
        all_ok = False
    
    # ValidationContext
    if hasattr(models_module, 'ValidationContext'):
        context = models_module.ValidationContext
        required = ['states', 'events', 'transitions', 'role_functions', 'initial_state',
                   'variables', 'flags', 'event_queues', 'interrupts', 'custom_types']
        # プロパティの確認
        missing_props = []
        for prop in required:
            if not hasattr(context, prop):
                missing_props.append(prop)
        if missing_props:
            print(f"  ❌ ValidationContext: 不足プロパティ: {missing_props}")
            all_ok = False
        else:
            print(f"  ✅ ValidationContext: 全{len(required)}プロパティ存在")
    else:
        print("  ❌ ValidationContext: クラスが存在しない")
        all_ok = False
    
    return all_ok


# ===== データ辞書テスト =====
def test_data_dicts():
    """データ辞書のテスト"""
    print("\n--- データ辞書 ---")
    
    data_dir = os.path.join(codegen_dir, 'validate', 'data')
    all_ok = True
    
    # validation_rules.py
    rules_path = os.path.join(data_dir, 'validation_rules.py')
    rules_module = load_module("test_validation_rules", rules_path)
    if rules_module:
        if hasattr(rules_module, 'VALIDATION_RULES'):
            rules = rules_module.VALIDATION_RULES
            categories = list(rules.keys())
            print(f"  ✅ VALIDATION_RULES: {len(categories)}カテゴリ存在")
            for cat in categories:
                rule_count = len(rules[cat])
                print(f"    - {cat}: {rule_count}ルール")
        else:
            print("  ❌ VALIDATION_RULES: 存在しない")
            all_ok = False
    else:
        all_ok = False
    
    # prompt_templates.py
    prompt_path = os.path.join(data_dir, 'prompt_templates.py')
    prompt_module = load_module("test_prompt_templates", prompt_path)
    if prompt_module:
        if hasattr(prompt_module, 'PROMPT_TEMPLATES'):
            templates = prompt_module.PROMPT_TEMPLATES
            print(f"  ✅ PROMPT_TEMPLATES: {len(templates)}テンプレート存在")
        else:
            print("  ❌ PROMPT_TEMPLATES: 存在しない")
            all_ok = False
        
        if hasattr(prompt_module, 'FEW_SHOT_EXAMPLE'):
            print("  ✅ FEW_SHOT_EXAMPLE: 存在")
        else:
            print("  ❌ FEW_SHOT_EXAMPLE: 存在しない")
            all_ok = False
        
        if hasattr(prompt_module, 'VALIDATION_POINTS'):
            print("  ✅ VALIDATION_POINTS: 存在")
        else:
            print("  ❌ VALIDATION_POINTS: 存在しない")
            all_ok = False
    else:
        all_ok = False
    
    # action_definitions.py
    action_path = os.path.join(data_dir, 'action_definitions.py')
    action_module = load_module("test_action_definitions", action_path)
    if action_module:
        if hasattr(action_module, 'ACTION_DEFINITIONS'):
            actions = action_module.ACTION_DEFINITIONS
            print(f"  ✅ ACTION_DEFINITIONS: {len(actions)}アクション存在")
        else:
            print("  ❌ ACTION_DEFINITIONS: 存在しない")
            all_ok = False
        
        if hasattr(action_module, 'format_action_definitions'):
            print("  ✅ format_action_definitions: 存在")
        else:
            print("  ❌ format_action_definitions: 存在しない")
            all_ok = False
    else:
        all_ok = False
    
    # keywords.py
    keywords_path = os.path.join(data_dir, 'keywords.py')
    keywords_module = load_module("test_keywords", keywords_path)
    if keywords_module:
        if hasattr(keywords_module, 'IGNORE_KEYWORDS'):
            print("  ✅ IGNORE_KEYWORDS: 存在")
        else:
            print("  ❌ IGNORE_KEYWORDS: 存在しない")
            all_ok = False
        
        if hasattr(keywords_module, 'MARKERS'):
            print("  ✅ MARKERS: 存在")
        else:
            print("  ❌ MARKERS: 存在しない")
            all_ok = False
        
        if hasattr(keywords_module, 'PARSE_KEYWORDS'):
            print("  ✅ PARSE_KEYWORDS: 存在")
        else:
            print("  ❌ PARSE_KEYWORDS: 存在しない")
            all_ok = False
    else:
        all_ok = False
    
    return all_ok


# ===== バリデータテスト =====
def test_validator():
    """バリデータクラスのテスト"""
    print("\n--- バリデータ ---")
    
    validator_path = os.path.join(codegen_dir, 'validate', 'validator.py')
    validator_module = load_module("test_validator_main", validator_path)
    if validator_module is None:
        return False
    
    all_ok = True
    
    if hasattr(validator_module, 'CodeGenerationValidator'):
        validator = validator_module.CodeGenerationValidator
        
        # VALIDATORS辞書
        if hasattr(validator, 'VALIDATORS'):
            validators = validator.VALIDATORS
            print(f"  ✅ VALIDATORS辞書: {len(validators)}カテゴリ")
            for cat, cls in validators.items():
                print(f"    - {cat}: {cls.__name__}")
        else:
            print("  ❌ VALIDATORS: 存在しない")
            all_ok = False
        
        required = ['validate', 'validate_category', 'get_categories']
        all_ok &= check_class_methods(validator, required, "CodeGenerationValidator")
    else:
        print("  ❌ CodeGenerationValidator: クラスが存在しない")
        all_ok = False
    
    return all_ok


# ===== 項目別バリデータテスト =====
def test_item_validators():
    """項目別バリデータのテスト"""
    print("\n--- 項目別バリデータ ---")
    
    items_dir = os.path.join(codegen_dir, 'validate', 'items')
    all_ok = True
    
    validator_files = [
        'state_validator.py',
        'event_validator.py',
        'transition_validator.py',
        'role_function_validator.py',
        'variable_validator.py',
        'flag_validator.py',
        'queue_validator.py',
        'interrupt_validator.py',
        'timer_validator.py',
        'custom_type_validator.py',
    ]
    
    for filename in validator_files:
        filepath = os.path.join(items_dir, filename)
        module = load_module(f"test_{filename.replace('.py', '')}", filepath)
        
        if module is None:
            all_ok = False
            continue
        
        # クラス名を推測
        class_name = filename.replace('.py', '').replace('_', ' ').title().replace(' ', '')
        if not hasattr(module, class_name):
            # 代替クラス名を試す
            for attr in dir(module):
                if attr.endswith('Validator') and not attr.startswith('_'):
                    class_name = attr
                    break
            else:
                print(f"  ❌ {filename}: Validatorクラスが見つからない")
                all_ok = False
                continue
        
        validator_class = getattr(module, class_name)
        
        if hasattr(validator_class, 'category'):
            print(f"  ✅ {class_name}: category={validator_class.category}")
        else:
            print(f"  ❌ {class_name}: category属性なし")
            all_ok = False
        
        if hasattr(validator_class, 'validate'):
            print(f"  ✅ {class_name}: validateメソッド存在")
        else:
            print(f"  ❌ {class_name}: validateメソッドなし")
            all_ok = False
        
        # rules辞書（インスタンス化して確認）
        try:
            instance = validator_class()
            if hasattr(instance, 'rules'):
                print(f"  ✅ {class_name}: rules辞書({len(instance.rules)}ルール)")
            else:
                print(f"  ❌ {class_name}: rules辞書なし")
                all_ok = False
        except Exception as e:
            print(f"  ❌ {class_name}: インスタンス化失敗: {e}")
            all_ok = False
    
    return all_ok


# ===== プロンプト生成テスト =====
def test_prompt_generator():
    """プロンプト生成クラスのテスト"""
    print("\n--- プロンプト生成 ---")
    
    prompt_path = os.path.join(codegen_dir, 'validate', 'prompt_generator.py')
    prompt_module = load_module("test_prompt_gen", prompt_path)
    if prompt_module is None:
        return False
    
    all_ok = True
    
    if hasattr(prompt_module, 'AIPromptGenerator'):
        generator = prompt_module.AIPromptGenerator
        required = ['generate_diagnosis_prompt', 'generate_review_prompt', '_format_data', '_format_validation']
        all_ok &= check_class_methods(generator, required, "AIPromptGenerator")
    else:
        print("  ❌ AIPromptGenerator: クラスが存在しない")
        all_ok = False
    
    return all_ok


# ===== 回答パーサーテスト =====
def test_response_parser():
    """回答パーサークラスのテスト"""
    print("\n--- 回答パーサー ---")
    
    parser_path = os.path.join(codegen_dir, 'validate', 'response_parser.py')
    parser_module = load_module("test_resp_parser", parser_path)
    if parser_module is None:
        return False
    
    all_ok = True
    
    if hasattr(parser_module, 'AIResponseParser'):
        parser = parser_module.AIResponseParser
        required = ['parse', 'parse_json_response', 'parse_text_response', '_extract_json', '_parse_change']
        all_ok &= check_class_methods(parser, required, "AIResponseParser")
        
        if hasattr(parser, 'ACTION_MAPPING'):
            mapping = parser.ACTION_MAPPING
            print(f"  ✅ ACTION_MAPPING: {len(mapping)}アクション")
        else:
            print("  ❌ ACTION_MAPPING: 存在しない")
            all_ok = False
    else:
        print("  ❌ AIResponseParser: クラスが存在しない")
        all_ok = False
    
    return all_ok


# ===== 変更アクションテスト =====
def test_change_actions():
    """変更アクションのテスト"""
    print("\n--- 変更アクション ---")
    
    actions_path = os.path.join(codegen_dir, 'validate', 'change_actions.py')
    actions_module = load_module("test_change_actions", actions_path)
    if actions_module is None:
        return False
    
    all_ok = True
    
    # ChangeActionType
    if hasattr(actions_module, 'ChangeActionType'):
        action_type = actions_module.ChangeActionType
        expected_values = [
            'SET_INITIAL', 'ADD_TRANSITION', 'ADD_STATE', 'ADD_EVENT',
            'REMOVE_TRANSITION', 'UPDATE_TRANSITION',
            'ADD_ROLE_FUNCTION', 'REMOVE_ROLE_FUNCTION',
            'ADD_VARIABLE', 'ADD_FLAG',
        ]
        missing = []
        for val in expected_values:
            if not hasattr(action_type, val):
                missing.append(val)
        if missing:
            print(f"  ❌ ChangeActionType: 不足: {missing}")
            all_ok = False
        else:
            print(f"  ✅ ChangeActionType: 全{len(expected_values)}列挙値存在")
    else:
        print("  ❌ ChangeActionType: 存在しない")
        all_ok = False
    
    # ChangeRequest
    if hasattr(actions_module, 'ChangeRequest'):
        request = actions_module.ChangeRequest
        required = ['to_dict', 'from_dict']
        all_ok &= check_class_methods(request, required, "ChangeRequest")
    else:
        print("  ❌ ChangeRequest: 存在しない")
        all_ok = False
    
    return all_ok


# ===== 変更適用テスト =====
def test_change_applier():
    """変更適用クラスのテスト"""
    print("\n--- 変更適用 ---")
    
    applier_path = os.path.join(codegen_dir, 'validate', 'change_applier.py')
    applier_module = load_module("test_change_applier", applier_path)
    if applier_module is None:
        return False
    
    all_ok = True
    
    if hasattr(applier_module, 'ChangeApplier'):
        applier = applier_module.ChangeApplier
        required = ['apply', 'apply_all', '_get_handler', '_set_initial', '_add_transition',
                   '_add_state', '_add_event', '_remove_transition', '_update_transition',
                   '_add_role_function', '_add_variable', '_add_flag']
        all_ok &= check_class_methods(applier, required, "ChangeApplier")
    else:
        print("  ❌ ChangeApplier: クラスが存在しない")
        all_ok = False
    
    return all_ok


# ===== クリップボード管理テスト =====
def test_clipboard_manager():
    """クリップボード管理のテスト"""
    print("\n--- クリップボード管理 ---")
    
    clipboard_path = os.path.join(codegen_dir, 'validate', 'clipboard_manager.py')
    clipboard_module = load_module("test_clipboard", clipboard_path)
    if clipboard_module is None:
        return False
    
    all_ok = True
    
    if hasattr(clipboard_module, 'ClipboardManager'):
        manager = clipboard_module.ClipboardManager
        required = ['copy_to_clipboard', 'get_from_clipboard']
        all_ok &= check_class_methods(manager, required, "ClipboardManager")
    else:
        print("  ❌ ClipboardManager: クラスが存在しない")
        all_ok = False
    
    return all_ok


# ===== ロガーテスト =====
def test_logger():
    """ロガーのテスト"""
    print("\n--- ロガー ---")
    
    logger_path = os.path.join(codegen_dir, 'validate', 'logger.py')
    logger_module = load_module("test_validate_logger", logger_path)
    if logger_module is None:
        return False
    
    all_ok = True
    
    if hasattr(logger_module, 'setup_logger'):
        print("  ✅ setup_logger: 存在")
    else:
        print("  ❌ setup_logger: 存在しない")
        all_ok = False
    
    if hasattr(logger_module, 'logger'):
        print("  ✅ logger: 存在")
    else:
        print("  ❌ logger: 存在しない")
        all_ok = False
    
    return all_ok


def run_all_tests():
    """全テスト実行"""
    print("=" * 70)
    print("検証モジュール メソッド存在確認テスト")
    print("=" * 70)
    
    results = {}
    
    results['モデルクラス'] = test_models()
    results['データ辞書'] = test_data_dicts()
    results['バリデータ'] = test_validator()
    results['項目別バリデータ'] = test_item_validators()
    results['プロンプト生成'] = test_prompt_generator()
    results['回答パーサー'] = test_response_parser()
    results['変更アクション'] = test_change_actions()
    results['変更適用'] = test_change_applier()
    results['クリップボード'] = test_clipboard_manager()
    results['ロガー'] = test_logger()
    
    print("\n" + "=" * 70)
    print("テスト結果集計")
    print("=" * 70)
    
    all_passed = True
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
        if not result:
            all_passed = False
    
    print("=" * 70)
    if all_passed:
        print("🎉 全メソッド存在確認テスト成功！")
    else:
        print("❌ 失敗したテストがあります")
    print("=" * 70)
    
    return all_passed


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)