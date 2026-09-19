# codegen/validate/items/cell_validator.py
"""Cell-level validator (v2.2) - integrated into the validate layer.

Rules:
  CELL_EMPTY_CONDITION        (Warning) condition empty AND target empty
  CELL_DUPLICATE_LABEL        (Error)   same label within one cell
  CELL_DANGLING_RELATION      (Error)   relation members referencing missing labels
  CELL_UNREACHABLE_TRANSITION (Warning) transition after a Commit+else
  CELL_OVERLAP_POSSIBLE       (Warning) duplicate condition strings in one cell
  CELL_DUPLICATE_TARGET       (Info)    multiple transitions targeting the same state
  CELL_EXCLUSIVE_NO_RETURN    (Info)    exclusive member without early_return
  CELL_EMPTY_TARGET           (Warning) target empty AND early_return False
"""

import logging
from typing import List

from ..models import (
    ValidationIssue, ValidationSeverity, ValidationContext,
)
from ..data.validation_rules import VALIDATION_RULES
from .base_validator import BaseValidator

logger = logging.getLogger("validate.cell_validator")


class CellValidator(BaseValidator):
    """Validates each (source, event) cell of a StateMachine."""

    category = "cell"

    def __init__(self):
        self.rules_data = VALIDATION_RULES.get(self.category, {})
        self.rules = {
            "CELL_EMPTY_CONDITION":        self._rule_empty_condition,
            "CELL_DUPLICATE_LABEL":        self._rule_duplicate_label,
            "CELL_DANGLING_RELATION":      self._rule_dangling_relation,
            "CELL_UNREACHABLE_TRANSITION": self._rule_unreachable,
            "CELL_OVERLAP_POSSIBLE":       self._rule_overlap,
            "CELL_DUPLICATE_TARGET":       self._rule_duplicate_target,
            "CELL_EXCLUSIVE_NO_RETURN":    self._rule_exclusive_no_return,
            "CELL_EMPTY_TARGET":           self._rule_empty_target,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _severity(self, code: str) -> ValidationSeverity:
        rule = self.rules_data.get(code, {})
        return ValidationSeverity.from_string(rule.get("severity", "info"))

    def _make_issue(self, code: str, message: str,
                    target: str = "") -> ValidationIssue:
        return ValidationIssue(
            category=self.category,
            code=code,
            message=message,
            severity=self._severity(code),
            target=target,
        )

    def _iter_cells(self, context: ValidationContext):
        """Return all (source, event) keys that have transitions or relations."""
        sm = context.state_machine
        if sm is None:
            return []
        keys = set()
        for t in sm.transitions:
            keys.add((t.source, t.event or ""))
        for (s, e) in sm.get_cell_keys():
            keys.add((s, e))
        return sorted(keys)

    def _loc(self, source: str, event: str) -> str:
        return f"{source}/{event or 'Completion'}"

    # ------------------------------------------------------------------
    # Rule 1: CELL_EMPTY_CONDITION
    # ------------------------------------------------------------------
    def _rule_empty_condition(self, context) -> List[ValidationIssue]:
        sm = context.state_machine
        if sm is None:
            return []
        issues = []
        for (source, event) in self._iter_cells(context):
            for t in sm.get_transitions_for_cell(source, event):
                cond = (getattr(t, "condition", "") or "").strip()
                target = (getattr(t, "target", "") or "").strip()
                if not cond and not target:
                    label = getattr(t, "label", "") or "(no label)"
                    issues.append(self._make_issue(
                        "CELL_EMPTY_CONDITION",
                        f"Transition '{label}' has no condition and no target",
                        self._loc(source, event),
                    ))
        return issues

    # ------------------------------------------------------------------
    # Rule 2: CELL_DUPLICATE_LABEL
    # ------------------------------------------------------------------
    def _rule_duplicate_label(self, context) -> List[ValidationIssue]:
        sm = context.state_machine
        if sm is None:
            return []
        issues = []
        for (source, event) in self._iter_cells(context):
            seen = set()
            for t in sm.get_transitions_for_cell(source, event):
                label = getattr(t, "label", "") or ""
                if not label:
                    continue
                if label in seen:
                    issues.append(self._make_issue(
                        "CELL_DUPLICATE_LABEL",
                        f"Duplicate transition label '{label}'",
                        self._loc(source, event),
                    ))
                else:
                    seen.add(label)
        return issues

    # ------------------------------------------------------------------
    # Rule 3: CELL_DANGLING_RELATION
    # ------------------------------------------------------------------
    def _rule_dangling_relation(self, context) -> List[ValidationIssue]:
        sm = context.state_machine
        if sm is None:
            return []
        issues = []
        for (source, event) in self._iter_cells(context):
            transitions = sm.get_transitions_for_cell(source, event)
            relations = sm.get_relations_for_cell(source, event)
            if not relations:
                continue
            valid = {getattr(t, "label", "") or "" for t in transitions}
            valid.discard("")
            for r in relations:
                for m in (r.members or []):
                    if m not in valid:
                        issues.append(self._make_issue(
                            "CELL_DANGLING_RELATION",
                            f"Relation references missing label '{m}'",
                            self._loc(source, event),
                        ))
        return issues

    # ------------------------------------------------------------------
    # Rule 4: CELL_UNREACHABLE_TRANSITION
    # ------------------------------------------------------------------
    def _rule_unreachable(self, context) -> List[ValidationIssue]:
        sm = context.state_machine
        if sm is None:
            return []
        issues = []
        for (source, event) in self._iter_cells(context):
            blocker = False
            for t in sm.get_transitions_for_cell(source, event):
                label = getattr(t, "label", "") or "(no label)"
                if blocker:
                    issues.append(self._make_issue(
                        "CELL_UNREACHABLE_TRANSITION",
                        f"Transition '{label}' is unreachable "
                        f"(a prior Commit transition always fires)",
                        self._loc(source, event),
                    ))
                    continue
                er = getattr(t, "early_return", False)
                cond = (getattr(t, "condition", "") or "").strip()
                has_else = getattr(t, "has_else", True)
                if er and (not cond or has_else):
                    blocker = True
        return issues

    # ------------------------------------------------------------------
    # Rule 5: CELL_OVERLAP_POSSIBLE
    # ------------------------------------------------------------------
    def _rule_overlap(self, context) -> List[ValidationIssue]:
        sm = context.state_machine
        if sm is None:
            return []
        issues = []
        for (source, event) in self._iter_cells(context):
            seen = {}
            for t in sm.get_transitions_for_cell(source, event):
                cond = (getattr(t, "condition", "") or "").strip()
                if not cond:
                    continue
                label = getattr(t, "label", "") or "(no label)"
                if cond in seen:
                    issues.append(self._make_issue(
                        "CELL_OVERLAP_POSSIBLE",
                        f"Transitions '{seen[cond]}' and '{label}' "
                        f"share the same condition '{cond}'",
                        self._loc(source, event),
                    ))
                else:
                    seen[cond] = label
        return issues

    # ------------------------------------------------------------------
    # Rule 6: CELL_DUPLICATE_TARGET
    # ------------------------------------------------------------------
    def _rule_duplicate_target(self, context) -> List[ValidationIssue]:
        sm = context.state_machine
        if sm is None:
            return []
        issues = []
        for (source, event) in self._iter_cells(context):
            by_target = {}
            for t in sm.get_transitions_for_cell(source, event):
                target = (getattr(t, "target", "") or "").strip()
                if not target:
                    continue
                label = getattr(t, "label", "") or "(no label)"
                by_target.setdefault(target, []).append(label)
            for target, labels in by_target.items():
                if len(labels) > 1:
                    issues.append(self._make_issue(
                        "CELL_DUPLICATE_TARGET",
                        f"Multiple transitions target '{target}': "
                        f"{', '.join(labels)}",
                        self._loc(source, event),
                    ))
        return issues

    # ------------------------------------------------------------------
    # Rule 7: CELL_EXCLUSIVE_NO_RETURN
    # ------------------------------------------------------------------
    def _rule_exclusive_no_return(self, context) -> List[ValidationIssue]:
        sm = context.state_machine
        if sm is None:
            return []
        issues = []
        for (source, event) in self._iter_cells(context):
            transitions = sm.get_transitions_for_cell(source, event)
            relations = sm.get_relations_for_cell(source, event)
            by_label = {getattr(t, "label", "") or "": t for t in transitions}
            for r in relations:
                if r.kind != "exclusive":
                    continue
                for m in (r.members or []):
                    t = by_label.get(m)
                    if t is None:
                        continue
                    if not getattr(t, "early_return", False):
                        issues.append(self._make_issue(
                            "CELL_EXCLUSIVE_NO_RETURN",
                            f"Exclusive member '{m}' does not have "
                            f"early_return=True",
                            self._loc(source, event),
                        ))
        return issues

    # ------------------------------------------------------------------
    # Rule 8: CELL_EMPTY_TARGET
    # ------------------------------------------------------------------
    def _rule_empty_target(self, context) -> List[ValidationIssue]:
        sm = context.state_machine
        if sm is None:
            return []
        issues = []
        for (source, event) in self._iter_cells(context):
            for t in sm.get_transitions_for_cell(source, event):
                target = (getattr(t, "target", "") or "").strip()
                er = getattr(t, "early_return", False)
                cond = (getattr(t, "condition", "") or "").strip()
                if not target and not er and cond:
                    label = getattr(t, "label", "") or "(no label)"
                    issues.append(self._make_issue(
                        "CELL_EMPTY_TARGET",
                        f"Transition '{label}' has no target "
                        f"and no early_return",
                        self._loc(source, event),
                    ))
        return issues