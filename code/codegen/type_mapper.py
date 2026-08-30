# codegen/type_mapper.py
"""
C言語型マッピングモジュール（辞書駆動版）
"""

import sys
import os
from typing import Set, List

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .code_templates import CodeTemplates
except ImportError:
    from code_templates import CodeTemplates


class CTypeMapper:
    """StaTableの型をC言語の型にマッピングするクラス"""
    
    def __init__(self):
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
    
    # 基本型マッピングテーブル
    TYPE_MAPPING = {
        'int': 'int',
        'int8': 'int8_t',
        'int16': 'int16_t',
        'int32': 'int32_t',
        'int64': 'int64_t',
        'uint': 'unsigned int',
        'uint8': 'uint8_t',
        'uint16': 'uint16_t',
        'uint32': 'uint32_t',
        'uint64': 'uint64_t',
        'float': 'float',
        'double': 'double',
        'bool': 'bool',
        'char': 'char',
        'string': 'char*',
        'void': 'void',
    }
    
    # 型カテゴリ定義
    TYPE_CATEGORIES = {
        'int': 'integer',
        'int8': 'integer',
        'int16': 'integer',
        'int32': 'integer',
        'int64': 'integer',
        'uint': 'integer',
        'uint8': 'integer',
        'uint16': 'integer',
        'uint32': 'integer',
        'uint64': 'integer',
        'float': 'float',
        'double': 'float',
        'bool': 'boolean',
        'char': 'character',
        'string': 'string',
        'void': 'void',
    }
    
    # ヘッダファイル要件定義
    HEADER_REQUIREMENTS = {
        'integer': '#include <stdint.h>',
        'boolean': '#include <stdbool.h>',
        'string': '#include <string.h>',
        'float': '#include <math.h>',
    }
    
    @classmethod
    def map_type(cls, sta_type):
        """型マッピング"""
        return cls.TYPE_MAPPING.get(sta_type, sta_type)
    
    @classmethod
    def get_type_category(cls, sta_type):
        """型カテゴリを取得"""
        return cls.TYPE_CATEGORIES.get(sta_type, 'custom')
    
    @classmethod
    def get_required_headers(cls, types):
        """必要なヘッダファイルを取得"""
        headers = set()
        categories = set()
        
        for type_name in types:
            category = cls.get_type_category(type_name)
            categories.add(category)
        
        for category in categories:
            header = cls.HEADER_REQUIREMENTS.get(category)
            if header:
                headers.add(header)
        
        return sorted(headers)