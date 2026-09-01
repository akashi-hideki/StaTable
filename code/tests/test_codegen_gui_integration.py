# tests/test_codegen_gui_integration.py
"""
コード生成ダイアログからコード生成までの統合テスト
GUI操作→コード生成→保存→マージの一連のフローを検証する
"""

import sys
import os
import importlib.util
import pytest
import tempfile
import shutil

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
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_sample_data():
    """サンプルデータを取得"""
    sample_path = os.path.join(codegen_dir, "sample_data.py")
    sample_module = load_module("gui_test_sample", sample_path)
    return sample_module.SampleDataGenerator().get_sample_data()


def get_generator():
    """コード生成器を取得"""
    cgen_path = os.path.join(codegen_dir, "c_code_generator.py")
    cgen_module = load_module("gui_test_cgen", cgen_path)
    return cgen_module.CCodeGenerator()


def get_dialog():
    """コード生成ダイアログを取得"""
    dialog_path = os.path.join(gui_dir, "code_generation_dialog.py")
    dialog_module = load_module("gui_test_dialog", dialog_path)
    return dialog_module


# PyQt6 が利用可能かチェック
try:
    from PyQt6.QtWidgets import QApplication
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


@pytest.fixture(scope="module")
def qapp():
    """QApplication フィクスチャ"""
    if not PYQT_AVAILABLE:
        pytest.skip("PyQt6がインストールされていません")
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def temp_dir():
    """一時ディレクトリ"""
    dir_path = tempfile.mkdtemp(prefix="statable_test_")
    yield dir_path
    shutil.rmtree(dir_path, ignore_errors=True)


@pytest.fixture
def sample_data():
    """サンプルデータ"""
    return get_sample_data()


@pytest.fixture
def generator():
    """コード生成器"""
    return get_generator()


@pytest.fixture
def dialog(qapp, sample_data):
    """コード生成ダイアログ"""
    if not PYQT_AVAILABLE:
        pytest.skip("PyQt6がインストールされていません")
    
    dialog_module = get_dialog()
    sm, gd = sample_data
    dlg = dialog_module.CodeGenerationDialog(
        state_machine=sm,
        global_defs=gd
    )
    yield dlg
    dlg.close()


# ===== ダイアログ基本テスト =====
class TestDialogBasics:
    """ダイアログの基本テスト"""
    
    def test_dialog_creation(self, dialog):
        """ダイアログが作成できるか"""
        assert dialog is not None
        assert dialog.windowTitle() == "Cコード生成"
    
    def test_initial_state(self, dialog):
        """初期状態の確認"""
        assert dialog.generate_btn.isEnabled()
        assert not dialog.save_btn.isEnabled()
        assert not dialog.progress_bar.isVisible()
        assert dialog.preview_tabs.count() == 0
        assert dialog.generated_files == {}
    
    def test_sample_data_loaded(self, dialog):
        """サンプルデータがロードされているか"""
        assert dialog.state_machine is not None
        assert dialog.global_defs is not None
        assert len(dialog.state_machine.states) > 0
        assert len(dialog.state_machine.events) > 0
        assert len(dialog.global_defs.variables) > 0
        assert len(dialog.global_defs.flags) > 0
    
    def test_style_combo(self, dialog):
        """生成スタイルコンボの確認"""
        assert dialog.style_combo.count() >= 2
        assert dialog.style_combo.currentData() in ["table_driven", "switch_case"]


