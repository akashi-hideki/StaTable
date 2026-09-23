# statable_gui/transition_editor_direct/dialog.py
"""Action edit main dialog (v2.2: 5-tab structure).

Tabs:
  - Transitions       : ordered list of transitions
  - Pre / Post Actions: cell-level actions (before / after transitions)
  - Relations         : relations between transitions
  - Overview          : coverage / reachability report
  - Preview           : generated C code

[v2.2 fix]
  - _load_draft() order: Actions -> Relations -> Transitions (last)
    to prevent intermediate signals from wiping cell_actions /
    cell_relations before they are loaded.
  - _loading flag suppresses _on_content_changed during initial load.
  - _sync_member_details() propagates {label: "cond -> target"} to
    RelationsTab so the member list shows identifiable entries.

[v2.5 change]
  - TransitionsTab and ActionsTab now receive `role_function_library`
    and `literal_library` from this dialog.

[R-6 change]
  - ActionEditorDialog now accepts `layer_names_provider` and forwards
    it to TransitionsTab and ActionsTab.  This completes the 4-hop
    wiring:
        MainWindow → StateMachineTab → MatrixTableWidget
                  → ActionEditorDialog → TransitionsTab / ActionsTab
    so the namespace combo box on those tabs lists every layer in
    the project, not just the current tab's layer.
  - Previously this dialog intentionally did NOT forward the
    provider (v2.5 scope).  R-6 completes the wiring.
"""

