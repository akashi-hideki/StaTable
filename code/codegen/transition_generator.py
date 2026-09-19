# codegen/transition_generator.py
"""
State transition function generation module (v2.2 multi-transition + nesting support).

Version: 2.2.1 (2026-09-19)
  - Fix: Nested group emitted duplicate transition blocks when parent
    and child both declared the same members. Now the parent skips
    labels that any descendant declares (see _collect_child_labels).
  - Fix: Section header is now a valid C block comment (see c_code_generator).

[v2.2 changes]
  - Multiple transitions per cell
  - `_handled` guard pattern (Commit / Tentative)
  - Cell actions (before_transitions / after_transitions)
  - Relations (group with shared_condition)
  - State entry / exit calls from State.entry / State.exit
  - §12-5: Recursive group nesting via TransitionRelation.children
  - Backward compatible: single transition without cell metadata
"""

import sys
import os
import logging
from string import Template
from typing import Dict, List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statable.model import State, Event, Transition
from statable.state_machine import StateMachine

try:
    from .type_mapper import CTypeMapper
    from .naming_convention import CNamingConvention
    from .code_templates import CodeTemplates
except ImportError:
    from type_mapper import CTypeMapper
    from naming_convention import CNamingConvention
    from code_templates import CodeTemplates

logger = logging.getLogger(__name__)


# ======================================================================
# Helpers
# ======================================================================
def ensure_list(value) -> List[str]:
    """Normalize str/None/list to List[str]."""
    if value is None:
        return []
    if isinstance(value, str):
        s = value.strip()
        return [s] if s else []
    if isinstance(value, list):
        return [str(x) for x in value if str(x).strip()]
    return [str(value)]


