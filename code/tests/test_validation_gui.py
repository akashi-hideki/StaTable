# tests/test_validation_gui.py
"""
検証・AI連携GUIの統合テスト
直接実行: python tests/test_validation_gui.py
"""

import sys
import os
import json
import importlib.util
import tempfile
import shutil
import logging

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
codegen_dir = os.path.join(project_root, 'codegen')
statable_dir = os.path.join(project_root, 'statable')
gui_dir = os.path.join(project_root, 'statable_gui')

sys.path.insert(0, project_root)
sys.path.insert(0, codegen_dir)
sys.path.insert(0, statable_dir)
sys.path.insert(0, gui_dir)

# ロガー設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_validation_gui")

# 結果カウンタ
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
    """モジュールをロード"""
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


def get_sample_data():
    """サンプルデータを取得"""
    sample_path = os.path.join(codegen_dir, "sample_data.py")
    sample_module = load_module("test_gui_sample", sample_path)
    if sample_module is None:
        return None, None
    sample_gen = sample_module.SampleDataGenerator()
    return sample_gen.get_sample_data()


# PySide6 が利用可能かチェック
try:
    from PySide6.QtWidgets import QApplication
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False


# ===== バリデータテスト =====
def test_validator():
    """検証機能のテスト"""
    print("\n=== バリデータ ===")
    
    validator_path = os.path.join(codegen_dir, 'validate', 'validator.py')
    validator_module = load_module("test_gui_validator", validator_path)
    if validator_module is None:
        log_result("validator.py", False)
        return
    
    sm, gd = get_sample_data()
    if sm is None or gd is None:
        log_result("サンプルデータ", False)
        return
    
    validator = validator_module.CodeGenerationValidator()
    result = validator.validate(sm, gd)
    
    log_result("validate()実行", result is not None)
    log_result("issues属性", hasattr(result, 'issues'))
    log_result("error_count", hasattr(result, 'error_count'))
    log_result("warning_count", hasattr(result, 'warning_count'))
    log_result("info_count", hasattr(result, 'info_count'))
    
    # カテゴリ確認
    categories = validator.get_categories()
    log_result("get_categories()", len(categories) >= 5, f"({len(categories)}カテゴリ)")
    
    # カテゴリ別検証
    issues = validator.validate_category('state', sm, gd)
    log_result("validate_category('state')", isinstance(issues, list))


# ===== プロンプト生成テスト =====
def test_prompt_generator():
    """プロンプト生成のテスト"""
    print("\n=== プロンプト生成 ===")
    
    prompt_path = os.path.join(codegen_dir, 'validate', 'prompt_generator.py')
    prompt_module = load_module("test_gui_prompt", prompt_path)
    if prompt_module is None:
        log_result("prompt_generator.py", False)
        return
    
    sm, gd = get_sample_data()
    if sm is None or gd is None:
        log_result("サンプルデータ", False)
        return
    
    generator = prompt_module.AIPromptGenerator()
    
    # 診断プロンプト
    prompt = generator.generate_diagnosis_prompt(sm, gd)
    log_result("generate_diagnosis_prompt()", len(prompt) > 100, f"({len(prompt)}文字)")
    log_result("JSON含む", 'JSON' in prompt)
    log_result("changes含む", 'changes' in prompt)
    log_result("状態名含む", all(name in prompt for name in sm.states.keys()))
    
    # レビュープロンプト
    review = generator.generate_review_prompt(sm, gd)
    log_result("generate_review_prompt()", len(review) > 50, f"({len(review)}文字)")


# ===== 回答パーサーテスト =====
def test_response_parser():
    """回答パーサーのテスト"""
    print("\n=== 回答パーサー ===")
    
    parser_path = os.path.join(codegen_dir, 'validate', 'response_parser.py')
    parser_module = load_module("test_gui_parser", parser_path)
    if parser_module is None:
        log_result("response_parser.py", False)
        return
    
    parser = parser_module.AIResponseParser()
    
    # JSON回答
    json_response = '''{
  "changes": [
    {
      "action": "set_initial",
      "params": {"state": "INIT"},
      "reason": "初期状態が未設定"
    },
    {
      "action": "add_transition",
      "params": {"source": "ERROR", "event": "STOP", "target": "IDLE"},
      "reason": "エラー回復"
    }
  ]
}'''
    
    changes = parser.parse(json_response)
    log_result("JSON解析", len(changes) == 2, f"({len(changes)}件)")
    
    if changes:
        log_result("set_initial解析", changes[0].action.value == 'set_initial')
        log_result("add_transition解析", changes[1].action.value == 'add_transition')
    
    # ノイズ付き回答
    noisy = f"承知しました。\n{json_response}\n以上です。"
    changes2 = parser.parse(noisy)
    log_result("ノイズ付きJSON解析", len(changes2) == 2, f"({len(changes2)}件)")
    
    # テキスト回答
    text_response = "ERROR --[STOP]--> IDLE を追加"
    changes3 = parser.parse_text_response(text_response)
    log_result("テキスト解析", len(changes3) >= 1, f"({len(changes3)}件)")


