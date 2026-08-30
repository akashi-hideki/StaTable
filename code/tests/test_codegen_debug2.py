# tests/test_codegen_debug2.py
"""
ロール関数ヘッダの失敗原因特定テスト
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
    sample_module = load_module("debug2_sample_data", sample_data_path)
    sample_gen = sample_module.SampleDataGenerator()
    return sample_gen.get_sample_data()


def get_code_generator():
    """コード生成器を取得"""
    cgen_path = os.path.join(codegen_dir, "c_code_generator.py")
    cgen_module = load_module("debug2_c_code_generator", cgen_path)
    return cgen_module.CCodeGenerator()


def debug_role_function_header():
    """ロール関数ヘッダの内容を詳細調査"""
    print("\n" + "=" * 60)
    print("ロール関数ヘッダの詳細調査")
    print("=" * 60)
    
    state_machine, global_defs = get_sample_data()
    code_gen = get_code_generator()
    
    # ヘッダ生成
    header_content = code_gen.generate_file('statable_role_functions.h', state_machine, global_defs)
    
    # 全行を表示
    print("\n--- 生成されたヘッダ全行 ---")
    lines = header_content.split('\n')
    for i, line in enumerate(lines):
        print(f"  Line {i:3d}: {line}")
    
    # STATE_t の検索
    print("\n--- STATE_t の検索 ---")
    if 'STATE_t' in header_content:
        print("  ✅ STATE_t が見つかりました")
        count = header_content.count('STATE_t')
        print(f"  出現回数: {count}")
        # 各出現位置を表示
        idx = 0
        for i in range(count):
            idx = header_content.find('STATE_t', idx)
            if idx == -1:
                break
            print(f"  位置 {idx}: ...{header_content[max(0,idx-20):idx+30]}...")
            idx += 1
    else:
        print("  ❌ STATE_t が見つかりません")
    
    # SystemContext_t の検索
    print("\n--- SystemContext_t の検索 ---")
    if 'SystemContext_t' in header_content:
        print("  ✅ SystemContext_t が見つかりました")
        count = header_content.count('SystemContext_t')
        print(f"  出現回数: {count}")
        idx = 0
        for i in range(count):
            idx = header_content.find('SystemContext_t', idx)
            if idx == -1:
                break
            print(f"  位置 {idx}: ...{header_content[max(0,idx-20):idx+30]}...")
            idx += 1
    else:
        print("  ❌ SystemContext_t が見つかりません")
    
    # current_state の検索
    print("\n--- current_state の検索 ---")
    if 'current_state' in header_content:
        print("  ✅ current_state が見つかりました")
        count = header_content.count('current_state')
        print(f"  出現回数: {count}")
    else:
        print("  ❌ current_state が見つかりません")
    
    # ctx の検索
    print("\n--- ctx の検索 ---")
    if 'ctx' in header_content:
        print("  ✅ ctx が見つかりました")
        count = header_content.count('ctx')
        print(f"  出現回数: {count}")
    else:
        print("  ❌ ctx が見つかりません")
    
    return header_content


def debug_role_function_generator_direct():
    """RoleFunctionGeneratorを直接テスト"""
    print("\n" + "=" * 60)
    print("RoleFunctionGenerator の直接テスト")
    print("=" * 60)
    
    rf_gen_path = os.path.join(codegen_dir, "role_function_generator.py")
    rf_module = load_module("debug2_role_gen", rf_gen_path)
    rf_gen = rf_module.RoleFunctionGenerator()
    
    from statable.model import RoleFunction
    
    # テスト用関数
    test_func = RoleFunction(name="PowerOn", return_type="void", description="電源ON処理")
    
    print(f"\n--- テスト関数: {test_func.name} ---")
    print(f"  return_type: {test_func.return_type}")
    print(f"  arg1_type: {getattr(test_func, 'arg1_type', 'N/A')}")
    print(f"  arg1_name: {getattr(test_func, 'arg1_name', 'N/A')}")
    print(f"  arg2_type: {getattr(test_func, 'arg2_type', 'N/A')}")
    print(f"  arg2_name: {getattr(test_func, 'arg2_name', 'N/A')}")
    
    # _collect_args のテスト
    print("\n--- _collect_args の結果 ---")
    args = rf_gen._collect_args(test_func)
    for arg in args:
        print(f"  {arg}")
    
    # _generate_args_str のテスト
    print("\n--- _generate_args_str の結果 ---")
    args_str = rf_gen._generate_args_str(test_func)
    print(f"  {args_str}")
    
    # 宣言生成
    print("\n--- 宣言生成 ---")
    decl = rf_gen.generate_function('declaration', test_func)
    print(decl)
    
    return rf_gen, test_func


def debug_role_function_data():
    """RoleFunctionのデータ構造を調査"""
    print("\n" + "=" * 60)
    print("RoleFunction データ構造の調査")
    print("=" * 60)
    
    from statable.model import RoleFunction
    
    # RoleFunction クラスの全属性を確認
    print("\n--- RoleFunction クラスの属性 ---")
    print(f"  __init__ パラメータ: {RoleFunction.__init__.__code__.co_varnames}")
    print(f"  デフォルト値: {RoleFunction.__init__.__defaults__}")
    
    # インスタンス作成
    rf = RoleFunction(name="Test", return_type="void")
    
    print("\n--- インスタンスの属性 ---")
    print(f"  name: {rf.name}")
    print(f"  return_type: {rf.return_type}")
    print(f"  description: {getattr(rf, 'description', 'N/A')}")
    print(f"  title: {getattr(rf, 'title', 'N/A')}")
    print(f"  arg1_type: {getattr(rf, 'arg1_type', 'N/A')}")
    print(f"  arg1_name: {getattr(rf, 'arg1_name', 'N/A')}")
    print(f"  arg2_type: {getattr(rf, 'arg2_type', 'N/A')}")
    print(f"  arg2_name: {getattr(rf, 'arg2_name', 'N/A')}")
    
    # 全属性を表示
    print("\n--- 全属性 ---")
    for attr in dir(rf):
        if not attr.startswith('_'):
            value = getattr(rf, attr)
            if not callable(value):
                print(f"  {attr}: {value}")
    
    return rf


def debug_c_code_generator_role_functions():
    """CCodeGeneratorのrole_functions関連を調査"""
    print("\n" + "=" * 60)
    print("CCodeGenerator の role_functions 調査")
    print("=" * 60)
    
    state_machine, global_defs = get_sample_data()
    code_gen = get_code_generator()
    
    # role_functions リストの取得
    role_functions_list = code_gen._get_role_functions_list(state_machine)
    
    print(f"\n--- role_functions リスト ---")
    print(f"  数: {len(role_functions_list)}")
    for i, rf in enumerate(role_functions_list):
        print(f"  [{i}] name={rf.name}, return_type={rf.return_type}")
        print(f"      arg1_type={getattr(rf, 'arg1_type', 'N/A')}")
        print(f"      arg1_name={getattr(rf, 'arg1_name', 'N/A')}")
    
    # generate_all_declarations のテスト
    print("\n--- generate_all_declarations の結果 ---")
    decls = code_gen.role_func_gen.generate_all_declarations(role_functions_list)
    print(decls[:500])
    
    return code_gen, role_functions_list


def run_debug_tests():
    """デバッグテスト実行"""
    print("=" * 60)
    print("ロール関数ヘッダデバッグテスト")
    print("=" * 60)
    
    # RoleFunction データ構造の調査
    debug_role_function_data()
    
    # RoleFunctionGenerator の直接テスト
    rf_gen, test_func = debug_role_function_generator_direct()
    
    # CCodeGenerator の調査
    code_gen, role_functions_list = debug_c_code_generator_role_functions()
    
    # ヘッダ内容の調査
    header_content = debug_role_function_header()
    
    print("\n" + "=" * 60)
    print("デバッグ調査完了")
    print("=" * 60)


if __name__ == "__main__":
    run_debug_tests()