class TransitionGenerator:
    """State transition function generator (v2.2 multi-transition support)"""

    SHORT_CELL_NAMES = True
    TABLE_MIN_COL_WIDTH = 14
    DEFAULT_TABLE_TYPE = 'array'
    DEFAULT_GENERATION_STYLE = 'table_driven'

    # ==================================================================
    # [v2.2] Cell function templates
    # ==================================================================
    CELL_TEMPLATES = {
        'header': Template(
            '/**\n'
            ' * @brief  Cell transition: $state_enum -[$event_enum]-> (multi)\n'
            ' * @note   Transition count: $transition_count\n'
            ' */\n'
        ),
        'signature': Template(
            'static $state_type $func_name(\n'
            '    const $context_type *transition,\n'
            '    SystemContext_t *ctx\n'
            ')\n'
            '{\n'
        ),
        'body_open': Template(
            '    $state_type next_state = transition->from_state;\n'
            '    bool _handled = false;\n'
        ),
        'body_open_simple': Template(
            '    $state_type next_state = transition->from_state;\n'
        ),
        'cell_actions_header': Template(
            '\n'
            '    /* ===== Cell actions ($trigger) ===== */\n'
        ),
        'cell_action_call': Template('    $call;\n'),
        'body_close': (
            '\n'
            '    return next_state;\n'
            '}\n'
        ),
    }

    # ==================================================================
    # Forward declarations
    # ==================================================================
    CELL_PROTO_TEMPLATES = {
        'section_comment': '/* ===== Cell transition function forward declarations ===== */\n',
        'prototype': Template(
            'static $state_type $func_name(\n'
            '    const $context_type *transition,\n'
            '    SystemContext_t *ctx);\n'
        ),
    }

    # ==================================================================
    # Transition table
    # ==================================================================
    TABLE_TEMPLATES = {
        'func_ptr_comment': '/* Transition function pointer type */\n',
        'func_ptr_typedef': Template(
            'typedef $state_type (*$func_type)(\n'
            '    const $context_type *, SystemContext_t *);\n'
        ),
        'table_comment': Template(
            '\n'
            '/* ============================================================== */\n'
            '/*  State transition table: rows=$row_desc, cols=$col_desc      */\n'
            '/*  Global variable (externally accessible)                     */\n'
            '/* ============================================================== */\n'
        ),
        'table_open': Template(
            'const $func_type $table_name\n'
            '    [$state_max][$event_max] = {\n'
        ),
        'table_close': '};\n',
    }

    TABLE_HEADER_TEMPLATES = {
        'header_comment': Template(
            '/**\n'
            ' * @brief  Transition table ($layer layer)\n'
            ' * @note   rows=$row_desc, cols=$col_desc\n'
            ' */\n'
        ),
        'func_ptr_typedef': Template(
            'typedef $state_type (*$func_type)(\n'
            '    const $context_type *, SystemContext_t *);\n'
        ),
        'extern_decl': Template(
            'extern const $func_type $table_name\n'
            '    [$state_max][$event_max];\n'
        ),
    }

    # ==================================================================
    # Function dictionary
    # ==================================================================
    DICT_TEMPLATES = {
        'struct_comment': (
            '/* Transition function dictionary entry */\n'
            '/* Used for debugging, logging, and dynamic dispatch */\n'
        ),
        'struct_open': (
            'typedef struct {\n'
            '    const char *name;\n'
        ),
        'struct_field_from': Template('    $state_type from_state;\n'),
        'struct_field_event': Template('    $event_type event;\n'),
        'struct_field_target': Template('    $state_type default_target;\n'),
        'struct_field_condition': '    const char *condition;\n',
        'struct_field_func': Template('    $func_type func;\n'),
        'struct_close': Template('}} $dict_type;\n'),
        'dict_comment': '\n/* Transition function dictionary */\n',
        'dict_open': Template('static const $dict_type $dict_name[] = {\n'),
        'dict_entry': Template(
            '    { "$trans_name",\n'
            '      $state_enum, $event_enum, $target_enum,\n'
            '      "$condition", $func_name },\n'
        ),
        'dict_close': '};\n',
        'dict_size': Template(
            '\n'
            '#define $size_macro \\\n'
            '    (sizeof($dict_name) / sizeof($dict_name[0]))\n'
        ),
    }

    # ==================================================================
    # Process function
    # ==================================================================
    PROCESS_TEMPLATES = {
        'comment': Template(
            '/**\n'
            ' * @brief  $layer layer state transition processing\n'
            ' * @param  current_state  Current state\n'
            ' * @param  event          Event that occurred\n'
            ' * @param  ctx            System context pointer\n'
            ' * @return State after transition\n'
            ' */\n'
        ),
        'signature': Template(
            '$state_type $func_name(\n'
            '    $state_type current_state,\n'
            '    $event_type event,\n'
            '    SystemContext_t *ctx\n'
            ')\n'
        ),
        'body': Template(
            '{\n'
            '    $context_type transition = {\n'
            '        .from_state = current_state,\n'
            '        .event = event,\n'
            '    };\n'
            '    $func_type func = $table_name[current_state][event];\n'
            '    if (func != NULL) {\n'
            '        return func(&transition, ctx);\n'
            '    }\n'
            '    return current_state;\n'
            '}\n'
        ),
    }

    # ==================================================================
    # GetNextEvent
    # ==================================================================
    GET_NEXT_TEMPLATES = {
        'comment': Template(
            '/**\n'
            ' * @brief  Get next event for $layer layer\n'
            ' * @param  ctx  System context pointer\n'
            ' * @return Next event ($event_none if no pending event)\n'
            ' */\n'
        ),
        'signature': Template('$event_type $func_name(SystemContext_t *ctx)\n'),
        'body': Template(
            '{\n'
            '    static uint8_t consecutive_count = 0;\n'
            '\n'
            '    if (ctx->pending_event_valid) {\n'
            '        consecutive_count++;\n'
            '        if (consecutive_count > MAX_CONSECUTIVE_PENDING_EVENTS) {\n'
            '            LOG_ERROR("Pending event chain too long (%d)", consecutive_count);\n'
            '            ctx->pending_event_valid = false;\n'
            '            consecutive_count = 0;\n'
            '            return $event_none;\n'
            '        }\n'
            '        $event_type evt = ($event_type)ctx->pending_event;\n'
            '        ctx->pending_event_valid = false;\n'
            '        return evt;\n'
            '    }\n'
            '    consecutive_count = 0;\n'
            '    return $event_none;\n'
            '}\n'
        ),
    }

    # ==================================================================
    # Constructor
    # ==================================================================
    def __init__(self):
        self.mapper = CTypeMapper()
        self.naming = CNamingConvention()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        self.layer_name: str = ""
        self._current_state_machine: Optional[StateMachine] = None

        self.table_generators: Dict[str, callable] = {
            'array':      self._generate_table_array,
            'switch':     self._generate_table_switch,
            'dictionary': self._generate_table_dictionary,
        }
        self.process_generators: Dict[str, callable] = {
            'table_driven': self._generate_process_table_driven,
            'switch_case':  self._generate_process_switch_case,
        }

    def set_layer(self, layer_name: str):
        self.layer_name = layer_name

    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)

    # ==================================================================
    # Name generation
    # ==================================================================
    def _state_enum(self, state_name: str) -> str:
        s = self.naming.to_pascal_case(state_name) if state_name else "Unknown"
        return f"STATE_{self.layer_name}_{s}" if self.layer_name else f"STATE_{s}"

    def _event_enum(self, event_name: str) -> str:
        e = self.naming.to_upper_snake(event_name) if event_name else "NONE"
        return f"EVENT_{self.layer_name}_{e}" if self.layer_name else f"EVENT_{e}"

    def _state_type(self) -> str:
        return f"STATE_{self.layer_name}_t" if self.layer_name else "STATE_t"

    def _event_type(self) -> str:
        return f"EVENT_{self.layer_name}_t" if self.layer_name else "EVENT_t"

    def _context_type(self) -> str:
        return f"TransitionContext_{self.layer_name}_t" if self.layer_name else "TransitionContext_t"

    def _func_type(self) -> str:
        return f"TransitionFunc_{self.layer_name}_t" if self.layer_name else "TransitionFunc_t"

    def _table_name(self) -> str:
        return f"transition_table_{self.layer_name}" if self.layer_name else "transition_matrix"

    def _state_max(self) -> str:
        return f"STATE_{self.layer_name}_MAX" if self.layer_name else "STATE_MAX"

    def _event_max(self) -> str:
        return f"EVENT_{self.layer_name}_MAX" if self.layer_name else "EVENT_MAX"

    def _cell_func_name(self, state_name: str, event_name: str) -> str:
        s = self.naming.to_pascal_case(state_name) if state_name else "Unknown"
        e = self.naming.to_upper_snake(event_name) if event_name else "NONE"
        if self.SHORT_CELL_NAMES:
            return f"t_{s}_{e}"
        return f"transition_{self.layer_name}_{s}_{e}" if self.layer_name \
            else f"transition_{s}_{e}"

    def _role_func_call(self, func_name: str) -> str:
        """Generate a role function call statement."""
        if not func_name:
            return "/* empty role function reference */"
        if func_name.startswith("RoleFunc_"):
            return f"{func_name}(transition, ctx)"
        if "." in func_name:
            ns, name = func_name.split(".", 1)
            ns_pascal = self.naming.to_pascal_case(ns)
            name_pascal = self.naming.to_pascal_case(name)
            return f"RoleFunc_{ns_pascal}_{name_pascal}(transition, ctx)"
        pascal = self.naming.to_pascal_case(func_name)
        if self.layer_name:
            full = f"RoleFunc_{self.layer_name}_{pascal}"
        else:
            full = f"RoleFunc_{pascal}"
        return f"{full}(transition, ctx)"

    def _role_func_call_bare(self, func_name: str) -> str:
        """Return only the C function name (no call suffix)."""
        if not func_name or not func_name.strip():
            return ""
        full = self._role_func_call(func_name)
        suffix = "(transition, ctx)"
        if full.endswith(suffix):
            return full[:-len(suffix)]
        if full.startswith("/*"):
            return ""
        return full

    # ==================================================================
    # State entry / exit call generation
    # ==================================================================
    def _build_exit_call(self, state_name: str) -> str:
        if not state_name or self._current_state_machine is None:
            return ''
        state = self._current_state_machine.states.get(state_name)
        if state is None:
            return ''
        exit_list = ensure_list(getattr(state, 'exit', []))
        if not exit_list:
            return ''
        lines = []
        for fn in exit_list:
            name = self._role_func_call_bare(fn)
            if not name:
                continue
            lines.append(f'        {name}(transition, ctx);  /* state exit */\n')
        return ''.join(lines)

    def _build_entry_call(self, state_name: str) -> str:
        if not state_name or self._current_state_machine is None:
            return ''
        state = self._current_state_machine.states.get(state_name)
        if state is None:
            return ''
        entry_list = ensure_list(getattr(state, 'entry', []))
        if not entry_list:
            return ''
        lines = []
        for fn in entry_list:
            name = self._role_func_call_bare(fn)
            if not name:
                continue
            lines.append(f'        {name}(transition, ctx);  /* state entry */\n')
        return ''.join(lines)

    # ==================================================================
    # Transition block generation
    # ==================================================================
    def _build_transition_block(self, trans, idx: int) -> str:
        """Build one transition block (Commit / Tentative, with / without else)."""
        condition = getattr(trans, 'condition', '')
        early_return = getattr(trans, 'early_return', False)
        target = getattr(trans, 'target', '')
        else_target = getattr(trans, 'else_target', '')
        pre_actions = ensure_list(getattr(trans, 'pre_actions', []))
        else_actions = ensure_list(getattr(trans, 'else_actions', []))
        has_else = getattr(trans, 'has_else', True)
        label = getattr(trans, 'label', '') or f"T{idx + 1}"

        has_else_body = has_else and bool(else_target or else_actions)
        cond_expr = condition if condition else "1"
        commit_str = "Commit" if early_return else "Tentative"

        exit_calls = self._build_exit_call(trans.source)
        entry_calls = self._build_entry_call(target)
        else_entry_calls = self._build_entry_call(else_target)

        pre_lines = ''.join(
            f'        {self._role_func_call(a)};\n' for a in pre_actions
        )
        else_lines = ''.join(
            f'        {self._role_func_call(a)};\n' for a in else_actions
        )

        target_line = (
            f'        next_state = {self._state_enum(target)};\n'
            if target else ''
        )
        else_target_line = (
            f'        next_state = {self._state_enum(else_target)};\n'
            if else_target else '        /* else target not set */\n'
        )

        lines = []
        lines.append(f'\n    /* ===== Transition[{label}] ({commit_str}) ===== */\n')

        if early_return:
            lines.append(f'    if (!_handled && {cond_expr}) {{\n')
        else:
            lines.append(f'    if ({cond_expr}) {{\n')

        lines.append(exit_calls)
        lines.append(pre_lines)
        lines.append(target_line)
        lines.append(entry_calls)
        if early_return:
            lines.append('        _handled = true;\n')

        if has_else_body:
            if early_return:
                lines.append(f'    }} else if (!_handled && !({cond_expr})) {{\n')
            else:
                lines.append('    } else {\n')

            lines.append(exit_calls)
            lines.append(else_lines)
            lines.append(else_target_line)
            lines.append(else_entry_calls)
            if early_return:
                lines.append('        _handled = true;\n')

        lines.append('    }\n')
        return ''.join(lines)

    # ==================================================================
    # §12-5: Transitions block with recursive group support
    # ==================================================================
    def _build_transitions_block(self, state, transitions, relations) -> str:
        """Build the sequence of transition blocks (v2.2 §12-5 nesting)."""
        parts = []

        # Build label -> transition map
        by_label = {}
        for t in transitions:
            lbl = getattr(t, 'label', '') or ''
            if lbl:
                by_label[lbl] = t

        # Collect all labels mentioned anywhere in the relation tree
        mentioned = set()

        def collect(r):
            for m in (getattr(r, 'members', None) or []):
                mentioned.add(m)
            for c in (getattr(r, 'children', None) or []):
                collect(c)

        for r in relations:
            collect(r)

        # Emit relations in order
        for r in relations:
            parts.append(self._emit_relation(r, by_label, indent_level=1))

        # Emit transitions not covered by any relation (backward compat)
        for t in transitions:
            lbl = getattr(t, 'label', '') or ''
            if lbl and lbl in mentioned:
                continue
            parts.append(self._build_transition_block(t, 0))

        return ''.join(parts)

    def _collect_child_labels(self, rel) -> set:
        """Recursively collect all labels mentioned in descendants of rel.

        [v2.2.1 fix]
          Used to avoid emitting the same transition twice when a parent
          and its child both declare the same members. The parent skips
          any label that any descendant declares.
        """
        labels = set()
        for child in (getattr(rel, 'children', None) or []):
            labels.update(getattr(child, 'members', None) or [])
            labels.update(self._collect_child_labels(child))
        return labels

    def _emit_relation(self, rel, by_label, indent_level=1) -> str:
        """Emit one relation (recursively for children).

        [v2.2.1 fix]
          If a child relation declares the same members as its parent,
          the child takes over and the parent does not emit them.
          This prevents duplicate transition blocks in the generated C.
        """
        parts = []
        pad = '    ' * indent_level

        shared_cond = (getattr(rel, 'shared_condition', '') or '').strip()
        has_cond = bool(shared_cond)

        if has_cond:
            parts.append(
                f'\n{pad}/* ===== Group (shared_condition) ===== */\n')
            parts.append(f'{pad}if ({shared_cond}) {{\n')
            inner_indent = indent_level + 1
        else:
            inner_indent = indent_level

        # v2.2.1: labels handled by descendant relations are skipped here
        child_labels = self._collect_child_labels(rel)

        # Members (skip those delegated to children)
        for label in (getattr(rel, 'members', None) or []):
            if label in child_labels:
                continue
            t = by_label.get(label)
            if t is None:
                continue
            block = self._build_transition_block(t, 0)
            extra = inner_indent - 1
            if extra > 0:
                block = self._indent_block(block, extra_indent=extra)
            parts.append(block)

        # Children (recursively)
        for child in (getattr(rel, 'children', None) or []):
            parts.append(self._emit_relation(child, by_label,
                                             indent_level=inner_indent))

        if has_cond:
            parts.append(f'{pad}}}\n')

        return ''.join(parts)

    def _indent_block(self, block: str, extra_indent: int = 1) -> str:
        """Indent an entire block by `extra_indent` levels."""
        pad = '    ' * extra_indent
        lines = block.split('\n')
        return '\n'.join(
            pad + line if line.strip() else line for line in lines
        )

    # ==================================================================
    # Cell function (with nesting)
    # ==================================================================
    def generate_transition_cell_functions(self, state_machine: StateMachine) -> str:
        """Generate transition functions for all cells (v2.2)."""
        self._current_state_machine = state_machine

        cell_blocks = []
        for state in state_machine.states.values():
            for event in state_machine.events.values():
                transitions = state_machine.get_transitions_for_cell(
                    state.name, event.name)
                if not transitions:
                    continue
                cell_blocks.append(
                    self._build_cell_function(state, event, transitions)
                )

        self._current_state_machine = None
        return '\n'.join(cell_blocks)

    def _build_cell_function(self, state, event, transitions) -> str:
        """Build one cell transition function (v2.2)."""
        T = self.CELL_TEMPLATES

        sm = self._current_state_machine
        cell_actions = sm.get_actions_for_cell(state.name, event.name) if sm else []
        cell_relations = sm.get_relations_for_cell(state.name, event.name) if sm else []

        needs_handled = any(
            getattr(t, 'early_return', False) for t in transitions
        )

        parts = []

        parts.append(T['header'].substitute(
            state_enum=self._state_enum(state.name),
            event_enum=self._event_enum(event.name),
            transition_count=len(transitions),
        ))

        parts.append(T['signature'].substitute(
            state_type=self._state_type(),
            func_name=self._cell_func_name(state.name, event.name),
            context_type=self._context_type(),
        ))

        if needs_handled:
            parts.append(T['body_open'].substitute(state_type=self._state_type()))
        else:
            parts.append(T['body_open_simple'].substitute(
                state_type=self._state_type()))

        # Cell actions (pre): before_transitions (+ legacy always)
        pre_actions_for_cell = [
            a for a in cell_actions
            if a.trigger in ("before_transitions", "always")
        ]
        if pre_actions_for_cell:
            parts.append(T['cell_actions_header'].substitute(
                trigger="before_transitions"))
            for a in pre_actions_for_cell:
                parts.append(T['cell_action_call'].substitute(
                    call=self._role_func_call(a.role_function)
                ))

        # Transitions (recursive)
        parts.append(self._build_transitions_block(
            state, transitions, cell_relations
        ))

        # Cell actions (post): after_transitions
        after_actions = [a for a in cell_actions
                         if a.trigger == "after_transitions"]
        if after_actions:
            parts.append(T['cell_actions_header'].substitute(
                trigger="after_transitions"))
            for a in after_actions:
                parts.append(T['cell_action_call'].substitute(
                    call=self._role_func_call(a.role_function)
                ))

        parts.append(T['body_close'])
        return ''.join(parts)

    # ==================================================================
    # Forward declarations
    # ==================================================================
    def generate_transition_cell_prototypes(self, state_machine: StateMachine) -> str:
        T = self.CELL_PROTO_TEMPLATES
        parts = [T['section_comment']]
        for state in state_machine.states.values():
            for event in state_machine.events.values():
                transitions = state_machine.get_transitions_for_cell(
                    state.name, event.name)
                if not transitions:
                    continue
                parts.append(T['prototype'].substitute(
                    state_type=self._state_type(),
                    func_name=self._cell_func_name(state.name, event.name),
                    context_type=self._context_type(),
                ))
        return ''.join(parts)

    # ==================================================================
    # Transition table (dispatch)
    # ==================================================================
    def generate_transition_table(self, state_machine: StateMachine,
                                  table_type: str = None) -> str:
        if table_type is None:
            table_type = self.DEFAULT_TABLE_TYPE
        generator = self.table_generators.get(table_type)
        if generator is None or table_type != 'array':
            generator = self.table_generators['array']
        return generator(state_machine)

    def _generate_table_array(self, state_machine: StateMachine) -> str:
        T = self.TABLE_TEMPLATES
        parts = []
        states = list(state_machine.states.values())
        events = list(state_machine.events.values())
        func_type = self._func_type()
        table_name = self._table_name()

        cell_values = []
        for state in states:
            row = []
            for event in events:
                transitions = state_machine.get_transitions_for_cell(
                    state.name, event.name)
                row.append(self._cell_func_name(state.name, event.name)
                           if transitions else "NULL")
            cell_values.append(row)

        state_col_width = max((len(s.name) for s in states), default=5)
        event_headers = []
        col_widths = []
        for event_idx, event in enumerate(events):
            event_disp = event.name if event.name else "NONE"
            event_headers.append(event_disp)
            w = max(len(event_disp), self.TABLE_MIN_COL_WIDTH)
            for state_idx in range(len(states)):
                w = max(w, len(cell_values[state_idx][event_idx]))
            col_widths.append(w)

        parts.append(T['func_ptr_comment'])
        parts.append(T['func_ptr_typedef'].substitute(
            state_type=self._state_type(),
            func_type=func_type,
            context_type=self._context_type(),
        ))
        parts.append(T['table_comment'].substitute(
            row_desc="state", col_desc="event"))
        parts.append(T['table_open'].substitute(
            func_type=func_type, table_name=table_name,
            state_max=self._state_max(), event_max=self._event_max(),
        ))

        header_state_pad = " " * (state_col_width + 2)
        header_cells = [event_headers[i].ljust(col_widths[i])
                        for i in range(len(events))]
        parts.append(
            "    /*" + " " + header_state_pad + " | " +
            " | ".join(header_cells) + " */\n"
        )
        sep = "    /* " + "-" * (state_col_width + 2) + "+"
        for w in col_widths:
            sep += "-" * w + "+"
        sep = sep[:-1] + "*/\n"
        parts.append(sep)

        for state_idx, state in enumerate(states):
            state_padded = state.name.ljust(state_col_width + 2)
            cells = [cell_values[state_idx][event_idx].ljust(col_widths[event_idx])
                     for event_idx in range(len(events))]
            row = f"    /* {state_padded}*/ {{ "
            row += ", ".join(cells)
            row += " },\n"
            parts.append(row)

        parts.append(T['table_close'])
        return ''.join(parts)

    def _generate_table_switch(self, sm): return self._generate_table_array(sm)
    def _generate_table_dictionary(self, sm): return self._generate_table_array(sm)

    # ==================================================================
    # Table header / dict / process / get_next
    # ==================================================================
    def generate_transition_table_header(self, state_machine: StateMachine) -> str:
        T = self.TABLE_HEADER_TEMPLATES
        parts = []
        parts.append(T['header_comment'].substitute(
            layer=self.layer_name or "system",
            row_desc="state", col_desc="event",
        ))
        parts.append(T['func_ptr_typedef'].substitute(
            state_type=self._state_type(),
            func_type=self._func_type(),
            context_type=self._context_type(),
        ))
        parts.append("")
        parts.append(T['extern_decl'].substitute(
            func_type=self._func_type(),
            table_name=self._table_name(),
            state_max=self._state_max(),
            event_max=self._event_max(),
        ))
        return ''.join(parts)

    def generate_function_dictionary(self, state_machine: StateMachine) -> str:
        T = self.DICT_TEMPLATES
        parts = []
        func_type = self._func_type()
        state_type = self._state_type()
        event_type = self._event_type()
        dict_type = f"TransitionDictEntry_{self.layer_name}_t" if self.layer_name else "TransitionDictEntry_t"
        dict_name = f"transition_dict_{self.layer_name}" if self.layer_name else "transition_dict"
        size_macro = f"TRANSITION_DICT_{self.layer_name.upper()}_SIZE" if self.layer_name else "TRANSITION_DICT_SIZE"

        parts.append(T['struct_comment'])
        parts.append(T['struct_open'])
        parts.append(T['struct_field_from'].substitute(state_type=state_type))
        parts.append(T['struct_field_event'].substitute(event_type=event_type))
        parts.append(T['struct_field_target'].substitute(state_type=state_type))
        parts.append(T['struct_field_condition'])
        parts.append(T['struct_field_func'].substitute(func_type=func_type))
        parts.append(T['struct_close'].substitute(dict_type=dict_type))

        parts.append(T['dict_comment'])
        parts.append(T['dict_open'].substitute(
            dict_type=dict_type, dict_name=dict_name))

        for state in state_machine.states.values():
            for event in state_machine.events.values():
                transitions = state_machine.get_transitions_for_cell(
                    state.name, event.name)
                if not transitions:
                    continue
                for idx, trans in enumerate(transitions):
                    base_name = (
                        f"{self.layer_name}_{state.name}_{event.name or 'NONE'}"
                        if self.layer_name
                        else f"{state.name}_{event.name or 'NONE'}"
                    )
                    trans_name = (f"{base_name}_{idx}"
                                  if len(transitions) > 1 else base_name)
                    target = trans.target or state.name
                    condition = trans.condition.replace('"', '\\"') if trans.condition else ""
                    parts.append(T['dict_entry'].substitute(
                        trans_name=trans_name,
                        state_enum=self._state_enum(state.name),
                        event_enum=self._event_enum(event.name),
                        target_enum=self._state_enum(target),
                        condition=condition,
                        func_name=self._cell_func_name(state.name, event.name),
                    ))
        parts.append(T['dict_close'])
        parts.append(T['dict_size'].substitute(
            size_macro=size_macro, dict_name=dict_name))
        return ''.join(parts)

    def generate_process_function(self, state_machine: StateMachine,
                                  generation_style: str = None) -> str:
        if generation_style is None:
            generation_style = self.DEFAULT_GENERATION_STYLE
        generator = self.process_generators.get(generation_style)
        if generator is None or generation_style != 'table_driven':
            generator = self.process_generators['table_driven']
        return generator(state_machine)

    def _generate_process_table_driven(self, state_machine: StateMachine) -> str:
        T = self.PROCESS_TEMPLATES
        func_name = (f"StateMachine_Process_{self.layer_name}"
                     if self.layer_name else "StateMachine_Process")
        parts = []
        parts.append(T['comment'].substitute(layer=self.layer_name or "system"))
        parts.append(T['signature'].substitute(
            state_type=self._state_type(),
            func_name=func_name,
            event_type=self._event_type(),
        ))
        parts.append(T['body'].substitute(
            context_type=self._context_type(),
            func_type=self._func_type(),
            table_name=self._table_name(),
        ))
        return ''.join(parts)

    def _generate_process_switch_case(self, sm):
        return self._generate_process_table_driven(sm)

    def generate_get_next_event_function(self, state_machine: StateMachine) -> str:
        T = self.GET_NEXT_TEMPLATES
        func_name = (f"StateMachine_GetNextEvent_{self.layer_name}"
                     if self.layer_name else "StateMachine_GetNextEvent")
        event_none = self._event_enum("")
        parts = []
        parts.append(T['comment'].substitute(
            layer=self.layer_name or "system",
            event_none=event_none))
        parts.append(T['signature'].substitute(
            event_type=self._event_type(),
            func_name=func_name))
        parts.append(T['body'].substitute(
            event_type=self._event_type(),
            event_none=event_none))
        return ''.join(parts)

    # ==================================================================
    # Batch generation
    # ==================================================================
    def generate_all(self, state_machine: StateMachine) -> Dict[str, str]:
        return {
            'cell_prototypes': self.generate_transition_cell_prototypes(state_machine),
            'cell_functions': self.generate_transition_cell_functions(state_machine),
            'transition_table': self.generate_transition_table(state_machine),
            'transition_table_header': self.generate_transition_table_header(state_machine),
            'function_dict': self.generate_function_dictionary(state_machine),
            'process_func': self.generate_process_function(state_machine),
            'get_next_event': self.generate_get_next_event_function(state_machine),
        }

    def generate_all_transitions(self, state_machine, table_type='array',
                                 process_type='table_driven'):
        result = self.generate_all(state_machine)
        return '\n'.join([
            result['cell_prototypes'],
            result['transition_table'],
            result['cell_functions'],
            result['process_func'],
        ])