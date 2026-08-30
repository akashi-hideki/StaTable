# tests/test_codegen_debug3.py
"""
statable_types.h の構造体セミコロン問題の原因特定テスト
"""

import sys
import os
import importlib.util

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
codegen_dir = os.path.join(project_root, 'codegen')
statable_dir = os.path.join(project_root, 'statable')

sys.path.insert(0, codegen_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, statable_dir)


def load_module(module_name, filepath):
    """モジュールをファイルパスからロード"""
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_sample_data():
    """サンプルデータを取得"""
    sample_data_path = os.path.join(codegen_dir, "sample_data.py")
    sample_module = load_module("debug3_sample_data", sample_data_path)
    sample_gen = sample_module.SampleDataGenerator()
    return sample_gen.get_sample_data()


def get_code_generator():
    """コード生成器を取得"""
    cgen_path = os.path.join(codegen_dir, "c_code_generator.py")
    cgen_module = load_module("debug3_c_code_generator", cgen_path)
    return cgen_module.CCodeGenerator()


def debug_types_header_structure():
    """型定義ヘッダの構造を詳細調査"""
    print("\n" + "=" * 60)
    print("statable_types.h の構造体セミコロン調査")
    print("=" * 60)
    
    state_machine, global_defs = get_sample_data()
    code_gen = get_code_generator()
    
    content = code_gen.generate_file('statable_types.h', state_machine, global_defs)
    
    # 全行を表示
    print("\n--- 生成された全行 ---")
    lines = content.split('\n')
    for i, line in enumerate(lines):
        print(f"  Line {i:3d}: {repr(line)}")
    
    # セミコロンの検索
    print("\n--- セミコロンの検索 ---")
    semicolon_count = content.count(';')
    print(f"  セミコロン数: {semicolon_count}")
    
    # `};` の検索
    print("\n--- `}};` の検索 ---")
    close_semicolon_count = content.count('};')
    print(f"  `}};` の数: {close_semicolon_count}")
    
    # 各 `};` の位置
    idx = 0
    for i in range(close_semicolon_count):
        idx = content.find('};', idx)
        if idx == -1:
            break
        print(f"  位置 {idx}: ...{content[max(0,idx-30):idx+10]}...")
        idx += 1
    
    # `} SystemStatus_t` の検索
    print("\n--- `} SystemStatus_t` の検索 ---")
    if '} SystemStatus_t' in content:
        print("  ✅ 見つかりました")
        idx = content.find('} SystemStatus_t')
        print(f"  位置: {idx}")
        print(f"  前後: ...{content[max(0,idx-20):idx+30]}...")
    else:
        print("  ❌ 見つかりません")
    
    # `} SystemData_t` の検索
    print("\n--- `} SystemData_t` の検索 ---")
    if '} SystemData_t' in content:
        print("  ✅ 見つかりました")
        idx = content.find('} SystemData_t')
        print(f"  位置: {idx}")
        print(f"  前後: ...{content[max(0,idx-20):idx+30]}...")
    else:
        print("  ❌ 見つかりません")
    
    # 各行の末尾を確認
    print("\n--- 構造体関連の行 ---")
    for i, line in enumerate(lines):
        if 'typedef struct' in line or '}' in line or 'SystemStatus' in line or 'SystemData' in line:
            print(f"  Line {i:3d}: {repr(line)}")
    
    return content


def debug_struct_generator_direct():
    """CStructGeneratorを直接テスト"""
    print("\n" + "=" * 60)
    print("CStructGenerator の直接テスト")
    print("=" * 60)
    
    struct_gen_path = os.path.join(codegen_dir, "struct_generator.py")
    struct_module = load_module("debug3_struct_gen", struct_gen_path)
    struct_gen = struct_module.CStructGenerator()
    
    state_machine, global_defs = get_sample_data()
    
    # 各構造体タイプを直接生成
    print("\n--- generate_struct('custom_type', ...) ---")
    for custom_type in global_defs.custom_types:
        result = struct_gen.generate_struct('custom_type', custom_type)
        print(f"  {custom_type.name}:")
        print(f"  {repr(result)}")
        print()
    
    print("\n--- generate_struct('system_data', ...) ---")
    result = struct_gen.generate_struct('system_data', global_defs)
    print(f"  {repr(result)}")
    print()
    
    print("\n--- generate_struct('event_flags', ...) ---")
    result = struct_gen.generate_struct('event_flags', global_defs)
    print(f"  {repr(result)}")
    print()
    
    print("\n--- generate_struct('system_context', ...) ---")
    result = struct_gen.generate_struct('system_context', global_defs)
    print(f"  {repr(result)}")
    print()
    
    return struct_gen


