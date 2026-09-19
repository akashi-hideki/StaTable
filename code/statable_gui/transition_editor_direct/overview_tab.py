# statable_gui/transition_editor_direct/overview_tab.py
"""Overview tab widget (v2.2).

Shows coverage analysis for the current cell and the whole state machine.
"""

import logging
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QPlainTextEdit,
    QLabel, QSplitter,
)

from .draft import ActionDraft
from .coverage_analyzer import CoverageAnalyzer

logger = logging.getLogger("transition_editor_direct.overview_tab")


class OverviewTab(QWidget):
    """Overview tab: coverage / reachability report."""

    def __init__(self, draft: ActionDraft,
                 state_machine=None, parent=None):
        super().__init__(parent)
        self.draft = draft
        self.state_machine = state_machine
        self.analyzer = CoverageAnalyzer()

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Coverage / reachability report"))
        top.addStretch()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        top.addWidget(refresh_btn)
        layout.addLayout(top)

        splitter = QSplitter(Qt.Vertical)

        # Cell-internal
        cell_box = QWidget()
        cell_layout = QVBoxLayout(cell_box)
        cell_layout.setContentsMargins(0, 0, 0, 0)
        cell_layout.addWidget(QLabel("Cell-level analysis"))
        self.cell_view = QPlainTextEdit()
        self.cell_view.setReadOnly(True)
        self.cell_view.setFont(QFont("Consolas", 10))
        cell_layout.addWidget(self.cell_view)
        splitter.addWidget(cell_box)

        # State graph
        graph_box = QWidget()
        graph_layout = QVBoxLayout(graph_box)
        graph_layout.setContentsMargins(0, 0, 0, 0)
        graph_layout.addWidget(QLabel("State graph analysis"))
        self.graph_view = QPlainTextEdit()
        self.graph_view.setReadOnly(True)
        self.graph_view.setFont(QFont("Consolas", 10))
        graph_layout.addWidget(self.graph_view)
        splitter.addWidget(graph_box)

        layout.addWidget(splitter)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def refresh(self):
        """Recompute analysis and update views."""
        self._refresh_cell_view()
        self._refresh_graph_view()

    def get_summary_text(self) -> str:
        """Return a plain-text summary (test-friendly)."""
        return (self.cell_view.toPlainText() + "\n\n"
                + self.graph_view.toPlainText())

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _refresh_cell_view(self):
        sm = self.state_machine
        source = self.draft.source
        event = self.draft.event

        lines = []
        lines.append(f"Cell: {source} -[{event or 'Completion'}]->")

        if sm is None:
            lines.append("(state machine not available)")
            self.cell_view.setPlainText("\n".join(lines))
            return

        report = self.analyzer.analyze_cell(sm, source, event)
        lines.append(f"Transitions: {report.transitions_count}")
        lines.append("")

        if report.unreachable_labels:
            lines.append("Unreachable transitions:")
            for lbl in report.unreachable_labels:
                lines.append(f"  - {lbl}")
        else:
            lines.append("Unreachable transitions: none")

        lines.append("")

        if report.duplicate_targets:
            lines.append("Duplicate targets:")
            for tgt, labels in report.duplicate_targets.items():
                lines.append(f"  - {tgt}: {', '.join(labels)}")
        else:
            lines.append("Duplicate targets: none")

        lines.append("")

        if report.overlap_pairs:
            lines.append("Possible condition overlaps:")
            for a, b in report.overlap_pairs:
                lines.append(f"  - {a} and {b}")
        else:
            lines.append("Possible condition overlaps: none")

        self.cell_view.setPlainText("\n".join(lines))

    def _refresh_graph_view(self):
        sm = self.state_machine
        lines = []

        if sm is None:
            lines.append("(state machine not available)")
            self.graph_view.setPlainText("\n".join(lines))
            return

        report = self.analyzer.analyze_state_graph(sm)

        lines.append(f"States: {len(sm.states)}")
        lines.append(f"Initial: {getattr(sm, 'initial_state', None) or '(unset)'}")
        lines.append("")

        if report.unreachable_states:
            lines.append("Unreachable states:")
            for s in report.unreachable_states:
                lines.append(f"  - {s}")
        else:
            lines.append("Unreachable states: none")

        lines.append("")

        if report.terminal_states:
            lines.append("Terminal states (no outgoing):")
            for s in report.terminal_states:
                lines.append(f"  - {s}")
        else:
            lines.append("Terminal states: none")

        lines.append("")

        if report.self_loops:
            lines.append("Self loops:")
            for src, evt in report.self_loops:
                lines.append(f"  - {src} -[{evt or 'Completion'}]-> {src}")
        else:
            lines.append("Self loops: none")

        self.graph_view.setPlainText("\n".join(lines))