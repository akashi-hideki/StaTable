# codegen package
"""
StaTable Code generation層

【v1.5 Add】
  - 再エクスポートは最小限に留める
  - CCodeGenerator は生成時に多数のサブモジュールを読み込むため、
    トップレベルで再エクスポートしない（Startup時間短縮のため）
"""

__all__ = [
    'CCodeGenerator',
    'CodeGenerationConfig',
    'ConfigManager',
]


def __getattr__(name):
    """\n    PEP 562 lazy import\n"""
    if name == 'CCodeGenerator':
        from .c_code_generator import CCodeGenerator
        return CCodeGenerator
    if name == 'CodeGenerationConfig':
        from .config import CodeGenerationConfig
        return CodeGenerationConfig
    if name == 'ConfigManager':
        from .config import ConfigManager
        return ConfigManager
    raise AttributeError(
        f"module 'codegen' has no attribute {name!r}"
    )