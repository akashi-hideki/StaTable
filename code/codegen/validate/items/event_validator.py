# codegen/validate/items/event_validator.py
"""
イベント検証
"""

import sys
import os
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from ..logger import logger
    from ..models import ValidationIssue, ValidationSeverity, ValidationContext
    from ..data.validation_rules import VALIDATION_RULES
    from .base_validator import BaseValidator
except ImportError:
    from logger import logger
    from models import ValidationIssue, ValidationSeverity, ValidationContext
    from data.validation_rules import VALIDATION_RULES
    from base_validator import BaseValidator


class EventValidator(BaseValidator):
    """イベント検証クラス"""
    
    category = "event"
    
    def __init__(self):
        logger.debug("EventValidator.__init__ started")
        self.rules_data = VALIDATION_RULES.get(self.category, {})
        self.rules = {
            'EVENT_UNUSED': self._check_unused_events,
            'EVENT_NO_TRANSITION': self._check_events_without_transitions,
        }
        logger.debug(f"EventValidator.__init__ completed: {len(self.rules)} rules")
    
    def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug(f"EventValidator.validate started: events={len(context.events)}")
        issues = []
        for code, rule_func in self.rules.items():
            logger.debug(f"Running rule: {code}")
            try:
                result = rule_func(context)
                if result:
                    issues.extend(result)
            except Exception as e:
                logger.error(f"Rule '{code}' failed: {e}", exc_info=True)
        logger.debug(f"EventValidator.validate completed: {len(issues)} issues")
        return issues
    
    def _create_issue(self, code: str, **kwargs) -> ValidationIssue:
        rule = self.rules_data.get(code, {})
        message = rule.get('message', '').format(**kwargs)
        severity_str = rule.get('severity', 'info')
        severity = ValidationSeverity.from_string(severity_str)
        suggestion = rule.get('suggestion', '')
        
        return ValidationIssue(
            category=self.category,
            code=code,
            message=message,
            severity=severity,
            suggestion=suggestion,
            target=kwargs.get('name', ''),
        )
    
    def _check_unused_events(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug("_check_unused_events started")
        issues = []
        used_events = set(t.event for t in context.transitions)
        
        for name in context.events.keys():
            if name not in used_events:
                logger.warning(f"Event '{name}' is unused")
                issues.append(self._create_issue('EVENT_UNUSED', name=name))
        
        logger.debug(f"_check_unused_events completed: {len(issues)} issues")
        return issues
    
    def _check_events_without_transitions(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug("_check_events_without_transitions started")
        issues = []
        
        for name in context.events.keys():
            has_transition = any(t.event == name for t in context.transitions)
            if not has_transition:
                logger.warning(f"Event '{name}' has no transitions")
                issues.append(self._create_issue('EVENT_NO_TRANSITION', name=name))
        
        logger.debug(f"_check_events_without_transitions completed: {len(issues)} issues")
        return issues