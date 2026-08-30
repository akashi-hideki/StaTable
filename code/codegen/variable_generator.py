# codegen/variable_generator.py
"""
変数・フラグ生成モジュール（完全データ駆動版）
"""

import sys
import os
import logging
from typing import Dict, Callable, List, Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statable.global_defs import SystemVariable, EventFlag, GlobalDefinitions

try:
    from .type_mapper import CTypeMapper
    from .naming_convention import CNamingConvention
    from .code_templates import CodeTemplates
except ImportError:
    from type_mapper import CTypeMapper
    from naming_convention import CNamingConvention
    from code_templates import CodeTemplates

logger = logging.getLogger(__name__)


class VariableGenerator:
    """変数・フラグ生成クラス（完全データ駆動）"""
    
    def __init__(self):
        self.mapper = CTypeMapper()
        self.naming = CNamingConvention()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        
        self.variable_type_detectors = {
            'array': lambda v: getattr(v, 'array_size', 0) > 0,
            'normal': lambda v: True,
        }
        
        self.variable_generators = {
            'global': self._generate_global_variable,
            'flag': self._generate_event_flag,
            'macro': self._generate_access_macro,
            'init': self._generate_init_code,
        }
        
        self.default_init_values = {
            'int': '0', 'int8': '0', 'int16': '0', 'int32': '0', 'int64': '0',
            'uint': '0', 'uint8': '0', 'uint16': '0', 'uint32': '0', 'uint64': '0',
            'float': '0.0f', 'double': '0.0', 'bool': 'false', 'char': '0', 'string': 'NULL',
        }
        
        self.init_generators = {
            'array': self._generate_array_init,
            'normal': self._generate_normal_init,
            'flag': self._generate_flag_init,
        }
        
        self.macro_generators = {
            'SystemVariable': self._generate_data_macro,
            'EventFlag': self._generate_flag_macro,
        }
        
        self.init_templates = {
            'comment': '''/**
 * @brief  システムコンテキスト初期化
 * @param  ctx  システムコンテキストポインタ
 */''',
            'signature': 'void {func_name}(SystemContext_t *ctx)',
            'function_open': '{',
            'null_check': '''    /* NULLチェック */
    if (ctx == NULL) {
        {log_error}("NULL pointer: ctx");
        return;
    }''',
            'entry_log': '    {log_debug}("Enter {func_name}");',
            'variables_comment': '    /* グローバル変数の初期化 */',
            'flags_comment': '    /* イベントフラグの初期化 */',
            'exit_log': '    {log_debug}("Exit {func_name}");',
            'function_close': '}',
        }
        
        self.init_function_steps = [
            {'action': 'template', 'key': 'comment'},
            {'action': 'template', 'key': 'signature', 'format': {'func_name': '{func_name}'}},
            {'action': 'template', 'key': 'function_open'},
            {'action': 'template', 'key': 'null_check', 'format': {'log_error': '{log_error}'}},
            {'action': 'blank'},
            {'action': 'template', 'key': 'entry_log', 'format': {'func_name': '{func_name}', 'log_debug': '{log_debug}'}},
            {'action': 'blank'},
            {'action': 'template', 'key': 'variables_comment'},
            {'action': 'loop', 'source': 'variables', 'generator': 'init'},
            {'action': 'blank'},
            {'action': 'template', 'key': 'flags_comment'},
            {'action': 'loop', 'source': 'flags', 'generator': 'init'},
            {'action': 'blank'},
            {'action': 'template', 'key': 'exit_log', 'format': {'func_name': '{func_name}', 'log_debug': '{log_debug}'}},
            {'action': 'template', 'key': 'function_close'},
        ]
        
        self.step_executors = {
            'template': self._execute_template_step,
            'blank': self._execute_blank_step,
            'loop': self._execute_loop_step,
        }
    
    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)
    
    def _detect_variable_type(self, var):
        for var_type, detector in self.variable_type_detectors.items():
            if detector(var):
                return var_type
        return 'normal'
    
    def _build_context(self, global_defs):
        return {
            'func_name': self.templates.FUNCTION_NAMES['system_context_init'],
            'log_debug': self.strings['log_debug'],
            'log_error': self.strings['log_error'],
            'variables': getattr(global_defs, 'variables', []),
            'flags': getattr(global_defs, 'flags', []),
        }
    
    def _replace_placeholders(self, template, params):
        result = template
        for key, value in params.items():
            result = result.replace('{' + key + '}', str(value))
        return result
    
    def _resolve_value(self, value, context):
        if isinstance(value, str) and value.startswith('{') and value.endswith('}'):
            key = value[1:-1]
            return str(context.get(key, value))
        return str(value)
    
    def _execute_template_step(self, step, context):
        template_key = step.get('key', '')
        template = self.init_templates.get(template_key, '')
        if not template:
            return []
        
        format_params = step.get('format', {})
        resolved_params = {}
        for key, value in format_params.items():
            resolved_params[key] = self._resolve_value(value, context)
        
        formatted = self._replace_placeholders(template, resolved_params)
        return [formatted]
    
    def _execute_blank_step(self, step, context):
        return [""]
    
    def _execute_loop_step(self, step, context):
        source_key = step.get('source', '')
        generator_key = step.get('generator', '')
        items = context.get(source_key, [])
        results = []
        for item in items:
            if generator_key == 'init':
                results.append(self._generate_init_code(item))
            elif generator_key == 'macro':
                results.append(self._generate_access_macro(item))
        return results
    
    def _generate_global_variable(self, var):
        var_name = self.naming.sanitize_identifier(getattr(var, 'name', 'unnamed'))
        c_type = self.mapper.map_type(getattr(var, 'type', 'void'))
        var_type = self._detect_variable_type(var)
        indent = self.strings['indent_1']
        
        if var_type == 'array':
            size = getattr(var, 'array_size', 0)
            return f"{indent}{c_type} {var_name}[{size}];"
        return f"{indent}{c_type} {var_name};"
    
    def _generate_event_flag(self, flag):
        flag_name = self.naming.sanitize_identifier(getattr(flag, 'name', 'unnamed'))
        indent = self.strings['indent_1']
        return f"{indent}uint8_t {flag_name};"
    
    def _generate_data_macro(self, var):
        var_name = self.naming.to_upper_snake(getattr(var, 'name', 'unnamed'))
        return f"#define DATA_{var_name}(ctx)    ((ctx)->data.{var_name})"
    
    def _generate_flag_macro(self, flag):
        flag_name = self.naming.to_upper_snake(getattr(flag, 'name', 'unnamed'))
        return f"#define FLAG_{flag_name}(ctx)   ((ctx)->flags.{flag_name})"
    
    def _generate_access_macro(self, item):
        item_class = item.__class__.__name__
        generator = self.macro_generators.get(item_class)
        return generator(item) if generator else ""
    
    def _generate_array_init(self, var):
        var_name = self.naming.sanitize_identifier(getattr(var, 'name', 'unnamed'))
        return f"    memset(ctx->data.{var_name}, 0, sizeof(ctx->data.{var_name}));"
    
    def _generate_normal_init(self, var):
        var_name = self.naming.sanitize_identifier(getattr(var, 'name', 'unnamed'))
        init_value = getattr(var, 'default_value', '') or self.default_init_values.get(getattr(var, 'type', 'void'), '0')
        return f"    ctx->data.{var_name} = {init_value};"
    
    def _generate_flag_init(self, flag):
        flag_name = self.naming.sanitize_identifier(getattr(flag, 'name', 'unnamed'))
        return f"    ctx->flags.{flag_name} = 0;"
    
    def _generate_init_code(self, item):
        item_class = item.__class__.__name__
        if item_class == 'SystemVariable':
            var_type = self._detect_variable_type(item)
            generator = self.init_generators.get(var_type)
            return generator(item) if generator else ""
        elif item_class == 'EventFlag':
            generator = self.init_generators.get('flag')
            return generator(item) if generator else ""
        return ""
    
    def generate_init_function(self, global_defs):
        self._log_debug("Generating init function (data-driven)")
        lines = []
        context = self._build_context(global_defs)
        for step in self.init_function_steps:
            executor = self.step_executors.get(step.get('action', ''))
            if executor:
                lines.extend(executor(step, context))
        return '\n'.join(lines)
    
    def generate_variable(self, var_type, item):
        generator = self.variable_generators.get(var_type)
        if generator:
            return generator(item)
        raise ValueError(f"Unknown variable type: {var_type}")
    
    def generate_all_macros(self, global_defs):
        lines = []
        for var in getattr(global_defs, 'variables', []):
            lines.append(self.generate_variable('macro', var))
        for flag in getattr(global_defs, 'flags', []):
            lines.append(self.generate_variable('macro', flag))
        return '\n'.join(lines)