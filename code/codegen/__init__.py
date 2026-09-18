# codegen package
"""
StaTable code generation layer

[v1.5 added]
  - Keep re-exports minimal
  - CCodeGenerator loads many submodules at generation time,
    so it is not re-exported at top level (to reduce startup time)
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