# codegen/validate/items/variable_validator.py
"""\nVariable validation\n"""

import sys
import os
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ..logger import logger
from ..models import ValidationIssue, ValidationSeverity, ValidationContext
from ..data.validation_rules import VALIDATION_RULES
from .base_validator import BaseValidator


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
        """[v2.7.2 fix] Accept stdint.h types and strip qualifiers.

        Previous behavior:
          - 'uint32_t' / 'uint8_t' were flagged (only legacy aliases
            'uint32' / 'uint8' were in the set)
          - 'volatile uint32_t' was flagged
        """
        issues = []
        basic_types = {
            # Plain C
            'int', 'short', 'long', 'unsigned', 'signed',
            'float', 'double', 'bool', 'char', 'string', 'void',
            # stdint.h (C99)
            'int8_t', 'int16_t', 'int32_t', 'int64_t',
            'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t',
            'intptr_t', 'uintptr_t', 'size_t',
            # Legacy aliases (without _t)
            'int8', 'int16', 'int32', 'int64',
            'uint', 'uint8', 'uint16', 'uint32', 'uint64',
        }
        qualifiers = {
            'volatile', 'const', 'static', 'register',
            'extern', 'inline', 'unsigned', 'signed',
            'long', 'short',
        }

        def normalize(t: str) -> str:
            parts = (t or '').strip().split()
            base = [p for p in parts if p not in qualifiers]
            return ' '.join(base) if base else (t or '').strip()

        def strip_extras(t: str) -> str:
            t = t.rstrip('*').strip()
            t = t.split('[')[0].strip()
            return t

        custom_type_names = {
            getattr(ct, 'name', '') for ct in context.custom_types
        }
        for var in context.variables:
            var_type = getattr(var, 'type', '') or ''
            name = getattr(var, 'name', '')
            if not var_type:
                continue
            normalized = normalize(var_type)
            candidates = {
                var_type, normalized,
                strip_extras(var_type), strip_extras(normalized),
            }
            if candidates & basic_types:
                continue
            if candidates & custom_type_names:
                continue
            issues.append(self._create_issue(
                'VAR_INVALID_TYPE', name=name, type=var_type))
        return issues
    
    def _check_invalid_array_size(self, context):
        issues = []
        for var in context.variables:
            array_size = getattr(var, 'array_size', 0)
            name = getattr(var, 'name', '')
            if array_size < 0:
                issues.append(self._create_issue('VAR_INVALID_ARRAY_SIZE', name=name))
        return issues