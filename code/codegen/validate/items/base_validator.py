# codegen/validate/items/base_validator.py
"""\nValidator base class\n"""

import sys
import os
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from validate.models import ValidationIssue, ValidationContext


class BaseValidator:
    """Validator base class"""
    
    category: str = ""
    rules = {}
    
    def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        issues = []
        for code, rule_func in self.rules.items():
            result = rule_func(context)
            if result:
                issues.extend(result)
        return issues