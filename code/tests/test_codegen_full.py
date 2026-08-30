# tests/test_codegen_full.py
"""
コード生成の完全テストプログラム
生成されたコードの内容・構造・整合性を検証する
"""

import sys
import os
import importlib.util
import traceback

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
    sample_module = load_module("full_sample_data", sample_data_path)
    sample_gen = sample_module.SampleDataGenerator()
    return sample_gen.get_sample_data()


def get_code_generator():
    """コード生成器を取得"""
    cgen_path = os.path.join(codegen_dir, "c_code_generator.py")
    cgen_module = load_module("full_c_code_generator", cgen_path)
    return cgen_module.CCodeGenerator()


def test_generate_all_files():
    """全ファイル生成テスト"""
    print("\n=== ファイル生成テスト ===")
    
    state_machine, global_defs = get_sample_data()
    code_gen = get_code_generator()
    
    generated_files = code_gen.generate_all(state_machine, global_defs)
    
    expected_files = [
        'statable_types.h',
        'statable_transitions.h',
        'statable_transitions.c',
        'statable_role_functions.h',
        'statable_role_functions.c',
        'statable_init.c',
    ]
    
    all_ok = True
    for filename in expected_files:
        if filename in generated_files:
            content = generated_files[filename]
            if len(content) > 0:
                print(f"  ✅ {filename}: {len(content)}文字")
            else:
                print(f"  ❌ {filename}: 空ファイル")
                all_ok = False
        else:
            print(f"  ❌ {filename}: 生成されていない")
            all_ok = False
    
    return generated_files, all_ok


def test_types_header_content(content):
    """型定義ヘッダの内容テスト"""
    print("\n=== 型定義ヘッダテスト ===")
    
    checks = [
        ('ファイルヘッダ', '/**' in content and '@file' in content),
        ('インクルードガード', '#ifndef STATABLE_TYPES_H' in content and '#endif' in content),
        ('stdint.h', '#include <stdint.h>' in content),
        ('stdbool.h', '#include <stdbool.h>' in content),
        ('string.h', '#include <string.h>' in content),
        ('状態列挙型', 'typedef enum {' in content and 'STATE_t' in content),
        ('イベント列挙型', 'EVENT_t' in content),
        ('フラグ列挙型', 'FLAG_t' in content),
        ('状態MAX', 'STATE_MAX' in content),
        ('イベントMAX', 'EVENT_MAX' in content),
        ('フラグMAX', 'FLAG_MAX' in content),
        ('SystemData_t', 'SystemData_t' in content),
        ('EventFlags_t', 'EventFlags_t' in content),
        ('SystemContext_t', 'SystemContext_t' in content),
        ('データマクロ', 'DATA_' in content),
        ('フラグマクロ', 'FLAG_' in content),
        ('状態値INIT', 'STATE_INIT' in content),
        ('状態値IDLE', 'STATE_IDLE' in content),
        ('状態値RUNNING', 'STATE_RUNNING' in content),
        ('状態値ERROR', 'STATE_ERROR' in content),
        ('イベント値POWER_ON', 'EVENT_POWER_ON' in content),
        ('イベント値START', 'EVENT_START' in content),
        ('イベント値STOP', 'EVENT_STOP' in content),
        ('イベント値ERROR_DETECTED', 'EVENT_ERROR_DETECTED' in content),
        ('ユーザー定義型', 'SystemStatus_t' in content),
        ('ユーザー定義型2', 'SensorData_t' in content),
        ('ビットフィールド', ': 1' in content),
        ('配列', '[64]' in content),
        ('構造体セミコロン', '} SystemStatus_t;' in content or '} SystemData_t;' in content),
    ]
    
    all_ok = True
    for check_name, result in checks:
        if result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_ok = False
    
    return all_ok


def test_transitions_header_content(content):
    """遷移関数ヘッダの内容テスト"""
    print("\n=== 遷移関数ヘッダテスト ===")
    
    checks = [
        ('ファイルヘッダ', '/**' in content),
        ('インクルードガード', '#ifndef STATABLE_TRANSITIONS_H' in content),
        ('types.h インクルード', '#include "statable_types.h"' in content),
        ('StateMachine_Process宣言', 'StateMachine_Process' in content),
        ('STATE_t引数', 'STATE_t current_state' in content),
        ('EVENT_t引数', 'EVENT_t event' in content),
        ('SystemContext_t引数', 'SystemContext_t *ctx' in content),
        ('戻り値STATE_t', 'STATE_t StateMachine_Process' in content),
        ('関数宣言セミコロン', ');' in content),
    ]
    
    all_ok = True
    for check_name, result in checks:
        if result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_ok = False
    
    return all_ok


