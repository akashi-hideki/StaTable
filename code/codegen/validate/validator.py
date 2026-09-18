# codegen/validate/validator.py
"""\nValidation main class\n"""

import sys
import os
from typing import List, Dict, Type

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Logger referenced directly
from validate.logger import logger

# Model
from validate.models import ValidationResult, ValidationIssue, ValidationContext

# Validator
from validate.items.state_validator import StateValidator
from validate.items.event_validator import EventValidator
from validate.items.transition_validator import TransitionValidator
from validate.items.role_function_validator import RoleFunctionValidator
from validate.items.variable_validator import VariableValidator
from validate.items.flag_validator import FlagValidator
from validate.items.queue_validator import QueueValidator
from validate.items.interrupt_validator import InterruptValidator
from validate.items.timer_validator import TimerValidator
from validate.items.custom_type_validator import CustomTypeValidator


class CodeGenerationValidator:
    """Code generation validation main class"""
    
    VALIDATORS: Dict[str, Type] = {
        'state': StateValidator,
        'event': EventValidator,
        'transition': TransitionValidator,
        'role_function': RoleFunctionValidator,
        'variable': VariableValidator,
        'flag': FlagValidator,
        'queue': QueueValidator,
        'interrupt': InterruptValidator,
        'timer': TimerValidator,
        'custom_type': CustomTypeValidator,
    }
    
    def __init__(self):
        logger.debug("CodeGenerationValidator.__init__ started")
        self._validators = {}
        for category, validator_class in self.VALIDATORS.items():
            logger.debug(f"Creating validator: {category} -> {validator_class.__name__}")
            self._validators[category] = validator_class()
        logger.debug(f"CodeGenerationValidator.__init__ completed: {len(self._validators)} validators")
    
    def validate(self, state_machine, global_defs) -> ValidationResult:
        logger.debug(f"validate started: sm_id={id(state_machine)}, gd_id={id(global_defs)}")
        
        context = ValidationContext(
            state_machine=state_machine,
            global_defs=global_defs
        )
        
        result = ValidationResult()
        
        for category, validator in self._validators.items():
            logger.debug(f"Running validator: {category}")
            try:
                issues = validator.validate(context)
                result.issues.extend(issues)
            except Exception as e:
                logger.error(f"Validator '{category}' failed: {e}", exc_info=True)
        
        logger.debug(f"validate completed: errors={result.error_count}, "
                    f"warnings={result.warning_count}, infos={result.info_count}")
        return result
    
    def validate_category(self, category: str, state_machine, global_defs) -> List[ValidationIssue]:
        logger.debug(f"validate_category: {category}")
        validator = self._validators.get(category)
        if validator is None:
            logger.warning(f"Unknown category: {category}")
            return []
        
        context = ValidationContext(
            state_machine=state_machine,
            global_defs=global_defs
        )
        
        return validator.validate(context)
    
    def get_categories(self) -> List[str]:
        return list(self._validators.keys())