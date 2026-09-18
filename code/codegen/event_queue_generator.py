# codegen/event_queue_generator.py
"""\nEvent queue code generation module (fully data-driven)\n"""

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
    """Event queue code generation class (fully data-driven)"""
    
    def __init__(self):
        self.mapper = CTypeMapper()
        self.naming = CNamingConvention()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        
        # Generation step definition
        self.struct_steps = [
            {'action': 'comment'},
            {'action': 'struct_start'},
            {'action': 'members'},
            {'action': 'struct_end'},
        ]
        
        self.enqueue_steps = [
            {'action': 'comment'},
            {'action': 'signature'},
            {'action': 'open'},
            {'action': 'null_check'},
            {'action': 'full_check'},
            {'action': 'enqueue_body'},
            {'action': 'close'},
        ]
        
        self.dequeue_steps = [
            {'action': 'comment'},
            {'action': 'signature'},
            {'action': 'open'},
            {'action': 'null_check'},
            {'action': 'empty_check'},
            {'action': 'dequeue_body'},
            {'action': 'close'},
        ]
        
        # Step execution dictionary
        self.struct_executors: Dict[str, Callable] = {
            'comment': self._execute_struct_comment,
            'struct_start': self._execute_struct_start,
            'members': self._execute_members,
            'struct_end': self._execute_struct_end,
        }
        
        self.enqueue_executors: Dict[str, Callable] = {
            'comment': self._execute_enqueue_comment,
            'signature': self._execute_enqueue_signature,
            'open': self._execute_open,
            'null_check': self._execute_null_check,
            'full_check': self._execute_full_check,
            'enqueue_body': self._execute_enqueue_body,
            'close': self._execute_close,
        }
        
        self.dequeue_executors: Dict[str, Callable] = {
            'comment': self._execute_dequeue_comment,
            'signature': self._execute_dequeue_signature,
            'open': self._execute_open,
            'null_check': self._execute_null_check,
            'empty_check': self._execute_empty_check,
            'dequeue_body': self._execute_dequeue_body,
            'close': self._execute_close,
        }
    
    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)
    
    # ===== Name generation =====
    def _generate_struct_name(self, queue):
        return self.naming.create_type_name(getattr(queue, 'name', 'EventQueue'))
    
    def _generate_func_prefix(self, queue):
        return f"EventQueue_{self.naming.to_pascal_case(getattr(queue, 'name', ''))}"
    
    # ===== Struct generation step =====
    def _execute_struct_comment(self, step, context):
        queue = context.get('queue')
        name = getattr(queue, 'name', 'unknown')
        desc = getattr(queue, 'description', '')
        lines = [f"/* Event queue: {name} */"]
        if desc:
            lines.append(f"/* {desc} */")
        return lines
    
    def _execute_struct_start(self, step, context):
        return ["typedef struct {"]
    
    def _execute_members(self, step, context):
        queue = context.get('queue')
        indent = self.strings['indent_1']
        size = getattr(queue, 'size', 0)
        element_type = self.mapper.map_type(getattr(queue, 'element_type', 'EVENT_t'))
        
        lines = []
        lines.append(f"{indent}{element_type} buffer[{size}];")
        lines.append(f"{indent}uint8_t head;")
        lines.append(f"{indent}uint8_t tail;")
        lines.append(f"{indent}uint8_t count;")
        
        if getattr(queue, 'interrupt_safe', False):
            lines.append(f"{indent}bool interrupt_safe;")
        
        if getattr(queue, 'rtos_enabled', False):
            lines.append(f"{indent}bool rtos_enabled;")
        
        return lines
    
    def _execute_struct_end(self, step, context):
        queue = context.get('queue')
        type_name = self._generate_struct_name(queue)
        return [f"}} {type_name};"]
    
    # ===== Enqueue generation step =====
    def _execute_enqueue_comment(self, step, context):
        queue = context.get('queue')
        name = getattr(queue, 'name', 'unknown')
        return [
            "/**",
            f" * @brief  Enqueue event ({name})",
            " * @param  queue  Queue",
            " * @param  event  Event",
            " * @return success: true, failure: false",
            " */",
        ]
    
    def _execute_enqueue_signature(self, step, context):
        queue = context.get('queue')
        type_name = self._generate_struct_name(queue)
        func_name = self._generate_func_prefix(queue) + "_Enqueue"
        return [f"bool {func_name}({type_name} *queue, EVENT_t event)"]
    
    def _execute_dequeue_comment(self, step, context):
        queue = context.get('queue')
        name = getattr(queue, 'name', 'unknown')
        return [
            "/**",
            f" * @brief  Dequeue event ({name})",
            " * @param  queue  Queue",
            " * @param  event  Dequeued event",
            " * @return success: true, failure: false",
            " */",
        ]
    
    def _execute_dequeue_signature(self, step, context):
        queue = context.get('queue')
        type_name = self._generate_struct_name(queue)
        func_name = self._generate_func_prefix(queue) + "_Dequeue"
        return [f"bool {func_name}({type_name} *queue, EVENT_t *event)"]
    
    def _execute_open(self, step, context):
        return ["{"]
    
    def _execute_close(self, step, context):
        return ["}"]
    
    def _execute_null_check(self, step, context):
        indent = self.strings['indent_1']
        lines = []
        lines.append(f"{indent}if (queue == NULL) {{")
        lines.append(f"{indent}{indent}return false;")
        lines.append(f"{indent}}}")
        return lines
    
    def _execute_full_check(self, step, context):
        queue = context.get('queue')
        size = getattr(queue, 'size', 0)
        indent = self.strings['indent_1']
        lines = []
        lines.append(f"{indent}if (queue->count >= {size}) {{")
        lines.append(f"{indent}{indent}return false;  /* Queue full */")
        lines.append(f"{indent}}}")
        return lines
    
    def _execute_empty_check(self, step, context):
        indent = self.strings['indent_1']
        lines = []
        lines.append(f"{indent}if (queue->count == 0) {{")
        lines.append(f"{indent}{indent}return false;  /* Queue empty */")
        lines.append(f"{indent}}}")
        return lines
    
    def _execute_enqueue_body(self, step, context):
        queue = context.get('queue')
        size = getattr(queue, 'size', 0)
        indent = self.strings['indent_1']
        lines = []
        lines.append(f"{indent}queue->buffer[queue->tail] = event;")
        lines.append(f"{indent}queue->tail = (queue->tail + 1) % {size};")
        lines.append(f"{indent}queue->count++;")
        lines.append(f"{indent}return true;")
        return lines
    
    def _execute_dequeue_body(self, step, context):
        queue = context.get('queue')
        size = getattr(queue, 'size', 0)
        indent = self.strings['indent_1']
        lines = []
        lines.append(f"{indent}if (event == NULL) {{")
        lines.append(f"{indent}{indent}return false;")
        lines.append(f"{indent}}}")
        lines.append(f"{indent}*event = queue->buffer[queue->head];")
        lines.append(f"{indent}queue->head = (queue->head + 1) % {size};")
        lines.append(f"{indent}queue->count--;")
        lines.append(f"{indent}return true;")
        return lines
    
    # ===== Public methods =====
    def generate_struct(self, queue: EventQueueDef) -> str:
        """Event queue struct generation"""
        self._log_debug(f"Generating struct for: {getattr(queue, 'name', 'unknown')}")
        context = {'queue': queue}
        lines = []
        for step in self.struct_steps:
            executor = self.struct_executors.get(step['action'])
            if executor:
                lines.extend(executor(step, context))
        return '\n'.join(lines)
    
    def generate_enqueue_function(self, queue: EventQueueDef) -> str:
        """Enqueue function generation"""
        self._log_debug(f"Generating enqueue for: {getattr(queue, 'name', 'unknown')}")
        context = {'queue': queue}
        lines = []
        for step in self.enqueue_steps:
            executor = self.enqueue_executors.get(step['action'])
            if executor:
                lines.extend(executor(step, context))
        return '\n'.join(lines)
    
    def generate_dequeue_function(self, queue: EventQueueDef) -> str:
        """Dequeue function generation"""
        self._log_debug(f"Generating dequeue for: {getattr(queue, 'name', 'unknown')}")
        context = {'queue': queue}
        lines = []
        for step in self.dequeue_steps:
            executor = self.dequeue_executors.get(step['action'])
            if executor:
                lines.extend(executor(step, context))
        return '\n'.join(lines)
    
    def generate_all_code(self, queue: EventQueueDef) -> str:
        """Generate all event queue code"""
        self._log_debug(f"Generating all code for: {getattr(queue, 'name', 'unknown')}")
        lines = []
        lines.append(self.generate_struct(queue))
        lines.append("")
        lines.append(self.generate_enqueue_function(queue))
        lines.append("")
        lines.append(self.generate_dequeue_function(queue))
        return '\n'.join(lines)
    
    def generate_all_structs(self, global_defs: GlobalDefinitions) -> str:
        """Generate all event queue structs"""
        lines = []
        for queue in getattr(global_defs, 'event_queues', []):
            lines.append(self.generate_struct(queue))
            lines.append("")
        return '\n'.join(lines)
    
    def generate_all_functions(self, global_defs: GlobalDefinitions) -> str:
        """Generate all event queue functions"""
        lines = []
        for queue in getattr(global_defs, 'event_queues', []):
            lines.append(self.generate_enqueue_function(queue))
            lines.append("")
            lines.append(self.generate_dequeue_function(queue))
            lines.append("")
        return '\n'.join(lines)
    
    def generate_all(self, global_defs: GlobalDefinitions) -> str:
        """Generate all event queue code"""
        lines = []
        for queue in getattr(global_defs, 'event_queues', []):
            lines.append(self.generate_all_code(queue))
            lines.append("")
        return '\n'.join(lines)