# ===== 変更適用テスト =====
def test_change_applier():
    """変更適用のテスト"""
    print("\n=== 変更適用 ===")
    
    applier_path = os.path.join(codegen_dir, 'validate', 'change_applier.py')
    applier_module = load_module("test_gui_applier", applier_path)
    if applier_module is None:
        log_result("change_applier.py", False)
        return
    
    actions_path = os.path.join(codegen_dir, 'validate', 'change_actions.py')
    actions_module = load_module("test_gui_actions", actions_path)
    if actions_module is None:
        log_result("change_actions.py", False)
        return
    
    sm, gd = get_sample_data()
    if sm is None or gd is None:
        log_result("サンプルデータ", False)
        return
    
    applier = applier_module.ChangeApplier(sm, gd)
    
    # set_initial
    change = actions_module.ChangeRequest(
        action=actions_module.ChangeActionType.SET_INITIAL,
        params={'state': 'INIT'},
        reason='初期状態設定'
    )
    success, message = applier.apply(change)
    log_result("set_initial適用", success, f"({message})")
    
    # add_transition
    change2 = actions_module.ChangeRequest(
        action=actions_module.ChangeActionType.ADD_TRANSITION,
        params={'source': 'ERROR', 'event': 'STOP', 'target': 'IDLE'},
        reason='エラー回復'
    )
    success2, message2 = applier.apply(change2)
    log_result("add_transition適用", success2, f"({message2})")
    
    # 全適用
    changes = [
        actions_module.ChangeRequest(
            action=actions_module.ChangeActionType.SET_INITIAL,
            params={'state': 'INIT'}
        ),
        actions_module.ChangeRequest(
            action=actions_module.ChangeActionType.ADD_TRANSITION,
            params={'source': 'ERROR', 'event': 'STOP', 'target': 'IDLE'}
        ),
    ]
    result = applier.apply_all(changes)
    log_result("apply_all()", result['applied'] >= 1, f"(適用: {result['applied']}, 失敗: {result['failed']})")


# ===== 統合フローテスト =====
def test_integration_flow():
    """統合フローのテスト"""
    print("\n=== 統合フロー ===")
    
    # 全モジュールをロード
    validator_path = os.path.join(codegen_dir, 'validate', 'validator.py')
    prompt_path = os.path.join(codegen_dir, 'validate', 'prompt_generator.py')
    parser_path = os.path.join(codegen_dir, 'validate', 'response_parser.py')
    applier_path = os.path.join(codegen_dir, 'validate', 'change_applier.py')
    actions_path = os.path.join(codegen_dir, 'validate', 'change_actions.py')
    
    validator_module = load_module("test_flow_validator", validator_path)
    prompt_module = load_module("test_flow_prompt", prompt_path)
    parser_module = load_module("test_flow_parser", parser_path)
    applier_module = load_module("test_flow_applier", applier_path)
    actions_module = load_module("test_flow_actions", actions_path)
    
    if None in [validator_module, prompt_module, parser_module, applier_module, actions_module]:
        log_result("モジュールロード", False)
        return
    
    sm, gd = get_sample_data()
    if sm is None or gd is None:
        log_result("サンプルデータ", False)
        return
    
    # 1. 検証
    validator = validator_module.CodeGenerationValidator()
    result = validator.validate(sm, gd)
    log_result("Step 1: 検証", True, f"(エラー: {result.error_count}, 警告: {result.warning_count})")
    
    # 2. プロンプト生成
    generator = prompt_module.AIPromptGenerator()
    prompt = generator.generate_diagnosis_prompt(sm, gd, result)
    log_result("Step 2: プロンプト生成", len(prompt) > 100, f"({len(prompt)}文字)")
    
    # 3. AI回答（シミュレーション）
    ai_response = '''{
  "changes": [
    {"action": "set_initial", "params": {"state": "INIT"}, "reason": "初期状態未設定"},
    {"action": "add_transition", "params": {"source": "ERROR", "event": "STOP", "target": "IDLE"}, "reason": "エラー回復"}
  ]
}'''
    
    # 4. 回答パース
    parser = parser_module.AIResponseParser()
    changes = parser.parse(ai_response)
    log_result("Step 4: 回答パース", len(changes) == 2, f"({len(changes)}件)")
    
    # 5. 変更適用
    applier = applier_module.ChangeApplier(sm, gd)
    apply_result = applier.apply_all(changes)
    log_result("Step 5: 変更適用", apply_result['applied'] >= 1, 
               f"(適用: {apply_result['applied']}, 失敗: {apply_result['failed']})")
    
    # 検証
    log_result("初期状態設定確認", sm.initial_state == 'INIT')


def run_all_tests():
    """全テスト実行"""
    global PASS_COUNT, FAIL_COUNT, FAILED_ITEMS
    PASS_COUNT = 0
    FAIL_COUNT = 0
    FAILED_ITEMS = []
    
    print("=" * 60)
    print("検証・AI連携 GUI統合テスト")
    print("=" * 60)
    
    test_validator()
    test_prompt_generator()
    test_response_parser()
    test_change_applier()
    test_integration_flow()
    
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