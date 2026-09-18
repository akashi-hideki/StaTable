# codegen/interrupt_generator.py
"""\nInterrupt handler ISR generation module (H3: ISR context support)\n\nFeatures:\n  1. Automatic ctx pointer insertion (SystemContext_t *ctx = &g_ctx;)\n  2. Action Namespace.Name -> RoleFunc_<NS>_<Name>(NULL, ctx) conversion\n  3. Legacy identifier(args) -> RoleFunc_<Layer>_<Pascal>(NULL, ctx) conversion\n  4. User marker [[STABLE_USER_CODE_START:<Marker>]]\n  5. Automatic extraction of used_role_functions / used_variables\n  6. Entry / exit logging\n\nMarker naming convention:\n  handler.name = \"TIMER0\"  -> ISR_TIMER0  / Marker \"TIMER0\"\n  handler.name = \"UART_RX\" -> ISR_UARTRX  / Marker \"UARTRX\"\n"""

import sys
import os
import re
import logging
from typing import Dict, Callable, List, Any, Optional, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statable.global_defs import (
    InterruptHandlerDef, InterruptAction, GlobalDefinitions,
)

try:
    from .naming_convention import CNamingConvention
    from .code_templates import CodeTemplates
except ImportError:
    from naming_convention import CNamingConvention
    from code_templates import CodeTemplates

logger = logging.getLogger(__name__)


# C reserved words (excluded to avoid mis-converting function-call forms)
_C_KEYWORDS = {
    'if', 'else', 'for', 'while', 'do', 'switch', 'case',
    'default', 'break', 'continue', 'return', 'goto',
    'sizeof', 'typedef', 'struct', 'union', 'enum',
    'static', 'const', 'volatile', 'extern', 'inline',
    'void', 'int', 'char', 'short', 'long', 'float', 'double',
    'signed', 'unsigned', 'bool', 'true', 'false', 'NULL',
}


