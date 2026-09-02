# codegen/validate/items/transition_validator.py
"""
遷移検証
"""

import sys
import os
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from validate.logger import logger
from validate.models import ValidationIssue, ValidationSeverity, ValidationContext
from validate.data.validation_rules import VALIDATION_RULES
from validate.items.base_validator import BaseValidator


class TransitionValidator(BaseValidator):
    """遷移検証クラス"""
    
    category = "transition"
    
    def __init__(self):
        self.rules_data = VALIDATION_RULES.get(self.category, {})
        self.rules = {
            'TRANSITION_TARGET_UNDEFINED': self._check_target_undefined,
            'TRANSITION_EVENT_UNDEFINED': self._check_event_undefined,
            'TRANSITION_SOURCE_UNDEFINED': self._check_source_undefined,
            'TRANSITION_DUPLICATE': self._check_duplicate_transitions,
            'TRANSITION_SELF_LOOP': self._check_self_loops,
        }
    
    def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        issues = []
        for code, rule_func in self.rules.items():
            result = rule_func(context)
            if result:
                issues.extend(result)
        return issues
    
    def _create_issue(self, code: str, **kwargs) -> ValidationIssue:
        rule = self.rules_data.get(code, {})
        message = rule.get('message', '').format(**kwargs)
        severity = ValidationSeverity.from_string(rule.get('severity', 'info'))
        
        target = kwargs.get('target', '') or kwargs.get('source', '') or kwargs.get('event', '')
        
        return ValidationIssue(
            category=self.category,
            code=code,
            message=message,
            severity=severity,
            suggestion=rule.get('suggestion', ''),
            target=target,
        )
    
    def _check_target_undefined(self, context):
        issues = []
        state_names = set(context.states.keys())
        for t in context.transitions:
            if t.target and t.target not in state_names:
                issues.append(self._create_issue('TRANSITION_TARGET_UNDEFINED', target=t.target))
        return issues
    
    def _check_event_undefined(self, context):
        issues = []
        event_names = set(context.events.keys())
        for t in context.transitions:
            if t.event and t.event not in event_names:
                issues.append(self._create_issue('TRANSITION_EVENT_UNDEFINED', event=t.event))
        return issues
    
    def _check_source_undefined(self, context):
        issues = []
        state_names = set(context.states.keys())
        for t in context.transitions:
            if t.source not in state_names:
                issues.append(self._create_issue('TRANSITION_SOURCE_UNDEFINED', source=t.source))
        return issues
    
    def _check_duplicate_transitions(self, context):
        issues = []
        seen = set()
        for t in context.transitions:
            key = (t.source, t.event, t.target)
            if key in seen:
                issues.append(self._create_issue(
                    'TRANSITION_DUPLICATE', source=t.source, event=t.event, target=t.target
                ))
            else:
                seen.add(key)
        return issues
    
    def _check_self_loops(self, context):
        issues = []
        for t in context.transitions:
            if t.source == t.target:
                issues.append(self._create_issue(
                    'TRANSITION_SELF_LOOP', source=t.source, event=t.event
                ))
        return issues