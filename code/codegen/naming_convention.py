# codegen/naming_convention.py
"""
C言語命名規則モジュール（辞書駆動版）
"""

import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .code_templates import CodeTemplates
except ImportError:
    from code_templates import CodeTemplates


class CNamingConvention:
    """C言語の命名規則を管理するクラス"""
    
    def __init__(self):
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
    
    # 変換パターン定義
    CONVERSION_PATTERNS = {
        'upper_snake': {
            'patterns': [
                (r'(.)([A-Z][a-z]+)', r'\1_\2'),
                (r'([a-z0-9])([A-Z])', r'\1_\2'),
            ],
            'transform': str.upper,
        },
        'lower_snake': {
            'patterns': [
                (r'(.)([A-Z][a-z]+)', r'\1_\2'),
                (r'([a-z0-9])([A-Z])', r'\1_\2'),
            ],
            'transform': str.lower,
        },
        'camel': {
            'split': r'[_-]',
            'first': str.lower,
            'rest': str.capitalize,
        },
        'pascal': {
            'split': r'[_-]',
            'first': str.capitalize,
            'rest': str.capitalize,
        },
    }
    
    # C言語予約語
    C_KEYWORDS = {
        'auto', 'break', 'case', 'char', 'const', 'continue',
        'default', 'do', 'double', 'else', 'enum', 'extern',
        'float', 'for', 'goto', 'if', 'inline', 'int', 'long',
        'register', 'restrict', 'return', 'short', 'signed',
        'sizeof', 'static', 'struct', 'switch', 'typedef',
        'union', 'unsigned', 'void', 'volatile', 'while',
        '_Bool', '_Complex', '_Imaginary'
    }
    
    # 識別子生成ルール
    IDENTIFIER_RULES = {
        'variable': 'to_lower_snake',
        'function': 'to_pascal_case',
        'type': 'to_pascal_case',
        'enum': 'to_upper_snake',
        'macro': 'to_upper_snake',
    }
    
    @classmethod
    def to_snake_case(cls, name, upper=False):
        """スネークケースに変換"""
        config = cls.CONVERSION_PATTERNS['upper_snake' if upper else 'lower_snake']
        result = name
        
        for pattern, replacement in config['patterns']:
            result = re.sub(pattern, replacement, result)
        
        return config['transform'](result)
    
    @classmethod
    def to_upper_snake(cls, name):
        """大文字スネークケースに変換"""
        return cls.to_snake_case(name, upper=True)
    
    @classmethod
    def to_lower_snake(cls, name):
        """小文字スネークケースに変換"""
        return cls.to_snake_case(name, upper=False)
    
    @classmethod
    def to_camel_case(cls, name):
        """キャメルケースに変換"""
        config = cls.CONVERSION_PATTERNS['camel']
        parts = re.split(config['split'], name)
        if not parts:
            return ""
        
        result = config['first'](parts[0])
        for part in parts[1:]:
            if part:
                result += config['rest'](part)
        return result
    
    @classmethod
    def to_pascal_case(cls, name):
        """パスカルケースに変換"""
        config = cls.CONVERSION_PATTERNS['pascal']
        parts = re.split(config['split'], name)
        if not parts:
            return ""
        
        result = ""
        for part in parts:
            if part:
                result += config['rest'](part)
        return result
    
    @classmethod
    def sanitize_identifier(cls, name):
        """識別子をサニタイズ"""
        if not name:
            return "_unnamed"
        
        if name[0].isdigit():
            name = '_' + name
        
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        
        if name in cls.C_KEYWORDS:
            name = name + '_'
        
        return name
    
    @classmethod
    def create_identifier(cls, name, kind='variable'):
        """種類に応じた識別子を生成"""
        method_name = cls.IDENTIFIER_RULES.get(kind, 'to_lower_snake')
        method = getattr(cls, method_name)
        return cls.sanitize_identifier(method(name))
    
    @classmethod
    def create_type_name(cls, name):
        """型名を生成"""
        base = cls.to_pascal_case(name)
        return f"{base}_t"
    
    @classmethod
    def create_enum_value(cls, prefix, name):
        """列挙値を生成"""
        clean_prefix = cls.sanitize_identifier(prefix)
        clean_name = cls.to_upper_snake(name)
        return f"{clean_prefix}_{clean_name}"
    
    @classmethod
    def create_function_name(cls, module, action):
        """関数名を生成"""
        clean_module = cls.to_pascal_case(module)
        clean_action = cls.to_pascal_case(action)
        return f"{clean_module}_{clean_action}"
    
    @classmethod
    def create_variable_name(cls, name):
        """変数名を生成"""
        return cls.sanitize_identifier(cls.to_lower_snake(name))
    
    @classmethod
    def create_macro_name(cls, name):
        """マクロ名を生成"""
        return cls.to_upper_snake(name)