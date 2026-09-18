# codegen/validate/items/queue_validator.py
"""
キュー検証
"""

import sys
import os
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from validate.logger import logger
from validate.models import ValidationIssue, ValidationSeverity, ValidationContext
from validate.data.validation_rules import VALIDATION_RULES
from validate.items.base_validator import BaseValidator


class QueueValidator(BaseValidator):
    """キュー検証クラス"""
    
    category = "queue"
    
    def __init__(self):
        logger.debug("QueueValidator.__init__ started")
        self.rules_data = VALIDATION_RULES.get(self.category, {})
        self.rules = {
            'QUEUE_INVALID_SIZE': self._check_invalid_size,
            'QUEUE_UNDEFINED_EVENT': self._check_undefined_event,
        }
        logger.debug(f"QueueValidator.__init__ completed: {len(self.rules)} rules")
    
    def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug(f"QueueValidator.validate started")
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
    
    def _check_invalid_size(self, context):
        issues = []
        for queue in context.event_queues:
            size = getattr(queue, 'size', 0)
            name = getattr(queue, 'name', '')
            if size <= 0:
                issues.append(self._create_issue('QUEUE_INVALID_SIZE', name=name))
        return issues
    
    def _check_undefined_event(self, context):
        issues = []
        event_names = set(context.events.keys())
        for queue in context.event_queues:
            event_ids = getattr(queue, 'event_ids', [])
            name = getattr(queue, 'name', '')
            for event_id in event_ids:
                if event_id not in event_names:
                    issues.append(self._create_issue('QUEUE_UNDEFINED_EVENT', name=name))
        return issues