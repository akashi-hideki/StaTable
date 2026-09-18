# statable_gui/code_generation_dialog.py
"""\nC code generation dialog (PySide6 compatible / multi-layer support)\n"""

import os
import sys
import json
import logging
from typing import Dict, Optional, List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QFileDialog, QMessageBox,
    QComboBox, QGroupBox, QFormLayout,
    QProgressBar, QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# Path settings
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

try:
    from codegen.c_code_generator import CCodeGenerator
    from codegen.sample_data import SampleDataGenerator
    from codegen.config import (
        CodeGenerationConfig, ConfigManager,
    )
except ImportError:
    sys.path.append(os.path.join(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        ),
        'codegen',
    ))
    from c_code_generator import CCodeGenerator
    from sample_data import SampleDataGenerator
    from config import (
        CodeGenerationConfig, ConfigManager,
    )

#Import the settings dialog
try:
    from .code_generation_settings_dialog import (
        CodeGenerationSettingsDialog,
    )
except ImportError:
    from code_generation_settings_dialog import (
        CodeGenerationSettingsDialog,
    )

logger = logging.getLogger(__name__)

#Default settings file path
DEFAULT_SETTINGS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "codegen_settings.json",
)


# ============================================================
# Warning collector class
# ============================================================
class WarningCollector(logging.Handler):
    """\n    Handler that collects logs at WARNING level or higher\n\n    usage:\n        collector = WarningCollector()\n        root = logging.getLogger()\n        root.addHandler(collector)\n        try:\n            ... processing ...\n        finally:\n            root.removeHandler(collector)\n\n        if collector.records:\n            show_message_box(collector.records)\n    """

    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.records: List[str] = []

    def emit(self, record):
        if record.levelno >= logging.WARNING:
            try:
                msg = record.getMessage()
            except Exception:
                msg = str(record.msg)
            self.records.append(msg)


