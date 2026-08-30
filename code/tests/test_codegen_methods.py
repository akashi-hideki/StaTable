# tests/test_codegen_methods.py
"""
コード生成モジュールのメソッド存在確認テスト
完全データ駆動版のすべてのクラスとメソッド・辞書を確認する
"""

import sys
import os
import inspect
import pytest

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
codegen_dir = os.path.join(project_root, 'codegen')
statable_dir = os.path.join(project_root, 'statable')

# パスを追加
sys.path.insert(0, project_root)
sys.path.insert(0, codegen_dir)
sys.path.insert(0, statable_dir)

# インポート
from code_templates import CodeTemplates
from type_mapper import CTypeMapper
from naming_convention import CNamingConvention
from struct_generator import CStructGenerator
from enum_generator import CEnumGenerator
from transition_generator import TransitionGenerator
from role_function_generator import RoleFunctionGenerator
from variable_generator import VariableGenerator
from c_code_generator import CCodeGenerator
from sample_data import SampleDataGenerator


# ===== CodeTemplates テスト =====
class TestCodeTemplates:
    """CodeTemplatesクラスのテスト"""
    
    def setup_method(self):
        self.templates = CodeTemplates()
    
    def test_class_exists(self):
        assert CodeTemplates is not None
    
    def test_strings_dict(self):
        assert hasattr(self.templates, 'STRINGS')
        assert isinstance(self.templates.STRINGS, dict)
        assert len(self.templates.STRINGS) > 0
    
    def test_section_headers_dict(self):
        assert hasattr(self.templates, 'SECTION_HEADERS')
        assert isinstance(self.templates.SECTION_HEADERS, dict)
        assert len(self.templates.SECTION_HEADERS) > 0
    
    def test_struct_comments_dict(self):
        assert hasattr(self.templates, 'STRUCT_COMMENTS')
        assert isinstance(self.templates.STRUCT_COMMENTS, dict)
        assert len(self.templates.STRUCT_COMMENTS) > 0
    
    def test_enum_comments_dict(self):
        assert hasattr(self.templates, 'ENUM_COMMENTS')
        assert isinstance(self.templates.ENUM_COMMENTS, dict)
        assert len(self.templates.ENUM_COMMENTS) > 0
    
    def test_function_comments_dict(self):
        assert hasattr(self.templates, 'FUNCTION_COMMENTS')
        assert isinstance(self.templates.FUNCTION_COMMENTS, dict)
        assert len(self.templates.FUNCTION_COMMENTS) > 0
    
    def test_type_names_dict(self):
        assert hasattr(self.templates, 'TYPE_NAMES')
        assert isinstance(self.templates.TYPE_NAMES, dict)
        assert len(self.templates.TYPE_NAMES) > 0
    
    def test_function_names_dict(self):
        assert hasattr(self.templates, 'FUNCTION_NAMES')
        assert isinstance(self.templates.FUNCTION_NAMES, dict)
        assert len(self.templates.FUNCTION_NAMES) > 0
    
    def test_macro_names_dict(self):
        assert hasattr(self.templates, 'MACRO_NAMES')
        assert isinstance(self.templates.MACRO_NAMES, dict)
        assert len(self.templates.MACRO_NAMES) > 0
    
    def test_formats_dict(self):
        assert hasattr(self.templates, 'FORMATS')
        assert isinstance(self.templates.FORMATS, dict)
        assert len(self.templates.FORMATS) > 0
    
    def test_debug_messages_dict(self):
        assert hasattr(self.templates, 'DEBUG_MESSAGES')
        assert isinstance(self.templates.DEBUG_MESSAGES, dict)
        assert len(self.templates.DEBUG_MESSAGES) > 0


