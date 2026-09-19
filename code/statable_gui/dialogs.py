# statable_gui/dialogs.py
"""Transition edit dialog (D&D edit support / v2.2 Mode column)."""

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

from .transition_editor_direct.dialog import ActionEditorDialog
from .transition_editor_direct.draft import ActionDraft, FlowItem

from .condition_builder_dialog import ConditionBuilderDialog


# ======================================================================
# Column constants (v2.2: Mode column inserted at index 5)
# ======================================================================
COL_TITLE = 0
COL_CONDITION = 1
COL_ACTION = 2
COL_TARGET = 3
COL_DISPLAY = 4
COL_MODE = 5   # v2.2
COLUMN_COUNT = 6


class TransitionTable(QTableWidget):
    """Table that reliably captures double-click events."""
    cell_double_clicked_any = Signal(int, int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        pos = event.position().toPoint()
        item = self.itemAt(pos)
        if item:
            row, col = item.row(), item.column()
            StaTableLogger.debug(
                f"TransitionTable.mouseDoubleClickEvent: row={row}, col={col}")
            self.cell_double_clicked_any.emit(row, col)
        else:
            StaTableLogger.debug(
                "TransitionTable.mouseDoubleClickEvent: no item at position")


class TransitionListDialog(QDialog):
    """Dialog to batch-edit multiple transitions in one cell.

    [v2.2]
      - Mode column (Commit / Tentative) added at index 5.
      - Transition.early_return is preserved through row<->transition conversion.
    """

    def __init__(self, parent=None, state_names=None, event_name="",
                 existing_transitions=None, role_functions=None,
                 global_defs=None, state_machine=None):
        super().__init__(parent)
        self.setWindowTitle("Transition edit (D&D visual editing)")
        self.setMinimumSize(1050, 600)
        self.state_names = state_names or []
        self.role_functions = role_functions or {}
        self.global_defs = global_defs if global_defs else GlobalDefinitions()
        self.event_name = event_name
        self.state_machine = state_machine

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            f"Event: {event_name if event_name else 'Completion transition'}"))

        self.table = TransitionTable(0, COLUMN_COUNT)
        self.table.setHorizontalHeaderLabels([
            "Title",
            "State transition condition",
            "Action",
            "Target",
            "Display title",
            "Mode",             # v2.2
        ])
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
        dnd_btn.setToolTip("Edit the selected row in the visual editor")
        dnd_btn.clicked.connect(self.open_dnd_editor)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(up_btn)
        btn_layout.addWidget(down_btn)
        btn_layout.addWidget(dnd_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
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
        if col == COL_CONDITION:
            self.open_condition_builder(row)
        elif col == COL_ACTION or col == COL_DISPLAY:
            self.open_dnd_editor_for_row(row)
        # Mode column: not double-clickable (combo box)
        # else: do nothing

    def open_condition_builder(self, row):
        item = self.table.item(row, COL_CONDITION)
        if not item:
            item = QTableWidgetItem("")
            self.table.setItem(row, COL_CONDITION, item)

        current_condition = (
            item.data(Qt.UserRole) if item.data(Qt.UserRole) else "")

        dlg = ConditionBuilderDialog(
            condition=current_condition,
            global_defs=self.global_defs,
            state_machine=self.state_machine,
            parent=self
        )
        if dlg.exec() == QDialog.Accepted:
            new_condition = dlg.get_condition_text()
            item.setText(new_condition.replace('\n', ' ; '))
            item.setData(Qt.UserRole, new_condition)
            self._update_display_title(row)
            StaTableLogger.info(f"Condition updated for row {row}")

    def open_dnd_editor_for_row(self, row):
        self.table.setCurrentCell(row, 0)
        self.open_dnd_editor()

    # ------------------------------------------------------------------
    # D&D Edit
    # ------------------------------------------------------------------
    def open_dnd_editor(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warning", "Please select a row to edit.")
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
        layer_name = getattr(self.state_machine, 'layer_name', '') or ''

        draft = ActionDraft(
            source=trans.source,
            event=trans.event,
            layer_name=layer_name,
        )
        flow_item = FlowItem(
            item_type="transition",
            name=trans.event or "Completion",
            edited_text=(
                trans.title
                if trans.title != "(untitled transition)"
                else trans.event or "Completion"
            ),
            params={
                "event": trans.event,
                "condition": trans.condition,
                "pre_actions": getattr(trans, 'pre_actions', []),
                "target": trans.target,
                "has_else": getattr(trans, 'has_else', True),
                "else_target": getattr(trans, 'else_target', ''),
                "else_actions": getattr(trans, 'else_actions', []),
                "early_return": getattr(trans, 'early_return', False),   # v2.2
                "label": getattr(trans, 'label', ''),                    # v2.2
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
                trans.early_return = params.get('early_return',
                                                getattr(trans, 'early_return', False))
                if params.get('label'):
                    trans.label = params['label']
                if item.edited_text and item.edited_text != item.name:
                    trans.title = item.edited_text
                break

    def _row_to_transition(self, row: int) -> Optional[Transition]:
        if row >= self.table.rowCount():
            return None
        title_item = self.table.item(row, COL_TITLE)
        title = title_item.text().strip() if title_item else "(untitled transition)"

        condition_item = self.table.item(row, COL_CONDITION)
        condition = (condition_item.data(Qt.UserRole)
                     if condition_item else "")

        target_widget = self.table.cellWidget(row, COL_TARGET)
        target = target_widget.currentText().strip() if target_widget else ""

        # v2.2: Mode
        mode_widget = self.table.cellWidget(row, COL_MODE)
        early_return = False
        if mode_widget is not None:
            early_return = (mode_widget.currentText().strip() == "Commit")

        return Transition(
            source="", event=self.event_name, condition=condition, action="",
            target=target, transition_type="external", title=title,
            early_return=early_return,
        )

    def _update_row_from_transition(self, row: int, trans: Transition):
        title_item = self.table.item(row, COL_TITLE)
        if title_item:
            title_item.setText(trans.title)

        cond_item = self.table.item(row, COL_CONDITION)
        if cond_item:
            cond_item.setText(trans.condition.replace('\n', ' ; '))
            cond_item.setData(Qt.UserRole, trans.condition)

        action_item = self.table.item(row, COL_ACTION)
        if action_item:
            action_item.setText("")
            action_item.setData(Qt.UserRole, "")

        target_widget = self.table.cellWidget(row, COL_TARGET)
        if target_widget:
            idx = target_widget.findText(trans.target)
            if idx >= 0:
                target_widget.setCurrentIndex(idx)

        # v2.2: Mode
        mode_widget = self.table.cellWidget(row, COL_MODE)
        if mode_widget is not None:
            mode_widget.setCurrentText(
                "Commit" if getattr(trans, 'early_return', False)
                else "Tentative"
            )

        self._update_display_title(row)

    # ------------------------------------------------------------------
    # Row management
    # ------------------------------------------------------------------
    def on_item_changed(self, item):
        if item.column() == COL_TITLE:
            row = item.row()
            display_item = self.table.item(row, COL_DISPLAY)
            if display_item:
                display_item.setText(item.text())

    def _update_display_title(self, row: int):
        title_item = self.table.item(row, COL_TITLE)
        display_item = self.table.item(row, COL_DISPLAY)
        if title_item and display_item:
            display_item.setText(title_item.text())

    def add_row(self, trans: Optional[Transition] = None):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # 0: Title
        title_text = trans.title if trans else "(untitled transition)"
        title_item = QTableWidgetItem(title_text)
        title_item.setToolTip("Title of this transition. Can be edited directly.")
        self.table.setItem(row, COL_TITLE, title_item)

        # 1: Condition
        cond_item = QTableWidgetItem(trans.condition if trans else "")
        cond_item.setToolTip("Double-click to open condition builder")
        cond_item.setData(Qt.UserRole, trans.condition if trans else "")
        self.table.setItem(row, COL_CONDITION, cond_item)

        # 2: Action
        action_text = trans.action if trans else ""
        action_item = QTableWidgetItem(action_text.replace('\n', ' ; '))
        action_item.setToolTip("Double-click for D&D editing")
        action_item.setData(Qt.UserRole, action_text)
        self.table.setItem(row, COL_ACTION, action_item)

        # 3: Target
        target_combo = QComboBox()
        target_combo.addItem("")
        target_combo.addItems(self.state_names)
        if trans and trans.target:
            idx = target_combo.findText(trans.target)
            if idx >= 0:
                target_combo.setCurrentIndex(idx)
        self.table.setCellWidget(row, COL_TARGET, target_combo)

        # 4: Display title
        display_title = self._generate_display_title(trans) if trans else ""
        display_item = QTableWidgetItem(display_title)
        display_item.setFlags(display_item.flags() & ~Qt.ItemIsEditable)
        display_item.setToolTip("Short label shown in state transition table")
        self.table.setItem(row, COL_DISPLAY, display_item)

        # 5: Mode (v2.2)
        mode_combo = QComboBox()
        mode_combo.addItems(["Commit", "Tentative"])
        if trans is not None and getattr(trans, 'early_return', False):
            mode_combo.setCurrentText("Commit")
        else:
            mode_combo.setCurrentText("Tentative")
        mode_combo.setToolTip(
            "Commit: stop evaluating later transitions (no overwrite)\n"
            "Tentative: later transitions may overwrite the target")
        self.table.setCellWidget(row, COL_MODE, mode_combo)

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
        # For widget columns (Target / Mode), swap values, not widgets
        widget_cols = (COL_TARGET, COL_MODE)
        for col in range(self.table.columnCount()):
            if col in widget_cols:
                w1 = self.table.cellWidget(row1, col)
                w2 = self.table.cellWidget(row2, col)
                if w1 is not None and w2 is not None:
                    text1 = w1.currentText()
                    text2 = w2.currentText()
                    w1.setCurrentText(text2)
                    w2.setCurrentText(text1)
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
            title_item = self.table.item(row, COL_TITLE)
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