"""グローバル変数・イベントフラグのデータモデル（ビジネスロジック層）"""

from dataclasses import dataclass
from typing import List


@dataclass
class SystemVariable:
    """システム全体で共有するグローバル変数"""
    name: str
    type: str
    unit: str = ""
    default_value: str = ""
    group: str = ""
    description: str = ""


@dataclass
class EventFlag:
    """ビットフィールドで扱うイベントフラグ"""
    name: str
    min_value: int
    max_value: int
    group: str = ""
    description: str = ""

    @property
    def bit_width(self) -> int:
        if self.max_value < self.min_value:
            return 0
        return (self.max_value - self.min_value).bit_length()


class GlobalDefinitions:
    """グローバル変数・イベントフラグの管理クラス"""

    def __init__(self):
        self.variables: List[SystemVariable] = []
        self.flags: List[EventFlag] = []

    def variable_groups(self) -> List[str]:
        return sorted({v.group for v in self.variables if v.group})

    def flag_groups(self) -> List[str]:
        return sorted({f.group for f in self.flags if f.group})