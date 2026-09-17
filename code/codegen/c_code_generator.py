# codegen/c_code_generator.py
"""
C code generation main class
(step-table driven / 13-file support / multi-layer support / by_layer / ISR)

Design policy:
  - Per-file generation procedure is declared in the FILE_STEPS table
  - Each step is bound to an executor via the step_executors dictionary
  - _run_steps() / _run_steps_multi() execute the step list in order
  - Conditional steps are declared by 'when' predicates
  - File-to-file dispatch is managed by the FILE_DISPATCH dictionary
  - Folder structure is resolved by FOLDER_STRUCTURE_RESOLVERS
  - Super include / super loop are always generated
  - Multiple layers are generated in bulk by generate_all_layers()
  - by_layer separates layer-specific files into layer folders

Version: 2.1 (2026-09-13 / Stage 3: ISR context support)
  - Added statable_all.h to interrupt_c (to obtain g_ctx / RoleFunc_* decls)
  - _step_interrupts recomputes used_role_functions / used_variables

[v1.6 sec 9.7 #91]
  - Append `_{layer}` suffix to layer-specific files in by_layer mode
    statable_role_functions.c -> statable_role_functions_Driver.c
  - Update include statements inside layer-specific files accordingly
  - Append layer suffix to include guard names (collision avoidance)
  - Common files individually include each layer's types in by_layer
  - Super include layer-specific include paths also use the suffix

[v1.6 sec 9.8 #92] (Option Y)
  - Consolidate common structs (FLAG_t / SystemData_t / EventFlags_t /
    SystemContext_t / TransitionContext_t / var_macros / pending_event_macros)
    into the new statable_types_common.h
  - Layer-specific statable_types_{layer}.h outputs enums only
  - Layer-specific statable_types_{layer}.h includes statable_types_common.h
  - custom_types also moved to the common section (no duplication per layer)
"""

import sys
import os
import logging
from typing import Dict, Callable, List, Any, Optional, Tuple
from datetime import datetime

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from statable.state_machine import StateMachine
from statable.global_defs import GlobalDefinitions

try:
    from .type_mapper import CTypeMapper
    from .naming_convention import CNamingConvention
    from .struct_generator import CStructGenerator
    from .enum_generator import CEnumGenerator
    from .transition_generator import TransitionGenerator
    from .role_function_generator import RoleFunctionGenerator
    from .variable_generator import VariableGenerator
    from .event_queue_generator import EventQueueGenerator
    from .interrupt_generator import InterruptGenerator
    from .timer_generator import TimerGenerator
    from .osal_generator import OSALGenerator
    from .code_templates import CodeTemplates
    from .code_merger import CodeMerger
    from .config import CodeGenerationConfig, ConfigManager
except ImportError:
    from type_mapper import CTypeMapper
    from naming_convention import CNamingConvention
    from struct_generator import CStructGenerator
    from enum_generator import CEnumGenerator
    from transition_generator import TransitionGenerator
    from role_function_generator import RoleFunctionGenerator
    from variable_generator import VariableGenerator
    from event_queue_generator import EventQueueGenerator
    from interrupt_generator import InterruptGenerator
    from timer_generator import TimerGenerator
    from osal_generator import OSALGenerator
    from code_templates import CodeTemplates
    from code_merger import CodeMerger
    from config import CodeGenerationConfig, ConfigManager

logger = logging.getLogger(__name__)


