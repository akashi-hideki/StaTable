# codegen package
"""
StaTable code generation layer

[v1.5 added]
  - Keep re-exports minimal
  - CCodeGenerator loads many submodules at generation time,
    so it is not re-exported at top level (to reduce startup time)
"""

__version__ = "3.4.3"

__all__ = [
    'CCodeGenerator',
    'CodeGenerationConfig',
    'ConfigManager',
    'validate',
    '__version__',
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
    if name == 'validate':
        import importlib
        return importlib.import_module('.validate', __name__)
    raise AttributeError(
        f"module 'codegen' has no attribute {name!r}"
    )