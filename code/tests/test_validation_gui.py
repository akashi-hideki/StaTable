# tests/test_validation_gui.py
"""
検証・AI連携GUIの統合テスト
"""

import sys
import os
import json
import importlib.util
import pytest
import tempfile
import shutil
import logging

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

# ロガー設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_validation_gui")


def load_module(name, path):
    """モジュールをファイルパスからロード"""
    logger.debug(f"load_module: {name} from {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_validator_module():
    """バリデータモジュールを取得"""
    path = os.path.join(codegen_dir, 'validate', 'validator.py')
    return load_module("test_validator", path)


def get_prompt_generator_module():
    """プロンプト生成モジュールを取得"""
    path = os.path.join(codegen_dir, 'validate', 'prompt_generator.py')
    return load_module("test_prompt_generator", path)


def get_response_parser_module():
    """回答パーサーモジュールを取得"""
    path = os.path.join(codegen_dir, 'validate', 'response_parser.py')
    return load_module("test_response_parser", path)


def get_change_applier_module():
    """変更適用モジュールを取得"""
    path = os.path.join(codegen_dir, 'validate', 'change_applier.py')
    return load_module("test_change_applier", path)


def get_sample_data():
    """サンプルデータを取得"""
    logger.debug("Loading sample data")
    sample_path = os.path.join(codegen_dir, "sample_data.py")
    sample_module = load_module("test_sample_data", sample_path)
    return sample_module.SampleDataGenerator().get_sample_data()


# PySide6 が利用可能かチェック
try:
    from PySide6.QtWidgets import QApplication
    PYSIDE_AVAILABLE = True
    logger.debug("PySide6 is available")
except ImportError:
    PYSIDE_AVAILABLE = False
    logger.warning("PySide6 is not available")


@pytest.fixture(scope="module")
def qapp():
    """QApplication フィクスチャ"""
    if not PYSIDE_AVAILABLE:
        pytest.skip("PySide6がインストールされていません")
    logger.debug("Creating QApplication")
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def sample_data():
    """サンプルデータ"""
    logger.debug("Creating sample data fixture")
    sm, gd = get_sample_data()
    logger.debug(f"Sample data: states={len(sm.states)}, events={len(sm.events)}, "
                f"transitions={len(sm.transitions)}")
    return sm, gd


@pytest.fixture
def validator():
    """バリデータ"""
    logger.debug("Creating validator fixture")
    validator_module = get_validator_module()
    return validator_module.CodeGenerationValidator()


@pytest.fixture
def prompt_generator():
    """プロンプト生成器"""
    logger.debug("Creating prompt generator fixture")
    prompt_module = get_prompt_generator_module()
    return prompt_module.AIPromptGenerator()


@pytest.fixture
def response_parser():
    """回答パーサー"""
    logger.debug("Creating response parser fixture")
    parser_module = get_response_parser_module()
    return parser_module.AIResponseParser()


@pytest.fixture
def change_applier(sample_data):
    """変更適用器"""
    logger.debug("Creating change applier fixture")
    applier_module = get_change_applier_module()
    sm, gd = sample_data
    return applier_module.ChangeApplier(sm, gd)


# ===== バリデータテスト =====
class TestValidator:
    """検証機能のテスト"""
    
    def test_validate_all(self, validator, sample_data):
        """全検証の実行"""
        logger.debug("test_validate_all started")
        sm, gd = sample_data
        
        result = validator.validate(sm, gd)
        
        logger.debug(f"Validation result: errors={result.error_count}, "
                    f"warnings={result.warning_count}, infos={result.info_count}")
        
        assert result is not None
        assert hasattr(result, 'issues')
        assert hasattr(result, 'error_count')
        assert hasattr(result, 'warning_count')
        assert hasattr(result, 'info_count')
    
    def test_validate_categories(self, validator, sample_data):
        """全カテゴリの検証"""
        logger.debug("test_validate_categories started")
        sm, gd = sample_data
        
        categories = validator.get_categories()
        logger.debug(f"Categories: {categories}")
        
        assert len(categories) >= 5
        assert 'state' in categories
        assert 'event' in categories
        assert 'transition' in categories
    
    def test_validate_specific_category(self, validator, sample_data):
        """特定カテゴリの検証"""
        logger.debug("test_validate_specific_category started")
        sm, gd = sample_data
        
        issues = validator.validate_category('state', sm, gd)
        logger.debug(f"State validation issues: {len(issues)}")
        
        assert isinstance(issues, list)
    
    def test_validation_result_to_dict(self, validator, sample_data):
        """検証結果の辞書変換"""
        logger.debug("test_validation_result_to_dict started")
        sm, gd = sample_data
        
        result = validator.validate(sm, gd)
        data = result.to_dict()
        
        logger.debug(f"Result dict keys: {list(data.keys())}")
        
        assert 'issues' in data
        assert 'error_count' in data
        assert 'warning_count' in data
        assert 'info_count' in data
        assert isinstance(data['issues'], list)


# ===== プロンプト生成テスト =====
class TestPromptGenerator:
    """プロンプト生成のテスト"""
    
    def test_generate_diagnosis_prompt(self, prompt_generator, sample_data):
        """診断プロンプトの生成"""
        logger.debug("test_generate_diagnosis_prompt started")
        sm, gd = sample_data
        
        prompt = prompt_generator.generate_diagnosis_prompt(sm, gd)
        
        logger.debug(f"Prompt length: {len(prompt)}")
        logger.debug(f"Prompt first 100 chars: {prompt[:100]}")
        
        assert len(prompt) > 100
        assert '状態遷移設計' in prompt
        assert 'JSON' in prompt
        assert 'changes' in prompt
    
    def test_prompt_contains_data(self, prompt_generator, sample_data):
        """プロンプトにデータが含まれるか"""
        logger.debug("test_prompt_contains_data started")
        sm, gd = sample_data
        
        prompt = prompt_generator.generate_diagnosis_prompt(sm, gd)
        
        # 状態名が含まれるか
        for name in sm.states.keys():
            assert name in prompt, f"状態「{name}」がプロンプトに含まれていない"
        
        # イベント名が含まれるか
        for name in sm.events.keys():
            assert name in prompt, f"イベント「{name}」がプロンプトに含まれていない"
    
    def test_prompt_has_few_shot_example(self, prompt_generator, sample_data):
        """Few-shot例が含まれるか"""
        logger.debug("test_prompt_has_few_shot_example started")
        sm, gd = sample_data
        
        prompt = prompt_generator.generate_diagnosis_prompt(sm, gd)
        
        assert 'set_initial' in prompt
        assert 'add_transition' in prompt
        assert 'reason' in prompt


# ===== 回答パーサーテスト =====
class TestResponseParser:
    """回答パーサーのテスト"""
    
    SAMPLE_AI_RESPONSE = '''{
  "changes": [
    {
      "action": "set_initial",
      "params": {"state": "INIT"},
      "reason": "初期状態が未設定のため"
    },
    {
      "action": "add_transition",
      "params": {
        "source": "ERROR",
        "event": "STOP",
        "target": "IDLE",
        "action_name": "ResetError"
      },
      "reason": "エラー状態からの回復遷移がないため"
    }
  ]
}'''
    
    def test_parse_json_response(self, response_parser):
        """JSON回答のパース"""
        logger.debug("test_parse_json_response started")
        
        changes = response_parser.parse(self.SAMPLE_AI_RESPONSE)
        
        logger.debug(f"Parsed changes: {len(changes)}")
        
        assert len(changes) == 2
        assert changes[0].action.value == 'set_initial'
        assert changes[0].params['state'] == 'INIT'
        assert changes[1].action.value == 'add_transition'
        assert changes[1].params['source'] == 'ERROR'
    
    def test_parse_with_noise(self, response_parser):
        """ノイズを含む回答のパース"""
        logger.debug("test_parse_with_noise started")
        
        noisy_response = f"""承知しました。検証結果を以下に示します。

{self.SAMPLE_AI_RESPONSE}

以上が提案する変更です。"""
        
        changes = response_parser.parse(noisy_response)
        
        logger.debug(f"Parsed changes from noisy response: {len(changes)}")
        
        assert len(changes) == 2
    
    def test_parse_text_response(self, response_parser):
        """テキスト回答のパース"""
        logger.debug("test_parse_text_response started")
        
        text_response = """1. ERROR --[STOP]--> IDLE を追加
2. 初期状態: INIT"""
        
        changes = response_parser.parse_text_response(text_response)
        
        logger.debug(f"Parsed changes from text: {len(changes)}")
        
        assert len(changes) >= 1


# ===== 変更適用テスト =====
class TestChangeApplier:
    """変更適用のテスト"""
    
    def test_apply_set_initial(self, change_applier, sample_data):
        """初期状態の設定"""
        logger.debug("test_apply_set_initial started")
        
        from codegen.validate.change_actions import ChangeRequest, ChangeActionType
        
        change = ChangeRequest(
            action=ChangeActionType.SET_INITIAL,
            params={'state': 'INIT'},
            reason='初期状態が未設定'
        )
        
        success, message = change_applier.apply(change)
        
        logger.debug(f"Apply result: success={success}, message={message}")
        
        assert success is True
        assert change_applier.sm.initial_state == 'INIT'
    
    def test_apply_add_transition(self, change_applier, sample_data):
        """遷移の追加"""
        logger.debug("test_apply_add_transition started")
        
        from codegen.validate.change_actions import ChangeRequest, ChangeActionType
        
        change = ChangeRequest(
            action=ChangeActionType.ADD_TRANSITION,
            params={
                'source': 'ERROR',
                'event': 'STOP',
                'target': 'IDLE',
                'action_name': 'ResetError',
            },
            reason='エラー回復遷移'
        )
        
        # 事前にイベントと状態が存在することを確認
        assert 'ERROR' in change_applier.sm.states
        assert 'STOP' in change_applier.sm.events
        assert 'IDLE' in change_applier.sm.states
        
        success, message = change_applier.apply(change)
        
        logger.debug(f"Apply result: success={success}, message={message}")
        
        assert success is True
    
    def test_apply_all(self, change_applier, sample_data):
        """全変更の適用"""
        logger.debug("test_apply_all started")
        
        from codegen.validate.change_actions import ChangeRequest, ChangeActionType
        
        changes = [
            ChangeRequest(
                action=ChangeActionType.SET_INITIAL,
                params={'state': 'INIT'},
                reason='初期状態設定'
            ),
            ChangeRequest(
                action=ChangeActionType.ADD_TRANSITION,
                params={'source': 'ERROR', 'event': 'STOP', 'target': 'IDLE'},
                reason='エラー回復'
            ),
        ]
        
        result = change_applier.apply_all(changes)
        
        logger.debug(f"Apply all result: applied={result['applied']}, failed={result['failed']}")
        
        assert result['applied'] == 2
        assert result['failed'] == 0


# ===== GUI統合テスト =====
class TestValidationGUI:
    """検証GUIの統合テスト"""
    
    def test_validation_dialog_exists(self):
        """検証ダイアログモジュールが存在するか"""
        logger.debug("test_validation_dialog_exists started")
        
        dialog_path = os.path.join(gui_dir, "validation_dialog.py")
        assert os.path.exists(dialog_path), "validation_dialog.pyが存在しません"
    
    def test_validation_dialog_creation(self, qapp, sample_data, validator, prompt_generator):
        """検証ダイアログの作成"""
        if not PYSIDE_AVAILABLE:
            pytest.skip("PySide6がインストールされていません")
        
        logger.debug("test_validation_dialog_creation started")
        
        dialog_path = os.path.join(gui_dir, "validation_dialog.py")
        if not os.path.exists(dialog_path):
            pytest.skip("validation_dialog.pyが存在しません")
        
        dialog_module = load_module("test_validation_dialog", dialog_path)
        sm, gd = sample_data
        
        dlg = dialog_module.ValidationDialog(sm, gd)
        
        logger.debug(f"Dialog created: title={dlg.windowTitle()}")
        
        assert dlg is not None
        assert dlg.windowTitle() == "コード生成前検証・AI診断"
        dlg.close()
    
    def test_validation_dialog_runs_validation(self, qapp, sample_data):
        """検証ダイアログが検証を実行するか"""
        if not PYSIDE_AVAILABLE:
            pytest.skip("PySide6がインストールされていません")
        
        logger.debug("test_validation_dialog_runs_validation started")
        
        dialog_path = os.path.join(gui_dir, "validation_dialog.py")
        if not os.path.exists(dialog_path):
            pytest.skip("validation_dialog.pyが存在しません")
        
        dialog_module = load_module("test_validation_dialog2", dialog_path)
        sm, gd = sample_data
        
        dlg = dialog_module.ValidationDialog(sm, gd)
        
        # 検証結果が設定されているか
        assert dlg.validation_result is not None
        assert hasattr(dlg.validation_result, 'issues')
        
        # 問題リストが表示されているか
        assert dlg.issue_tree.topLevelItemCount() >= 0
        
        logger.debug(f"Issue tree items: {dlg.issue_tree.topLevelItemCount()}")
        
        dlg.close()


# ===== 統合フローテスト =====
class TestIntegrationFlow:
    """統合フローのテスト"""
    
    def test_full_validation_flow(self, validator, prompt_generator, response_parser, change_applier, sample_data):
        """検証→プロンプト生成→回答パース→変更適用のフルフロー"""
        logger.debug("test_full_validation_flow started")
        
        sm, gd = sample_data
        
        # 1. 検証
        result = validator.validate(sm, gd)
        logger.debug(f"Step 1 - Validation: errors={result.error_count}")
        
        # 2. プロンプト生成
        prompt = prompt_generator.generate_diagnosis_prompt(sm, gd, result)
        logger.debug(f"Step 2 - Prompt generated: {len(prompt)} chars")
        
        # 3. AI回答（シミュレーション）
        ai_response = '''{
  "changes": [
    {
      "action": "set_initial",
      "params": {"state": "INIT"},
      "reason": "初期状態が未設定"
    }
  ]
}'''
        
        # 4. 回答パース
        changes = response_parser.parse(ai_response)
        logger.debug(f"Step 4 - Parsed changes: {len(changes)}")
        
        # 5. 変更適用
        result = change_applier.apply_all(changes)
        logger.debug(f"Step 5 - Applied: {result['applied']}, Failed: {result['failed']}")
        
        # 検証
        assert result['applied'] == 1
        assert change_applier.sm.initial_state == 'INIT'
        
        logger.debug("Full validation flow completed successfully")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])