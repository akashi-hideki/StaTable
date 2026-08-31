# codegen/event_queue_generator.py
"""
イベントキューコード生成モジュール（完全データ駆動版）
"""

import sys
import os
import logging
from typing import Dict, Callable, List, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statable.global_defs import EventQueueDef, GlobalDefinitions

try:
    from .type_mapper import CTypeMapper
    from .naming_convention import CNamingConvention
    from .code_templates import CodeTemplates
except ImportError:
    from type_mapper import CTypeMapper
    from naming_convention import CNamingConvention
    from code_templates import CodeTemplates

logger = logging.getLogger(__name__)


class EventQueueGenerator:
    """イベントキューコード生成クラス（完全データ駆動）"""
    
    def __init__(self):
        self.mapper = CTypeMapper()
        self.naming = CNamingConvention()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        
        # 生成ステップ定義
        self.struct_steps = [
            {'action': 'comment'},
            {'action': 'struct_start'},
            {'action': 'members'},
            {'action': 'struct_end'},
        ]
        
        self.function_steps = [
            {'action': 'comment'},
            {'action': 'signature'},
            {'action': 'body'},
            {'action': 'close'},
        ]
        
        # ステップ実行辞書
        self.step_executors: Dict[str, Callable] = {
            'comment': self._execute_comment_step,
            'struct_start': self._execute_struct_start_step,
            'members': self._execute_members_step,
            'struct_end': self._execute_struct_end_step,
            'signature': self._execute_signature_step,
            'body': self._execute_body_step,
            'close': self._execute_close_step,
        }
    
    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)
    
    def _sanitize_name(self, name):
        return self.naming.sanitize_identifier(name)
    
    def _generate_struct_name(self, queue):
        return self.naming.create_type_name(getattr(queue, 'name', 'EventQueue'))
    
    def _execute_comment_step(self, step, context):
        queue = context.get('queue')
        return [f"/* イベントキュー: {getattr(queue, 'name', 'unknown')} */"]
    
    def _execute_struct_start_step(self, step, context):
        return ["typedef struct {"]
    
    def _execute_members_step(self, step, context):
        queue = context.get('queue')
        indent = self.strings['indent_1']
        lines = []
        
        # キュー名
        lines.append(f"{indent}uint8_t buffer[{getattr(queue, 'size', 0)}];")
        lines.append(f"{indent}uint8_t head;")
        lines.append(f"{indent}uint8_t tail;")
        lines.append(f"{indent}uint8_t count;")
        
        return lines
    
    def _execute_struct_end_step(self, step, context):
        queue = context.get('queue')
        type_name = self._generate_struct_name(queue)
        return [f"}} {type_name};"]
    
    def _execute_signature_step(self, step, context):
        queue = context.get('queue')
        type_name = self._generate_struct_name(queue)
        func_suffix = step.get('suffix', '')
        return [f"void EventQueue_{self.naming.to_pascal_case(getattr(queue, 'name', ''))}{func_suffix}({type_name} *queue)"]
    
    def _execute_body_step(self, step, context):
        indent = self.strings['indent_1']
        return [f"{indent}/* TODO: 実装 */"]
    
    def _execute_close_step(self, step, context):
        return ["}"]
    
    def generate_struct(self, queue: EventQueueDef) -> str:
        """イベントキュー構造体生成"""
        self._log_debug(f"Generating struct for queue: {queue.name}")
        context = {'queue': queue}
        lines = []
        for step in self.struct_steps:
            executor = self.step_executors.get(step['action'])
            if executor:
                lines.extend(executor(step, context))
        return '\n'.join(lines)
    
    def generate_all_structs(self, global_defs: GlobalDefinitions) -> str:
        """全イベントキュー構造体生成"""
        lines = []
        for queue in getattr(global_defs, 'event_queues', []):
            lines.append(self.generate_struct(queue))
            lines.append("")
        return '\n'.join(lines)


# 簡略版：実際にはさらに詳細な関数生成が必要