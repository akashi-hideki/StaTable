# codegen/cell_validator.py
"""Cell-level validator for StaTable v2.2.

Independent of the existing validate layer to avoid intrusiveness.
Placed at codegen/ top-level (not under codegen/validate/) because
the legacy codegen/validate/__init__.py has a pre-existing broken
import chain (from validate.logger import logger).

Validates cell_actions / cell_relations / multi-transition cells.

Rules:
  CELL_EMPTY_CONDITION      (Warning) condition empty AND target empty
  CELL_DUPLICATE_LABEL      (Error)   same label within one cell
  CELL_DANGLING_RELATION    (Error)   relation members referencing missing labels
  CELL_UNREACHABLE_TRANSITION (Warning) transition after a Commit+else
  CELL_OVERLAP_POSSIBLE     (Warning) duplicate condition strings in one cell
  CELL_DUPLICATE_TARGET     (Info)    multiple transitions targeting the same state
  CELL_EXCLUSIVE_NO_RETURN  (Info)    exclusive member without early_return
  CELL_EMPTY_TARGET         (Warning) target empty AND early_return False
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger("codegen.cell_validator")


@dataclass
class Issue:
    """A single validation issue."""
    code: str
    level: str          # "Error" | "Warning" | "Info"
    message: str
    location: str = ""  # e.g. "Idle/START"

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "level": self.level,
            "message": self.message,
            "location": self.location,
        }


class CellValidator:
    """Validates each (source, event) cell."""

    LEVEL_ERROR = "Error"
    LEVEL_WARNING = "Warning"
    LEVEL_INFO = "Info"

    def __init__(self):
        self.issues: List[Issue] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def validate(self, state_machine) -> List[Issue]:
        """Validate the whole StateMachine. Returns a list of Issue."""
        self.issues = []
        if state_machine is None:
            return []

        cells = self._collect_cells(state_machine)
        for (source, event) in cells:
            transitions = state_machine.get_transitions_for_cell(
                source, event)
            relations = state_machine.get_relations_for_cell(
                source, event)
            if not transitions and not relations:
                continue
            loc = f"{source}/{event or 'Completion'}"
            self._validate_cell(loc, transitions, relations)

        return self.issues

    # ------------------------------------------------------------------
    # Cell collection
    # ------------------------------------------------------------------
    def _collect_cells(self, sm):
        """Return all (source, event) keys that have transitions or relations."""
        keys = set()
        for t in sm.transitions:
            keys.add((t.source, t.event or ""))
        for (s, e) in sm.get_cell_keys():
            keys.add((s, e))
        return sorted(keys)

    # ------------------------------------------------------------------
    # Per-cell validation
    # ------------------------------------------------------------------
    def _validate_cell(self, loc: str, transitions, relations):
        self._check_empty_condition(loc, transitions)
        self._check_duplicate_label(loc, transitions)
        self._check_dangling_relation(loc, transitions, relations)
        self._check_unreachable(loc, transitions)
        self._check_overlap(loc, transitions)
        self._check_duplicate_target(loc, transitions)
        self._check_exclusive_no_return(loc, transitions, relations)
        self._check_empty_target(loc, transitions)

    # ------------------------------------------------------------------
    # Rule 1: CELL_EMPTY_CONDITION
    # ------------------------------------------------------------------
    def _check_empty_condition(self, loc, transitions):
        for t in transitions:
            cond = (getattr(t, "condition", "") or "").strip()
            target = (getattr(t, "target", "") or "").strip()
            if not cond and not target:
                label = getattr(t, "label", "") or "(no label)"
                self._add(
                    "CELL_EMPTY_CONDITION",
                    self.LEVEL_WARNING,
                    f"Transition '{label}' has no condition and no target "
                    f"(no-op transition)",
                    loc,
                )

    # ------------------------------------------------------------------
    # Rule 2: CELL_DUPLICATE_LABEL
    # ------------------------------------------------------------------
    def _check_duplicate_label(self, loc, transitions):
        seen = {}
        for t in transitions:
            label = getattr(t, "label", "") or ""
            if not label:
                continue
            if label in seen:
                self._add(
                    "CELL_DUPLICATE_LABEL",
                    self.LEVEL_ERROR,
                    f"Duplicate transition label '{label}'",
                    loc,
                )
            else:
                seen[label] = True

    # ------------------------------------------------------------------
    # Rule 3: CELL_DANGLING_RELATION
    # ------------------------------------------------------------------
    def _check_dangling_relation(self, loc, transitions, relations):
        valid = {getattr(t, "label", "") or "" for t in transitions}
        valid.discard("")
        for r in relations:
            for m in (r.members or []):
                if m not in valid:
                    self._add(
                        "CELL_DANGLING_RELATION",
                        self.LEVEL_ERROR,
                        f"Relation references missing label '{m}'",
                        loc,
                    )

    # ------------------------------------------------------------------
    # Rule 4: CELL_UNREACHABLE_TRANSITION
    # ------------------------------------------------------------------
    def _check_unreachable(self, loc, transitions):
        blocker_found = False
        for t in transitions:
            label = getattr(t, "label", "") or "(no label)"
            if blocker_found:
                self._add(
                    "CELL_UNREACHABLE_TRANSITION",
                    self.LEVEL_WARNING,
                    f"Transition '{label}' is unreachable "
                    f"(a prior Commit transition always fires)",
                    loc,
                )
                continue
            er = getattr(t, "early_return", False)
            cond = (getattr(t, "condition", "") or "").strip()
            has_else = getattr(t, "has_else", True)
            if er and (not cond or has_else):
                blocker_found = True

    # ------------------------------------------------------------------
    # Rule 5: CELL_OVERLAP_POSSIBLE
    # ------------------------------------------------------------------
    def _check_overlap(self, loc, transitions):
        seen = {}
        for t in transitions:
            cond = (getattr(t, "condition", "") or "").strip()
            if not cond:
                continue
            label = getattr(t, "label", "") or "(no label)"
            if cond in seen:
                self._add(
                    "CELL_OVERLAP_POSSIBLE",
                    self.LEVEL_WARNING,
                    f"Transitions '{seen[cond]}' and '{label}' "
                    f"share the same condition '{cond}'",
                    loc,
                )
            else:
                seen[cond] = label

    # ------------------------------------------------------------------
    # Rule 6: CELL_DUPLICATE_TARGET
    # ------------------------------------------------------------------
    def _check_duplicate_target(self, loc, transitions):
        by_target = {}
        for t in transitions:
            target = (getattr(t, "target", "") or "").strip()
            if not target:
                continue
            label = getattr(t, "label", "") or "(no label)"
            by_target.setdefault(target, []).append(label)
        for target, labels in by_target.items():
            if len(labels) > 1:
                self._add(
                    "CELL_DUPLICATE_TARGET",
                    self.LEVEL_INFO,
                    f"Multiple transitions target '{target}': "
                    f"{', '.join(labels)}",
                    loc,
                )

    # ------------------------------------------------------------------
    # Rule 7: CELL_EXCLUSIVE_NO_RETURN
    # ------------------------------------------------------------------
    def _check_exclusive_no_return(self, loc, transitions, relations):
        by_label = {getattr(t, "label", "") or "": t for t in transitions}
        for r in relations:
            if r.kind != "exclusive":
                continue
            for m in (r.members or []):
                t = by_label.get(m)
                if t is None:
                    continue
                if not getattr(t, "early_return", False):
                    self._add(
                        "CELL_EXCLUSIVE_NO_RETURN",
                        self.LEVEL_INFO,
                        f"Exclusive member '{m}' does not have early_return=True",
                        loc,
                    )

    # ------------------------------------------------------------------
    # Rule 8: CELL_EMPTY_TARGET
    # ------------------------------------------------------------------
    def _check_empty_target(self, loc, transitions):
        for t in transitions:
            target = (getattr(t, "target", "") or "").strip()
            er = getattr(t, "early_return", False)
            cond = (getattr(t, "condition", "") or "").strip()
            if not target and not er and cond:
                label = getattr(t, "label", "") or "(no label)"
                self._add(
                    "CELL_EMPTY_TARGET",
                    self.LEVEL_WARNING,
                    f"Transition '{label}' has no target and no early_return",
                    loc,
                )

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------
    def _add(self, code: str, level: str, message: str, location: str):
        self.issues.append(Issue(
            code=code, level=level, message=message, location=location,
        ))