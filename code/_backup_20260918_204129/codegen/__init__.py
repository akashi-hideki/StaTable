# codegen package
"""
StaTable Code generation層

【v1.5 Add】
  - 再エクスポートは最小限に留める
  - CCodeGenerator は生成時に多数のサブモジュールを読み込むため、
    トップレベルで再エクスポートしない（起動時間短縮のため）
"""

__all__ = [
    'CCodeGenerator',
    'CodeGenerationConfig',
    'ConfigManager',
]


def __getattr__(name):
    """
    PEP 562 遅延インポート

    `from codegen import CCodeGenerator` のように使われた時のみ、
    実際のモジュールをロードする。
    起動時間を抑えつつ、利便性を確保する。
    """
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