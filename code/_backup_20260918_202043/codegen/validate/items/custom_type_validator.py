# codegen/validate/items/custom_type_validator.py
"""
カスタム型検証
"""

import sys
import os
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from validate.logger import logger
from validate.models import ValidationIssue, ValidationSeverity, ValidationContext
from validate.data.validation_rules import VALIDATION_RULES
from validate.items.base_validator import BaseValidator


class CustomTypeValidator(BaseValidator):
    """カスタム型検証クラス"""
    
    category = "custom_type"
    
    def __init__(self):
        logger.debug("CustomTypeValidator.__init__ started")
        self.rules_data = VALIDATION_RULES.get(self.category, {})
        self.rules = {
            'TYPE_DUPLICATE_NAME': self._check_duplicate_names,
            'TYPE_NO_MEMBERS': self._check_no_members,
        }
        logger.debug(f"CustomTypeValidator.__init__ completed: {len(self.rules)} rules")
    
    def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug(f"CustomTypeValidator.validate started")
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
        for custom_type in context.custom_types:
            name = getattr(custom_type, 'name', '')
            if name in seen:
                issues.append(self._create_issue('TYPE_DUPLICATE_NAME', name=name))
            else:
                seen.add(name)
        return issues
    
    def _check_no_members(self, context):
        issues = []
        for custom_type in context.custom_types:
            members = getattr(custom_type, 'members', [])
            name = getattr(custom_type, 'name', '')
            if not members:
                issues.append(self._create_issue('TYPE_NO_MEMBERS', name=name))
        return issues