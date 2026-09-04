# tests/test_validation_real_data.py
"""
検証機能の実データテスト
実際のデータパターンで検証機能をテストする
直接実行: python tests/test_validation_real_data.py
"""

import sys
import os
import importlib.util
import logging

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
codegen_dir = os.path.join(project_root, 'codegen')
statable_dir = os.path.join(project_root, 'statable')

sys.path.insert(0, project_root)
sys.path.insert(0, codegen_dir)
sys.path.insert(0, statable_dir)

# ロガー設定（WARNINGに抑制）
logging.basicConfig(level=logging.WARNING)
validate_logger = logging.getLogger('validate')
validate_logger.setLevel(logging.WARNING)

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


# ===== インポート =====
from statable.state_machine import StateMachine
from statable.model import State, Event, Transition, RoleFunction, StateType, EventKind
from statable.global_defs import (
    GlobalDefinitions, SystemVariable, EventFlag,
    CustomTypeDef, StructMemberDef,
    EventQueueDef, InterruptHandlerDef, InterruptAction,
    TimerBaseDef, TimerDerivedDef
)

from validate.validator import CodeGenerationValidator
from validate.models import ValidationSeverity


# ===== テストデータ作成ヘルパー =====

def create_valid_state_machine():
    """正常なステートマシンを作成"""
    sm = StateMachine()
    
    # 状態
    sm.add_state(State(name="INIT", type=StateType.INITIAL, description="初期状態"))
    sm.add_state(State(name="IDLE", type=StateType.NORMAL, description="アイドル状態"))
    sm.add_state(State(name="RUNNING", type=StateType.NORMAL, description="実行状態"))
    sm.add_state(State(name="ERROR", type=StateType.NORMAL, description="エラー状態"))
    
    # 初期状態
    sm.set_initial("INIT")
    
    # イベント
    sm.add_event(Event(name="POWER_ON", kind=EventKind.SIGNAL, description="電源ON"))
    sm.add_event(Event(name="START", kind=EventKind.SIGNAL, description="開始"))
    sm.add_event(Event(name="STOP", kind=EventKind.SIGNAL, description="停止"))
    sm.add_event(Event(name="RESET", kind=EventKind.SIGNAL, description="リセット"))
    sm.add_event(Event(name="ERROR_DETECTED", kind=EventKind.SIGNAL, description="エラー検出"))
    
    # 遷移
    sm.add_transition(Transition(source="INIT", event="POWER_ON", target="IDLE", action="PowerOn"))
    sm.add_transition(Transition(source="IDLE", event="START", target="RUNNING", condition="StartOk", action="Start"))
    sm.add_transition(Transition(source="RUNNING", event="STOP", target="IDLE", action="Stop"))
    sm.add_transition(Transition(source="IDLE", event="ERROR_DETECTED", target="ERROR", action="HandleError"))
    sm.add_transition(Transition(source="ERROR", event="RESET", target="IDLE", action="ResetError"))
    
    # ロール関数
    sm.add_role_function(RoleFunction(name="PowerOn", return_type="void", description="電源ON処理"))
    sm.add_role_function(RoleFunction(name="StartOk", return_type="bool", description="開始条件"))
    sm.add_role_function(RoleFunction(name="Start", return_type="void", description="開始処理"))
    sm.add_role_function(RoleFunction(name="Stop", return_type="void", description="停止処理"))
    sm.add_role_function(RoleFunction(name="HandleError", return_type="void", description="エラー処理"))
    sm.add_role_function(RoleFunction(name="ResetError", return_type="void", description="エラーリセット"))
    
    return sm


def create_valid_global_defs():
    """正常なグローバル定義を作成"""
    gd = GlobalDefinitions()
    
    # 変数
    gd.variables = [
        SystemVariable(name="battery_voltage", type="uint16", unit="mV", group="Power"),
        SystemVariable(name="system_tick", type="uint32", unit="ms", group="Timer"),
    ]
    
    # フラグ
    gd.flags = [
        EventFlag(name="EVT_POWER_ON_REQ", min_value=0, max_value=1, group="System"),
        EventFlag(name="EVT_START_REQ", min_value=0, max_value=1, group="System"),
        EventFlag(name="EVT_ERROR_FLAG", min_value=0, max_value=1, group="Error"),
    ]
    
    return gd


def create_sm_without_initial():
    """初期状態なしのステートマシン"""
    sm = create_valid_state_machine()
    sm.initial_state = None
    return sm


