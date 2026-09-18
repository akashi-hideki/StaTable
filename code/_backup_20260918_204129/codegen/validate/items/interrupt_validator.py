# codegen/validate/items/interrupt_validator.py
"""
割り込み検証
"""

import sys
import os
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from validate.logger import logger
from validate.models import ValidationIssue, ValidationSeverity, ValidationContext
from validate.data.validation_rules import VALIDATION_RULES
from validate.items.base_validator import BaseValidator


class InterruptValidator(BaseValidator):
    """割り込み検証クラス"""
    
    category = "interrupt"
    
    def __init__(self):
        logger.debug("InterruptValidator.__init__ started")
        self.rules_data = VALIDATION_RULES.get(self.category, {})
        self.rules = {
            'INTERRUPT_DUPLICATE_NAME': self._check_duplicate_names,
            'INTERRUPT_UNDEFINED_EVENT': self._check_undefined_event,
        }
        logger.debug(f"InterruptValidator.__init__ completed: {len(self.rules)} rules")
    
    def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug(f"InterruptValidator.validate started")
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
    
    def _check_duplicate_names(self, context):
        issues = []
        seen = set()
        for interrupt in context.interrupts:
            name = getattr(interrupt, 'name', '')
            if name in seen:
                issues.append(self._create_issue('INTERRUPT_DUPLICATE_NAME', name=name))
            else:
                seen.add(name)
        return issues
    
    def _check_undefined_event(self, context):
        issues = []
        event_names = set(context.events.keys())
        for interrupt in context.interrupts:
            event_list = getattr(interrupt, 'event_names', [])
            name = getattr(interrupt, 'name', '')
            for event_name in event_list:
                if event_name and event_name not in event_names:
                    issues.append(self._create_issue('INTERRUPT_UNDEFINED_EVENT', name=name))
        return issues