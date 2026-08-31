# tests/test_codegen_complete.py
"""
コード生成モジュールの完全統合テスト
全フェーズ（1-6）の機能を網羅的に検証する
"""

import sys
import os
import importlib.util
import pytest

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
codegen_dir = os.path.join(project_root, 'codegen')
statable_dir = os.path.join(project_root, 'statable')

sys.path.insert(0, codegen_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, statable_dir)


def load_module(name, path):
    """モジュールをファイルパスからロード"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_sample_data():
    """サンプルデータを取得"""
    sample_path = os.path.join(codegen_dir, "sample_data.py")
    sample_module = load_module("complete_sample", sample_path)
    return sample_module.SampleDataGenerator().get_sample_data()


def get_generator():
    """コード生成器を取得"""
    cgen_path = os.path.join(codegen_dir, "c_code_generator.py")
    cgen_module = load_module("complete_cgen", cgen_path)
    return cgen_module.CCodeGenerator()


@pytest.fixture(scope="module")
def sample_data():
    """サンプルデータフィクスチャ"""
    return get_sample_data()


@pytest.fixture(scope="module")
def generator():
    """コード生成器フィクスチャ"""
    return get_generator()


@pytest.fixture(scope="module")
def generated_files(sample_data, generator):
    """生成ファイルフィクスチャ"""
    sm, gd = sample_data
    return generator.generate_all(sm, gd)


# ===== フェーズ1: 基本データ型・構造体生成テスト =====
class TestPhase1BasicTypes:
    """フェーズ1: 基本データ型・構造体生成"""
    
    def test_types_header_generated(self, generated_files):
        assert 'statable_types.h' in generated_files
    
    def test_state_enum(self, generated_files):
        content = generated_files['statable_types.h']
        assert 'STATE_t' in content
        assert 'STATE_INIT' in content
        assert 'STATE_MAX' in content
    
    def test_event_enum(self, generated_files):
        content = generated_files['statable_types.h']
        assert 'EVENT_t' in content
        assert 'EVENT_POWER_ON' in content
        assert 'EVENT_MAX' in content
    
    def test_flag_enum(self, generated_files):
        content = generated_files['statable_types.h']
        assert 'FLAG_t' in content
        assert 'FLAG_MAX' in content
    
    def test_custom_types(self, generated_files):
        content = generated_files['statable_types.h']
        assert 'SystemStatus_t' in content
        assert 'SensorData_t' in content
    
    def test_system_structs(self, generated_files):
        content = generated_files['statable_types.h']
        assert 'SystemData_t' in content
        assert 'EventFlags_t' in content
        assert 'SystemContext_t' in content
    
    def test_bitfield(self, generated_files):
        content = generated_files['statable_types.h']
        assert ': 1' in content  # ビットフィールド
    
    def test_array(self, generated_files):
        content = generated_files['statable_types.h']
        assert '[64]' in content  # 配列
    
    def test_macros(self, generated_files):
        content = generated_files['statable_types.h']
        assert 'DATA_' in content
        assert 'FLAG_' in content


# ===== フェーズ2: 状態遷移ロジック生成テスト =====
class TestPhase2Transitions:
    """フェーズ2: 状態遷移ロジック生成"""
    
    def test_transitions_header(self, generated_files):
        assert 'statable_transitions.h' in generated_files
    
    def test_transitions_source(self, generated_files):
        assert 'statable_transitions.c' in generated_files
    
    def test_state_machine_process_decl(self, generated_files):
        content = generated_files['statable_transitions.h']
        assert 'StateMachine_Process' in content
        assert 'STATE_t current_state' in content
        assert 'EVENT_t event' in content
        assert 'SystemContext_t *ctx' in content
    
    def test_transition_table(self, generated_files):
        content = generated_files['statable_transitions.c']
        assert 'transition_matrix' in content
        assert 'TransitionCell_t' in content
    
    def test_state_machine_process_impl(self, generated_files):
        content = generated_files['statable_transitions.c']
        assert 'StateMachine_Process' in content
        assert 'return next_state' in content
    
    def test_null_check(self, generated_files):
        content = generated_files['statable_transitions.c']
        assert 'ctx == NULL' in content
    
    def test_range_check(self, generated_files):
        content = generated_files['statable_transitions.c']
        assert 'STATE_MAX' in content
        assert 'EVENT_MAX' in content
    
    def test_debug_logs(self, generated_files):
        content = generated_files['statable_transitions.c']
        assert 'LOG_DEBUG' in content
        assert 'LOG_INFO' in content
        assert 'LOG_ERROR' in content


# ===== フェーズ3: ロール関数生成テスト =====
class TestPhase3RoleFunctions:
    """フェーズ3: ロール関数生成"""
    
    def test_role_functions_header(self, generated_files):
        assert 'statable_role_functions.h' in generated_files
    
    def test_role_functions_source(self, generated_files):
        assert 'statable_role_functions.c' in generated_files
    
    def test_all_role_functions_declared(self, generated_files):
        content = generated_files['statable_role_functions.h']
        assert 'RoleFunc_PowerOn' in content
        assert 'RoleFunc_StartOk' in content
        assert 'RoleFunc_Start' in content
        assert 'RoleFunc_Stop' in content
        assert 'RoleFunc_HandleError' in content
        assert 'RoleFunc_ProcessData' in content
    
    def test_all_role_functions_implemented(self, generated_files):
        content = generated_files['statable_role_functions.c']
        assert 'RoleFunc_PowerOn' in content
        assert 'RoleFunc_StartOk' in content
        assert 'RoleFunc_ProcessData' in content
    
    def test_todo_comments(self, generated_files):
        content = generated_files['statable_role_functions.c']
        assert 'TODO' in content
    
    def test_unused_arg_suppression(self, generated_files):
        content = generated_files['statable_role_functions.c']
        assert '(void)current_state' in content
        assert '(void)ctx' in content
    
    def test_user_markers(self, generated_files):
        content = generated_files['statable_role_functions.c']
        assert 'STABLE_USER_CODE_START' in content
        assert 'STABLE_USER_CODE_END' in content
    
    def test_args_with_custom_params(self, generated_files):
        content = generated_files['statable_role_functions.c']
        assert '(void)data' in content
        assert '(void)len' in content


# ===== フェーズ4: イベントキュー・割り込み処理テスト =====
class TestPhase4EventQueueInterrupt:
    """フェーズ4: イベントキュー・割り込み処理"""
    
    def test_event_queue_source(self, generated_files):
        assert 'statable_event_queue.c' in generated_files
    
    def test_interrupt_source(self, generated_files):
        assert 'statable_interrupt.c' in generated_files
    
    def test_event_queue_struct(self, generated_files):
        content = generated_files['statable_event_queue.c']
        assert 'typedef struct' in content
        assert 'EventQueue' in content
    
    def test_event_queue_functions(self, generated_files):
        content = generated_files['statable_event_queue.c']
        assert 'Enqueue' in content
        assert 'Dequeue' in content
    
    def test_isr_generation(self, generated_files):
        content = generated_files['statable_interrupt.c']
        assert 'ISR_' in content
    
    def test_isr_actions(self, generated_files):
        content = generated_files['statable_interrupt.c']
        assert 'EVT_START_REQ' in content or 'system_tick' in content


# ===== フェーズ5: タイマ変数生成テスト =====
class TestPhase5Timer:
    """フェーズ5: タイマ変数生成"""
    
    def test_timer_source(self, generated_files):
        assert 'statable_timer.c' in generated_files
    
    def test_timer_struct(self, generated_files):
        content = generated_files['statable_timer.c']
        assert 'TimerVariables_t' in content
    
    def test_timer_base_variable(self, generated_files):
        content = generated_files['statable_timer.c']
        assert 'g_system_tick' in content
    
    def test_timer_derived_variables(self, generated_files):
        content = generated_files['statable_timer.c']
        assert 'g_tick_10ms' in content
        assert 'g_tick_100ms' in content
    
    def test_timer_init_function(self, generated_files):
        content = generated_files['statable_timer.c']
        assert 'Timer_Init' in content
    
    def test_timer_update_function(self, generated_files):
        content = generated_files['statable_timer.c']
        assert 'Timer_Update' in content


# ===== フェーズ6: OSAL生成テスト =====
class TestPhase6OSAL:
    """フェーズ6: OSAL生成"""
    
    def test_osal_header(self, generated_files):
        assert 'osal.h' in generated_files
    
    def test_osal_source(self, generated_files):
        assert 'osal.c' in generated_files
    
    def test_osal_types(self, generated_files):
        content = generated_files['osal.h']
        assert 'OSAL_Status_t' in content
        assert 'OSAL_Mutex_t' in content
        assert 'OSAL_Semaphore_t' in content
        assert 'OSAL_Queue_t' in content
    
    def test_osal_mutex_functions(self, generated_files):
        content = generated_files['osal.h']
        assert 'OSAL_Mutex_Create' in content
        assert 'OSAL_Mutex_Lock' in content
        assert 'OSAL_Mutex_Unlock' in content
    
    def test_osal_semaphore_functions(self, generated_files):
        content = generated_files['osal.h']
        assert 'OSAL_Semaphore_Create' in content
        assert 'OSAL_Semaphore_Take' in content
        assert 'OSAL_Semaphore_Give' in content
    
    def test_osal_queue_functions(self, generated_files):
        content = generated_files['osal.h']
        assert 'OSAL_Queue_Create' in content
        assert 'OSAL_Queue_Send' in content
        assert 'OSAL_Queue_Receive' in content
    
    def test_osal_critical_section(self, generated_files):
        content = generated_files['osal.h']
        assert 'OSAL_Critical_Enter' in content
        assert 'OSAL_Critical_Exit' in content
    
    def test_osal_mutex_impl(self, generated_files):
        content = generated_files['osal.c']
        assert 'OSAL_Mutex_Create' in content
        assert 'mutex->locked' in content
    
    def test_osal_semaphore_impl(self, generated_files):
        content = generated_files['osal.c']
        assert 'OSAL_Semaphore_Create' in content
        assert 'sem->count' in content
    
    def test_osal_queue_impl(self, generated_files):
        content = generated_files['osal.c']
        assert 'OSAL_Queue_Create' in content
        assert 'queue->count' in content


# ===== 初期化処理テスト =====
class TestInitSource:
    """初期化処理テスト"""
    
    def test_init_source(self, generated_files):
        assert 'statable_init.c' in generated_files
    
    def test_system_context_init(self, generated_files):
        content = generated_files['statable_init.c']
        assert 'SystemContext_Init' in content
    
    def test_variable_init(self, generated_files):
        content = generated_files['statable_init.c']
        assert 'ctx->data' in content
    
    def test_flag_init(self, generated_files):
        content = generated_files['statable_init.c']
        assert 'ctx->flags' in content


# ===== 総合テスト =====
class TestCompleteGeneration:
    """総合テスト"""
    
    def test_total_file_count(self, generated_files):
        """11ファイルが生成されるか"""
        assert len(generated_files) == 11
    
    def test_expected_files_present(self, generated_files):
        """全ファイルが存在するか"""
        expected = [
            'statable_types.h',
            'statable_transitions.h',
            'statable_transitions.c',
            'statable_role_functions.h',
            'statable_role_functions.c',
            'statable_init.c',
            'statable_event_queue.c',
            'statable_interrupt.c',
            'statable_timer.c',
            'osal.h',
            'osal.c',
        ]
        for filename in expected:
            assert filename in generated_files, f"{filename}が生成されていない"
    
    def test_all_files_non_empty(self, generated_files):
        """全ファイルが空でないか"""
        for filename, content in generated_files.items():
            assert len(content) > 0, f"{filename}が空"
    
    def test_all_files_string(self, generated_files):
        """全ファイルが文字列型か"""
        for filename, content in generated_files.items():
            assert isinstance(content, str), f"{filename}が文字列型でない"
    
    def test_save_all_files(self, generated_files, generator, tmp_path):
        """全ファイル保存テスト"""
        saved = generator.save_generated_code(generated_files, str(tmp_path))
        assert len(saved) == 11
    
    def test_merge_save_all_files(self, generated_files, generator, tmp_path):
        """マージ保存テスト"""
        saved = generator.save_generated_code_with_merge(generated_files, str(tmp_path))
        assert len(saved) == 11


# ===== マージ機能テスト =====
class TestMergeFunctionality:
    """マージ機能テスト"""
    
    def test_merge_new_files(self, generated_files, generator, tmp_path):
        """新規ファイルのマージ保存"""
        saved = generator.save_generated_code_with_merge(generated_files, str(tmp_path))
        assert len(saved) == 11
    
    def test_merge_existing_with_user_code(self, generated_files, generator, tmp_path):
        """既存ファイル（ユーザーコードあり）のマージ"""
        # 1回目の保存
        generator.save_generated_code(generated_files, str(tmp_path))
        
        # ユーザーコードを追加
        role_func_path = os.path.join(str(tmp_path), 'statable_role_functions.c')
        with open(role_func_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        user_code = '    ctx->flags.EVT_POWER_ON_REQ = 1;  // ユーザー実装'
        content = content.replace(
            '    // ユーザー実装コードをここに記述',
            user_code
        )
        
        with open(role_func_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 2回目の保存（マージ）
        merged = generator.save_generated_code_with_merge(generated_files, str(tmp_path))
        assert len(merged) == 11
        
        # ユーザーコードが保持されているか
        with open(role_func_path, 'r', encoding='utf-8') as f:
            merged_content = f.read()
        assert 'ctx->flags.EVT_POWER_ON_REQ = 1;' in merged_content
    
    def test_merge_summary(self, generated_files, generator, tmp_path):
        """マージサマリーテスト"""
        generator.save_generated_code(generated_files, str(tmp_path))
        summary = generator.get_merge_summary(generated_files, str(tmp_path))
        assert len(summary) == 11
        for filename, info in summary.items():
            assert 'file_user_code' in info
            assert 'func_user_codes' in info


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])