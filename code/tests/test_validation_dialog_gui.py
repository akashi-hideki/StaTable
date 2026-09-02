# tests/test_validation_dialog_gui.py
"""
検証・AI連携GUIの単体テスト
直接実行: python tests/test_validation_dialog_gui.py
"""

import sys
import os
import json
import importlib.util
import logging

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
codegen_dir = os.path.join(project_root, 'codegen')
statable_dir = os.path.join(project_root, 'statable')
gui_dir = os.path.join(project_root, 'statable_gui')

sys.path.insert(0, project_root)
sys.path.insert(0, codegen_dir)
sys.path.insert(0, statable_dir)
sys.path.insert(0, gui_dir)

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_validation_dialog")

# 結果カウンタ
PASS_COUNT = 0
FAIL_COUNT = 0
FAILED_ITEMS = []

# QApplicationを最初に作成
app = None
try:
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False


def log_result(name, success, detail=""):
    global PASS_COUNT, FAIL_COUNT
    if success:
        PASS_COUNT += 1
        print(f"  ✅ {name}")
    else:
        FAIL_COUNT += 1
        FAILED_ITEMS.append(name)
        print(f"  ❌ {name} {detail}")


def load_module(name, path):
    """モジュールをロード"""
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"    → ロード失敗: {e}")
        return None


def get_sample_data():
    """サンプルデータを取得"""
    sample_path = os.path.join(codegen_dir, "sample_data.py")
    sample_module = load_module("test_dialog_sample", sample_path)
    if sample_module is None:
        return None, None
    sample_gen = sample_module.SampleDataGenerator()
    return sample_gen.get_sample_data()


def mock_message_boxes():
    """QMessageBoxをモック化して表示されないようにする"""
    try:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information = lambda *args, **kwargs: QMessageBox.StandardButton.Ok
        QMessageBox.warning = lambda *args, **kwargs: QMessageBox.StandardButton.Ok
        QMessageBox.critical = lambda *args, **kwargs: QMessageBox.StandardButton.Ok
        return True
    except Exception:
        return False


def test_dialog_file_exists():
    """validation_dialog.pyの存在確認"""
    print("\n=== ダイアログファイル確認 ===")
    
    dialog_path = os.path.join(gui_dir, "validation_dialog.py")
    exists = os.path.exists(dialog_path)
    log_result("validation_dialog.py", exists, f"(パス: {dialog_path})")
    return exists


def test_dialog_module_load():
    """validation_dialog.pyのロード確認"""
    print("\n=== ダイアログモジュールロード ===")
    
    dialog_path = os.path.join(gui_dir, "validation_dialog.py")
    module = load_module("test_validation_dialog_module", dialog_path)
    
    if module is None:
        log_result("モジュールロード", False)
        return False
    
    log_result("ValidationDialog", hasattr(module, 'ValidationDialog'))
    log_result("show_validation_dialog", hasattr(module, 'show_validation_dialog'))
    return True


def test_dialog_creation():
    """ダイアログの作成確認"""
    print("\n=== ダイアログ作成 ===")
    
    if not PYSIDE_AVAILABLE:
        log_result("PySide6", False, "(利用不可)")
        return
    
    dialog_path = os.path.join(gui_dir, "validation_dialog.py")
    module = load_module("test_dialog_create", dialog_path)
    if module is None:
        log_result("モジュールロード", False)
        return
    
    sm, gd = get_sample_data()
    if sm is None or gd is None:
        log_result("サンプルデータ", False)
        return
    
    try:
        dlg = module.ValidationDialog(sm, gd)
        log_result("ダイアログ作成", dlg is not None)
        log_result("ウィンドウタイトル", dlg.windowTitle() == "コード生成前検証・AI診断")
        log_result("タブ数", dlg.tab_widget.count() == 4, f"({dlg.tab_widget.count()}タブ)")
        dlg.close()
        return True
    except Exception as e:
        log_result("ダイアログ作成", False, f"({e})")
        return False


