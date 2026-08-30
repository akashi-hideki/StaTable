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
    
    def _detect_member_type(self, member):
        for member_type, detector in self.member_type_detectors.items():
            if detector(member):
                return member_type
        return 'normal'
    
    def _generate_bit_field(self, member, name, c_type, indent):
        width = getattr(member, 'bit_width', 0)
        return f"{indent}{c_type} {name} : {width};"
    
    def _generate_array(self, member, name, c_type, indent):
        size = getattr(member, 'array_size', 0)
        return f"{indent}{c_type} {name}[{size}];"
    
    def _generate_normal(self, member, name, c_type, indent):
        return f"{indent}{c_type} {name};"
    
    def _generate_member(self, member):
        member_type = self._detect_member_type(member)
        generator = self.member_generators[member_type]
        member_name = self.naming.sanitize_identifier(getattr(member, 'name', 'unnamed'))
        c_type = self.mapper.map_type(getattr(member, 'data_type', 'void'))
        indent = self.strings['indent_1']
        return generator(member, member_name, c_type, indent)
    
    def _execute_struct_comment_step(self, step, context):
        struct_def = context.get('struct_def')
        lines = []
        if getattr(struct_def, 'description', ''):
            lines.append(f"/* {struct_def.description} */")
        if getattr(struct_def, 'title', '') and struct_def.title != getattr(struct_def, 'name', ''):
            lines.append(f"/* Title: {struct_def.title} */")
        return lines
    
    def _execute_fixed_comment_step(self, step, context):
        key = step.get('key', '')
        comment = self.templates.STRUCT_COMMENTS.get(key, {})
        return [
            f"/* {comment.get('title', '')} */",
            f"/* {comment.get('description', '')} */",
        ]
    
    def _execute_struct_start_step(self, step, context):
        return ["typedef struct {"]
    
    def _execute_loop_members_step(self, step, context):
        struct_def = context.get('struct_def')
        lines = []
        for member in getattr(struct_def, 'members', []):
            if getattr(member, 'description', ''):
                indent = self.strings['indent_1']
                lines.append(f"{indent}/* {member.description} */")
            if getattr(member, 'title', '') and member.title != getattr(member, 'name', ''):
                indent = self.strings['indent_1']
                lines.append(f"{indent}/* Title: {member.title} */")
            lines.append(self._generate_member(member))
        return lines
    
    def _execute_loop_variables_step(self, step, context):
        global_defs = context.get('global_defs')
        lines = []
        current_group = None
        indent = self.strings['indent_1']
        
        for var in getattr(global_defs, 'variables', []):
            if getattr(var, 'group', '') and var.group != current_group:
                if current_group is not None:
                    lines.append("")
                lines.append(f"{indent}/* === {var.group} === */")
                current_group = var.group
            
            comments = []
            if getattr(var, 'description', ''):
                comments.append(var.description)
            if getattr(var, 'unit', ''):
                comments.append(f"[{var.unit}]")
            if comments:
                lines.append(f"{indent}/* {' '.join(comments)} */")
            
            var_name = self.naming.sanitize_identifier(getattr(var, 'name', 'unnamed'))
            c_type = self.mapper.map_type(getattr(var, 'type', 'void'))
            
            if getattr(var, 'array_size', 0) > 0:
                lines.append(f"{indent}{c_type} {var_name}[{var.array_size}];")
            else:
                lines.append(f"{indent}{c_type} {var_name};")
        
        return lines
    
    def _execute_loop_flags_step(self, step, context):
        global_defs = context.get('global_defs')
        lines = []
        current_group = None
        indent = self.strings['indent_1']
        
        for flag in getattr(global_defs, 'flags', []):
            if getattr(flag, 'group', '') and flag.group != current_group:
                if current_group is not None:
                    lines.append("")
                lines.append(f"{indent}/* === {flag.group} === */")
                current_group = flag.group
            
            if getattr(flag, 'description', ''):
                lines.append(f"{indent}/* {flag.description} */")
            
            flag_name = self.naming.sanitize_identifier(getattr(flag, 'name', 'unnamed'))
            lines.append(f"{indent}uint8_t {flag_name};")
        
        return lines
    
    def _execute_context_members_step(self, step, context):
        indent = self.strings['indent_1']
        return [
            f"{indent}{self.templates.TYPE_NAMES['system_data']} data;     /* グローバル変数 */",
            f"{indent}{self.templates.TYPE_NAMES['event_flags']} flags;    /* イベントフラグ */",
        ]
    
    def _execute_struct_end_step(self, step, context):
        struct_def = context.get('struct_def')
        type_name = self.naming.create_type_name(getattr(struct_def, 'name', 'Unknown'))
        return [f"}} {type_name};"]
    
    def _execute_struct_end_fixed_step(self, step, context):
        type_name_key = step.get('type_name', '')
        type_name = self.templates.TYPE_NAMES.get(type_name_key, 'Unknown_t')
        return [f"}} {type_name};"]
    
    def _generate_custom_type(self, struct_def):
        self._log_debug(f"Generating custom type: {getattr(struct_def, 'name', 'unknown')}")
        context = {'struct_def': struct_def}
        lines = []
        for step in self.struct_steps['custom_type']:
            executor = self.step_executors.get(step['action'])
            if executor:
                lines.extend(executor(step, context))
        return '\n'.join(lines)
    
    def _generate_system_data(self, global_defs):
        self._log_debug("Generating system data struct")
        context = {'global_defs': global_defs}
        lines = []
        for step in self.struct_steps['system_data']:
            executor = self.step_executors.get(step['action'])
            if executor:
                lines.extend(executor(step, context))
        return '\n'.join(lines)
    
    def _generate_event_flags(self, global_defs):
        self._log_debug("Generating event flags struct")
        context = {'global_defs': global_defs}
        lines = []
        for step in self.struct_steps['event_flags']:
            executor = self.step_executors.get(step['action'])
            if executor:
                lines.extend(executor(step, context))
        return '\n'.join(lines)
    
    def _generate_system_context(self, global_defs):
        self._log_debug("Generating system context struct")
        context = {'global_defs': global_defs}
        lines = []
        for step in self.struct_steps['system_context']:
            executor = self.step_executors.get(step['action'])
            if executor:
                lines.extend(executor(step, context))
        return '\n'.join(lines)
    
    def generate_struct(self, struct_type, item):
        generator = self.struct_generators.get(struct_type)
        if generator:
            return generator(item)
        raise ValueError(f"Unknown struct type: {struct_type}")
    
    def generate_all_structs(self, global_defs):
        lines = []
        if getattr(global_defs, 'custom_types', []):
            line = self.strings['section_line']
            title = self.templates.SECTION_HEADERS['custom_types']
            lines.append(f"{line}\n *  {title}\n{line}")
            lines.append("")
            for custom_type in global_defs.custom_types:
                lines.append(self.generate_struct('custom_type', custom_type))
                lines.append("")
        
        line = self.strings['section_line']
        title = self.templates.SECTION_HEADERS['system_structs']
        lines.append(f"{line}\n *  {title}\n{line}")
        lines.append("")
        lines.append(self.generate_struct('system_data', global_defs))
        lines.append("")
        lines.append(self.generate_struct('event_flags', global_defs))
        lines.append("")
        lines.append(self.generate_struct('system_context', global_defs))
        
        return '\n'.join(lines)