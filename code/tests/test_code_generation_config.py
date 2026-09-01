# tests/test_code_generation_config.py
"""
コード生成設定のテスト
"""

import sys
import os
import importlib.util
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'codegen'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'statable'))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'codegen', 'config.py')
    module = load_module("test_config", config_path)
    return module.CodeGenerationConfig()


@pytest.fixture
def config_manager():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'codegen', 'config.py')
    module = load_module("test_config_manager", config_path)
    return module.ConfigManager()


class TestCodeGenerationConfig:
    """CodeGenerationConfig のテスト"""
    
    def test_default_values(self, config):
        assert config.generation_style == "table_driven"
        assert config.table_type == "array"
        assert config.os_type == "non_rtos"
        assert config.state_prefix == "STATE"
        assert config.event_prefix == "EVENT"
        assert config.flag_prefix == "FLAG"
        assert config.enable_debug_logs is True
        assert config.enable_info_logs is True
        assert config.enable_error_logs is True
        assert config.enable_comments is True
        assert config.enable_doxygen is True
        assert config.enable_user_markers is True
        assert config.save_with_merge is True
    
    def test_to_dict(self, config):
        data = config.to_dict()
        assert isinstance(data, dict)
        assert data['generation_style'] == "table_driven"
        assert data['os_type'] == "non_rtos"
    
    def test_from_dict(self, config):
        data = {
            'generation_style': 'switch_case',
            'table_type': 'switch',
            'os_type': 'freertos',
        }
        new_config = config.__class__.from_dict({**config.to_dict(), **data})
        assert new_config.generation_style == 'switch_case'
        assert new_config.table_type == 'switch'
        assert new_config.os_type == 'freertos'


class TestConfigManager:
    """ConfigManager のテスト"""
    
    def test_get_config(self, config_manager):
        config = config_manager.get_config()
        assert config is not None
        assert config.generation_style == "table_driven"
    
    def test_update(self, config_manager):
        config_manager.update(generation_style="switch_case", os_type="freertos")
        config = config_manager.get_config()
        assert config.generation_style == "switch_case"
        assert config.os_type == "freertos"
    
    def test_reset(self, config_manager):
        config_manager.update(generation_style="switch_case")
        config_manager.reset()
        config = config_manager.get_config()
        assert config.generation_style == "table_driven"
    
    def test_get_available_styles(self, config_manager):
        styles = config_manager.get_available_styles()
        assert 'table_driven' in styles
        assert 'switch_case' in styles
    
    def test_get_available_os_types(self, config_manager):
        os_types = config_manager.get_available_os_types()
        assert 'non_rtos' in os_types
        assert 'freertos' in os_types
        assert 'threadx' in os_types


if __name__ == '__main__':
    pytest.main([__file__, '-v'])