def debug_struct_end_step():
    """構造体終了ステップの実行を調査"""
    print("\n" + "=" * 60)
    print("構造体終了ステップの調査")
    print("=" * 60)
    
    struct_gen_path = os.path.join(codegen_dir, "struct_generator.py")
    struct_module = load_module("debug3_struct_gen2", struct_gen_path)
    struct_gen = struct_module.CStructGenerator()
    
    state_machine, global_defs = get_sample_data()
    
    # custom_type の生成ステップを確認
    print("\n--- custom_type の生成ステップ ---")
    print(f"  struct_steps['custom_type']: {struct_gen.struct_steps['custom_type']}")
    
    # struct_end ステップの実行
    print("\n--- _execute_struct_end_step のテスト ---")
    for custom_type in global_defs.custom_types:
        context = {'struct_def': custom_type}
        result = struct_gen._execute_struct_end_step({}, context)
        print(f"  {custom_type.name}: {result}")
    
    # struct_end_fixed ステップの実行
    print("\n--- _execute_struct_end_fixed_step のテスト ---")
    for type_name_key in ['system_data', 'event_flags', 'system_context']:
        step = {'type_name': type_name_key}
        result = struct_gen._execute_struct_end_fixed_step(step, {})
        print(f"  {type_name_key}: {result}")
    
    # create_type_name のテスト
    print("\n--- create_type_name のテスト ---")
    for name in ['SystemStatus', 'SensorData', 'system_data', 'event_flags', 'system_context']:
        result = struct_gen.naming.create_type_name(name)
        print(f"  {name} -> {result}")
    
    return struct_gen


def debug_c_code_generator_types():
    """CCodeGeneratorの型定義ヘッダ生成を調査"""
    print("\n" + "=" * 60)
    print("CCodeGenerator の型定義ヘッダ生成調査")
    print("=" * 60)
    
    state_machine, global_defs = get_sample_data()
    code_gen = get_code_generator()
    
    # 各ステップの実行結果を確認
    print("\n--- struct_gen.generate_struct('custom_type', ...) ---")
    for custom_type in global_defs.custom_types:
        result = code_gen.struct_gen.generate_struct('custom_type', custom_type)
        print(f"  {custom_type.name}:")
        print(f"    最後の30文字: ...{result[-30:]}")
    
    print("\n--- struct_gen.generate_struct('system_data', ...) ---")
    result = code_gen.struct_gen.generate_struct('system_data', global_defs)
    print(f"  最後の30文字: ...{result[-30:]}")
    
    print("\n--- struct_gen.generate_struct('event_flags', ...) ---")
    result = code_gen.struct_gen.generate_struct('event_flags', global_defs)
    print(f"  最後の30文字: ...{result[-30:]}")
    
    print("\n--- struct_gen.generate_struct('system_context', ...) ---")
    result = code_gen.struct_gen.generate_struct('system_context', global_defs)
    print(f"  最後の30文字: ...{result[-30:]}")
    
    # 型定義ヘッダ全体を生成
    print("\n--- 型定義ヘッダ全体の最後の100文字 ---")
    content = code_gen.generate_file('statable_types.h', state_machine, global_defs)
    print(f"  ...{content[-100:]}")
    
    return code_gen


def run_debug_tests():
    """デバッグテスト実行"""
    print("=" * 60)
    print("statable_types.h セミコロン問題デバッグ")
    print("=" * 60)
    
    # CStructGenerator の直接テスト
    struct_gen = debug_struct_generator_direct()
    
    # 構造体終了ステップの調査
    debug_struct_end_step()
    
    # CCodeGenerator の調査
    code_gen = debug_c_code_generator_types()
    
    # 型定義ヘッダの構造調査
    content = debug_types_header_structure()
    
    print("\n" + "=" * 60)
    print("デバッグ調査完了")
    print("=" * 60)


if __name__ == "__main__":
    run_debug_tests()