# codegen/struct_generator.py
"""
C構造体コード生成モジュール（完全データ駆動版）
"""

import sys
import os
import logging
from typing import Dict, Callable, List, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statable.global_defs import StructMemberDef, CustomTypeDef, GlobalDefinitions

try:
    from .type_mapper import CTypeMapper
    from .naming_convention import CNamingConvention
    from .code_templates import CodeTemplates
except ImportError:
    from type_mapper import CTypeMapper
    from naming_convention import CNamingConvention
    from code_templates import CodeTemplates

logger = logging.getLogger(__name__)


class CStructGenerator:
    """C構造体コード生成クラス（完全データ駆動）"""
    
    def __init__(self):
        self.mapper = CTypeMapper()
        self.naming = CNamingConvention()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        
        self.member_type_detectors = {
            'bit_field': lambda m: getattr(m, 'bit_width', 0) > 0,
            'array': lambda m: getattr(m, 'array_size', 0) > 0,
            'normal': lambda m: True,
        }
        
        self.member_generators = {
            'bit_field': self._generate_bit_field,
            'array': self._generate_array,
            'normal': self._generate_normal,
        }
        
        self.struct_generators = {
            'custom_type': self._generate_custom_type,
            'system_data': self._generate_system_data,
            'event_flags': self._generate_event_flags,
            'system_context': self._generate_system_context,
        }
        
        self.struct_steps = {
            'custom_type': [
                {'action': 'struct_comment'},
                {'action': 'struct_start'},
                {'action': 'loop_members'},
                {'action': 'struct_end'},
            ],
            'system_data': [
                {'action': 'fixed_comment', 'key': 'system_data'},
                {'action': 'struct_start'},
                {'action': 'loop_variables'},
                {'action': 'struct_end_fixed', 'type_name': 'system_data'},
            ],
            'event_flags': [
                {'action': 'fixed_comment', 'key': 'event_flags'},
                {'action': 'struct_start'},
                {'action': 'loop_flags'},
                {'action': 'struct_end_fixed', 'type_name': 'event_flags'},
            ],
            'system_context': [
                {'action': 'fixed_comment', 'key': 'system_context'},
                {'action': 'struct_start'},
                {'action': 'context_members'},
                {'action': 'struct_end_fixed', 'type_name': 'system_context'},
            ],
        }
        
        self.step_executors: Dict[str, Callable] = {
            'struct_comment': self._execute_struct_comment_step,
            'fixed_comment': self._execute_fixed_comment_step,
            'struct_start': self._execute_struct_start_step,
            'loop_members': self._execute_loop_members_step,
            'loop_variables': self._execute_loop_variables_step,
            'loop_flags': self._execute_loop_flags_step,
            'context_members': self._execute_context_members_step,
            'struct_end': self._execute_struct_end_step,
            'struct_end_fixed': self._execute_struct_end_fixed_step,
        }
    
    def _log_debug(self, message: str, level: str = 'debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)
    
    def _detect_member_type(self, member: StructMemberDef) -> str:
        for member_type, detector in self.member_type_detectors.items():
            if detector(member):
                return member_type
        return 'normal'
    
    def _generate_bit_field(self, member, name, c_type, indent):
        return self.formats['member_bitfield'].format(
            indent=indent, type=c_type, name=name, width=getattr(member, 'bit_width', 0)
        )
    
    def _generate_array(self, member, name, c_type, indent):
        return self.formats['member_array'].format(
            indent=indent, type=c_type, name=name, size=getattr(member, 'array_size', 0)
        )
    
    def _generate_normal(self, member, name, c_type, indent):
        return self.formats['member_normal'].format(
            indent=indent, type=c_type, name=name
        )
    
    def _generate_member(self, member: StructMemberDef) -> str:
        member_type = self._detect_member_type(member)
        generator = self.member_generators[member_type]
        member_name = self.naming.sanitize_identifier(member.name)
        c_type = self.mapper.map_type(getattr(member, 'data_type', 'void'))
        indent = self.strings['indent_1']
        return generator(member, member_name, c_type, indent)
    
    # ===== ステップ実行関数 =====
    def _execute_struct_comment_step(self, step: Dict, context: Dict) -> List[str]:
        struct_def = context['struct_def']
        lines = []
        if getattr(struct_def, 'description', ''):
            lines.append(f"/* {struct_def.description} */")
        if getattr(struct_def, 'title', '') and struct_def.title != struct_def.name:
            lines.append(f"/* Title: {struct_def.title} */")
        return lines
    
    def _execute_fixed_comment_step(self, step: Dict, context: Dict) -> List[str]:
        key = step.get('key', '')
        comment = self.templates.STRUCT_COMMENTS.get(key, {})
        return [
            f"/* {comment.get('title', '')} */",
            f"/* {comment.get('description', '')} */",
        ]
    
    def _execute_struct_start_step(self, step: Dict, context: Dict) -> List[str]:
        return [self.formats['struct_start']]
    
    def _execute_loop_members_step(self, step: Dict, context: Dict) -> List[str]:
        struct_def = context['struct_def']
        lines = []
        
        for member in getattr(struct_def, 'members', []):
            if getattr(member, 'description', ''):
                lines.append(self.formats['inline_comment'].format(
                    indent=self.strings['indent_1'], comment=member.description
                ))
            if getattr(member, 'title', '') and member.title != member.name:
                lines.append(self.formats['title_comment'].format(
                    indent=self.strings['indent_1'], title=member.title
                ))
            lines.append(self._generate_member(member))
        
        return lines
    
    def _execute_loop_variables_step(self, step: Dict, context: Dict) -> List[str]:
        global_defs = context['global_defs']
        lines = []
        current_group = None
        
        for var in getattr(global_defs, 'variables', []):
            if getattr(var, 'group', '') and var.group != current_group:
                if current_group is not None:
                    lines.append("")
                group_sep = self.formats['group_separator'].format(group_name=var.group)
                lines.append(f"{self.strings['indent_1']}{group_sep}")
                current_group = var.group
            
            comments = []
            if getattr(var, 'description', ''):
                comments.append(var.description)
            if getattr(var, 'unit', ''):
                comments.append(f"[{var.unit}]")
            if comments:
                lines.append(self.formats['inline_comment'].format(
                    indent=self.strings['indent_1'], comment=' '.join(comments)
                ))
            
            var_name = self.naming.sanitize_identifier(var.name)
            c_type = self.mapper.map_type(getattr(var, 'type', 'void'))
            
            if getattr(var, 'array_size', 0) > 0:
                lines.append(self.formats['member_array'].format(
                    indent=self.strings['indent_1'], type=c_type, name=var_name, size=var.array_size
                ))
            else:
                lines.append(self.formats['member_normal'].format(
                    indent=self.strings['indent_1'], type=c_type, name=var_name
                ))
        
        return lines
    
    def _execute_loop_flags_step(self, step: Dict, context: Dict) -> List[str]:
        global_defs = context['global_defs']
        lines = []
        current_group = None
        
        for flag in getattr(global_defs, 'flags', []):
            if getattr(flag, 'group', '') and flag.group != current_group:
                if current_group is not None:
                    lines.append("")
                group_sep = self.formats['group_separator'].format(group_name=flag.group)
                lines.append(f"{self.strings['indent_1']}{group_sep}")
                current_group = flag.group
            
            if getattr(flag, 'description', ''):
                lines.append(self.formats['inline_comment'].format(
                    indent=self.strings['indent_1'], comment=flag.description
                ))
            
            flag_name = self.naming.sanitize_identifier(flag.name)
            lines.append(self.formats['member_normal'].format(
                indent=self.strings['indent_1'], type='uint8_t', name=flag_name
            ))
        
        return lines
    
    def _execute_context_members_step(self, step: Dict, context: Dict) -> List[str]:
        return [
            f"{self.strings['indent_1']}{self.templates.TYPE_NAMES['system_data']} data;     /* グローバル変数 */",
            f"{self.strings['indent_1']}{self.templates.TYPE_NAMES['event_flags']} flags;    /* イベントフラグ */",
        ]
    
    def _execute_struct_end_step(self, step: Dict, context: Dict) -> List[str]:
        struct_def = context['struct_def']
        type_name = self.naming.create_type_name(struct_def.name)
        return [self.formats['struct_end'].format(type_name=type_name)]
    
    def _execute_struct_end_fixed_step(self, step: Dict, context: Dict) -> List[str]:
        type_name_key = step.get('type_name', '')
        type_name = self.templates.TYPE_NAMES.get(type_name_key, 'Unknown_t')
        return [self.formats['struct_end'].format(type_name=type_name)]
    
    # ===== 構造体生成 =====
    def _generate_custom_type(self, struct_def: CustomTypeDef) -> str:
        self._log_debug(f"Generating custom type: {struct_def.name}")
        context = {'struct_def': struct_def}
        steps = self.struct_steps['custom_type']
        lines = []
        for step in steps:
            executor = self.step_executors.get(step['action'])
            if executor:
                lines.extend(executor(step, context))
        return '\n'.join(lines)
    
    def _generate_system_data(self, global_defs: GlobalDefinitions) -> str:
        self._log_debug("Generating system data struct")
        context = {'global_defs': global_defs}
        steps = self.struct_steps['system_data']
        lines = []
        for step in steps:
            executor = self.step_executors.get(step['action'])
            if executor:
                lines.extend(executor(step, context))
        return '\n'.join(lines)
    
    def _generate_event_flags(self, global_defs: GlobalDefinitions) -> str:
        self._log_debug("Generating event flags struct")
        context = {'global_defs': global_defs}
        steps = self.struct_steps['event_flags']
        lines = []
        for step in steps:
            executor = self.step_executors.get(step['action'])
            if executor:
                lines.extend(executor(step, context))
        return '\n'.join(lines)
    
    def _generate_system_context(self, global_defs: GlobalDefinitions) -> str:
        self._log_debug("Generating system context struct")
        context = {'global_defs': global_defs}
        steps = self.struct_steps['system_context']
        lines = []
        for step in steps:
            executor = self.step_executors.get(step['action'])
            if executor:
                lines.extend(executor(step, context))
        return '\n'.join(lines)
    
    def generate_struct(self, struct_type: str, item) -> str:
        generator = self.struct_generators.get(struct_type)
        if generator:
            return generator(item)
        raise ValueError(f"Unknown struct type: {struct_type}")
    
    def generate_all_structs(self, global_defs: GlobalDefinitions) -> str:
        lines = []
        if global_defs.custom_types:
            line = self.strings['section_line']
            title = self.templates.SECTION_HEADERS['custom_types']
            lines.append(self.formats['section_header'].format(line=line, title=title))
            lines.append("")
            for custom_type in global_defs.custom_types:
                lines.append(self.generate_struct('custom_type', custom_type))
                lines.append("")
        
        line = self.strings['section_line']
        title = self.templates.SECTION_HEADERS['system_structs']
        lines.append(self.formats['section_header'].format(line=line, title=title))
        lines.append("")
        lines.append(self.generate_struct('system_data', global_defs))
        lines.append("")
        lines.append(self.generate_struct('event_flags', global_defs))
        lines.append("")
        lines.append(self.generate_struct('system_context', global_defs))
        
        return '\n'.join(lines)