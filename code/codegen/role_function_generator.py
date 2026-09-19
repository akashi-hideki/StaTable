# codegen/role_function_generator.py
"""
Role function generation module (multi-layer state machine / ISR support)

Version: 3.2 (2026-09-20 / MISRA fixes)
  - MISRA 17.7 / unreadVariable: `transition_id` and per-variable data
    pointers are now explicitly discarded via `(void)` immediately after
    declaration. User code markers can still freely use them.
    This removes ~250 unreadVariable warnings in generated C without
    changing the function signature (arg/return types are design-fixed).

Version: 3.1 (2026-09-19 / v2.2.5 fixes)
  - _collect_call_sites now also collects:
      * State entry / exit references
      * Cell-level actions (before_transitions / after_transitions)
  - _should_emit_implementation now accepts namespace prefix matches.

Version: 3.0 (2026-09-13 / Stage 4: transition-side Namespace.Name support)

[v1.5 addition]
  - _VALID_C_IDENTIFIER guard added to _normalize_func_ref

[v1.6 addition]
  - _should_emit_implementation added (layer filter / Option A)
"""

import sys
import os
import re
import logging
from string import Template
from typing import Dict, List, Iterable, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statable.model import RoleFunction

try:
    from .type_mapper import CTypeMapper
    from .naming_convention import CNamingConvention
    from .code_templates import CodeTemplates
    from .code_merger import CodeMerger
except ImportError:
    from type_mapper import CTypeMapper
    from naming_convention import CNamingConvention
    from code_templates import CodeTemplates
    from code_merger import CodeMerger

logger = logging.getLogger(__name__)


# ======================================================================
# v1.5 addition: C identifier validation regex
# ======================================================================
_VALID_C_IDENTIFIER = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
_VALID_QUALIFIED = re.compile(
    r'^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?$'
)


