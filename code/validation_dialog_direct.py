# validation_dialog_direct.py
"""
検証ダイアログを直接表示する
実行: python validation_dialog_direct.py
"""

import sys
import os
import logging
import importlib.util

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'codegen'))
sys.path.insert(0, os.path.join(current_dir, 'statable'))
sys.path.insert(0, os.path.join(current_dir, 'statable_gui'))

# ロガー設定（WARNINGに抑制して過剰な出力を防ぐ）
logging.basicConfig(level=logging.WARNING)

from PySide6.QtWidgets import QApplication


def load_module_from_file(module_name, filepath):
    """モジュールをファイルからロード"""
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    """メイン関数"""
    print("検証ダイアログを起動します...")
    
    # QApplication を最初に作成
    app = QApplication(sys.argv)
    
    # validation_dialog.py をロード
    dialog_path = os.path.join(current_dir, 'statable_gui', 'validation_dialog.py')
    if not os.path.exists(dialog_path):
        print(f"エラー: {dialog_path} が見つかりません")
        return 1
    
    validation_module = load_module_from_file("validation_dialog_direct", dialog_path)
    
    # sample_data.py をロード
    sample_path = os.path.join(current_dir, 'codegen', 'sample_data.py')
    sample_module = load_module_from_file("sample_data_direct", sample_path)
    
    # サンプルデータを取得
    sample_gen = sample_module.SampleDataGenerator()
    sm, gd = sample_gen.get_sample_data()
    
    print(f"データ: 状態={len(sm.states)}, イベント={len(sm.events)}, 遷移={len(sm.transitions)}")
    
    # 検証ダイアログを直接表示
    dialog = validation_module.ValidationDialog(sm, gd)
    dialog.show()  # show()で非モーダル表示
    
    print("ダイアログを表示しました。閉じると終了します。")
    
    # イベントループ開始
    exit_code = app.exec()
    
    print("ダイアログを閉じました。")
    return exit_code


if __name__ == '__main__':
    sys.exit(main())