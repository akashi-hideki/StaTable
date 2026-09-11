# statable_gui/code_generation_settings_dialog.py
"""
コード生成設定ダイアログ
- 基本設定、ログ設定、外部インクルード、出力設定のタブ構成
- 生成方式・テーブル方式は固定（テーブル駆動 + 配列方式のみ）
"""

import os
import sys
import logging
from typing import Dict, Optional, List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QGroupBox, QFormLayout,
    QCheckBox, QLineEdit, QFileDialog, QTabWidget,
    QWidget, QMessageBox, QDialogButtonBox, QListWidget,
    QListWidgetItem, QSpinBox, QAbstractItemView
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
    """コード生成設定ダイアログ"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.get_config()
        
        self.setWindowTitle("コード生成設定")
        self.setMinimumSize(600, 600)
        
        self._setup_ui()
        self._load_config()
    
    def _setup_ui(self):
        """UIを構築"""
        main_layout = QVBoxLayout(self)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # タブ
        self.basic_tab = QWidget()
        self._setup_basic_tab()
        self.tab_widget.addTab(self.basic_tab, "基本設定")
        
        # ログ設定タブ
        self.log_tab = QWidget()
        self._setup_log_tab()
        self.tab_widget.addTab(self.log_tab, "ログ設定")
        
        # 出力設定タブ
        self.include_tab = QWidget()
        self._setup_include_tab()
        self.tab_widget.addTab(self.include_tab, "外部インクルード")
        
        self.output_tab = QWidget()
        self._setup_output_tab()
        self.tab_widget.addTab(self.output_tab, "出力設定")
        
        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.reset_btn = QPushButton("リセット")
        self.reset_btn.clicked.connect(self._on_reset)
        button_layout.addWidget(self.reset_btn)
        
        self.cancel_btn = QPushButton("キャンセル")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self._on_ok)
        button_layout.addWidget(self.ok_btn)
        
        main_layout.addLayout(button_layout)
    
    def _setup_basic_tab(self):
        """基本設定タブ"""
        layout = QVBoxLayout(self.basic_tab)
        
        # ★ プロジェクト名
        project_group = QGroupBox("プロジェクト設定")
        project_layout = QFormLayout(project_group)
        
        self.project_name_edit = QLineEdit()
        self.project_name_edit.setPlaceholderText("例: MyProject")
        self.project_name_edit.setToolTip("生成ファイル名 <project_name>_run.c に使用されます")
        project_layout.addRow("プロジェクト名:", self.project_name_edit)
        
        layout.addWidget(project_group)
        
        # ★ 生成スタイル（固定表示）
        style_group = QGroupBox("生成スタイル")
        style_layout = QFormLayout(style_group)
        
        # 生成方式: 固定
        style_value_label = QLabel("テーブル駆動方式（セル単位関数 + 関数テーブル）")
        style_value_label.setStyleSheet("font-weight: bold;")
        style_layout.addRow("生成方式:", style_value_label)
        
        # テーブル方式: 固定
        table_value_label = QLabel("配列方式（2次元配列 + O(1) アクセス）")
        table_value_label.setStyleSheet("font-weight: bold;")
        style_layout.addRow("テーブル方式:", table_value_label)
        
        # 説明
        note_label = QLabel(
            "※ C言語向けに最適化された方式で固定されています。\n"
            "   セル単位の遷移関数を生成し、関数テーブルで管理します。"
        )
        note_label.setStyleSheet("color: gray; font-size: 10px; margin-left: 10px;")
        style_layout.addRow("", note_label)
        
        # OS種別（これは意味があるので選択可能）
        self.os_type_combo = QComboBox()
        self.os_type_combo.addItem("NonRTOS（ベアメタル）", "non_rtos")
        self.os_type_combo.addItem("FreeRTOS", "freertos")
        self.os_type_combo.addItem("ThreadX", "threadx")
        style_layout.addRow("OS種別:", self.os_type_combo)
        
        layout.addWidget(style_group)
        
        # 命名規則
        naming_group = QGroupBox("命名規則")
        naming_layout = QFormLayout(naming_group)
        
        self.naming_prefix_edit = QLineEdit()
        self.naming_prefix_edit.setPlaceholderText("関数名のプレフィックス（任意）")
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
        
        # 保留イベント制限
        pending_group = QGroupBox("保留イベント設定")
        pending_layout = QFormLayout(pending_group)
        
        self.max_pending_spin = QSpinBox()
        self.max_pending_spin.setRange(1, 255)
        self.max_pending_spin.setValue(16)
        self.max_pending_spin.setToolTip(
            "保留イベントの連続処理回数の上限。\n"
            "この回数を超えると無限ループを防止するため処理を打ち切ります。"
        )
        pending_layout.addRow("最大連続処理回数:", self.max_pending_spin)
        
        layout.addWidget(pending_group)
        layout.addStretch()
    
    def _setup_include_tab(self):
        """外部インクルード設定タブ"""
        layout = QVBoxLayout(self.include_tab)
        
        # 外部インクルードファイル
        include_group = QGroupBox("外部インクルードファイル")
        include_layout = QVBoxLayout(include_group)
        
        hint_label = QLabel(
            "Renesas Smart Configurator 等の生成ヘッダを指定します。\n"
            "指定したヘッダは、選択された挿入先に #include されます。"
        )
        hint_label.setStyleSheet("color: gray; font-size: 10px;")
        include_layout.addWidget(hint_label)
        
        self.include_list = QListWidget()
        self.include_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.include_list.setMinimumHeight(120)
        include_layout.addWidget(self.include_list)
        
        include_btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("追加...")
        add_btn.clicked.connect(self._on_add_include)
        include_btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("削除")
        remove_btn.clicked.connect(self._on_remove_include)
        include_btn_layout.addWidget(remove_btn)
        
        up_btn = QPushButton("上へ")
        up_btn.clicked.connect(self._on_move_include_up)
        include_btn_layout.addWidget(up_btn)
        
        down_btn = QPushButton("下へ")
        down_btn.clicked.connect(self._on_move_include_down)
        include_btn_layout.addWidget(down_btn)
        
        include_btn_layout.addStretch()
        include_layout.addLayout(include_btn_layout)
        
        layout.addWidget(include_group)
        
        # 挿入先
        target_group = QGroupBox("挿入先")
        target_layout = QVBoxLayout(target_group)
        
        self.include_in_super_check = QCheckBox("statable_all.h（ユーザー main.c 用）")
        target_layout.addWidget(self.include_in_super_check)
        
        self.include_in_role_check = QCheckBox("ロール関数 .c ファイル")
        target_layout.addWidget(self.include_in_role_check)
        
        self.include_in_transitions_check = QCheckBox("transitions .c ファイル")
        target_layout.addWidget(self.include_in_transitions_check)
        
        self.include_in_common_check = QCheckBox("共通 .c ファイル")
        target_layout.addWidget(self.include_in_common_check)
        
        layout.addWidget(target_group)
        layout.addStretch()
    
    def _setup_output_tab(self):
        """出力設定タブ"""
        layout = QVBoxLayout(self.output_tab)
        
        # 出力設定
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
        
        # フォルダ構成
        folder_group = QGroupBox("フォルダ構成")
        folder_layout = QFormLayout(folder_group)
        
        self.folder_structure_combo = QComboBox()
        self.folder_structure_combo.addItem("include/src分離（推奨）", "by_type")
        self.folder_structure_combo.addItem("層ごと", "by_layer")
        self.folder_structure_combo.addItem("フラット", "flat")
        folder_layout.addRow("構成:", self.folder_structure_combo)
        
        self.include_dir_edit = QLineEdit()
        folder_layout.addRow("includeフォルダ名:", self.include_dir_edit)
        
        self.source_dir_edit = QLineEdit()
        folder_layout.addRow("srcフォルダ名:", self.source_dir_edit)
        
        self.common_dir_edit = QLineEdit()
        folder_layout.addRow("共通フォルダ名:", self.common_dir_edit)
        
        self.project_dir_edit = QLineEdit()
        folder_layout.addRow("プロジェクトフォルダ名:", self.project_dir_edit)
        
        layout.addWidget(folder_group)
        
        # スーパーインクルード
        super_group = QGroupBox("スーパーインクルード")
        super_layout = QVBoxLayout(super_group)
        
        self.generate_super_check = QCheckBox("statable_all.h を生成する（ユーザー main.c 用）")
        super_layout.addWidget(self.generate_super_check)
        
        super_form = QFormLayout()
        self.super_include_name_edit = QLineEdit()
        super_form.addRow("ファイル名:", self.super_include_name_edit)
        
        self.super_include_dir_edit = QLineEdit()
        super_form.addRow("配置フォルダ:", self.super_include_dir_edit)
        
        super_layout.addLayout(super_form)
        
        layout.addWidget(super_group)
        
        # マージ設定
        merge_group = QGroupBox("マージ設定")
        merge_layout = QVBoxLayout(merge_group)
        
        self.save_with_merge_check = QCheckBox("既存ファイルとマージして保存（ユーザーコード保持）")
        merge_layout.addWidget(self.save_with_merge_check)
        
        layout.addWidget(merge_group)
        layout.addStretch()
    
    def _load_config(self):
        # プロジェクト名
        self.project_name_edit.setText(self.config.project_name)
        
        # ★ 生成方式・テーブル方式は固定のため、内部設定を強制
        self.config.generation_style = "table_driven"
        self.config.table_type = "array"
        
        # OS種別
        idx = self.os_type_combo.findData(self.config.os_type)
        if idx >= 0:
            self.os_type_combo.setCurrentIndex(idx)
        
        # 命名規則
        self.naming_prefix_edit.setText(self.config.naming_prefix)
        self.state_prefix_edit.setText(self.config.state_prefix)
        self.event_prefix_edit.setText(self.config.event_prefix)
        self.flag_prefix_edit.setText(self.config.flag_prefix)
        
        # コメント
        self.enable_comments_check.setChecked(self.config.enable_comments)
        self.enable_doxygen_check.setChecked(self.config.enable_doxygen)
        self.enable_markers_check.setChecked(self.config.enable_user_markers)
        
        # ログ
        self.enable_debug_logs_check.setChecked(self.config.enable_debug_logs)
        self.enable_info_logs_check.setChecked(self.config.enable_info_logs)
        self.enable_error_logs_check.setChecked(self.config.enable_error_logs)
        
        # 保留イベント
        self.max_pending_spin.setValue(self.config.max_consecutive_pending_events)
        
        # 外部インクルード
        self.include_list.clear()
        for inc in self.config.external_includes:
            self.include_list.addItem(inc)
        
        self.include_in_super_check.setChecked(self.config.external_includes_in_super)
        self.include_in_role_check.setChecked(self.config.external_includes_in_role)
        self.include_in_transitions_check.setChecked(self.config.external_includes_in_transitions)
        self.include_in_common_check.setChecked(self.config.external_includes_in_common)
        
        # 出力
        self.output_dir_edit.setText(self.config.output_directory)
        self.save_with_merge_check.setChecked(self.config.save_with_merge)
        
        # フォルダ構成
        idx = self.folder_structure_combo.findData(self.config.folder_structure)
        if idx >= 0:
            self.folder_structure_combo.setCurrentIndex(idx)
        
        self.include_dir_edit.setText(self.config.include_dir_name)
        self.source_dir_edit.setText(self.config.source_dir_name)
        self.common_dir_edit.setText(self.config.common_dir_name)
        self.project_dir_edit.setText(self.config.project_dir_name)
        
        # スーパーインクルード
        self.generate_super_check.setChecked(self.config.generate_super_include)
        self.super_include_name_edit.setText(self.config.super_include_file)
        self.super_include_dir_edit.setText(self.config.super_include_dir)
    
    def _save_config(self):
        # プロジェクト名
        self.config.project_name = self.project_name_edit.text().strip() or "MyProject"
        
        # ★ 生成方式・テーブル方式は固定
        self.config.generation_style = "table_driven"
        self.config.table_type = "array"
        
        # OS種別
        self.config.os_type = self.os_type_combo.currentData()
        
        # 命名規則
        self.config.naming_prefix = self.naming_prefix_edit.text()
        self.config.state_prefix = self.state_prefix_edit.text() or "STATE"
        self.config.event_prefix = self.event_prefix_edit.text() or "EVENT"
        self.config.flag_prefix = self.flag_prefix_edit.text() or "FLAG"
        
        # コメント
        self.config.enable_comments = self.enable_comments_check.isChecked()
        self.config.enable_doxygen = self.enable_doxygen_check.isChecked()
        self.config.enable_user_markers = self.enable_markers_check.isChecked()
        
        # ログ
        self.config.enable_debug_logs = self.enable_debug_logs_check.isChecked()
        self.config.enable_info_logs = self.enable_info_logs_check.isChecked()
        self.config.enable_error_logs = self.enable_error_logs_check.isChecked()
        
        # 保留イベント
        self.config.max_consecutive_pending_events = self.max_pending_spin.value()
        
        # 外部インクルード
        self.config.external_includes = [
            self.include_list.item(i).text()
            for i in range(self.include_list.count())
        ]
        self.config.external_includes_in_super = self.include_in_super_check.isChecked()
        self.config.external_includes_in_role = self.include_in_role_check.isChecked()
        self.config.external_includes_in_transitions = self.include_in_transitions_check.isChecked()
        self.config.external_includes_in_common = self.include_in_common_check.isChecked()
        
        # 出力
        self.config.output_directory = self.output_dir_edit.text()
        self.config.save_with_merge = self.save_with_merge_check.isChecked()
        
        # フォルダ構成
        self.config.folder_structure = self.folder_structure_combo.currentData()
        self.config.include_dir_name = self.include_dir_edit.text() or "include"
        self.config.source_dir_name = self.source_dir_edit.text() or "src"
        self.config.common_dir_name = self.common_dir_edit.text() or "common"
        self.config.project_dir_name = self.project_dir_edit.text() or "project"
        
        # スーパーインクルード
        self.config.generate_super_include = self.generate_super_check.isChecked()
        self.config.super_include_file = self.super_include_name_edit.text() or "statable_all.h"
        self.config.super_include_dir = self.super_include_dir_edit.text() or "common"
        
        self.config_manager.set_config(self.config)
    
    def _on_ok(self):
        """OKボタン"""
        self._save_config()
        self.accept()
    
    def _on_reset(self):
        """リセットボタン"""
        reply = QMessageBox.question(
            self, "確認", "設定をリセットしますか？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
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
    
    # ===== 外部インクルード操作 =====
    def _on_add_include(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "外部インクルードファイルを選択", "",
            "Header files (*.h);;All files (*)"
        )
        if files:
            for f in files:
                # パスからファイル名のみ取得（既存の登録方法に合わせる）
                name = os.path.basename(f)
                # 重複チェック
                existing = [
                    self.include_list.item(i).text()
                    for i in range(self.include_list.count())
                ]
                if name not in existing:
                    self.include_list.addItem(name)
    
    def _on_remove_include(self):
        row = self.include_list.currentRow()
        if row >= 0:
            self.include_list.takeItem(row)
    
    def _on_move_include_up(self):
        row = self.include_list.currentRow()
        if row > 0:
            item = self.include_list.takeItem(row)
            self.include_list.insertItem(row - 1, item)
            self.include_list.setCurrentRow(row - 1)
    
    def _on_move_include_down(self):
        row = self.include_list.currentRow()
        if 0 <= row < self.include_list.count() - 1:
            item = self.include_list.takeItem(row)
            self.include_list.insertItem(row + 1, item)
            self.include_list.setCurrentRow(row + 1)
    
    def get_config(self) -> CodeGenerationConfig:
        """設定を取得"""
        return self.config