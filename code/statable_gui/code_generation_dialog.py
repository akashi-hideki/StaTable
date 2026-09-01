# statable_gui/code_generation_dialog.py
"""
Cコード生成ダイアログ（PySide6対応）
"""

import os
import sys
import json
import logging
from typing import Dict, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QFileDialog, QMessageBox,
    QComboBox, QGroupBox, QFormLayout,
    QProgressBar, QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from codegen.c_code_generator import CCodeGenerator
    from codegen.sample_data import SampleDataGenerator
    from codegen.config import CodeGenerationConfig, ConfigManager
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'codegen'))
    from c_code_generator import CCodeGenerator
    from sample_data import SampleDataGenerator
    from config import CodeGenerationConfig, ConfigManager

# 設定ダイアログをインポート
try:
    from .code_generation_settings_dialog import CodeGenerationSettingsDialog
except ImportError:
    from code_generation_settings_dialog import CodeGenerationSettingsDialog

logger = logging.getLogger(__name__)

# デフォルト設定ファイルパス
DEFAULT_SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "codegen_settings.json")


class CodeGenerationDialog(QDialog):
    """Cコード生成ダイアログ（PySide6対応）"""
    
    def __init__(self, state_machine=None, global_defs=None, parent=None, settings_file=None):
        super().__init__(parent)
        self.state_machine = state_machine
        self.global_defs = global_defs
        self.generated_files: Dict[str, str] = {}
        self.config_manager = ConfigManager()
        self.settings_file = settings_file or DEFAULT_SETTINGS_FILE
        
        self._load_saved_settings()
        
        self.setWindowTitle("Cコード生成")
        self.setMinimumSize(800, 600)
        
        self._setup_ui()
        self._load_sample_data_if_needed()
        self._load_config_to_ui()
    
    def _load_saved_settings(self):
        """前回の設定を読み込む"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if 'output_directory' in data:
                    self.config_manager.update(output_directory=data['output_directory'])
                if 'generation_style' in data:
                    self.config_manager.update(generation_style=data['generation_style'])
                if 'os_type' in data:
                    self.config_manager.update(os_type=data['os_type'])
                if 'save_with_merge' in data:
                    self.config_manager.update(save_with_merge=data['save_with_merge'])
                
                logger.info(f"前回の設定を読み込みました: {data}")
        except Exception as e:
            logger.warning(f"設定読み込みに失敗: {e}")
    
    def _save_settings(self):
        """現在の設定を保存"""
        try:
            config = self.config_manager.get_config()
            data = {
                'output_directory': config.output_directory,
                'generation_style': config.generation_style,
                'os_type': config.os_type,
                'save_with_merge': config.save_with_merge,
            }
            
            settings_dir = os.path.dirname(self.settings_file)
            if settings_dir and not os.path.exists(settings_dir):
                os.makedirs(settings_dir, exist_ok=True)
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"設定を保存しました: {data}")
        except Exception as e:
            logger.warning(f"設定保存に失敗: {e}")
    
    def _setup_ui(self):
        """UIを構築"""
        main_layout = QVBoxLayout(self)
        
        # 設定情報グループ
        info_group = QGroupBox("生成設定情報")
        info_layout = QFormLayout(info_group)
        
        # 出力先
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("出力先ディレクトリを選択")
        self.output_dir_edit.textChanged.connect(self._on_output_dir_changed)
        self.output_dir_btn = QPushButton("参照...")
        self.output_dir_btn.clicked.connect(self._select_output_dir)
        
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_edit)
        output_dir_layout.addWidget(self.output_dir_btn)
        
        info_layout.addRow("出力先:", output_dir_layout)
        
        # 生成スタイル
        self.style_combo = QComboBox()
        self.style_combo.addItem("テーブル駆動方式", "table_driven")
        self.style_combo.addItem("switch-case方式", "switch_case")
        self.style_combo.currentIndexChanged.connect(self._on_style_changed)
        info_layout.addRow("生成スタイル:", self.style_combo)
        
        # OS種別ラベル
        self.os_label = QLabel("NonRTOS")
        info_layout.addRow("OS種別:", self.os_label)
        
        # マージ設定ラベル
        self.merge_label = QLabel("有効")
        info_layout.addRow("マージ:", self.merge_label)
        
        # 詳細設定ボタン
        self.settings_btn = QPushButton("詳細設定...")
        self.settings_btn.clicked.connect(self._open_settings_dialog)
        info_layout.addRow("", self.settings_btn)
        
        main_layout.addWidget(info_group)
        
        # アクションボタン
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("コード生成")
        self.generate_btn.clicked.connect(self._generate_code)
        button_layout.addWidget(self.generate_btn)
        
        self.save_btn = QPushButton("保存")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._save_code)
        button_layout.addWidget(self.save_btn)
        
        self.close_btn = QPushButton("閉じる")
        self.close_btn.clicked.connect(self._on_close)
        button_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(button_layout)
        
        # プレビューエリア
        preview_label = QLabel("生成コードプレビュー:")
        main_layout.addWidget(preview_label)
        
        self.preview_tabs = QComboBox()
        self.preview_tabs.currentIndexChanged.connect(self._update_preview)
        main_layout.addWidget(self.preview_tabs)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Consolas", 10))
        main_layout.addWidget(self.preview_text)
        
        # プログレスバー
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
    
    def _load_sample_data_if_needed(self):
        """サンプルデータが未設定の場合にロード"""
        if self.state_machine is None or self.global_defs is None:
            sample_gen = SampleDataGenerator()
            self.state_machine, self.global_defs = sample_gen.get_sample_data()
            logger.info("サンプルデータをロードしました")
    
    def _load_config_to_ui(self):
        """設定をUIに反映"""
        config = self.config_manager.get_config()
        
        if config.output_directory:
            self.output_dir_edit.setText(config.output_directory)
        
        idx = self.style_combo.findData(config.generation_style)
        if idx >= 0:
            self.style_combo.setCurrentIndex(idx)
        
        self._update_info_labels(config)
    
    def _update_info_labels(self, config):
        """設定情報ラベルを更新"""
        os_names = {
            'non_rtos': 'NonRTOS（ベアメタル）',
            'freertos': 'FreeRTOS',
            'threadx': 'ThreadX',
        }
        self.os_label.setText(os_names.get(config.os_type, config.os_type))
        self.merge_label.setText("有効" if config.save_with_merge else "無効")
    
    def _on_output_dir_changed(self, text):
        """出力先変更時の処理"""
        self.config_manager.update(output_directory=text if text else "")
    
    def _select_output_dir(self):
        """出力先ディレクトリを選択"""
        current = self.output_dir_edit.text() or os.getcwd()
        dir_path = QFileDialog.getExistingDirectory(
            self, "出力先ディレクトリを選択", current
        )
        if dir_path:
            self.output_dir_edit.setText(dir_path)
            self.config_manager.update(output_directory=dir_path)
            self._save_settings()
    
    def _on_style_changed(self, index):
        """スタイル変更時の処理"""
        style = self.style_combo.currentData()
        self.config_manager.update(generation_style=style)
        self._save_settings()
    
    def _open_settings_dialog(self):
        """詳細設定ダイアログを開く"""
        dialog = CodeGenerationSettingsDialog(
            config_manager=self.config_manager,
            parent=self
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            self.config_manager.set_config(config)
            self._load_config_to_ui()
            self._save_settings()
            logger.info(f"設定更新: {config.to_dict()}")
    
    def _generate_code(self):
        """コード生成を実行"""
        if self.state_machine is None or self.global_defs is None:
            QMessageBox.warning(self, "警告", "ステートマシンとグローバル定義が設定されていません。")
            return
        
        output_dir = self.output_dir_edit.text().strip()
        if output_dir:
            self.config_manager.update(output_directory=output_dir)
        
        if not output_dir:
            QMessageBox.warning(self, "警告", "出力先ディレクトリを設定してください。")
            self._select_output_dir()
            output_dir = self.output_dir_edit.text().strip()
            if not output_dir:
                return
        
        config = self.config_manager.get_config()
        
        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        try:
            generator = CCodeGenerator(config=config)
            self.generated_files = generator.generate_all(self.state_machine, self.global_defs)
            
            self.preview_tabs.clear()
            for filename in self.generated_files.keys():
                self.preview_tabs.addItem(filename)
            
            self._update_preview()
            
            self.generate_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
            
            self._save_settings()
            
            QMessageBox.information(self, "完了", 
                f"{len(self.generated_files)}ファイルを生成しました。\n出力先: {output_dir}")
            
        except Exception as e:
            self.generate_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "エラー", f"コード生成に失敗しました:\n{e}")
    
    def _update_preview(self):
        """プレビューを更新"""
        filename = self.preview_tabs.currentText()
        if filename in self.generated_files:
            self.preview_text.setPlainText(self.generated_files[filename])
        else:
            self.preview_text.clear()
    
    def _save_code(self):
        """生成コードを保存"""
        if not self.generated_files:
            QMessageBox.warning(self, "警告", "生成されたコードがありません。")
            return
        
        output_dir = self.output_dir_edit.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "警告", "出力先ディレクトリを設定してください。")
            return
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            config = self.config_manager.get_config()
            generator = CCodeGenerator(config=config)
            
            if config.save_with_merge:
                saved_files = generator.save_generated_code_with_merge(self.generated_files, output_dir)
            else:
                saved_files = generator.save_generated_code(self.generated_files, output_dir)
            
            self._save_settings()
            
            QMessageBox.information(self, "保存完了", 
                f"{len(saved_files)}ファイルを保存しました。\n\n出力先: {output_dir}")
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"保存に失敗しました:\n{e}")
    
    def _on_close(self):
        """閉じる時の処理"""
        self._save_settings()
        self.reject()
    
    def get_generated_files(self) -> Dict[str, str]:
        """生成されたファイルを取得"""
        return self.generated_files
    
    def get_config(self):
        """現在の設定を取得"""
        return self.config_manager.get_config()