# codegen/validate/items/role_function_validator.py
"""
Role function validation
"""

import sys
import os
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ..logger import logger
from ..models import ValidationIssue, ValidationSeverity, ValidationContext
from ..data.validation_rules import VALIDATION_RULES
from .base_validator import BaseValidator


class RoleFunctionValidator(BaseValidator):
    """Role function validator class"""
    
    category = "role_function"
    
    def __init__(self):
        logger.debug("RoleFunctionValidator.__init__ started")
        self.rules_data = VALIDATION_RULES.get(self.category, {})
        self.rules = {
            'ROLE_FUNC_NO_RETURN_TYPE': self._check_no_return_type,
            'ROLE_FUNC_ARG_MISMATCH': self._check_arg_mismatch,
            'ROLE_FUNC_UNUSED': self._check_unused_functions,
        }
        logger.debug(f"RoleFunctionValidator.__init__ completed: {len(self.rules)} rules")
    
    def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug(f"RoleFunctionValidator.validate started")
        issues = []
        for code, rule_func in self.rules.items():
            try:
                result = rule_func(context)
                if result:
                    issues.extend(result)
            except Exception as e:
                logger.error(f"Rule '{code}' failed: {e}", exc_info=True)
        return issues
    
    def _create_issue(self, code: str, **kwargs) -> ValidationIssue:
        rule = self.rules_data.get(code, {})
        message = rule.get('message', '').format(**kwargs)
        severity = ValidationSeverity.from_string(rule.get('severity', 'info'))
        return ValidationIssue(
            category=self.category,
            code=code,
            message=message,
            severity=severity,
            suggestion=rule.get('suggestion', ''),
            target=kwargs.get('name', ''),
        )
    
    def _check_no_return_type(self, context):
        issues = []
        for name, func in context.role_functions.items():
            return_type = getattr(func, 'return_type', '')
            if not return_type:
                issues.append(self._create_issue('ROLE_FUNC_NO_RETURN_TYPE', name=name))
        return issues
    
    def _check_arg_mismatch(self, context):
        issues = []
        for name, func in context.role_functions.items():
            arg1_type = getattr(func, 'arg1_type', '')
            arg1_name = getattr(func, 'arg1_name', '')
            arg2_type = getattr(func, 'arg2_type', '')
            arg2_name = getattr(func, 'arg2_name', '')
            if (arg1_type and not arg1_name) or (arg1_name and not arg1_type):
                issues.append(self._create_issue('ROLE_FUNC_ARG_MISMATCH', name=name))
            if (arg2_type and not arg2_name) or (arg2_name and not arg2_type):
                issues.append(self._create_issue('ROLE_FUNC_ARG_MISMATCH', name=name))
        return issues
    
    def _collect_referenced_names(self, context):
        """[v2.7.2 fix] Collect every name that references a role function.

        Sources:
          - Transition.action / .pre_actions / .else_actions
          - Transition.condition (parsed for RoleFunc_X / NS.Name)
          - State.entry / exit / do_actions
          - Cell actions (via state_machine.get_actions_for_cell)
          - Event.trigger_detail.caller
        """
        import re
        used = set()

        def add(ref):
            if not ref:
                return
            ref = str(ref).strip()
            if not ref:
                return
            used.add(ref)
            if '.' in ref:
                used.add(ref.split('.', 1)[1])

        def add_text(text):
            if not text:
                return
            text = str(text)
            # RoleFunc_<NS>_<Name> pattern
            for m in re.finditer(r'RoleFunc_(\w+)', text):
                used.add(m.group(0))
                used.add(m.group(1))
            # NS.Name pattern
            for m in re.finditer(r'([A-Z]\w*)\.([A-Za-z_]\w*)', text):
                used.add(f"{m.group(1)}.{m.group(2)}")
                used.add(m.group(2))

        # 1. Transitions
        for t in getattr(context, 'transitions', []) or []:
            add(getattr(t, 'action', ''))
            add_text(getattr(t, 'condition', ''))
            for a in (getattr(t, 'pre_actions', []) or []):
                add(a)
            for a in (getattr(t, 'else_actions', []) or []):
                add(a)

        # 2. Via state_machine (defensive)
        sm = (getattr(context, 'state_machine', None)
              or getattr(context, 'sm', None))
        if sm is not None:
            for state in (getattr(sm, 'states', {}) or {}).values():
                for attr in ('entry', 'exit', 'do_actions'):
                    for a in (getattr(state, attr, []) or []):
                        rf = getattr(a, 'role_function', None)
                        if rf:
                            add(rf)
                        elif isinstance(a, str):
                            add(a)
            for ev in (getattr(sm, 'events', {}) or {}).values():
                td = getattr(ev, 'trigger_detail', None)
                if td is not None:
                    add(getattr(td, 'caller', ''))
            try:
                for key in sm.get_cell_keys():
                    for a in sm.get_actions_for_cell(*key):
                        rf = getattr(a, 'role_function', None)
                        if rf:
                            add(rf)
            except Exception:
                pass

        # 3. Fallback: context.states
        for state in (getattr(context, 'states', {}) or {}).values():
            for attr in ('entry', 'exit', 'do_actions'):
                for a in (getattr(state, attr, []) or []):
                    rf = getattr(a, 'role_function', None)
                    if rf:
                        add(rf)
                    elif isinstance(a, str):
                        add(a)

        return used

    def _check_unused_functions(self, context):
        """[v2.7.2 fix] Match refs via bare / qualified / RoleFunc_ aliases."""
        issues = []
        used = self._collect_referenced_names(context)
        for name, func in context.role_functions.items():
            aliases = {name}
            ns = getattr(func, 'namespace', '') or ''
            if ns:
                aliases.add(f"{ns}.{name}")
                aliases.add(f"RoleFunc_{ns}_{name}")
            aliases.add(f"RoleFunc_{name}")
            if aliases & used:
                continue
            issues.append(self._create_issue('ROLE_FUNC_UNUSED', name=name))
        return issues