# codegen/variable_generator.py
"""
変数・フラグ生成モジュール（多層ステートマシン対応版）

【v1.5 修正】
  - _generate_normal_init でカスタム構造体変数を memset で初期化
    （v1.4 までは `ctx->data.system_status = 0;` でコンパイルエラー）

【v1.6 §9.8 #92 修正】
  - アクセスマクロのフィールド名を修正
    DATA_COUNTER(ctx) ((ctx)->data.COUNTER)  ← バグ
    DATA_COUNTER(ctx) ((ctx)->data.counter)  ← 修正後
    マクロ名は大文字（to_upper_snake）、フィールド名は sanitize_identifier を使用。
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
    """変数・フラグ生成クラス（多層ステートマシン対応）"""

    INIT_TEMPLATES = {
        'comment': (
            '/**\n'
            ' * @brief  システムコンテキスト初期化\n'
            ' * @param  ctx  システムコンテキストポインタ\n'
            ' */\n'
        ),
        'signature': Template(
            'void $func_name(SystemContext_t *ctx)\n'
        ),
        'function_open': '{\n',
        'null_check': Template(
            '    /* NULLチェック */\n'
            '    if (ctx == NULL) {\n'
            '        $log_error("NULL pointer: ctx");\n'
            '        return;\n'
            '    }\n'
        ),
        'entry_log': Template(
            '    $log_debug("Enter $func_name");\n'
        ),
        'variables_comment': (
            '    /* グローバル変数の初期化 */\n'
        ),
        'flags_comment': (
            '    /* イベントフラグの初期化 */\n'
        ),
        'pending_event_comment': (
            '    /* 保留イベントの初期化 */\n'
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

    DEFAULT_INIT_VALUES = {
        'int': '0', 'int8': '0', 'int16': '0', 'int32': '0', 'int64': '0',
        'uint': '0', 'uint8': '0', 'uint16': '0', 'uint32': '0', 'uint64': '0',
        'float': '0.0f', 'double': '0.0', 'bool': 'false',
        'char': '0', 'string': 'NULL',
    }

    # ★ v1.6 §9.8 #92: マクロ名とフィールド名を分離
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
    # ★ v1.6 §9.8 #92: マクロ生成（マクロ名 = 大文字、フィールド名 = 元のまま）
    # ================================================================
    def _generate_data_macro(self, var) -> str:
        """
        データアクセスマクロを生成

        【v1.6 修正】
          旧: DATA_COUNTER(ctx) ((ctx)->data.COUNTER)  ← フィールド名が大文字（バグ）
          新: DATA_COUNTER(ctx) ((ctx)->data.counter)  ← フィールド名を元のまま
        """
        raw_name = getattr(var, 'name', 'unnamed')
        macro_name = self.naming.to_upper_snake(raw_name)
        field_name = self.naming.sanitize_identifier(raw_name)
        return self.MACRO_TEMPLATES['data_macro'].substitute(
            macro_name=macro_name, field_name=field_name
        ).rstrip('\n')

    def _generate_flag_macro(self, flag) -> str:
        """
        フラグアクセスマクロを生成

        【v1.6 修正】
          旧: FLAG_EVT_INIT_DONE(ctx) ((ctx)->flags.EVT_INIT_DONE)  ← バグ
          新: FLAG_EVT_INIT_DONE(ctx) ((ctx)->flags.EVT_INIT_DONE)  ← 一致（元々 OK）
          ※ フィールド名は struct 側で sanitize_identifier されてない場合あり
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
    # 初期化コード生成
    # ================================================================
    def _generate_array_init(self, var) -> str:
        var_name = self.naming.sanitize_identifier(getattr(var, 'name', 'unnamed'))
        return self.INIT_CODE_TEMPLATES['array_init'].substitute(
            var_name=var_name
        ).rstrip('\n')

    def _generate_normal_init(self, var) -> str:
        """
        【v1.5 修正】
          - カスタム型（DEFAULT_INIT_VALUES に無い型）は memset を使う
          - プリミティブ型は従来通り = 0 などの数値代入
        """
        var_name = self.naming.sanitize_identifier(getattr(var, 'name', 'unnamed'))
        var_type = getattr(var, 'type', 'void')

        # ★ v1.5: カスタム型判定 → memset
        if var_type not in self.DEFAULT_INIT_VALUES:
            self._log_debug(
                f"_generate_normal_init: '{var_name}' (type='{var_type}') "
                f"is a custom type → using memset"
            )
            return self.INIT_CODE_TEMPLATES['struct_init'].substitute(
                var_name=var_name
            ).rstrip('\n')

        init_value = getattr(var, 'default_value', '') or \
            self.DEFAULT_INIT_VALUES.get(var_type, '0')
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
    # 公開 API
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