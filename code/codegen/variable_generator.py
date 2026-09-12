# codegen/variable_generator.py
"""
変数・フラグ生成モジュール（多層ステートマシン対応版）

生成するもの:
  1. 変数アクセスマクロ (DATA_<VAR> / FLAG_<FLAG>)
  2. SystemContext_Init() 関数
     - グローバル変数の初期化
     - イベントフラグの初期化
     - ★ 保留イベントの初期化 (pending_event / pending_event_valid)
"""

import sys
import os
import logging
from string import Template
from typing import Dict, Callable, List, Any, Optional

# ======================================================================
# パス設定（どこから実行されても動作するように）
# ======================================================================
_this_dir = os.path.dirname(os.path.abspath(__file__))         # codegen/
_parent_dir = os.path.dirname(_this_dir)                       # code/
for _p in (_this_dir, _parent_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ======================================================================
# インポート
# ======================================================================
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

    # ==================================================================
    # 【データテーブル①】初期化関数テンプレート
    # ==================================================================
    INIT_TEMPLATES = {
        # --- 関数コメント ---
        'comment': (
            '/**\n'
            ' * @brief  システムコンテキスト初期化\n'
            ' * @param  ctx  システムコンテキストポインタ\n'
            ' */\n'
        ),

        # --- 関数シグネチャ ---
        'signature': Template(
            'void $func_name(SystemContext_t *ctx)\n'
        ),

        # --- 関数開始 ---
        'function_open': (
            '{\n'
        ),

        # --- NULL チェック ---
        'null_check': Template(
            '    /* NULLチェック */\n'
            '    if (ctx == NULL) {\n'
            '        $log_error("NULL pointer: ctx");\n'
            '        return;\n'
            '    }\n'
        ),

        # --- エントリログ ---
        'entry_log': Template(
            '    $log_debug("Enter $func_name");\n'
        ),

        # --- 変数初期化セクションコメント ---
        'variables_comment': (
            '    /* グローバル変数の初期化 */\n'
        ),

        # --- フラグ初期化セクションコメント ---
        'flags_comment': (
            '    /* イベントフラグの初期化 */\n'
        ),

        # --- ★ 保留イベント初期化セクションコメント ---
        'pending_event_comment': (
            '    /* 保留イベントの初期化 */\n'
        ),

        # --- ★ 保留イベント初期化 ---
        'pending_event_init': (
            '    ctx->pending_event = 0;\n'
            '    ctx->pending_event_valid = false;\n'
        ),

        # --- エグジットログ ---
        'exit_log': Template(
            '    $log_debug("Exit $func_name");\n'
        ),

        # --- 関数終了 ---
        'function_close': (
            '}\n'
        ),
    }

    # ==================================================================
    # 【データテーブル②】初期化関数のステップ
    # ==================================================================
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
        # ★ 保留イベントの初期化
        {'action': 'template', 'key': 'pending_event_comment'},
        {'action': 'template', 'key': 'pending_event_init'},
        {'action': 'blank'},
        {'action': 'template', 'key': 'exit_log',
         'format': {'func_name': '{func_name}', 'log_debug': '{log_debug}'}},
        {'action': 'template', 'key': 'function_close'},
    ]

    # ==================================================================
    # 【データテーブル③】初期値マッピング
    # ==================================================================
    DEFAULT_INIT_VALUES = {
        'int': '0', 'int8': '0', 'int16': '0', 'int32': '0', 'int64': '0',
        'uint': '0', 'uint8': '0', 'uint16': '0', 'uint32': '0', 'uint64': '0',
        'float': '0.0f', 'double': '0.0', 'bool': 'false',
        'char': '0', 'string': 'NULL',
    }

    # ==================================================================
    # 【データテーブル④】変数アクセスマクロテンプレート
    # ==================================================================
    MACRO_TEMPLATES = {
        'data_macro': Template(
            '#define DATA_$var_name(ctx)    ((ctx)->data.$var_name)\n'
        ),
        'flag_macro': Template(
            '#define FLAG_$flag_name(ctx)   ((ctx)->flags.$flag_name)\n'
        ),
    }

    # ==================================================================
    # 【データテーブル⑤】初期化コードテンプレート
    # ==================================================================
    INIT_CODE_TEMPLATES = {
        'array_init': Template(
            '    memset(ctx->data.$var_name, 0, sizeof(ctx->data.$var_name));\n'
        ),
        'normal_init': Template(
            '    ctx->data.$var_name = $init_value;\n'
        ),
        'flag_init': Template(
            '    ctx->flags.$flag_name = 0;\n'
        ),
    }

    # ==================================================================
    # 【データテーブル⑥】変数種別検出
    # ==================================================================
    VARIABLE_TYPE_DETECTORS = {
        'array': lambda v: getattr(v, 'array_size', 0) > 0,
        'normal': lambda v: True,
    }

    # ==================================================================
    # コンストラクタ
    # ==================================================================
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

    # ==================================================================
    # ヘルパー
    # ==================================================================
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

    # ==================================================================
    # ステップ実行関数
    # ==================================================================
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

    # ==================================================================
    # 変数アクセスマクロ生成
    # ==================================================================
    def _generate_data_macro(self, var) -> str:
        var_name = self.naming.to_upper_snake(getattr(var, 'name', 'unnamed'))
        return self.MACRO_TEMPLATES['data_macro'].substitute(var_name=var_name).rstrip('\n')

    def _generate_flag_macro(self, flag) -> str:
        flag_name = self.naming.to_upper_snake(getattr(flag, 'name', 'unnamed'))
        return self.MACRO_TEMPLATES['flag_macro'].substitute(flag_name=flag_name).rstrip('\n')

    def _generate_access_macro(self, item) -> str:
        item_class = item.__class__.__name__
        if item_class == 'SystemVariable':
            return self._generate_data_macro(item)
        elif item_class == 'EventFlag':
            return self._generate_flag_macro(item)
        return ""

    # ==================================================================
    # 初期化コード生成
    # ==================================================================
    def _generate_array_init(self, var) -> str:
        var_name = self.naming.sanitize_identifier(getattr(var, 'name', 'unnamed'))
        return self.INIT_CODE_TEMPLATES['array_init'].substitute(
            var_name=var_name
        ).rstrip('\n')

    def _generate_normal_init(self, var) -> str:
        var_name = self.naming.sanitize_identifier(getattr(var, 'name', 'unnamed'))
        init_value = getattr(var, 'default_value', '') or \
            self.DEFAULT_INIT_VALUES.get(getattr(var, 'type', 'void'), '0')
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

    # ==================================================================
    # 公開メソッド
    # ==================================================================
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