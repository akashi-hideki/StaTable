"""割り込み処理・デバイスリソース・タイマ設定の管理ダイアログ（状態遷移条件対応版）"""

from typing import Optional, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QMouseEvent
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QHeaderView,
    QComboBox, QLineEdit, QDialogButtonBox, QMessageBox,
    QAbstractItemView, QSpinBox, QCheckBox, QFormLayout
)

from statable.global_defs import (
    GlobalDefinitions,
    InterruptHandlerDef,
    InterruptAction,
    DevicePlaceholderDef,
    TimerBaseDef,
    TimerDerivedDef,
)

from .symbol_picker import SymbolPickerWidget
from .condition_edit_dialog import ConditionEditDialog
from .action_edit_dialog import ActionEditDialog
from .logger import StaTableLogger


# ----------------------------------------------------------------------
# 一覧テーブル（ダブルクリックを確実に捕捉）
# ----------------------------------------------------------------------
class DoubleClickTable(QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        pos = event.position().toPoint()
        item = self.itemAt(pos)
        if item:
            row = item.row()
            StaTableLogger.debug(f"DoubleClickTable.mouseDoubleClickEvent: row={row}")
            self.cellDoubleClicked.emit(row, item.column())
        else:
            StaTableLogger.debug("DoubleClickTable.mouseDoubleClickEvent: no item")


# ----------------------------------------------------------------------
# 割り込み処理編集ダイアログ（条件付きアクションテーブル）
# ----------------------------------------------------------------------
class InterruptEditDialog(QDialog):
    def __init__(
        self,
        parent=None,
        event_names=None,
        interrupt: Optional[InterruptHandlerDef] = None,
        global_defs: Optional[GlobalDefinitions] = None,
        role_functions: Optional[dict] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("割り込み処理編集")
        self.setMinimumSize(1100, 800)
        self.event_names = event_names or []
        self.global_defs = global_defs if global_defs else GlobalDefinitions()
        self.role_functions = role_functions if role_functions is not None else {}

        layout = QVBoxLayout(self)

        # タイトル
        title = QLabel("割り込み処理編集")
        title.setFont(QFont("sans-serif", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 基本情報フォーム
        form = QFormLayout()
        layout.addLayout(form)

        self.name_edit = QLineEdit()
        if interrupt:
            self.name_edit.setText(interrupt.name)
        form.addRow("割り込み名", self.name_edit)

        self.desc_edit = QLineEdit()
        if interrupt:
            self.desc_edit.setText(interrupt.description)
        form.addRow("説明", self.desc_edit)

        # イベント名（編集可能コンボ）
        self.event_combo = QComboBox()
        self.event_combo.setEditable(True)
        self.event_combo.addItems(self.event_names)
        if interrupt and interrupt.event_names:
            self.event_combo.setCurrentText(interrupt.event_names[0])
        form.addRow("イベント名", self.event_combo)

        # タイマ割り込みフラグ
        self.timer_check = QCheckBox()
        self.timer_check.setChecked(interrupt.is_timer if interrupt else False)
        form.addRow("タイマ割り込み", self.timer_check)

        layout.addWidget(QLabel("条件付きアクション一覧:"))

        # アクションテーブル（ガード条件＋動作コード）
        self.action_table = DoubleClickTable(0, 2)
        self.action_table.setHorizontalHeaderLabels(["状態遷移条件", "動作コード"])
        self.action_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.action_table.cellDoubleClicked.connect(self.on_action_double_clicked)
        layout.addWidget(self.action_table, stretch=1)

        # 行追加・削除ボタン
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("行追加")
        add_btn.clicked.connect(lambda: self.add_action_row())
        del_btn = QPushButton("行削除")
        del_btn.clicked.connect(lambda: self.delete_action_row())
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # OK/Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # 初期データ読み込み
        if interrupt and interrupt.actions:
            for act in interrupt.actions:
                self.add_action_row(act.condition, act.action)
        else:
            self.add_action_row()

        StaTableLogger.debug("InterruptEditDialog initialized")

    def add_action_row(self, condition: str = "", action: str = ""):
        """アクションテーブルに1行追加"""
        row = self.action_table.rowCount()
        self.action_table.insertRow(row)

        # ガード条件（読み取り専用）
        condition_item = QTableWidgetItem(condition.replace('\n', ' ; ') if condition else "")
        condition_item.setToolTip("ダブルクリックで状態遷移条件を編集")
        condition_item.setData(Qt.UserRole, condition)
        self.action_table.setItem(row, 0, condition_item)

        # 動作コード（読み取り専用）
        action_item = QTableWidgetItem(action.replace('\n', ' ; ') if action else "")
        action_item.setToolTip("ダブルクリックで動作コードを編集")
        action_item.setData(Qt.UserRole, action)
        self.action_table.setItem(row, 1, action_item)

    def delete_action_row(self):
        row = self.action_table.currentRow()
        if row >= 0:
            self.action_table.removeRow(row)

    def on_action_double_clicked(self, row, col):
        """ガード条件または動作コードを編集"""
        StaTableLogger.debug(f"on_action_double_clicked: row={row}, col={col}")

        if col == 0:
            item = self.action_table.item(row, 0)
            if not item:
                return
            current_condition = item.data(Qt.UserRole) if item.data(Qt.UserRole) else ""
            dlg = ConditionEditDialog(
                self,
                condition_text=current_condition,
                global_defs=self.global_defs,
                role_functions=self.role_functions
            )
            if dlg.exec() == QDialog.Accepted:
                new_condition = dlg.get_condition_text()
                item.setText(new_condition.replace('\n', ' ; '))
                item.setData(Qt.UserRole, new_condition)

        elif col == 1:
            item = self.action_table.item(row, 1)
            if not item:
                return
            current_action = item.data(Qt.UserRole) if item.data(Qt.UserRole) else ""
            dlg = ActionEditDialog(
                self,
                action_text=current_action,
                role_functions=self.role_functions,
                global_defs=self.global_defs
            )
            if dlg.exec() == QDialog.Accepted:
                new_action = dlg.get_action_text()
                item.setText(new_action.replace('\n', ' ; '))
                item.setData(Qt.UserRole, new_action)

    def get_interrupt(self) -> InterruptHandlerDef:
        """編集結果を取得"""
        actions = []
        for row in range(self.action_table.rowCount()):
            condition_item = self.action_table.item(row, 0)
            action_item = self.action_table.item(row, 1)
            if not condition_item or not action_item:
                continue
            condition = condition_item.data(Qt.UserRole) if condition_item.data(Qt.UserRole) else ""
            action = action_item.data(Qt.UserRole) if action_item.data(Qt.UserRole) else ""
            if not condition and not action:
                continue
            actions.append(InterruptAction(guard=guard, action=action))

        event_names = []
        if self.event_combo.currentText().strip():
            event_names.append(self.event_combo.currentText().strip())

        return InterruptHandlerDef(
            name=self.name_edit.text().strip(),
            description=self.desc_edit.text().strip(),
            event_names=event_names,
            is_timer=self.timer_check.isChecked(),
            actions=actions,
        )


# ----------------------------------------------------------------------
# デバイスリソース仮定義編集ダイアログ
# ----------------------------------------------------------------------
class DevicePlaceholderEditDialog(QDialog):
    def __init__(self, parent=None, placeholder: Optional[DevicePlaceholderDef] = None):
        super().__init__(parent)
        self.setWindowTitle("デバイスリソース仮定義編集")
        self.setMinimumWidth(400)

        form = QFormLayout(self)
        self.name_edit = QLineEdit()
        if placeholder:
            self.name_edit.setText(placeholder.name)
        form.addRow("仮定義名", self.name_edit)

        self.desc_edit = QLineEdit()
        if placeholder:
            self.desc_edit.setText(placeholder.description)
        form.addRow("説明", self.desc_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def get_placeholder(self) -> DevicePlaceholderDef:
        return DevicePlaceholderDef(
            name=self.name_edit.text().strip(),
            description=self.desc_edit.text().strip(),
        )


# ----------------------------------------------------------------------
# タイマ基準編集ダイアログ
# ----------------------------------------------------------------------
class TimerBaseEditDialog(QDialog):
    def __init__(self, parent=None, timer_base: TimerBaseDef = None):
        super().__init__(parent)
        self.setWindowTitle("タイマ基準変数編集")
        self.setMinimumWidth(400)

        form = QFormLayout(self)
        self.var_edit = QLineEdit()
        if timer_base:
            self.var_edit.setText(timer_base.variable_name)
        form.addRow("基準変数名", self.var_edit)

        self.unit_edit = QLineEdit()
        if timer_base:
            self.unit_edit.setText(timer_base.unit)
        form.addRow("単位", self.unit_edit)

        self.type_edit = QLineEdit()
        if timer_base:
            self.type_edit.setText(timer_base.data_type)
        form.addRow("型", self.type_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def get_values(self) -> tuple:
        return (
            self.var_edit.text().strip(),
            self.unit_edit.text().strip(),
            self.type_edit.text().strip(),
        )


# ----------------------------------------------------------------------
# 派生タイマ編集ダイアログ
# ----------------------------------------------------------------------
class TimerDerivedEditDialog(QDialog):
    def __init__(self, parent=None, derived: Optional[TimerDerivedDef] = None):
        super().__init__(parent)
        self.setWindowTitle("派生タイマ変数編集")
        self.setMinimumWidth(400)

        form = QFormLayout(self)
        self.period_edit = QLineEdit()
        if derived:
            self.period_edit.setText(derived.period_name)
        form.addRow("周期名", self.period_edit)

        self.mult_spin = QSpinBox()
        self.mult_spin.setRange(1, 1000000)
        if derived:
            self.mult_spin.setValue(derived.multiplier)
        form.addRow("倍率", self.mult_spin)

        self.var_edit = QLineEdit()
        if derived:
            self.var_edit.setText(derived.variable_name)
        form.addRow("変数名", self.var_edit)

        self.type_edit = QLineEdit()
        if derived:
            self.type_edit.setText(derived.data_type)
        form.addRow("型", self.type_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def get_derived(self) -> TimerDerivedDef:
        return TimerDerivedDef(
            period_name=self.period_edit.text().strip(),
            multiplier=self.mult_spin.value(),
            variable_name=self.var_edit.text().strip(),
            data_type=self.type_edit.text().strip(),
        )


# ----------------------------------------------------------------------
# メインダイアログ
# ----------------------------------------------------------------------
class InterruptHandlerEditDialog(QDialog):
    """割り込み処理・デバイスリソース・タイマ設定をまとめて管理するダイアログ"""

    def __init__(
        self,
        global_defs: GlobalDefinitions,
        event_names: Optional[List[str]] = None,
        role_functions: Optional[dict] = None,
        parent=None
    ):
        super().__init__(parent)
        self.global_defs = global_defs
        self.event_names = event_names or []
        self.role_functions = role_functions if role_functions is not None else {}

        self.setWindowTitle("割り込み処理・デバイスリソース・タイマ設定")
        self.setMinimumSize(1200, 800)

        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tabs.addTab(self._create_interrupt_tab(), "割り込み処理")
        self.tabs.addTab(self._create_placeholder_tab(), "デバイスリソース")
        self.tabs.addTab(self._create_timer_tab(), "タイマ設定")

        close_btn = QPushButton("閉じる")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

        self.refresh_interrupt_table()
        self.refresh_placeholder_table()
        self.refresh_timer_table()

        StaTableLogger.debug("InterruptHandlerEditDialog initialized")

    # ------------------------------------------------------------------
    # 割り込み処理タブ
    # ------------------------------------------------------------------
    def _create_interrupt_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.interrupt_table = DoubleClickTable(0, 5)
        self.interrupt_table.setHorizontalHeaderLabels([
            "割り込み名", "説明", "イベント名", "タイマ", "条件付きアクション数"
        ])
        self.interrupt_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.interrupt_table.cellDoubleClicked.connect(self.on_interrupt_double_clicked)
        layout.addWidget(self.interrupt_table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("追加")
        add_btn.clicked.connect(self.add_interrupt)
        del_btn = QPushButton("削除")
        del_btn.clicked.connect(self.delete_interrupt)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    def refresh_interrupt_table(self):
        self.interrupt_table.setRowCount(0)
        for intr in self.global_defs.interrupts:
            row = self.interrupt_table.rowCount()
            self.interrupt_table.insertRow(row)
            self.interrupt_table.setItem(row, 0, QTableWidgetItem(intr.name))
            self.interrupt_table.setItem(row, 1, QTableWidgetItem(intr.description))
            self.interrupt_table.setItem(row, 2, QTableWidgetItem(", ".join(intr.event_names)))
            self.interrupt_table.setItem(row, 3, QTableWidgetItem("✔" if intr.is_timer else ""))
            self.interrupt_table.setItem(row, 4, QTableWidgetItem(str(len(intr.actions))))

    def on_interrupt_double_clicked(self, row, col):
        StaTableLogger.debug(f"on_interrupt_double_clicked: row={row}, col={col}")
        if row < 0 or row >= len(self.global_defs.interrupts):
            return
        target = self.global_defs.interrupts[row]
        dlg = InterruptEditDialog(
            self,
            event_names=self.event_names,
            interrupt=target,
            global_defs=self.global_defs,
            role_functions=self.role_functions
        )
        if dlg.exec() == QDialog.Accepted:
            new_intr = dlg.get_interrupt()
            if not new_intr.name:
                QMessageBox.warning(self, "警告", "割り込み名を入力してください。")
                return
            self.global_defs.interrupts[row] = new_intr
            self.refresh_interrupt_table()

    def add_interrupt(self):
        dlg = InterruptEditDialog(
            self,
            event_names=self.event_names,
            global_defs=self.global_defs,
            role_functions=self.role_functions
        )
        if dlg.exec() == QDialog.Accepted:
            intr = dlg.get_interrupt()
            if not intr.name:
                QMessageBox.warning(self, "警告", "割り込み名を入力してください。")
                return
            self.global_defs.interrupts.append(intr)
            self.refresh_interrupt_table()

    def delete_interrupt(self):
        row = self.interrupt_table.currentRow()
        if 0 <= row < len(self.global_defs.interrupts):
            self.global_defs.interrupts.pop(row)
            self.refresh_interrupt_table()

    # ------------------------------------------------------------------
    # デバイスリソースタブ
    # ------------------------------------------------------------------
    def _create_placeholder_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.placeholder_table = DoubleClickTable(0, 2)
        self.placeholder_table.setHorizontalHeaderLabels(["仮定義名", "説明"])
        self.placeholder_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.placeholder_table.cellDoubleClicked.connect(self.on_placeholder_double_clicked)
        layout.addWidget(self.placeholder_table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("追加")
        add_btn.clicked.connect(self.add_placeholder)
        del_btn = QPushButton("削除")
        del_btn.clicked.connect(self.delete_placeholder)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    def refresh_placeholder_table(self):
        self.placeholder_table.setRowCount(0)
        for ph in self.global_defs.placeholders:
            row = self.placeholder_table.rowCount()
            self.placeholder_table.insertRow(row)
            self.placeholder_table.setItem(row, 0, QTableWidgetItem(ph.name))
            self.placeholder_table.setItem(row, 1, QTableWidgetItem(ph.description))

    def on_placeholder_double_clicked(self, row, col):
        StaTableLogger.debug(f"on_placeholder_double_clicked: row={row}, col={col}")
        if row < 0 or row >= len(self.global_defs.placeholders):
            return
        target = self.global_defs.placeholders[row]
        dlg = DevicePlaceholderEditDialog(self, placeholder=target)
        if dlg.exec() == QDialog.Accepted:
            new_ph = dlg.get_placeholder()
            if not new_ph.name:
                QMessageBox.warning(self, "警告", "仮定義名を入力してください。")
                return
            self.global_defs.placeholders[row] = new_ph
            self.refresh_placeholder_table()

    def add_placeholder(self):
        dlg = DevicePlaceholderEditDialog(self)
        if dlg.exec() == QDialog.Accepted:
            ph = dlg.get_placeholder()
            if not ph.name:
                QMessageBox.warning(self, "警告", "仮定義名を入力してください。")
                return
            self.global_defs.placeholders.append(ph)
            self.refresh_placeholder_table()

    def delete_placeholder(self):
        row = self.placeholder_table.currentRow()
        if 0 <= row < len(self.global_defs.placeholders):
            self.global_defs.placeholders.pop(row)
            self.refresh_placeholder_table()

    # ------------------------------------------------------------------
    # タイマ設定タブ
    # ------------------------------------------------------------------
    def _create_timer_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 基準変数表示（ダブルクリックで編集）
        self.base_display = DoubleClickTable(1, 3)
        self.base_display.setHorizontalHeaderLabels(["基準変数名", "単位", "型"])
        self.base_display.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.base_display.setRowCount(1)
        self.base_display.cellDoubleClicked.connect(self.on_base_double_clicked)
        layout.addWidget(self.base_display)

        layout.addWidget(QLabel("派生タイマ変数:"))
        self.derived_table = DoubleClickTable(0, 4)
        self.derived_table.setHorizontalHeaderLabels(["周期名", "倍率", "変数名", "型"])
        self.derived_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.derived_table.cellDoubleClicked.connect(self.on_derived_double_clicked)
        layout.addWidget(self.derived_table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("追加")
        add_btn.clicked.connect(self.add_derived)
        del_btn = QPushButton("削除")
        del_btn.clicked.connect(self.delete_derived)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    def refresh_timer_table(self):
        # 基準変数
        self.base_display.setItem(0, 0, QTableWidgetItem(self.global_defs.timer_base.variable_name))
        self.base_display.setItem(0, 1, QTableWidgetItem(self.global_defs.timer_base.unit))
        self.base_display.setItem(0, 2, QTableWidgetItem(self.global_defs.timer_base.data_type))

        # 派生タイマ
        self.derived_table.setRowCount(0)
        for d in self.global_defs.timer_base.derived:
            row = self.derived_table.rowCount()
            self.derived_table.insertRow(row)
            self.derived_table.setItem(row, 0, QTableWidgetItem(d.period_name))
            self.derived_table.setItem(row, 1, QTableWidgetItem(str(d.multiplier)))
            self.derived_table.setItem(row, 2, QTableWidgetItem(d.variable_name))
            self.derived_table.setItem(row, 3, QTableWidgetItem(d.data_type))

    def on_base_double_clicked(self, row, col):
        StaTableLogger.debug(f"on_base_double_clicked: row={row}, col={col}")
        dlg = TimerBaseEditDialog(self, timer_base=self.global_defs.timer_base)
        if dlg.exec() == QDialog.Accepted:
            var, unit, typ = dlg.get_values()
            if not var:
                QMessageBox.warning(self, "警告", "基準変数名を入力してください。")
                return
            self.global_defs.timer_base.variable_name = var
            self.global_defs.timer_base.unit = unit
            self.global_defs.timer_base.data_type = typ
            self.global_defs.add_timer_variables()
            self.refresh_timer_table()

    def on_derived_double_clicked(self, row, col):
        StaTableLogger.debug(f"on_derived_double_clicked: row={row}, col={col}")
        if row < 0 or row >= len(self.global_defs.timer_base.derived):
            return
        target = self.global_defs.timer_base.derived[row]
        dlg = TimerDerivedEditDialog(self, derived=target)
        if dlg.exec() == QDialog.Accepted:
            new_d = dlg.get_derived()
            if not new_d.period_name:
                QMessageBox.warning(self, "警告", "周期名を入力してください。")
                return
            self.global_defs.timer_base.derived[row] = new_d
            self.global_defs.add_timer_variables()
            self.refresh_timer_table()

    def add_derived(self):
        dlg = TimerDerivedEditDialog(self)
        if dlg.exec() == QDialog.Accepted:
            d = dlg.get_derived()
            if not d.period_name:
                QMessageBox.warning(self, "警告", "周期名を入力してください。")
                return
            self.global_defs.timer_base.derived.append(d)
            self.global_defs.add_timer_variables()
            self.refresh_timer_table()

    def delete_derived(self):
        row = self.derived_table.currentRow()
        if 0 <= row < len(self.global_defs.timer_base.derived):
            self.global_defs.timer_base.derived.pop(row)
            self.global_defs.add_timer_variables()
            self.refresh_t