class InterruptGenerator:
    """Interrupt handler ISR generation class (H3: context support)"""

    # ================================================================
    # Class constants
    # ================================================================
    AUTO_INSERT_CTX = True
    CTX_VAR_NAME = 'ctx'
    G_CTX_NAME = 'g_ctx'

    def __init__(self):
        self.naming = CNamingConvention()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        self.layer_name: str = ''

        # ============================================================
        # Generation step
        # ============================================================
        self.isr_steps = [
            {'action': 'comment'},
            {'action': 'signature'},
            {'action': 'open'},
            {'action': 'context'},
            {'action': 'enter_log'},
            {'action': 'actions'},
            {'action': 'user_section'},
            {'action': 'exit_log'},
            {'action': 'close'},
        ]

        self.step_executors: Dict[str, Callable] = {
            'comment':      self._execute_comment_step,
            'signature':    self._execute_signature_step,
            'open':         self._execute_open_step,
            'context':      self._execute_context_step,
            'enter_log':    self._execute_enter_log_step,
            'actions':      self._execute_actions_step,
            'user_section': self._execute_user_section_step,
            'exit_log':     self._execute_exit_log_step,
            'close':        self._execute_close_step,
        }

    def set_layer(self, layer_name: str):
        """Set layer name (used for RoleFunc name generation in legacy identifier(args) form)"""
        self.layer_name = layer_name or ''

    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)

    # ================================================================
    # Name generation
    # ================================================================
    def _get_isr_function_name(self, handler) -> str:
        """ISR_<PascalCase(handler.name)>"""
        name = getattr(handler, 'name', '') or 'unnamed'
        return f"ISR_{self.naming.to_pascal_case(name)}"

    def _get_marker_name(self, handler) -> str:
        """PascalCase(handler.name)"""
        name = getattr(handler, 'name', '') or 'unnamed'
        return self.naming.to_pascal_case(name)

    def _get_handler_display_name(self, handler) -> str:
        """Log display name (original name as-is)"""
        return getattr(handler, 'name', '') or 'unnamed'

    # ================================================================
    # Action parsing
    # ================================================================
    def _parse_action(self, action_text: str) -> Tuple[str, List[str]]:
        """\n        Convert action string to C code\n\n        Args:\n            action_text: Input action string\n\n        Returns:\n            (c_code, used_role_functions)\n\n        Conversion rules:\n          1. Namespace.Name [(args)] -> RoleFunc_Namespace_Name(NULL, ctx)\n          2. identifier(args)          -> RoleFunc_<Layer>_PascalId(NULL, ctx)\n          3. otherwise                 -> as-is\n        """
        if not action_text:
            return "", []
        text = action_text.strip()
        if not text:
            return "", []

        used: List[str] = []

        # --- 1. Namespace.Name form ---
        m = re.fullmatch(
            r'([A-Z]\w*)\.([A-Za-z_]\w*)\s*(\(.*\))?',
            text, re.DOTALL,
        )
        if m:
            ns = m.group(1)
            name = m.group(2)
            pascal = self.naming.to_pascal_case(name)
            qualified = f"{ns}.{name}"
            used.append(qualified)
            return f"RoleFunc_{ns}_{pascal}(NULL, ctx)", used

        # --- 2. Function call form ---
        m = re.fullmatch(
            r'([A-Za-z_]\w*)\s*(\(.*\))',
            text, re.DOTALL,
        )
        if m:
            fname = m.group(1)
            # Names already starting with RoleFunc_ / ISR_ are kept as-is
            if fname.startswith('RoleFunc_') or fname.startswith('ISR_'):
                return text, used
            # C keywords kept as-is
            if fname in _C_KEYWORDS:
                return text, used
            # Convert to RoleFunc name (arguments discarded)
            pascal = self.naming.to_pascal_case(fname)
            if self.layer_name:
                call = f"RoleFunc_{self.layer_name}_{pascal}(NULL, ctx)"
                qualified = f"{self.layer_name}.{pascal}"
            else:
                call = f"RoleFunc_{pascal}(NULL, ctx)"
                qualified = pascal
            used.append(qualified)
            return call, used

        # --- 3. Otherwise ---
        return text, used

    def _parse_action_with_semicolon(
        self, action: InterruptAction,
    ) -> Tuple[str, List[str]]:
        """Convert condition-attached action to a single line of C code"""
        body, used = self._parse_action(getattr(action, 'action', ''))
        if not body:
            return "", used
        # Normalize trailing semicolon
        body = body.rstrip(';').rstrip()
        condition = (getattr(action, 'condition', '') or '').strip()
        if condition:
            return f"if ({condition}) {{ {body}; }}", used
        return f"{body};", used

    # ================================================================
    # Used symbol extraction
    # ================================================================
    def extract_used_symbols(
        self, handler: InterruptHandlerDef,
    ) -> Tuple[List[str], List[str]]:
        """\n        Extract used role functions and used variables from handler\n\n        Returns:\n            (used_role_functions, used_variables)\n            used_role_functions: [\"Driver.Init\", \"Application.HandleTick\"]\n            used_variables:      [\"counter\", \"EVT_START\"]\n        """
        used_rfs: List[str] = []
        used_vars: List[str] = []
        seen_rf = set()
        seen_var = set()

        for action in getattr(handler, 'actions', []):
            text = getattr(action, 'action', '') or ''
            _, rfs = self._parse_action(text)
            for r in rfs:
                if r and r not in seen_rf:
                    seen_rf.add(r)
                    used_rfs.append(r)

            # ctx->data.X / ctx->flags.X
            for m in re.finditer(
                r'ctx->(?:data|flags)\.([A-Za-z_]\w*)', text,
            ):
                v = m.group(1)
                if v and v not in seen_var:
                    seen_var.add(v)
                    used_vars.append(v)

        return used_rfs, used_vars

    def update_handler_symbols(self, handler: InterruptHandlerDef):
        """Recompute handler's used_role_functions / used_variables and write back"""
        used_rfs, used_vars = self.extract_used_symbols(handler)
        handler.used_role_functions = used_rfs
        handler.used_variables = used_vars

    # ================================================================
    # Step execution
    # ================================================================
    def _execute_comment_step(self, step, context):
        handler = context['handler']
        display = self._get_handler_display_name(handler)
        used_rfs = context.get('used_role_functions', [])
        description = getattr(handler, 'description', '') or ''

        lines = [
            "/**",
            f" * @brief  {display} 割り込みハンドラ",
        ]
        if description:
            lines.append(f" * @note   {description}")
        if used_rfs:
            lines.append(" * @note   Used role functions:")
            for r in used_rfs:
                lines.append(f" *         - {r}")
        lines.append(" */")
        return lines

    def _execute_signature_step(self, step, context):
        handler = context['handler']
        func_name = self._get_isr_function_name(handler)
        return [f"void {func_name}(void)"]

    def _execute_open_step(self, step, context):
        return ["{"]

    def _execute_context_step(self, step, context):
        if not self.AUTO_INSERT_CTX:
            return []
        return [
            "",
            "    /* ===== Context reference (auto-generated) ===== */",
            f"    SystemContext_t *{self.CTX_VAR_NAME} = &{self.G_CTX_NAME};",
            f"    (void){self.CTX_VAR_NAME};",
        ]

    def _execute_enter_log_step(self, step, context):
        handler = context['handler']
        display = self._get_handler_display_name(handler)
        return [
            "",
            "    /* ===== Entry log ===== */",
            f'    LOG_DEBUG("Enter ISR: {display}");',
        ]

    def _execute_actions_step(self, step, context):
        handler = context['handler']
        actions = getattr(handler, 'actions', []) or []
        if not actions:
            return []

        lines = [
            "",
            "    /* ===== Actions (auto-generated) ===== */",
        ]
        has_action = False
        for action in actions:
            body, _ = self._parse_action_with_semicolon(action)
            if body:
                lines.append(f"    {body}")
                has_action = True
        if not has_action:
            lines.append("    /* (action undefined) */")
        return lines

    def _execute_user_section_step(self, step, context):
        handler = context['handler']
        marker = self._get_marker_name(handler)
        return [
            "",
            "    /* ===== User extension area ===== */",
            f"    /* [[STABLE_USER_CODE_START:{marker}]] */",
            "    /* Add user code here */",
            f"    /* [[STABLE_USER_CODE_END:{marker}]] */",
        ]

    def _execute_exit_log_step(self, step, context):
        handler = context['handler']
        display = self._get_handler_display_name(handler)
        return [
            "",
            "    /* ===== Exit log ===== */",
            f'    LOG_DEBUG("Exit ISR: {display}");',
        ]

    def _execute_close_step(self, step, context):
        return ["}"]

    # ================================================================
    # Public API
    # ================================================================
    def generate_isr(
        self, handler: InterruptHandlerDef,
        update_handler: bool = False,
    ) -> str:
        """\n        Generate ISR\n\n        Args:\n            handler: Interrupt handler definition\n            update_handler: If True, write used_* back to handler\n        """
        self._log_debug(f"Generating ISR for: {handler.name}")

        used_rfs, used_vars = self.extract_used_symbols(handler)

        if update_handler:
            handler.used_role_functions = used_rfs
            handler.used_variables = used_vars

        context = {
            'handler': handler,
            'used_role_functions': used_rfs,
            'used_variables': used_vars,
        }
        lines: List[str] = []
        for step in self.isr_steps:
            executor = self.step_executors.get(step['action'])
            if executor is None:
                continue
            result = executor(step, context)
            if result:
                lines.extend(result)
        return '\n'.join(lines)

    def generate_all_isrs(
        self, global_defs: GlobalDefinitions,
        update_handlers: bool = False,
    ) -> str:
        """Generate all ISRs"""
        lines: List[str] = []
        for handler in getattr(global_defs, 'interrupts', []):
            lines.append(self.generate_isr(
                handler, update_handler=update_handlers,
            ))
            lines.append("")
            lines.append("")
        return '\n'.join(lines).rstrip() + '\n'