# statable_gui/transition_editor_direct/dialog.py
"""
動作編集メインダイアログ（共有ライブラリ対応・操作性改善版）
"""

import logging
import sys
import os

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget,
    QWidget, QSplitter, QMessageBox, QToolBar
)
from PySide6.QtCore import Qt

from .draft import ActionDraft, FlowItem
from .palette_widget import PaletteWidget
from .canvas_widget import FlowCanvas, FlowNodeItem
from .code_widget import CodeWidget
from .system_global_dialog import SystemGlobalDialog

# 条件ビルダー
try:
    from condition_builder_dialog import ConditionBuilderDialog
except ImportError:
    from statable_gui.condition_builder_dialog import ConditionBuilderDialog

# 共有ライブラリ
try:
    from libcntrl.role_function_library import RoleFunctionLibrary, RoleFunction
    from libcntrl.condition_library import ConditionLibrary
    from libcntrl.literal_library import LiteralLibrary
    from libcntrl.role_function_edit_dialog import RoleFunctionEditDialog
except ImportError:
    from statable_gui.libcntrl.role_function_library import RoleFunctionLibrary, RoleFunction
    from statable_gui.libcntrl.condition_library import ConditionLibrary
    from statable_gui.libcntrl.literal_library import LiteralLibrary
    from statable_gui.libcntrl.role_function_edit_dialog import RoleFunctionEditDialog

logger = logging.getLogger("transition_editor_direct.dialog")


