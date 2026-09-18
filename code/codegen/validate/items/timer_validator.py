# codegen/validate/items/timer_validator.py
"""
Timer検証
"""

import sys
import os
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from validate.logger import logger
from validate.models import ValidationIssue, ValidationSeverity, ValidationContext
from validate.data.validation_rules import VALIDATION_RULES
from validate.items.base_validator import BaseValidator


class TimerValidator(BaseValidator):
    """Timer検証クラス"""
    
    category = "timer"
    
    def __init__(self):
        logger.debug("TimerValidator.__init__ started")
        self.rules_data = VALIDATION_RULES.get(self.category, {})
        self.rules = {
            'TIMER_DUPLICATE_VARIABLE': self._check_duplicate_variables,
            'TIMER_INVALID_MULTIPLIER': self._check_invalid_multiplier,
        }
        logger.debug(f"TimerValidator.__init__ completed: {len(self.rules)} rules")
    
    def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug(f"TimerValidator.validate started")
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
    
    def _get_all_timer_variables(self, context):
        timer_vars = []
        timer_base = context.timer_base
        if timer_base:
            timer_vars.append(getattr(timer_base, 'variable_name', ''))
            for derived in getattr(timer_base, 'derived', []):
                timer_vars.append(getattr(derived, 'variable_name', ''))
        for timer in context.extra_timers:
            timer_vars.append(getattr(timer, 'variable_name', ''))
            for derived in getattr(timer, 'derived', []):
                timer_vars.append(getattr(derived, 'variable_name', ''))
        return timer_vars
    
    def _check_duplicate_variables(self, context):
        issues = []
        existing = set(getattr(v, 'name', '') for v in context.variables)
        timer_vars = self._get_all_timer_variables(context)
        seen = set()
        for var_name in timer_vars:
            if not var_name:
                continue
            if var_name in seen:
                issues.append(self._create_issue('TIMER_DUPLICATE_VARIABLE', name=var_name))
            elif var_name in existing:
                issues.append(self._create_issue('TIMER_DUPLICATE_VARIABLE', name=var_name))
            else:
                seen.add(var_name)
        return issues
    
    def _check_invalid_multiplier(self, context):
        issues = []
        timer_base = context.timer_base
        if timer_base:
            for derived in getattr(timer_base, 'derived', []):
                multiplier = getattr(derived, 'multiplier', 0)
                name = getattr(derived, 'variable_name', '')
                if multiplier <= 0:
                    issues.append(self._create_issue('TIMER_INVALID_MULTIPLIER', name=name))
        for timer in context.extra_timers:
            for derived in getattr(timer, 'derived', []):
                multiplier = getattr(derived, 'multiplier', 0)
                name = getattr(derived, 'variable_name', '')
                if multiplier <= 0:
                    issues.append(self._create_issue('TIMER_INVALID_MULTIPLIER', name=name))
        return issues