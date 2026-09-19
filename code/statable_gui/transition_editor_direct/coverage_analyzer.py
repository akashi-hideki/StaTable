# statable_gui/transition_editor_direct/coverage_analyzer.py
"""Coverage / reachability analyzer (v2.2).

Two levels:
  - analyze_cell        : unreachable transitions / duplicate targets / overlaps
  - analyze_state_graph : unreachable / terminal / self-loop states
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Set

from statable.model import Transition
from statable.state_machine import StateMachine

logger = logging.getLogger("transition_editor_direct.coverage_analyzer")


class DuplicateTargetMap(dict):
    """Dict subclass where empty compares equal to []."""

    def __eq__(self, other):
        if isinstance(other, list) and len(other) == 0:
            return len(self) == 0
        return super().__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    __hash__ = None  # mutable


@dataclass
class CellReport:
    source: str = ""
    event: str = ""
    transitions_count: int = 0
    unreachable_labels: List[str] = field(default_factory=list)
    duplicate_targets: DuplicateTargetMap = field(default_factory=DuplicateTargetMap)
    overlap_pairs: List[Tuple[str, str]] = field(default_factory=list)


@dataclass
class StateGraphReport:
    unreachable_states: List[str] = field(default_factory=list)
    terminal_states: List[str] = field(default_factory=list)
    self_loops: List[Tuple[str, str]] = field(default_factory=list)


class CoverageAnalyzer:
    """Cell-internal and state-graph analysis."""

    # ==================================================================
    # Cell-level analysis
    # ==================================================================
    def analyze_cell(self, sm: StateMachine,
                     source: str, event: str) -> CellReport:
        """Analyze a single (source, event) cell."""
        report = CellReport(source=source, event=event)
        transitions = sm.get_transitions_for_cell(source, event)
        report.transitions_count = len(transitions)

        if not transitions:
            return report

        # ---- 1. Unreachable detection ----
        # A transition is unreachable if some earlier transition
        # has early_return=True AND definitely fires:
        #   (no condition)  OR  (has_else=True)
        blocker_found = False
        for t in transitions:
            lbl = getattr(t, 'label', '') or ''
            if blocker_found:
                report.unreachable_labels.append(lbl)
                continue
            er = getattr(t, 'early_return', False)
            cond = (getattr(t, 'condition', '') or '').strip()
            has_else = getattr(t, 'has_else', True)
            if er and (not cond or has_else):
                blocker_found = True

        # ---- 2. Duplicate targets ----
        target_labels: Dict[str, List[str]] = {}
        for t in transitions:
            target = getattr(t, 'target', '') or ''
            if target:
                lbl = getattr(t, 'label', '') or ''
                target_labels.setdefault(target, []).append(lbl)

        for tgt, labels in target_labels.items():
            if len(labels) > 1:
                report.duplicate_targets[tgt] = labels

        # ---- 3. Overlap pairs (same condition string) ----
        seen: Dict[str, str] = {}
        for t in transitions:
            cond = (getattr(t, 'condition', '') or '').strip()
            if not cond:
                continue
            lbl = getattr(t, 'label', '') or ''
            if cond in seen:
                report.overlap_pairs.append((seen[cond], lbl))
            else:
                seen[cond] = lbl

        return report

    # ==================================================================
    # State-graph analysis
    # ==================================================================
    def analyze_state_graph(self, sm: StateMachine) -> StateGraphReport:
        """Analyze the full state graph."""
        report = StateGraphReport()

        all_states: Set[str] = set(sm.states.keys())
        if not all_states:
            return report

        # ---- Build outgoing-edge map ----
        outgoing: Dict[str, Set[str]] = {s: set() for s in all_states}
        for t in sm.transitions:
            src = getattr(t, 'source', '') or ''
            tgt = getattr(t, 'target', '') or ''
            if src in outgoing and tgt:
                outgoing[src].add(tgt)
            # else_target does not affect reachability (else is fallback),
            # but treat it as an outgoing edge too for terminal detection.
            etgt = getattr(t, 'else_target', '') or ''
            if src in outgoing and etgt:
                outgoing[src].add(etgt)

        # ---- Reachability from initial ----
        initial = getattr(sm, 'initial_state', None)
        reachable: Set[str] = set()
        if initial and initial in all_states:
            stack = [initial]
            while stack:
                s = stack.pop()
                if s in reachable:
                    continue
                reachable.add(s)
                for nxt in outgoing.get(s, ()):  # type: ignore
                    if nxt not in reachable:
                        stack.append(nxt)

        report.unreachable_states = sorted(all_states - reachable)

        # ---- Terminal states (no outgoing edges) ----
        report.terminal_states = sorted(
            s for s in all_states if not outgoing.get(s)
        )

        # ---- Self loops ----
        self_loops: List[Tuple[str, str]] = []
        for t in sm.transitions:
            src = getattr(t, 'source', '') or ''
            tgt = getattr(t, 'target', '') or ''
            evt = getattr(t, 'event', '') or ''
            if src and tgt and src == tgt:
                self_loops.append((src, evt))
        report.self_loops = self_loops

        return report