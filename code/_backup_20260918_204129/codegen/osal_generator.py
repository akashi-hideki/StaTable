# codegen/osal_generator.py
"""\nOSAL (OS abstraction layer) code generation module (template-split version)\n"""

import sys
import os
import logging
from typing import Dict, Callable, List, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .code_templates import CodeTemplates
    from .naming_convention import CNamingConvention
except ImportError:
    from code_templates import CodeTemplates
    from naming_convention import CNamingConvention

logger = logging.getLogger(__name__)


class OSALGenerator:
    """OSAL code generation class (template-split version)"""
    
    def __init__(self):
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        self.osal_templates = self.templates.OSAL
        self.naming = CNamingConvention()
        
        # Header generation step
        self.header_steps = [
            {'action': 'file_comment'},
            {'action': 'include_guard_start'},
            {'action': 'includes'},
            {'action': 'type_defs'},
            {'action': 'mutex_decls'},
            {'action': 'semaphore_decls'},
            {'action': 'queue_decls'},
            {'action': 'critical_decls'},
            {'action': 'include_guard_end'},
        ]
        
        # Source generation step
        self.source_steps = [
            {'action': 'file_comment'},
            {'action': 'includes'},
            {'action': 'mutex_impl'},
            {'action': 'semaphore_impl'},
            {'action': 'queue_impl'},
            {'action': 'critical_impl'},
        ]
        
        # Step execution dictionary
        self.step_executors: Dict[str, Callable] = {
            'file_comment': self._execute_file_comment,
            'include_guard_start': self._execute_include_guard_start,
            'includes': self._execute_includes,
            'type_defs': self._execute_type_defs,
            'mutex_decls': self._execute_mutex_decls,
            'semaphore_decls': self._execute_semaphore_decls,
            'queue_decls': self._execute_queue_decls,
            'critical_decls': self._execute_critical_decls,
            'include_guard_end': self._execute_include_guard_end,
            'mutex_impl': self._execute_mutex_impl,
            'semaphore_impl': self._execute_semaphore_impl,
            'queue_impl': self._execute_queue_impl,
            'critical_impl': self._execute_critical_impl,
        }
    
    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)
    
    # ===== Step execution function =====
    def _execute_file_comment(self, step, context):
        os_type = context.get('os_type', 'non_rtos')
        os_info = self.osal_templates['os_types'].get(os_type, {})
        filename = context.get('filename', 'osal.h')
        os_name = os_info.get('name', 'NonRTOS')
        
        template = self.osal_templates['header']['file_comment']
        return [template.format(filename=filename, os_name=os_name)]
    
    def _execute_include_guard_start(self, step, context):
        guard_name = context.get('guard_name', 'OSAL_H')
        return [self.osal_templates['header']['include_guard_start'].format(guard_name=guard_name)]
    
    def _execute_includes(self, step, context):
        os_type = context.get('os_type', 'non_rtos')
        lines = ["#include <stdint.h>", "#include <stdbool.h>", ""]
        
        if os_type == 'freertos':
            lines.append(self.osal_templates['header']['freertos_includes'])
            lines.append("")
        elif os_type == 'threadx':
            lines.append(self.osal_templates['header']['threadx_includes'])
            lines.append("")
        
        return lines
    
    def _execute_type_defs(self, step, context):
        os_type = context.get('os_type', 'non_rtos')
        lines = []
        
        lines.append(self.osal_templates['header']['type_defs_comment'])
        lines.append(self.osal_templates['header']['status_enum'])
        lines.append("")
        
        if os_type == 'non_rtos':
            lines.append(self.osal_templates['header']['mutex_type_nonrtos'])
            lines.append("")
            lines.append(self.osal_templates['header']['semaphore_type_nonrtos'])
            lines.append("")
            lines.append(self.osal_templates['header']['queue_type_nonrtos'])
            lines.append("")
        
        return lines
    
    def _execute_mutex_decls(self, step, context):
        return [self.osal_templates['header']['mutex_decls'], ""]
    
    def _execute_semaphore_decls(self, step, context):
        return [self.osal_templates['header']['semaphore_decls'], ""]
    
    def _execute_queue_decls(self, step, context):
        return [self.osal_templates['header']['queue_decls'], ""]
    
    def _execute_critical_decls(self, step, context):
        return [self.osal_templates['header']['critical_decls'], ""]
    
    def _execute_include_guard_end(self, step, context):
        guard_name = context.get('guard_name', 'OSAL_H')
        return [self.osal_templates['header']['include_guard_end'].format(guard_name=guard_name)]
    
    def _execute_mutex_impl(self, step, context):
        os_type = context.get('os_type', 'non_rtos')
        lines = []
        
        if os_type == 'non_rtos':
            lines.append(self.osal_templates['source']['mutex_section_comment'])
            lines.append(self.osal_templates['source']['mutex_create_nonrtos'])
            lines.append("")
            lines.append(self.osal_templates['source']['mutex_lock_nonrtos'])
            lines.append("")
            lines.append(self.osal_templates['source']['mutex_unlock_nonrtos'])
            lines.append("")
        
        return lines
    
    def _execute_semaphore_impl(self, step, context):
        os_type = context.get('os_type', 'non_rtos')
        lines = []
        
        if os_type == 'non_rtos':
            lines.append(self.osal_templates['source']['semaphore_section_comment'])
            lines.append(self.osal_templates['source']['semaphore_create_nonrtos'])
            lines.append("")
            lines.append(self.osal_templates['source']['semaphore_take_nonrtos'])
            lines.append("")
            lines.append(self.osal_templates['source']['semaphore_give_nonrtos'])
            lines.append("")
        
        return lines
    
    def _execute_queue_impl(self, step, context):
        os_type = context.get('os_type', 'non_rtos')
        lines = []
        
        if os_type == 'non_rtos':
            lines.append(self.osal_templates['source']['queue_section_comment'])
            lines.append(self.osal_templates['source']['queue_create_nonrtos'])
            lines.append("")
            lines.append(self.osal_templates['source']['queue_send_nonrtos'])
            lines.append("")
            lines.append(self.osal_templates['source']['queue_receive_nonrtos'])
            lines.append("")
        
        return lines
    
    def _execute_critical_impl(self, step, context):
        os_type = context.get('os_type', 'non_rtos')
        lines = []
        
        if os_type == 'non_rtos':
            lines.append(self.osal_templates['source']['critical_section_comment'])
            lines.append(self.osal_templates['source']['critical_enter_nonrtos'])
            lines.append("")
            lines.append(self.osal_templates['source']['critical_exit_nonrtos'])
            lines.append("")
        
        return lines
    
    # ===== Public methods =====
    def generate_header(self, os_type='non_rtos') -> str:
        """OSAL header generation"""
        self._log_debug(f"Generating OSAL header for: {os_type}")
        
        os_info = self.osal_templates['os_types'].get(os_type, {})
        context = {
            'filename': os_info.get('header', 'osal.h'),
            'os_type': os_type,
            'guard_name': 'OSAL_H',
        }
        
        lines = []
        for step in self.header_steps:
            executor = self.step_executors.get(step['action'])
            if executor:
                lines.extend(executor(step, context))
        
        return '\n'.join(lines)
    
    def generate_source(self, os_type='non_rtos') -> str:
        """OSAL source generation"""
        self._log_debug(f"Generating OSAL source for: {os_type}")
        
        os_info = self.osal_templates['os_types'].get(os_type, {})
        context = {
            'filename': os_info.get('source', 'osal.c'),
            'os_type': os_type,
        }
        
        lines = []
        for step in self.source_steps:
            executor = self.step_executors.get(step['action'])
            if executor:
                lines.extend(executor(step, context))
        
        return '\n'.join(lines)
    
    def generate_all(self, os_type='non_rtos') -> Dict[str, str]:
        """Generate all OSAL code"""
        os_info = self.osal_templates['os_types'].get(os_type, {})
        return {
            os_info.get('header', 'osal.h'): self.generate_header(os_type),
            os_info.get('source', 'osal.c'): self.generate_source(os_type),
        }
    
    def get_available_os_types(self) -> Dict[str, str]:
        """Get available OS types"""
        return {key: value['description'] for key, value in self.osal_templates['os_types'].items()}