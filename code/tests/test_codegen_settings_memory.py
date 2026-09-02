# tests/test_codegen_settings_memory.py
"""
コード生成設定の記憶機能テスト
前回の出力先が記憶されているかを検証する
"""

import sys
import os
import json
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


def get_dialog_module():
    """ダイアログモジュールを取得"""
    dialog_path = os.path.join(gui_dir, "code_generation_dialog.py")
    return load_module("settings_memory_dialog", dialog_path)


def get_sample_data():
    """サンプルデータを取得"""
    sample_path = os.path.join(codegen_dir, "sample_data.py")
    sample_module = load_module("settings_memory_sample", sample_path)
    return sample_module.SampleDataGenerator().get_sample_data()


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
def temp_settings_file():
    """一時設定ファイルのパスを提供"""
    temp_dir = tempfile.mkdtemp(prefix="settings_test_")
    temp_file = os.path.join(temp_dir, "codegen_settings.json")
    
    yield temp_file
    
    # クリーンアップ
    if os.path.exists(temp_file):
        os.remove(temp_file)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_data():
    """サンプルデータ"""
    return get_sample_data()


@pytest.fixture
def dialog(qapp, sample_data, temp_settings_file):
    """ダイアログのフィクスチャ（settings_fileを直接渡す）"""
    if not PYQT_AVAILABLE:
        pytest.skip("PyQt6がインストールされていません")
    
    dialog_module = get_dialog_module()
    sm, gd = sample_data
    dlg = dialog_module.CodeGenerationDialog(
        state_machine=sm,
        global_defs=gd,
        settings_file=temp_settings_file
    )
    yield dlg
    dlg.close()


def create_dialog(qapp, sample_data, settings_file):
    """ダイアログを作成するヘルパー"""
    if not PYQT_AVAILABLE:
        pytest.skip("PyQt6がインストールされていません")
    
    dialog_module = get_dialog_module()
    sm, gd = sample_data
    return dialog_module.CodeGenerationDialog(
        state_machine=sm,
        global_defs=gd,
        settings_file=settings_file
    )


