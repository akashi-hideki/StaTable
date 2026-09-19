# statable_gui/transition_editor_direct/dialog.py
"""Action edit main dialog (v2.2: 5-tab structure).

Tabs:
  - Transitions : ordered list of transitions
  - Actions     : cell actions (transition-independent)
  - Relations   : relations between transitions
  - Overview    : coverage / reachability report
  - Preview     : generated C code
"""

import logging
import sys
import os
from typing import List

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget,
    QWidget, QMessageBox, QToolBar, QLabel,
)
from PySide6.QtCore import Qt

from .draft import (
    ActionDraft, FlowItem, transition_to_flow_item, flow_item_to_transition,
)
from .transitions_tab import TransitionsTab
from .actions_tab import ActionsTab
from .relations_tab import RelationsTab
from .overview_tab import OverviewTab
from .code_widget import CodeWidget

from statable_gui.libcntrl.role_function_library import (
    RoleFunctionLibrary, RoleFunction,
)
from statable_gui.libcntrl.condition_library import (
    ConditionLibrary, ConditionTemplate,
)
from statable_gui.libcntrl.literal_library import LiteralLibrary

logger = logging.getLogger("transition_editor_direct.dialog")


class ActionEditorDialog(QDialog):
    """Main dialog for editing a transition cell (v2.2 / 5 tabs)."""

    TAB_NAMES = ("Transitions", "Actions", "Relations", "Overview", "Preview")

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

        self.role_function_library = (
            role_function_library if role_function_library
            else RoleFunctionLibrary()
        )
        self.condition_library = (
            condition_library if condition_library
            else ConditionLibrary()
        )
        self.literal_library = (
            literal_library if literal_library
            else LiteralLibrary()
        )

        logger.debug("=== ActionEditorDialog init ===")
        logger.debug(f"source={draft.source}, event={draft.event}")

        self.setWindowTitle(
            f"Action edit: {draft.source} --[{draft.event}]--> ?")
        self.setMinimumSize(1000, 700)

        self._setup_ui()
        self._load_draft()

        logger.debug("=== ActionEditorDialog init end ===")

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        toolbar = QToolBar()
        refresh_btn = QPushButton("Refresh preview")
        refresh_btn.clicked.connect(self._on_refresh_preview)
        toolbar.addWidget(refresh_btn)
        main_layout.addWidget(toolbar)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: Transitions
        self.transitions_tab = TransitionsTab(
            self.draft,
            states=self.states,
            global_defs=self.global_defs,
            state_machine=self.state_machine,
        )
        self.tabs.addTab(self.transitions_tab, self.TAB_NAMES[0])

        # Tab 2: Actions
        self.actions_tab = ActionsTab(
            self.draft,
            role_functions=self.role_functions,
            global_defs=self.global_defs,
            state_machine=self.state_machine,
        )
        self.tabs.addTab(self.actions_tab, self.TAB_NAMES[1])

        # Tab 3: Relations
        self.relations_tab = RelationsTab(self.draft)
        self.tabs.addTab(self.relations_tab, self.TAB_NAMES[2])

        # Tab 4: Overview
        self.overview_tab = OverviewTab(
            self.draft,
            state_machine=self.state_machine,
        )
        self.tabs.addTab(self.overview_tab, self.TAB_NAMES[3])

        # Tab 5: Preview
        self.code_widget = CodeWidget(self.draft)
        self.tabs.addTab(self.code_widget, self.TAB_NAMES[4])

        # Signal connections
        self.transitions_tab.transitions_changed.connect(
            self._on_content_changed)
        self.actions_tab.actions_changed.connect(
            self._on_content_changed)
        self.relations_tab.relations_changed.connect(
            self._on_content_changed)

        # OK / Cancel
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self._on_accept)
        btn_layout.addWidget(ok_btn)
        main_layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Load / save
    # ------------------------------------------------------------------
    def _load_draft(self):
        transitions = []
        for item in self.draft.flow_items:
            if item.item_type == "transition":
                t = flow_item_to_transition(
                    item, self.draft.source, self.draft.event)
                transitions.append(t)
        self.transitions_tab.set_transitions(transitions)

        self.actions_tab.set_actions(list(self.draft.cell_actions))
        self.relations_tab.set_relations(list(self.draft.cell_relations))

    def _save_draft(self):
        transitions = self.transitions_tab.get_transitions()
        self.draft.flow_items = [
            transition_to_flow_item(t) for t in transitions
        ]
        self.draft.cell_actions = list(self.actions_tab.get_actions())
        self.draft.cell_relations = list(self.relations_tab.get_relations())

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------
    def _on_content_changed(self):
        self._save_draft()
        self.code_widget.update_code()
        # Refresh overview so it reflects the latest edits
        try:
            self.overview_tab.refresh()
        except Exception as e:
            logger.warning(f"overview refresh failed: {e}")

    def _on_refresh_preview(self):
        self._save_draft()
        self.code_widget.update_code()
        try:
            self.overview_tab.refresh()
        except Exception as e:
            logger.warning(f"overview refresh failed: {e}")

    def _on_accept(self):
        self._save_draft()
        self.accept()

    # ------------------------------------------------------------------
    # Public API (test-friendly)
    # ------------------------------------------------------------------
    def get_tab_names(self) -> List[str]:
        return [self.tabs.tabText(i) for i in range(self.tabs.count())]