def test_validation_execution():
    """検証実行の確認"""
    print("\n=== 検証実行 ===")
    
    if not PYSIDE_AVAILABLE:
        log_result("PySide6", False, "(利用不可)")
        return
    
    dialog_path = os.path.join(gui_dir, "validation_dialog.py")
    module = load_module("test_dialog_validation", dialog_path)
    if module is None:
        log_result("モジュールロード", False)
        return
    
    sm, gd = get_sample_data()
    if sm is None or gd is None:
        log_result("サンプルデータ", False)
        return
    
    dlg = module.ValidationDialog(sm, gd)
    
    # 検証結果
    log_result("検証結果あり", dlg.validation_result is not None)
    
    # サマリーラベル
    summary_text = dlg.summary_label.text()
    log_result("サマリー表示", len(summary_text) > 0, f"({summary_text})")
    
    # 問題リスト
    issue_count = dlg.issue_tree.topLevelItemCount()
    log_result("問題リスト", issue_count >= 0, f"({issue_count}件)")
    
    # プロンプトプレビュー
    prompt_text = dlg.prompt_preview.toPlainText()
    log_result("プロンプト生成", len(prompt_text) > 100, f"({len(prompt_text)}文字)")
    
    dlg.close()


def test_copy_prompt():
    """プロンプトコピーの確認"""
    print("\n=== プロンプトコピー ===")
    
    if not PYSIDE_AVAILABLE:
        log_result("PySide6", False, "(利用不可)")
        return
    
    mock_message_boxes()
    
    dialog_path = os.path.join(gui_dir, "validation_dialog.py")
    module = load_module("test_dialog_copy", dialog_path)
    if module is None:
        log_result("モジュールロード", False)
        return
    
    sm, gd = get_sample_data()
    dlg = module.ValidationDialog(sm, gd)
    
    # コピー処理
    try:
        dlg._copy_prompt()
        log_result("_copy_prompt()実行", True)
    except Exception as e:
        log_result("_copy_prompt()実行", False, f"({e})")
    
    # クリップボード確認
    try:
        clipboard_text = dlg.clipboard.get_from_clipboard()
        log_result("クリップボード内容", len(clipboard_text) > 100, f"({len(clipboard_text)}文字)")
        log_result("JSON含む", 'JSON' in clipboard_text)
        log_result("changes含む", 'changes' in clipboard_text)
    except Exception as e:
        log_result("クリップボード確認", False, f"({e})")
    
    dlg.close()


def test_parse_response():
    """AI回答解析の確認"""
    print("\n=== AI回答解析 ===")
    
    if not PYSIDE_AVAILABLE:
        log_result("PySide6", False, "(利用不可)")
        return
    
    mock_message_boxes()
    
    dialog_path = os.path.join(gui_dir, "validation_dialog.py")
    module = load_module("test_dialog_parse", dialog_path)
    if module is None:
        log_result("モジュールロード", False)
        return
    
    sm, gd = get_sample_data()
    dlg = module.ValidationDialog(sm, gd)
    
    # AI回答を設定
    ai_response = '''{
  "changes": [
    {
      "action": "set_initial",
      "params": {"state": "INIT"},
      "reason": "初期状態が未設定"
    },
    {
      "action": "add_transition",
      "params": {"source": "ERROR", "event": "STOP", "target": "IDLE"},
      "reason": "エラー回復"
    }
  ]
}'''
    dlg.response_edit.setPlainText(ai_response)
    
    # 解析実行
    try:
        dlg._parse_response()
        log_result("_parse_response()実行", True)
    except Exception as e:
        log_result("_parse_response()実行", False, f"({e})")
    
    # 解析結果
    log_result("解析された変更数", len(dlg.parsed_changes) == 2, f"({len(dlg.parsed_changes)}件)")
    
    # 変更一覧表示
    change_count = dlg.change_tree.topLevelItemCount()
    log_result("変更一覧表示", change_count == 2, f"({change_count}件)")
    
    # タブ切り替え
    current_tab = dlg.tab_widget.currentIndex()
    log_result("タブ切り替え", current_tab == 3, f"(タブ: {current_tab})")
    
    dlg.close()


