# statable_gui/transition_editor_direct/dialog.py
"""
動作編集メインダイアログ（デバッグログ強化版）
"""

import logging

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget,
    QWidget, QSplitter, QMessageBox
)
from PySide6.QtCore import Qt

from .draft import ActionDraft, FlowItem
from .palette_widget import PaletteWidget
from .canvas_widget import FlowCanvas, FlowNodeItem
from .code_widget import CodeWidget
from .system_global_dialog import SystemGlobalDialog
from .edit_dialogs import FunctionEditDialog

from statable_gui.condition_builder_dialog import ConditionBuilderDialog

logger = logging.getLogger("transition_editor_direct.dialog")


class ActionEditorDialog(QDialog):
    def __init__(self, draft: ActionDraft,
                 role_functions=None, transition_events=None,
                 states=None, global_defs=None, state_machine=None,
                 parent=None):
        super().__init__(parent)
        self.draft = draft
        self.role_functions = role_functions or []
        self.states = states or []
        self.global_defs = global_defs
        self.state_machine = state_machine

        logger.debug("=== ActionEditorDialog init ===")
        logger.debug(f"source={draft.source}, event={draft.event}")
        for i, item in enumerate(draft.flow_items):
            logger.debug(f"  flow_item[{i}]: type={item.item_type}, params={item.params}")

        self.setWindowTitle(f"動作編集: {draft.source} --[{draft.event}]--> ?")
        self.setMinimumSize(900, 650)

        self._setup_ui()
        logger.debug("=== ActionEditorDialog init end ===")

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        flow_tab = QWidget()
        flow_layout = QVBoxLayout(flow_tab)

        splitter = QSplitter(Qt.Horizontal)
        self.palette = PaletteWidget(self.role_functions)
        self.palette.setMinimumWidth(200)
        splitter.addWidget(self.palette)

        self.canvas = FlowCanvas(self.draft)
        splitter.addWidget(self.canvas)
        splitter.setSizes([200, 650])

        flow_layout.addWidget(splitter)
        self.tabs.addTab(flow_tab, "フロー編集")

        self.code_widget = CodeWidget(self.draft)
        self.tabs.addTab(self.code_widget, "コード")

        self.canvas.node_edit_requested.connect(self._on_node_edit_requested)
        self.canvas.node_delete_requested.connect(self._on_node_delete_requested)
        self.canvas.draft_updated.connect(self.code_widget.update_code)
        logger.debug("Signal connections established")

        global_btn = QPushButton("システムグローバル...")
        global_btn.clicked.connect(self._open_system_global)
        main_layout.addWidget(global_btn)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        main_layout.addLayout(btn_layout)

    def _on_node_edit_requested(self, node: FlowNodeItem):
        logger.debug(f"Node edit requested: type={node.item_type}")
        if node.item_type == "function":
            flow_item = node.flow_item
            if flow_item:
                logger.debug(f"  function item name={flow_item.name}")
                dlg = FunctionEditDialog(flow_item, self.role_functions, self)
                if dlg.exec() == QDialog.Accepted:
                    new_name, _ = dlg.get_result()
                    flow_item.name = new_name
                    flow_item.edited_text = new_name + "()"
                    self.canvas._rebuild()
                    self.code_widget.update_code()
        elif node.item_type == "transition":
            flow_item = node.flow_item
            if flow_item:
                logger.debug(f"  transition item condition='{flow_item.params.get('condition','')}'")
                dlg = ConditionBuilderDialog(
                    condition=flow_item.params.get('condition', ''),
                    global_defs=self.global_defs,
                    state_machine=self.state_machine,
                    parent=self
                )
                if dlg.exec() == QDialog.Accepted:
                    new_condition = dlg.get_condition_text()
                    logger.debug(f"  new condition='{new_condition}'")
                    flow_item.params['condition'] = new_condition
                    event_name = flow_item.params.get('event', self.draft.event)
                    flow_item.edited_text = f"{event_name}: {new_condition}" if new_condition else event_name
                    self.canvas._rebuild()
                    self.code_widget.update_code()

    def _on_node_delete_requested(self, node: FlowNodeItem):
        ret = QMessageBox.question(self, "確認", "このノードを削除しますか？")
        if ret == QMessageBox.Yes:
            flow_item = node.flow_item
            if flow_item and flow_item in self.draft.flow_items:
                self.draft.flow_items.remove(flow_item)
                self.canvas._rebuild()
                self.code_widget.update_code()
            else:
                logger.warning("Cannot delete node: flow_item not found")

    def _open_system_global(self):
        logger.debug("Opening system global dialog")
        dialog = SystemGlobalDialog(self.draft, self)
        dialog.exec()
        self.code_widget.update_code()
        logger.debug("System global dialog closed, code updated")