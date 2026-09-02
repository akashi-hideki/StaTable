# statable_gui/validation_dialog.py
"""
検証・AI連携ダイアログ
PySide6対応
"""

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
    """検証・AI連携ダイアログ"""
    
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
        
        self.setWindowTitle("コード生成前検証・AI診断")
        self.setMinimumSize(900, 700)
        
        self._setup_ui()
        self._run_validation()
    
    def _setup_ui(self):
        """UIを構築"""
        main_layout = QVBoxLayout(self)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # ===== 検証結果タブ =====
        self.validation_tab = QWidget()
        self._setup_validation_tab()
        self.tab_widget.addTab(self.validation_tab, "① 検証結果")
        
        # ===== AIプロンプトタブ =====
        self.prompt_tab = QWidget()
        self._setup_prompt_tab()
        self.tab_widget.addTab(self.prompt_tab, "② AIプロンプト")
        
        # ===== AI回答タブ =====
        self.response_tab = QWidget()
        self._setup_response_tab()
        self.tab_widget.addTab(self.response_tab, "③ AI回答取り込み")
        
        # ===== 変更一覧タブ =====
        self.changes_tab = QWidget()
        self._setup_changes_tab()
        self.tab_widget.addTab(self.changes_tab, "④ 変更一覧・反映")
        
        # 閉じるボタン
        button_layout = QHBoxLayout()
        close_btn = QPushButton("閉じる")
        close_btn.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        main_layout.addLayout(button_layout)
    
    def _setup_validation_tab(self):
        """検証結果タブのセットアップ"""
        layout = QVBoxLayout(self.validation_tab)
        
        # サマリーラベル
        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.summary_label)
        
        # 問題リスト
        self.issue_tree = QTreeWidget()
        self.issue_tree.setHeaderLabels(["重大度", "カテゴリ", "メッセージ", "対象", "修正提案"])
        self.issue_tree.setColumnWidth(0, 80)
        self.issue_tree.setColumnWidth(1, 100)
        self.issue_tree.setColumnWidth(2, 300)
        self.issue_tree.setColumnWidth(3, 100)
        self.issue_tree.setColumnWidth(4, 300)
        layout.addWidget(self.issue_tree)
        
        # 再検証ボタン
        revalidate_btn = QPushButton("再検証")
        revalidate_btn.clicked.connect(self._run_validation)
        layout.addWidget(revalidate_btn)
    
    def _setup_prompt_tab(self):
        """AIプロンプトタブのセットアップ"""
        layout = QVBoxLayout(self.prompt_tab)
        
        # 説明ラベル
        info_label = QLabel(
            "以下の手順でAI診断を行います：\n"
            "1. 「コピー」ボタンでプロンプトをクリップボードにコピー\n"
            "2. ChatGPT等に貼り付けて質問\n"
            "3. AIの回答をコピー\n"
            "4. 「AI回答取り込み」タブで回答を貼り付け"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # コピーボタン
        copy_btn = QPushButton("プロンプトをコピー")
        copy_btn.clicked.connect(self._copy_prompt)
        layout.addWidget(copy_btn)
        
        # プロンプトプレビュー
        self.prompt_preview = QTextEdit()
        self.prompt_preview.setReadOnly(True)
        layout.addWidget(self.prompt_preview)
    
    def _setup_response_tab(self):
        """AI回答タブのセットアップ"""
        layout = QVBoxLayout(self.response_tab)
        
        # 貼り付けボタン
        paste_btn = QPushButton("クリップボードから貼り付け")
        paste_btn.clicked.connect(self._paste_response)
        layout.addWidget(paste_btn)
        
        # 回答入力
        self.response_edit = QTextEdit()
        self.response_edit.setPlaceholderText("AIの回答をここに貼り付けてください")
        layout.addWidget(self.response_edit)
        
        # 解析ボタン
        parse_btn = QPushButton("回答を解析して変更一覧を生成")
        parse_btn.clicked.connect(self._parse_response)
        layout.addWidget(parse_btn)
    
    def _setup_changes_tab(self):
        """変更一覧タブのセットアップ"""
        layout = QVBoxLayout(self.changes_tab)
        
        # 変更一覧
        self.change_tree = QTreeWidget()
        self.change_tree.setHeaderLabels(["選択", "アクション", "パラメータ", "理由"])
        self.change_tree.setColumnWidth(0, 50)
        self.change_tree.setColumnWidth(1, 150)
        self.change_tree.setColumnWidth(2, 400)
        self.change_tree.setColumnWidth(3, 250)
        layout.addWidget(self.change_tree)
        
        # 反映ボタン
        apply_btn = QPushButton("選択した変更を反映")
        apply_btn.clicked.connect(self._apply_changes)
        layout.addWidget(apply_btn)
    
    def _run_validation(self):
        """検証を実行"""
        logger.debug("_run_validation started")
        self.validation_result = self.validator.validate(self.sm, self.gd)
        
        # サマリー更新
        summary = (f"エラー: {self.validation_result.error_count} | "
                  f"警告: {self.validation_result.warning_count} | "
                  f"情報: {self.validation_result.info_count}")
        self.summary_label.setText(summary)
        
        # 問題リスト更新
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
            # 重大度に応じた色付け
            color = severity_colors.get(issue.severity.value, Qt.black)
            item.setForeground(0, color)
            self.issue_tree.addTopLevelItem(item)
        
        # プロンプト生成
        prompt = self.prompt_generator.generate_diagnosis_prompt(
            self.sm, self.gd, self.validation_result
        )
        self.prompt_preview.setPlainText(prompt)
        
        logger.debug(f"_run_validation completed: {summary}")
    
    def _copy_prompt(self):
        """プロンプトをクリップボードにコピー"""
        prompt = self.prompt_generator.generate_diagnosis_prompt(
            self.sm, self.gd, self.validation_result
        )
        if self.clipboard.copy_to_clipboard(prompt):
            QMessageBox.information(self, "コピー完了",
                "プロンプトをクリップボードにコピーしました。\n"
                "ChatGPT等に貼り付けて質問してください。")
        else:
            QMessageBox.warning(self, "エラー", "クリップボードへのコピーに失敗しました。")
    
    def _paste_response(self):
        """クリップボードからAI回答を貼り付け"""
        text = self.clipboard.get_from_clipboard()
        if text:
            self.response_edit.setPlainText(text)
        else:
            QMessageBox.warning(self, "警告", "クリップボードが空です。")
    
    def _parse_response(self):
        """AI回答を解析"""
        text = self.response_edit.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "警告", "AI回答が入力されていません。")
            return
        
        self.parsed_changes = self.response_parser.parse(text)
        
        # 変更一覧を表示
        self.change_tree.clear()
        for change in self.parsed_changes:
            item = QTreeWidgetItem()
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Checked)
            item.setText(1, change.action.value)
            item.setText(2, json.dumps(change.params, ensure_ascii=False))
            item.setText(3, change.reason)
            self.change_tree.addTopLevelItem(item)
        
        # タブを変更一覧に切り替え
        self.tab_widget.setCurrentIndex(3)
        
        QMessageBox.information(self, "解析完了",
            f"{len(self.parsed_changes)}件の変更を抽出しました。")
    
    def _apply_changes(self):
        """選択した変更を反映"""
        selected_changes = []
        for i in range(self.change_tree.topLevelItemCount()):
            item = self.change_tree.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                selected_changes.append(self.parsed_changes[i])
        
        if not selected_changes:
            QMessageBox.warning(self, "警告", "反映する変更が選択されていません。")
            return
        
        applier = ChangeApplier(self.sm, self.gd)
        result = applier.apply_all(selected_changes)
        
        QMessageBox.information(self, "反映完了",
            f"{result['applied']}件の変更を反映しました。\n"
            f"失敗: {result['failed']}件")
        
        # 再検証
        self._run_validation()


def show_validation_dialog(sm, gd, parent=None):
    """検証ダイアログを表示するヘルパー関数"""
    dialog = ValidationDialog(sm, gd, parent)
    dialog.exec()