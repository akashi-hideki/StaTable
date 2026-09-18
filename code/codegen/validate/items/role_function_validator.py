# codegen/validate/items/role_function_validator.py
"""
Role function検証
"""

import sys
import os
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from validate.logger import logger
from validate.models import ValidationIssue, ValidationSeverity, ValidationContext
from validate.data.validation_rules import VALIDATION_RULES
from validate.items.base_validator import BaseValidator


class RoleFunctionValidator(BaseValidator):
    """Role function検証クラス"""
    
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
    
    def _check_unused_functions(self, context):
        issues = []
        used = set()
        for t in context.transitions:
            if getattr(t, 'action', ''):
                used.add(t.action)
            if getattr(t, 'condition', ''):
                used.add(t.condition)
        for name in context.role_functions.keys():
            if name not in used:
                issues.append(self._create_issue('ROLE_FUNC_UNUSED', name=name))
        return issues