# ===== CTypeMapper テスト =====
class TestCTypeMapper:
    """CTypeMapperクラスのテスト"""
    
    def setup_method(self):
        self.mapper = CTypeMapper()
    
    def test_class_exists(self):
        assert CTypeMapper is not None
    
    def test_type_mapping_dict(self):
        assert hasattr(self.mapper, 'TYPE_MAPPING')
        assert isinstance(self.mapper.TYPE_MAPPING, dict)
        assert len(self.mapper.TYPE_MAPPING) > 0
    
    def test_type_categories_dict(self):
        assert hasattr(self.mapper, 'TYPE_CATEGORIES')
        assert isinstance(self.mapper.TYPE_CATEGORIES, dict)
        assert len(self.mapper.TYPE_CATEGORIES) > 0
    
    def test_header_requirements_dict(self):
        assert hasattr(self.mapper, 'HEADER_REQUIREMENTS')
        assert isinstance(self.mapper.HEADER_REQUIREMENTS, dict)
        assert len(self.mapper.HEADER_REQUIREMENTS) > 0
    
    def test_map_type_method(self):
        assert hasattr(self.mapper, 'map_type')
        assert callable(self.mapper.map_type)
    
    def test_get_type_category_method(self):
        assert hasattr(self.mapper, 'get_type_category')
        assert callable(self.mapper.get_type_category)
    
    def test_get_required_headers_method(self):
        assert hasattr(self.mapper, 'get_required_headers')
        assert callable(self.mapper.get_required_headers)
    
    def test_map_basic_type(self):
        assert self.mapper.map_type('uint8') == 'uint8_t'
        assert self.mapper.map_type('int32') == 'int32_t'
        assert self.mapper.map_type('bool') == 'bool'
        assert self.mapper.map_type('void') == 'void'
    
    def test_map_custom_type(self):
        assert self.mapper.map_type('SystemStatus') == 'SystemStatus'
        assert self.mapper.map_type('MyCustomType') == 'MyCustomType'


# ===== CNamingConvention テスト =====
class TestCNamingConvention:
    """CNamingConventionクラスのテスト"""
    
    def setup_method(self):
        self.naming = CNamingConvention()
    
    def test_class_exists(self):
        assert CNamingConvention is not None
    
    def test_conversion_patterns_dict(self):
        assert hasattr(self.naming, 'CONVERSION_PATTERNS')
        assert isinstance(self.naming.CONVERSION_PATTERNS, dict)
        assert len(self.naming.CONVERSION_PATTERNS) > 0
    
    def test_c_keywords_set(self):
        assert hasattr(self.naming, 'C_KEYWORDS')
        assert isinstance(self.naming.C_KEYWORDS, set)
        assert len(self.naming.C_KEYWORDS) > 0
    
    def test_identifier_rules_dict(self):
        assert hasattr(self.naming, 'IDENTIFIER_RULES')
        assert isinstance(self.naming.IDENTIFIER_RULES, dict)
        assert len(self.naming.IDENTIFIER_RULES) > 0
    
    def test_all_naming_methods(self):
        methods = [
            'to_upper_snake', 'to_lower_snake', 'to_camel_case',
            'to_pascal_case', 'sanitize_identifier', 'create_identifier',
            'create_type_name', 'create_enum_value', 'create_function_name',
            'create_variable_name', 'create_macro_name',
        ]
        for method_name in methods:
            assert hasattr(self.naming, method_name), f"{method_name}が存在しません"
            assert callable(getattr(self.naming, method_name)), f"{method_name}が呼び出せません"
    
    def test_naming_conversion(self):
        assert self.naming.to_upper_snake('systemStatus') == 'SYSTEM_STATUS'
        assert self.naming.to_lower_snake('SystemStatus') == 'system_status'
        assert self.naming.to_pascal_case('system_status') == 'SystemStatus'
        assert self.naming.to_camel_case('system_status') == 'systemStatus'