def test_apply_changes():
    """変更反映の確認"""
    print("\n=== 変更反映 ===")
    
    if not PYSIDE_AVAILABLE:
        log_result("PySide6", False, "(利用不可)")
        return
    
    mock_message_boxes()
    
    dialog_path = os.path.join(gui_dir, "validation_dialog.py")
    module = load_module("test_dialog_apply", dialog_path)
    if module is None:
        log_result("モジュールロード", False)
        return
    
    sm, gd = get_sample_data()
    dlg = module.ValidationDialog(sm, gd)
    
    # AI回答を設定して解析
    ai_response = '''{
  "changes": [
    {"action": "set_initial", "params": {"state": "INIT"}, "reason": "初期状態"}
  ]
}'''
    dlg.response_edit.setPlainText(ai_response)
    dlg._parse_response()
    
    # 初期状態をリセット
    sm.initial_state = None
    
    # 変更反映
    try:
        dlg._apply_changes()
        log_result("_apply_changes()実行", True)
    except Exception as e:
        log_result("_apply_changes()実行", False, f"({e})")
    
    # 反映確認
    log_result("初期状態反映", sm.initial_state == 'INIT', f"(initial_state={sm.initial_state})")
    
    dlg.close()


def test_full_gui_flow():
    """GUIフルフローの確認"""
    print("\n=== GUIフルフロー ===")
    
    if not PYSIDE_AVAILABLE:
        log_result("PySide6", False, "(利用不可)")
        return
    
    mock_message_boxes()
    
    dialog_path = os.path.join(gui_dir, "validation_dialog.py")
    module = load_module("test_dialog_flow", dialog_path)
    if module is None:
        log_result("モジュールロード", False)
        return
    
    sm, gd = get_sample_data()
    
    # 初期状態をリセット
    sm.initial_state = None
    
    dlg = module.ValidationDialog(sm, gd)
    
    # Step 1: 検証
    log_result("Step 1: 検証実行", dlg.validation_result is not None)
    log_result("Step 1: 初期状態エラー検出", 
               any(i.code == 'STATE_NO_INITIAL' for i in dlg.validation_result.issues))
    
    # Step 2: プロンプト生成
    prompt = dlg.prompt_generator.generate_diagnosis_prompt(sm, gd, dlg.validation_result)
    log_result("Step 2: プロンプト生成", len(prompt) > 100)
    
    # Step 3: AI回答（シミュレーション）
    ai_response = '''{
  "changes": [
    {"action": "set_initial", "params": {"state": "INIT"}, "reason": "初期状態が未設定のため"}
  ]
}'''
    dlg.response_edit.setPlainText(ai_response)
    
    # Step 4: 解析
    dlg._parse_response()
    log_result("Step 4: 解析", len(dlg.parsed_changes) == 1)
    
    # Step 5: 反映
    dlg._apply_changes()
    log_result("Step 5: 反映", sm.initial_state == 'INIT')
    
    # Step 6: 再検証
    dlg._run_validation()
    log_result("Step 6: 再検証", 
               not any(i.code == 'STATE_NO_INITIAL' for i in dlg.validation_result.issues))
    
    dlg.close()


def run_all_tests():
    """全テスト実行"""
    global PASS_COUNT, FAIL_COUNT, FAILED_ITEMS
    PASS_COUNT = 0
    FAIL_COUNT = 0
    FAILED_ITEMS = []
    
    print("=" * 60)
    print("検証・AI連携GUI 単体テスト")
    print("=" * 60)
    
    test_dialog_file_exists()
    test_dialog_module_load()
    test_dialog_creation()
    test_validation_execution()
    test_copy_prompt()
    test_parse_response()
    test_apply_changes()
    test_full_gui_flow()
    
    print("\n" + "=" * 60)
    print("テスト結果")
    print("=" * 60)
    print(f"  合格: {PASS_COUNT}")
    print(f"  失敗: {FAIL_COUNT}")
    
    if FAILED_ITEMS:
        print("\n  失敗項目:")
        for item in FAILED_ITEMS:
            print(f"    - {item}")
    
    print("=" * 60)
    
    if FAIL_COUNT == 0:
        print("🎉 全テスト成功！")
        return True
    else:
        print("❌ 失敗したテストがあります")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)