import logging
import sys
import os
from typing import List, Callable

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

    TAB_NAMES = ("Transitions", "Pre / Post Actions",
                 "Relations", "Overview", "Preview")

    def __init__(self, draft: ActionDraft,
                 role_functions=None, transition_events=None,
                 states=None, global_defs=None, state_machine=None,
                 role_function_library=None, condition_library=None,
                 literal_library=None,
                 layer_names_provider: Callable[[], List[str]] = None,
                 parent=None):
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
        # [R-6] All-tabs namespace provider (forwarded to tabs).
        self.layer_names_provider = layer_names_provider

        # v2.2 fix: guard flag for _load_draft
        self._loading = False

        logger.debug("=== ActionEditorDialog init ===")
        logger.debug(f"source={draft.source}, event={draft.event}")
        logger.debug(
            f"has_layer_names_provider="
            f"{layer_names_provider is not None}")

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

        # ==============================================================
        # Tab 1: Transitions
        # ==============================================================
        # [v2.5] Pass shared libraries so "+ New Role Function" on this
        #        tab can build the same RoleFunctionDialog kwargs as
        #        SettingsPanel (global_vars / events / literals /
        #        namespace_choices).
        # [R-6]  Forward layer_names_provider so namespace_choices
        #        include every layer in the project.
        self.transitions_tab = TransitionsTab(
            self.draft,
            states=self.states,
            global_defs=self.global_defs,
            state_machine=self.state_machine,
            role_function_library=self.role_function_library,
            literal_library=self.literal_library,
            layer_names_provider=self.layer_names_provider,
        )
        # v2.2: provide role function candidates to the TransitionsTab
        self.transitions_tab.set_role_functions(self.role_functions)
        self.tabs.addTab(self.transitions_tab, self.TAB_NAMES[0])

        # ==============================================================
        # Tab 2: Pre / Post Actions
        # ==============================================================
        # [v2.5] Same context propagation as Tab 1.
        # [R-6]  Forward layer_names_provider.
        self.actions_tab = ActionsTab(
            self.draft,
            role_functions=self.role_functions,
            global_defs=self.global_defs,
            state_machine=self.state_machine,
            role_function_library=self.role_function_library,
            literal_library=self.literal_library,
            layer_names_provider=self.layer_names_provider,
        )
        self.tabs.addTab(self.actions_tab, self.TAB_NAMES[1])

        # ==============================================================
        # Tab 3: Relations
        # ==============================================================
        self.relations_tab = RelationsTab(self.draft)
        self.tabs.addTab(self.relations_tab, self.TAB_NAMES[2])

        # ==============================================================
        # Tab 4: Overview
        # ==============================================================
        self.overview_tab = OverviewTab(
            self.draft,
            state_machine=self.state_machine,
        )
        self.tabs.addTab(self.overview_tab, self.TAB_NAMES[3])

        # ==============================================================
        # Tab 5: Preview
        # ==============================================================
        self.code_widget = CodeWidget(self.draft)
        self.tabs.addTab(self.code_widget, self.TAB_NAMES[4])

        # ==============================================================
        # Signal connections
        # ==============================================================
        self.transitions_tab.transitions_changed.connect(
            self._on_content_changed)
        self.actions_tab.actions_changed.connect(
            self._on_content_changed)
        self.relations_tab.relations_changed.connect(
            self._on_content_changed)

        # ==============================================================
        # OK / Cancel
        # ==============================================================
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
        """Populate tabs from the current draft state.

        [v2.2 fix]
          Order: Actions -> Relations -> Transitions (last).
        """
        self._loading = True
        try:
            # 1. Actions first
            actions = list(self.draft.cell_actions)
            logger.debug(
                f"_load_draft: actions={len(actions)}, "
                f"relations={len(self.draft.cell_relations)}")
            self.actions_tab.set_actions(actions)

            # 2. Relations
            relations = list(self.draft.cell_relations)
            self.relations_tab.set_relations(relations)

            # 3. Transitions last (emits signals)
            transitions = []
            for item in self.draft.flow_items:
                if item.item_type == "transition":
                    t = flow_item_to_transition(
                        item, self.draft.source, self.draft.event)
                    transitions.append(t)
            self.transitions_tab.set_transitions(transitions)
        finally:
            self._loading = False

        # v2.2: sync member details before refreshing preview
        self._sync_member_details()

        # Refresh preview / overview once after load
        try:
            self.code_widget.update_code()
        except Exception as e:
            logger.warning(f"code update failed: {e}")
        try:
            self.overview_tab.refresh()
        except Exception as e:
            logger.warning(f"overview refresh failed: {e}")

    def _save_draft(self):
        """Sync tab contents back to the draft."""
        transitions = self.transitions_tab.get_transitions()
        self.draft.flow_items = [
            transition_to_flow_item(t) for t in transitions
        ]
        self.draft.cell_actions = list(self.actions_tab.get_actions())
        self.draft.cell_relations = list(self.relations_tab.get_relations())

    # ------------------------------------------------------------------
    # v2.2: member details propagation
    # ------------------------------------------------------------------
    def _sync_member_details(self):
        """Build {label: 'cond -> target [mode]'} from the TransitionsTab
        and pass it to RelationsTab so members are identifiable.
        """
        details = {}
        try:
            transitions = self.transitions_tab.get_transitions()
        except Exception as e:
            logger.warning(f"_sync_member_details failed: {e}")
            return

        for t in transitions:
            label = getattr(t, 'label', '') or ''
            if not label:
                continue
            cond = (getattr(t, 'condition', '') or '').strip() or "(no cond)"
            target = (getattr(t, 'target', '') or '').strip() or "(none)"
            mode = "Commit" if getattr(t, 'early_return', False) else "Tentative"
            details[label] = f"{cond} -> {target}  [{mode}]"

        self.relations_tab.set_member_details(details)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------
    def _on_content_changed(self):
        # v2.2 fix: ignore signals emitted during initial load
        if getattr(self, "_loading", False):
            return

        self._save_draft()
        self._sync_member_details()
        self.code_widget.update_code()
        try:
            self.overview_tab.refresh()
        except Exception as e:
            logger.warning(f"overview refresh failed: {e}")

    def _on_refresh_preview(self):
        self._save_draft()
        self._sync_member_details()
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