# codegen/validate/response_validator.py
"""
Response validator for AI proposals.

Validates the ChangeRequests produced by AIResponseParser before they
are handed to ChangeApplier. Matches SPEC_AI_PROMPT_v1.1 §6.

Four validation stages:

  Stage 1. Schema      - action is a known ChangeActionType,
                         params is dict, reason is non-empty.
  Stage 2. Action      - (parser already filters this; kept for
                         callers that bypass the parser)
  Stage 3. Parameters  - ACTION_DEFINITIONS required params present
                         and of the correct type.
  Stage 4. References  - source / target / event / role_function
                         refer to existing objects (per-action rules).

Invalid requests are moved to `invalid_requests` with a human-readable
reason. Non-fatal issues go into `warnings`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Set

from .logger import logger
from .change_actions import ChangeRequest, ChangeActionType
from .data.action_definitions import ACTION_DEFINITIONS


# ======================================================================
# Result container
# ======================================================================
@dataclass
class ResponseValidationResult:
    """Outcome of ResponseValidator.validate()."""
    valid_requests: List[ChangeRequest] = field(default_factory=list)
    invalid_requests: List[Tuple[ChangeRequest, str]] = field(
        default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.valid_requests) + len(self.invalid_requests)

    @property
    def ok(self) -> bool:
        return not self.invalid_requests


# ======================================================================
# Validator
# ======================================================================
class ResponseValidator:
    """Validate ChangeRequests against the current StateMachine."""

    def __init__(self):
        logger.debug("ResponseValidator.__init__ started")
        self.action_definitions = ACTION_DEFINITIONS
        logger.debug("ResponseValidator.__init__ completed")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def validate(
        self,
        requests: List[ChangeRequest],
        sm,
        gd=None,
    ) -> ResponseValidationResult:
        result = ResponseValidationResult()
        for req in requests or []:
            err = self._validate_one(req, sm, gd, result.warnings)
            if err is None:
                result.valid_requests.append(req)
            else:
                result.invalid_requests.append((req, err))
                logger.debug(
                    "ResponseValidator: rejected %s: %s",
                    getattr(req, 'action', '?'), err)
        return result

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------
    def _validate_one(self, req, sm, gd, warnings) -> Optional[str]:
        for check in (
            lambda: self._check_schema(req),
            lambda: self._check_params(req),
            lambda: self._check_references(req, sm),
        ):
            err = check()
            if err:
                return err
        self._collect_warnings(req, sm, warnings)
        return None

    # ------------------------------------------------------------------
    # Stage 1: Schema
    # ------------------------------------------------------------------
    def _check_schema(self, req) -> Optional[str]:
        if not isinstance(req, ChangeRequest):
            return "not a ChangeRequest"
        if not isinstance(req.action, ChangeActionType):
            return "action is not a ChangeActionType"
        if not isinstance(req.params, dict):
            return "params is not a dict"
        if not isinstance(req.reason, str) or not req.reason.strip():
            return "reason is empty"
        return None

    # ------------------------------------------------------------------
    # Stage 3: Parameters
    # ------------------------------------------------------------------
    def _check_params(self, req) -> Optional[str]:
        definition = self.action_definitions.get(req.action.value)
        if definition is None:
            return f"action '{req.action.value}' is not defined"
        params = definition.get('params', {})
        for pname, pinfo in params.items():
            required = bool(pinfo.get('required'))
            if pname not in req.params:
                if required:
                    return f"missing required param '{pname}'"
                continue
            value = req.params[pname]
            if required:
                if value is None:
                    return f"param '{pname}' is empty"
                if isinstance(value, str) and not value.strip():
                    return f"param '{pname}' is empty"
            err = self._check_param_type(pname, value, pinfo)
            if err:
                return err
        return None

    def _check_param_type(self, name, value, info) -> Optional[str]:
        t = info.get('type', 'str')
        if t == 'str':
            if not isinstance(value, str):
                return f"param '{name}' should be str"
        elif t == 'int':
            if isinstance(value, bool):
                return f"param '{name}' should be int"
            try:
                int(value)
            except (TypeError, ValueError):
                return f"param '{name}' should be int"
        elif t == 'bool':
            if not isinstance(value, bool):
                return f"param '{name}' should be bool"
        elif t == 'list':
            if not isinstance(value, list):
                return f"param '{name}' should be list"
        elif t == 'enum':
            values = info.get('values', [])
            if value not in values:
                joined = ", ".join(str(v) for v in values)
                return f"param '{name}' must be one of {joined}"
        return None

    # ------------------------------------------------------------------
    # Stage 4: References
    # ------------------------------------------------------------------
    def _check_references(self, req, sm) -> Optional[str]:
        if sm is None:
            return None
        a = req.action
        p = req.params
        if a == ChangeActionType.ADD_TRANSITION:
            return self._ref_add_transition(p, sm)
        if a == ChangeActionType.REMOVE_TRANSITION:
            return self._ref_remove_transition(p, sm)
        if a == ChangeActionType.SET_INITIAL:
            return self._ref_set_initial(p, sm)
        if a == ChangeActionType.ADD_ACTION_STEP:
            return self._ref_add_action_step(p, sm)
        if a == ChangeActionType.ADD_TRANSITION_RELATION:
            return self._ref_add_transition_relation(p, sm)
        # [extension] cell-level checks beyond SPEC §6.3, harmless
        if a == ChangeActionType.SET_EARLY_RETURN:
            return self._ref_set_early_return(p, sm)
        return None

    def _ref_add_transition(self, p, sm) -> Optional[str]:
        source = p.get('source', '')
        event = p.get('event', '')
        if source not in sm.states:
            return f"source state '{source}' does not exist"
        if event not in sm.events:
            return f"event '{event}' does not exist"
        return None

    def _ref_remove_transition(self, p, sm) -> Optional[str]:
        source = p.get('source', '')
        event = p.get('event', '')
        target = p.get('target', '')
        for t in sm.transitions:
            if t.source == source and t.event == event \
                    and t.target == target:
                return None
        return (
            f"transition {source} --[{event}]--> {target} "
            "does not exist"
        )

    def _ref_set_initial(self, p, sm) -> Optional[str]:
        state = p.get('state', '')
        if state not in sm.states:
            return f"state '{state}' does not exist"
        return None

    def _ref_add_action_step(self, p, sm) -> Optional[str]:
        rf = p.get('role_function', '')
        if not self._role_function_exists(rf, sm):
            return f"role function '{rf}' does not exist"
        return None

    def _ref_add_transition_relation(self, p, sm) -> Optional[str]:
        source = p.get('source', '')
        event = p.get('event', '')
        members = p.get('members', []) or []
        labels = self._cell_labels(sm, source, event)
        for m in members:
            if m not in labels:
                return (
                    f"label '{m}' not found in cell ({source}, {event})"
                )
        return None

    def _ref_set_early_return(self, p, sm) -> Optional[str]:
        source = p.get('source', '')
        event = p.get('event', '')
        label = p.get('label', '')
        labels = self._cell_labels(sm, source, event)
        if label not in labels:
            return f"label '{label}' not found in ({source}, {event})"
        return None

    # ------------------------------------------------------------------
    # Warnings (non-blocking)
    # ------------------------------------------------------------------
    def _collect_warnings(self, req, sm, warnings):
        if req.confidence < 0.5:
            ident = req.id or req.action.value
            warnings.append(
                f"{ident}: low confidence ({req.confidence:.2f})"
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _role_function_exists(self, name: str, sm) -> bool:
        if not name:
            return False
        if name in sm.role_functions:
            return True
        for rf in sm.role_functions.values():
            if getattr(rf, 'qualified_name', '') == name:
                return True
        return False

    def _cell_labels(self, sm, source: str, event: str) -> Set[str]:
        labels: Set[str] = set()
        try:
            transitions = sm.get_transitions_for_cell(source, event)
        except AttributeError:
            return labels
        for t in transitions or []:
            label = getattr(t, 'label', '')
            if label:
                labels.add(label)
        return labels