# ===== CStructGenerator テスト =====
class TestCStructGenerator:
    """CStructGeneratorクラスのテスト"""
    
    def setup_method(self):
        self.struct_gen = CStructGenerator()
    
    def test_class_exists(self):
        assert CStructGenerator is not None
    
    def test_member_type_detectors_dict(self):
        assert hasattr(self.struct_gen, 'member_type_detectors')
        assert isinstance(self.struct_gen.member_type_detectors, dict)
        assert len(self.struct_gen.member_type_detectors) > 0
    
    def test_member_generators_dict(self):
        assert hasattr(self.struct_gen, 'member_generators')
        assert isinstance(self.struct_gen.member_generators, dict)
        assert len(self.struct_gen.member_generators) > 0
    
    def test_struct_generators_dict(self):
        assert hasattr(self.struct_gen, 'struct_generators')
        assert isinstance(self.struct_gen.struct_generators, dict)
        assert len(self.struct_gen.struct_generators) > 0
    
    def test_struct_steps_dict(self):
        assert hasattr(self.struct_gen, 'struct_steps')
        assert isinstance(self.struct_gen.struct_steps, dict)
        assert len(self.struct_gen.struct_steps) > 0
    
    def test_step_executors_dict(self):
        assert hasattr(self.struct_gen, 'step_executors')
        assert isinstance(self.struct_gen.step_executors, dict)
        assert len(self.struct_gen.step_executors) > 0
    
    def test_generate_struct_method(self):
        assert hasattr(self.struct_gen, 'generate_struct')
        assert callable(self.struct_gen.generate_struct)
    
    def test_generate_all_structs_method(self):
        assert hasattr(self.struct_gen, 'generate_all_structs')
        assert callable(self.struct_gen.generate_all_structs)


# ===== CEnumGenerator テスト =====
class TestCEnumGenerator:
    """CEnumGeneratorクラスのテスト"""
    
    def setup_method(self):
        self.enum_gen = CEnumGenerator()
    
    def test_class_exists(self):
        assert CEnumGenerator is not None
    
    def test_enum_configs_dict(self):
        assert hasattr(self.enum_gen, 'enum_configs')
        assert isinstance(self.enum_gen.enum_configs, dict)
        assert len(self.enum_gen.enum_configs) > 0
    
    def test_enum_steps_list(self):
        assert hasattr(self.enum_gen, 'enum_steps')
        assert isinstance(self.enum_gen.enum_steps, list)
        assert len(self.enum_gen.enum_steps) > 0
    
    def test_step_executors_dict(self):
        assert hasattr(self.enum_gen, 'step_executors')
        assert isinstance(self.enum_gen.step_executors, dict)
        assert len(self.enum_gen.step_executors) > 0
    
    def test_generate_enum_method(self):
        assert hasattr(self.enum_gen, 'generate_enum')
        assert callable(self.enum_gen.generate_enum)
    
    def test_generate_all_enums_method(self):
        assert hasattr(self.enum_gen, 'generate_all_enums')
        assert callable(self.enum_gen.generate_all_enums)
    
    def test_generate_bit_mask_enum_method(self):
        assert hasattr(self.enum_gen, 'generate_bit_mask_enum')
        assert callable(self.enum_gen.generate_bit_mask_enum)


# ===== TransitionGenerator テスト =====
class TestTransitionGenerator:
    """TransitionGeneratorクラスのテスト"""
    
    def setup_method(self):
        self.transition_gen = TransitionGenerator()
    
    def test_class_exists(self):
        assert TransitionGenerator is not None
    
    def test_table_generators_dict(self):
        assert hasattr(self.transition_gen, 'table_generators')
        assert isinstance(self.transition_gen.table_generators, dict)
        assert len(self.transition_gen.table_generators) > 0
    
    def test_process_generators_dict(self):
        assert hasattr(self.transition_gen, 'process_generators')
        assert isinstance(self.transition_gen.process_generators, dict)
        assert len(self.transition_gen.process_generators) > 0
    
    def test_table_steps_dict(self):
        assert hasattr(self.transition_gen, 'table_steps')
        assert isinstance(self.transition_gen.table_steps, dict)
        assert len(self.transition_gen.table_steps) > 0
    
    def test_table_templates_dict(self):
        assert hasattr(self.transition_gen, 'table_templates')
        assert isinstance(self.transition_gen.table_templates, dict)
        assert len(self.transition_gen.table_templates) > 0
    
    def test_cell_templates_dict(self):
        assert hasattr(self.transition_gen, 'cell_templates')
        assert isinstance(self.transition_gen.cell_templates, dict)
        assert len(self.transition_gen.cell_templates) > 0
    
    def test_process_steps_list(self):
        assert hasattr(self.transition_gen, 'process_steps')
        assert isinstance(self.transition_gen.process_steps, list)
        assert len(self.transition_gen.process_steps) > 0
    
    def test_process_templates_dict(self):
        assert hasattr(self.transition_gen, 'process_templates')
        assert isinstance(self.transition_gen.process_templates, dict)
        assert len(self.transition_gen.process_templates) > 0
    
    def test_step_executors_dict(self):
        assert hasattr(self.transition_gen, 'step_executors')
        assert isinstance(self.transition_gen.step_executors, dict)
        assert len(self.transition_gen.step_executors) > 0
    
    def test_generate_transition_table_method(self):
        assert hasattr(self.transition_gen, 'generate_transition_table')
        assert callable(self.transition_gen.generate_transition_table)
    
    def test_generate_process_function_method(self):
        assert hasattr(self.transition_gen, 'generate_process_function')
        assert callable(self.transition_gen.generate_process_function)
    
    def test_generate_all_transitions_method(self):
        assert hasattr(self.transition_gen, 'generate_all_transitions')
        assert callable(self.transition_gen.generate_all_transitions)