def test_transitions_source_content(content):
    """遷移関数ソースの内容テスト"""
    print("\n=== 遷移関数ソーステスト ===")
    
    checks = [
        ('ファイルヘッダ', '/**' in content),
        ('transitions.h インクルード', '#include "statable_transitions.h"' in content),
        ('role_functions.h インクルード', '#include "statable_role_functions.h"' in content),
        ('遷移セル構造体', 'TransitionCell_t' in content),
        ('遷移テーブル', 'transition_matrix' in content),
        ('状態遷移関数', 'StateMachine_Process' in content),
        ('NULLチェック', 'ctx == NULL' in content),
        ('範囲チェック', 'STATE_MAX' in content and 'EVENT_MAX' in content),
        ('デバッグログ入口', 'LOG_DEBUG' in content),
        ('エラーログ', 'LOG_ERROR' in content),
        ('情報ログ', 'LOG_INFO' in content),
        ('条件チェック', 'cell->condition' in content),
        ('アクション実行', 'cell->action' in content),
        ('状態遷移', 'next_state' in content),
        ('戻り値', 'return next_state' in content),
        ('遷移INIT→IDLE', 'STATE_IDLE' in content),
        ('遷移IDLE→RUNNING', 'STATE_RUNNING' in content),
        ('遷移RUNNING→ERROR', 'STATE_ERROR' in content),
        ('条件関数', 'Condition_' in content),
        ('アクション関数', 'Action_' in content),
    ]
    
    all_ok = True
    for check_name, result in checks:
        if result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_ok = False
    
    return all_ok


def test_role_functions_header_content(content):
    """ロール関数ヘッダの内容テスト"""
    print("\n=== ロール関数ヘッダテスト ===")
    
    checks = [
        ('ファイルヘッダ', '/**' in content),
        ('インクルードガード', '#ifndef STATABLE_ROLE_FUNCTIONS_H' in content),
        ('types.h インクルード', '#include "statable_types.h"' in content),
        ('RoleFunc_PowerOn', 'RoleFunc_PowerOn' in content),
        ('RoleFunc_StartOk', 'RoleFunc_StartOk' in content),
        ('RoleFunc_Start', 'RoleFunc_Start' in content),
        ('RoleFunc_Stop', 'RoleFunc_Stop' in content),
        ('RoleFunc_HandleError', 'RoleFunc_HandleError' in content),
        ('RoleFunc_ProcessData', 'RoleFunc_ProcessData' in content),
        ('STATE_t引数', 'STATE_t *current_state' in content),
        ('SystemContext_t引数', 'SystemContext_t *ctx' in content),
        ('戻り値void', 'void RoleFunc_PowerOn' in content),
        ('戻り値bool', 'bool RoleFunc_StartOk' in content),
        ('戻り値int', 'int RoleFunc_ProcessData' in content),
        ('関数宣言セミコロン', ');' in content),
    ]
    
    all_ok = True
    for check_name, result in checks:
        if result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_ok = False
    
    return all_ok


def test_role_functions_source_content(content):
    """ロール関数ソースの内容テスト"""
    print("\n=== ロール関数ソーステスト ===")
    
    checks = [
        ('ファイルヘッダ', '/**' in content),
        ('role_functions.h インクルード', '#include "statable_role_functions.h"' in content),
        ('TODOコメント', 'TODO' in content),
        ('未使用引数警告抑制', '(void)current_state' in content),
        ('未使用引数ctx', '(void)ctx' in content),
        ('デバッグログ', 'LOG_DEBUG' in content),
        ('戻り値return', 'return' in content),
        ('空実装PowerOn', 'RoleFunc_PowerOn' in content),
        ('空実装StartOk', 'RoleFunc_StartOk' in content),
        ('引数付きProcessData', 'RoleFunc_ProcessData' in content),
        ('引数data', '(void)data' in content),
        ('引数len', '(void)len' in content),
    ]
    
    all_ok = True
    for check_name, result in checks:
        if result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_ok = False
    
    return all_ok


def test_init_source_content(content):
    """初期化ソースの内容テスト"""
    print("\n=== 初期化ソーステスト ===")
    
    checks = [
        ('ファイルヘッダ', '/**' in content),
        ('types.h インクルード', '#include "statable_types.h"' in content),
        ('SystemContext_Init関数', 'SystemContext_Init' in content),
        ('NULLチェック', 'ctx == NULL' in content),
        ('デバッグログ入口', 'LOG_DEBUG' in content),
        ('グローバル変数初期化', 'ctx->data' in content),
        ('イベントフラグ初期化', 'ctx->flags' in content),
        ('battery_voltage初期化', 'battery_voltage' in content),
        ('system_tick初期化', 'system_tick' in content),
        ('data_buffer初期化', 'memset' in content and 'data_buffer' in content),
        ('EVT_POWER_ON_REQ初期化', 'EVT_POWER_ON_REQ' in content),
        ('EVT_START_REQ初期化', 'EVT_START_REQ' in content),
    ]
    
    all_ok = True
    for check_name, result in checks:
        if result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_ok = False
    
    return all_ok