# ======================================================================
# Helpers
# ======================================================================
def ensure_list(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        s = value.strip()
        return [s] if s else []
    if isinstance(value, list):
        return [str(x) for x in value if str(x).strip()]
    return [str(value)]


_C_KEYWORDS = {
    'auto', 'break', 'case', 'char', 'const', 'continue',
    'default', 'do', 'double', 'else', 'enum', 'extern',
    'float', 'for', 'goto', 'if', 'inline', 'int', 'long',
    'register', 'restrict', 'return', 'short', 'signed',
    'sizeof', 'static', 'struct', 'switch', 'typedef',
    'union', 'unsigned', 'void', 'volatile', 'while',
    'true', 'false', 'NULL',
}


class RoleFuncCallSite:
    """One role function call site (from_state x event)"""
    __slots__ = ('func_name', 'kind', 'from_state', 'event', 'target')

    def __init__(self, func_name, kind, from_state, event, target):
        self.func_name = func_name
        self.kind = kind
        self.from_state = from_state
        self.event = event
        self.target = target

    def key(self):
        return (self.from_state, self.event)

    def __repr__(self):
        return (f"CallSite({self.func_name!r}, {self.kind!r}, "
                f"{self.from_state}->{self.target})")


class RoleFunctionGenerator:
    """Role function generation class (multi-layer state machine / ISR support)"""

    # ================================================================
    # [Table 1] Declaration templates
    # ================================================================
    DECLARATION_TEMPLATES = {
        'comment_with_desc': Template(
            '/**\n'
            ' * @brief  Role function: $title\n'
            ' * @note   $description\n'
            ' * @param  transition  Transition context (may be NULL: called from ISR)\n'
            ' * @param  ctx         System context pointer\n'
            ' * @return 0: success, non-zero: error (can also be used for condition checks)\n'
            ' */\n'
        ),
        'comment_no_desc': Template(
            '/**\n'
            ' * @brief  Role function: $title\n'
            ' * @param  transition  Transition context (may be NULL: called from ISR)\n'
            ' * @param  ctx         System context pointer\n'
            ' * @return 0: success, non-zero: error (can also be used for condition checks)\n'
            ' */\n'
        ),
        'signature_open': Template('int $func_name(\n'),
        'signature_args': Template(
            '    const $context_type *transition,\n'
            '    SystemContext_t *ctx\n'
        ),
        'declaration_close': ');\n',
    }

    # ================================================================
    # [Table 2] Implementation templates (with NULL guard)
    # ================================================================
    IMPLEMENTATION_TEMPLATES = {
        'comment_with_desc': Template(
            '/**\n'
            ' * @brief  Role function: $title\n'
            ' * @note   $description\n'
            '$call_sites'
            ' */\n'
        ),
        'comment_no_desc': Template(
            '/**\n'
            ' * @brief  Role function: $title\n'
            '$call_sites'
            ' */\n'
        ),
        'signature_open': Template('int $func_name(\n'),
        'signature_args': Template(
            '    const $context_type *transition,\n'
            '    SystemContext_t *ctx\n'
        ),
        'body_open': ')\n{\n',

        'null_guard_header': (
            '    /* ===== transition NULL guard (supports ISR calls) ===== */\n'
        ),
        'null_guard_decl': Template(
            '    $c_type $member_name = $max_value;\n'
        ),
        'null_guard_check': (
            '    if (transition != NULL) {\n'
        ),
        'null_guard_assign': Template(
            '        $member_name = transition->$member_name;\n'
        ),
        'null_guard_close': (
            '    }\n'
        ),
        'null_guard_suppress': Template(
            '    (void)$member_name;   /* suppress unused warning */\n'
        ),

        'unused_ctx': '    (void)ctx;         /* suppress unused argument warning */\n',
        'blank': '\n',

        'local_transition_id_header': (
            '    /* ===== transition ID (index within call_sites) ===== */\n'
        ),
        # [v3.2 / MISRA 17.7] 宣言直後に (void) で参照を明示。
        # ユーザーコードマーカー内では自由に使用可能。
        'local_transition_id_decl': Template(
            '    const uint16_t transition_id = Transition_GetId(\n'
            '        transition, $table_arg, $count_arg);\n'
            '    (void)transition_id;   /* suppress unused warning */\n'
        ),

        'local_data_header': '    /* ===== local pointer to ctx->data ===== */\n',
        'local_data_pointer': Template(
            '    $c_type *const $var_name = &ctx->data.$var_name;'
            '  /* $comment */\n'
        ),
        'local_data_array': Template(
            '    $c_type *const $var_name = ctx->data.$var_name;'
            '  /* $comment */\n'
        ),

        'local_ret_header': '    /* ===== return value ===== */\n',
        'local_ret_decl': '    int ret = 0;   /* can be modified in user code */\n',

        'todo_comment': Template('    /* $todo */\n'),
        'user_marker_start': Template(
            '    /* [[STABLE_USER_CODE_START:$marker_name]] */\n'
        ),
        'user_marker_hint': '    /* Write user implementation code here */\n',
        'user_marker_end': Template(
            '    /* [[STABLE_USER_CODE_END:$marker_name]] */\n'
        ),

        'return_default': '    return ret;\n',
        'body_close': '}\n',
    }

    # ================================================================
    # [Table 3] TRANSITION_ID_NONE constant
    # ================================================================
    NONE_DEFINE_TEMPLATES = {
        'section_comment': (
            '\n'
            '/* ============================================================== */\n'
            '/*  Transition ID constant                                        */\n'
            '/* ============================================================== */\n'
        ),
        'define': '#define TRANSITION_ID_NONE   ((uint16_t)0xFFFF)\n',
    }

    # ================================================================
    # [Table 4] Common struct for call site tables
    # ================================================================
    ENTRY_STRUCT_TEMPLATES = {
        'section_comment': (
            '\n'
            '/* ============================================================== */\n'
            '/*  Role function call site table (common struct)                 */\n'
            '/*  Identify cells by {from_state, event} pair                    */\n'
            '/* ============================================================== */\n'
        ),
        'struct_typedef': Template(
            'typedef struct {\n'
            '    $state_type from_state;   /* source state */\n'
            '    $event_type event;        /* event */\n'
            '} $entry_type;\n'
        ),
    }

    # ================================================================
    # [Table 5] Transition_GetId
    # ================================================================
    TRANSITION_ID_FUNC_TEMPLATES = {
        'prototype_comment': (
            '\n'
            '/* Transition_GetId forward declaration (body at end of file) */\n'
        ),
        'prototype': Template(
            'static uint16_t Transition_GetId(\n'
            '    const $context_type *transition,\n'
            '    const $entry_type *table,\n'
            '    uint16_t table_size);\n'
        ),
        'definition_comment': (
            '\n\n'
            '/* ============================================================== */\n'
            '/*  Transition ID conversion (end of file)                        */\n'
            '/*  Linearly scans the per-function call_sites table and          */\n'
            '/*  returns the index of the matching entry.                      */\n'
            '/*  Returns TRANSITION_ID_NONE if no match / transition==NULL.    */\n'
            '/* ============================================================== */\n'
            '/**\n'
            ' * @brief  Convert transition info to a unique ID\n'
            ' * @param  transition  Transition context (may be NULL)\n'
            ' * @param  table       Call site table (may be NULL)\n'
            ' * @param  table_size  Number of entries in the table\n'
            ' * @return Index in the table (TRANSITION_ID_NONE if no match)\n'
            ' */\n'
        ),
        'definition': Template(
            'static uint16_t Transition_GetId(\n'
            '    const $context_type *transition,\n'
            '    const $entry_type *table,\n'
            '    uint16_t table_size)\n'
            '{\n'
            '    uint16_t i;\n'
            '\n'
            '    if (transition == NULL || table == NULL) {\n'
            '        return TRANSITION_ID_NONE;\n'
            '    }\n'
            '\n'
            '    for (i = 0; i < table_size; i++) {\n'
            '        if (table[i].from_state == transition->from_state &&\n'
            '            table[i].event      == transition->event) {\n'
            '            return i;\n'
            '        }\n'
            '    }\n'
            '    return TRANSITION_ID_NONE;\n'
            '}\n'
        ),
    }

    # ================================================================
    # [Table 6] Per-function call_sites table
    # ================================================================
    CALL_SITE_TABLE_TEMPLATES = {
        'table_header': Template(
            '\n/* --- call site table for $func_name --- */\n'
        ),
        'table_open': Template(
            'static const $struct_type $table_name[] = {\n'
        ),
        'entry': Template(
            '    { $from_state,$event },\n'
        ),
        'table_close': '};\n',
        'count_macro': Template(
            '#define $count_macro \\\n'
            '    (sizeof($table_name) / sizeof($table_name[0]))\n'
        ),
    }

    # ================================================================
    # [Table 7] Call site comments
    # ================================================================
    CALL_SITES_COMMENT_TEMPLATES = {
        'header': ' *\n * @note   Call sites:\n',
        'line': Template(
            ' *         - [$kind]$kind_pad  $from_state$from_pad'
            ' -[$event]-> $target\n'
        ),
        'none': ' *\n * @note   Call sites: (none)\n',
    }

    # ================================================================
    # [Table 8] User-added area at end of file
    # ================================================================
    TAIL_USER_SECTION_TEMPLATES = {
        'section_comment': (
            '\n\n'
            '/* ============================================================== */\n'
            '/*  User-added area                                               */\n'
            '/*  Code added here is preserved across regenerations             */\n'
            '/* ============================================================== */\n'
        ),
        'marker_start': '/* [[STABLE_USER_CODE_TAIL_START]] */\n',
        'default_hint': '/* Write user-added code here (helper functions, etc.) */\n',
        'marker_end': '/* [[STABLE_USER_CODE_TAIL_END]] */\n',
    }

    # ================================================================
    # Constructor
    # ================================================================
    def __init__(self):
        self.mapper = CTypeMapper()
        self.naming = CNamingConvention()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        self.merger = CodeMerger()
        self.layer_name: str = ""

    def set_layer(self, layer_name: str):
        self.layer_name = layer_name

    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)

    # ================================================================
    # Name generation (namespace support)
    # ================================================================
    def _resolve_name_and_namespace(self, func) -> tuple:
        name = getattr(func, 'name', 'unnamed')
        namespace = getattr(func, 'namespace', '') or ''
        if not namespace and self.layer_name:
            namespace = self.layer_name
        return name, namespace

    def _generate_function_name(self, func) -> str:
        """RoleFunc_<Namespace>_<PascalName>"""
        name, namespace = self._resolve_name_and_namespace(func)
        pascal = self.naming.to_pascal_case(name)
        if namespace:
            return f"RoleFunc_{namespace}_{pascal}"
        return f"RoleFunc_{pascal}"

    def _get_marker_name(self, func) -> str:
        name, namespace = self._resolve_name_and_namespace(func)
        pascal = self.naming.to_pascal_case(name)
        if namespace:
            return f"{namespace}_{pascal}"
        return pascal

    def _get_short_name(self, func) -> str:
        return self.naming.to_pascal_case(getattr(func, 'name', 'unnamed'))

    def _context_type(self) -> str:
        if self.layer_name:
            return f"TransitionContext_{self.layer_name}_t"
        return "TransitionContext_t"

    def _state_type(self) -> str:
        return f"STATE_{self.layer_name}_t" if self.layer_name else "STATE_t"

    def _event_type(self) -> str:
        return f"EVENT_{self.layer_name}_t" if self.layer_name else "EVENT_t"

    def _state_enum(self, state_name: str) -> str:
        s = self.naming.to_pascal_case(state_name) if state_name else "Unknown"
        return f"STATE_{self.layer_name}_{s}" if self.layer_name else f"STATE_{s}"

    def _event_enum(self, event_name: str) -> str:
        e = self.naming.to_upper_snake(event_name) if event_name else "NONE"
        return f"EVENT_{self.layer_name}_{e}" if self.layer_name else f"EVENT_{e}"

    def _state_max(self) -> str:
        return f"STATE_{self.layer_name}_MAX" if self.layer_name else "STATE_MAX"

    def _event_none(self) -> str:
        return f"EVENT_{self.layer_name}_NONE" if self.layer_name else "EVENT_NONE"

    def _entry_struct_type(self) -> str:
        return (f"RoleFuncCallSiteEntry_{self.layer_name}_t"
                if self.layer_name else "RoleFuncCallSiteEntry_t")

    # ================================================================
    # Deduplication
    # ================================================================
    def _dedupe_by_name(self, funcs: Iterable) -> List:
        seen = set()
        result = []
        for func in funcs:
            name = getattr(func, 'name', None)
            namespace = getattr(func, 'namespace', '') or ''
            if not name:
                self._log_debug(
                    f"_dedupe_by_name: skip (no name): {func!r}",
                    'warning'
                )
                continue
            key = f"{namespace}.{name}" if namespace else name
            if key in seen:
                self._log_debug(
                    f"_dedupe_by_name: duplicate skipped: {key}"
                )
                continue
            seen.add(key)
            result.append(func)
        return result

    def _resolve_comment_title(self, func) -> str:
        title = getattr(func, 'title', '')
        name = getattr(func, 'name', 'unnamed')
        qualified = getattr(func, 'qualified_name', name)
        if title and title != f"Role function: {name}" \
                and title != f"Role function: {qualified}":
            return title
        return qualified

    # ================================================================
    # v1.5: reference normalization (with identifier validation)
    # ================================================================
    def _normalize_func_ref(self, ref: str) -> str:
        if not ref:
            return ""
        name = ref.strip()
        if not name:
            return ""

        # 1. Strip argument part
        if '(' in name:
            name = name.split('(', 1)[0].strip()

        # 2. Handle RoleFunc_ prefix
        if name.startswith("RoleFunc_"):
            rest = name[len("RoleFunc_"):]
            if self.layer_name:
                prefix = f"{self.layer_name}_"
                if rest.startswith(prefix):
                    candidate = f"{self.layer_name}.{rest[len(prefix):]}"
                    if _VALID_QUALIFIED.match(candidate):
                        return candidate
                    self._log_debug(
                        f"_normalize_func_ref: reject invalid RoleFunc_ ref: "
                        f"{ref!r} (candidate={candidate!r})",
                        'warning',
                    )
                    return ""
            if _VALID_C_IDENTIFIER.match(rest):
                return rest
            self._log_debug(
                f"_normalize_func_ref: reject invalid RoleFunc_ ref: "
                f"{ref!r} (rest={rest!r})",
                'warning',
            )
            return ""

        # 3. v1.5 addition: identifier validation
        if not _VALID_QUALIFIED.match(name):
            self._log_debug(
                f"_normalize_func_ref: reject invalid identifier: "
                f"{ref!r} (name={name!r})",
                'warning',
            )
            return ""

        return name

    # ================================================================
    # Extract function names from condition expression
    # ================================================================
    def _extract_func_names_from_condition(self, condition: str) -> List[str]:
        if not condition:
            return []
        names = set()

        # 1. RoleFunc_XXX form
        for m in re.finditer(r'\bRoleFunc_\w+', condition):
            names.add(m.group(0))

        # 2. Namespace.Name form
        for m in re.finditer(r'\b([A-Z]\w*)\.([A-Za-z_]\w*)\b', condition):
            names.add(f"{m.group(1)}.{m.group(2)}")

        # 3. function_name(...) form
        for m in re.finditer(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(', condition):
            n = m.group(1)
            if n not in _C_KEYWORDS:
                names.add(n)

        # 4. Whole string is a bare identifier
        stripped = condition.strip()
        if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', stripped):
            if stripped not in _C_KEYWORDS:
                names.add(stripped)

        # 5. Bare identifiers within the expression (PascalCase only)
        for m in re.finditer(r'(?<![.\w])([A-Z]\w*)(?![.\w])', condition):
            n = m.group(1)
            if n not in _C_KEYWORDS:
                names.add(n)

        return [self._normalize_func_ref(n) for n in names if n]

    # ================================================================
    # Call site collection
    # ================================================================
    def _collect_call_sites(self, state_machine
                            ) -> Dict[str, List[RoleFuncCallSite]]:
        """Collect all call sites for role functions.

        [v2.2.5 fix]
          Extended to also collect:
            - State entry / exit references
            - Cell-level actions (before_transitions / after_transitions)
        """
        if state_machine is None:
            return {}
        call_map: Dict[str, List[RoleFuncCallSite]] = {}
        seen = set()

        # ---- 1. Transition-level refs ----
        for state in state_machine.states.values():
            for event in state_machine.events.values():
                transitions = state_machine.get_transitions_for_cell(
                    state.name, event.name
                )
                for trans in transitions:
                    target = getattr(trans, 'target', '') or ''
                    cond = getattr(trans, 'condition', '') or ''
                    for fname in self._extract_func_names_from_condition(cond):
                        key = (fname, 'condition', state.name, event.name)
                        if key in seen:
                            continue
                        seen.add(key)
                        call_map.setdefault(fname, []).append(RoleFuncCallSite(
                            fname, 'condition',
                            state.name, event.name, target,
                        ))
                    for action in ensure_list(
                            getattr(trans, 'pre_actions', [])):
                        norm = self._normalize_func_ref(action)
                        if not norm:
                            continue
                        key = (norm, 'pre_action', state.name, event.name)
                        if key in seen:
                            continue
                        seen.add(key)
                        call_map.setdefault(norm, []).append(RoleFuncCallSite(
                            norm, 'pre_action',
                            state.name, event.name, target,
                        ))
                    else_target = getattr(trans, 'else_target', '') or ''
                    for action in ensure_list(
                            getattr(trans, 'else_actions', [])):
                        norm = self._normalize_func_ref(action)
                        if not norm:
                            continue
                        key = (norm, 'else_action', state.name, event.name)
                        if key in seen:
                            continue
                        seen.add(key)
                        call_map.setdefault(norm, []).append(RoleFuncCallSite(
                            norm, 'else_action',
                            state.name, event.name,
                            else_target or target,
                        ))

        # ---- 2. v2.2.5: State entry / exit refs ----
        for state in state_machine.states.values():
            for fname in ensure_list(getattr(state, 'entry', [])):
                norm = self._normalize_func_ref(fname)
                if not norm:
                    continue
                key = (norm, 'state_entry', state.name, '')
                if key in seen:
                    continue
                seen.add(key)
                call_map.setdefault(norm, []).append(RoleFuncCallSite(
                    norm, 'state_entry', state.name, '', state.name,
                ))
            for fname in ensure_list(getattr(state, 'exit', [])):
                norm = self._normalize_func_ref(fname)
                if not norm:
                    continue
                key = (norm, 'state_exit', state.name, '')
                if key in seen:
                    continue
                seen.add(key)
                call_map.setdefault(norm, []).append(RoleFuncCallSite(
                    norm, 'state_exit', state.name, '', state.name,
                ))

        # ---- 3. v2.2.5: Cell-level actions ----
        if hasattr(state_machine, 'get_cell_keys'):
            try:
                cell_keys = state_machine.get_cell_keys()
            except Exception:
                cell_keys = []
            for cell_key in cell_keys:
                try:
                    source, event = cell_key
                except Exception:
                    continue
                for action in state_machine.get_actions_for_cell(
                        source, event):
                    rf = getattr(action, 'role_function', '') or ''
                    norm = self._normalize_func_ref(rf)
                    if not norm:
                        continue
                    trigger = getattr(action, 'trigger',
                                      'before_transitions')
                    kind = f'cell_action_{trigger}'
                    key = (norm, kind, source, event)
                    if key in seen:
                        continue
                    seen.add(key)
                    call_map.setdefault(norm, []).append(RoleFuncCallSite(
                        norm, kind, source, event, '',
                    ))

        self._log_debug(
            f"_collect_call_sites: {len(call_map)} funcs, "
            f"{sum(len(v) for v in call_map.values())} call sites"
        )
        return call_map

    def _get_call_sites_for_func(
        self, func, call_map: Dict[str, List[RoleFuncCallSite]],
    ) -> List[RoleFuncCallSite]:
        qualified = getattr(func, 'qualified_name', None) or ''
        if qualified:
            cs = call_map.get(qualified, [])
            if cs:
                return cs
        bare = getattr(func, 'name', '')
        if bare:
            return call_map.get(bare, [])
        return []

    def _format_call_sites_comment(self, call_sites) -> str:
        T = self.CALL_SITES_COMMENT_TEMPLATES
        if not call_sites:
            return T['none']
        kind_width = max(len(cs.kind) for cs in call_sites)
        from_width = max(
            len(self._state_enum(cs.from_state)) for cs in call_sites
        )
        event_width = max(
            len(self._event_enum(cs.event)) for cs in call_sites
        )
        parts = [T['header']]
        for cs in call_sites:
            from_str = self._state_enum(cs.from_state)
            event_str = self._event_enum(cs.event)
            target_str = (self._state_enum(cs.target)
                          if cs.target else '(not set)')
            parts.append(T['line'].substitute(
                kind=cs.kind,
                kind_pad=' ' * (kind_width - len(cs.kind)),
                from_state=from_str,
                from_pad=' ' * (from_width - len(from_str)),
                event=event_str,
                target=target_str,
            ))
        return ''.join(parts)

    # ================================================================
    # v1.6 sec 9.6 #90 Option A: layer filter decision
    # ================================================================
    def _should_emit_implementation(self, func, call_map) -> bool:
        """Decide whether to emit this function's implementation.

        Conditions for emission:
          1. Self-layer function
             (namespace == self.layer_name, OR namespace is a prefix
              of / equal to the layer_name modulo case)
          2. Function called from this layer's transitions /
             state entry-exit / cell actions (has an entry in call_map)

        [v2.2.5 fix]
          Namespace prefix matching added: XML often uses short namespaces
          (e.g. namespace="App" for layer_name="Application"), which
          previously caused self-layer functions to be dropped.

        Otherwise (other-layer function with no caller) is skipped to
        prevent emitting many empty stubs for other layers.
        """
        namespace = getattr(func, 'namespace', '') or ''
        layer = self.layer_name or ''

        # 1a. Exact match
        if namespace == layer:
            return True

        # 1b. v2.2.5: prefix match (App <-> Application, Drv <-> Driver)
        if namespace and layer:
            ns_l, ly_l = namespace.lower(), layer.lower()
            if ly_l.startswith(ns_l) or ns_l.startswith(ly_l):
                # Require at least 3 chars to avoid spurious short matches
                if min(len(ns_l), len(ly_l)) >= 3:
                    return True

        # 2. Caller in this layer
        qn = getattr(func, 'qualified_name', None) or ''
        if qn and call_map.get(qn):
            return True
        bare = getattr(func, 'name', '') or ''
        if bare and call_map.get(bare):
            return True

        return False

    # ================================================================
    # Generation methods
    # ================================================================
    def generate_none_define(self) -> str:
        T = self.NONE_DEFINE_TEMPLATES
        return T['section_comment'] + T['define']

    def generate_entry_struct(self) -> str:
        T = self.ENTRY_STRUCT_TEMPLATES
        return (
            T['section_comment'] +
            T['struct_typedef'].substitute(
                state_type=self._state_type(),
                event_type=self._event_type(),
                entry_type=self._entry_struct_type(),
            )
        )

    def generate_transition_id_prototype(self) -> str:
        T = self.TRANSITION_ID_FUNC_TEMPLATES
        return (
            T['prototype_comment'] +
            T['prototype'].substitute(
                context_type=self._context_type(),
                entry_type=self._entry_struct_type(),
            )
        )

    def generate_transition_id_function(self) -> str:
        T = self.TRANSITION_ID_FUNC_TEMPLATES
        return (
            T['definition_comment'] +
            T['definition'].substitute(
                context_type=self._context_type(),
                entry_type=self._entry_struct_type(),
            )
        )

    def generate_call_sites_table(self, func, call_sites) -> str:
        if not call_sites:
            return ""

        short = self._get_short_name(func)
        table_name = f"call_sites_{short}"
        count_macro = f"CALL_SITES_{short}_COUNT"

        unique_entries = []
        seen = set()
        for cs in call_sites:
            k = cs.key()
            if k in seen:
                continue
            seen.add(k)
            unique_entries.append(cs)

        if not unique_entries:
            return ""

        from_strs = [self._state_enum(cs.from_state)
                     for cs in unique_entries]
        from_width = max(len(s) for s in from_strs)

        T = self.CALL_SITE_TABLE_TEMPLATES
        parts = [
            T['table_header'].substitute(func_name=short),
            T['table_open'].substitute(
                struct_type=self._entry_struct_type(),
                table_name=table_name,
            ),
        ]

        for cs in unique_entries:
            from_str = self._state_enum(cs.from_state)
            event_str = self._event_enum(cs.event)
            pad = ' ' * (from_width - len(from_str) + 1)
            parts.append(T['entry'].substitute(
                from_state=from_str,
                event=pad + event_str,
            ))

        parts.append(T['table_close'])
        parts.append(T['count_macro'].substitute(
            count_macro=count_macro,
            table_name=table_name,
        ))
        return ''.join(parts)

    def generate_tail_user_section(self) -> str:
        T = self.TAIL_USER_SECTION_TEMPLATES
        return ''.join([
            T['section_comment'],
            T['marker_start'],
            T['default_hint'],
            T['marker_end'],
        ])

    def _format_var_comment(self, var) -> str:
        description = getattr(var, 'description', '') or ''
        unit = getattr(var, 'unit', '') or ''
        if description and unit:
            return f"{description} [{unit}]"
        return description or unit or ""

    def _generate_local_transition_members(self) -> str:
        T = self.IMPLEMENTATION_TEMPLATES
        parts = [
            T['null_guard_header'],
            T['null_guard_decl'].substitute(
                c_type=self._state_type(),
                member_name='from_state',
                max_value=self._state_max(),
            ),
            T['null_guard_decl'].substitute(
                c_type=self._event_type(),
                member_name='event',
                max_value=self._event_none(),
            ),
            T['null_guard_check'],
            T['null_guard_assign'].substitute(member_name='from_state'),
            T['null_guard_assign'].substitute(member_name='event'),
            T['null_guard_close'],
            T['null_guard_suppress'].substitute(member_name='from_state'),
            T['null_guard_suppress'].substitute(member_name='event'),
            T['blank'],
        ]
        return ''.join(parts)

    def _generate_local_transition_id(self, func,
                                      has_call_sites: bool) -> str:
        T = self.IMPLEMENTATION_TEMPLATES
        if has_call_sites:
            short = self._get_short_name(func)
            table_arg = f"call_sites_{short}"
            count_arg = f"(uint16_t)CALL_SITES_{short}_COUNT"
        else:
            table_arg = "NULL"
            count_arg = "0"

        return ''.join([
            T['local_transition_id_header'],
            T['local_transition_id_decl'].substitute(
                table_arg=table_arg,
                count_arg=count_arg,
            ),
            T['blank'],
        ])

    def _generate_local_data_pointers(self, global_defs) -> str:
        """Generate local pointers to ctx->data and explicitly discard
        them with (void) so that unused ones don't raise warnings.

        [v3.2 / MISRA 17.7 / unreadVariable]
          User code marker may use only a subset of these pointers.
          The (void) cast suppresses the warning while leaving the
          pointers usable inside the marker.
        """
        if global_defs is None:
            return ""
        variables = getattr(global_defs, 'variables', []) or []
        if not variables:
            return ""
        T = self.IMPLEMENTATION_TEMPLATES
        parts = [T['local_data_header']]
        for var in variables:
            var_name = self.naming.sanitize_identifier(
                getattr(var, 'name', 'unnamed')
            )
            c_type = self.mapper.map_type(
                getattr(var, 'type', 'void')
            )
            comment = self._format_var_comment(var)
            array_size = getattr(var, 'array_size', 0)
            if array_size > 0:
                parts.append(T['local_data_array'].substitute(
                    c_type=c_type, var_name=var_name,
                    comment=comment,
                ))
            else:
                parts.append(T['local_data_pointer'].substitute(
                    c_type=c_type, var_name=var_name,
                    comment=comment,
                ))
        # [v3.2] Explicit discard to suppress unreadVariable warnings.
        for var in variables:
            var_name = self.naming.sanitize_identifier(
                getattr(var, 'name', 'unnamed')
            )
            parts.append(f'    (void){var_name};'
                         f'   /* suppress unused warning */\n')
        parts.append(T['blank'])
        return ''.join(parts)

    def _has_local_data_pointers(self, global_defs) -> bool:
        if global_defs is None:
            return False
        return bool(getattr(global_defs, 'variables', []) or [])

    def _generate_local_retvar(self) -> str:
        T = self.IMPLEMENTATION_TEMPLATES
        return ''.join([
            T['local_ret_header'],
            T['local_ret_decl'],
            T['blank'],
        ])

    def generate_declaration(self, func) -> str:
        T = self.DECLARATION_TEMPLATES
        parts = []
        title = self._resolve_comment_title(func)
        description = getattr(func, 'description', '')
        if description:
            parts.append(T['comment_with_desc'].substitute(
                title=title, description=description,
            ))
        else:
            parts.append(T['comment_no_desc'].substitute(title=title))
        parts.append(T['signature_open'].substitute(
            func_name=self._generate_function_name(func),
        ))
        parts.append(T['signature_args'].substitute(
            context_type=self._context_type(),
        ))
        parts.append(T['declaration_close'])
        return ''.join(parts)

    def generate_implementation(self, func, global_defs=None,
                                call_sites=None,
                                include_transition_id: bool = True) -> str:
        T = self.IMPLEMENTATION_TEMPLATES
        parts = []

        title = self._resolve_comment_title(func)
        description = getattr(func, 'description', '')
        call_sites_comment = self._format_call_sites_comment(
            call_sites or []
        )

        if description:
            parts.append(T['comment_with_desc'].substitute(
                title=title, description=description,
                call_sites=call_sites_comment,
            ))
        else:
            parts.append(T['comment_no_desc'].substitute(
                title=title, call_sites=call_sites_comment,
            ))

        parts.append(T['signature_open'].substitute(
            func_name=self._generate_function_name(func),
        ))
        parts.append(T['signature_args'].substitute(
            context_type=self._context_type(),
        ))
        parts.append(T['body_open'])

        parts.append(self._generate_local_transition_members())

        if include_transition_id:
            has_cs = bool(call_sites)
            parts.append(self._generate_local_transition_id(func, has_cs))

        if self._has_local_data_pointers(global_defs):
            parts.append(self._generate_local_data_pointers(global_defs))
        else:
            parts.append(T['unused_ctx'])

        parts.append(self._generate_local_retvar())

        parts.append(T['todo_comment'].substitute(
            todo=self.strings['todo']
        ))
        parts.append(T['blank'])

        marker_name = self._get_marker_name(func)
        parts.append(T['user_marker_start'].substitute(
            marker_name=marker_name
        ))
        parts.append(T['user_marker_hint'])
        parts.append(T['user_marker_end'].substitute(
            marker_name=marker_name
        ))
        parts.append(T['blank'])

        parts.append(T['return_default'])
        parts.append(T['body_close'])
        return ''.join(parts)

    def generate_call(self, func_name: str) -> str:
        if func_name.startswith("RoleFunc_"):
            full_name = func_name
        elif '.' in func_name:
            ns, name = func_name.split('.', 1)
            full_name = (f"RoleFunc_{ns}_"
                         f"{self.naming.to_pascal_case(name)}")
        elif self.layer_name:
            full_name = (f"RoleFunc_{self.layer_name}_"
                         f"{self.naming.to_pascal_case(func_name)}")
        else:
            full_name = (f"RoleFunc_"
                         f"{self.naming.to_pascal_case(func_name)}")
        return f"{full_name}(transition, ctx)"

    def generate_all_declarations(self, role_functions: List) -> str:
        unique_funcs = self._dedupe_by_name(role_functions)
        parts = []
        for func in unique_funcs:
            parts.append(self.generate_declaration(func))
            parts.append('\n')
        return ''.join(parts)

    def generate_all_implementations(self, role_functions: List,
                                     state_machine=None,
                                     global_defs=None) -> str:
        """
        Generate the implementation set for this layer's file.

        [v2.2.5]
          Filtering now includes:
            - Self-layer functions (namespace == layer_name or prefix match)
            - Functions called from this layer's transitions, state
              entry/exit, or cell actions
        """
        unique_funcs = self._dedupe_by_name(role_functions)
        include_transition_id = state_machine is not None
        call_map = self._collect_call_sites(state_machine) \
            if include_transition_id else {}

        # v1.5 addition: detect undefined references (before filtering)
        if call_map:
            defined_keys = set()
            for f in unique_funcs:
                qn = getattr(f, 'qualified_name', None) \
                    or getattr(f, 'name', '')
                if qn:
                    defined_keys.add(qn)
            for ref in call_map.keys():
                if ref and ref not in defined_keys:
                    self._log_debug(
                        f"Undefined role function reference in "
                        f"transitions: '{ref}' (not in role_functions)",
                        'warning',
                    )

        # v1.6 sec 9.6 #90 Option A: layer filter
        filtered_funcs = [
            f for f in unique_funcs
            if self._should_emit_implementation(f, call_map)
        ]
        skipped = len(unique_funcs) - len(filtered_funcs)
        if skipped:
            self._log_debug(
                f"generate_all_implementations: "
                f"layer='{self.layer_name}', "
                f"emitted={len(filtered_funcs)}, "
                f"skipped={skipped} "
                f"(not self-layer and no caller in this layer)"
            )

        parts = []

        if include_transition_id:
            parts.append(self.generate_none_define())
            parts.append('\n')
            parts.append(self.generate_entry_struct())
            parts.append('\n')
            parts.append(self.generate_transition_id_prototype())
            parts.append('\n')

            for func in filtered_funcs:
                call_sites = self._get_call_sites_for_func(func, call_map)
                table_code = self.generate_call_sites_table(
                    func, call_sites
                )
                if table_code:
                    parts.append(table_code)
                    parts.append('\n')

            parts.append('\n')

        for func in filtered_funcs:
            call_sites = self._get_call_sites_for_func(func, call_map)
            parts.append(self.generate_implementation(
                func, global_defs, call_sites, include_transition_id,
            ))
            parts.append('\n')

        if include_transition_id:
            parts.append(self.generate_transition_id_function())

        parts.append(self.generate_tail_user_section())

        return ''.join(parts)

    def _collect_args(self, func) -> List[tuple]:
        return [
            (
                'transition',
                f'const TransitionContext_{self.layer_name}_t *'
                if self.layer_name else 'const TransitionContext_t *',
                'transition context',
            ),
            ('ctx', 'SystemContext_t *', 'system context pointer'),
        ]