# ===== RoleFunctionGenerator テスト =====
class TestRoleFunctionGenerator:
    """RoleFunctionGeneratorクラスのテスト"""
    
    def setup_method(self):
        self.role_gen = RoleFunctionGenerator()
    
    def test_class_exists(self):
        assert RoleFunctionGenerator is not None
    
    def test_arg_generators_dict(self):
        assert hasattr(self.role_gen, 'arg_generators')
        assert isinstance(self.role_gen.arg_generators, dict)
        assert len(self.role_gen.arg_generators) > 0
    
    def test_default_return_values_dict(self):
        assert hasattr(self.role_gen, 'default_return_values')
        assert isinstance(self.role_gen.default_return_values, dict)
        assert len(self.role_gen.default_return_values) > 0
    
    def test_function_generators_dict(self):
        assert hasattr(self.role_gen, 'function_generators')
        assert isinstance(self.role_gen.function_generators, dict)
        assert len(self.role_gen.function_generators) > 0
    
    def test_return_comments_dict(self):
        assert hasattr(self.role_gen, 'return_comments')
        assert isinstance(self.role_gen.return_comments, dict)
        assert len(self.role_gen.return_comments) > 0
    
    def test_standard_args_list(self):
        assert hasattr(self.role_gen, 'standard_args')
        assert isinstance(self.role_gen.standard_args, list)
        assert len(self.role_gen.standard_args) > 0
    
    def test_declaration_steps_list(self):
        assert hasattr(self.role_gen, 'declaration_steps')
        assert isinstance(self.role_gen.declaration_steps, list)
        assert len(self.role_gen.declaration_steps) > 0
    
    def test_implementation_steps_list(self):
        assert hasattr(self.role_gen, 'implementation_steps')
        assert isinstance(self.role_gen.implementation_steps, list)
        assert len(self.role_gen.implementation_steps) > 0
    
    def test_step_executors_dict(self):
        assert hasattr(self.role_gen, 'step_executors')
        assert isinstance(self.role_gen.step_executors, dict)
        assert len(self.role_gen.step_executors) > 0
    
    def test_generate_function_method(self):
        assert hasattr(self.role_gen, 'generate_function')
        assert callable(self.role_gen.generate_function)
    
    def test_generate_all_declarations_method(self):
        assert hasattr(self.role_gen, 'generate_all_declarations')
        assert callable(self.role_gen.generate_all_declarations)
    
    def test_generate_all_implementations_method(self):
        assert hasattr(self.role_gen, 'generate_all_implementations')
        assert callable(self.role_gen.generate_all_implementations)