def create_sm_with_unreachable_state():
    """到達不能状態があるステートマシン"""
    sm = create_valid_state_machine()
    sm.add_state(State(name="ISOLATED", type=StateType.NORMAL, description="孤立状態"))
    return sm


def create_sm_with_undefined_target():
    """未定義の遷移先があるステートマシン"""
    sm = create_valid_state_machine()
    sm.add_transition(Transition(source="IDLE", event="START", target="UNDEFINED_STATE"))
    return sm


def create_sm_with_undefined_event():
    """未定義イベントを使用するステートマシン"""
    sm = create_valid_state_machine()
    sm.add_transition(Transition(source="IDLE", event="UNDEFINED_EVENT", target="RUNNING"))
    return sm


def create_sm_with_duplicate_transition():
    """重複遷移があるステートマシン"""
    sm = create_valid_state_machine()
    sm.add_transition(Transition(source="INIT", event="POWER_ON", target="IDLE", action="PowerOn"))
    return sm


def create_sm_with_unused_event():
    """未使用イベントがあるステートマシン"""
    sm = create_valid_state_machine()
    sm.add_event(Event(name="UNUSED_EVENT", kind=EventKind.SIGNAL, description="未使用イベント"))
    return sm


def create_sm_with_self_loop():
    """自己遷移があるステートマシン"""
    sm = create_valid_state_machine()
    sm.add_transition(Transition(source="IDLE", event="START", target="IDLE"))
    return sm


def create_sm_with_unused_role_function():
    """未使用ロール関数があるステートマシン"""
    sm = create_valid_state_machine()
    sm.add_role_function(RoleFunction(name="UnusedFunction", return_type="void", description="未使用関数"))
    return sm


def create_gd_with_duplicate_variable():
    """重複変数があるグローバル定義"""
    gd = create_valid_global_defs()
    gd.variables.append(SystemVariable(name="battery_voltage", type="uint16", group="Power"))
    return gd


def create_gd_with_duplicate_flag():
    """重複フラグがあるグローバル定義"""
    gd = create_valid_global_defs()
    gd.flags.append(EventFlag(name="EVT_POWER_ON_REQ", min_value=0, max_value=1, group="System"))
    return gd


def create_gd_with_invalid_variable_type():
    """無効な型の変数があるグローバル定義"""
    gd = create_valid_global_defs()
    gd.variables.append(SystemVariable(name="unknown_var", type="unknown_type", group="Test"))
    return gd


def create_gd_with_invalid_flag_range():
    """不正な範囲のフラグがあるグローバル定義"""
    gd = create_valid_global_defs()
    gd.flags.append(EventFlag(name="INVALID_FLAG", min_value=10, max_value=1, group="Test"))
    return gd


# ===== 検証テスト =====

class TestValidData:
    """正常なデータの検証"""
    
    def test_valid_data_no_errors(self):
        """正常データはエラーなし"""
        print("\n--- 正常データ ---")
        validator = CodeGenerationValidator()
        sm = create_valid_state_machine()
        gd = create_valid_global_defs()
        
        result = validator.validate(sm, gd)
        
        log_result("エラーなし", result.error_count == 0, f"(エラー: {result.error_count})")
        log_result("警告は許容", result.warning_count >= 0, f"(警告: {result.warning_count})")


class TestStateValidation:
    """状態検証のテスト"""
    
    def test_missing_initial_state(self):
        """初期状態なしを検出"""
        print("\n--- 初期状態なし ---")
        validator = CodeGenerationValidator()
        sm = create_sm_without_initial()
        gd = create_valid_global_defs()
        
        result = validator.validate(sm, gd)
        
        has_error = any(i.code == 'STATE_NO_INITIAL' for i in result.issues)
        log_result("STATE_NO_INITIAL検出", has_error)
        log_result("ERRORレベル", result.error_count >= 1, f"(エラー: {result.error_count})")
    
    def test_unreachable_state(self):
        """到達不能状態を検出"""
        print("\n--- 到達不能状態 ---")
        validator = CodeGenerationValidator()
        sm = create_sm_with_unreachable_state()
        gd = create_valid_global_defs()
        
        result = validator.validate(sm, gd)
        
        has_warning = any(i.code == 'STATE_UNREACHABLE' and i.target == 'ISOLATED' for i in result.issues)
        log_result("STATE_UNREACHABLE検出", has_warning)


