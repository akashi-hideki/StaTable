# codegen/variable_generator.py
"""
Variable and flag generation module (multi-layer state machine support)

[v1.5 fix]
  - _generate_normal_init initializes custom struct variables with memset
    (v1.4 used `ctx->data.system_status = 0;` which caused compile errors)

[v1.6 sec 9.8 #92 fix]
  - Fix access macro field name
    DATA_COUNTER(ctx) ((ctx)->data.COUNTER)  -> bug
    DATA_COUNTER(ctx) ((ctx)->data.counter)  -> fixed
    Macro name is uppercase (to_upper_snake); field name uses sanitize_identifier.

[v2.0 fix]
  - Correctly recognize standard types with `_t` suffix (uint32_t / uint8_t, etc.)
    Old: DEFAULT_INIT_VALUES had 'uint32' but not 'uint32_t'
        -> standard types were treated as custom types, generating redundant memset
    New: added _t-suffixed types to DEFAULT_INIT_VALUES
        _normalize_type_for_init strips volatile / const qualifiers before lookup
"""

import sys
import os
import logging
from string import Template
from typing import Dict, Callable, List, Any, Optional

_this_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_this_dir)
for _p in (_this_dir, _parent_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

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
    """Variable and flag generation class (multi-layer state machine support)"""

    INIT_TEMPLATES = {
        'comment': (
            '/**\n'
            ' * @brief  System context initialization\n'
            ' * @param  ctx  System context pointer\n'
            ' */\n'
        ),
        'signature': Template(
            'void $func_name(SystemContext_t *ctx)\n'
        ),
        'function_open': '{\n',
        'null_check': Template(
            '    /* NULL check */\n'
            '    if (ctx == NULL) {\n'
            '        $log_error("NULL pointer: ctx");\n'
            '        return;\n'
            '    }\n'
        ),
        'entry_log': Template(
            '    $log_debug("Enter $func_name");\n'
        ),
        'variables_comment': (
            '    /* Initialize global variables */\n'
        ),
        'flags_comment': (
            '    /* Initialize event flags */\n'
        ),
        'pending_event_comment': (
            '    /* Initialize pending event */\n'
        ),
        'pending_event_init': (
            '    ctx->pending_event = 0;\n'
            '    ctx->pending_event_valid = false;\n'
        ),
        'exit_log': Template(
            '    $log_debug("Exit $func_name");\n'
        ),
        'function_close': '}\n',
    }

    INIT_FUNCTION_STEPS = [
        {'action': 'template', 'key': 'comment'},
        {'action': 'template', 'key': 'signature',
         'format': {'func_name': '{func_name}'}},
        {'action': 'template', 'key': 'function_open'},
        {'action': 'template', 'key': 'null_check',
         'format': {'log_error': '{log_error}'}},
        {'action': 'blank'},
        {'action': 'template', 'key': 'entry_log',
         'format': {'func_name': '{func_name}', 'log_debug': '{log_debug}'}},
        {'action': 'blank'},
        {'action': 'template', 'key': 'variables_comment'},
        {'action': 'loop', 'source': 'variables', 'generator': 'init'},
        {'action': 'blank'},
        {'action': 'template', 'key': 'flags_comment'},
        {'action': 'loop', 'source': 'flags', 'generator': 'init'},
        {'action': 'blank'},
        {'action': 'template', 'key': 'pending_event_comment'},
        {'action': 'template', 'key': 'pending_event_init'},
        {'action': 'blank'},
        {'action': 'template', 'key': 'exit_log',
         'format': {'func_name': '{func_name}', 'log_debug': '{log_debug}'}},
        {'action': 'template', 'key': 'function_close'},
    ]

    # ================================================================
    # v2.0 fix: add standard types with _t suffix
    #   Consistent with type_mapper.py TYPE_MAPPING:
    #     'uint32' -> 'uint32_t' is converted, so
    #     generated code must treat 'uint32_t' as a standard type
    # ================================================================
    DEFAULT_INIT_VALUES = {
        # ---- Signed integers ----
        'int': '0', 'int8': '0', 'int16': '0', 'int32': '0', 'int64': '0',
        'int8_t': '0', 'int16_t': '0', 'int32_t': '0', 'int64_t': '0',
        'short': '0', 'long': '0',
        # ---- Unsigned integers ----
        'uint': '0', 'uint8': '0', 'uint16': '0', 'uint32': '0', 'uint64': '0',
        'uint8_t': '0', 'uint16_t': '0', 'uint32_t': '0', 'uint64_t': '0',
        'unsigned': '0', 'unsigned int': '0', 'size_t': '0',
        # ---- Floating point ----
        'float': '0.0f', 'double': '0.0',
        # ---- Boolean / character ----
        'bool': 'false', '_Bool': 'false',
        'char': '0', 'string': 'NULL',
    }

    # Type qualifiers (may appear at the beginning)
    _TYPE_QUALIFIERS = ('volatile', 'const', 'static')

    # v1.6 sec 9.8 #92: separate macro name and field name
    MACRO_TEMPLATES = {
        'data_macro': Template(
            '#define DATA_$macro_name(ctx)    ((ctx)->data.$field_name)\n'
        ),
        'flag_macro': Template(
            '#define FLAG_$macro_name(ctx)   ((ctx)->flags.$field_name)\n'
        ),
    }

    INIT_CODE_TEMPLATES = {
        'array_init': Template(
            '    memset(ctx->data.$var_name, 0, sizeof(ctx->data.$var_name));\n'
        ),
        'struct_init': Template(
            '    memset(&ctx->data.$var_name, 0, sizeof(ctx->data.$var_name));\n'
        ),
        'normal_init': Template(
            '    ctx->data.$var_name = $init_value;\n'
        ),
        'flag_init': Template(
            '    ctx->flags.$flag_name = 0;\n'
        ),
    }

    VARIABLE_TYPE_DETECTORS = {
        'array': lambda v: getattr(v, 'array_size', 0) > 0,
        'normal': lambda v: True,
    }

    def __init__(self):
        self.mapper = CTypeMapper()
        self.naming = CNamingConvention()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS

        self.step_executors = {
            'template': self._execute_template_step,
            'blank': self._execute_blank_step,
            'loop': self._execute_loop_step,
        }

    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)

    def _detect_variable_type(self, var) -> str:
        for var_type, detector in self.VARIABLE_TYPE_DETECTORS.items():
            if detector(var):
                return var_type
        return 'normal'

    def _build_context(self, global_defs: GlobalDefinitions) -> dict:
        return {
            'func_name': self.templates.FUNCTION_NAMES['system_context_init'],
            'log_debug': self.strings['log_debug'],
            'log_error': self.strings['log_error'],
            'variables': getattr(global_defs, 'variables', []),
            'flags': getattr(global_defs, 'flags', []),
        }

    def _replace_placeholders(self, template: str, params: dict) -> str:
        result = template
        for key, value in params.items():
            result = result.replace('$' + key, str(value))
        return result

    def _resolve_value(self, value, context: dict) -> str:
        if isinstance(value, str) and value.startswith('{') and value.endswith('}'):
            key = value[1:-1]
            return str(context.get(key, value))
        return str(value)

    def _execute_template_step(self, step: dict, context: dict) -> List[str]:
        template_key = step.get('key', '')
        template = self.INIT_TEMPLATES.get(template_key, '')
        if not template:
            return []

        format_params = step.get('format', {})
        resolved = {}
        for k, v in format_params.items():
            resolved[k] = self._resolve_value(v, context)

        if isinstance(template, Template):
            return [template.substitute(resolved).rstrip('\n')]

        return [self._replace_placeholders(template, resolved).rstrip('\n')]

    def _execute_blank_step(self, step: dict, context: dict) -> List[str]:
        return [""]

    def _execute_loop_step(self, step: dict, context: dict) -> List[str]:
        source_key = step.get('source', '')
        generator_key = step.get('generator', '')
        items = context.get(source_key, [])
        results = []
        for item in items:
            if generator_key == 'init':
                results.append(self._generate_init_code(item))
            elif generator_key == 'macro':
                results.append(self._generate_access_macro(item))
        return [r for r in results if r]

    # ================================================================
    # v1.6 sec 9.8 #92: macro generation (macro name = uppercase,
    # field name = original)
    # ================================================================
    def _generate_data_macro(self, var) -> str:
        """
        Generate data access macro.

        [v1.6 fix]
          Old: DATA_COUNTER(ctx) ((ctx)->data.COUNTER)   -> uppercase field (bug)
          New: DATA_COUNTER(ctx) ((ctx)->data.counter)   -> original field
        """
        raw_name = getattr(var, 'name', 'unnamed')
        macro_name = self.naming.to_upper_snake(raw_name)
        field_name = self.naming.sanitize_identifier(raw_name)
        return self.MACRO_TEMPLATES['data_macro'].substitute(
            macro_name=macro_name, field_name=field_name
        ).rstrip('\n')

    def _generate_flag_macro(self, flag) -> str:
        """
        Generate flag access macro.

        [v1.6 fix]
          Old: FLAG_EVT_INIT_DONE(ctx) ((ctx)->flags.EVT_INIT_DONE)   -> bug
          New: FLAG_EVT_INIT_DONE(ctx) ((ctx)->flags.EVT_INIT_DONE)   -> matches
          * Field name may not be sanitize_identifier-ed on the struct side
        """
        raw_name = getattr(flag, 'name', 'unnamed')
        macro_name = self.naming.to_upper_snake(raw_name)
        field_name = self.naming.sanitize_identifier(raw_name)
        return self.MACRO_TEMPLATES['flag_macro'].substitute(
            macro_name=macro_name, field_name=field_name
        ).rstrip('\n')

    def _generate_access_macro(self, item) -> str:
        item_class = item.__class__.__name__
        if item_class == 'SystemVariable':
            return self._generate_data_macro(item)
        elif item_class == 'EventFlag':
            return self._generate_flag_macro(item)
        return ""

    # ================================================================
    # v2.0 addition: normalize type name
    # ================================================================
    def _normalize_type_for_init(self, var_type: str) -> str:
        """
        Normalize type name so it can be looked up in DEFAULT_INIT_VALUES.

        Examples:
          'volatile uint32_t' -> 'uint32_t'
          'uint32_t'          -> 'uint32_t'
          'const uint8_t'     -> 'uint8_t'
          'MyCustomType'      -> 'MyCustomType' (unchanged)
        """
        if not var_type:
            return ''
        tokens = var_type.strip().split()
        # Strip leading qualifiers
        while tokens and tokens[0] in self._TYPE_QUALIFIERS:
            tokens.pop(0)
        # Sign qualifiers such as 'unsigned int' are preserved
        normalized = ' '.join(tokens)
        return normalized

    # ================================================================
    # Initialization code generation
    # ================================================================
    def _generate_array_init(self, var) -> str:
        var_name = self.naming.sanitize_identifier(getattr(var, 'name', 'unnamed'))
        return self.INIT_CODE_TEMPLATES['array_init'].substitute(
            var_name=var_name
        ).rstrip('\n')

    def _generate_normal_init(self, var) -> str:
        """
        [v1.5 fix]
          - Custom types (not in DEFAULT_INIT_VALUES) use memset
          - Primitive types use direct assignment (= 0 etc.)

        [v2.0 fix]
          - Correctly recognize standard types with _t suffix (uint32_t etc.)
          - Strip volatile / const qualifiers before lookup
          - Prevents redundant memset generation
        """
        var_name = self.naming.sanitize_identifier(getattr(var, 'name', 'unnamed'))
        raw_type = getattr(var, 'type', 'void')
        normalized_type = self._normalize_type_for_init(raw_type)

        # v2.0: custom type check (using normalized type name)
        if normalized_type not in self.DEFAULT_INIT_VALUES:
            self._log_debug(
                f"_generate_normal_init: '{var_name}' "
                f"(type='{raw_type}' -> '{normalized_type}') "
                f"is a custom type -> using memset"
            )
            return self.INIT_CODE_TEMPLATES['struct_init'].substitute(
                var_name=var_name
            ).rstrip('\n')

        # Standard type: = 0 / = false / = 0.0f etc.
        init_value = getattr(var, 'default_value', '') or \
            self.DEFAULT_INIT_VALUES.get(normalized_type, '0')
        return self.INIT_CODE_TEMPLATES['normal_init'].substitute(
            var_name=var_name, init_value=init_value
        ).rstrip('\n')

    def _generate_flag_init(self, flag) -> str:
        flag_name = self.naming.sanitize_identifier(getattr(flag, 'name', 'unnamed'))
        return self.INIT_CODE_TEMPLATES['flag_init'].substitute(
            flag_name=flag_name
        ).rstrip('\n')

    def _generate_init_code(self, item) -> str:
        item_class = item.__class__.__name__
        if item_class == 'SystemVariable':
            var_type = self._detect_variable_type(item)
            if var_type == 'array':
                return self._generate_array_init(item)
            else:
                return self._generate_normal_init(item)
        elif item_class == 'EventFlag':
            return self._generate_flag_init(item)
        return ""

    # ================================================================
    # Public API
    # ================================================================
    def generate_init_function(self, global_defs: GlobalDefinitions) -> str:
        self._log_debug("=== generate_init_function START ===")
        lines = []
        context = self._build_context(global_defs)

        for step in self.INIT_FUNCTION_STEPS:
            executor = self.step_executors.get(step.get('action', ''))
            if executor:
                lines.extend(executor(step, context))

        result = '\n'.join(lines)
        self._log_debug(f"=== generate_init_function END: {len(result)} chars ===")
        return result

    def generate_all_macros(self, global_defs: GlobalDefinitions) -> str:
        self._log_debug("=== generate_all_macros START ===")
        lines = []
        for var in getattr(global_defs, 'variables', []):
            lines.append(self._generate_data_macro(var))
        for flag in getattr(global_defs, 'flags', []):
            lines.append(self._generate_flag_macro(flag))
        result = '\n'.join(lines)
        self._log_debug(f"=== generate_all_macros END: {len(lines)} macros ===")
        return result

    def generate_variable(self, var_type: str, item) -> str:
        if var_type == 'macro':
            return self._generate_access_macro(item)
        elif var_type == 'init':
            return self._generate_init_code(item)
        elif var_type == 'global':
            return self._generate_normal_init(item)
        elif var_type == 'flag':
            return self._generate_flag_init(item)
        raise ValueError(f"Unknown variable type: {var_type}")

    def generate_all(self, global_defs: GlobalDefinitions) -> Dict[str, str]:
        self._log_debug("=== generate_all START (variable_generator) ===")
        result = {
            'init_function': self.generate_init_function(global_defs),
            'macros': self.generate_all_macros(global_defs),
        }
        self._log_debug("=== generate_all END (variable_generator) ===")
        return result