# ===== コード生成テスト =====
class TestCodeGeneration:
    """コード生成のテスト"""
    
    def test_generate_button_click(self, dialog, qapp):
        """生成ボタンクリックでコードが生成されるか"""
        # 生成ボタンをクリック
        dialog.generate_btn.click()
        
        # ワーカースレッドの完了を待つ
        if dialog.worker is not None:
            dialog.worker.wait(5000)
        
        # 生成結果を確認
        generated_files = dialog.get_generated_files()
        assert len(generated_files) == 11
        assert 'statable_types.h' in generated_files
        assert 'statable_transitions.c' in generated_files
        assert 'osal.h' in generated_files
        assert 'osal.c' in generated_files
    
    def test_generate_all_files_content(self, dialog, qapp):
        """生成された全ファイルの内容確認"""
        dialog.generate_btn.click()
        if dialog.worker is not None:
            dialog.worker.wait(5000)
        
        generated_files = dialog.get_generated_files()
        
        # 各ファイルが空でないか
        for filename, content in generated_files.items():
            assert len(content) > 0, f"{filename}が空"
        
        # 主要な内容の確認
        assert 'STATE_t' in generated_files['statable_types.h']
        assert 'StateMachine_Process' in generated_files['statable_transitions.c']
        assert 'RoleFunc_' in generated_files['statable_role_functions.c']
        assert 'OSAL_Status_t' in generated_files['osal.h']
    
    def test_preview_update(self, dialog, qapp):
        """プレビューが更新されるか"""
        dialog.generate_btn.click()
        if dialog.worker is not None:
            dialog.worker.wait(5000)
        
        # プレビュータブが11個あるか
        assert dialog.preview_tabs.count() == 11
        
        # 最初のタブを選択して内容確認
        dialog.preview_tabs.setCurrentIndex(0)
        preview_text = dialog.preview_text.toPlainText()
        assert len(preview_text) > 0
    
    def test_save_enabled_after_generation(self, dialog, qapp):
        """生成後に保存ボタンが有効になるか"""
        assert not dialog.save_btn.isEnabled()
        
        dialog.generate_btn.click()
        if dialog.worker is not None:
            dialog.worker.wait(5000)
        
        assert dialog.save_btn.isEnabled()
    
    def test_generation_error_handling(self, qapp):
        """生成エラーハンドリング"""
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        dialog_module = get_dialog()
        # 不正なデータでダイアログ作成
        dlg = dialog_module.CodeGenerationDialog(
            state_machine=None,
            global_defs=None
        )
        
        # サンプルデータがロードされるはず
        assert dlg.state_machine is not None
        assert dlg.global_defs is not None
        dlg.close()


# ===== 保存テスト =====
class TestSaveFunctionality:
    """保存機能のテスト"""
    
    def test_save_to_directory(self, dialog, qapp, temp_dir):
        """ディレクトリへの保存"""
        dialog.generate_btn.click()
        if dialog.worker is not None:
            dialog.worker.wait(5000)
        
        # 出力先を設定
        dialog.output_dir_edit.setText(temp_dir)
        
        # 保存ボタンをクリック
        dialog.save_btn.click()
        
        # ファイルが保存されているか
        expected_files = [
            'statable_types.h', 'statable_transitions.h',
            'statable_transitions.c', 'statable_role_functions.h',
            'statable_role_functions.c', 'statable_init.c',
            'statable_event_queue.c', 'statable_interrupt.c',
            'statable_timer.c', 'osal.h', 'osal.c',
        ]
        
        for filename in expected_files:
            filepath = os.path.join(temp_dir, filename)
            assert os.path.exists(filepath), f"{filename}が保存されていない"
    
    def test_save_without_output_dir(self, dialog, qapp):
        """出力先未設定での保存"""
        dialog.generate_btn.click()
        if dialog.worker is not None:
            dialog.worker.wait(5000)
        
        # 出力先をクリア
        dialog.output_dir_edit.setText("")
        
        # 保存ボタンをクリック（警告が表示されるはず）
        dialog.save_btn.click()
        
        # エラーが発生しないこと
        assert True
    