class TestTransitionValidation:
    """遷移検証のテスト"""
    
    def test_undefined_target(self):
        """未定義遷移先を検出"""
        print("\n--- 未定義遷移先 ---")
        validator = CodeGenerationValidator()
        sm = create_sm_with_undefined_target()
        gd = create_valid_global_defs()
        
        result = validator.validate(sm, gd)
        
        has_error = any(i.code == 'TRANSITION_TARGET_UNDEFINED' for i in result.issues)
        log_result("TRANSITION_TARGET_UNDEFINED検出", has_error)
        log_result("ERRORレベル", result.error_count >= 1, f"(エラー: {result.error_count})")
    
    def test_undefined_event(self):
        """未定義イベントを検出"""
        print("\n--- 未定義イベント ---")
        validator = CodeGenerationValidator()
        sm = create_sm_with_undefined_event()
        gd = create_valid_global_defs()
        
        result = validator.validate(sm, gd)
        
        has_error = any(i.code == 'TRANSITION_EVENT_UNDEFINED' for i in result.issues)
        log_result("TRANSITION_EVENT_UNDEFINED検出", has_error)
    
    def test_duplicate_transition(self):
        """重複遷移を検出"""
        print("\n--- 重複遷移 ---")
        validator = CodeGenerationValidator()
        sm = create_sm_with_duplicate_transition()
        gd = create_valid_global_defs()
        
        result = validator.validate(sm, gd)
        
        has_warning = any(i.code == 'TRANSITION_DUPLICATE' for i in result.issues)
        log_result("TRANSITION_DUPLICATE検出", has_warning)
    
    def test_self_loop(self):
        """自己遷移を検出"""
        print("\n--- 自己遷移 ---")
        validator = CodeGenerationValidator()
        sm = create_sm_with_self_loop()
        gd = create_valid_global_defs()
        
        result = validator.validate(sm, gd)
        
        has_info = any(i.code == 'TRANSITION_SELF_LOOP' for i in result.issues)
        log_result("TRANSITION_SELF_LOOP検出", has_info)


class TestEventValidation:
    """イベント検証のテスト"""
    
    def test_unused_event(self):
        """未使用イベントを検出"""
        print("\n--- 未使用イベント ---")
        validator = CodeGenerationValidator()
        sm = create_sm_with_unused_event()
        gd = create_valid_global_defs()
        
        result = validator.validate(sm, gd)
        
        has_warning = any(i.code == 'EVENT_UNUSED' and i.target == 'UNUSED_EVENT' for i in result.issues)
        log_result("EVENT_UNUSED検出", has_warning)


class TestRoleFunctionValidation:
    """ロール関数検証のテスト"""
    
    def test_unused_role_function(self):
        """未使用ロール関数を検出"""
        print("\n--- 未使用ロール関数 ---")
        validator = CodeGenerationValidator()
        sm = create_sm_with_unused_role_function()
        gd = create_valid_global_defs()
        
        result = validator.validate(sm, gd)
        
        has_warning = any(i.code == 'ROLE_FUNC_UNUSED' and i.target == 'UnusedFunction' for i in result.issues)
        log_result("ROLE_FUNC_UNUSED検出", has_warning)


class TestVariableValidation:
    """変数検証のテスト"""
    
    def test_duplicate_variable(self):
        """重複変数を検出"""
        print("\n--- 重複変数 ---")
        validator = CodeGenerationValidator()
        sm = create_valid_state_machine()
        gd = create_gd_with_duplicate_variable()
        
        result = validator.validate(sm, gd)
        
        has_error = any(i.code == 'VAR_DUPLICATE_NAME' for i in result.issues)
        log_result("VAR_DUPLICATE_NAME検出", has_error)
        log_result("ERRORレベル", result.error_count >= 1, f"(エラー: {result.error_count})")
    
    def test_invalid_variable_type(self):
        """無効な型の変数を検出"""
        print("\n--- 無効な型 ---")
        validator = CodeGenerationValidator()
        sm = create_valid_state_machine()
        gd = create_gd_with_invalid_variable_type()
        
        result = validator.validate(sm, gd)
        
        has_warning = any(i.code == 'VAR_INVALID_TYPE' for i in result.issues)
        log_result("VAR_INVALID_TYPE検出", has_warning)


