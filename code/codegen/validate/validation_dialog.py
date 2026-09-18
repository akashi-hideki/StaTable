# statable_gui/validation_dialog.py
"""\nValidation / AI integration dialog\nPySide6 compatible\n"""

import sys
import os
import json
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'codegen'))

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QTabWidget, QWidget, QGroupBox,
    QFormLayout, QComboBox, QSplitter
)
from PySide6.QtCore import Qt

from validate.validator import CodeGenerationValidator
from validate.prompt_generator import AIPromptGenerator
from validate.response_parser import AIResponseParser
from validate.change_applier import ChangeApplier
from validate.clipboard_manager import ClipboardManager
from validate.models import ValidationResult

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("validation_dialog")


class ValidationDialog(QDialog):
    """Validation / AI integration dialog"""
    
    def __init__(self, sm, gd, parent=None):
        super().__init__(parent)
        self.sm = sm
        self.gd = gd
        self.validator = CodeGenerationValidator()
        self.prompt_generator = AIPromptGenerator()
        self.response_parser = AIResponseParser()
        self.clipboard = ClipboardManager()
        self.validation_result = None
        self.parsed_changes = []
        
        self.setWindowTitle("Pre-generation validation / AI diagnosis")
        self.setMinimumSize(900, 700)
        
        self._setup_ui()
        self._run_validation()
    
    def _setup_ui(self):
        """Build UI"""
        main_layout = QVBoxLayout(self)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # ===== Validation result tab =====
        self.validation_tab = QWidget()
        self._setup_validation_tab()
        self.tab_widget.addTab(self.validation_tab, "1) Validation result")
        
        # ===== AI prompt tab =====
        self.prompt_tab = QWidget()
        self._setup_prompt_tab()
        self.tab_widget.addTab(self.prompt_tab, "2) AI prompt")
        
        # ===== AI answer tab =====
        self.response_tab = QWidget()
        self._setup_response_tab()
        self.tab_widget.addTab(self.response_tab, "3) AI answer intake")
        
        # ===== Change list tab =====
        self.changes_tab = QWidget()
        self._setup_changes_tab()
        self.tab_widget.addTab(self.changes_tab, "4) Change list / apply")
        
        # Close button
        button_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        main_layout.addLayout(button_layout)
    
    def _setup_validation_tab(self):
        """Set up the validation result tab"""
        layout = QVBoxLayout(self.validation_tab)
        
        # Summary label
        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.summary_label)
        
        # Problem list
        self.issue_tree = QTreeWidget()
        self.issue_tree.setHeaderLabels(["Severity", "Category", "Message", "Target", "Suggested fix"])
        self.issue_tree.setColumnWidth(0, 80)
        self.issue_tree.setColumnWidth(1, 100)
        self.issue_tree.setColumnWidth(2, 300)
        self.issue_tree.setColumnWidth(3, 100)
        self.issue_tree.setColumnWidth(4, 300)
        layout.addWidget(self.issue_tree)
        
        # Re-validate button
        revalidate_btn = QPushButton("Re-validate")
        revalidate_btn.clicked.connect(self._run_validation)
        layout.addWidget(revalidate_btn)
    
    def _setup_prompt_tab(self):
        """Set up the AI prompt tab"""
        layout = QVBoxLayout(self.prompt_tab)
        
        # Description label
        info_label = QLabel(
            "Perform AI diagnosis with the following steps:\n"
            "1. Click \"Copy\" button to copy the prompt to the clipboard\n"
            "2. Paste into ChatGPT or similar and ask\n"
            "3. Copy the AI answer\n"
            "4. Paste the answer in the \"AI answer intake\" tab"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Copy button
        copy_btn = QPushButton("Copy prompt")
        copy_btn.clicked.connect(self._copy_prompt)
        layout.addWidget(copy_btn)
        
        # Prompt preview
        self.prompt_preview = QTextEdit()
        self.prompt_preview.setReadOnly(True)
        layout.addWidget(self.prompt_preview)
    
    def _setup_response_tab(self):
        """Set up the AI answer tab"""
        layout = QVBoxLayout(self.response_tab)
        
        # Paste button
        paste_btn = QPushButton("Paste from clipboard")
        paste_btn.clicked.connect(self._paste_response)
        layout.addWidget(paste_btn)
        
        # Answer input
        self.response_edit = QTextEdit()
        self.response_edit.setPlaceholderText("Paste the AI answer here")
        layout.addWidget(self.response_edit)
        
        # Parse button
        parse_btn = QPushButton("Parse the answer and generate a change list")
        parse_btn.clicked.connect(self._parse_response)
        layout.addWidget(parse_btn)
    
    def _setup_changes_tab(self):
        """Set up the change list tab"""
        layout = QVBoxLayout(self.changes_tab)
        
        # Change list
        self.change_tree = QTreeWidget()
        self.change_tree.setHeaderLabels(["Selection", "Action", "Parameter", "Reason"])
        self.change_tree.setColumnWidth(0, 50)
        self.change_tree.setColumnWidth(1, 150)
        self.change_tree.setColumnWidth(2, 400)
        self.change_tree.setColumnWidth(3, 250)
        layout.addWidget(self.change_tree)
        
        # Apply button
        apply_btn = QPushButton("Apply selected changes")
        apply_btn.clicked.connect(self._apply_changes)
        layout.addWidget(apply_btn)
    
    def _run_validation(self):
        """Run validation"""
        logger.debug("_run_validation started")
        self.validation_result = self.validator.validate(self.sm, self.gd)
        
        # Summary update
        summary = (f"エラー: {self.validation_result.error_count} | "
                  f"警告: {self.validation_result.warning_count} | "
                  f"情報: {self.validation_result.info_count}")
        self.summary_label.setText(summary)
        
        # Problem list update
        self.issue_tree.clear()
        severity_colors = {
            'error': Qt.red,
            'warning': Qt.yellow,
            'info': Qt.blue,
        }
        
        for issue in self.validation_result.issues:
            item = QTreeWidgetItem([
                issue.severity.value.upper(),
                issue.category,
                issue.message,
                issue.target,
                issue.suggestion,
            ])
            # Severity-based coloring
            color = severity_colors.get(issue.severity.value, Qt.black)
            item.setForeground(0, color)
            self.issue_tree.addTopLevelItem(item)
        
        # Prompt generation
        prompt = self.prompt_generator.generate_diagnosis_prompt(
            self.sm, self.gd, self.validation_result
        )
        self.prompt_preview.setPlainText(prompt)
        
        logger.debug(f"_run_validation completed: {summary}")
    
    def _copy_prompt(self):
        """Copy prompt to clipboard"""
        prompt = self.prompt_generator.generate_diagnosis_prompt(
            self.sm, self.gd, self.validation_result
        )
        if self.clipboard.copy_to_clipboard(prompt):
            QMessageBox.information(self, "Copy complete",
                "Prompt copied to clipboard.\n"
                "Please paste into ChatGPT or similar and ask.")
        else:
            QMessageBox.warning(self, "Error", "Failed to copy to clipboard.")
    
    def _paste_response(self):
        """Paste AI answer from clipboard"""
        text = self.clipboard.get_from_clipboard()
        if text:
            self.response_edit.setPlainText(text)
        else:
            QMessageBox.warning(self, "Warning", "Clipboard is empty.")
    
    def _parse_response(self):
        """Parse AI answer"""
        text = self.response_edit.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Warning", "AI answer is empty.")
            return
        
        self.parsed_changes = self.response_parser.parse(text)
        
        # Show change list
        self.change_tree.clear()
        for change in self.parsed_changes:
            item = QTreeWidgetItem()
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Checked)
            item.setText(1, change.action.value)
            item.setText(2, json.dumps(change.params, ensure_ascii=False))
            item.setText(3, change.reason)
            self.change_tree.addTopLevelItem(item)
        
        # Switch the tab to the change list
        self.tab_widget.setCurrentIndex(3)
        
        QMessageBox.information(self, "Parse complete",
            f"{len(self.parsed_changes)}件の変更を抽出しました。")
    
    def _apply_changes(self):
        """Apply selected changes"""
        selected_changes = []
        for i in range(self.change_tree.topLevelItemCount()):
            item = self.change_tree.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                selected_changes.append(self.parsed_changes[i])
        
        if not selected_changes:
            QMessageBox.warning(self, "Warning", "No changes selected for applying.")
            return
        
        applier = ChangeApplier(self.sm, self.gd)
        result = applier.apply_all(selected_changes)
        
        QMessageBox.information(self, "Apply complete",
            f"{result['applied']}件の変更を反映しました。\n"
            f"失敗: {result['failed']}件")
        
        # Re-validate
        self._run_validation()


def show_validation_dialog(sm, gd, parent=None):
    """Helper function to show the validation dialog"""
    dialog = ValidationDialog(sm, gd, parent)
    dialog.exec()