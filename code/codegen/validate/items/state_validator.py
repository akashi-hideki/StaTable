# codegen/validate/items/state_validator.py
"""\nState validation\n"""

import sys
import os
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from validate.logger import logger
from validate.models import ValidationIssue, ValidationSeverity, ValidationContext
from validate.data.validation_rules import VALIDATION_RULES
from validate.items.base_validator import BaseValidator


class StateValidator(BaseValidator):
    """State validation class"""
    
    category = "state"
    
    def __init__(self):
        logger.debug("StateValidator.__init__ started")
        self.rules_data = VALIDATION_RULES.get(self.category, {})
        self.rules = {
            'STATE_NO_INITIAL': self._check_initial_state,
            'STATE_UNREACHABLE': self._check_unreachable_states,
            'STATE_NO_TRANSITION': self._check_no_transition_states,
            'STATE_DUPLICATE': self._check_duplicate_states,
        }
        logger.debug(f"StateValidator.__init__ completed: {len(self.rules)} rules")
    
    def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug(f"StateValidator.validate started")
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
    
    def _check_initial_state(self, context):
        if context.initial_state is None:
            return [self._create_issue('STATE_NO_INITIAL')]
        return []
    
    def _check_unreachable_states(self, context):
        issues = []
        reachable = set(t.target for t in context.transitions if t.target)
        for name in context.states.keys():
            if name not in reachable and name != context.initial_state:
                issues.append(self._create_issue('STATE_UNREACHABLE', name=name))
        return issues
    
    def _check_no_transition_states(self, context):
        issues = []
        sources = set(t.source for t in context.transitions)
        for name in context.states.keys():
            if name not in sources:
                issues.append(self._create_issue('STATE_NO_TRANSITION', name=name))
        return issues
    
    def _check_duplicate_states(self, context):
        issues = []
        lower_names = {}
        for name in context.states.keys():
            lower = name.lower()
            if lower in lower_names:
                issues.append(self._create_issue('STATE_DUPLICATE', name=name, other=lower_names[lower]))
            else:
                lower_names[lower] = name
        return issues