class ActionEditorDialog(QDialog):
    def __init__(self, draft: ActionDraft,
                 role_functions=None, transition_events=None,
                 states=None, global_defs=None, state_machine=None,
                 role_function_library=None, condition_library=None,
                 literal_library=None, parent=None):
        super().__init__(parent)
        self.draft = draft
        self.role_functions = role_functions or []
        self.states = states or []
        self.global_defs = global_defs
        self.state_machine = state_machine

        # 共有ライブラリ（なければ新規作成）
        self.role_function_library = role_function_library if role_function_library else RoleFunctionLibrary()
        self.condition_library = condition_library if condition_library else ConditionLibrary()
        self.literal_library = literal_library if literal_library else LiteralLibrary()

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

        # ツールバー
        toolbar = QToolBar()
        auto_align_btn = QPushButton("自動整列")
        auto_align_btn.clicked.connect(self.canvas_auto_align)
        toolbar.addWidget(auto_align_btn)
        main_layout.addWidget(toolbar)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        flow_tab = QWidget()
        flow_layout = QVBoxLayout(flow_tab)

        splitter = QSplitter(Qt.Horizontal)

        # パレットには共有ライブラリの関数名リストを渡す
        function_names = [rf.name for rf in self.role_function_library.list_all()]
        if not function_names:
            function_names = self.role_functions

        self.palette = PaletteWidget(function_names)
        self.palette.setMinimumWidth(200)
        splitter.addWidget(self.palette)

        self.canvas = FlowCanvas(self.draft)
        splitter.addWidget(self.canvas)
        splitter.setSizes([200, 650])

        flow_layout.addWidget(splitter)
        self.tabs.addTab(flow_tab, "フロー編集")

        self.code_widget = CodeWidget(self.draft)
        self.tabs.addTab(self.code_widget, "コード")

        # シグナル接続
        self.canvas.node_edit_requested.connect(self._on_node_edit_requested)
        self.canvas.node_delete_requested.connect(self._on_node_delete_requested)
        self.canvas.node_duplicate_requested.connect(self._on_node_duplicate_requested)
        self.canvas.node_move_up_requested.connect(self._on_node_move_up_requested)
        self.canvas.node_move_down_requested.connect(self._on_node_move_down_requested)
        self.canvas.draft_updated.connect(self.code_widget.update_code)

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

    def canvas_auto_align(self):
        """キャンバスのノードを自動整列"""
        self.canvas.auto_align()

    def _on_node_edit_requested(self, node: FlowNodeItem):
        logger.debug(f"Node edit requested: type={node.item_type}")
        if node.item_type == "function":
            flow_item = node.flow_item
            if flow_item:
                # 共有ライブラリからロール関数を取得（なければ新規）
                rf = self.role_function_library.get(flow_item.name)
                if rf is None:
                    rf = RoleFunction(name=flow_item.name, title=flow_item.name)
                    self.role_function_library.add(rf)

                # 使用可能なグローバル変数・イベント・リテラルを収集
                global_vars = [v.name for v in getattr(self.global_defs, 'variables', [])]
                events = [e.name for e in self.state_machine.events.values()] if self.state_machine else []
                literals = [lit.name for lit in self.literal_library.list_all()]

                dlg = RoleFunctionEditDialog(
                    rf,
                    global_vars=global_vars,
                    events=events,
                    literals=literals,
                    parent=self
                )
                if dlg.exec() == QDialog.Accepted:
                    updated_rf = dlg.get_role_function()
                    flow_item.name = updated_rf.name
                    flow_item.edited_text = updated_rf.name + "()"
                    self.canvas._rebuild()
                    self.code_widget.update_code()

        elif node.item_type == "transition":
            flow_item = node.flow_item
            if flow_item:
                logger.debug(f"  transition item condition='{flow_item.params.get('condition','')}'")
                dlg = ConditionBuilderDialog(
                    condition=flow_item.params.get('condition', ''),
                    event_name=flow_item.params.get('event', self.draft.event),
                    global_defs=self.global_defs,
                    state_machine=self.state_machine,
                    literal_library=self.literal_library,
                    parent=self
                )
                if dlg.exec() == QDialog.Accepted:
                    new_condition = dlg.get_condition_text()
                    new_event_name = dlg.get_event_name()
                    logger.debug(f"  new condition='{new_condition}', new event='{new_event_name}'")
                    flow_item.params['condition'] = new_condition
                    flow_item.params['event'] = new_event_name
                    flow_item.name = new_event_name if new_event_name else "NewEvent"
                    if new_condition:
                        flow_item.edited_text = f"{new_event_name}: {new_condition}" if new_event_name else new_condition
                    else:
                        flow_item.edited_text = new_event_name if new_event_name else "NewEvent"
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

    def _on_node_duplicate_requested(self, node: FlowNodeItem):
        """ノードを複製して下に追加"""
        flow_item = node.flow_item
        if flow_item:
            # 深いコピーを作成
            import copy
            new_item = copy.deepcopy(flow_item)
            # 名前を少し変える（例：NewEvent_2）
            if new_item.item_type == "transition":
                base = new_item.params.get('event', 'NewEvent')
                new_item.params['event'] = base + "_copy"
                new_item.name = base + "_copy"
                new_item.edited_text = base + "_copy"
            else:
                new_item.name = new_item.name + "_copy"
                new_item.edited_text = new_item.name + "()"
            self.draft.flow_items.append(new_item)
            self.canvas._rebuild()
            self.code_widget.update_code()

    def _on_node_move_up_requested(self, node: FlowNodeItem):
        """ノードを上へ移動"""
        flow_item = node.flow_item
        if flow_item and flow_item in self.draft.flow_items:
            idx = self.draft.flow_items.index(flow_item)
            if idx > 0:
                self.draft.flow_items.pop(idx)
                self.draft.flow_items.insert(idx - 1, flow_item)
                self.canvas._rebuild()
                self.code_widget.update_code()

    def _on_node_move_down_requested(self, node: FlowNodeItem):
        """ノードを下へ移動"""
        flow_item = node.flow_item
        if flow_item and flow_item in self.draft.flow_items:
            idx = self.draft.flow_items.index(flow_item)
            if idx < len(self.draft.flow_items) - 1:
                self.draft.flow_items.pop(idx)
                self.draft.flow_items.insert(idx + 1, flow_item)
                self.canvas._rebuild()
                self.code_widget.update_code()

    def _open_system_global(self):
        logger.debug("Opening system global dialog")
        dialog = SystemGlobalDialog(self.draft, self)
        dialog.exec()
        self.code_widget.update_code()
        logger.debug("System global dialog closed, code updated")