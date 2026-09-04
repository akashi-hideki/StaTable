# statable_gui/transition_editor/wizard_widget.py
"""
遷移ウィザードモードウィジェット（ドラッグアンドドロップ対応）
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QCheckBox, QComboBox, QLineEdit,
    QListWidget, QListWidgetItem, QGroupBox,
    QStackedWidget, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal

from .draft import TransitionDraft, ConditionEntry, ActionEntry


class TransitionWizardWidget(QWidget):
    """遷移ウィザードモード"""

    draft_updated = Signal()

    def __init__(self, draft: TransitionDraft, role_functions=None, states=None, parent=None):
        super().__init__(parent)
        self.draft = draft
        self.role_functions = role_functions or []
        self.states = states or []
        self.current_step = 0

        self._setup_ui()
        self._load_draft()
        self._update_step_buttons()
        self._update_nav_buttons()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # ステップインジケーター
        step_layout = QHBoxLayout()
        self.step_buttons = []
        step_names = ["① 前処理", "② 条件", "③ 実行", "④ 後処理"]
        for i, name in enumerate(step_names):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=i: self._go_to_step(idx))
            self.step_buttons.append(btn)
            step_layout.addWidget(btn)
        main_layout.addLayout(step_layout)

        # ステップコンテンツ
        self.step_content = QStackedWidget()
        main_layout.addWidget(self.step_content)

        self.step_content.addWidget(self._create_pre_step())
        self.step_content.addWidget(self._create_condition_step())
        self.step_content.addWidget(self._create_action_step())
        self.step_content.addWidget(self._create_post_step())

        # ナビゲーション
        nav_layout = QHBoxLayout()
        self.back_btn = QPushButton("← 戻る")
        self.back_btn.clicked.connect(self._go_back)
        nav_layout.addWidget(self.back_btn)

        self.skip_btn = QPushButton("スキップ")
        self.skip_btn.clicked.connect(self._skip_step)
        nav_layout.addWidget(self.skip_btn)

        self.next_btn = QPushButton("次へ →")
        self.next_btn.clicked.connect(self._go_next)
        nav_layout.addWidget(self.next_btn)

        main_layout.addLayout(nav_layout)

    # ---- 前処理ステップ ----
    def _create_pre_step(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("前処理")
        gl = QVBoxLayout(group)

        self.pre_check = QCheckBox("前処理を使用する")
        self.pre_check.toggled.connect(self._on_pre_check_toggled)
        gl.addWidget(self.pre_check)

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("アクション:"))
        self.pre_action_combo = QComboBox()
        self.pre_action_combo.setEditable(True)
        self.pre_action_combo.addItems(self.role_functions)
        self.pre_action_combo.currentTextChanged.connect(self._on_draft_changed)
        h1.addWidget(self.pre_action_combo)
        gl.addLayout(h1)

        h2 = QHBoxLayout()
        h2.addWidget(QLabel("結果変数:"))
        self.pre_result_edit = QLineEdit()
        self.pre_result_edit.textChanged.connect(self._on_draft_changed)
        h2.addWidget(self.pre_result_edit)
        gl.addLayout(h2)

        layout.addWidget(group)
        layout.addStretch()
        return widget

    # ---- 条件ステップ（D&D対応） ----
    def _create_condition_step(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("条件（ドラッグで優先順位変更）")
        gl = QVBoxLayout(group)

        # 条件リスト（D&Dで並べ替え可能）
        self.condition_list = QListWidget()
        self.condition_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.condition_list.setDefaultDropAction(Qt.MoveAction)
        self.condition_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.condition_list.model().rowsMoved.connect(self._update_conditions_from_list)
        gl.addWidget(self.condition_list)

        # パレット（ドラッグ元）
        palette_label = QLabel("▼ パレット（ドラッグして条件を追加）")
        gl.addWidget(palette_label)

        self.condition_palette = QListWidget()
        self.condition_palette.setDragEnabled(True)
        self.condition_palette.setDragDropMode(QAbstractItemView.DragOnly)
        for cond in ["condition == 1", "condition == 0", "result == 0", "result != 0"]:
            self.condition_palette.addItem(cond)
        gl.addWidget(self.condition_palette)

        # デフォルト条件
        self.default_check = QCheckBox("デフォルト条件を使用")
        self.default_check.toggled.connect(self._on_draft_changed)
        gl.addWidget(self.default_check)

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("遷移先:"))
        self.default_target_combo = QComboBox()
        self.default_target_combo.setEditable(True)
        self.default_target_combo.addItems(self.states)
        self.default_target_combo.currentTextChanged.connect(self._on_draft_changed)
        h1.addWidget(self.default_target_combo)
        gl.addLayout(h1)

        layout.addWidget(group)
        layout.addStretch()
        return widget

    # ---- 実行ステップ（D&D対応） ----
    def _create_action_step(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("実行処理（ドラッグで順序変更）")
        gl = QVBoxLayout(group)

        # アクションリスト（D&Dで並べ替え可能）
        self.action_list = QListWidget()
        self.action_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.action_list.setDefaultDropAction(Qt.MoveAction)
        self.action_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.action_list.model().rowsMoved.connect(self._update_actions_from_list)
        gl.addWidget(self.action_list)

        # パレット（ドラッグ元）
        palette_label = QLabel("▼ パレット（ドラッグしてアクションを追加）")
        gl.addWidget(palette_label)

        self.action_palette = QListWidget()
        self.action_palette.setDragEnabled(True)
        self.action_palette.setDragDropMode(QAbstractItemView.DragOnly)
        self.action_palette.addItems(self.role_functions)
        gl.addWidget(self.action_palette)

        # 付帯条件（遷移ガード）
        guard_group = QGroupBox("遷移設定（アクション実行後）")
        ggl = QVBoxLayout(guard_group)

        self.guard_check = QCheckBox("付帯条件を使用する")
        self.guard_check.toggled.connect(self._on_draft_changed)
        ggl.addWidget(self.guard_check)

        hg1 = QHBoxLayout()
        hg1.addWidget(QLabel("条件式:"))
        self.guard_edit = QLineEdit()
        self.guard_edit.textChanged.connect(self._on_draft_changed)
        hg1.addWidget(self.guard_edit)
        ggl.addLayout(hg1)

        hg2 = QHBoxLayout()
        hg2.addWidget(QLabel("成立時遷移先:"))
        self.guard_success_combo = QComboBox()
        self.guard_success_combo.setEditable(True)
        self.guard_success_combo.addItems(self.states)
        self.guard_success_combo.currentTextChanged.connect(self._on_draft_changed)
        hg2.addWidget(self.guard_success_combo)
        ggl.addLayout(hg2)

        self.guard_fail_check = QCheckBox("不成立時の遷移先を指定する")
        self.guard_fail_check.toggled.connect(self._on_draft_changed)
        ggl.addWidget(self.guard_fail_check)

        hg3 = QHBoxLayout()
        hg3.addWidget(QLabel("遷移先:"))
        self.guard_fail_combo = QComboBox()
        self.guard_fail_combo.setEditable(True)
        self.guard_fail_combo.addItems(self.states)
        self.guard_fail_combo.currentTextChanged.connect(self._on_draft_changed)
        hg3.addWidget(self.guard_fail_combo)
        ggl.addLayout(hg3)

        hg4 = QHBoxLayout()
        hg4.addWidget(QLabel("処理:"))
        self.guard_fail_action_combo = QComboBox()
        self.guard_fail_action_combo.setEditable(True)
        self.guard_fail_action_combo.addItems(self.role_functions)
        self.guard_fail_action_combo.currentTextChanged.connect(self._on_draft_changed)
        hg4.addWidget(self.guard_fail_action_combo)
        ggl.addLayout(hg4)

        gl.addWidget(guard_group)
        layout.addWidget(group)
        layout.addStretch()
        return widget

    # ---- 後処理ステップ ----
    def _create_post_step(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("後処理")
        gl = QVBoxLayout(group)

        self.post_check = QCheckBox("後処理を使用する")
        self.post_check.toggled.connect(self._on_draft_changed)
        gl.addWidget(self.post_check)

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("アクション:"))
        self.post_action_combo = QComboBox()
        self.post_action_combo.setEditable(True)
        self.post_action_combo.addItems(self.role_functions)
        self.post_action_combo.currentTextChanged.connect(self._on_draft_changed)
        h1.addWidget(self.post_action_combo)
        gl.addLayout(h1)

        self.fallback_check = QCheckBox("フォールバックを使用する")
        self.fallback_check.toggled.connect(self._on_draft_changed)
        gl.addWidget(self.fallback_check)

        h2 = QHBoxLayout()
        h2.addWidget(QLabel("アクション:"))
        self.fallback_action_combo = QComboBox()
        self.fallback_action_combo.setEditable(True)
        self.fallback_action_combo.addItems(self.role_functions)
        self.fallback_action_combo.currentTextChanged.connect(self._on_draft_changed)
        h2.addWidget(self.fallback_action_combo)
        gl.addLayout(h2)

        layout.addWidget(group)
        layout.addStretch()
        return widget

    # ---- ドラフト読み込み ----
    def _load_draft(self):
        self.pre_check.setChecked(self.draft.use_pre_action)
        self.pre_action_combo.setCurrentText(self.draft.pre_action)
        self.pre_result_edit.setText(self.draft.pre_result_var)

        self.default_check.setChecked(self.draft.use_default_condition)
        self.default_target_combo.setCurrentText(self.draft.default_target)

        self.post_check.setChecked(self.draft.use_post_action)
        self.post_action_combo.setCurrentText(self.draft.post_action)
        self.fallback_check.setChecked(self.draft.use_fallback)
        self.fallback_action_combo.setCurrentText(self.draft.fallback_action)

        # 条件リスト
        self.condition_list.clear()
        for cond in self.draft.conditions:
            item = QListWidgetItem(
                f"[{cond.priority}] {cond.condition} → {cond.target} ({cond.action})"
            )
            item.setData(Qt.UserRole, cond)
            self.condition_list.addItem(item)

        # アクションリスト
        self.action_list.clear()
        for act in self.draft.actions:
            item = QListWidgetItem(f"[{act.order}] {act.action}")
            item.setData(Qt.UserRole, act)
            self.action_list.addItem(item)

        # 付帯条件
        self.guard_check.setChecked(self.draft.use_transition_guard)
        self.guard_edit.setText(self.draft.transition_guard)
        self.guard_success_combo.setCurrentText(self.draft.guard_success_target)
        self.guard_fail_check.setChecked(self.draft.guard_fail_mode == "target")
        self.guard_fail_combo.setCurrentText(self.draft.guard_fail_target)
        self.guard_fail_action_combo.setCurrentText(self.draft.guard_fail_action)

    # ---- ステップ移動 ----
    def _go_to_step(self, index):
        self.current_step = index
        self.step_content.setCurrentIndex(index)
        self._update_step_buttons()
        self._update_nav_buttons()

    def _go_back(self):
        if self.current_step > 0:
            self._go_to_step(self.current_step - 1)

    def _go_next(self):
        if self.current_step < 3:
            self._go_to_step(self.current_step + 1)

    def _skip_step(self):
        self._go_next()

    def _update_step_buttons(self):
        for i, btn in enumerate(self.step_buttons):
            btn.setChecked(i == self.current_step)

    def _update_nav_buttons(self):
        self.back_btn.setEnabled(self.current_step > 0)
        self.next_btn.setEnabled(self.current_step < 3)
        self.next_btn.setText("完了" if self.current_step == 3 else "次へ →")
        self.skip_btn.setVisible(self.current_step < 3)

    # ---- ドラフト更新 ----
    def _on_draft_changed(self, *args):
        self.draft.use_pre_action = self.pre_check.isChecked()
        self.draft.pre_action = self.pre_action_combo.currentText()
        self.draft.pre_result_var = self.pre_result_edit.text()

        self.draft.use_default_condition = self.default_check.isChecked()
        self.draft.default_target = self.default_target_combo.currentText()

        self.draft.use_post_action = self.post_check.isChecked()
        self.draft.post_action = self.post_action_combo.currentText()
        self.draft.use_fallback = self.fallback_check.isChecked()
        self.draft.fallback_action = self.fallback_action_combo.currentText()

        self.draft.use_transition_guard = self.guard_check.isChecked()
        self.draft.transition_guard = self.guard_edit.text()
        self.draft.guard_success_target = self.guard_success_combo.currentText()
        self.draft.guard_fail_mode = "target" if self.guard_fail_check.isChecked() else "stay"
        self.draft.guard_fail_target = self.guard_fail_combo.currentText()
        self.draft.guard_fail_action = self.guard_fail_action_combo.currentText()

        self.draft_updated.emit()

    def _on_pre_check_toggled(self, checked):
        self.pre_action_combo.setEnabled(checked)
        self.pre_result_edit.setEnabled(checked)
        self._on_draft_changed()

    # ---- D&D リスト同期 ----
    def _update_conditions_from_list(self, *args):
        self.draft.conditions = []
        for i in range(self.condition_list.count()):
            item = self.condition_list.item(i)
            entry = item.data(Qt.UserRole)
            if entry:
                entry.priority = i + 1
                entry.target = self._extract_target(item.text())
                entry.action = self._extract_action(item.text())
                entry.condition = self._extract_condition(item.text())
            else:
                entry = ConditionEntry(priority=i + 1, condition=item.text())
            self.draft.conditions.append(entry)
            item.setText(
                f"[{i+1}] {entry.condition} → {entry.target} ({entry.action})"
            )
        self.draft_updated.emit()

    def _update_actions_from_list(self, *args):
        self.draft.actions = []
        for i in range(self.action_list.count()):
            item = self.action_list.item(i)
            entry = item.data(Qt.UserRole)
            if not entry:
                entry = ActionEntry(order=i + 1, action=item.text())
            entry.order = i + 1
            self.draft.actions.append(entry)
            item.setText(f"[{i+1}] {entry.action}")
        self.draft_updated.emit()

    def _extract_target(self, text: str) -> str:
        # "[1] cond → TARGET (action)" から TARGET を抽出
        if "→" in text:
            rest = text.split("→")[1].strip()
            if "(" in rest:
                return rest.split("(")[0].strip()
            return rest.strip()
        return ""

    def _extract_action(self, text: str) -> str:
        if "(" in text and ")" in text:
            return text.split("(")[1].split(")")[0].strip()
        return ""

    def _extract_condition(self, text: str) -> str:
        if "]" in text and "→" in text:
            return text.split("]")[1].split("→")[0].strip()
        return ""

    def reset_to_step(self, step_index):
        self._go_to_step(step_index)