# ===== VariableGenerator テスト =====
class TestVariableGenerator:
    """VariableGeneratorクラスのテスト"""
    
    def setup_method(self):
        self.var_gen = VariableGenerator()
    
    def test_class_exists(self):
        assert VariableGenerator is not None
    
    def test_variable_type_detectors_dict(self):
        assert hasattr(self.var_gen, 'variable_type_detectors')
        assert isinstance(self.var_gen.variable_type_detectors, dict)
        assert len(self.var_gen.variable_type_detectors) > 0
    
    def test_variable_generators_dict(self):
        assert hasattr(self.var_gen, 'variable_generators')
        assert isinstance(self.var_gen.variable_generators, dict)
        assert len(self.var_gen.variable_generators) > 0
    
    def test_default_init_values_dict(self):
        assert hasattr(self.var_gen, 'default_init_values')
        assert isinstance(self.var_gen.default_init_values, dict)
        assert len(self.var_gen.default_init_values) > 0
    
    def test_init_generators_dict(self):
        assert hasattr(self.var_gen, 'init_generators')
        assert isinstance(self.var_gen.init_generators, dict)
        assert len(self.var_gen.init_generators) > 0
    
    def test_macro_generators_dict(self):
        assert hasattr(self.var_gen, 'macro_generators')
        assert isinstance(self.var_gen.macro_generators, dict)
        assert len(self.var_gen.macro_generators) > 0
    
    def test_init_code_templates_dict(self):
        assert hasattr(self.var_gen, 'init_code_templates')
        assert isinstance(self.var_gen.init_code_templates, dict)
        assert len(self.var_gen.init_code_templates) > 0
    
    def test_init_templates_dict(self):
        assert hasattr(self.var_gen, 'init_templates')
        assert isinstance(self.var_gen.init_templates, dict)
        assert len(self.var_gen.init_templates) > 0
    
    def test_init_function_steps_list(self):
        assert hasattr(self.var_gen, 'init_function_steps')
        assert isinstance(self.var_gen.init_function_steps, list)
        assert len(self.var_gen.init_function_steps) > 0
    
    def test_step_executors_dict(self):
        assert hasattr(self.var_gen, 'step_executors')
        assert isinstance(self.var_gen.step_executors, dict)
        assert len(self.var_gen.step_executors) > 0
    
    def test_generate_variable_method(self):
        assert hasattr(self.var_gen, 'generate_variable')
        assert callable(self.var_gen.generate_variable)
    
    def test_generate_all_macros_method(self):
        assert hasattr(self.var_gen, 'generate_all_macros')
        assert callable(self.var_gen.generate_all_macros)
    
    def test_generate_init_function_method(self):
        assert hasattr(self.var_gen, 'generate_init_function')
        assert callable(self.var_gen.generate_init_function)


# ===== CCodeGenerator テスト =====
class TestCCodeGenerator:
    """CCodeGeneratorクラスのテスト"""
    
    def setup_method(self):
        self.code_gen = CCodeGenerator()
    
    def test_class_exists(self):
        assert CCodeGenerator is not None
    
    def test_file_generators_dict(self):
        assert hasattr(self.code_gen, 'file_generators')
        assert isinstance(self.code_gen.file_generators, dict)
        assert len(self.code_gen.file_generators) > 0
    
    def test_generate_all_method(self):
        assert hasattr(self.code_gen, 'generate_all')
        assert callable(self.code_gen.generate_all)
    
    def test_generate_file_method(self):
        assert hasattr(self.code_gen, 'generate_file')
        assert callable(self.code_gen.generate_file)
    
    def test_save_generated_code_method(self):
        assert hasattr(self.code_gen, 'save_generated_code')
        assert callable(self.code_gen.save_generated_code)
    
    def test_required_files(self):
        required_files = [
            'statable_types.h',
            'statable_transitions.h',
            'statable_transitions.c',
            'statable_role_functions.h',
            'statable_role_functions.c',
            'statable_init.c',
        ]
        for filename in required_files:
            assert filename in self.code_gen.file_generators, f"{filename}が定義されていません"


# ===== SampleDataGenerator テスト =====
class TestSampleDataGenerator:
    """SampleDataGeneratorクラスのテスト"""
    
    def setup_method(self):
        self.sample_gen = SampleDataGenerator()
    
    def test_class_exists(self):
        assert SampleDataGenerator is not None
    
    def test_create_sample_state_machine_method(self):
        assert hasattr(self.sample_gen, 'create_sample_state_machine')
        assert callable(self.sample_gen.create_sample_state_machine)
    
    def test_create_sample_global_defs_method(self):
        assert hasattr(self.sample_gen, 'create_sample_global_defs')
        assert callable(self.sample_gen.create_sample_global_defs)
    
    def test_get_sample_data_method(self):
        assert hasattr(self.sample_gen, 'get_sample_data')
        assert callable(self.sample_gen.get_sample_data)


