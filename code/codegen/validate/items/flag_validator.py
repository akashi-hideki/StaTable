# codegen/validate/items/flag_validator.py
"""\nFlag validation\n"""

import sys
import os
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ..logger import logger
from ..models import ValidationIssue, ValidationSeverity, ValidationContext
from ..data.validation_rules import VALIDATION_RULES
from .base_validator import BaseValidator


class FlagValidator(BaseValidator):
    """Flag validation class"""
    
    category = "flag"
    
    def __init__(self):
        logger.debug("FlagValidator.__init__ started")
        self.rules_data = VALIDATION_RULES.get(self.category, {})
        self.rules = {
            'FLAG_DUPLICATE_NAME': self._check_duplicate_names,
            'FLAG_INVALID_RANGE': self._check_invalid_range,
        }
        logger.debug(f"FlagValidator.__init__ completed: {len(self.rules)} rules")
    
    def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug(f"FlagValidator.validate started")
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
        for flag in context.flags:
            name = getattr(flag, 'name', '')
            if name in seen:
                issues.append(self._create_issue('FLAG_DUPLICATE_NAME', name=name))
            else:
                seen.add(name)
        return issues
    
    def _check_invalid_range(self, context):
        issues = []
        for flag in context.flags:
            min_value = getattr(flag, 'min_value', 0)
            max_value = getattr(flag, 'max_value', 0)
            name = getattr(flag, 'name', '')
            if min_value > max_value:
                issues.append(self._create_issue('FLAG_INVALID_RANGE', name=name))
        return issues