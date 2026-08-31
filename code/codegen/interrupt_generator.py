# codegen/interrupt_generator.py
"""
割り込み処理ISR骨格生成モジュール（完全データ駆動版）
"""

import sys
import os
import logging
from typing import Dict, Callable, List, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statable.global_defs import InterruptHandlerDef, InterruptAction, GlobalDefinitions

try:
    from .naming_convention import CNamingConvention
    from .code_templates import CodeTemplates
except ImportError:
    from naming_convention import CNamingConvention
    from code_templates import CodeTemplates

logger = logging.getLogger(__name__)


class InterruptGenerator:
    """割り込み処理ISR骨格生成クラス（完全データ駆動）"""
    
    def __init__(self):
        self.naming = CNamingConvention()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        
        # 生成ステップ
        self.isr_steps = [
            {'action': 'comment'},
            {'action': 'signature'},
            {'action': 'open'},
            {'action': 'body'},
            {'action': 'close'},
        ]
        
        self.step_executors: Dict[str, Callable] = {
            'comment': self._execute_comment_step,
            'signature': self._execute_signature_step,
            'open': self._execute_open_step,
            'body': self._execute_body_step,
            'close': self._execute_close_step,
        }
    
    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)
    
    def _execute_comment_step(self, step, context):
        handler = context.get('handler')
        return [f"/* 割り込み処理: {getattr(handler, 'name', 'unknown')} */"]
    
    def _execute_signature_step(self, step, context):
        handler = context.get('handler')
        func_name = f"ISR_{self.naming.to_pascal_case(getattr(handler, 'name', ''))}"
        return [f"void {func_name}(void)"]
    
    def _execute_open_step(self, step, context):
        return ["{"]
    
    def _execute_body_step(self, step, context):
        handler = context.get('handler')
        indent = self.strings['indent_1']
        lines = []
        
        # デバッグログ
        lines.append(f"{indent}{self.strings['log_debug']}(\"Enter ISR\");")
        lines.append("")
        
        # アクション
        for action in getattr(handler, 'actions', []):
            condition = getattr(action, 'condition', '')
            act = getattr(action, 'action', '')
            if condition:
                lines.append(f"{indent}if ({condition}) {{")
                lines.append(f"{indent}{indent}{act};")
                lines.append(f"{indent}}}")
            else:
                if act:
                    lines.append(f"{indent}{act};")
        
        lines.append("")
        lines.append(f"{indent}{self.strings['log_debug']}(\"Exit ISR\");")
        return lines
    
    def _execute_close_step(self, step, context):
        return ["}"]
    
    def generate_isr(self, handler: InterruptHandlerDef) -> str:
        """ISR骨格生成"""
        self._log_debug(f"Generating ISR for: {handler.name}")
        context = {'handler': handler}
        lines = []
        for step in self.isr_steps:
            executor = self.step_executors.get(step['action'])
            if executor:
                lines.extend(executor(step, context))
        return '\n'.join(lines)
    
    def generate_all_isrs(self, global_defs: GlobalDefinitions) -> str:
        """全ISR骨格生成"""
        lines = []
        for handler in getattr(global_defs, 'interrupts', []):
            lines.append(self.generate_isr(handler))
            lines.append("")
        return '\n'.join(lines)