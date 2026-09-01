# statable_gui/code_generation_settings_dialog.py
"""
コード生成設定ダイアログ（PySide6対応）
"""

import os
import sys
import logging
from typing import Dict, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QGroupBox, QFormLayout,
    QCheckBox, QLineEdit, QFileDialog, QTabWidget,
    QWidget, QMessageBox, QDialogButtonBox
)
from PySide6.QtCore import Qt

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from codegen.config import CodeGenerationConfig, ConfigManager
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'codegen'))
    from config import CodeGenerationConfig, ConfigManager

logger = logging.getLogger(__name__)


class CodeGenerationSettingsDialog(QDialog):
    """コード生成設定ダイアログ（PySide6対応）"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.get_config()
        
        self.setWindowTitle("コード生成設定")
        self.setMinimumSize(500, 400)
        
        self._setup_ui()
        self._load_config()
    
    def _setup_ui(self):
        """UIを構築"""
        main_layout = QVBoxLayout(self)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 基本設定タブ
        self.basic_tab = QWidget()
        self._setup_basic_tab()
        self.tab_widget.addTab(self.basic_tab, "基本設定")
        
        # ログ設定タブ
        self.log_tab = QWidget()
        self._setup_log_tab()
        self.tab_widget.addTab(self.log_tab, "ログ設定")
        
        # 出力設定タブ
        self.output_tab = QWidget()
        self._setup_output_tab()
        self.tab_widget.addTab(self.output_tab, "出力設定")
        
        # ボタン
        button_layout = QHBoxLayout()
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self._on_ok)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("キャンセル")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.reset_btn = QPushButton("リセット")
        self.reset_btn.clicked.connect(self._on_reset)
        button_layout.addWidget(self.reset_btn)
        
        main_layout.addLayout(button_layout)
    
    def _setup_basic_tab(self):
        """基本設定タブ"""
        layout = QVBoxLayout(self.basic_tab)
        
        # 生成スタイルグループ
        style_group = QGroupBox("生成スタイル")
        style_layout = QFormLayout(style_group)
        
        self.style_combo = QComboBox()
        self.style_combo.addItem("テーブル駆動方式", "table_driven")
        self.style_combo.addItem("switch-case方式", "switch_case")
        style_layout.addRow("生成方式:", self.style_combo)
        
        self.table_type_combo = QComboBox()
        self.table_type_combo.addItem("配列方式", "array")
        self.table_type_combo.addItem("switch-case方式", "switch")
        self.table_type_combo.addItem("辞書方式（非推奨）", "dictionary")
        style_layout.addRow("テーブル方式:", self.table_type_combo)
        
        self.os_type_combo = QComboBox()
        self.os_type_combo.addItem("NonRTOS（ベアメタル）", "non_rtos")
        self.os_type_combo.addItem("FreeRTOS", "freertos")
        self.os_type_combo.addItem("ThreadX", "threadx")
        style_layout.addRow("OS種別:", self.os_type_combo)
        
        layout.addWidget(style_group)
        
        # 命名規則グループ
        naming_group = QGroupBox("命名規則")
        naming_layout = QFormLayout(naming_group)
        
        self.naming_prefix_edit = QLineEdit()
        self.naming_prefix_edit.setPlaceholderText("関数名のプレフィックス")
        naming_layout.addRow("プレフィックス:", self.naming_prefix_edit)
        
        self.state_prefix_edit = QLineEdit()
        naming_layout.addRow("状態プレフィックス:", self.state_prefix_edit)
        
        self.event_prefix_edit = QLineEdit()
        naming_layout.addRow("イベントプレフィックス:", self.event_prefix_edit)
        
        self.flag_prefix_edit = QLineEdit()
        naming_layout.addRow("フラグプレフィックス:", self.flag_prefix_edit)
        
        layout.addWidget(naming_group)
        
        # コメント設定
        comment_group = QGroupBox("コメント設定")
        comment_layout = QVBoxLayout(comment_group)
        
        self.enable_comments_check = QCheckBox("コメントを生成する")
        comment_layout.addWidget(self.enable_comments_check)
        
        self.enable_doxygen_check = QCheckBox("Doxygen形式のコメントを生成する")
        comment_layout.addWidget(self.enable_doxygen_check)
        
        self.enable_markers_check = QCheckBox("ユーザーコードマーカーを生成する")
        comment_layout.addWidget(self.enable_markers_check)
        
        layout.addWidget(comment_group)
        layout.addStretch()
    
    def _setup_log_tab(self):
        """ログ設定タブ"""
        layout = QVBoxLayout(self.log_tab)
        
        log_group = QGroupBox("デバッグログ設定")
        log_layout = QVBoxLayout(log_group)
        
        self.enable_debug_logs_check = QCheckBox("DEBUGログを生成する")
        log_layout.addWidget(self.enable_debug_logs_check)
        
        self.enable_info_logs_check = QCheckBox("INFOログを生成する")
        log_layout.addWidget(self.enable_info_logs_check)
        
        self.enable_error_logs_check = QCheckBox("ERRORログを生成する")
        log_layout.addWidget(self.enable_error_logs_check)
        
        layout.addWidget(log_group)
        layout.addStretch()
    
    def _setup_output_tab(self):
        """出力設定タブ"""
        layout = QVBoxLayout(self.output_tab)
        
        output_group = QGroupBox("出力設定")
        output_layout = QFormLayout(output_group)
        
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("出力先ディレクトリ")
        self.output_dir_btn = QPushButton("参照...")
        self.output_dir_btn.clicked.connect(self._select_output_dir)
        
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_edit)
        output_dir_layout.addWidget(self.output_dir_btn)
        
        output_layout.addRow("出力先:", output_dir_layout)
        
        layout.addWidget(output_group)
        
        merge_group = QGroupBox("マージ設定")
        merge_layout = QVBoxLayout(merge_group)
        
        self.save_with_merge_check = QCheckBox("既存ファイルとマージして保存する（ユーザーコード保持）")
        merge_layout.addWidget(self.save_with_merge_check)
        
        layout.addWidget(merge_group)
        layout.addStretch()
    
    def _load_config(self):
        """設定を読み込む"""
        # スタイル
        idx = self.style_combo.findData(self.config.generation_style)
        if idx >= 0:
            self.style_combo.setCurrentIndex(idx)
        
        idx = self.table_type_combo.findData(self.config.table_type)
        if idx >= 0:
            self.table_type_combo.setCurrentIndex(idx)
        
        idx = self.os_type_combo.findData(self.config.os_type)
        if idx >= 0:
            self.os_type_combo.setCurrentIndex(idx)
        
        # 命名規則
        self.naming_prefix_edit.setText(self.config.naming_prefix)
        self.state_prefix_edit.setText(self.config.state_prefix)
        self.event_prefix_edit.setText(self.config.event_prefix)
        self.flag_prefix_edit.setText(self.config.flag_prefix)
        
        # コメント設定
        self.enable_comments_check.setChecked(self.config.enable_comments)
        self.enable_doxygen_check.setChecked(self.config.enable_doxygen)
        self.enable_markers_check.setChecked(self.config.enable_user_markers)
        
        # ログ設定
        self.enable_debug_logs_check.setChecked(self.config.enable_debug_logs)
        self.enable_info_logs_check.setChecked(self.config.enable_info_logs)
        self.enable_error_logs_check.setChecked(self.config.enable_error_logs)
        
        # 出力設定
        self.output_dir_edit.setText(self.config.output_directory)
        self.save_with_merge_check.setChecked(self.config.save_with_merge)
    
    def _save_config(self):
        """設定を保存"""
        self.config.generation_style = self.style_combo.currentData()
        self.config.table_type = self.table_type_combo.currentData()
        self.config.os_type = self.os_type_combo.currentData()
        
        self.config.naming_prefix = self.naming_prefix_edit.text()
        self.config.state_prefix = self.state_prefix_edit.text() or "STATE"
        self.config.event_prefix = self.event_prefix_edit.text() or "EVENT"
        self.config.flag_prefix = self.flag_prefix_edit.text() or "FLAG"
        
        self.config.enable_comments = self.enable_comments_check.isChecked()
        self.config.enable_doxygen = self.enable_doxygen_check.isChecked()
        self.config.enable_user_markers = self.enable_markers_check.isChecked()
        
        self.config.enable_debug_logs = self.enable_debug_logs_check.isChecked()
        self.config.enable_info_logs = self.enable_info_logs_check.isChecked()
        self.config.enable_error_logs = self.enable_error_logs_check.isChecked()
        
        self.config.output_directory = self.output_dir_edit.text()
        self.config.save_with_merge = self.save_with_merge_check.isChecked()
        
        self.config_manager.set_config(self.config)
    
    def _on_ok(self):
        """OKボタン"""
        self._save_config()
        self.accept()
    
    def _on_reset(self):
        """リセットボタン"""
        self.config_manager.reset()
        self.config = self.config_manager.get_config()
        self._load_config()
    
    def _select_output_dir(self):
        """出力先ディレクトリを選択"""
        current = self.output_dir_edit.text() or os.getcwd()
        dir_path = QFileDialog.getExistingDirectory(
            self, "出力先ディレクトリを選択", current
        )
        if dir_path:
            self.output_dir_edit.setText(dir_path)
    
    def get_config(self) -> CodeGenerationConfig:
        """設定を取得"""
        return self.config