class CCodeGenerator:
    """C code generation main class
       (step-table driven / 13-file support / multi-layer support)"""

    # ================================================================
    # [Table 1] Per-file step definitions
    # ================================================================
    FILE_STEPS: Dict[str, List[Dict[str, Any]]] = {
        # v1.6 sec 9.8 #92: common type definitions (new)
        'statable_types_common.h': [
            {'action': 'file_header',
             'filename': 'statable_types_common.h'},
            {'action': 'blank'},
            {'action': 'guard_start'},
            {'action': 'include_section', 'key': 'types'},
            {'action': 'section_header', 'key': 'type_defs'},
            {'action': 'blank'},
            {'action': 'custom_types',
             'when': lambda c: bool(c['global_defs'].custom_types)},
            {'action': 'section_header', 'key': 'system_structs'},
            {'action': 'blank'},
            {'action': 'struct', 'kind': 'system_data'},
            {'action': 'blank'},
            {'action': 'struct', 'kind': 'event_flags'},
            {'action': 'blank'},
            {'action': 'struct', 'kind': 'system_context'},
            {'action': 'blank'},
            {'action': 'struct', 'kind': 'common_transition_context'},
            {'action': 'blank'},
            {'action': 'struct', 'kind': 'pending_event_macros'},
            {'action': 'blank'},
            {'action': 'section_header', 'key': 'var_macros'},
            {'action': 'blank'},
            {'action': 'var_macros'},
            {'action': 'blank'},
            {'action': 'guard_end'},
        ],
        # v1.6 sec 9.8 #92: layer-specific type definitions (enum only)
        'statable_types.h': [
            {'action': 'file_header',
             'filename': 'statable_types.h'},
            {'action': 'blank'},
            {'action': 'guard_start'},
            {'action': 'include_section', 'key': 'types_layer'},
            {'action': 'section_header', 'key': 'type_defs'},
            {'action': 'blank'},
            {'action': 'enums'},
            {'action': 'blank'},
            {'action': 'guard_end'},
        ],
        'statable_transitions.h': [
            {'action': 'file_header',
             'filename': 'statable_transitions.h'},
            {'action': 'blank'},
            {'action': 'guard_start'},
            {'action': 'include_section',
             'key': 'transitions_h'},
            {'action': 'section_header',
             'key': 'function_decls'},
            {'action': 'blank'},
            {'action': 'state_machine_decl'},
            {'action': 'blank'},
            {'action': 'guard_end'},
        ],
        'statable_transitions.c': [
            {'action': 'file_header',
             'filename': 'statable_transitions.c'},
            {'action': 'blank'},
            {'action': 'include_section',
             'key': 'transitions_c'},
            {'action': 'section_header',
             'key': 'transition_table'},
            {'action': 'blank'},
            {'action': 'cell_prototypes'},
            {'action': 'blank'},
            {'action': 'transition_table'},
            {'action': 'blank'},
            {'action': 'cell_functions'},
            {'action': 'blank'},
            {'action': 'section_header',
             'key': 'transition_func'},
            {'action': 'blank'},
            {'action': 'process_func'},
        ],
        'statable_role_functions.h': [
            {'action': 'file_header',
             'filename': 'statable_role_functions.h'},
            {'action': 'blank'},
            {'action': 'guard_start'},
            {'action': 'include_section',
             'key': 'role_functions_h'},
            {'action': 'section_header',
             'key': 'role_functions'},
            {'action': 'blank'},
            {'action': 'role_decls'},
            {'action': 'blank'},
            {'action': 'guard_end'},
        ],
        'statable_role_functions.c': [
            {'action': 'file_header',
             'filename': 'statable_role_functions.c'},
            {'action': 'blank'},
            {'action': 'include_section',
             'key': 'role_functions_c'},
            {'action': 'section_header', 'key': 'role_impl'},
            {'action': 'blank'},
            {'action': 'role_impls'},
        ],
        'statable_init.c': [
            {'action': 'file_header',
             'filename': 'statable_init.c'},
            {'action': 'blank'},
            {'action': 'include_section', 'key': 'init_c'},
            {'action': 'section_header', 'key': 'init_func'},
            {'action': 'blank'},
            {'action': 'init_func'},
        ],
        'statable_event_queue.c': [
            {'action': 'file_header',
             'filename': 'statable_event_queue.c'},
            {'action': 'blank'},
            {'action': 'include_section',
             'key': 'event_queue_c'},
            {'action': 'event_queues'},
        ],
        'statable_interrupt.c': [
            {'action': 'file_header',
             'filename': 'statable_interrupt.c'},
            {'action': 'blank'},
            {'action': 'include_section',
             'key': 'interrupt_c'},
            {'action': 'interrupts'},
        ],
        'statable_timer.c': [
            {'action': 'file_header',
             'filename': 'statable_timer.c'},
            {'action': 'blank'},
            {'action': 'include_section', 'key': 'timer_c'},
            {'action': 'section_header', 'key': 'type_defs'},
            {'action': 'blank'},
            {'action': 'timer_struct'},
            {'action': 'blank'},
            {'action': 'section_header', 'key': 'init_func'},
            {'action': 'blank'},
            {'action': 'timer_init'},
            {'action': 'blank'},
            {'action': 'section_header',
             'key': 'transition_func'},
            {'action': 'blank'},
            {'action': 'timer_update'},
        ],
        'osal.h': [
            {'action': 'osal_header'},
        ],
        'osal.c': [
            {'action': 'osal_source'},
        ],
        # Super include (including extern declarations)
        'statable_all.h': [
            {'action': 'super_include_header'},
            {'action': 'blank'},
            {'action': 'super_include_guard_start'},
            {'action': 'blank'},
            {'action': 'super_include_common'},
            {'action': 'blank'},
            {'action': 'super_include_layer'},
            {'action': 'blank'},
            {'action': 'super_include_project'},
            {'action': 'blank'},
            {'action': 'super_include_extern_vars'},
            {'action': 'blank'},
            {'action': 'super_include_extern_funcs'},
            {'action': 'blank'},
            {'action': 'super_include_external',
             'when': lambda c: (
                 c['config'].external_includes_in_super
                 and bool(c['config'].external_includes)
             )},
            {'action': 'blank',
             'when': lambda c: (
                 c['config'].external_includes_in_super
                 and bool(c['config'].external_includes)
             )},
            {'action': 'super_include_user'},
            {'action': 'blank'},
            {'action': 'super_include_guard_end'},
        ],
    }

    # ================================================================
    # [Table 2] struct kind -> generator method dispatch
    # ================================================================
    STRUCT_KIND_DISPATCH: Dict[str, str] = {
        'system_data':                'system_data',
        'event_flags':                'event_flags',
        'system_context':             'system_context',
        'common_transition_context':  'common_transition_context',
        'pending_event_macros':       'pending_event_macros',
    }

    # ================================================================
    # [Table 3] filename -> generator method dispatch
    # ================================================================
    FILE_DISPATCH: Dict[str, str] = {
        'statable_types_common.h':
            '_generate_types_common_header',
        'statable_types.h':
            '_generate_types_header',
        'statable_transitions.h':
            '_generate_transitions_header',
        'statable_transitions.c':
            '_generate_transitions_source',
        'statable_role_functions.h':
            '_generate_role_functions_header',
        'statable_role_functions.c':
            '_generate_role_functions_source',
        'statable_init.c':
            '_generate_init_source',
        'statable_event_queue.c':
            '_generate_event_queue_source',
        'statable_interrupt.c':
            '_generate_interrupt_source',
        'statable_timer.c':
            '_generate_timer_source',
        'osal.h':
            '_generate_osal_header',
        'osal.c':
            '_generate_osal_source',
        'statable_all.h':
            '_generate_super_include',
    }

    # ================================================================
    # [Table 4] filename -> category (for by_type)
    # ================================================================
    FILE_CATEGORY: Dict[str, str] = {
        'statable_types_common.h':   'include',
        'statable_types.h':          'include',
        'statable_transitions.h':    'include',
        'statable_role_functions.h': 'include',
        'statable_transitions.c':    'src',
        'statable_role_functions.c': 'src',
        'statable_init.c':           'src',
        'statable_event_queue.c':    'src',
        'statable_interrupt.c':      'src',
        'statable_timer.c':          'src',
        'osal.h':                    'common',
        'osal.c':                    'common',
    }

    # ================================================================
    # [Table 5] folder_structure -> path resolver method
    # ================================================================
    FOLDER_STRUCTURE_RESOLVERS: Dict[str, str] = {
        'flat':     '_resolve_path_flat',
        'by_type':  '_resolve_path_by_type',
        'by_layer': '_resolve_path_by_layer',
    }

    # ================================================================
    # [Table 6] File classification for by_layer
    # ================================================================
    LAYER_SPECIFIC_FILES = {
        'statable_types.h',   # Layer-specific (enum only)
        'statable_transitions.h',
        'statable_transitions.c',
        'statable_role_functions.h',
        'statable_role_functions.c',
    }

    COMMON_FILES = {
        'statable_types_common.h',   # v1.6 sec 9.8 #92
        'statable_init.c',
        'statable_event_queue.c',
        'statable_interrupt.c',
        'statable_timer.c',
        'osal.h',
        'osal.c',
        'statable_all.h',
    }

    # ================================================================
    # Constructor
    # ================================================================
    def __init__(self,
                 config: Optional[CodeGenerationConfig] = None):
        self.mapper = CTypeMapper()
        self.naming = CNamingConvention()
        self.struct_gen = CStructGenerator()
        self.enum_gen = CEnumGenerator()
        self.transition_gen = TransitionGenerator()
        self.role_func_gen = RoleFunctionGenerator()
        self.variable_gen = VariableGenerator()
        self.event_queue_gen = EventQueueGenerator()
        self.interrupt_gen = InterruptGenerator()
        self.timer_gen = TimerGenerator()
        self.osal_gen = OSALGenerator()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        self.merger = CodeMerger()

        # Configuration
        self.config_manager = ConfigManager()
        if config:
            self.config_manager.set_config(config)
        self.config = self.config_manager.get_config()

        self.generation_date = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        # Shared library active only during generation
        self._current_role_function_library = None

        # Super loop filename
        self.super_loop_filename = (
            f"{self.config.project_name}_run.c"
        )

        # Copy at instance level
        self.FILE_STEPS = dict(self.__class__.FILE_STEPS)
        self.FILE_DISPATCH = dict(self.__class__.FILE_DISPATCH)
        self.FILE_CATEGORY = dict(self.__class__.FILE_CATEGORY)

        # Register super loop dynamically
        self.FILE_STEPS[self.super_loop_filename] = [
            {'action': 'super_loop_header'},
            {'action': 'blank'},
            {'action': 'super_loop_include'},
            {'action': 'blank'},
            {'action': 'super_loop_context_var'},
            {'action': 'blank'},
            {'action': 'super_loop_state_var'},
            {'action': 'blank'},
            {'action': 'super_loop_init_func'},
            {'action': 'blank'},
            {'action': 'super_loop_run_func'},
        ]
        self.FILE_DISPATCH[self.super_loop_filename] = \
            '_generate_super_loop'
        self.FILE_CATEGORY[self.super_loop_filename] = 'src'

        # ===== File generation metadata =====
        self.file_generators: Dict[str, Dict] = {
            'statable_types_common.h': {
                'description': 'Common type definitions for state transition system',
                'guard_name': 'STATABLE_TYPES_COMMON_H',
            },
            'statable_types.h': {
                'description': 'Layer-specific type definitions (enum)',
                'guard_name': 'STATABLE_TYPES_H',
            },
            'statable_transitions.h': {
                'description': 'State transition function declarations',
                'guard_name': 'STATABLE_TRANSITIONS_H',
            },
            'statable_transitions.c': {
                'description': 'State transition logic',
                'guard_name': None,
            },
            'statable_role_functions.h': {
                'description': 'Role function declarations',
                'guard_name': 'STATABLE_ROLE_FUNCTIONS_H',
            },
            'statable_role_functions.c': {
                'description': 'Role function implementations',
                'guard_name': None,
            },
            'statable_init.c': {
                'description': 'Initialization processing',
                'guard_name': None,
            },
            'statable_event_queue.c': {
                'description': 'Event queue implementation',
                'guard_name': None,
            },
            'statable_interrupt.c': {
                'description': 'Interrupt handler ISR',
                'guard_name': None,
            },
            'statable_timer.c': {
                'description': 'Timer processing',
                'guard_name': None,
            },
            'osal.h': {
                'description': 'OSAL header',
                'guard_name': 'OSAL_H',
            },
            'osal.c': {
                'description': 'OSAL source',
                'guard_name': None,
            },
            'statable_all.h': {
                'description': 'StaTable super include',
                'guard_name': 'STATABLE_ALL_H',
            },
            self.super_loop_filename: {
                'description': 'State machine super loop',
                'guard_name': None,
            },
        }

        # ===== Include definitions =====
        self.include_headers: Dict[str, List[str]] = {
            # Standard headers for common type definitions
            'types': [
                '#include <stdint.h>',
                '#include <stdbool.h>',
                '#include <string.h>',
            ],
            # v1.6 sec 9.8 #92: layer-specific files include common types
            'types_layer': [
                '#include "statable_types_common.h"',
            ],
            'transitions_h': [
                '#include "statable_types{layer_suffix}.h"',
            ],
            'transitions_c': [
                '#include "statable_transitions{layer_suffix}.h"',
                '#include "statable_role_functions{layer_suffix}.h"',
            ],
            'role_functions_h': [
                '#include "statable_types{layer_suffix}.h"',
            ],
            'role_functions_c': [
                '#include "statable_role_functions{layer_suffix}.h"',
            ],
            # Common files (individually expanded by _step_include_section in by_layer)
            'init_c': ['#include "statable_types_common.h"'],
            'event_queue_c': ['#include "statable_types_common.h"'],
            'interrupt_c': [
                '#include "statable_types_common.h"',
                '#include "statable_all.h"',
            ],
            'timer_c': ['#include "statable_types_common.h"'],
        }

        # ===== Step executor dictionary =====
        self.step_executors: Dict[str, Callable] = {
            # Common
            'file_header':        self._step_file_header,
            'blank':              self._step_blank,
            'guard_start':        self._step_guard_start,
            'guard_end':          self._step_guard_end,
            'include_section':    self._step_include_section,
            'section_header':     self._step_section_header,
            # Type definitions
            'enums':              self._step_enums,
            'custom_types':       self._step_custom_types,
            'struct':             self._step_struct,
            'var_macros':         self._step_var_macros,
            # Transitions
            'state_machine_decl': self._step_state_machine_decl,
            'cell_prototypes':    self._step_cell_prototypes,
            'transition_table':   self._step_transition_table,
            'cell_functions':     self._step_cell_functions,
            'process_func':       self._step_process_func,
            # Roles
            'role_decls':         self._step_role_decls,
            'role_impls':         self._step_role_impls,
            # Initialization
            'init_func':          self._step_init_func,
            # Event queue / interrupt
            'event_queues':       self._step_event_queues,
            'interrupts':         self._step_interrupts,
            # Timer
            'timer_struct':       self._step_timer_struct,
            'timer_init':         self._step_timer_init,
            'timer_update':       self._step_timer_update,
            # OSAL
            'osal_header':        self._step_osal_header,
            'osal_source':        self._step_osal_source,
            # Super include
            'super_include_header':      self._step_super_include_header,
            'super_include_guard_start': self._step_super_include_guard_start,
            'super_include_common':      self._step_super_include_common,
            'super_include_layer':       self._step_super_include_layer,
            'super_include_project':     self._step_super_include_project,
            'super_include_extern_vars': self._step_super_include_extern_vars,
            'super_include_extern_funcs': self._step_super_include_extern_funcs,
            'super_include_external':    self._step_super_include_external,
            'super_include_user':        self._step_super_include_user,
            'super_include_guard_end':   self._step_super_include_guard_end,
            # Super loop
            'super_loop_header':      self._step_super_loop_header,
            'super_loop_include':     self._step_super_loop_include,
            'super_loop_context_var': self._step_super_loop_context_var,
            'super_loop_state_var':   self._step_super_loop_state_var,
            'super_loop_init_func':   self._step_super_loop_init_func,
            'super_loop_run_func':    self._step_super_loop_run_func,
        }

    # ================================================================
    # Logging
    # ================================================================
    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)

    # ================================================================
    # Configuration
    # ================================================================
    def get_config(self) -> CodeGenerationConfig:
        return self.config

    def set_config(self, config: CodeGenerationConfig):
        self.config_manager.set_config(config)
        self.config = self.config_manager.get_config()

    def update_config(self, **kwargs):
        self.config_manager.update(**kwargs)
        self.config = self.config_manager.get_config()

    def reset_config(self):
        self.config_manager.reset()
        self.config = self.config_manager.get_config()

    # ================================================================
    # Helpers
    # ================================================================
    def _get_states_list(self, state_machine):
        return list(state_machine.states.values())

    def _get_events_list(self, state_machine):
        return list(state_machine.events.values())

    def _get_role_functions_list(self, state_machine):
        """Return the role function list merged from
           state_machine and the shared library"""
        funcs = dict(state_machine.role_functions)
        lib = self._current_role_function_library
        if lib is not None:
            for rf in lib.list_all():
                name = getattr(rf, 'name', None)
                if name and name not in funcs:
                    funcs[name] = rf
        return list(funcs.values())

    def _get_layer_name(self, state_machine) -> str:
        """Get layer name (empty string if unset)"""
        return getattr(state_machine, 'layer_name', '') or ''

    def _get_initial_state(self, state_machine) -> str:
        """Get initial state name (defaults to 'Idle' if unset)"""
        initial = getattr(state_machine, 'initial_state', None)
        if not initial:
            initial = getattr(state_machine, 'initial', None)
        return initial or 'Idle'

    def _generate_section_header(self, section_key):
        line = self.strings['section_line']
        title = self.templates.SECTION_HEADERS.get(
            section_key, ''
        )
        return f"{line}\n *  {title}\n{line}"

    def _generate_file_header(self, filename, description=""):
        return (
            f"/**\n"
            f" * @file    {filename}\n"
            f" * @brief   {description}\n"
            f" *\n"
            f" * @note    {self.strings['auto_generated']}\n"
            f" *          - {self.strings['no_edit']}\n"
            f" *          - {self.strings['edit_in_statable']}\n"
            f" *\n"
            f" * @date    {self.generation_date}\n"
            f" */"
        )

    def _generate_include_guard_start(self, guard_name):
        return f"#ifndef {guard_name}\n#define {guard_name}\n"

    def _generate_include_guard_end(self, guard_name):
        return f"#endif /* {guard_name} */"

    def _generate_include_section(self, include_key, layer_suffix=''):
        lines = [self._generate_section_header('include'), ""]
        for header in self.include_headers.get(include_key, []):
            header = header.replace('{layer_suffix}', layer_suffix)
            lines.append(header)
        lines.append("")
        return '\n'.join(lines)

    # ================================================================
    # v1.6 sec 9.7 #91: Layer suffix helpers
    # ================================================================
    def _layer_filename(self, filename: str, layer_name: str) -> str:
        if not layer_name:
            return filename
        if filename not in self.LAYER_SPECIFIC_FILES:
            return filename
        stem, ext = os.path.splitext(filename)
        return f"{stem}_{layer_name}{ext}"

    def _layer_suffix(self, layer_name: str) -> str:
        return f"_{layer_name}" if layer_name else ""

    # ================================================================
    # Multi-layer support
    # ================================================================
    def _normalize_layers(self, layers) -> List[Tuple[str, StateMachine]]:
        """
        Normalize layers.

        Args:
            layers: List[(name, sm)] or List[sm] or StateMachine

        Returns:
            List[(layer_name, state_machine)] (ascending priority)
        """
        if layers is None:
            return []

        # Single StateMachine
        if isinstance(layers, StateMachine):
            name = self._get_layer_name(layers)
            return [(name, layers)]

        # List
        result = []
        for item in layers:
            if isinstance(item, tuple) and len(item) == 2:
                name, sm = item
            elif isinstance(item, StateMachine):
                name = self._get_layer_name(item)
                sm = item
            else:
                continue
            # If layer name is unset, use tab name as default
            if not self._get_layer_name(sm) and name:
                sm.layer_name = name
            result.append((name, sm))

        # Sort ascending by priority
        result.sort(
            key=lambda x: getattr(x[1], 'layer_priority', 5)
        )
        return result

    def _setup_layer_generators(self, state_machine):
        """Propagate state_machine.layer_name to each sub-generator"""
        layer_name = self._get_layer_name(state_machine)
        for name, gen in [
            ('enum_gen',       self.enum_gen),
            ('transition_gen', self.transition_gen),
            ('role_func_gen',  self.role_func_gen),
            ('struct_gen',     self.struct_gen),
            ('interrupt_gen',  self.interrupt_gen),
        ]:
            if hasattr(gen, 'set_layer'):
                gen.set_layer(layer_name)

    # ================================================================
    # Folder structure resolution
    # ================================================================
    def _resolve_output_path(self, filename: str,
                             layer_name: str = '') -> str:
        """
        Return the relative save path for the given filename.

        If filename already contains a path separator ('/' or '\\'),
        use it as-is (e.g. "Driver/statable_types.h" for by_layer).
        """
        # Already path-like -> use as-is
        if '/' in filename or '\\' in filename:
            return filename

        # Special handling for super include
        if filename == 'statable_all.h':
            return self._resolve_super_include_path(layer_name)

        structure = self.config.folder_structure
        resolver_name = self.FOLDER_STRUCTURE_RESOLVERS.get(
            structure, '_resolve_path_flat'
        )
        resolver = getattr(self, resolver_name,
                           self._resolve_path_flat)
        return resolver(filename, layer_name)

    def _resolve_super_include_path(self, layer_name: str = '') -> str:
        """Resolve the save path for the super include"""
        fname = self.config.super_include_file
        structure = self.config.folder_structure

        if structure == 'flat':
            return fname
        elif structure == 'by_type':
            return os.path.join(
                self.config.super_include_dir, fname
            )
        elif structure == 'by_layer':
            # If layer_name is set, use layer folder; otherwise root
            if layer_name:
                return os.path.join(layer_name, fname)
            return fname
        return fname

    def _resolve_path_flat(self, filename: str,
                           layer_name: str = '') -> str:
        """flat: all files in the same folder"""
        return filename

    def _resolve_path_by_type(self, filename: str,
                              layer_name: str = '') -> str:
        """by_type: classify into include / src / common"""
        category = self.FILE_CATEGORY.get(filename, '')
        if category == 'include':
            return os.path.join(
                self.config.include_dir_name, filename
            )
        elif category == 'src':
            return os.path.join(
                self.config.source_dir_name, filename
            )
        elif category == 'common':
            return os.path.join(
                self.config.common_dir_name, filename
            )
        return filename

    def _resolve_path_by_layer(self, filename: str,
                               layer_name: str = '') -> str:
        """
        by_layer: place into layer folder.

        When generate_all_layers is used with by_layer, the key already
        contains "layer/filename", so this function is normally not called
        (see early return in _resolve_output_path).

        Fallback for using by_layer with single-layer generate_all.
        """
        if not layer_name:
            return filename
        # Only layer-specific files get folder separation
        if filename in self.LAYER_SPECIFIC_FILES:
            fname = self._layer_filename(filename, layer_name)
            return os.path.join(layer_name, fname)
        return filename

    # ================================================================
    # Generic step execution
    # ================================================================
    def _run_steps(self, filename,
                   state_machine, global_defs) -> str:
        """Generate one file following the step table (single layer)"""
        return self._run_steps_multi(
            filename,
            [(self._get_layer_name(state_machine), state_machine)],
            global_defs
        )

    # ================================================================
    # Generic step execution (multi-layer)
    # ================================================================
    def _run_steps_multi(self, filename,
                         layers: List[Tuple[str, StateMachine]],
                         global_defs) -> str:
        """Multi-layer step execution"""
        if not layers:
            return ""

        file_config = self.file_generators[filename]
        steps = self.FILE_STEPS.get(filename, [])
        context = {
            'layers':        layers,
            'state_machine': layers[0][1],
            'global_defs':   global_defs,
            'file_config':   file_config,
            'filename':      filename,
            'config':        self.config,
            'is_multi':      len(layers) > 1,
        }
        parts: List[str] = []
        for step in steps:
            when = step.get('when')
            if when is not None and not when(context):
                continue
            action = step.get('action', '')
            executor = self.step_executors.get(action)
            if executor is None:
                self._log_debug(
                    f"Unknown step action: {action}", 'warning'
                )
                continue
            result = executor(step, context)
            if result is None:
                continue
            if isinstance(result, list):
                parts.extend(result)
            else:
                parts.append(result)
        return '\n'.join(parts)

    # ================================================================
    # Step executor functions
    # ================================================================
    def _step_file_header(self, step, ctx):
        filename = step.get('filename', ctx['filename'])
        layers = ctx.get('layers', [])

        if (filename in self.LAYER_SPECIFIC_FILES and layers):
            layer_name = self._get_layer_name(layers[0][1])
            filename = self._layer_filename(filename, layer_name)

        desc = ctx['file_config'].get('description', '')
        return [self._generate_file_header(filename, desc)]

    def _step_blank(self, step, ctx):
        return [""]

    def _step_guard_start(self, step, ctx):
        guard = ctx['file_config'].get('guard_name')
        if not guard:
            return []
        filename = ctx.get('filename', '')
        layers = ctx.get('layers', [])
        if filename in self.LAYER_SPECIFIC_FILES and layers:
            layer_name = self._get_layer_name(layers[0][1])
            if layer_name:
                guard = f"{guard}_{layer_name.upper()}"
        return [self._generate_include_guard_start(guard)]

    def _step_guard_end(self, step, ctx):
        guard = ctx['file_config'].get('guard_name')
        if not guard:
            return []
        filename = ctx.get('filename', '')
        layers = ctx.get('layers', [])
        if filename in self.LAYER_SPECIFIC_FILES and layers:
            layer_name = self._get_layer_name(layers[0][1])
            if layer_name:
                guard = f"{guard}_{layer_name.upper()}"
        return [self._generate_include_guard_end(guard)]

    def _step_include_section(self, step, ctx):
        key = step.get('key', '')
        filename = ctx.get('filename', '')
        layers = ctx.get('layers', [])
        structure = ctx['config'].folder_structure

        # 1. Layer-specific file: single-layer suffix
        if filename in self.LAYER_SPECIFIC_FILES and layers:
            layer_name = self._get_layer_name(layers[0][1])
            suffix = self._layer_suffix(layer_name)
            return [self._generate_include_section(
                key, layer_suffix=suffix
            )]

        # 2. Common file + by_layer: individually include each layer's types
        if structure == 'by_layer' and filename in (
                'statable_init.c',
                'statable_event_queue.c',
                'statable_interrupt.c',
                'statable_timer.c'):
            lines = [self._generate_section_header('include'), ""]

            if filename == 'statable_interrupt.c':
                lines.append('#include "statable_all.h"')
            else:
                # Common type definitions + each layer's enum
                lines.append('#include "statable_types_common.h"')
                for layer_name, sm in layers:
                    layer = self._get_layer_name(sm)
                    if layer:
                        lines.append(
                            f'#include "{layer}/'
                            f'statable_types_{layer}.h"'
                        )
            lines.append("")
            return ['\n'.join(lines)]

        # 3. Other: static include
        return [self._generate_include_section(key)]

    def _step_section_header(self, step, ctx):
        return [self._generate_section_header(
            step.get('key', '')
        )]

    def _step_enums(self, step, ctx):
        """Concatenate enums from multiple layers"""
        gd = ctx['global_defs']
        layers = ctx['layers']
        results = []
        for layer_name, sm in layers:
            self._setup_layer_generators(sm)
            enum_code = self.enum_gen.generate_all_enums(
                self._get_states_list(sm),
                self._get_events_list(sm),
                gd.flags,
            )
            if enum_code:
                results.append(enum_code)
        if not results:
            return ['']
        return ['\n'.join(results)]

    def _step_custom_types(self, step, ctx):
        gd = ctx['global_defs']
        result: List[str] = [
            self._generate_section_header('custom_types'),
            "",
        ]
        for custom_type in gd.custom_types:
            result.append(self.struct_gen.generate_struct(
                'custom_type', custom_type
            ))
            result.append("")
        return result

    def _step_struct(self, step, ctx):
        """Dispatch struct kind by dictionary lookup"""
        kind = step.get('kind', '')
        method_name = self.STRUCT_KIND_DISPATCH.get(kind)
        if method_name is None:
            return []
        # First arg of struct_gen.generate_struct is the kind
        return [self.struct_gen.generate_struct(
            kind, ctx['global_defs']
        )]

    def _step_var_macros(self, step, ctx):
        return [self.variable_gen.generate_all_macros(
            ctx['global_defs']
        )]

    def _step_state_machine_decl(self, step, ctx):
        """Concatenate StateMachine_Process declarations for multiple layers"""
        layers = ctx['layers']
        results = []
        for layer_name, sm in layers:
            layer = self._get_layer_name(sm)
            if layer:
                state_type = f"STATE_{layer}_t"
                event_type = f"EVENT_{layer}_t"
                func_name = f"StateMachine_Process_{layer}"
            else:
                state_type = "STATE_t"
                event_type = "EVENT_t"
                func_name = "StateMachine_Process"

            results.append('\n'.join([
                "/**",
                " * @brief  State transition processing",
                " * @param  current_state  Current state",
                " * @param  event          Event that occurred",
                " * @param  ctx            System context pointer",
                " * @return State after transition",
                " */",
                f"{state_type} {func_name}(",
                f"    {state_type} current_state,",
                f"    {event_type} event,",
                "    SystemContext_t *ctx",
                ");",
            ]))
        return ['\n'.join(results)] if results else ['']

    def _step_cell_prototypes(self, step, ctx):
        """Per-cell function forward declarations for multiple layers"""
        layers = ctx['layers']
        results = []
        for layer_name, sm in layers:
            self._setup_layer_generators(sm)
            proto = (self.transition_gen
                     .generate_transition_cell_prototypes(sm))
            if proto:
                results.append(proto)
        return ['\n'.join(results)] if results else ['']

    def _step_transition_table(self, step, ctx):
        """Transition tables for multiple layers"""
        layers = ctx['layers']
        results = []
        for layer_name, sm in layers:
            self._setup_layer_generators(sm)
            tbl = self.transition_gen.generate_transition_table(
                sm, table_type=ctx['config'].table_type,
            )
            if tbl:
                results.append(tbl)
        return ['\n'.join(results)] if results else ['']

    def _step_cell_functions(self, step, ctx):
        """Cell function bodies for multiple layers"""
        layers = ctx['layers']
        results = []
        for layer_name, sm in layers:
            self._setup_layer_generators(sm)
            funcs = (self.transition_gen
                     .generate_transition_cell_functions(sm))
            if funcs:
                results.append(funcs)
        return ['\n'.join(results)] if results else ['']

    def _step_process_func(self, step, ctx):
        """StateMachine_Process for multiple layers"""
        layers = ctx['layers']
        results = []
        for layer_name, sm in layers:
            self._setup_layer_generators(sm)
            func = self.transition_gen.generate_process_function(
                sm,
                generation_style=ctx['config'].generation_style,
            )
            if func:
                results.append(func)
        return ['\n'.join(results)] if results else ['']

    def _step_role_decls(self, step, ctx):
        """Role function declarations for multiple layers"""
        layers = ctx['layers']
        results = []
        for layer_name, sm in layers:
            self._setup_layer_generators(sm)
            decls = (self.role_func_gen
                     .generate_all_declarations(
                         self._get_role_functions_list(sm)))
            if decls:
                results.append(decls)
        return ['\n'.join(results)] if results else ['']

    def _step_role_impls(self, step, ctx):
        """Role function implementations for multiple layers"""
        layers = ctx['layers']
        results = []
        for layer_name, sm in layers:
            self._setup_layer_generators(sm)
            impls = (self.role_func_gen
                     .generate_all_implementations(
                         self._get_role_functions_list(sm),
                         state_machine=sm,
                         global_defs=ctx['global_defs'],
                     ))
            if impls:
                results.append(impls)
        return ['\n'.join(results)] if results else ['']

    def _step_init_func(self, step, ctx):
        return [self.variable_gen.generate_init_function(
            ctx['global_defs']
        )]

    def _step_event_queues(self, step, ctx):
        gd = ctx['global_defs']
        queues = getattr(gd, 'event_queues', [])
        if not queues:
            return ["/* No event queue definitions */"]
        result: List[str] = [
            self._generate_section_header('type_defs'),
            "",
        ]
        for queue in queues:
            result.append(
                self.event_queue_gen.generate_all_code(queue)
            )
            result.append("")
        return result

    # Stage 3: recompute used_role_functions / used_variables
    def _step_interrupts(self, step, ctx):
        gd = ctx['global_defs']
        interrupts = getattr(gd, 'interrupts', [])
        if not interrupts:
            return ["/* No interrupt handler definitions */"]
        result: List[str] = [
            self._generate_section_header('transition_func'),
            "",
        ]
        for handler in interrupts:
            # Automatically extract and write back used role funcs / vars
            try:
                self.interrupt_gen.update_handler_symbols(handler)
            except Exception as e:
                self._log_debug(
                    f"update_handler_symbols failed for "
                    f"'{getattr(handler, 'name', '?')}': {e}",
                    'warning',
                )
            result.append(
                self.interrupt_gen.generate_isr(handler)
            )
            result.append("")
        return result

    def _step_timer_struct(self, step, ctx):
        return [self.timer_gen.generate_struct(
            ctx['global_defs']
        )]

    def _step_timer_init(self, step, ctx):
        return [self.timer_gen.generate_init_function(
            ctx['global_defs']
        )]

    def _step_timer_update(self, step, ctx):
        return [self.timer_gen.generate_update_function(
            ctx['global_defs']
        )]

    def _step_osal_header(self, step, ctx):
        return [self.osal_gen.generate_header(
            self.config.os_type
        )]

    def _step_osal_source(self, step, ctx):
        return [self.osal_gen.generate_source(
            self.config.os_type
        )]

    # ================================================================
    # Super include steps
    # ================================================================
    def _step_super_include_header(self, step, ctx):
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        fname = self.config.super_include_file
        return [T['file_comment'].format(filename=fname)]

    def _step_super_include_guard_start(self, step, ctx):
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        return [T['guard_start'].rstrip('\n')]

    def _step_super_include_guard_end(self, step, ctx):
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        return [T['guard_end']]

    def _step_super_include_common(self, step, ctx):
        """
        v1.6 sec 9.8 #92: include common type definitions + each layer's enum
        """
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        layers = ctx['layers']
        structure = self.config.folder_structure

        parts = [T['common_section']]

        if structure == 'by_layer':
            # Common type definitions (one)
            parts.append('#include "statable_types_common.h"')
            # Each layer's enum
            for layer_name, sm in layers:
                layer = self._get_layer_name(sm)
                if layer:
                    parts.append(
                        f'#include "{layer}/'
                        f'statable_types_{layer}.h"'
                    )
        else:
            parts.append('#include "statable_types_common.h"')
            parts.append('#include "statable_types.h"')
        return parts

    def _step_super_include_layer(self, step, ctx):
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        layers = ctx['layers']
        structure = self.config.folder_structure

        parts = [T['layer_section']]

        if structure == 'by_layer':
            for layer_name, sm in layers:
                layer = self._get_layer_name(sm)
                if layer:
                    parts.append(
                        f'#include "{layer}/'
                        f'statable_transitions_{layer}.h"'
                    )
                    parts.append(
                        f'#include "{layer}/'
                        f'statable_role_functions_{layer}.h"'
                    )
        else:
            parts.append('#include "statable_transitions.h"')
            parts.append('#include "statable_role_functions.h"')
        return parts

    def _step_super_include_project(self, step, ctx):
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        return [
            T['project_section'],
            '#include "osal.h"',
        ]

    def _step_super_include_extern_vars(self, step, ctx):
        """extern variable declarations for all layers"""
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        layers = ctx['layers']
        parts = [T['extern_var_section'], T['extern_context']]

        for layer_name, sm in layers:
            layer = self._get_layer_name(sm)
            if layer:
                parts.append(T['extern_state'].format(layer=layer))
            else:
                parts.append(T['extern_state_nolayer'])
        return parts

    def _step_super_include_extern_funcs(self, step, ctx):
        """extern declarations for super loop functions"""
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        project = self.config.project_name
        return [
            T['extern_func_section'],
            T['extern_init'].format(project_name=project),
            T['extern_run'].format(project_name=project),
        ]

    def _step_super_include_external(self, step, ctx):
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        result = [T['external_section']]
        for inc in self.config.external_includes:
            inc = inc.strip()
            if not inc:
                continue
            if inc.startswith('#include'):
                result.append(inc)
            else:
                result.append(f'#include "{inc}"')
        return result

    def _step_super_include_user(self, step, ctx):
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        return [
            T['user_section'],
            T['user_marker_start'],
            T['user_marker_end'],
        ]

    # ================================================================
    # Super loop steps
    # ================================================================
    def _step_super_loop_header(self, step, ctx):
        T = self.templates.SUPER_LOOP_TEMPLATES
        project = self.config.project_name
        return [T['file_comment'].format(project_name=project)]

    def _step_super_loop_include(self, step, ctx):
        return [self.templates.SUPER_LOOP_TEMPLATES['include']]

    def _step_super_loop_context_var(self, step, ctx):
        return [self.templates.SUPER_LOOP_TEMPLATES['context_var']]

    def _step_super_loop_state_var(self, step, ctx):
        """state variable definitions for all layers"""
        layers = ctx['layers']
        T = self.templates.SUPER_LOOP_TEMPLATES
        parts = []
        for layer_name, sm in layers:
            layer = self._get_layer_name(sm)
            if layer:
                parts.append(T['state_var'].format(layer=layer))
            else:
                parts.append(T['state_var_nolayer'])
        return parts

    def _step_super_loop_init_func(self, step, ctx):
        """Initialization for all layers"""
        layers = ctx['layers']
        project = self.config.project_name
        T = self.templates.SUPER_LOOP_TEMPLATES

        parts = [
            T['init_func_comment'],
            T['init_func_signature'].format(project_name=project),
            T['init_func_open'],
            T['init_context'],
        ]
        for layer_name, sm in layers:
            layer = self._get_layer_name(sm)
            initial = self._get_initial_state(sm)
            if layer:
                parts.append(T['init_state'].format(
                    layer=layer, initial=initial,
                ))
            else:
                parts.append(T['init_state_nolayer'].format(
                    initial=initial,
                ))
        parts.append(T['init_func_close'])
        return parts

    def _step_super_loop_run_func(self, step, ctx):
        """run block for all layers (in priority order)"""
        layers = ctx['layers']
        project = self.config.project_name
        T = self.templates.SUPER_LOOP_TEMPLATES

        parts = [
            T['run_func_comment'],
            T['run_func_signature'].format(project_name=project),
            T['run_func_open'],
            T['run_while'],
        ]
        for layer_name, sm in layers:
            layer = self._get_layer_name(sm)
            priority = getattr(sm, 'layer_priority', 5)
            if layer:
                block = T['run_block'].format(
                    layer=layer,
                    priority=priority,
                )
            else:
                block = T['run_block_nolayer']
            # Adjust indentation
            indented = '        ' + block.replace(
                '\n', '\n        ')
            parts.append(indented)
        parts.append(T['run_while_close'])
        parts.append(T['run_func_close'])
        return parts

    # ================================================================
    # File generation methods
    # ================================================================
    def _generate_types_common_header(self, sm, gd):
        return self._run_steps('statable_types_common.h', sm, gd)

    def _generate_types_header(self, sm, gd):
        return self._run_steps('statable_types.h', sm, gd)

    def _generate_transitions_header(self, sm, gd):
        return self._run_steps('statable_transitions.h', sm, gd)

    def _generate_transitions_source(self, sm, gd):
        return self._run_steps('statable_transitions.c', sm, gd)

    def _generate_role_functions_header(self, sm, gd):
        return self._run_steps('statable_role_functions.h', sm, gd)

    def _generate_role_functions_source(self, sm, gd):
        return self._run_steps('statable_role_functions.c', sm, gd)

    def _generate_init_source(self, sm, gd):
        return self._run_steps('statable_init.c', sm, gd)

    def _generate_event_queue_source(self, sm, gd):
        return self._run_steps('statable_event_queue.c', sm, gd)

    def _generate_interrupt_source(self, sm, gd):
        return self._run_steps('statable_interrupt.c', sm, gd)

    def _generate_timer_source(self, sm, gd):
        return self._run_steps('statable_timer.c', sm, gd)

    def _generate_osal_header(self, sm, gd):
        return self._run_steps('osal.h', sm, gd)

    def _generate_osal_source(self, sm, gd):
        return self._run_steps('osal.c', sm, gd)

    # Super include
    def _generate_super_include(self, sm, gd):
        return self._run_steps('statable_all.h', sm, gd)

    def _generate_super_loop(self, sm, gd):
        return self._run_steps(self.super_loop_filename, sm, gd)

    # ================================================================
    # Public methods (single layer)
    # ================================================================
    def generate_all(self, state_machine, global_defs,
                     role_function_library=None):
        """Generate all code for a single layer (backward compatible)"""
        self._setup_layer_generators(state_machine)

        prev = self._current_role_function_library
        self._current_role_function_library = role_function_library
        try:
            generated_files = {}
            for filename in self.file_generators.keys():
                # Skip check for super include
                if (filename == 'statable_all.h'
                        and not self.config.generate_super_include):
                    continue
                method_name = self.FILE_DISPATCH.get(filename)
                if method_name is None:
                    continue
                method = getattr(self, method_name, None)
                if method is None:
                    continue
                generated_files[filename] = method(
                    state_machine, global_defs
                )
            return generated_files
        finally:
            self._current_role_function_library = prev

    def generate_file(self, filename, state_machine, global_defs,
                      role_function_library=None):
        """Generate a specific file (single layer)"""
        self._setup_layer_generators(state_machine)

        prev = self._current_role_function_library
        self._current_role_function_library = role_function_library
        try:
            if filename not in self.file_generators:
                raise ValueError(f"Unknown file: {filename}")
            return self._run_steps(
                filename, state_machine, global_defs
            )
        finally:
            self._current_role_function_library = prev

    # ================================================================
    # Public methods (multi-layer)
    # ================================================================
    def generate_all_layers(self, layers, global_defs,
                            role_function_library=None):
        """Generate code for multiple layers.

        Args:
            layers: List[(layer_name, StateMachine)] or
                    single StateMachine (backward compatible)
            global_defs: GlobalDefinitions
            role_function_library: shared library (optional)

        Returns:
            Dict[str, str]: generated file dictionary
            - by_type / flat: normal filenames
            - by_layer: "layer/filename" form (layer-specific)
                        + normal filenames (common)
        """
        # Normalize + sort by priority
        norm_layers = self._normalize_layers(layers)
        if not norm_layers:
            return {}

        structure = self.config.folder_structure

        if structure == 'by_layer':
            return self._generate_all_by_layer(
                norm_layers, global_defs, role_function_library
            )

        # by_type / flat: merge all layers into one file
        primary_sm = norm_layers[0][1]
        self._setup_layer_generators(primary_sm)

        prev = self._current_role_function_library
        self._current_role_function_library = role_function_library
        try:
            generated_files = {}
            for filename in self.file_generators.keys():
                if (filename == 'statable_all.h'
                        and not self.config.generate_super_include):
                    continue
                generated_files[filename] = self._run_steps_multi(
                    filename, norm_layers, global_defs
                )
            return generated_files
        finally:
            self._current_role_function_library = prev

    def _generate_all_by_layer(self, layers, global_defs,
                               role_function_library):
        """
        by_layer dedicated generation.

        v1.6 sec 9.8 #92:
          - Add common file statable_types_common.h
          - Layer-specific statable_types_{layer}.h contains enum only
        """
        self._log_debug(
            f"_generate_all_by_layer: {len(layers)} layers"
        )
        generated_files = {}

        prev = self._current_role_function_library
        self._current_role_function_library = role_function_library
        try:
            # === 1. Layer-specific files ===
            for layer_name, sm in layers:
                self._setup_layer_generators(sm)

                if not layer_name:
                    for fname in self.LAYER_SPECIFIC_FILES:
                        method_name = self.FILE_DISPATCH.get(fname)
                        if method_name is None:
                            continue
                        method = getattr(self, method_name, None)
                        if method is None:
                            continue
                        generated_files[fname] = method(
                            sm, global_defs
                        )
                    continue

                for fname in self.LAYER_SPECIFIC_FILES:
                    method_name = self.FILE_DISPATCH.get(fname)
                    if method_name is None:
                        continue
                    method = getattr(self, method_name, None)
                    if method is None:
                        continue
                    content = method(sm, global_defs)

                    fname_with_layer = self._layer_filename(
                        fname, layer_name
                    )
                    generated_files[
                        f"{layer_name}/{fname_with_layer}"
                    ] = content

            # === 2. Common files ===
            common_names = list(self.COMMON_FILES) + [
                self.super_loop_filename
            ]
            for fname in common_names:
                # Skip check for super include
                if (fname == 'statable_all.h'
                        and not self.config.generate_super_include):
                    continue
                content = self._run_steps_multi(
                    fname, layers, global_defs
                )
                generated_files[fname] = content

            return generated_files
        finally:
            self._current_role_function_library = prev

    # ================================================================
    # Save
    # ================================================================
    def save_generated_code(self, generated_files, output_dir,
                            layer_name: str = ''):
        """Save generated code (no merge)"""
        saved_files = []
        os.makedirs(output_dir, exist_ok=True)

        for filename, content in generated_files.items():
            rel_path = self._resolve_output_path(
                filename, layer_name
            )
            filepath = os.path.join(output_dir, rel_path)

            # Create parent directory
            parent = os.path.dirname(filepath)
            if parent:
                os.makedirs(parent, exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            saved_files.append(filepath)

        return saved_files

    def save_generated_code_with_merge(self, generated_files,
                                       output_dir,
                                       layer_name: str = ''):
        """Save while preserving user code"""
        merged_files = self.merger.merge_all_files(
            generated_files, output_dir,
            path_resolver=self._resolve_output_path,
            layer_name=layer_name,
        )
        return self.save_generated_code(
            merged_files, output_dir, layer_name
        )

    def get_merge_summary(self, generated_files, output_dir,
                          layer_name: str = ''):
        """Summary of the merge result"""
        summary = {}
        for filename, content in generated_files.items():
            rel_path = self._resolve_output_path(
                filename, layer_name
            )
            existing_path = os.path.join(output_dir, rel_path)
            if os.path.exists(existing_path):
                with open(existing_path, 'r',
                          encoding='utf-8') as f:
                    existing_content = f.read()
                summary[filename] = (
                    self.merger.get_user_code_summary(
                        existing_content
                    )
                )
            else:
                summary[filename] = {
                    'file_user_code': 0,
                    'func_user_codes': 0,
                    'file_tail_user_code': 0,
                }
        return summary

    def get_generated_file_list(self):
        """Return the list of generated files"""
        return list(self.file_generators.keys())