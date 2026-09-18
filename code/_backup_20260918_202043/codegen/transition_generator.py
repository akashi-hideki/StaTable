# codegen/transition_generator.py
"""
State transition function generation module (multi-layer state machine support)

Generated artifacts:
  1. Per-cell transition functions (static, short name t_<State>_<Event>)
     - Forward declarations (prototypes)
     - Implementation bodies
  2. Transition table (global const, with extern declaration)
  3. Function dictionary (for debugging / reflection)
  4. StateMachine_Process_<Layer>() function
  5. StateMachine_GetNextEvent_<Layer>() function

Design policy:
  - Transition table is externally accessible (global)
  - Cell functions are static (internal implementation detail)
  - Cell functions are forward-declared, then table and implementations
    are emitted (order independent)
  - Table layout: rows=states, columns=events (specification format)

[v2.0 fix]
  - `_role_func_call`: correctly convert `namespace.name` form (e.g. "App.Init")
    to `RoleFunc_<Namespace>_<Name>(transition, ctx)`
    Old: RoleFunc_App.Init(...)  <- C compile error
    New: RoleFunc_App_Init(...)  <- correct
"""

import sys
import os
import logging
from string import Template
from typing import Dict, List

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
    """State transition function generator (multi-layer support)"""

    # Whether to use short cell function names (recommended True for static)
    SHORT_CELL_NAMES = True

    # Minimum column width for the transition table
    TABLE_MIN_COL_WIDTH = 14

    # Default settings
    DEFAULT_TABLE_TYPE = 'array'
    DEFAULT_GENERATION_STYLE = 'table_driven'

    # ==================================================================
    # Templates
    # ==================================================================
    CELL_TEMPLATES = {
        # --- Header comment ---
        'header': Template(
            '/**\n'
            ' * @brief  Cell transition: $state_enum -[$event_enum]-> $target\n'
            ' */\n'
        ),

        # --- Function signature ---
        'signature': Template(
            'static $state_type $func_name(\n'
            '    const $context_type *transition,\n'
            '    SystemContext_t *ctx\n'
            ')\n'
            '{\n'
        ),

        # --- State variable initialization ---
        'body_open': Template(
            '    $state_type next_state = transition->from_state;\n'
        ),

        # --- Conditional transition block ---
        'cond_block': Template(
            '\n'
            '    /* Transition[$idx] */\n'
            '    if ($condition) {\n'
            '$pre_actions'
            '        next_state = $target_enum;\n'
            '        return next_state;\n'
            '    }\n'
        ),

        # --- Unconditional transition block ---
        'cond_block_empty': Template(
            '\n'
            '    /* Transition[$idx] (unconditional) */\n'
            '    if (1) {\n'
            '$pre_actions'
            '        next_state = $target_enum;\n'
            '        return next_state;\n'
            '    }\n'
        ),

        # --- pre_action call line ---
        'pre_action_line': Template(
            '        $call;\n'
        ),

        # --- else clause header ---
        'else_header': (
            '\n'
            '    /* ==== else clause ==== */\n'
        ),

        # --- else_action call line ---
        'else_action_line': Template(
            '    $call;\n'
        ),

        # --- else target ---
        'else_target': Template(
            '    next_state = $target_enum;\n'
        ),

        # --- else target not set ---
        'else_target_unset': (
            '    /* else target not set */\n'
        ),

        # --- Function body close ---
        'body_close': (
            '\n'
            '    return next_state;\n'
            '}\n'
        ),
    }

    # ==================================================================
    # [Table 1b] Forward declarations of cell functions
    # ==================================================================
    CELL_PROTO_TEMPLATES = {
        # --- Section comment ---
        'section_comment': '/* ===== Cell transition function forward declarations ===== */\n',

        # --- Prototype body ---
        'prototype': Template(
            'static $state_type $func_name(\n'
            '    const $context_type *transition,\n'
            '    SystemContext_t *ctx);\n'
        ),
    }

    # ==================================================================
    # [Table 2] Transition table (global + horizontal layout)
    # ==================================================================
    TABLE_TEMPLATES = {
        # --- Function pointer type ---
        'func_ptr_comment': '/* Transition function pointer type */\n',
        'func_ptr_typedef': Template(
            'typedef $state_type (*$func_type)(\n'
            '    const $context_type *, SystemContext_t *);\n'
        ),

        # --- Table description comment ---
        'table_comment': Template(
            '\n'
            '/* ============================================================== */\n'
            '/*  State transition table: rows=$row_desc, cols=$col_desc      */\n'
            '/*  Global variable (externally accessible)                     */\n'
            '/* ============================================================== */\n'
        ),

        # --- Table body (no static = global) ---
        'table_open': Template(
            'const $func_type $table_name\n'
            '    [$state_max][$event_max] = {\n'
        ),

        # --- Table close ---
        'table_close': '};\n',
    }

    # ==================================================================
    # [Table 3] extern declaration for header
    # ==================================================================
    TABLE_HEADER_TEMPLATES = {
        # --- Header comment ---
        'header_comment': Template(
            '/**\n'
            ' * @brief  Transition table ($layer layer)\n'
            ' * @note   rows=$row_desc, cols=$col_desc\n'
            ' */\n'
        ),

        # --- Function pointer type ---
        'func_ptr_typedef': Template(
            'typedef $state_type (*$func_type)(\n'
            '    const $context_type *, SystemContext_t *);\n'
        ),

        # --- extern declaration ---
        'extern_decl': Template(
            'extern const $func_type $table_name\n'
            '    [$state_max][$event_max];\n'
        ),
    }

    # ==================================================================
    # [Table 4] Function dictionary
    # ==================================================================
    DICT_TEMPLATES = {
        # --- Entry struct comment ---
        'struct_comment': (
            '/* Transition function dictionary entry */\n'
            '/* Used for debugging, logging, and dynamic dispatch */\n'
        ),

        # --- Entry struct open ---
        'struct_open': (
            'typedef struct {\n'
            '    const char *name;                    /* Transition name */\n'
        ),

        # --- Member: source state ---
        'struct_field_from': Template(
            '    $state_type from_state;              /* Source state */\n'
        ),

        # --- Member: event ---
        'struct_field_event': Template(
            '    $event_type event;                   /* Event */\n'
        ),

        # --- Member: default target ---
        'struct_field_target': Template(
            '    $state_type default_target;          /* Default target */\n'
        ),

        # --- Member: condition ---
        'struct_field_condition': (
            '    const char *condition;               /* Condition (string) */\n'
        ),

        # --- Member: function pointer ---
        'struct_field_func': Template(
            '    $func_type func;                     /* Transition function pointer */\n'
        ),

        # --- Entry struct close ---
        'struct_close': Template('}} $dict_type;\n'),

        # --- Dictionary comment ---
        'dict_comment': '\n/* Transition function dictionary */\n',

        # --- Dictionary open ---
        'dict_open': Template(
            'static const $dict_type $dict_name[] = {\n'
        ),

        # --- Dictionary entry ---
        'dict_entry': Template(
            '    { "$trans_name",\n'
            '      $state_enum, $event_enum, $target_enum,\n'
            '      "$condition", $func_name },\n'
        ),

        # --- Dictionary close ---
        'dict_close': '};\n',

        # --- Size macro ---
        'dict_size': Template(
            '\n'
            '#define $size_macro \\\n'
            '    (sizeof($dict_name) / sizeof($dict_name[0]))\n'
        ),
    }

    # ==================================================================
    # [Table 5] StateMachine_Process_<Layer>
    # ==================================================================
    PROCESS_TEMPLATES = {
        # --- Comment ---
        'comment': Template(
            '/**\n'
            ' * @brief  $layer layer state transition processing\n'
            ' * @param  current_state  Current state\n'
            ' * @param  event          Event that occurred\n'
            ' * @param  ctx            System context pointer\n'
            ' * @return State after transition\n'
            ' */\n'
        ),

        # --- Signature ---
        'signature': Template(
            '$state_type $func_name(\n'
            '    $state_type current_state,\n'
            '    $event_type event,\n'
            '    SystemContext_t *ctx\n'
            ')\n'
        ),

        # --- Body ---
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
    # [Table 6] StateMachine_GetNextEvent_<Layer>
    # ==================================================================
    GET_NEXT_TEMPLATES = {
        # --- Comment ---
        'comment': Template(
            '/**\n'
            ' * @brief  Get next event for $layer layer\n'
            ' * @param  ctx  System context pointer\n'
            ' * @return Next event ($event_none if no pending event)\n'
            ' */\n'
        ),

        # --- Signature ---
        'signature': Template(
            '$event_type $func_name(SystemContext_t *ctx)\n'
        ),

        # --- Body ---
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

        # Dispatch table (table_type)
        self.table_generators: Dict[str, callable] = {
            'array':      self._generate_table_array,
            'switch':     self._generate_table_switch,
            'dictionary': self._generate_table_dictionary,
        }

        # Dispatch table (generation_style)
        self.process_generators: Dict[str, callable] = {
            'table_driven': self._generate_process_table_driven,
            'switch_case':  self._generate_process_switch_case,
        }

    def set_layer(self, layer_name: str):
        """Set layer name (e.g. 'Driver', 'Middleware', 'Application')"""
        self.layer_name = layer_name

    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)

    # ==================================================================
    # Name generation
    # ==================================================================
    def _state_enum(self, state_name: str) -> str:
        """STATE_<Layer>_<Name>"""
        s = self.naming.to_pascal_case(state_name) if state_name else "Unknown"
        return f"STATE_{self.layer_name}_{s}" if self.layer_name else f"STATE_{s}"

    def _event_enum(self, event_name: str) -> str:
        """EVENT_<Layer>_<Name> (EVENT_<Layer>_NONE if empty)"""
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
        """transition_<Layer>_<State>_<Event>"""
        s = self.naming.to_pascal_case(state_name) if state_name else "Unknown"
        e = self.naming.to_upper_snake(event_name) if event_name else "NONE"
        if self.SHORT_CELL_NAMES:
            return f"t_{s}_{e}"
        return f"transition_{self.layer_name}_{s}_{e}" if self.layer_name \
            else f"transition_{s}_{e}"

    def _role_func_call(self, func_name: str) -> str:
        """
        Generate a role function call statement.

        [v2.0 fix]
          Correctly convert `namespace.name` form (e.g. "App.Init")
          to `RoleFunc_<Namespace>_<Name>(transition, ctx)`.

          Consistent with `_normalize_func_ref` in role_function_generator.py:
            - role_function_generator side: "App.Init" -> "RoleFunc_App_Init"
            - transition_generator side (this method): same conversion applied

          Old bug:
            func_name = "App.Init"
            -> to_pascal_case("App.Init") does not handle "." so remains "App.Init"
            -> RoleFunc_App.Init(...)  <- C compile error

          Fixed:
            func_name = "App.Init"
            -> split(".", 1) into ns="App", name="Init"
            -> RoleFunc_App_Init(...)  <- correct
        """
        if not func_name:
            return "/* empty role function reference */"

        # Already has RoleFunc_ prefix
        if func_name.startswith("RoleFunc_"):
            return f"{func_name}(transition, ctx)"

        # Handle namespace.name form
        if "." in func_name:
            ns, name = func_name.split(".", 1)
            # PascalCase both namespace and name
            ns_pascal = self.naming.to_pascal_case(ns)
            name_pascal = self.naming.to_pascal_case(name)
            return f"RoleFunc_{ns_pascal}_{name_pascal}(transition, ctx)"

        # No namespace
        pascal = self.naming.to_pascal_case(func_name)
        if self.layer_name:
            full = f"RoleFunc_{self.layer_name}_{pascal}"
        else:
            full = f"RoleFunc_{pascal}"
        return f"{full}(transition, ctx)"

    # ==================================================================
    # Per-cell transition functions
    # ==================================================================
    def generate_transition_cell_functions(self, state_machine: StateMachine) -> str:
        """Generate transition functions for all cells"""
        cell_blocks = []

        for state in state_machine.states.values():
            for event in state_machine.events.values():
                transitions = state_machine.get_transitions_for_cell(state.name, event.name)
                if not transitions:
                    continue
                cell_blocks.append(self._build_cell_function(state, event, transitions))
        return '\n'.join(cell_blocks)

    # ==================================================================
    # 1b. Per-cell transition functions (forward declarations)
    # ==================================================================
    def generate_transition_cell_prototypes(self, state_machine: StateMachine) -> str:
        """
        Generate forward declarations (prototypes) for per-cell transition functions.

        Example output:
            /* ===== Cell transition function forward declarations ===== */
            static STATE_Driver_t t_Idle_START(
                const TransitionContext_Driver_t *transition,
                SystemContext_t *ctx);
            static STATE_Driver_t t_Active_ERROR(
                const TransitionContext_Driver_t *transition,
                SystemContext_t *ctx);
        """
        T = self.CELL_PROTO_TEMPLATES
        parts = [T['section_comment']]
        for state in state_machine.states.values():
            for event in state_machine.events.values():
                transitions = state_machine.get_transitions_for_cell(state.name, event.name)
                if not transitions:
                    continue

                parts.append(T['prototype'].substitute(
                    state_type=self._state_type(),
                    func_name=self._cell_func_name(state.name, event.name),
                    context_type=self._context_type(),
                ))
        return ''.join(parts)

    def _build_cell_function(self, state, event, transitions) -> str:
        """Build one cell transition function as a string"""
        parts = []
        T = self.CELL_TEMPLATES

        # --- Header comment ---
        parts.append(T['header'].substitute(
            state_enum=self._state_enum(state.name),
            event_enum=self._event_enum(event.name),
            target=transitions[0].target if transitions[0].target else "?",
        ))

        # --- Function signature + body open ---
        parts.append(T['signature'].substitute(
            state_type=self._state_type(),
            func_name=self._cell_func_name(state.name, event.name),
            context_type=self._context_type(),
        ))
        parts.append(T['body_open'].substitute(state_type=self._state_type()))

        # --- Each transition block ---
        for idx, trans in enumerate(transitions):
            parts.append(self._build_transition_block(trans, idx))

        # --- else clause (only for the last transition) ---
        last_trans = transitions[-1]
        if getattr(last_trans, 'has_else', True):
            parts.append(self._build_else_block(last_trans))

        # --- Function body close ---
        parts.append(T['body_close'])

        return ''.join(parts)

    def _build_transition_block(self, trans, idx) -> str:
        """Build one transition block as a string"""
        T = self.CELL_TEMPLATES
        condition = getattr(trans, 'condition', '')
        pre_actions = ensure_list(getattr(trans, 'pre_actions', []))
        target = getattr(trans, 'target', '')

        # Combine pre_actions into one string
        pre_actions_code = ''.join(
            T['pre_action_line'].substitute(call=self._role_func_call(a))
            for a in pre_actions
        )

        # Switch template based on condition presence
        if condition:
            return T['cond_block'].substitute(
                idx=idx, condition=condition,
                pre_actions=pre_actions_code,
                target_enum=self._state_enum(target) if target else "next_state",
            )
        return T['cond_block_empty'].substitute(
            idx=idx, pre_actions=pre_actions_code,
            target_enum=self._state_enum(target) if target else "next_state",
        )

    def _build_else_block(self, trans) -> str:
        """Build the else clause as a string"""
        T = self.CELL_TEMPLATES
        else_actions = ensure_list(getattr(trans, 'else_actions', []))
        else_target = getattr(trans, 'else_target', '')

        # Skip output if neither else_actions nor else_target is set
        if not else_actions and not else_target:
            return ''
        parts = [T['else_header']]
        for ea in else_actions:
            parts.append(T['else_action_line'].substitute(
                call=self._role_func_call(ea)
            ))
        if else_target:
            parts.append(T['else_target'].substitute(
                target_enum=self._state_enum(else_target)
            ))
        else:
            parts.append(T['else_target_unset'])
        return ''.join(parts)

    # ==================================================================
    # Transition table (dispatch version)
    # ==================================================================
    def generate_transition_table(self, state_machine: StateMachine,
                                  table_type: str = None) -> str:
        """Generate the transition table.

        Args:
            state_machine: StateMachine
            table_type: 'array' / 'switch' / 'dictionary'
                        (defaults to 'array' if None)
        """
        if table_type is None:
            table_type = self.DEFAULT_TABLE_TYPE

        generator = self.table_generators.get(table_type)

        if generator is None:
            self._log_debug(
                f"Unknown table_type '{table_type}', "
                f"falling back to '{self.DEFAULT_TABLE_TYPE}'",
                'warning'
            )
            generator = self.table_generators[self.DEFAULT_TABLE_TYPE]
        elif table_type != 'array':
            # switch / dictionary not implemented -> fall back to array
            self._log_debug(
                f"table_type '{table_type}' is not implemented yet, "
                f"falling back to 'array'",
                'warning'
            )
            generator = self.table_generators['array']

        return generator(state_machine)

    def _generate_table_array(self, state_machine: StateMachine) -> str:
        """Array form (current implementation)"""
        self._log_debug("=== _generate_table_array START ===")
        T = self.TABLE_TEMPLATES
        parts = []

        # Prepare names
        states = list(state_machine.states.values())
        events = list(state_machine.events.values())

        func_type = self._func_type()
        table_name = self._table_name()

        # --- Precompute cell values ---
        cell_values = []
        for state in states:
            row = []
            for event in events:
                transitions = state_machine.get_transitions_for_cell(state.name, event.name)
                row.append(self._cell_func_name(state.name, event.name)
                           if transitions else "NULL")
            cell_values.append(row)

        # --- Compute column widths ---
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

        # --- Function pointer type ---
        parts.append(T['func_ptr_comment'])
        parts.append(T['func_ptr_typedef'].substitute(
            state_type=self._state_type(),
            func_type=func_type,
            context_type=self._context_type(),
        ))

        # --- Table description ---
        parts.append(T['table_comment'].substitute(
            row_desc="state", col_desc="event",
        ))

        # --- Table open ---
        parts.append(T['table_open'].substitute(
            func_type=func_type,
            table_name=table_name,
            state_max=self._state_max(),
            event_max=self._event_max(),
        ))

        # --- Header row ---
        header_state_pad = " " * (state_col_width + 2)
        header_cells = [event_headers[i].ljust(col_widths[i])
                        for i in range(len(events))]
        header_line = "    /*" + " " + header_state_pad + " | " \
                      + " | ".join(header_cells) + " */"
        parts.append(header_line + "\n")

        # --- Separator ---
        sep = "    /* " + "-" * (state_col_width + 2) + "+"
        for w in col_widths:
            sep += "-" * w + "+"
        sep = sep[:-1] + "*/"
        parts.append(sep + "\n")

        # --- Data rows ---
        for state_idx, state in enumerate(states):
            state_padded = state.name.ljust(state_col_width + 2)
            cells = []
            for event_idx in range(len(events)):
                cell_content = cell_values[state_idx][event_idx].ljust(col_widths[event_idx])
                cells.append(cell_content)

            row = f"    /* {state_padded}*/ {{ "
            row += ", ".join(cells)
            row += " },"
            parts.append(row + "\n")

        # --- Table close ---
        parts.append(T['table_close'])
        self._log_debug("=== _generate_table_array END ===")
        return ''.join(parts)

    def _generate_table_switch(self, state_machine: StateMachine) -> str:
        """switch form (not implemented -> array fallback)"""
        self._log_debug(
            "_generate_table_switch: not implemented, "
            "falling back to array",
            'warning'
        )
        return self._generate_table_array(state_machine)

    def _generate_table_dictionary(self, state_machine: StateMachine) -> str:
        """dictionary form (not implemented -> array fallback)"""
        self._log_debug(
            "_generate_table_dictionary: not implemented, "
            "falling back to array",
            'warning'
        )
        return self._generate_table_array(state_machine)

    # ==================================================================
    # extern declaration for header
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

    # ==================================================================
    # Function dictionary
    # ==================================================================
    def generate_function_dictionary(self, state_machine: StateMachine) -> str:
        """Generate a name-based function dictionary"""
        T = self.DICT_TEMPLATES
        parts = []

        # Prepare names
        func_type = self._func_type()
        state_type = self._state_type()
        event_type = self._event_type()
        dict_type = f"TransitionDictEntry_{self.layer_name}_t" if self.layer_name else "TransitionDictEntry_t"
        dict_name = f"transition_dict_{self.layer_name}" if self.layer_name else "transition_dict"
        size_macro = f"TRANSITION_DICT_{self.layer_name.upper()}_SIZE" if self.layer_name else "TRANSITION_DICT_SIZE"

        # --- Entry struct ---
        parts.append(T['struct_comment'])
        parts.append(T['struct_open'])
        parts.append(T['struct_field_from'].substitute(state_type=state_type))
        parts.append(T['struct_field_event'].substitute(event_type=event_type))
        parts.append(T['struct_field_target'].substitute(state_type=state_type))
        parts.append(T['struct_field_condition'])
        parts.append(T['struct_field_func'].substitute(func_type=func_type))
        parts.append(T['struct_close'].substitute(dict_type=dict_type))

        # --- Dictionary body ---
        parts.append(T['dict_comment'])
        parts.append(T['dict_open'].substitute(
            dict_type=dict_type, dict_name=dict_name,
        ))

        for state in state_machine.states.values():
            for event in state_machine.events.values():
                transitions = state_machine.get_transitions_for_cell(state.name, event.name)
                if not transitions:
                    continue
                for idx, trans in enumerate(transitions):
                    # Transition name
                    base_name = f"{self.layer_name}_{state.name}_{event.name or 'NONE'}" \
                        if self.layer_name else f"{state.name}_{event.name or 'NONE'}"
                    trans_name = f"{base_name}_{idx}" if len(transitions) > 1 else base_name

                    # Default target
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
            size_macro=size_macro, dict_name=dict_name,
        ))
        return ''.join(parts)

    # ==================================================================
    # StateMachine_Process (dispatch version)
    # ==================================================================
    def generate_process_function(self, state_machine: StateMachine,
                                  generation_style: str = None) -> str:
        """Generate the state transition processing function.

        Args:
            state_machine: StateMachine
            generation_style: 'table_driven' / 'switch_case'
                              (defaults to 'table_driven' if None)
        """
        if generation_style is None:
            generation_style = self.DEFAULT_GENERATION_STYLE

        generator = self.process_generators.get(generation_style)

        if generator is None:
            self._log_debug(
                f"Unknown generation_style '{generation_style}', "
                f"falling back to '{self.DEFAULT_GENERATION_STYLE}'",
                'warning'
            )
            generator = self.process_generators[self.DEFAULT_GENERATION_STYLE]
        elif generation_style != 'table_driven':
            self._log_debug(
                f"generation_style '{generation_style}' is not implemented yet, "
                f"falling back to 'table_driven'",
                'warning'
            )
            generator = self.process_generators['table_driven']

        return generator(state_machine)

    def _generate_process_table_driven(self, state_machine: StateMachine) -> str:
        """Table-driven form (current implementation)"""
        T = self.PROCESS_TEMPLATES
        func_name = f"StateMachine_Process_{self.layer_name}" if self.layer_name \
            else "StateMachine_Process"
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

    def _generate_process_switch_case(self, state_machine: StateMachine) -> str:
        """switch form (not implemented -> table_driven fallback)"""
        self._log_debug(
            "_generate_process_switch_case: not implemented, "
            "falling back to table_driven",
            'warning'
        )
        return self._generate_process_table_driven(state_machine)

    # ==================================================================
    # GetNextEvent
    # ==================================================================
    def generate_get_next_event_function(self, state_machine: StateMachine) -> str:
        """Generate the function that retrieves pending events"""
        T = self.GET_NEXT_TEMPLATES

        func_name = f"StateMachine_GetNextEvent_{self.layer_name}" if self.layer_name \
            else "StateMachine_GetNextEvent"
        event_none = self._event_enum("")

        parts = []
        parts.append(T['comment'].substitute(
            layer=self.layer_name or "system",
            event_none=event_none,
        ))
        parts.append(T['signature'].substitute(
            event_type=self._event_type(),
            func_name=func_name,
        ))
        parts.append(T['body'].substitute(
            event_type=self._event_type(),
            event_none=event_none,
        ))
        return ''.join(parts)

    # ==================================================================
    # Batch generation
    # ==================================================================
    def generate_all(self, state_machine: StateMachine) -> Dict[str, str]:
        """
        Return all generated artifacts as a dictionary.

        Returns:
            {
                'cell_prototypes': str,        # Forward declarations of cell functions
                'cell_functions': str,         # Cell function implementations
                'transition_table': str,       # 2D array table (global)
                'transition_table_header': str,# extern declaration of the table
                'function_dict': str,          # Function dictionary
                'process_func': str,           # StateMachine_Process_<Layer>
                'get_next_event': str,         # StateMachine_GetNextEvent_<Layer>
            }
        """
        return {
            'cell_prototypes': self.generate_transition_cell_prototypes(state_machine),
            'cell_functions': self.generate_transition_cell_functions(state_machine),
            'transition_table': self.generate_transition_table(state_machine),
            'transition_table_header': self.generate_transition_table_header(state_machine),
            'function_dict': self.generate_function_dictionary(state_machine),
            'process_func': self.generate_process_function(state_machine),
            'get_next_event': self.generate_get_next_event_function(state_machine),
        }

    # ==================================================================
    # Backward-compatible API
    # ==================================================================
    def generate_all_transitions(self, state_machine, table_type='array',
                                 process_type='table_driven'):
        """Backward compat: return as a single string
           (forward declarations + implementations + table + Process)"""
        result = self.generate_all(state_machine)
        return '\n'.join([
            result['cell_prototypes'],
            result['transition_table'],
            result['cell_functions'],
            result['process_func'],
        ])