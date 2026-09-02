# validation_dialog_runner.py
"""
検証・AI連携ダイアログを表示するスタンドアロンスクリプト
実行: python validation_dialog_runner.py
"""

import sys
import os
import logging

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'codegen'))
sys.path.insert(0, os.path.join(current_dir, 'statable'))
sys.path.insert(0, os.path.join(current_dir, 'statable_gui'))

# ロガー設定（INFOレベルにして過剰なデバッグ出力を抑制）
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt

from validate.validator import CodeGenerationValidator
from validate.prompt_generator import AIPromptGenerator
from validate.response_parser import AIResponseParser
from validate.change_applier import ChangeApplier
from validate.clipboard_manager import ClipboardManager

# validation_dialog.py をロード
import importlib.util

def load_validation_dialog():
    """validation_dialog.pyをロード"""
    dialog_path = os.path.join(current_dir, 'statable_gui', 'validation_dialog.py')
    if not os.path.exists(dialog_path):
        print(f"エラー: {dialog_path} が見つかりません")
        return None
    
    spec = importlib.util.spec_from_file_location("validation_dialog_module", dialog_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_sample_data():
    """サンプルデータを取得"""
    sample_path = os.path.join(current_dir, 'codegen', 'sample_data.py')
    spec = importlib.util.spec_from_file_location("sample_data_module", sample_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sample_gen = module.SampleDataGenerator()
    return sample_gen.get_sample_data()


class MainWindow(QMainWindow):
    """検証ダイアログを開くためのメインウィンドウ"""
    
    def __init__(self, validation_module, sm, gd):
        super().__init__()
        self.validation_module = validation_module
        self.sm = sm
        self.gd = gd
        
        self.setWindowTitle("検証・AI連携テスト")
        self.setMinimumSize(400, 300)
        
        # 中央ウィジェット
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 説明ラベル
        info_label = QLabel(
            "検証・AI連携ダイアログのテスト\n\n"
            "「検証ダイアログを開く」ボタンをクリックしてください。"
        )
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        # ダイアログ表示ボタン
        open_btn = QPushButton("検証ダイアログを開く")
        open_btn.setMinimumHeight(50)
        open_btn.clicked.connect(self._open_validation_dialog)
        layout.addWidget(open_btn)
        
        # データ情報
        data_label = QLabel(
            f"状態数: {len(sm.states)}\n"
            f"イベント数: {len(sm.events)}\n"
            f"遷移数: {len(sm.transitions)}\n"
            f"変数数: {len(gd.variables)}\n"
            f"フラグ数: {len(gd.flags)}"
        )
        layout.addWidget(data_label)
    
    def _open_validation_dialog(self):
        """検証ダイアログを開く"""
        dialog = self.validation_module.ValidationDialog(self.sm, self.gd, self)
        dialog.exec()


def main():
    """メイン関数"""
    print("=" * 60)
    print("検証・AI連携ダイアログ スタンドアロン実行")
    print("=" * 60)
    
    # QApplication を作成
    app = QApplication(sys.argv)
    
    # 検証ダイアログモジュールをロード
    validation_module = load_validation_dialog()
    if validation_module is None:
        print("検証ダイアログのロードに失敗しました")
        return 1
    
    # サンプルデータを取得
    sm, gd = get_sample_data()
    print(f"サンプルデータ: 状態={len(sm.states)}, イベント={len(sm.events)}, 遷移={len(sm.transitions)}")
    
    # メインウィンドウを作成
    window = MainWindow(validation_module, sm, gd)
    window.show()
    
    # イベントループ開始
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())