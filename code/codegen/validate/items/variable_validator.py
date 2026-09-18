# codegen/validate/items/variable_validator.py
"""\nVariable validation\n"""

import sys
import os
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from validate.logger import logger
from validate.models import ValidationIssue, ValidationSeverity, ValidationContext
from validate.data.validation_rules import VALIDATION_RULES
from validate.items.base_validator import BaseValidator


class VariableValidator(BaseValidator):
    """Variable validation class"""
    
    category = "variable"
    
    def __init__(self):
        logger.debug("VariableValidator.__init__ started")
        self.rules_data = VALIDATION_RULES.get(self.category, {})
        self.rules = {
            'VAR_DUPLICATE_NAME': self._check_duplicate_names,
            'VAR_INVALID_TYPE': self._check_invalid_type,
            'VAR_INVALID_ARRAY_SIZE': self._check_invalid_array_size,
        }
        logger.debug(f"VariableValidator.__init__ completed: {len(self.rules)} rules")
    
    def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug(f"VariableValidator.validate started")
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
        for var in context.variables:
            name = getattr(var, 'name', '')
            if name in seen:
                issues.append(self._create_issue('VAR_DUPLICATE_NAME', name=name))
            else:
                seen.add(name)
        return issues
    
    def _check_invalid_type(self, context):
        issues = []
        basic_types = {'int', 'int8', 'int16', 'int32', 'int64',
                      'uint', 'uint8', 'uint16', 'uint32', 'uint64',
                      'float', 'double', 'bool', 'char', 'string', 'void'}
        custom_type_names = {getattr(ct, 'name', '') for ct in context.custom_types}
        for var in context.variables:
            var_type = getattr(var, 'type', '')
            name = getattr(var, 'name', '')
            if var_type and var_type not in basic_types and var_type not in custom_type_names:
                issues.append(self._create_issue('VAR_INVALID_TYPE', name=name, type=var_type))
        return issues
    
    def _check_invalid_array_size(self, context):
        issues = []
        for var in context.variables:
            array_size = getattr(var, 'array_size', 0)
            name = getattr(var, 'name', '')
            if array_size < 0:
                issues.append(self._create_issue('VAR_INVALID_ARRAY_SIZE', name=name))
        return issues