# statable_gui/code_generation_settings_dialog.py
"""\nCode generation settings dialog\n- Tab structure: basic settings, log settings, external include, output settings\n- Generation style / table style are fixed (table-driven + array style only)\n"""

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

# Path settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from codegen.config import CodeGenerationConfig, ConfigManager
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'codegen'))
    from config import CodeGenerationConfig, ConfigManager

logger = logging.getLogger(__name__)


class CodeGenerationSettingsDialog(QDialog):
    """Code generation settingsダイアログ"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.get_config()
        
        self.setWindowTitle("Code generation settings")
        self.setMinimumSize(600, 600)
        
        self._setup_ui()
        self._load_config()
    
    def _setup_ui(self):
        """Build UI"""
        main_layout = QVBoxLayout(self)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Tab
        self.basic_tab = QWidget()
        self._setup_basic_tab()
        self.tab_widget.addTab(self.basic_tab, "Basic settings")
        
        # Log設定タブ
        self.log_tab = QWidget()
        self._setup_log_tab()
        self.tab_widget.addTab(self.log_tab, "Log settings")
        
        # Output settingsタブ
        self.include_tab = QWidget()
        self._setup_include_tab()
        self.tab_widget.addTab(self.include_tab, "External include")
        
        self.output_tab = QWidget()
        self._setup_output_tab()
        self.tab_widget.addTab(self.output_tab, "Output settings")
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self._on_reset)
        button_layout.addWidget(self.reset_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self._on_ok)
        button_layout.addWidget(self.ok_btn)
        
        main_layout.addLayout(button_layout)
    
    def _setup_basic_tab(self):
        """Basic settings tab"""
        layout = QVBoxLayout(self.basic_tab)
        
        # ★ Project name
        project_group = QGroupBox("Project settings")
        project_layout = QFormLayout(project_group)
        
        self.project_name_edit = QLineEdit()
        self.project_name_edit.setPlaceholderText("Example: MyProject")
        self.project_name_edit.setToolTip("Used as the generated file name <project_name>_run.c")
        project_layout.addRow("Project name:", self.project_name_edit)
        
        layout.addWidget(project_group)
        
        # Generation style (fixed display)
        style_group = QGroupBox("Generation style")
        style_layout = QFormLayout(style_group)
        
        # Generation style: fixed
        style_value_label = QLabel("Table-driven style (cell-level function + function table)")
        style_value_label.setStyleSheet("font-weight: bold;")
        style_layout.addRow("Generation style:", style_value_label)
        
        # Table style: fixed
        table_value_label = QLabel("Array方式（2次元Array + O(1) アクセス）")
        table_value_label.setStyleSheet("font-weight: bold;")
        style_layout.addRow("Table style:", table_value_label)
        
        # description
        note_label = QLabel(
            "* Fixed to a style optimized for C.\n"
            "   Generates cell-level transition functions, managed by a function table."
        )
        note_label.setStyleSheet("color: gray; font-size: 10px; margin-left: 10px;")
        style_layout.addRow("", note_label)
        
        # OS type（これは意味があるのでSelection可能）
        self.os_type_combo = QComboBox()
        self.os_type_combo.addItem("NonRTOS (bare metal)", "non_rtos")
        self.os_type_combo.addItem("FreeRTOS", "freertos")
        self.os_type_combo.addItem("ThreadX", "threadx")
        style_layout.addRow("OS type:", self.os_type_combo)
        
        layout.addWidget(style_group)
        
        # Naming convention
        naming_group = QGroupBox("Naming convention")
        naming_layout = QFormLayout(naming_group)
        
        self.naming_prefix_edit = QLineEdit()
        self.naming_prefix_edit.setPlaceholderText("Function nameのプレフィックス（任意）")
        naming_layout.addRow("Prefix:", self.naming_prefix_edit)
        
        self.state_prefix_edit = QLineEdit()
        naming_layout.addRow("State prefix:", self.state_prefix_edit)
        
        self.event_prefix_edit = QLineEdit()
        naming_layout.addRow("Event prefix:", self.event_prefix_edit)
        
        self.flag_prefix_edit = QLineEdit()
        naming_layout.addRow("Flag prefix:", self.flag_prefix_edit)
        
        layout.addWidget(naming_group)
        
        # comment設定
        comment_group = QGroupBox("Comment settings")
        comment_layout = QVBoxLayout(comment_group)
        
        self.enable_comments_check = QCheckBox("Generate comments")
        comment_layout.addWidget(self.enable_comments_check)
        
        self.enable_doxygen_check = QCheckBox("Generate Doxygen-style comments")
        comment_layout.addWidget(self.enable_doxygen_check)
        
        self.enable_markers_check = QCheckBox("Generate user code markers")
        comment_layout.addWidget(self.enable_markers_check)
        
        layout.addWidget(comment_group)
        layout.addStretch()
    
    def _setup_log_tab(self):
        """Log settings tab"""
        layout = QVBoxLayout(self.log_tab)
        
        log_group = QGroupBox("Debug log settings")
        log_layout = QVBoxLayout(log_group)
        
        self.enable_debug_logs_check = QCheckBox("Generate DEBUG logs")
        log_layout.addWidget(self.enable_debug_logs_check)
        
        self.enable_info_logs_check = QCheckBox("Generate INFO logs")
        log_layout.addWidget(self.enable_info_logs_check)
        
        self.enable_error_logs_check = QCheckBox("Generate ERROR logs")
        log_layout.addWidget(self.enable_error_logs_check)
        
        layout.addWidget(log_group)
        
        # Pending event制限
        pending_group = QGroupBox("Pending event settings")
        pending_layout = QFormLayout(pending_group)
        
        self.max_pending_spin = QSpinBox()
        self.max_pending_spin.setRange(1, 255)
        self.max_pending_spin.setValue(16)
        self.max_pending_spin.setToolTip(
            "Upper limit of consecutive pending events.\n"
            "Processing is aborted beyond this count to prevent infinite loops."
        )
        pending_layout.addRow("Max consecutive processing:", self.max_pending_spin)
        
        layout.addWidget(pending_group)
        layout.addStretch()
    
    def _setup_include_tab(self):
        """External include settings tab"""
        layout = QVBoxLayout(self.include_tab)
        
        # External includeファイル
        include_group = QGroupBox("External include file")
        include_layout = QVBoxLayout(include_group)
        
        hint_label = QLabel(
            "Specify a generated header such as Renesas Smart Configurator output.\n"
            "The specified header is #include'd into the selected insertion target."
        )
        hint_label.setStyleSheet("color: gray; font-size: 10px;")
        include_layout.addWidget(hint_label)
        
        self.include_list = QListWidget()
        self.include_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.include_list.setMinimumHeight(120)
        include_layout.addWidget(self.include_list)
        
        include_btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add...")
        add_btn.clicked.connect(self._on_add_include)
        include_btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Delete")
        remove_btn.clicked.connect(self._on_remove_include)
        include_btn_layout.addWidget(remove_btn)
        
        up_btn = QPushButton("Move up")
        up_btn.clicked.connect(self._on_move_include_up)
        include_btn_layout.addWidget(up_btn)
        
        down_btn = QPushButton("Move down")
        down_btn.clicked.connect(self._on_move_include_down)
        include_btn_layout.addWidget(down_btn)
        
        include_btn_layout.addStretch()
        include_layout.addLayout(include_btn_layout)
        
        layout.addWidget(include_group)
        
        # Insert先
        target_group = QGroupBox("Insert先")
        target_layout = QVBoxLayout(target_group)
        
        self.include_in_super_check = QCheckBox("statable_all.h (for user main.c)")
        target_layout.addWidget(self.include_in_super_check)
        
        self.include_in_role_check = QCheckBox("Role function .c ファイル")
        target_layout.addWidget(self.include_in_role_check)
        
        self.include_in_transitions_check = QCheckBox("transitions .c file")
        target_layout.addWidget(self.include_in_transitions_check)
        
        self.include_in_common_check = QCheckBox("common .c file")
        target_layout.addWidget(self.include_in_common_check)
        
        layout.addWidget(target_group)
        layout.addStretch()
    
    def _setup_output_tab(self):
        """Output settingsタブ"""
        layout = QVBoxLayout(self.output_tab)
        
        # Output settings
        output_group = QGroupBox("Output settings")
        output_layout = QFormLayout(output_group)
        
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Output directory")
        self.output_dir_btn = QPushButton("Browse...")
        self.output_dir_btn.clicked.connect(self._select_output_dir)
        
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_edit)
        output_dir_layout.addWidget(self.output_dir_btn)
        
        output_layout.addRow("Output directory:", output_dir_layout)
        
        layout.addWidget(output_group)
        
        # Folder structure
        folder_group = QGroupBox("Folder structure")
        folder_layout = QFormLayout(folder_group)
        
        self.folder_structure_combo = QComboBox()
        self.folder_structure_combo.addItem("include/src separation (recommended)", "by_type")
        self.folder_structure_combo.addItem("Per layer", "by_layer")
        self.folder_structure_combo.addItem("Flat", "flat")
        folder_layout.addRow("Structure:", self.folder_structure_combo)
        
        self.include_dir_edit = QLineEdit()
        folder_layout.addRow("include folder name:", self.include_dir_edit)
        
        self.source_dir_edit = QLineEdit()
        folder_layout.addRow("src folder name:", self.source_dir_edit)
        
        self.common_dir_edit = QLineEdit()
        folder_layout.addRow("Common folder name:", self.common_dir_edit)
        
        self.project_dir_edit = QLineEdit()
        folder_layout.addRow("Project folder name:", self.project_dir_edit)
        
        layout.addWidget(folder_group)
        
        # Super include
        super_group = QGroupBox("Super include")
        super_layout = QVBoxLayout(super_group)
        
        self.generate_super_check = QCheckBox("Generate statable_all.h (for user main.c)")
        super_layout.addWidget(self.generate_super_check)
        
        super_form = QFormLayout()
        self.super_include_name_edit = QLineEdit()
        super_form.addRow("File name:", self.super_include_name_edit)
        
        self.super_include_dir_edit = QLineEdit()
        super_form.addRow("Placement folder:", self.super_include_dir_edit)
        
        super_layout.addLayout(super_form)
        
        layout.addWidget(super_group)
        
        # Merge settings
        merge_group = QGroupBox("Merge settings")
        merge_layout = QVBoxLayout(merge_group)
        
        self.save_with_merge_check = QCheckBox("既存ファイルとマージしてSave（ユーザーCode保持）")
        merge_layout.addWidget(self.save_with_merge_check)
        
        layout.addWidget(merge_group)
        layout.addStretch()
    
    def _load_config(self):
        # Project name
        self.project_name_edit.setText(self.config.project_name)
        
        # Generation style / table style are fixed, so force internal settings
        self.config.generation_style = "table_driven"
        self.config.table_type = "array"
        
        # OS type
        idx = self.os_type_combo.findData(self.config.os_type)
        if idx >= 0:
            self.os_type_combo.setCurrentIndex(idx)
        
        # Naming convention
        self.naming_prefix_edit.setText(self.config.naming_prefix)
        self.state_prefix_edit.setText(self.config.state_prefix)
        self.event_prefix_edit.setText(self.config.event_prefix)
        self.flag_prefix_edit.setText(self.config.flag_prefix)
        
        # comment
        self.enable_comments_check.setChecked(self.config.enable_comments)
        self.enable_doxygen_check.setChecked(self.config.enable_doxygen)
        self.enable_markers_check.setChecked(self.config.enable_user_markers)
        
        # Log
        self.enable_debug_logs_check.setChecked(self.config.enable_debug_logs)
        self.enable_info_logs_check.setChecked(self.config.enable_info_logs)
        self.enable_error_logs_check.setChecked(self.config.enable_error_logs)
        
        # Pending event
        self.max_pending_spin.setValue(self.config.max_consecutive_pending_events)
        
        # External include
        self.include_list.clear()
        for inc in self.config.external_includes:
            self.include_list.addItem(inc)
        
        self.include_in_super_check.setChecked(self.config.external_includes_in_super)
        self.include_in_role_check.setChecked(self.config.external_includes_in_role)
        self.include_in_transitions_check.setChecked(self.config.external_includes_in_transitions)
        self.include_in_common_check.setChecked(self.config.external_includes_in_common)
        
        # Output
        self.output_dir_edit.setText(self.config.output_directory)
        self.save_with_merge_check.setChecked(self.config.save_with_merge)
        
        # Folder structure
        idx = self.folder_structure_combo.findData(self.config.folder_structure)
        if idx >= 0:
            self.folder_structure_combo.setCurrentIndex(idx)
        
        self.include_dir_edit.setText(self.config.include_dir_name)
        self.source_dir_edit.setText(self.config.source_dir_name)
        self.common_dir_edit.setText(self.config.common_dir_name)
        self.project_dir_edit.setText(self.config.project_dir_name)
        
        # Super include
        self.generate_super_check.setChecked(self.config.generate_super_include)
        self.super_include_name_edit.setText(self.config.super_include_file)
        self.super_include_dir_edit.setText(self.config.super_include_dir)
    
    def _save_config(self):
        # Project name
        self.config.project_name = self.project_name_edit.text().strip() or "MyProject"
        
        # Generation style / table style fixed
        self.config.generation_style = "table_driven"
        self.config.table_type = "array"
        
        # OS type
        self.config.os_type = self.os_type_combo.currentData()
        
        # Naming convention
        self.config.naming_prefix = self.naming_prefix_edit.text()
        self.config.state_prefix = self.state_prefix_edit.text() or "STATE"
        self.config.event_prefix = self.event_prefix_edit.text() or "EVENT"
        self.config.flag_prefix = self.flag_prefix_edit.text() or "FLAG"
        
        # comment
        self.config.enable_comments = self.enable_comments_check.isChecked()
        self.config.enable_doxygen = self.enable_doxygen_check.isChecked()
        self.config.enable_user_markers = self.enable_markers_check.isChecked()
        
        # Log
        self.config.enable_debug_logs = self.enable_debug_logs_check.isChecked()
        self.config.enable_info_logs = self.enable_info_logs_check.isChecked()
        self.config.enable_error_logs = self.enable_error_logs_check.isChecked()
        
        # Pending event
        self.config.max_consecutive_pending_events = self.max_pending_spin.value()
        
        # External include
        self.config.external_includes = [
            self.include_list.item(i).text()
            for i in range(self.include_list.count())
        ]
        self.config.external_includes_in_super = self.include_in_super_check.isChecked()
        self.config.external_includes_in_role = self.include_in_role_check.isChecked()
        self.config.external_includes_in_transitions = self.include_in_transitions_check.isChecked()
        self.config.external_includes_in_common = self.include_in_common_check.isChecked()
        
        # Output
        self.config.output_directory = self.output_dir_edit.text()
        self.config.save_with_merge = self.save_with_merge_check.isChecked()
        
        # Folder structure
        self.config.folder_structure = self.folder_structure_combo.currentData()
        self.config.include_dir_name = self.include_dir_edit.text() or "include"
        self.config.source_dir_name = self.source_dir_edit.text() or "src"
        self.config.common_dir_name = self.common_dir_edit.text() or "common"
        self.config.project_dir_name = self.project_dir_edit.text() or "project"
        
        # Super include
        self.config.generate_super_include = self.generate_super_check.isChecked()
        self.config.super_include_file = self.super_include_name_edit.text() or "statable_all.h"
        self.config.super_include_dir = self.super_include_dir_edit.text() or "common"
        
        self.config_manager.set_config(self.config)
    
    def _on_ok(self):
        """OK button"""
        self._save_config()
        self.accept()
    
    def _on_reset(self):
        """Reset button"""
        reply = QMessageBox.question(
            self, "Confirm", "Reset settings?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.config_manager.reset()
            self.config = self.config_manager.get_config()
            self._load_config()
    
    def _select_output_dir(self):
        """Select output directory"""
        current = self.output_dir_edit.text() or os.getcwd()
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select output directory", current
        )
        if dir_path:
            self.output_dir_edit.setText(dir_path)
    
    # ===== External include操作 =====
    def _on_add_include(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "External include fileをSelection", "",
            "Header files (*.h);;All files (*)"
        )
        if files:
            for f in files:
                # Extract only the file name from the path (consistent with existing registration)
                name = os.path.basename(f)
                # Duplicate check
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
        """Get settings"""
        return self.config