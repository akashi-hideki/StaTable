# tests/test_imports_check.py
"""
コード生成モジュールのインポート確認テスト
"""

import sys
import os
import importlib
import traceback

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
codegen_dir = os.path.join(project_root, 'codegen')
statable_dir = os.path.join(project_root, 'statable')

# codegenを優先してパスに追加
sys.path.insert(0, codegen_dir)  # codegenを先に追加
sys.path.insert(0, project_root)
sys.path.insert(0, statable_dir)


def test_import_statables():
    """statableモジュールのインポート確認"""
    modules = [
        'statable.model',
        'statable.state_machine',
        'statable.global_defs',
    ]
    
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
            print(f"✅ {module_name}: インポート成功")
        except Exception as e:
            print(f"❌ {module_name}: インポート失敗 - {e}")
            raise


def test_import_codegen():
    """codegenモジュールのインポート確認"""
    # モジュールを直接ファイルパスからインポート
    import importlib.util
    
    codegen_files = [
        'code_templates',
        'type_mapper',
        'naming_convention',
        'struct_generator',
        'enum_generator',
        'transition_generator',
        'role_function_generator',
        'variable_generator',
        'c_code_generator',
    ]
    
    for module_name in codegen_files:
        try:
            filepath = os.path.join(codegen_dir, f"{module_name}.py")
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"✅ {module_name}: インポート成功")
        except Exception as e:
            print(f"❌ {module_name}: インポート失敗 - {e}")
            traceback.print_exc()
            raise
    
    # sample_data は特別に処理
    try:
        filepath = os.path.join(codegen_dir, "sample_data.py")
        spec = importlib.util.spec_from_file_location("codegen_sample_data", filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f"✅ sample_data: インポート成功")
    except Exception as e:
        print(f"❌ sample_data: インポート失敗 - {e}")
        traceback.print_exc()
        raise


def test_import_classes():
    """各クラスのインポート確認"""
    import importlib.util
    
    class_mappings = [
        ('code_templates', 'CodeTemplates'),
        ('type_mapper', 'CTypeMapper'),
        ('naming_convention', 'CNamingConvention'),
        ('struct_generator', 'CStructGenerator'),
        ('enum_generator', 'CEnumGenerator'),
        ('transition_generator', 'TransitionGenerator'),
        ('role_function_generator', 'RoleFunctionGenerator'),
        ('variable_generator', 'VariableGenerator'),
        ('c_code_generator', 'CCodeGenerator'),
    ]
    
    for module_name, class_name in class_mappings:
        try:
            filepath = os.path.join(codegen_dir, f"{module_name}.py")
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            cls = getattr(module, class_name)
            print(f"✅ {module_name}.{class_name}: インポート成功")
        except Exception as e:
            print(f"❌ {module_name}.{class_name}: インポート失敗 - {e}")
            raise


def test_instantiate_all_classes():
    """全クラスのインスタンス化確認"""
    import importlib.util
    
    class_mappings = [
        ('code_templates', 'CodeTemplates'),
        ('type_mapper', 'CTypeMapper'),
        ('naming_convention', 'CNamingConvention'),
        ('struct_generator', 'CStructGenerator'),
        ('enum_generator', 'CEnumGenerator'),
        ('transition_generator', 'TransitionGenerator'),
        ('role_function_generator', 'RoleFunctionGenerator'),
        ('variable_generator', 'VariableGenerator'),
        ('c_code_generator', 'CCodeGenerator'),
    ]
    
    for module_name, class_name in class_mappings:
        try:
            filepath = os.path.join(codegen_dir, f"{module_name}.py")
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            cls = getattr(module, class_name)
            instance = cls()
            print(f"✅ {class_name}: インスタンス化成功")
        except Exception as e:
            print(f"❌ {class_name}: インスタンス化失敗 - {e}")
            traceback.print_exc()
            raise


def test_full_code_generation():
    """完全なコード生成テスト"""
    import importlib.util
    
    # sample_data をロード
    sample_data_path = os.path.join(codegen_dir, "sample_data.py")
    spec = importlib.util.spec_from_file_location("codegen_sample_data", sample_data_path)
    sample_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sample_module)
    
    # c_code_generator をロード
    cgen_path = os.path.join(codegen_dir, "c_code_generator.py")
    spec = importlib.util.spec_from_file_location("codegen_c_code_generator", cgen_path)
    cgen_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cgen_module)
    
    # サンプルデータ生成
    sample_gen = sample_module.SampleDataGenerator()
    state_machine, global_defs = sample_gen.get_sample_data()
    
    # コード生成
    code_gen = cgen_module.CCodeGenerator()
    generated_files = code_gen.generate_all(state_machine, global_defs)
    
    print(f"✅ コード生成成功: {len(generated_files)}ファイル生成")
    for filename in generated_files:
        content = generated_files[filename]
        print(f"   - {filename}: {len(content)}文字")
    
    return generated_files


def run_all_tests():
    """全テスト実行"""
    print("=" * 60)
    print("インポート確認テスト")
    print("=" * 60)
    print()
    
    print("--- statableモジュール ---")
    test_import_statables()
    print()
    
    print("--- codegenモジュール ---")
    test_import_codegen()
    print()
    
    print("--- クラスインポート ---")
    test_import_classes()
    print()
    
    print("--- インスタンス化 ---")
    test_instantiate_all_classes()
    print()
    
    print("--- コード生成 ---")
    test_full_code_generation()
    print()
    
    print("=" * 60)
    print("全テスト完了")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()