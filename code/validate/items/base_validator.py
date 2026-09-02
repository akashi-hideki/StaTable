# codegen/validate/items/base_validator.py
"""
バリデータ基底クラス
"""

from typing import List
from ..models import ValidationIssue, ValidationContext


class BaseValidator:
    """バリデータ基底クラス"""
    
    # カテゴリ名（サブクラスでオーバーライド）
    category: str = ""
    
    # 検証ルール辞書（サブクラスで定義）
    # {ルールコード: 検証関数}
    rules = {}
    
    def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        """検証を実行"""
        issues = []
        for code, rule_func in self.rules.items():
            result = rule_func(context)
            if result:
                issues.extend(result)
        return issues