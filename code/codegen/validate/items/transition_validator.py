# codegen/validate/items/transition_validator.py
"""
遷移検証
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


class TransitionValidator(BaseValidator):
    """遷移検証クラス"""
    
    category = "transition"
    
    def __init__(self):
        logger.debug("TransitionValidator.__init__ started")
        self.rules_data = VALIDATION_RULES.get(self.category, {})
        self.rules = {
            'TRANSITION_TARGET_UNDEFINED': self._check_target_undefined,
            'TRANSITION_EVENT_UNDEFINED': self._check_event_undefined,
            'TRANSITION_SOURCE_UNDEFINED': self._check_source_undefined,
            'TRANSITION_DUPLICATE': self._check_duplicate_transitions,
            'TRANSITION_SELF_LOOP': self._check_self_loops,
        }
        logger.debug(f"TransitionValidator.__init__ completed: {len(self.rules)} rules")
    
    def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug(f"TransitionValidator.validate started: transitions={len(context.transitions)}")
        issues = []
        for code, rule_func in self.rules.items():
            logger.debug(f"Running rule: {code}")
            try:
                result = rule_func(context)
                if result:
                    issues.extend(result)
            except Exception as e:
                logger.error(f"Rule '{code}' failed: {e}", exc_info=True)
        logger.debug(f"TransitionValidator.validate completed: {len(issues)} issues")
        return issues
    
    def _create_issue(self, code: str, **kwargs) -> ValidationIssue:
        rule = self.rules_data.get(code, {})
        message = rule.get('message', '').format(**kwargs)
        severity_str = rule.get('severity', 'info')
        severity = ValidationSeverity.from_string(severity_str)
        suggestion = rule.get('suggestion', '')
        
        target = kwargs.get('target', '') or kwargs.get('source', '') or kwargs.get('event', '')
        
        return ValidationIssue(
            category=self.category,
            code=code,
            message=message,
            severity=severity,
            suggestion=suggestion,
            target=target,
        )
    
    def _check_target_undefined(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug("_check_target_undefined started")
        issues = []
        state_names = set(context.states.keys())
        
        for t in context.transitions:
            if t.target and t.target not in state_names:
                logger.warning(f"Transition target '{t.target}' is undefined")
                issues.append(self._create_issue('TRANSITION_TARGET_UNDEFINED', target=t.target))
        
        logger.debug(f"_check_target_undefined completed: {len(issues)} issues")
        return issues
    
    def _check_event_undefined(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug("_check_event_undefined started")
        issues = []
        event_names = set(context.events.keys())
        
        for t in context.transitions:
            if t.event and t.event not in event_names:
                logger.warning(f"Transition event '{t.event}' is undefined")
                issues.append(self._create_issue('TRANSITION_EVENT_UNDEFINED', event=t.event))
        
        logger.debug(f"_check_event_undefined completed: {len(issues)} issues")
        return issues
    
    def _check_source_undefined(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug("_check_source_undefined started")
        issues = []
        state_names = set(context.states.keys())
        
        for t in context.transitions:
            if t.source not in state_names:
                logger.warning(f"Transition source '{t.source}' is undefined")
                issues.append(self._create_issue('TRANSITION_SOURCE_UNDEFINED', source=t.source))
        
        logger.debug(f"_check_source_undefined completed: {len(issues)} issues")
        return issues
    
    def _check_duplicate_transitions(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug("_check_duplicate_transitions started")
        issues = []
        seen = set()
        
        for t in context.transitions:
            key = (t.source, t.event, t.target)
            if key in seen:
                logger.warning(f"Duplicate transition: {t.source} --[{t.event}]--> {t.target}")
                issues.append(self._create_issue(
                    'TRANSITION_DUPLICATE', source=t.source, event=t.event, target=t.target
                ))
            else:
                seen.add(key)
        
        logger.debug(f"_check_duplicate_transitions completed: {len(issues)} issues")
        return issues
    
    def _check_self_loops(self, context: ValidationContext) -> List[ValidationIssue]:
        logger.debug("_check_self_loops started")
        issues = []
        
        for t in context.transitions:
            if t.source == t.target:
                logger.debug(f"Self loop: {t.source} --[{t.event}]--> {t.source}")
                issues.append(self._create_issue(
                    'TRANSITION_SELF_LOOP', source=t.source, event=t.event
                ))
        
        logger.debug(f"_check_self_loops completed: {len(issues)} issues")
        return issues