# codegen/validate/items/event_validator.py
"""
イベント検証
"""

import sys
import os
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from validate.logger import logger
from validate.models import ValidationIssue, ValidationSeverity, ValidationContext
from validate.data.validation_rules import VALIDATION_RULES
from validate.items.base_validator import BaseValidator


class EventValidator(BaseValidator):
    """イベント検証クラス"""
    
    category = "event"
    
    def __init__(self):
        self.rules_data = VALIDATION_RULES.get(self.category, {})
        self.rules = {
            'EVENT_UNUSED': self._check_unused_events,
            'EVENT_NO_TRANSITION': self._check_events_without_transitions,
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
        
        return ValidationIssue(
            category=self.category,
            code=code,
            message=message,
            severity=severity,
            suggestion=rule.get('suggestion', ''),
            target=kwargs.get('name', ''),
        )
    
    def _check_unused_events(self, context):
        issues = []
        used_events = set(t.event for t in context.transitions)
        for name in context.events.keys():
            if name not in used_events:
                issues.append(self._create_issue('EVENT_UNUSED', name=name))
        return issues
    
    def _check_events_without_transitions(self, context):
        issues = []
        for name in context.events.keys():
            has_transition = any(t.event == name for t in context.transitions)
            if not has_transition:
                issues.append(self._create_issue('EVENT_NO_TRANSITION', name=name))
        return issues