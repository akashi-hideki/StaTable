# statable_gui/dialogs.py
"""\nTransition edit dialog (D&D edit support / condition builder direct launch support)\n"""

from typing import Optional, List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QComboBox, QDialogButtonBox,
    QAbstractItemView, QMessageBox
)
from PySide6.QtGui import QFont, QMouseEvent
from PySide6.QtCore import Qt, Signal

from statable.model import Transition
from .global_defs import GlobalDefinitions
from .logger import StaTableLogger

# D&D editor integration
from .transition_editor_direct.dialog import ActionEditorDialog
from .transition_editor_direct.draft import ActionDraft, FlowItem

# Condition builder
from .condition_builder_dialog import ConditionBuilderDialog


class TransitionTable(QTableWidget):
    """Table that reliably captures double-click events"""
    cell_double_clicked_any = Signal(int, int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        pos = event.position().toPoint()
        item = self.itemAt(pos)
        if item:
            row, col = item.row(), item.column()
            StaTableLogger.debug(f"TransitionTable.mouseDoubleClickEvent: row={row}, col={col}")
            self.cell_double_clicked_any.emit(row, col)
        else:
            StaTableLogger.debug("TransitionTable.mouseDoubleClickEvent: no item at position")


class TransitionListDialog(QDialog):
    """Dialog to batch-edit multiple transitions in one cell (D&D edit support, condition builder direct launch)"""

    def __init__(self, parent=None, state_names=None, event_name="",
                 existing_transitions=None, role_functions=None, global_defs=None,
                 state_machine=None):
        super().__init__(parent)
        self.setWindowTitle("TransitionEdit（D&DビジュアルEdit）")
        self.setMinimumSize(1000, 600)
        self.state_names = state_names or []
        self.role_functions = role_functions or {}
        self.global_defs = global_defs if global_defs else GlobalDefinitions()
        self.event_name = event_name
        self.state_machine = state_machine

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"イベント: {event_name if event_name else 'Completion transition'}"))

        self.table = TransitionTable(0, 5)
        self.table.setHorizontalHeaderLabels(["Title", "State transition condition", "Action", "Target", "表示Title"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setFont(QFont("Consolas", 10))
        layout.addWidget(self.table)

        self.table.cell_double_clicked_any.connect(self.on_cell_double_clicked)
        self.table.itemChanged.connect(self.on_item_changed)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add row")
        add_btn.clicked.connect(lambda: self.add_row())
        del_btn = QPushButton("Delete row")
        del_btn.clicked.connect(lambda: self.delete_row())
        up_btn = QPushButton("Move up")
        up_btn.clicked.connect(lambda: self.move_row_up())
        down_btn = QPushButton("Move down")
        down_btn.clicked.connect(lambda: self.move_row_down())

        dnd_btn = QPushButton("D&DEdit")
        dnd_btn.setToolTip("Selection中のRowをビジュアルエディタでEditしdoes")
        dnd_btn.clicked.connect(self.open_dnd_editor)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(up_btn)
        btn_layout.addWidget(down_btn)
        btn_layout.addWidget(dnd_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if existing_transitions:
            for trans in existing_transitions:
                self.add_row(trans)
        else:
            self.add_row()

        StaTableLogger.debug("TransitionListDialog initialization completed")

    # ------------------------------------------------------------------
    # Double-click handling
    # ------------------------------------------------------------------
    def on_cell_double_clicked(self, row, col):
        """列に応じてEditダイアログを切り替える"""
        if col == 1:
            # State transition condition列 → Condition builder
            self.open_condition_builder(row)
        elif col == 2 or col == 4:
            # Action column or display title column -> D&D editor
            self.open_dnd_editor_for_row(row)
        else:
            # Do nothing otherwise
            pass

    def open_condition_builder(self, row):
        """Conditionビルダーを開いてCondition式をEditする"""
        item = self.table.item(row, 1)
        if not item:
            item = QTableWidgetItem("")
            self.table.setItem(row, 1, item)

        current_condition = item.data(Qt.UserRole) if item.data(Qt.UserRole) else ""

        dlg = ConditionBuilderDialog(
            condition=current_condition,
            global_defs=self.global_defs,
            state_machine=self.state_machine,
            parent=self
        )
        if dlg.exec() == QDialog.Accepted:
            new_condition = dlg.get_condition_text()  # Symbol name text
            item.setText(new_condition.replace('\n', ' ; '))
            item.setData(Qt.UserRole, new_condition)
            self._update_display_title(row)
            StaTableLogger.info(f"Condition updated for row {row}")

    def open_dnd_editor_for_row(self, row):
        """Open D&D editor for specified row"""
        self.table.setCurrentCell(row, 0)
        self.open_dnd_editor()

    # ------------------------------------------------------------------
    # D&DEdit
    # ------------------------------------------------------------------
    def open_dnd_editor(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warning", "EditするRowをSelectionしてください。")
            return

        trans = self._row_to_transition(row)
        if trans is None:
            return

        draft = self._transition_to_draft(trans)

        role_func_names = []
        if isinstance(self.role_functions, dict):
            role_func_names = list(self.role_functions.keys())
        elif isinstance(self.role_functions, list):
            role_func_names = self.role_functions

        transition_events = [trans.event] if trans.event else []
        states = self.state_names

        dialog = ActionEditorDialog(
            draft,
            role_functions=role_func_names,
            transition_events=transition_events,
            states=states,
            global_defs=self.global_defs,
            state_machine=self.state_machine,
            parent=self
        )
        if dialog.exec() == ActionEditorDialog.Accepted:
            self._draft_to_transition(draft, trans)
            self._update_row_from_transition(row, trans)
            StaTableLogger.info(f"D&D editing completed for row {row}")
    def _transition_to_draft(self, trans: Transition) -> ActionDraft:
        """\n        Transition -> ActionDraft conversion\n\n        [v1.6 change] pass layer_name (section 11.2 #4)\n          code_widget._get_layer_name() gives this the highest priority,\n          so explicitly propagate the SM's layer name here.\n        """
        # v1.6: get SM's layer_name (if empty, defer to fallback)
        layer_name = getattr(self.state_machine, 'layer_name', '') or ''

        draft = ActionDraft(
            source=trans.source,
            event=trans.event,
            layer_name=layer_name,   # v1.6 added
        )
        flow_item = FlowItem(
            item_type="transition",
            name=trans.event or "Completion",
            edited_text=trans.title if trans.title != "(untitled transition)" else trans.event or "Completion",
            params={
                "event": trans.event,
                "condition": trans.condition,
                "pre_actions": getattr(trans, 'pre_actions', []),
                "target": trans.target,
                "has_else": getattr(trans, 'has_else', True),
                "else_target": getattr(trans, 'else_target', ''),
                "else_actions": getattr(trans, 'else_actions', []),
            }
        )
        draft.flow_items.append(flow_item)
        return draft

    def _draft_to_transition(self, draft: ActionDraft, trans: Transition) -> None:
        for item in draft.flow_items:
            if item.item_type == "transition":
                params = item.params
                trans.condition = params.get('condition', '')
                trans.pre_actions = params.get('pre_actions', [])
                trans.target = params.get('target', '')
                trans.has_else = params.get('has_else', True)
                trans.else_target = params.get('else_target', '')
                trans.else_actions = params.get('else_actions', [])
                if item.edited_text and item.edited_text != item.name:
                    trans.title = item.edited_text
                break

    def _row_to_transition(self, row: int) -> Optional[Transition]:
        if row >= self.table.rowCount():
            return None
        title_item = self.table.item(row, 0)
        title = title_item.text().strip() if title_item else "(untitled transition)"
        condition_item = self.table.item(row, 1)
        condition = condition_item.data(Qt.UserRole) if condition_item else ""
        target_widget = self.table.cellWidget(row, 3)
        target = target_widget.currentText().strip() if target_widget else ""
        return Transition(
            source="", event=self.event_name, condition=condition, action="",
            target=target, transition_type="external", title=title,
        )

    def _update_row_from_transition(self, row: int, trans: Transition):
        title_item = self.table.item(row, 0)
        if title_item:
            title_item.setText(trans.title)
        cond_item = self.table.item(row, 1)
        if cond_item:
            cond_item.setText(trans.condition.replace('\n', ' ; '))
            cond_item.setData(Qt.UserRole, trans.condition)
        action_item = self.table.item(row, 2)
        if action_item:
            action_item.setText("")
            action_item.setData(Qt.UserRole, "")
        target_widget = self.table.cellWidget(row, 3)
        if target_widget:
            idx = target_widget.findText(trans.target)
            if idx >= 0:
                target_widget.setCurrentIndex(idx)
        self._update_display_title(row)

    # ------------------------------------------------------------------
    # Row management
    # ------------------------------------------------------------------
    def on_item_changed(self, item):
        if item.column() == 0:
            StaTableLogger.debug(f"Title edited directly: row={item.row()}, text='{item.text()}'")
            row = item.row()
            display_item = self.table.item(row, 4)
            if display_item:
                display_item.setText(item.text())

    def _update_display_title(self, row: int):
        title_item = self.table.item(row, 0)
        display_item = self.table.item(row, 4)
        if title_item and display_item:
            display_item.setText(title_item.text())

    def add_row(self, trans: Optional[Transition] = None):
        row = self.table.rowCount()
        self.table.insertRow(row)

        title_text = trans.title if trans else "(untitled transition)"
        title_item = QTableWidgetItem(title_text)
        title_item.setToolTip("このTransitionのTitle。直接Editできdoes。")
        self.table.setItem(row, 0, title_item)

        cond_item = QTableWidgetItem(trans.condition if trans else "")
        cond_item.setToolTip("Double-click to open condition builder")
        cond_item.setData(Qt.UserRole, trans.condition if trans else "")
        self.table.setItem(row, 1, cond_item)

        action_text = trans.action if trans else ""
        action_item = QTableWidgetItem(action_text.replace('\n', ' ; '))
        action_item.setToolTip("ダブルクリックでD&DEdit")
        action_item.setData(Qt.UserRole, action_text)
        self.table.setItem(row, 2, action_item)

        target_combo = QComboBox()
        target_combo.addItem("")
        target_combo.addItems(self.state_names)
        if trans and trans.target:
            idx = target_combo.findText(trans.target)
            if idx >= 0:
                target_combo.setCurrentIndex(idx)
        self.table.setCellWidget(row, 3, target_combo)

        display_title = self._generate_display_title(trans) if trans else ""
        display_item = QTableWidgetItem(display_title)
        display_item.setFlags(display_item.flags() & ~Qt.ItemIsEditable)
        display_item.setToolTip("Short label shown in state transition table")
        self.table.setItem(row, 4, display_item)

    def delete_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def move_row_up(self):
        row = self.table.currentRow()
        if row > 0:
            self._swap_rows(row, row - 1)

    def move_row_down(self):
        row = self.table.currentRow()
        if row >= 0 and row < self.table.rowCount() - 1:
            self._swap_rows(row, row + 1)

    def _swap_rows(self, row1: int, row2: int):
        for col in range(self.table.columnCount()):
            if col == 3:
                combo1 = self.table.cellWidget(row1, col)
                combo2 = self.table.cellWidget(row2, col)
                if combo1 and combo2:
                    text1 = combo1.currentText()
                    text2 = combo2.currentText()
                    combo1.setCurrentText(text2)
                    combo2.setCurrentText(text1)
            else:
                item1 = self.table.takeItem(row1, col)
                item2 = self.table.takeItem(row2, col)
                self.table.setItem(row1, col, item2)
                self.table.setItem(row2, col, item1)

    def _generate_display_title(self, trans: Optional[Transition]) -> str:
        if not trans:
            return ""
        if trans.title and trans.title != "(untitled transition)":
            return trans.title
        parts = [trans.target] if trans.target else ["(internal)"]
        if trans.condition:
            condition_display = trans.condition.replace('\n', ' ; ')
            parts.append(f"[{condition_display[:30]}]")
        return " ".join(parts)

    def _on_accept(self):
        for row in range(self.table.rowCount()):
            title_item = self.table.item(row, 0)
            if title_item and not title_item.text().strip():
                title_item.setText("(untitled transition)")
            self._update_display_title(row)
        self.accept()

    def get_transitions(self) -> List[Transition]:
        transitions = []
        for row in range(self.table.rowCount()):
            trans = self._row_to_transition(row)
            if trans:
                transitions.append(trans)
        return transitions