# ============================================================
# CodeGenerationDialog
# ============================================================
class CodeGenerationDialog(QDialog):
    """C code generation dialog (multi-layer support)"""

    def __init__(self, state_machine=None,
                 global_defs=None,
                 parent=None,
                 settings_file=None,
                 role_function_library=None):
        super().__init__(parent)
        self.state_machine = state_machine
        self.global_defs = global_defs
        self.generated_files: Dict[str, str] = {}
        self.config_manager = ConfigManager()
        self.settings_file = (
            settings_file or DEFAULT_SETTINGS_FILE
        )
        self.role_function_library = role_function_library
        # Multi-layer list (set from outside)
        self.all_layers = None

        self._load_saved_settings()

        self.setWindowTitle("CCode generation")
        self.setMinimumSize(800, 600)

        self._setup_ui()
        self._load_sample_data_if_needed()
        self._load_config_to_ui()

    #---- Setting read/write ----
    def _load_saved_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r',
                          encoding='utf-8') as f:
                    data = json.load(f)
                if 'output_directory' in data:
                    self.config_manager.update(
                        output_directory=data['output_directory'])
                if 'generation_style' in data:
                    self.config_manager.update(
                        generation_style=data['generation_style'])
                if 'os_type' in data:
                    self.config_manager.update(
                        os_type=data['os_type'])
                if 'save_with_merge' in data:
                    self.config_manager.update(
                        save_with_merge=data['save_with_merge'])
                logger.info(
                    f"前回の設定を読み込みました: {data}")
        except Exception as e:
            logger.warning(f"設定読み込みに失敗: {e}")

    def _save_settings(self):
        """Save current settings"""
        try:
            config = self.config_manager.get_config()
            data = {
                'output_directory': config.output_directory,
                'generation_style': config.generation_style,
                'os_type': config.os_type,
                'save_with_merge': config.save_with_merge,
            }
            settings_dir = os.path.dirname(
                self.settings_file)
            if settings_dir and not os.path.exists(
                settings_dir):
                os.makedirs(settings_dir, exist_ok=True)
            with open(self.settings_file, 'w',
                      encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False,
                          indent=2)
            logger.info(f"設定を保存しました: {data}")
        except Exception as e:
            logger.warning(f"設定保存に失敗: {e}")

    # ---- UI ----
    def _setup_ui(self):
        """Build UI"""
        main_layout = QVBoxLayout(self)
        
        # Settings info group
        info_group = QGroupBox("Generation settingsInfo")
        info_layout = QFormLayout(info_group)
        
        # Output destination
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText(
            "Select output directory")
        self.output_dir_edit.textChanged.connect(
            self._on_output_dir_changed)
        self.output_dir_btn = QPushButton("Browse...")
        self.output_dir_btn.clicked.connect(
            self._select_output_dir)

        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_edit)
        output_dir_layout.addWidget(self.output_dir_btn)
        info_layout.addRow("Output directory:", output_dir_layout)
        
        # Generation style
        self.style_combo = QComboBox()
        self.style_combo.addItem(
            "Table-driven style", "table_driven")
        self.style_combo.addItem(
            "switch-case style", "switch_case")
        self.style_combo.currentIndexChanged.connect(
            self._on_style_changed)
        info_layout.addRow("Generation style:", self.style_combo)
        
        # OS type label
        self.os_label = QLabel("NonRTOS")
        info_layout.addRow("OS type:", self.os_label)
        
        # Merge settings label
        self.merge_label = QLabel("Enabled")
        info_layout.addRow("Merge:", self.merge_label)
        
        # Advanced settings button
        self.settings_btn = QPushButton("Advanced settings...")
        self.settings_btn.clicked.connect(
            self._open_settings_dialog)
        info_layout.addRow("", self.settings_btn)
        
        main_layout.addWidget(info_group)
        
        # Action buttons
        button_layout = QHBoxLayout()

        self.generate_btn = QPushButton("Code generation")
        self.generate_btn.clicked.connect(
            self._generate_code)
        button_layout.addWidget(self.generate_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._save_code)
        button_layout.addWidget(self.save_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self._on_close)
        button_layout.addWidget(self.close_btn)

        main_layout.addLayout(button_layout)
        
        # Preview area
        preview_label = QLabel("Generated code preview:")
        main_layout.addWidget(preview_label)

        self.preview_tabs = QComboBox()
        self.preview_tabs.currentIndexChanged.connect(
            self._update_preview)
        main_layout.addWidget(self.preview_tabs)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Consolas", 10))
        main_layout.addWidget(self.preview_text)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

    #---- Data load ----
    def _load_sample_data_if_needed(self):
        """Load when sample data not set"""
        if self.state_machine is None or \
           self.global_defs is None:
            sample_gen = SampleDataGenerator()
            self.state_machine, self.global_defs = \
                sample_gen.get_sample_data()
            logger.info("Sample data loaded")

    def _load_config_to_ui(self):
        """Reflect settings to UI"""
        config = self.config_manager.get_config()
        
        if config.output_directory:
            self.output_dir_edit.setText(
                config.output_directory)
        idx = self.style_combo.findData(
            config.generation_style)
        if idx >= 0:
            self.style_combo.setCurrentIndex(idx)
        self._update_info_labels(config)

    def _update_info_labels(self, config):
        """Update the settings info label"""
        os_names = {
            'non_rtos': 'NonRTOS (bare metal)',
            'freertos': 'FreeRTOS',
            'threadx': 'ThreadX',
        }
        self.os_label.setText(
            os_names.get(config.os_type, config.os_type))
        self.merge_label.setText(
            "Enabled" if config.save_with_merge else "Disabled")

    #---- Event handler ----
    def _on_output_dir_changed(self, text):
        """Handler when output dir changes"""
        self.config_manager.update(
            output_directory=text if text else "")

    def _select_output_dir(self):
        """Select output directory"""
        current = self.output_dir_edit.text() or os.getcwd()
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select output directory", current)
        if dir_path:
            self.output_dir_edit.setText(dir_path)
            self.config_manager.update(
                output_directory=dir_path)
            self._save_settings()

    def _on_style_changed(self, index):
        """Handler when style changes"""
        style = self.style_combo.currentData()
        self.config_manager.update(
            generation_style=style)
        self._save_settings()

    def _open_settings_dialog(self):
        """Open advanced settings dialog"""
        dialog = CodeGenerationSettingsDialog(
            config_manager=self.config_manager,
            parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            self.config_manager.set_config(config)
            self._load_config_to_ui()
            self._save_settings()

    # ---- Warning display ----
    def _show_warnings(self, records):
        if not records:
            return
        # Deduplication (order-preserving)
        seen = set()
        unique = []
        for r in records:
            if r not in seen:
                seen.add(r)
                unique.append(r)
        QMessageBox.warning(
            self,
            "Warnings during generation",
            "The following warnings occurred:\n\n"
            + "\n".join(f"・{m}" for m in unique),
        )

    # ---- ★ Code generation ----
    def _generate_code(self):
        """Execute code generation"""
        if self.state_machine is None or \
           self.global_defs is None:
            QMessageBox.warning(
                self, "Warning",
                "State machine and global definitions"
                "is not set.")
            return

        output_dir = self.output_dir_edit.text().strip()
        if output_dir:
            self.config_manager.update(
                output_directory=output_dir)

        if not output_dir:
            QMessageBox.warning(
                self, "Warning",
                "Please set the output directory.")
            self._select_output_dir()
            output_dir = self.output_dir_edit.text().strip()
            if not output_dir:
                return

        config = self.config_manager.get_config()

        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        # Attach warning collection handler
        collector = WarningCollector()
        root_logger = logging.getLogger()
        root_logger.addHandler(collector)
        try:
            generator = CCodeGenerator(config=config)
            # Automatic multi-layer / single detection
            if self.all_layers and len(self.all_layers) > 0:
                logger.info(
                    f"Multi-layer generation: "
                    f"{len(self.all_layers)} layers"
                )
                self.generated_files = (
                    generator.generate_all_layers(
                        self.all_layers,
                        self.global_defs,
                        role_function_library=(
                            self.role_function_library),
                    )
                )
            else:
                logger.info("Single-layer generation")
                self.generated_files = generator.generate_all(
                    self.state_machine,
                    self.global_defs,
                    role_function_library=(
                        self.role_function_library),
                )
        except Exception as e:
            self.generate_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
            QMessageBox.critical(
                self, "Error",
                f"コード生成に失敗しました:\n{e}")
            return
        finally:
            root_logger.removeHandler(collector)

        # Preview apply
        self.preview_tabs.clear()
        for filename in self.generated_files.keys():
            self.preview_tabs.addItem(filename)
        self._update_preview()

        self.generate_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._save_settings()

        # CompletionMessage
        QMessageBox.information(
            self, "Completion",
            f"{len(self.generated_files)}ファイルを"
            f"生成しました。\n出力先: {output_dir}")

        # Show warnings last if any
        self._show_warnings(collector.records)

    def _update_preview(self):
        """Update preview"""
        filename = self.preview_tabs.currentText()
        if filename in self.generated_files:
            self.preview_text.setPlainText(
                self.generated_files[filename])
        else:
            self.preview_text.clear()

    def _save_code(self):
        """Save generated code"""
        if not self.generated_files:
            QMessageBox.warning(
                self, "Warning",
                "No code was generated.")
            return
        
        output_dir = self.output_dir_edit.text().strip()
        if not output_dir:
            QMessageBox.warning(
                self, "Warning",
                "Please set the output directory.")
            return

        try:
            os.makedirs(output_dir, exist_ok=True)
            config = self.config_manager.get_config()
            generator = CCodeGenerator(config=config)
            if config.save_with_merge:
                saved_files = \
                    generator.save_generated_code_with_merge(
                        self.generated_files, output_dir)
            else:
                saved_files = \
                    generator.save_generated_code(
                        self.generated_files, output_dir)
            self._save_settings()
            QMessageBox.information(
                self, "Save complete",
                f"{len(saved_files)}ファイルを"
                f"保存しました。\n\n"
                f"出力先: {output_dir}")
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"保存に失敗しました:\n{e}")

    def _on_close(self):
        """Handler on close"""
        self._save_settings()
        self.reject()

    # ---- getter ----
    def get_generated_files(self) -> Dict[str, str]:
        """Get generated files"""
        return self.generated_files

    def get_config(self):
        """Get current settings"""
        return self.config_manager.get_config()