# ===== コード生成統合テスト =====
class TestCodeGeneration:
    """コード生成の統合テスト"""
    
    def setup_method(self):
        self.sample_gen = SampleDataGenerator()
        self.code_gen = CCodeGenerator()
        self.state_machine, self.global_defs = self.sample_gen.get_sample_data()
    
    def test_generate_all_files(self):
        """全ファイル生成テスト"""
        generated_files = self.code_gen.generate_all(self.state_machine, self.global_defs)
        assert len(generated_files) == 6
        
        for filename, content in generated_files.items():
            assert len(content) > 0, f"{filename}が空です"
    
    def test_generate_types_header(self):
        """型定義ヘッダ生成テスト"""
        content = self.code_gen.generate_file('statable_types.h', self.state_machine, self.global_defs)
        assert 'typedef enum' in content
        assert 'typedef struct' in content
        assert 'STATE_t' in content
        assert 'EVENT_t' in content
        assert 'SystemContext_t' in content
    
    def test_generate_transitions_header(self):
        """遷移関数ヘッダ生成テスト"""
        content = self.code_gen.generate_file('statable_transitions.h', self.state_machine, self.global_defs)
        assert 'StateMachine_Process' in content
        assert 'STATE_t' in content
        assert 'EVENT_t' in content
        assert 'SystemContext_t' in content
    
    def test_generate_transitions_source(self):
        """遷移関数ソース生成テスト"""
        content = self.code_gen.generate_file('statable_transitions.c', self.state_machine, self.global_defs)
        assert 'transition_matrix' in content
        assert 'StateMachine_Process' in content
        assert 'LOG_DEBUG' in content
        assert 'LOG_ERROR' in content
    
    def test_generate_role_functions_header(self):
        """ロール関数ヘッダ生成テスト"""
        content = self.code_gen.generate_file('statable_role_functions.h', self.state_machine, self.global_defs)
        assert 'RoleFunc_' in content
        assert 'STATE_t' in content
        assert 'SystemContext_t' in content
    
    def test_generate_role_functions_source(self):
        """ロール関数ソース生成テスト"""
        content = self.code_gen.generate_file('statable_role_functions.c', self.state_machine, self.global_defs)
        assert 'RoleFunc_' in content
        assert 'TODO' in content
        assert '(void)' in content
    
    def test_generate_init_source(self):
        """初期化ソース生成テスト"""
        content = self.code_gen.generate_file('statable_init.c', self.state_machine, self.global_defs)
        assert 'SystemContext_Init' in content
        assert 'ctx->data' in content
        assert 'ctx->flags' in content
    
    def test_data_driven_structure(self):
        """データ駆動構造の確認"""
        # 各ジェネレータが適切なデータ駆動辞書を持っているか
        generators = [
            self.code_gen.struct_gen,
            self.code_gen.enum_gen,
            self.code_gen.transition_gen,
            self.code_gen.role_func_gen,
            self.code_gen.variable_gen,
        ]
        
        for gen in generators:
            # ステップ実行辞書の確認
            if hasattr(gen, 'step_executors'):
                assert isinstance(gen.step_executors, dict)
                assert len(gen.step_executors) > 0
            
            # 生成辞書の確認
            if hasattr(gen, 'struct_generators'):
                assert isinstance(gen.struct_generators, dict)
            if hasattr(gen, 'enum_configs'):
                assert isinstance(gen.enum_configs, dict)
            if hasattr(gen, 'table_generators'):
                assert isinstance(gen.table_generators, dict)
            if hasattr(gen, 'function_generators'):
                assert isinstance(gen.function_generators, dict)
            if hasattr(gen, 'variable_generators'):
                assert isinstance(gen.variable_generators, dict)


if __name__ == "__main__":
    pytest.main([__file__, '-v', '--tb=short'])