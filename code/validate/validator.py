# codegen/validate/validator.py
"""
検証メインクラス
"""

from typing import List, Dict, Type
from .logger import logger
from .models import ValidationResult, ValidationIssue, ValidationContext
from .items.state_validator import StateValidator
from .items.event_validator import EventValidator
from .items.transition_validator import TransitionValidator
from .items.role_function_validator import RoleFunctionValidator
from .items.variable_validator import VariableValidator
from .items.flag_validator import FlagValidator
from .items.queue_validator import QueueValidator
from .items.interrupt_validator import InterruptValidator
from .items.timer_validator import TimerValidator
from .items.custom_type_validator import CustomTypeValidator


class CodeGenerationValidator:
    """コード生成検証メインクラス"""
    
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
        """全検証を実行"""
        logger.debug(f"validate started: sm_id={id(state_machine)}, gd_id={id(global_defs)}")
        
        context = ValidationContext(
            state_machine=state_machine,
            global_defs=global_defs
        )
        logger.debug(f"Context: states={len(context.states)}, events={len(context.events)}, "
                    f"transitions={len(context.transitions)}")
        
        result = ValidationResult()
        
        for category, validator in self._validators.items():
            logger.debug(f"Running validator: {category}")
            try:
                issues = validator.validate(context)
                logger.debug(f"Validator '{category}' returned {len(issues)} issues")
                result.issues.extend(issues)
            except Exception as e:
                logger.error(f"Validator '{category}' failed: {e}", exc_info=True)
        
        logger.debug(f"validate completed: errors={result.error_count}, "
                    f"warnings={result.warning_count}, infos={result.info_count}")
        return result
    
    def validate_category(self, category: str, state_machine, global_defs) -> List[ValidationIssue]:
        """特定カテゴリのみ検証"""
        logger.debug(f"validate_category: {category}")
        validator = self._validators.get(category)
        if validator is None:
            logger.warning(f"Unknown category: {category}")
            return []
        
        context = ValidationContext(
            state_machine=state_machine,
            global_defs=global_defs
        )
        
        issues = validator.validate(context)
        logger.debug(f"Category '{category}' returned {len(issues)} issues")
        return issues
    
    def get_categories(self) -> List[str]:
        """検証カテゴリ一覧を取得"""
        categories = list(self._validators.keys())
        logger.debug(f"get_categories: {categories}")
        return categories