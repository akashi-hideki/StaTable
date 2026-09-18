# codegen/timer_generator.py
"""
Timer variable generation module (fully data-driven version)

[v1.5 fix]
  - generate_struct: TimerVariables_t removed
    Timer variables are already expanded into SystemData_t via
    add_timer_variables(), so the unused typedef is no longer emitted.
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
    """Timer variable generation class (fully data-driven)"""

    def __init__(self):
        self.mapper = CTypeMapper()
        self.naming = CNamingConvention()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS

        self.timer_struct_steps = [
            {'action': 'comment'},
            {'action': 'struct_start'},
            {'action': 'members'},
            {'action': 'struct_end'},
        ]

        self.init_steps = [
            {'action': 'comment'},
            {'action': 'signature'},
            {'action': 'open'},
            {'action': 'null_check'},
            {'action': 'entry_log'},
            {'action': 'init_base_timers'},
            {'action': 'init_derived_timers'},
            {'action': 'exit_log'},
            {'action': 'close'},
        ]

        self.update_steps = [
            {'action': 'comment'},
            {'action': 'signature'},
            {'action': 'open'},
            {'action': 'null_check'},
            {'action': 'update_derived_timers'},
            {'action': 'close'},
        ]

        self.struct_executors: Dict[str, Callable] = {
            'comment': self._execute_struct_comment,
            'struct_start': self._execute_struct_start,
            'members': self._execute_members,
            'struct_end': self._execute_struct_end,
        }

        self.init_executors: Dict[str, Callable] = {
            'comment': self._execute_init_comment,
            'signature': self._execute_init_signature,
            'open': self._execute_open,
            'null_check': self._execute_null_check,
            'entry_log': self._execute_entry_log,
            'init_base_timers': self._execute_init_base_timers,
            'init_derived_timers': self._execute_init_derived_timers,
            'exit_log': self._execute_exit_log,
            'close': self._execute_close,
        }

        self.update_executors: Dict[str, Callable] = {
            'comment': self._execute_update_comment,
            'signature': self._execute_update_signature,
            'open': self._execute_open,
            'null_check': self._execute_null_check,
            'update_derived_timers': self._execute_update_derived_timers,
            'close': self._execute_close,
        }

    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)

    def _get_all_timers(self, global_defs):
        timers = []
        timer_base = getattr(global_defs, 'timer_base', None)
        if timer_base:
            timers.append(timer_base)
        timers.extend(getattr(global_defs, 'extra_timers', []))
        return timers

    def _get_all_derived_timers(self, global_defs):
        derived_timers = []
        for timer in self._get_all_timers(global_defs):
            derived_timers.extend(getattr(timer, 'derived', []))
        return derived_timers

    def _execute_struct_comment(self, step, context):
        return ["/* Timer variable struct */", "/* Manages timer variables used across the system */"]

    def _execute_struct_start(self, step, context):
        return ["typedef struct {"]

    def _execute_members(self, step, context):
        global_defs = context.get('global_defs')
        indent = self.strings['indent_1']
        lines = []

        for timer in self._get_all_timers(global_defs):
            var_name = self.naming.sanitize_identifier(getattr(timer, 'variable_name', 'unknown'))
            data_type = self.mapper.map_type(getattr(timer, 'data_type', 'uint32_t'))
            unit = getattr(timer, 'unit', '')
            comment = f"/* {unit} */" if unit else ""
            lines.append(f"{indent}{data_type} {var_name}; {comment}".rstrip())

        for derived in self._get_all_derived_timers(global_defs):
            var_name = self.naming.sanitize_identifier(getattr(derived, 'variable_name', 'unknown'))
            data_type = self.mapper.map_type(getattr(derived, 'data_type', 'uint8_t'))
            period_name = getattr(derived, 'period_name', '')
            comment = f"/* {period_name} */" if period_name else ""
            lines.append(f"{indent}{data_type} {var_name}; {comment}".rstrip())

        return lines

    def _execute_struct_end(self, step, context):
        return ["} TimerVariables_t;"]

    def _execute_init_comment(self, step, context):
        return [
            "/**",
            " * @brief  Timer variable initialization",
            " * @param  ctx  System context pointer",
            " */",
        ]

    def _execute_init_signature(self, step, context):
        return ["void Timer_Init(SystemContext_t *ctx)"]

    def _execute_open(self, step, context):
        return ["{"]

    def _execute_close(self, step, context):
        return ["}"]

    def _execute_null_check(self, step, context):
        indent = self.strings['indent_1']
        return [
            f"{indent}if (ctx == NULL) {{",
            f"{indent}{indent}return;",
            f"{indent}}}",
        ]

    def _execute_entry_log(self, step, context):
        indent = self.strings['indent_1']
        return [f"{indent}{self.strings['log_debug']}(\"Enter Timer_Init\");", ""]

    def _execute_init_base_timers(self, step, context):
        global_defs = context.get('global_defs')
        indent = self.strings['indent_1']
        lines = []

        for timer in self._get_all_timers(global_defs):
            var_name = self.naming.sanitize_identifier(getattr(timer, 'variable_name', 'unknown'))
            lines.append(f"{indent}ctx->data.{var_name} = 0;")

        return lines

    def _execute_init_derived_timers(self, step, context):
        global_defs = context.get('global_defs')
        indent = self.strings['indent_1']
        lines = []

        for derived in self._get_all_derived_timers(global_defs):
            var_name = self.naming.sanitize_identifier(getattr(derived, 'variable_name', 'unknown'))
            lines.append(f"{indent}ctx->data.{var_name} = 0;")

        return lines

    def _execute_exit_log(self, step, context):
        indent = self.strings['indent_1']
        return ["", f"{indent}{self.strings['log_debug']}(\"Exit Timer_Init\");"]

    def _execute_update_comment(self, step, context):
        return [
            "/**",
            " * @brief  Timer update processing",
            " * @param  ctx  System context pointer",
            " */",
        ]

    def _execute_update_signature(self, step, context):
        return ["void Timer_Update(SystemContext_t *ctx)"]

    def _execute_update_derived_timers(self, step, context):
        global_defs = context.get('global_defs')
        indent = self.strings['indent_1']
        lines = []

        for timer in self._get_all_timers(global_defs):
            base_var = self.naming.sanitize_identifier(getattr(timer, 'variable_name', 'unknown'))

            for derived in getattr(timer, 'derived', []):
                derived_var = self.naming.sanitize_identifier(getattr(derived, 'variable_name', 'unknown'))
                multiplier = getattr(derived, 'multiplier', 1)
                data_type = self.mapper.map_type(getattr(derived, 'data_type', 'uint8_t'))

                if multiplier > 0:
                    lines.append(f"{indent}ctx->data.{derived_var} = ({data_type})(ctx->data.{base_var} / {multiplier});")

        return lines

    def generate_struct(self, global_defs: GlobalDefinitions) -> str:
        """
        Generate timer variable struct.

        [v1.5 change]
          Timer variables are already expanded into SystemData_t;
          TimerVariables_t is no longer used (v1.5 sec 9.6 #83).
          The function is retained for backward compatibility but
          now returns an empty string.
        """
        self._log_debug(
            "generate_struct: TimerVariables_t is unused, returning empty"
        )
        return ""

    def generate_init_function(self, global_defs: GlobalDefinitions) -> str:
        self._log_debug("Generating timer init function")
        context = {'global_defs': global_defs}
        lines = []
        for step in self.init_steps:
            executor = self.init_executors.get(step['action'])
            if executor:
                lines.extend(executor(step, context))
        return '\n'.join(lines)

    def generate_update_function(self, global_defs: GlobalDefinitions) -> str:
        self._log_debug("Generating timer update function")
        context = {'global_defs': global_defs}
        lines = []
        for step in self.update_steps:
            executor = self.update_executors.get(step['action'])
            if executor:
                lines.extend(executor(step, context))
        return '\n'.join(lines)

    def generate_all(self, global_defs: GlobalDefinitions) -> str:
        lines = []
        lines.append(self.generate_struct(global_defs))
        lines.append("")
        lines.append(self.generate_init_function(global_defs))
        lines.append("")
        lines.append(self.generate_update_function(global_defs))
        return '\n'.join(lines)