# ===== 設定記憶テスト =====
class TestSettingsMemory:
    """設定記憶機能のテスト"""
    
    def test_initial_no_settings(self, temp_settings_file):
        """初回起動時は設定ファイルが存在しない"""
        assert not os.path.exists(temp_settings_file)
    
    def test_save_output_dir(self, qapp, sample_data, temp_settings_file):
        """出力先を設定して保存"""
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        dlg = create_dialog(qapp, sample_data, temp_settings_file)
        
        test_dir = os.path.join(tempfile.gettempdir(), "statable_output_test")
        dlg.output_dir_edit.setText(test_dir)
        
        dlg._save_settings()
        dlg.close()
        
        assert os.path.exists(temp_settings_file), f"設定ファイルが作成されていない: {temp_settings_file}"
        
        with open(temp_settings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert data['output_directory'] == test_dir
    
    def test_load_output_dir_on_restart(self, qapp, sample_data, temp_settings_file):
        """2回目の起動で前回の出力先が復元されるか"""
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        # 1回目
        dlg1 = create_dialog(qapp, sample_data, temp_settings_file)
        test_dir = os.path.join(tempfile.gettempdir(), "statable_output_test2")
        dlg1.output_dir_edit.setText(test_dir)
        dlg1._save_settings()
        dlg1.close()
        
        # 2回目
        dlg2 = create_dialog(qapp, sample_data, temp_settings_file)
        
        assert dlg2.output_dir_edit.text() == test_dir
        assert dlg2.get_config().output_directory == test_dir
        
        dlg2.close()
    
    def test_save_style(self, qapp, sample_data, temp_settings_file):
        """生成スタイルを保存して復元"""
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        # 1回目
        dlg1 = create_dialog(qapp, sample_data, temp_settings_file)
        idx = dlg1.style_combo.findData("switch_case")
        dlg1.style_combo.setCurrentIndex(idx)
        dlg1._save_settings()
        dlg1.close()
        
        # 設定ファイル確認
        with open(temp_settings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert data['generation_style'] == 'switch_case'
        
        # 2回目
        dlg2 = create_dialog(qapp, sample_data, temp_settings_file)
        assert dlg2.style_combo.currentData() == 'switch_case'
        assert dlg2.get_config().generation_style == 'switch_case'
        dlg2.close()
    
    def test_save_all_settings(self, qapp, sample_data, temp_settings_file):
        """全設定を保存して復元"""
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        # 1回目
        dlg1 = create_dialog(qapp, sample_data, temp_settings_file)
        test_dir = os.path.join(tempfile.gettempdir(), "statable_output_test3")
        dlg1.output_dir_edit.setText(test_dir)
        
        idx = dlg1.style_combo.findData("switch_case")
        dlg1.style_combo.setCurrentIndex(idx)
        
        dlg1.config_manager.update(os_type="freertos")
        dlg1.config_manager.update(save_with_merge=False)
        dlg1._save_settings()
        dlg1.close()
        
        # 設定ファイル確認
        with open(temp_settings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['output_directory'] == test_dir
        assert data['generation_style'] == 'switch_case'
        assert data['os_type'] == 'freertos'
        assert data['save_with_merge'] == False
        
        # 2回目
        dlg2 = create_dialog(qapp, sample_data, temp_settings_file)
        config = dlg2.get_config()
        
        assert config.output_directory == test_dir
        assert config.generation_style == 'switch_case'
        assert config.os_type == 'freertos'
        assert config.save_with_merge == False
        
        assert dlg2.output_dir_edit.text() == test_dir
        assert dlg2.style_combo.currentData() == 'switch_case'
        
        dlg2.close()
    
    def test_settings_dialog_remembers_output_dir(self, qapp, sample_data, temp_settings_file):
        """設定ダイアログに前回の出力先が表示されるか"""
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        # 1回目
        dlg1 = create_dialog(qapp, sample_data, temp_settings_file)
        test_dir = os.path.join(tempfile.gettempdir(), "statable_output_test4")
        dlg1.output_dir_edit.setText(test_dir)
        dlg1._save_settings()
        dlg1.close()
        
        # 2回目
        dlg2 = create_dialog(qapp, sample_data, temp_settings_file)
        config = dlg2.get_config()
        assert config.output_directory == test_dir
        
        dlg2.close()


# ===== 設定ファイルの内容テスト =====
class TestSettingsFileFormat:
    """設定ファイルのフォーマットテスト"""
    
    def test_settings_file_format(self, qapp, sample_data, temp_settings_file):
        """設定ファイルが正しいJSONフォーマットか"""
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        dlg = create_dialog(qapp, sample_data, temp_settings_file)
        dlg._save_settings()
        dlg.close()
        
        assert os.path.exists(temp_settings_file), "設定ファイルが作成されていない"
        
        with open(temp_settings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'output_directory' in data
        assert 'generation_style' in data
        assert 'os_type' in data
        assert 'save_with_merge' in data
    
    def test_settings_file_corrupted(self, qapp, sample_data, temp_settings_file):
        """設定ファイルが壊れていても動作するか"""
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        # 壊れたJSONを書き込む
        os.makedirs(os.path.dirname(temp_settings_file), exist_ok=True)
        with open(temp_settings_file, 'w', encoding='utf-8') as f:
            f.write("{invalid json}")
        
        # エラーにならずにダイアログが作成されるか
        dlg = create_dialog(qapp, sample_data, temp_settings_file)
        assert dlg is not None
        dlg.close()


# ===== 設定記憶と生成の統合テスト =====
class TestSettingsMemoryIntegration:
    """設定記憶とコード生成の統合テスト"""
    
    def test_generate_with_remembered_settings(self, qapp, sample_data, temp_settings_file):
        """記憶された設定でコード生成できるか"""
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        # 1回目: 出力先を設定
        dlg1 = create_dialog(qapp, sample_data, temp_settings_file)
        test_dir = tempfile.mkdtemp(prefix="statable_gen_test_")
        dlg1.output_dir_edit.setText(test_dir)
        dlg1._save_settings()
        dlg1.close()
        
        # 2回目: 復元された設定で生成
        dlg2 = create_dialog(qapp, sample_data, temp_settings_file)
        
        # 出力先が復元されているか
        assert dlg2.output_dir_edit.text() == test_dir
        
        # コード生成
        dlg2._generate_code()
        
        # 生成結果の確認
        generated_files = dlg2.get_generated_files()
        assert len(generated_files) == 11
        
        dlg2.close()
        
        # クリーンアップ
        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])