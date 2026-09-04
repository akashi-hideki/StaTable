# statable_gui/transition_editor/dialog.py
"""
遷移編集メインダイアログ
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTabWidget, QWidget, QMessageBox
)
from PySide6.QtCore import Qt

from .draft import TransitionDraft
from .wizard_widget import TransitionWizardWidget
from .edit_widget import TransitionEditWidget


class TransitionEditorDialog(QDialog):
    """遷移編集ダイアログ"""

    def __init__(self, draft: TransitionDraft, role_functions=None, states=None, parent=None):
        super().__init__(parent)
        self.draft = draft
        self.role_functions = role_functions or []
        self.states = states or []
        self.is_new = draft.is_empty()

        self.setWindowTitle("遷移編集")
        self.setMinimumSize(700, 600)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # モード切替タブ
        self.mode_tabs = QTabWidget()
        main_layout.addWidget(self.mode_tabs)

        # ウィザードモード
        self.wizard_widget = TransitionWizardWidget(
            self.draft, self.role_functions, self.states
        )
        self.wizard_widget.draft_updated.connect(self._on_draft_updated)
        self.mode_tabs.addTab(self.wizard_widget, "ウィザード")

        # 編集モード
        self.edit_widget = TransitionEditWidget(
            self.draft, self.role_functions, self.states
        )
        self.edit_widget.draft_updated.connect(self._on_draft_updated)
        self.edit_widget.clear_requested.connect(self._on_clear_requested)
        self.mode_tabs.addTab(self.edit_widget, "編集")

        # 初期モード選択
        if self.is_new:
            self.mode_tabs.setCurrentIndex(0)  # ウィザード
        else:
            self.mode_tabs.setCurrentIndex(1)  # 編集

        # ボタン
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        main_layout.addLayout(btn_layout)

    def _on_draft_updated(self):
        pass

    def _on_clear_requested(self):
        """編集モードのクリアボタン"""
        ret = QMessageBox.question(
            self,
            "確認",
            "現在の設定をクリアして、ウィザードで再設定しますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if ret == QMessageBox.Yes:
            self.draft.clear()
            self.mode_tabs.setCurrentIndex(0)  # ウィザードへ
            self.wizard_widget.reset_to_step(0)