# ===== マージ機能テスト =====
class TestMergeFunctionality:
    """マージ機能のテスト"""
    
    def test_merge_save(self, dialog, qapp, temp_dir):
        """マージ保存のテスト"""
        dialog.generate_btn.click()
        if dialog.worker is not None:
            dialog.worker.wait(5000)
        
        dialog.output_dir_edit.setText(temp_dir)
        
        # 1回目の保存
        dialog.save_btn.click()
        
        # ユーザーコードを追加
        role_func_path = os.path.join(temp_dir, 'statable_role_functions.c')
        with open(role_func_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        user_code = '    ctx->flags.EVT_POWER_ON_REQ = 1;  // ユーザー実装'
        content = content.replace(
            '    // ユーザー実装コードをここに記述',
            user_code
        )
        
        with open(role_func_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 2回目の生成
        dialog.generate_btn.click()
        if dialog.worker is not None:
            dialog.worker.wait(5000)
        
        # マージ保存
        dialog.save_btn.click()
        
        # ユーザーコードが保持されているか
        with open(role_func_path, 'r', encoding='utf-8') as f:
            merged_content = f.read()
        
        assert 'ctx->flags.EVT_POWER_ON_REQ = 1;' in merged_content
    

# ===== 設定ダイアログテスト =====
class TestSettingsDialog:
    """設定ダイアログのテスト"""
    
    def test_settings_dialog_creation(self, qapp):
        """設定ダイアログが作成できるか"""
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        settings_path = os.path.join(gui_dir, "code_generation_settings_dialog.py")
        settings_module = load_module("gui_test_settings", settings_path)
        
        dlg = settings_module.CodeGenerationSettingsDialog()
        assert dlg is not None
        assert dlg.windowTitle() == "コード生成設定"
        dlg.close()
    
    def test_settings_default_values(self, qapp):
        """設定のデフォルト値確認"""
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        settings_path = os.path.join(gui_dir, "code_generation_settings_dialog.py")
        settings_module = load_module("gui_test_settings2", settings_path)
        
        dlg = settings_module.CodeGenerationSettingsDialog()
        
        assert dlg.style_combo.currentData() == "table_driven"
        assert dlg.table_type_combo.currentData() == "array"
        assert dlg.os_type_combo.currentData() == "non_rtos"
        assert dlg.enable_debug_logs_check.isChecked()
        assert dlg.enable_info_logs_check.isChecked()
        assert dlg.enable_error_logs_check.isChecked()
        assert dlg.save_with_merge_check.isChecked()
        
        dlg.close()
    
    def test_settings_change(self, qapp):
        """設定変更のテスト"""
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        settings_path = os.path.join(gui_dir, "code_generation_settings_dialog.py")
        settings_module = load_module("gui_test_settings3", settings_path)
        
        dlg = settings_module.CodeGenerationSettingsDialog()
        
        # 設定を変更
        dlg.style_combo.setCurrentIndex(dlg.style_combo.findData("switch_case"))
        dlg.os_type_combo.setCurrentIndex(dlg.os_type_combo.findData("freertos"))
        dlg.enable_debug_logs_check.setChecked(False)
        
        # OKボタン
        dlg._on_ok()
        
        # 設定が保存されているか
        config = dlg.get_config()
        assert config.generation_style == "switch_case"
        assert config.os_type == "freertos"
        assert config.enable_debug_logs is False
        
        dlg.close()


# ===== エンドツーエンドテスト =====
class TestEndToEnd:
    """エンドツーエンドテスト"""
    
    def test_full_flow(self, qapp, temp_dir, sample_data):
        """完全なフロー: 設定→生成→保存→マージ"""
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        dialog_module = get_dialog()
        sm, gd = sample_data
        
        # 1. ダイアログ作成
        dlg = dialog_module.CodeGenerationDialog(
            state_machine=sm,
            global_defs=gd
        )
        
        # 2. 生成スタイルを設定
        dlg.style_combo.setCurrentIndex(dlg.style_combo.findData("table_driven"))
        
        # 3. コード生成
        dlg.generate_btn.click()
        if dlg.worker is not None:
            dlg.worker.wait(5000)
        
        generated_files = dlg.get_generated_files()
        assert len(generated_files) == 11
        
        # 4. 出力先設定
        dlg.output_dir_edit.setText(temp_dir)
        
        # 5. 保存
        dlg.save_btn.click()
        
        # 6. ファイル確認
        assert os.path.exists(os.path.join(temp_dir, 'statable_types.h'))
        assert os.path.exists(os.path.join(temp_dir, 'osal.c'))
        
        # 7. ユーザーコード追加
        role_func_path = os.path.join(temp_dir, 'statable_role_functions.c')
        with open(role_func_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = content.replace(
            '    // ユーザー実装コードをここに記述',
            '    // カスタム実装\n    ctx->flags.EVT_POWER_ON_REQ = 1;'
        )
        with open(role_func_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 8. 再生成
        dlg.generate_btn.click()
        if dlg.worker is not None:
            dlg.worker.wait(5000)
        
        # 9. マージ保存
        dlg.save_btn.click()
        
        # 10. ユーザーコード保持確認
        with open(role_func_path, 'r', encoding='utf-8') as f:
            final_content = f.read()
        assert 'ctx->flags.EVT_POWER_ON_REQ = 1;' in final_content
        
        dlg.close()
    
    def test_full_flow_with_custom_settings(self, qapp, temp_dir, sample_data):
        """カスタム設定での完全フロー"""
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        dialog_module = get_dialog()
        sm, gd = sample_data
        
        dlg = dialog_module.CodeGenerationDialog(
            state_machine=sm,
            global_defs=gd
        )
        
        # 生成スタイルをswitch_caseに変更
        dlg.style_combo.setCurrentIndex(dlg.style_combo.findData("switch_case"))
        
        # 生成
        dlg.generate_btn.click()
        if dlg.worker is not None:
            dlg.worker.wait(5000)
        
        generated_files = dlg.get_generated_files()
        assert len(generated_files) == 11
        
        # switch-case方式の特徴を確認
        transitions_content = generated_files['statable_transitions.c']
        assert 'switch' in transitions_content
        
        dlg.close()


# ===== 実行 =====
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])