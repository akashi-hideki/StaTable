# codegen/timer_generator.py
"""
タイマ変数生成モジュール（完全データ駆動版）
"""

import sys
import os
import logging
from typing import Dict, Callable, List, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statable.global_defs import TimerBaseDef, TimerDerivedDef, GlobalDefinitions

try:
    from .type_mapper import CTypeMapper
    from .naming_convention import CNamingConvention
    from .code_templates import CodeTemplates
except ImportError:
    from type_mapper import CTypeMapper
    from naming_convention import CNamingConvention
    from code_templates import CodeTemplates

logger = logging.getLogger(__name__)


class TimerGenerator:
    """タイマ変数生成クラス（完全データ駆動）"""
    
    def __init__(self):
        self.mapper = CTypeMapper()
        self.naming = CNamingConvention()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        
        # 生成ステップ
        self.timer_struct_steps = [
            {'action': 'comment'},
            {'action': 'struct_start'},
            {'action': 'members'},
            {'action': 'struct_end'},
        ]
        
        self.step_executors: Dict[str, Callable] = {
            'comment': self._execute_comment_step,
            'struct_start': self._execute_struct_start_step,
            'members': self._execute_members_step,
            'struct_end': self._execute_struct_end_step,
        }
    
    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)
    
    def _execute_comment_step(self, step, context):
        return ["/* タイマ変数構造体 */"]
    
    def _execute_struct_start_step(self, step, context):
        return ["typedef struct {"]
    
    def _execute_members_step(self, step, context):
        global_defs = context.get('global_defs')
        indent = self.strings['indent_1']
        lines = []
        
        # 基準タイマ
        timer_base = getattr(global_defs, 'timer_base', None)
        if timer_base:
            var_name = self.naming.sanitize_identifier(getattr(timer_base, 'variable_name', 'g_system_tick'))
            data_type = self.mapper.map_type(getattr(timer_base, 'data_type', 'uint32_t'))
            lines.append(f"{indent}{data_type} {var_name};")
        
        # 追加タイマ
        for timer in getattr(global_defs, 'extra_timers', []):
            var_name = self.naming.sanitize_identifier(getattr(timer, 'variable_name', 'unknown'))
            data_type = self.mapper.map_type(getattr(timer, 'data_type', 'uint32_t'))
            lines.append(f"{indent}{data_type} {var_name};")
        
        # 派生タイマ
        for timer in [timer_base] + list(getattr(global_defs, 'extra_timers', [])):
            if timer is None:
                continue
            for derived in getattr(timer, 'derived', []):
                var_name = self.naming.sanitize_identifier(getattr(derived, 'variable_name', 'unknown'))
                data_type = self.mapper.map_type(getattr(derived, 'data_type', 'uint8_t'))
                lines.append(f"{indent}{data_type} {var_name};")
        
        return lines
    
    def _execute_struct_end_step(self, step, context):
        return ["} TimerVariables_t;"]
    
    def generate_struct(self, global_defs: GlobalDefinitions) -> str:
        """タイマ変数構造体生成"""
        self._log_debug("Generating timer struct")
        context = {'global_defs': global_defs}
        lines = []
        for step in self.timer_struct_steps:
            executor = self.step_executors.get(step['action'])
            if executor:
                lines.extend(executor(step, context))
        return '\n'.join(lines)
    
    def generate_init_function(self, global_defs: GlobalDefinitions) -> str:
        """タイマ初期化関数生成"""
        self._log_debug("Generating timer init function")
        indent = self.strings['indent_1']
        lines = []
        
        lines.append("/**")
        lines.append(" * @brief  タイマ変数初期化")
        lines.append(" * @param  ctx  システムコンテキストポインタ")
        lines.append(" */")
        lines.append("void Timer_Init(SystemContext_t *ctx)")
        lines.append("{")
        lines.append(f"{indent}if (ctx == NULL) {{")
        lines.append(f"{indent}{indent}return;")
        lines.append(f"{indent}}}")
        lines.append("")
        
        timer_base = getattr(global_defs, 'timer_base', None)
        if timer_base:
            var_name = self.naming.sanitize_identifier(getattr(timer_base, 'variable_name', 'g_system_tick'))
            lines.append(f"{indent}ctx->data.{var_name} = 0;")
        
        for timer in getattr(global_defs, 'extra_timers', []):
            var_name = self.naming.sanitize_identifier(getattr(timer, 'variable_name', 'unknown'))
            lines.append(f"{indent}ctx->data.{var_name} = 0;")
        
        lines.append("}")
        return '\n'.join(lines)