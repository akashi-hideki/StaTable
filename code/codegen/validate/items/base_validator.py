# codegen/validate/items/base_validator.py
"""
バリデータ基底クラス
"""

import sys
import os
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from ..models import ValidationIssue, ValidationContext
except ImportError:
    from models import ValidationIssue, ValidationContext


class BaseValidator:
    """バリデータ基底クラス"""
    
    category: str = ""
    rules = {}
    
    def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        """検証を実行"""
        issues = []
        for code, rule_func in self.rules.items():
            result = rule_func(context)
            if result:
                issues.extend(result)
        return issues