class TestFlagValidation:
    """フラグ検証のテスト"""
    
    def test_duplicate_flag(self):
        """重複フラグを検出"""
        print("\n--- 重複フラグ ---")
        validator = CodeGenerationValidator()
        sm = create_valid_state_machine()
        gd = create_gd_with_duplicate_flag()
        
        result = validator.validate(sm, gd)
        
        has_error = any(i.code == 'FLAG_DUPLICATE_NAME' for i in result.issues)
        log_result("FLAG_DUPLICATE_NAME検出", has_error)
    
    def test_invalid_flag_range(self):
        """不正な範囲のフラグを検出"""
        print("\n--- 不正なフラグ範囲 ---")
        validator = CodeGenerationValidator()
        sm = create_valid_state_machine()
        gd = create_gd_with_invalid_flag_range()
        
        result = validator.validate(sm, gd)
        
        has_warning = any(i.code == 'FLAG_INVALID_RANGE' for i in result.issues)
        log_result("FLAG_INVALID_RANGE検出", has_warning)


class TestValidationResult:
    """検証結果のテスト"""
    
    def test_result_properties(self):
        """検証結果のプロパティ確認"""
        print("\n--- 検証結果プロパティ ---")
        validator = CodeGenerationValidator()
        sm = create_valid_state_machine()
        gd = create_valid_global_defs()
        
        result = validator.validate(sm, gd)
        
        log_result("passed", hasattr(result, 'passed'))
        log_result("error_count", hasattr(result, 'error_count'))
        log_result("warning_count", hasattr(result, 'warning_count'))
        log_result("info_count", hasattr(result, 'info_count'))
        log_result("get_errors()", hasattr(result, 'get_errors'))
        log_result("get_warnings()", hasattr(result, 'get_warnings'))
        log_result("get_infos()", hasattr(result, 'get_infos'))
        log_result("get_by_category()", hasattr(result, 'get_by_category'))
        log_result("to_dict()", hasattr(result, 'to_dict'))
    
    def test_result_to_dict(self):
        """検証結果の辞書変換"""
        print("\n--- 検証結果の辞書変換 ---")
        validator = CodeGenerationValidator()
        sm = create_valid_state_machine()
        gd = create_valid_global_defs()
        
        result = validator.validate(sm, gd)
        data = result.to_dict()
        
        log_result("issuesキー", 'issues' in data)
        log_result("error_countキー", 'error_count' in data)
        log_result("warning_countキー", 'warning_count' in data)
        log_result("info_countキー", 'info_count' in data)
        log_result("passedキー", 'passed' in data)
        
        if 'issues' in data:
            log_result("issuesがリスト", isinstance(data['issues'], list))
            if data['issues']:
                issue = data['issues'][0]
                log_result("issue.category", 'category' in issue)
                log_result("issue.code", 'code' in issue)
                log_result("issue.message", 'message' in issue)
                log_result("issue.severity", 'severity' in issue)


class TestCategoryValidation:
    """カテゴリ別検証のテスト"""
    
    def test_validate_specific_categories(self):
        """特定カテゴリの検証"""
        print("\n--- カテゴリ別検証 ---")
        validator = CodeGenerationValidator()
        sm = create_valid_state_machine()
        gd = create_valid_global_defs()
        
        categories = validator.get_categories()
        log_result("カテゴリ取得", len(categories) >= 5, f"({len(categories)}カテゴリ)")
        
        for category in categories:
            issues = validator.validate_category(category, sm, gd)
            log_result(f"validate_category('{category}')", isinstance(issues, list), f"({len(issues)}件)")


def run_all_tests():
    """全テスト実行"""
    global PASS_COUNT, FAIL_COUNT, FAILED_ITEMS
    PASS_COUNT = 0
    FAIL_COUNT = 0
    FAILED_ITEMS = []
    
    print("=" * 60)
    print("検証機能 実データテスト")
    print("=" * 60)
    
    # 正常データテスト
    TestValidData().test_valid_data_no_errors()
    
    # 状態検証
    TestStateValidation().test_missing_initial_state()
    TestStateValidation().test_unreachable_state()
    
    # 遷移検証
    TestTransitionValidation().test_undefined_target()
    TestTransitionValidation().test_undefined_event()
    TestTransitionValidation().test_duplicate_transition()
    TestTransitionValidation().test_self_loop()
    
    # イベント検証
    TestEventValidation().test_unused_event()
    
    # ロール関数検証
    TestRoleFunctionValidation().test_unused_role_function()
    
    # 変数検証
    TestVariableValidation().test_duplicate_variable()
    TestVariableValidation().test_invalid_variable_type()
    
    # フラグ検証
    TestFlagValidation().test_duplicate_flag()
    TestFlagValidation().test_invalid_flag_range()
    
    # 検証結果
    TestValidationResult().test_result_properties()
    TestValidationResult().test_result_to_dict()
    
    # カテゴリ別検証
    TestCategoryValidation().test_validate_specific_categories()
    
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