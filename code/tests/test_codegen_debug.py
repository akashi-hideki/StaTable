# tests/test_codegen_debug.py
"""
コード生成の失敗原因特定テスト
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
    sample_module = load_module("debug_sample_data", sample_data_path)
    sample_gen = sample_module.SampleDataGenerator()
    return sample_gen.get_sample_data()


def get_code_generator():
    """コード生成器を取得"""
    cgen_path = os.path.join(codegen_dir, "c_code_generator.py")
    cgen_module = load_module("debug_c_code_generator", cgen_path)
    return cgen_module.CCodeGenerator()


def debug_types_header():
    """型定義ヘッダの内容を調査"""
    print("\n" + "=" * 60)
    print("型定義ヘッダの調査")
    print("=" * 60)
    
    state_machine, global_defs = get_sample_data()
    code_gen = get_code_generator()
    
    content = code_gen.generate_file('statable_types.h', state_machine, global_defs)
    
    # ユーザー定義型の調査
    print("\n--- ユーザー定義型の調査 ---")
    print(f"custom_types 数: {len(global_defs.custom_types)}")
    for i, ct in enumerate(global_defs.custom_types):
        print(f"  [{i}] name={ct.name}, title={ct.title}")
        print(f"      members={len(ct.members)}")
        for j, m in enumerate(ct.members):
            print(f"        [{j}] name={m.name}, type={m.data_type}, bit_width={m.bit_width}, array_size={m.array_size}")
    
    # SystemStatus_t の検索
    print("\n--- SystemStatus_t の検索 ---")
    if 'SystemStatus_t' in content:
        print("  ✅ SystemStatus_t が見つかりました")
        idx = content.find('SystemStatus_t')
        print(f"  位置: {idx}")
        print(f"  前後: ...{content[max(0,idx-50):idx+50]}...")
    else:
        print("  ❌ SystemStatus_t が見つかりません")
    
    # SensorData_t の検索
    print("\n--- SensorData_t の検索 ---")
    if 'SensorData_t' in content:
        print("  ✅ SensorData_t が見つかりました")
        idx = content.find('SensorData_t')
        print(f"  位置: {idx}")
        print(f"  前後: ...{content[max(0,idx-50):idx+50]}...")
    else:
        print("  ❌ SensorData_t が見つかりません")
    
    # custom_types セクションの確認
    print("\n--- custom_types セクションの確認 ---")
    if 'ユーザー定義型' in content:
        print("  ✅ 'ユーザー定義型' セクションあり")
        idx = content.find('ユーザー定義型')
        print(f"  位置: {idx}")
        print(f"  内容: ...{content[idx:idx+200]}...")
    else:
        print("  ❌ 'ユーザー定義型' セクションなし")
    
    # 生成された内容の関連部分を表示
    print("\n--- 生成内容（custom_types関連） ---")
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'custom' in line.lower() or 'SystemStatus' in line or 'SensorData' in line:
            print(f"  Line {i}: {line}")
    
    return content


def debug_transitions_source():
    """遷移関数ソースの内容を調査"""
    print("\n" + "=" * 60)
    print("遷移関数ソースの調査")
    print("=" * 60)
    
    state_machine, global_defs = get_sample_data()
    code_gen = get_code_generator()
    
    content = code_gen.generate_file('statable_transitions.c', state_machine, global_defs)
    
    # StateMachine_Process の検索
    print("\n--- StateMachine_Process の検索 ---")
    if 'StateMachine_Process' in content:
        print("  ✅ StateMachine_Process が見つかりました")
        idx = content.find('StateMachine_Process')
        print(f"  位置: {idx}")
        print(f"  前後: ...{content[max(0,idx-30):idx+80]}...")
    else:
        print("  ❌ StateMachine_Process が見つかりません")
    
    # LOG_DEBUG の検索
    print("\n--- LOG_DEBUG の検索 ---")
    if 'LOG_DEBUG' in content:
        print("  ✅ LOG_DEBUG が見つかりました")
        count = content.count('LOG_DEBUG')
        print(f"  出現回数: {count}")
        idx = content.find('LOG_DEBUG')
        print(f"  最初の位置: {idx}")
        print(f"  前後: ...{content[max(0,idx-30):idx+80]}...")
    else:
        print("  ❌ LOG_DEBUG が見つかりません")
    
    # LOG_ERROR の検索
    print("\n--- LOG_ERROR の検索 ---")
    if 'LOG_ERROR' in content:
        print("  ✅ LOG_ERROR が見つかりました")
        count = content.count('LOG_ERROR')
        print(f"  出現回数: {count}")
        idx = content.find('LOG_ERROR')
        print(f"  最初の位置: {idx}")
    else:
        print("  ❌ LOG_ERROR が見つかりません")
    
    # LOG_INFO の検索
    print("\n--- LOG_INFO の検索 ---")
    if 'LOG_INFO' in content:
        print("  ✅ LOG_INFO が見つかりました")
        count = content.count('LOG_INFO')
        print(f"  出現回数: {count}")
        idx = content.find('LOG_INFO')
        print(f"  最初の位置: {idx}")
    else:
        print("  ❌ LOG_INFO が見つかりません")
    
    # 生成された内容の関連部分を表示
    print("\n--- 生成内容（関数部分） ---")
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'StateMachine' in line or 'LOG_' in line or 'next_state' in line:
            print(f"  Line {i}: {line}")
    
    return content


def debug_role_functions():
    """ロール関数の内容を調査"""
    print("\n" + "=" * 60)
    print("ロール関数の調査")
    print("=" * 60)
    
    state_machine, global_defs = get_sample_data()
    code_gen = get_code_generator()
    
    # role_functions の内容確認
    print("\n--- role_functions の確認 ---")
    print(f"role_functions 数: {len(state_machine.role_functions)}")
    for name, rf in state_machine.role_functions.items():
        print(f"  {name}: return_type={rf.return_type}, title={getattr(rf, 'title', 'N/A')}")
        print(f"    arg1_type={getattr(rf, 'arg1_type', '')}, arg1_name={getattr(rf, 'arg1_name', '')}")
        print(f"    arg2_type={getattr(rf, 'arg2_type', '')}, arg2_name={getattr(rf, 'arg2_name', '')}")
    
    # ヘッダ生成
    header_content = code_gen.generate_file('statable_role_functions.h', state_machine, global_defs)
    
    print("\n--- ロール関数ヘッダの内容 ---")
    for name in state_machine.role_functions.keys():
        func_name = f"RoleFunc_{name}"
        if func_name in header_content:
            print(f"  ✅ {func_name} が見つかりました")
        else:
            print(f"  ❌ {func_name} が見つかりません")
    
    # 戻り値の確認
    print("\n--- 戻り値の確認 ---")
    for name, rf in state_machine.role_functions.items():
        return_type = rf.return_type
        if return_type == 'void':
            search_str = f"void RoleFunc_{name}"
        elif return_type == 'bool':
            search_str = f"bool RoleFunc_{name}"
        else:
            search_str = f"{return_type} RoleFunc_{name}"
        
        if search_str in header_content:
            print(f"  ✅ {name}: '{search_str}' が見つかりました")
        else:
            print(f"  ❌ {name}: '{search_str}' が見つかりません")
    
    # ソース生成
    source_content = code_gen.generate_file('statable_role_functions.c', state_machine, global_defs)
    
    print("\n--- ロール関数ソースの内容 ---")
    for name in state_machine.role_functions.keys():
        func_name = f"RoleFunc_{name}"
        if func_name in source_content:
            print(f"  ✅ {func_name} が見つかりました")
        else:
            print(f"  ❌ {func_name} が見つかりません")
    
    # 生成されたヘッダの関連部分を表示
    print("\n--- 生成されたヘッダ（先頭50行） ---")
    lines = header_content.split('\n')
    for i, line in enumerate(lines[:50]):
        print(f"  Line {i}: {line}")
    
    return header_content, source_content


def debug_role_function_generator():
    """RoleFunctionGenerator を直接テスト"""
    print("\n" + "=" * 60)
    print("RoleFunctionGenerator の直接テスト")
    print("=" * 60)
    
    # ジェネレータをロード
    rf_gen_path = os.path.join(codegen_dir, "role_function_generator.py")
    rf_module = load_module("debug_role_function_generator", rf_gen_path)
    rf_gen = rf_module.RoleFunctionGenerator()
    
    # テスト用のRoleFunction
    from statable.model import RoleFunction
    
    test_funcs = [
        RoleFunction(name="PowerOn", return_type="void", description="電源ON処理"),
        RoleFunction(name="StartOk", return_type="bool", description="開始条件チェック"),
        RoleFunction(name="ProcessData", return_type="int",
                    arg1_type="uint8_t*", arg1_name="data",
                    arg2_type="uint16_t", arg2_name="len",
                    description="データ処理"),
    ]
    
    for func in test_funcs:
        print(f"\n--- {func.name} ---")
        print(f"  return_type: {func.return_type}")
        print(f"  title: {getattr(func, 'title', 'N/A')}")
        print(f"  description: {func.description}")
        
        # 関数名生成
        func_name = rf_gen._generate_function_name(func)
        print(f"  生成された関数名: {func_name}")
        
        # 宣言生成
        try:
            decl = rf_gen.generate_function('declaration', func)
            print(f"  宣言生成成功:")
            print(f"  {decl}")
        except Exception as e:
            print(f"  ❌ 宣言生成失敗: {e}")
            import traceback
            traceback.print_exc()
        
        # 実装生成
        try:
            impl = rf_gen.generate_function('implementation', func)
            print(f"  実装生成成功:")
            print(f"  {impl[:200]}...")
        except Exception as e:
            print(f"  ❌ 実装生成失敗: {e}")
            import traceback
            traceback.print_exc()


def debug_state_machine_data():
    """StateMachine のデータ構造を調査"""
    print("\n" + "=" * 60)
    print("StateMachine データ構造の調査")
    print("=" * 60)
    
    state_machine, global_defs = get_sample_data()
    
    print(f"\n--- states ---")
    print(f"型: {type(state_machine.states)}")
    for name, state in state_machine.states.items():
        print(f"  {name}: type={getattr(state, 'type', 'N/A')}, title={getattr(state, 'title', 'N/A')}")
    
    print(f"\n--- events ---")
    print(f"型: {type(state_machine.events)}")
    for name, event in state_machine.events.items():
        print(f"  {name}: kind={getattr(event, 'kind', 'N/A')}, title={getattr(event, 'title', 'N/A')}")
    
    print(f"\n--- transitions ---")
    print(f"型: {type(state_machine.transitions)}")
    for i, t in enumerate(state_machine.transitions):
        print(f"  [{i}] source={t.source}, event={t.event}, target={t.target}")
        print(f"      condition={getattr(t, 'condition', 'N/A')}, action={getattr(t, 'action', 'N/A')}")
        print(f"      title={getattr(t, 'title', 'N/A')}")
    
    print(f"\n--- role_functions ---")
    print(f"型: {type(state_machine.role_functions)}")
    for name, rf in state_machine.role_functions.items():
        print(f"  {name}: return_type={rf.return_type}")
        print(f"    title={getattr(rf, 'title', 'N/A')}")
        print(f"    description={getattr(rf, 'description', 'N/A')}")
        print(f"    arg1_type={getattr(rf, 'arg1_type', 'N/A')}")
        print(f"    arg1_name={getattr(rf, 'arg1_name', 'N/A')}")
        print(f"    arg2_type={getattr(rf, 'arg2_type', 'N/A')}")
        print(f"    arg2_name={getattr(rf, 'arg2_name', 'N/A')}")


def run_debug_tests():
    """デバッグテスト実行"""
    print("=" * 60)
    print("コード生成デバッグテスト")
    print("=" * 60)
    
    # StateMachine データ構造の調査
    debug_state_machine_data()
    
    # RoleFunctionGenerator の直接テスト
    debug_role_function_generator()
    
    # 型定義ヘッダの調査
    types_content = debug_types_header()
    
    # 遷移関数ソースの調査
    transitions_content = debug_transitions_source()
    
    # ロール関数の調査
    header_content, source_content = debug_role_functions()
    
    print("\n" + "=" * 60)
    print("デバッグ調査完了")
    print("=" * 60)


if __name__ == "__main__":
    run_debug_tests()