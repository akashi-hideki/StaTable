# codegen/enum_generator.py
"""
C列挙型コード生成モジュール（完全データ駆動版）
"""

import sys
import os
import logging
from typing import Dict, Callable, List, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statable.model import State, Event, StateType, EventKind
from statable.global_defs import EventFlag

try:
    from .naming_convention import CNamingConvention
    from .code_templates import CodeTemplates
except ImportError:
    from naming_convention import CNamingConvention
    from code_templates import CodeTemplates

logger = logging.getLogger(__name__)


class CEnumGenerator:
    """C列挙型コード生成クラス（完全データ駆動）"""
    
    def __init__(self):
        self.naming = CNamingConvention()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        
        self.enum_configs: Dict[str, Dict] = {
            'state': {
                'prefix': 'STATE',
                'type_name': 'STATE_t',
                'max_name': 'STATE_MAX',
                'comment_key': 'state',
                'comment_generator': self._generate_state_comment,
            },
            'event': {
                'prefix': 'EVENT',
                'type_name': 'EVENT_t',
                'max_name': 'EVENT_MAX',
                'comment_key': 'event',
                'comment_generator': self._generate_event_comment,
            },
            'flag': {
                'prefix': 'FLAG',
                'type_name': 'FLAG_t',
                'max_name': 'FLAG_MAX',
                'comment_key': 'flag',
                'comment_generator': self._generate_flag_comment,
            },
        }
        
        self.enum_steps = [
            {'action': 'comment'},
            {'action': 'enum_start'},
            {'action': 'loop_values'},
            {'action': 'blank'},
            {'action': 'max_value'},
            {'action': 'enum_end'},
        ]
        
        self.step_executors: Dict[str, Callable] = {
            'comment': self._execute_comment_step,
            'enum_start': self._execute_enum_start_step,
            'loop_values': self._execute_loop_values_step,
            'blank': self._execute_blank_step,
            'max_value': self._execute_max_value_step,
            'enum_end': self._execute_enum_end_step,
        }
    
    def _log_debug(self, message: str, level: str = 'debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)
    
    def _generate_state_comment(self, state):
        comments = []
        if getattr(state, 'description', ''):
            comments.append(state.description)
        if getattr(state, 'type', None) and state.type != StateType.NORMAL:
            comments.append(f"Type: {state.type.name}")
        if getattr(state, 'title', ''):
            comments.append(f"Title: {state.title}")
        return ' '.join(comments)
    
    def _generate_event_comment(self, event):
        comments = []
        if getattr(event, 'description', ''):
            comments.append(event.description)
        if getattr(event, 'kind', None) and event.kind != EventKind.SIGNAL:
            comments.append(f"Kind: {event.kind.name}")
        if getattr(event, 'title', ''):
            comments.append(f"Title: {event.title}")
        return ' '.join(comments)
    
    def _generate_flag_comment(self, flag):
        comments = []
        if getattr(flag, 'description', ''):
            comments.append(flag.description)
        if getattr(flag, 'title', ''):
            comments.append(f"Title: {flag.title}")
        return ' '.join(comments)
    
    def _execute_comment_step(self, step, context):
        config = context['config']
        enum_comment = self.templates.ENUM_COMMENTS[config['comment_key']]
        return [
            f"/* {enum_comment['title']} */",
            f"/* {enum_comment['description']} */",
        ]
    
    def _execute_enum_start_step(self, step, context):
        return ["typedef enum {"]
    
    def _execute_loop_values_step(self, step, context):
        items = context['items']
        config = context['config']
        lines = []
        for i, item in enumerate(items):
            item_name = self.naming.create_enum_value(config['prefix'], getattr(item, 'name', 'unnamed'))
            comment = config['comment_generator'](item)
            if comment:
                lines.append(f"    {item_name} = {i},    /* {comment} */")
            else:
                lines.append(f"    {item_name} = {i},")
        return lines
    
    def _execute_blank_step(self, step, context):
        return [""]
    
    def _execute_max_value_step(self, step, context):
        config = context['config']
        return [f"    {config['max_name']}           /* 要素数（システム用） */"]
    
    def _execute_enum_end_step(self, step, context):
        config = context['config']
        return [f"}} {config['type_name']};"]
    
    def _generate_enum(self, enum_type, items):
        self._log_debug(f"Generating enum: {enum_type}")
        config = self.enum_configs.get(enum_type)
        if not config or not items:
            return ""
        context = {'config': config, 'items': items}
        lines = []
        for step in self.enum_steps:
            executor = self.step_executors.get(step['action'])
            if executor:
                lines.extend(executor(step, context))
        return '\n'.join(lines)
    
    def generate_enum(self, enum_type, items):
        return self._generate_enum(enum_type, items)
    
    def generate_all_enums(self, states, events, flags):
        lines = []
        lines.append(self.generate_enum('state', states))
        lines.append("")
        lines.append(self.generate_enum('event', events))
        if flags:
            lines.append("")
            lines.append(self.generate_enum('flag', flags))
        return '\n'.join(lines)
    
    def generate_bit_mask_enum(self, flags):
        if not flags:
            return ""
        lines = []
        lines.append("/* イベントフラグビットマスク定義 */")
        lines.append("/* ビット単位でフラグを管理する場合に使用 */")
        lines.append("typedef enum {")
        for i, flag in enumerate(flags):
            flag_name = self.naming.create_enum_value("FLAG_MASK", getattr(flag, 'name', 'unnamed'))
            bit_value = 1 << i
            if getattr(flag, 'description', ''):
                lines.append(f"    {flag_name} = 0x{bit_value:02X},    /* {flag.description} */")
            else:
                lines.append(f"    {flag_name} = 0x{bit_value:02X},")
        lines.append("} FLAG_MASK_t;")
        return '\n'.join(lines)