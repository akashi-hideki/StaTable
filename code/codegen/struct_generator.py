# codegen/struct_generator.py
"""
C struct code generation module (multi-layer state machine support)

Generated structs:
  1. custom_type              : user-defined types (unchanged)
  2. system_data              : global variables (unchanged)
  3. event_flags              : event flags (unchanged)
  4. system_context           : SystemContext_t (pending_event added)
  5. transition_context       : common TransitionContext_t (new base type)
  6. layer_transition_context : TransitionContext_<Layer>_t (new, per-layer)
  7. pending_event_macros     : FIRE_EVENT / MAX_CONSECUTIVE_PENDING_EVENTS macros (new)

Design policy:
  - Templates are data-tabled using string.Template
  - pending_event is uint16_t (holds each layer's enum value generically)
  - Provides both per-layer TransitionContext_<Layer>_t and
    the common base type TransitionContext_t
"""

import sys
import os
import logging
from string import Template
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
    """C struct code generation class (multi-layer state machine support)"""

    # ==================================================================
    # [Data Table 1] Common struct templates (SystemContext_t etc.)
    # ==================================================================
    CONTEXT_TEMPLATES = {
        # --- Section comment ---
        'section_comment': Template(
            '/* $title */\n'
            '/* $description */\n'
        ),

        # --- struct start ---
        'struct_start': (
            'typedef struct {\n'
        ),

        # --- data / flags members ---
        'member_data': Template(
            '    $system_data_type data;     /* global variables */\n'
        ),
        'member_flags': Template(
            '    $event_flags_type flags;    /* event flags */\n'
        ),

        # --- pending_event members ---
        'member_pending_event': Template(
            '    uint16_t pending_event_$layer;      /* [F-3 S2] pending event */\n'
        ),
        'member_pending_event_valid': Template(
            '    bool pending_event_valid_$layer;    /* [F-3 S2] pending valid flag */\n'
        ),
        # [C-52] one queue per layer
        'member_queue': Template(
            '    EventQueueState_t queue_$layer;  /* [C-52] per-layer queue */\n'
        ),

        # --- struct end ---
        'struct_end': Template(
            '} $type_name;\n'
        ),
    }

    # ==================================================================
    # [Data Table 2] Common macro templates
    # ==================================================================
    MACRO_TEMPLATES = {
        # --- Section comment ---
        'section_comment': (
            '\n'
            '/* ============================================================== */\n'
            '/*  Pending event control                                         */\n'
            '/* ============================================================== */\n'
        ),

        # --- FIRE_EVENT macro ---
        'fire_event_macro': (
            '\n'
            '/* Event fire macro */\n'
            '/* Used within role functions: FIRE_EVENT(ctx, EVENT_XXX_YYY); */\n'
            '#define FIRE_EVENT(ctx, evt)  do { \\\n'
            '    (ctx)->pending_event = (uint16_t)(evt); \\\n'
            '    (ctx)->pending_event_valid = true; \\\n'
            '} while(0)\n'
        ),

        # --- MAX_CONSECUTIVE_PENDING_EVENTS macro ---
        'max_consecutive_macro': (
            '\n'
            '/* Upper limit for consecutive pending event processing */\n'
            '/* Infinite loop prevention. Can be overridden at build time via -D */\n'
            '#ifndef MAX_CONSECUTIVE_PENDING_EVENTS\n'
            '#define MAX_CONSECUTIVE_PENDING_EVENTS 16\n'
            '#endif\n'
        ),
        # [C-52] per-layer queue size + init macro
        'queue_section_comment': (
            '\n'
            '/* ============================================================== */\n'
            '/*  Layer event queue (C-52)                                      */\n'
            '/* ============================================================== */\n'
        ),
        'queue_size_macro': (
            '\n'
            '/* Per-layer queue capacity. Override via -D at build time. */\n'
            '#ifndef STATABLE_LAYER_QUEUE_SIZE\n'
            '#define STATABLE_LAYER_QUEUE_SIZE 16\n'
            '#endif\n'
        ),
        'queue_state_type': (
            '\n'
            '/* Ring buffer state (one instance per layer, embedded in */\n'
            '/* SystemContext_t).  Protected by STATABLE_ENTER/EXIT_  */\n'
            '/* CRITICAL hooks (see below).                            */\n'
            'typedef struct {\n'
            '    uint16_t buffer[STATABLE_LAYER_QUEUE_SIZE];\n'
            '    volatile uint16_t head;\n'
            '    volatile uint16_t tail;\n'
            '    volatile uint16_t count;\n'
            '    volatile uint32_t dropped;  /* [C-54] full-drop count */\n'
            '} EventQueueState_t;\n'
        ),
        # [C-54] Critical section hooks (default no-op)
        'critical_hooks': (
            '\n'
            '/* ============================================================== */\n'
            '/*  Critical section hooks (C-54)                                 */\n'
            '/* ============================================================== */\n'
            '/* Called around per-layer queue operations to make them safe    */\n'
            '/* against ISR preemption.  Default: no-op (single-context).     */\n'
            '/* Override at build time via -D (see OSAL porting guide).       */\n'
            '#ifndef STATABLE_ENTER_CRITICAL\n'
            '#define STATABLE_ENTER_CRITICAL()  do { } while (0)\n'
            '#endif\n'
            '#ifndef STATABLE_EXIT_CRITICAL\n'
            '#define STATABLE_EXIT_CRITICAL()   do { } while (0)\n'
            '#endif\n'
        ),
    }

    # ==================================================================
    # [Data Table 3] Common TransitionContext_t template
    # ==================================================================
    COMMON_TRANSITION_CONTEXT_TEMPLATES = {
        'comment': (
            '/* Generic transition context (for common role functions across layers) */\n'
            '/* Same layout as each layer\'s TransitionContext_<Layer>_t */\n'
        ),
        'struct_start': (
            'typedef struct {\n'
        ),
        'member_from_state': (
            '    uint16_t from_state;   /* source state (cast from layer enum) */\n'
        ),
        'member_event': (
            '    uint16_t event;        /* event (cast from layer enum) */\n'
        ),
        'struct_end': (
            '} TransitionContext_t;\n'
        ),
    }

    # ==================================================================
    # [Data Table 4] Per-layer TransitionContext_<Layer>_t
    # ==================================================================
    LAYER_TRANSITION_CONTEXT_TEMPLATES = {
        'comment': Template(
            '/* Transition context for $layer layer */\n'
        ),
        'struct_start': (
            'typedef struct {\n'
        ),
        'member_from_state': Template(
            '    $state_type from_state;   /* source state */\n'
        ),
        'member_event': Template(
            '    $event_type event;        /* event */\n'
        ),
        'struct_end': Template(
            '} $type_name;\n'
        ),
    }

    # ==================================================================
    # [Data Table 5] Member type detection
    # ==================================================================
    MEMBER_TYPE_DETECTORS = {
        'bit_field': lambda m: getattr(m, 'bit_width', 0) > 0,
        'array': lambda m: getattr(m, 'array_size', 0) > 0,
        'normal': lambda m: True,
    }

    # ==================================================================
    # [Data Table 6] Member generation templates
    # ==================================================================
    MEMBER_TEMPLATES = {
        'bit_field': Template(
            '$indent$c_type $name : $width;\n'
        ),
        'array': Template(
            '$indent$c_type $name[$size];\n'
        ),
        'normal': Template(
            '$indent$c_type $name;\n'
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
        # [C-52] all layers of the current project
        self._all_layers: list = []

    def set_layer(self, layer_name: str):
        """Set layer name (for per-layer TransitionContext generation)"""
        self.layer_name = layer_name
        logger.debug(f"CStructGenerator.set_layer: layer_name='{layer_name}'")

    def set_layers(self, layers):
        """[C-52] Record all (name, sm) pairs for queue members."""
        self._all_layers = list(layers or [])

    def _log_debug(self, message: str, level: str = 'debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)

    # ==================================================================
    # Helpers
    # ==================================================================
    def _detect_member_type(self, member) -> str:
        for member_type, detector in self.MEMBER_TYPE_DETECTORS.items():
            if detector(member):
                return member_type
        return 'normal'

    def _generate_member(self, member) -> str:
        """Generate one member"""
        member_type = self._detect_member_type(member)
        template = self.MEMBER_TEMPLATES[member_type]
        member_name = self.naming.sanitize_identifier(getattr(member, 'name', 'unnamed'))
        c_type = self.mapper.map_type(getattr(member, 'data_type', 'void'))
        indent = self.strings['indent_1']

        if member_type == 'bit_field':
            return template.substitute(
                indent=indent, c_type=c_type,
                name=member_name,
                width=getattr(member, 'bit_width', 0),
            )
        elif member_type == 'array':
            return template.substitute(
                indent=indent, c_type=c_type,
                name=member_name,
                size=getattr(member, 'array_size', 0),
            )
        else:
            return template.substitute(
                indent=indent, c_type=c_type, name=member_name,
            )

    # ==================================================================
    # 1. Custom type
    # ==================================================================
    def _generate_custom_type(self, struct_def: CustomTypeDef) -> str:
        self._log_debug(f"Generating custom type: {getattr(struct_def, 'name', 'unknown')}")
        lines = []

        # Comment
        if getattr(struct_def, 'description', ''):
            lines.append(f"/* {struct_def.description} */")
        if getattr(struct_def, 'title', '') and struct_def.title != getattr(struct_def, 'name', ''):
            lines.append(f"/* Title: {struct_def.title} */")

        # struct body
        lines.append("typedef struct {")
        for member in getattr(struct_def, 'members', []):
            if getattr(member, 'description', ''):
                indent = self.strings['indent_1']
                lines.append(f"{indent}/* {member.description} */")
            if getattr(member, 'title', '') and member.title != getattr(member, 'name', ''):
                indent = self.strings['indent_1']
                lines.append(f"{indent}/* Title: {member.title} */")
            lines.append(self._generate_member(member).rstrip('\n'))

        type_name = self.naming.create_type_name(getattr(struct_def, 'name', 'Unknown'))
        lines.append(f"}} {type_name};")

        return '\n'.join(lines)

    # ==================================================================
    # 2. SystemData_t
    # ==================================================================
    def _generate_system_data(self, global_defs: GlobalDefinitions) -> str:
        self._log_debug("Generating system data struct")
        lines = []

        # Comment
        comment = self.templates.STRUCT_COMMENTS.get('system_data', {})
        lines.append(f"/* {comment.get('title', '')} */")
        lines.append(f"/* {comment.get('description', '')} */")

        # struct body
        lines.append("typedef struct {")
        current_group = None
        indent = self.strings['indent_1']

        for var in getattr(global_defs, 'variables', []):
            # Group comment
            if getattr(var, 'group', '') and var.group != current_group:
                if current_group is not None:
                    lines.append("")
                lines.append(f"{indent}/* === {var.group} === */")
                current_group = var.group

            # Description / unit
            comments = []
            if getattr(var, 'description', ''):
                comments.append(var.description)
            if getattr(var, 'unit', ''):
                comments.append(f"[{var.unit}]")
            if comments:
                lines.append(f"{indent}/* {' '.join(comments)} */")

            # Variable body
            var_name = self.naming.sanitize_identifier(getattr(var, 'name', 'unnamed'))
            c_type = self.mapper.map_type(getattr(var, 'type', 'void'))

            if getattr(var, 'array_size', 0) > 0:
                lines.append(f"{indent}{c_type} {var_name}[{var.array_size}];")
            else:
                lines.append(f"{indent}{c_type} {var_name};")

        lines.append(f"}} {self.templates.TYPE_NAMES['system_data']};")
        return '\n'.join(lines)

    # ==================================================================
    # 3. EventFlags_t
    # ==================================================================
    def _generate_event_flags(self, global_defs: GlobalDefinitions) -> str:
        self._log_debug("Generating event flags struct")
        lines = []

        # Comment
        comment = self.templates.STRUCT_COMMENTS.get('event_flags', {})
        lines.append(f"/* {comment.get('title', '')} */")
        lines.append(f"/* {comment.get('description', '')} */")

        # struct body
        lines.append("typedef struct {")
        current_group = None
        indent = self.strings['indent_1']

        for flag in getattr(global_defs, 'flags', []):
            # Group comment
            if getattr(flag, 'group', '') and flag.group != current_group:
                if current_group is not None:
                    lines.append("")
                lines.append(f"{indent}/* === {flag.group} === */")
                current_group = flag.group

            # Description
            if getattr(flag, 'description', ''):
                lines.append(f"{indent}/* {flag.description} */")

            # Flag body
            flag_name = self.naming.sanitize_identifier(getattr(flag, 'name', 'unnamed'))
            lines.append(f"{indent}uint8_t {flag_name};")

        lines.append(f"}} {self.templates.TYPE_NAMES['event_flags']};")
        return '\n'.join(lines)

    # ==================================================================
    # 4. SystemContext_t (pending_event added)
    # ==================================================================
    def _generate_system_context(self, global_defs: GlobalDefinitions) -> str:
        """
        Generate SystemContext_t (with pending_event / pending_event_valid).

        Example output:
            /* System context struct */
            /* Integrates global variables and event flags */
            typedef struct {
                SystemData_t data;              /* global variables */
                EventFlags_t flags;             /* event flags */
                uint16_t pending_event;         /* pending event */
                bool pending_event_valid;       /* pending event valid flag */
            } SystemContext_t;
        """
        self._log_debug("Generating system context struct (with pending_event)")
        T = self.CONTEXT_TEMPLATES
        lines = []

        # Comment
        comment = self.templates.STRUCT_COMMENTS.get('system_context', {})
        lines.append(T['section_comment'].substitute(
            title=comment.get('title', 'System context struct'),
            description=comment.get('description', 'Integrates global variables and event flags'),
        ).rstrip('\n'))

        # struct body
        lines.append(T['struct_start'].rstrip('\n'))
        lines.append(T['member_data'].substitute(
            system_data_type=self.templates.TYPE_NAMES['system_data'],
        ).rstrip('\n'))
        lines.append(T['member_flags'].substitute(
            event_flags_type=self.templates.TYPE_NAMES['event_flags'],
        ).rstrip('\n'))

        # [F-3 Step 2] per-layer pending_event slots
        for layer_name, sm in self._all_layers:
            layer = getattr(sm, 'layer_name', '') or layer_name
            if layer:
                lines.append(
                    T['member_pending_event'].substitute(
                        layer=layer).rstrip('\n'))
                lines.append(
                    T['member_pending_event_valid'].substitute(
                        layer=layer).rstrip('\n'))

        # [C-52] per-layer queues
        for layer_name, sm in self._all_layers:
            layer = getattr(sm, 'layer_name', '') or layer_name
            if layer:
                lines.append(
                    T['member_queue'].substitute(layer=layer).rstrip('\n'))

        # struct end
        lines.append(T['struct_end'].substitute(
            type_name=self.templates.TYPE_NAMES['system_context'],
        ).rstrip('\n'))

        return '\n'.join(lines)

    # ==================================================================
    # 5. Common TransitionContext_t (base type)
    # ==================================================================
    def generate_common_transition_context(self) -> str:
        """
        Generate the common base type TransitionContext_t.

        Example output:
            /* Generic transition context (for common role functions across layers) */
            /* Same layout as each layer's TransitionContext_<Layer>_t */
            typedef struct {
                uint16_t from_state;   /* source state (cast from layer enum) */
                uint16_t event;        /* event (cast from layer enum) */
            } TransitionContext_t;
        """
        self._log_debug("Generating common TransitionContext_t")
        T = self.COMMON_TRANSITION_CONTEXT_TEMPLATES
        lines = [
            T['comment'].rstrip('\n'),
            T['struct_start'].rstrip('\n'),
            T['member_from_state'].rstrip('\n'),
            T['member_event'].rstrip('\n'),
            T['struct_end'].rstrip('\n'),
        ]
        return '\n'.join(lines)

    # ==================================================================
    # 6. Per-layer TransitionContext_<Layer>_t
    # ==================================================================
    def generate_layer_transition_context(self, state_type: str,
                                          event_type: str) -> str:
        """
        Generate per-layer TransitionContext_<Layer>_t.

        Args:
            state_type: layer state type (e.g. 'STATE_Driver_t')
            event_type: layer event type (e.g. 'EVENT_Driver_t')

        Example output:
            /* Transition context for Driver layer */
            typedef struct {
                STATE_Driver_t from_state;   /* source state */
                EVENT_Driver_t event;        /* event */
            } TransitionContext_Driver_t;
        """
        if not self.layer_name:
            self._log_debug("generate_layer_transition_context: layer_name is empty, "
                            "returning empty string")
            return ""

        self._log_debug(f"Generating layer TransitionContext for '{self.layer_name}'")
        T = self.LAYER_TRANSITION_CONTEXT_TEMPLATES
        type_name = f"TransitionContext_{self.layer_name}_t"

        lines = [
            T['comment'].substitute(layer=self.layer_name).rstrip('\n'),
            T['struct_start'].rstrip('\n'),
            T['member_from_state'].substitute(state_type=state_type).rstrip('\n'),
            T['member_event'].substitute(event_type=event_type).rstrip('\n'),
            T['struct_end'].substitute(type_name=type_name).rstrip('\n'),
        ]
        return '\n'.join(lines)

    # ==================================================================
    # 7. Pending event macros (FIRE_EVENT / MAX_CONSECUTIVE_PENDING_EVENTS)
    # ==================================================================
    def generate_pending_event_macros(self) -> str:
        """
        Generate pending event control macros.

        Example output:
            /* ============================================================== */
            /*  Pending event control                                         */
            /* ============================================================== */

            /* Event fire macro */
            /* Used within role functions: FIRE_EVENT(ctx, EVENT_XXX_YYY); */
            #define FIRE_EVENT(ctx, evt)  do { \\
                (ctx)->pending_event = (uint16_t)(evt); \\
                (ctx)->pending_event_valid = true; \\
            } while(0)

            /* Upper limit for consecutive pending event processing */
            /* Infinite loop prevention. Can be overridden at build time via -D */
            #ifndef MAX_CONSECUTIVE_PENDING_EVENTS
            #define MAX_CONSECUTIVE_PENDING_EVENTS 16
            #endif
        """
        self._log_debug("Generating pending event macros")
        T = self.MACRO_TEMPLATES
        parts = [T['section_comment']]
        # [F-3 Step 2] FIRE_EVENT(ctx, evt) is removed.
        parts.append(
            '\n'
            '/* [F-3 Step 2] FIRE_EVENT(ctx, evt) is removed.           */\n'
            '/* Use FIRE_EVENT_<Layer>(ctx, evt) with an explicit layer. */\n'
        )
        _bs = chr(92)  # backslash
        _tpl = (
            '\n'
            '/* Fire event for {layer} layer (protected) */\n'
            '#define FIRE_EVENT_{layer}(ctx, evt)  do {{ {bs}\n'
            '    STATABLE_ENTER_CRITICAL(); {bs}\n'
            '    (ctx)->pending_event_{layer} = (uint16_t)(evt); {bs}\n'
            '    (ctx)->pending_event_valid_{layer} = true; {bs}\n'
            '    STATABLE_EXIT_CRITICAL(); {bs}\n'
            '}} while (0)\n'
        )
        seen = set()
        for layer_name, sm in self._all_layers:
            layer = getattr(sm, 'layer_name', '') or layer_name
            if not layer or layer in seen:
                continue
            seen.add(layer)
            parts.append(_tpl.format(layer=layer, bs=_bs))
        parts.append(T['max_consecutive_macro'])
        return ''.join(parts)

    # ================================================================
    # [C-52] Per-layer queue: types + macros
    # ================================================================
    def generate_layer_queue_types(self) -> str:
        """EventQueueState_t + size macro (emitted once)."""
        if not self._all_layers:
            return ""
        T = self.MACRO_TEMPLATES
        return ''.join([
            T['queue_section_comment'],
            T['critical_hooks'],
            T['queue_size_macro'],
            T['queue_state_type'],
        ])

    def generate_layer_queue_macros(self) -> str:
        """FIRE_EVENT_QUEUE_<Layer> / INIT_EVENT_QUEUE_<Layer> macros."""
        if not self._all_layers:
            return ""
        parts = []
        seen = set()
        for layer_name, sm in self._all_layers:
            layer = getattr(sm, 'layer_name', '') or layer_name
            if not layer or layer in seen:
                continue
            seen.add(layer)
            parts.append(
                f'\n'
                f'/* Queue send (C-54: protected by hooks; drops+counts if full) */\n'
                f'#define FIRE_EVENT_QUEUE_{layer}(ctx, evt)  do {{ \\\n'
                f'    STATABLE_ENTER_CRITICAL(); \\\n'
                f'    EventQueueState_t *q_ = &(ctx)->queue_{layer}; \\\n'
                f'    if (q_->count < STATABLE_LAYER_QUEUE_SIZE) {{ \\\n'
                f'        q_->buffer[q_->tail] = (uint16_t)(evt); \\\n'
                f'        q_->tail = (uint16_t)((q_->tail + 1U) % STATABLE_LAYER_QUEUE_SIZE); \\\n'
                f'        q_->count++; \\\n'
                f'    }} else {{ \\\n'
                f'        q_->dropped++; \\\n'
                f'    }} \\\n'
                f'    STATABLE_EXIT_CRITICAL(); \\\n'
                f'}} while (0)\n'
            )
            parts.append(
                f'\n'
                f'/* Queue init (C-54: protected) */\n'
                f'#define INIT_EVENT_QUEUE_{layer}(ctx)  do {{ \\\n'
                f'    STATABLE_ENTER_CRITICAL(); \\\n'
                f'    (ctx)->queue_{layer}.head = 0U; \\\n'
                f'    (ctx)->queue_{layer}.tail = 0U; \\\n'
                f'    (ctx)->queue_{layer}.count = 0U; \\\n'
                f'    (ctx)->queue_{layer}.dropped = 0U; \\\n'
                f'    STATABLE_EXIT_CRITICAL(); \\\n'
                f'}} while (0)\n'
            )
        return ''.join(parts)
    def generate_all_structs(self, global_defs: GlobalDefinitions) -> str:
        """Generate all structs in bulk
        (custom_type + system_data + event_flags + system_context).

        [v2.2.1 fix] Section header now emits a valid C block comment
        using section_line_start / section_line_end.
        """
        lines = []

        def _section_header(title_key: str) -> str:
            start = self.strings['section_line_start']
            end = self.strings['section_line_end']
            title = self.templates.SECTION_HEADERS.get(title_key, '')
            return f"{start}\n *  {title}\n{end}"

        # custom_types
        if getattr(global_defs, 'custom_types', []):
            lines.append(_section_header('custom_types'))
            lines.append("")
            for custom_type in global_defs.custom_types:
                lines.append(self._generate_custom_type(custom_type))
                lines.append("")

        # system_structs
        lines.append(_section_header('system_structs'))
        lines.append("")
        lines.append(self._generate_system_data(global_defs))
        lines.append("")
        lines.append(self._generate_event_flags(global_defs))
        lines.append("")
        lines.append(self._generate_system_context(global_defs))

        return '\n'.join(lines)

    def generate_all(self, global_defs: GlobalDefinitions) -> Dict[str, str]:
        """
        Return all generated artifacts as a dictionary.

        Returns:
            {
                'custom_types': str,               # user-defined types
                'system_data': str,                # SystemData_t
                'event_flags': str,                # EventFlags_t
                'system_context': str,             # SystemContext_t (with pending_event)
                'common_transition_context': str,  # common TransitionContext_t (base)
                'pending_event_macros': str,       # FIRE_EVENT / MAX_CONSECUTIVE
            }
        """
        self._log_debug("=== generate_all START (struct_generator) ===")
        result = {
            'custom_types': '\n\n'.join(
                self._generate_custom_type(ct)
                for ct in getattr(global_defs, 'custom_types', [])
            ),
            'system_data': self._generate_system_data(global_defs),
            'event_flags': self._generate_event_flags(global_defs),
            'system_context': self._generate_system_context(global_defs),
            'common_transition_context': self.generate_common_transition_context(),
            'pending_event_macros': self.generate_pending_event_macros(),
        }
        self._log_debug("=== generate_all END (struct_generator) ===")
        return result

    # ==================================================================
    # Backward-compatible API
    # ==================================================================
    def generate_struct(self, struct_type: str, item) -> str:
        """Backward compat: generate a single struct"""
        if struct_type == 'custom_type':
            return self._generate_custom_type(item)
        elif struct_type == 'system_data':
            return self._generate_system_data(item)
        elif struct_type == 'event_flags':
            return self._generate_event_flags(item)
        elif struct_type == 'system_context':
            return self._generate_system_context(item)
        elif struct_type == 'common_transition_context':
            return self.generate_common_transition_context()
        elif struct_type == 'pending_event_macros':
            return self.generate_pending_event_macros()
        elif struct_type == 'layer_queue_types':
            return self.generate_layer_queue_types()
        elif struct_type == 'layer_queue_macros':
            return self.generate_layer_queue_macros()
        raise ValueError(f"Unknown struct type: {struct_type}")