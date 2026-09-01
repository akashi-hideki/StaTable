# tests/test_codegen_settings_memory.py
"""
コード生成設定の記憶機能テスト
前回の出力先が記憶されているかを検証する
設定ダイアログの表示テストを含む
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


def get_settings_dialog_module():
    """設定ダイアログモジュールを取得"""
    settings_path = os.path.join(gui_dir, "code_generation_settings_dialog.py")
    if os.path.exists(settings_path):
        return load_module("settings_dialog_module", settings_path)
    return None


def get_sample_data():
    """サンプルデータを取得"""
    sample_path = os.path.join(codegen_dir, "sample_data.py")
    sample_module = load_module("settings_memory_sample", sample_path)
    return sample_module.SampleDataGenerator().get_sample_data()


# PyQt6 が利用可能かチェック
try:
    from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox, QFileDialog
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
    
    if os.path.exists(temp_file):
        os.remove(temp_file)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_data():
    """サンプルデータ"""
    return get_sample_data()


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
        assert not os.path.exists(temp_settings_file)
    
    def test_save_output_dir(self, qapp, sample_data, temp_settings_file):
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        dlg = create_dialog(qapp, sample_data, temp_settings_file)
        test_dir = os.path.join(tempfile.gettempdir(), "statable_output_test")
        dlg.output_dir_edit.setText(test_dir)
        dlg._save_settings()
        dlg.close()
        
        assert os.path.exists(temp_settings_file)
        
        with open(temp_settings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert data['output_directory'] == test_dir
    
    def test_load_output_dir_on_restart(self, qapp, sample_data, temp_settings_file):
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        dlg1 = create_dialog(qapp, sample_data, temp_settings_file)
        test_dir = os.path.join(tempfile.gettempdir(), "statable_output_test2")
        dlg1.output_dir_edit.setText(test_dir)
        dlg1._save_settings()
        dlg1.close()
        
        dlg2 = create_dialog(qapp, sample_data, temp_settings_file)
        assert dlg2.output_dir_edit.text() == test_dir
        assert dlg2.get_config().output_directory == test_dir
        dlg2.close()
    
    def test_save_style(self, qapp, sample_data, temp_settings_file):
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        dlg1 = create_dialog(qapp, sample_data, temp_settings_file)
        idx = dlg1.style_combo.findData("switch_case")
        dlg1.style_combo.setCurrentIndex(idx)
        dlg1._save_settings()
        dlg1.close()
        
        with open(temp_settings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert data['generation_style'] == 'switch_case'
        
        dlg2 = create_dialog(qapp, sample_data, temp_settings_file)
        assert dlg2.style_combo.currentData() == 'switch_case'
        dlg2.close()
    
    def test_save_all_settings(self, qapp, sample_data, temp_settings_file):
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        dlg1 = create_dialog(qapp, sample_data, temp_settings_file)
        test_dir = os.path.join(tempfile.gettempdir(), "statable_output_test3")
        dlg1.output_dir_edit.setText(test_dir)
        
        idx = dlg1.style_combo.findData("switch_case")
        dlg1.style_combo.setCurrentIndex(idx)
        
        dlg1.config_manager.update(os_type="freertos")
        dlg1.config_manager.update(save_with_merge=False)
        dlg1._save_settings()
        dlg1.close()
        
        with open(temp_settings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['output_directory'] == test_dir
        assert data['generation_style'] == 'switch_case'
        assert data['os_type'] == 'freertos'
        assert data['save_with_merge'] == False
        
        dlg2 = create_dialog(qapp, sample_data, temp_settings_file)
        config = dlg2.get_config()
        assert config.output_directory == test_dir
        assert config.generation_style == 'switch_case'
        assert config.os_type == 'freertos'
        assert config.save_with_merge == False
        dlg2.close()
    
    def test_settings_dialog_remembers_output_dir(self, qapp, sample_data, temp_settings_file):
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        dlg1 = create_dialog(qapp, sample_data, temp_settings_file)
        test_dir = os.path.join(tempfile.gettempdir(), "statable_output_test4")
        dlg1.output_dir_edit.setText(test_dir)
        dlg1._save_settings()
        dlg1.close()
        
        dlg2 = create_dialog(qapp, sample_data, temp_settings_file)
        config = dlg2.get_config()
        assert config.output_directory == test_dir
        dlg2.close()


# ===== 設定ファイルの内容テスト =====
class TestSettingsFileFormat:
    """設定ファイルのフォーマットテスト"""
    
    def test_settings_file_format(self, qapp, sample_data, temp_settings_file):
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        dlg = create_dialog(qapp, sample_data, temp_settings_file)
        dlg._save_settings()
        dlg.close()
        
        assert os.path.exists(temp_settings_file)
        
        with open(temp_settings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'output_directory' in data
        assert 'generation_style' in data
        assert 'os_type' in data
        assert 'save_with_merge' in data
    
    def test_settings_file_corrupted(self, qapp, sample_data, temp_settings_file):
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        os.makedirs(os.path.dirname(temp_settings_file), exist_ok=True)
        with open(temp_settings_file, 'w', encoding='utf-8') as f:
            f.write("{invalid json}")
        
        dlg = create_dialog(qapp, sample_data, temp_settings_file)
        assert dlg is not None
        dlg.close()


# ===== 設定ダイアログ表示テスト =====
class TestSettingsDialogDisplay:
    """設定ダイアログの表示テスト"""
    
    def test_settings_dialog_module_exists(self):
        """設定ダイアログモジュールが存在するか"""
        settings_module = get_settings_dialog_module()
        if settings_module is None:
            pytest.skip("設定ダイアログが存在しません")
        assert hasattr(settings_module, 'CodeGenerationSettingsDialog')
    
    def test_settings_dialog_creation(self, qapp):
        """設定ダイアログが作成できるか"""
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        settings_module = get_settings_dialog_module()
        if settings_module is None:
            pytest.skip("設定ダイアログが存在しません")
        
        dlg = settings_module.CodeGenerationSettingsDialog()
        assert dlg is not None
        assert dlg.windowTitle() == "コード生成設定"
        dlg.close()
    
    def test_settings_dialog_show(self, qapp):
        """設定ダイアログが表示できるか（非モーダル）"""
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        settings_module = get_settings_dialog_module()
        if settings_module is None:
            pytest.skip("設定ダイアログが存在しません")
        
        dlg = settings_module.CodeGenerationSettingsDialog()
        dlg.show()
        qapp.processEvents()
        assert dlg.isVisible()
        dlg.hide()
        dlg.close()
    
    def test_codegen_dialog_opens_settings(self, qapp, sample_data, temp_settings_file, monkeypatch):
        """コード生成ダイアログから設定ダイアログが開けるか"""
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        dlg = create_dialog(qapp, sample_data, temp_settings_file)
        
        # _open_settings_dialog をモック化
        called = {'count': 0}
        
        def mock_open_settings():
            called['count'] += 1
        
        monkeypatch.setattr(dlg, '_open_settings_dialog', mock_open_settings)
        
        # 設定ボタンをクリック
        dlg.settings_btn.click()
        
        assert called['count'] == 1, f"設定ダイアログが開かれていない (count={called['count']})"
        
        dlg.close()
    
    def test_generate_opens_settings_when_no_output_dir(self, qapp, sample_data, temp_settings_file, monkeypatch):
        """出力先未設定時に生成すると設定ダイアログが開くか"""
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        dlg = create_dialog(qapp, sample_data, temp_settings_file)
        
        # 出力先を空にする
        dlg.output_dir_edit.setText("")
        dlg.config_manager.update(output_directory="")
        
        # _select_output_dir をモック化
        called = {'count': 0}
        
        def mock_select_output_dir():
            called['count'] += 1
            # 出力先を設定
            dlg.output_dir_edit.setText(tempfile.gettempdir())
            dlg.config_manager.update(output_directory=tempfile.gettempdir())
        
        monkeypatch.setattr(dlg, '_select_output_dir', mock_select_output_dir)
        
        # QMessageBox.warning をモック化
        monkeypatch.setattr(QMessageBox, 'warning', lambda *args, **kwargs: QMessageBox.StandardButton.Ok)
        # QMessageBox.information をモック化
        monkeypatch.setattr(QMessageBox, 'information', lambda *args, **kwargs: QMessageBox.StandardButton.Ok)
        
        # 生成を実行
        dlg._generate_code()
        
        # _select_output_dir が呼ばれたか（出力先未設定のため）
        assert called['count'] >= 1, f"出力先選択が呼ばれていない (count={called['count']})"
        
        dlg.close()


# ===== 設定記憶と生成の統合テスト =====
class TestSettingsMemoryIntegration:
    """設定記憶とコード生成の統合テスト"""
    
    def test_generate_with_remembered_settings(self, qapp, sample_data, temp_settings_file):
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6がインストールされていません")
        
        dlg1 = create_dialog(qapp, sample_data, temp_settings_file)
        test_dir = tempfile.mkdtemp(prefix="statable_gen_test_")
        dlg1.output_dir_edit.setText(test_dir)
        dlg1._save_settings()
        dlg1.close()
        
        dlg2 = create_dialog(qapp, sample_data, temp_settings_file)
        assert dlg2.output_dir_edit.text() == test_dir
        
        dlg2._generate_code()
        
        generated_files = dlg2.get_generated_files()
        assert len(generated_files) == 11
        
        dlg2.close()
        
        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])