def test_generated_code_structure(generated_files):
    """生成コードの構造テスト"""
    print("\n=== 構造テスト ===")
    
    all_ok = True
    
    for filename, content in generated_files.items():
        if isinstance(content, str):
            print(f"  ✅ {filename}: 文字列型")
        else:
            print(f"  ❌ {filename}: 文字列型ではない")
            all_ok = False
    
    return all_ok


def test_save_generated_code(generated_files):
    """コード保存テスト"""
    print("\n=== 保存テスト ===")
    
    output_dir = os.path.join(current_dir, 'generated_output')
    code_gen = get_code_generator()
    
    try:
        saved_files = code_gen.save_generated_code(generated_files, output_dir)
        print(f"  ✅ {len(saved_files)}ファイル保存成功")
        
        for filepath in saved_files:
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                print(f"  ✅ {os.path.basename(filepath)}: {file_size}バイト")
            else:
                print(f"  ❌ {filepath}: 存在しない")
                return False
        
        return True
    except Exception as e:
        print(f"  ❌ 保存失敗: {e}")
        traceback.print_exc()
        return False


def test_c_compile_check(generated_files):
    """C言語としての構文チェック（簡易）"""
    print("\n=== C構文チェック（簡易） ===")
    
    all_ok = True
    
    # 中括弧のバランスチェック
    for filename, content in generated_files.items():
        open_braces = content.count('{')
        close_braces = content.count('}')
        
        if open_braces == close_braces:
            print(f"  ✅ {filename}: 中括弧バランスOK ({open_braces}個)")
        else:
            print(f"  ❌ {filename}: 中括弧不一致 (開:{open_braces}, 閉:{close_braces})")
            all_ok = False
    
    # 修正: セミコロンチェックはファイルタイプに応じて適切に判断
    # .h ファイルは関数宣言があれば `);` が必要
    # types.h は関数宣言がないので、構造体の `};` をチェック
    
    # statable_types.h は構造体定義のセミコロンをチェック
    types_content = generated_files.get('statable_types.h', '')
    if '};' in types_content:
        print(f"  ✅ statable_types.h: 構造体セミコロンOK")
    else:
        print(f"  ❌ statable_types.h: 構造体セミコロンなし")
        all_ok = False
    
    # 他のヘッダファイルは関数宣言のセミコロンをチェック
    header_files_with_functions = [
        'statable_transitions.h',
        'statable_role_functions.h',
    ]
    
    for filename in header_files_with_functions:
        content = generated_files.get(filename, '')
        if ');' in content:
            print(f"  ✅ {filename}: 関数宣言セミコロンOK")
        else:
            print(f"  ❌ {filename}: 関数宣言セミコロンなし")
            all_ok = False
    
    return all_ok


def test_full_output_display(generated_files):
    """生成コードの表示テスト"""
    print("\n=== 生成コードサンプル ===")
    
    for filename, content in generated_files.items():
        lines = content.split('\n')
        print(f"\n--- {filename} (先頭5行) ---")
        for line in lines[:5]:
            print(f"  {line}")
        print(f"  ... (全{len(lines)}行)")


def run_all_tests():
    """全テスト実行"""
    print("=" * 60)
    print("コード生成完全テスト")
    print("=" * 60)
    
    generated_files, files_ok = test_generate_all_files()
    
    if not files_ok:
        print("\n❌ ファイル生成に失敗")
        return False
    
    types_ok = test_types_header_content(generated_files['statable_types.h'])
    trans_h_ok = test_transitions_header_content(generated_files['statable_transitions.h'])
    trans_c_ok = test_transitions_source_content(generated_files['statable_transitions.c'])
    role_h_ok = test_role_functions_header_content(generated_files['statable_role_functions.h'])
    role_c_ok = test_role_functions_source_content(generated_files['statable_role_functions.c'])
    init_ok = test_init_source_content(generated_files['statable_init.c'])
    
    structure_ok = test_generated_code_structure(generated_files)
    save_ok = test_save_generated_code(generated_files)
    syntax_ok = test_c_compile_check(generated_files)
    
    test_full_output_display(generated_files)
    
    print("\n" + "=" * 60)
    print("テスト結果集計")
    print("=" * 60)
    
    all_results = {
        'ファイル生成': files_ok,
        '型定義ヘッダ': types_ok,
        '遷移関数ヘッダ': trans_h_ok,
        '遷移関数ソース': trans_c_ok,
        'ロール関数ヘッダ': role_h_ok,
        'ロール関数ソース': role_c_ok,
        '初期化ソース': init_ok,
        '構造テスト': structure_ok,
        '保存テスト': save_ok,
        'C構文チェック': syntax_ok,
    }
    
    all_passed = True
    for test_name, result in all_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("🎉 全テスト成功！")
    else:
        print("❌ 失敗したテストがあります")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)