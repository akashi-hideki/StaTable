# codegen/validate/items/state_validator.py
"""
状態検証
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


class StateValidator(BaseValidator):
    """状態検証クラス"""
    
    category = "state"
    
    def __init__(self):
        logger.debug("StateValidator.__init__ started")
        self.rules_data = VALIDATION_RULES.get(self.category, {})
        self.rules = {
            'STATE_NO_INITIAL': self._check_initial_state,
            'STATE_UNREACHABLE': self._check_unreachable_states,
            'STATE_NO_TRANSITION': self._check_no_transition_states,
            'STATE_DUPLICATE': self._check_duplicate_states,
        }
        logger.debug(f"StateValidator.__init__ completed: {len(self.rules)} rules")
    
    def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug(f"StateValidator.validate started: states={len(context.states)}")
        issues = []
        for code, rule_func in self.rules.items():
            logger.debug(f"Running rule: {code}")
            try:
                result = rule_func(context)
                if result:
                    logger.debug(f"Rule '{code}' found {len(result)} issues")
                    issues.extend(result)
            except Exception as e:
                logger.error(f"Rule '{code}' failed: {e}", exc_info=True)
        logger.debug(f"StateValidator.validate completed: {len(issues)} issues")
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
    
    def _check_initial_state(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug(f"_check_initial_state: initial_state={context.initial_state}")
        if context.initial_state is None:
            logger.warning("Initial state is not set")
            return [self._create_issue('STATE_NO_INITIAL')]
        logger.debug("Initial state is set")
        return []
    
    def _check_unreachable_states(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug("_check_unreachable_states started")
        issues = []
        reachable = set()
        for t in context.transitions:
            if t.target:
                reachable.add(t.target)
        
        for name in context.states.keys():
            if name not in reachable and name != context.initial_state:
                logger.warning(f"State '{name}' is unreachable")
                issues.append(self._create_issue('STATE_UNREACHABLE', name=name))
        
        logger.debug(f"_check_unreachable_states completed: {len(issues)} issues")
        return issues
    
    def _check_no_transition_states(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug("_check_no_transition_states started")
        issues = []
        sources = set(t.source for t in context.transitions)
        
        for name in context.states.keys():
            if name not in sources:
                logger.warning(f"State '{name}' has no outgoing transitions")
                issues.append(self._create_issue('STATE_NO_TRANSITION', name=name))
        
        logger.debug(f"_check_no_transition_states completed: {len(issues)} issues")
        return issues
    
    def _check_duplicate_states(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug("_check_duplicate_states started")
        issues = []
        lower_names = {}
        
        for name in context.states.keys():
            lower = name.lower()
            if lower in lower_names:
                logger.warning(f"Duplicate state: '{name}' vs '{lower_names[lower]}'")
                issues.append(self._create_issue('STATE_DUPLICATE', name=name, other=lower_names[lower]))
            else:
                lower_names[lower] = name
        
        logger.debug(f"_check_duplicate_states completed: {len(issues)} issues")
        return issues