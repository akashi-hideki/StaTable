# codegen/enum_generator.py
"""
C enum code generation module (multi-layer state machine support)

[v1.5 fix]
  - generate_event_enum: filter out empty-name events from the main loop
    (NONE is already handled at the top, preventing duplicate definitions)
"""

import sys
import os
import logging
from string import Template
from typing import Dict, List, Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statable.model import State, Event, StateType, EventKind
from statable.global_defs import EventFlag

try:
    from .naming_convention import CNamingConvention
    from .code_templates import CodeTemplates
except ImportError:
    from naming_convention import CNamingConvention
    from code_templates import CodeTemplates

logger = logging.getLogger(__name__)


class CEnumGenerator:
    """C enum code generation class (multi-layer state machine support)"""

    ENUM_TEMPLATES = {
        'section_comment': Template(
            '/* $description */\n'
        ),
        'enum_start': 'typedef enum {\n',
        'value_with_comment': Template(
            '    $name = $value,    /* $comment */\n'
        ),
        'value': Template(
            '    $name = $value,\n'
        ),
        'max_value': Template(
            '    $name           /* element count (for system use) */\n'
        ),
        'enum_end': Template(
            '} $type_name;\n'
        ),
    }

    LAYER_TYPE_NAMES = {
        'state': {
            'value_prefix': 'STATE',
            'type_suffix': '_t',
            'max_suffix': '_MAX',
            'none_value': None,
        },
        'event': {
            'value_prefix': 'EVENT',
            'type_suffix': '_t',
            'max_suffix': '_MAX',
            'none_value': 'NONE',
        },
        'flag': {
            'value_prefix': 'FLAG',
            'type_suffix': '_t',
            'max_suffix': '_MAX',
            'none_value': None,
        },
    }

    COMMENT_FORMATS = {
        'state': {
            'description_suffix': None,
            'type_suffix': 'Type: {type_name}',
            'title_prefix': 'Title: ',
        },
        'event': {
            'description_suffix': None,
            'kind_suffix': 'Kind: {kind_name}',
            'title_prefix': 'Title: ',
        },
        'flag': {
            'description_suffix': None,
            'title_prefix': 'Title: ',
        },
    }

    def __init__(self):
        self.naming = CNamingConvention()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        self.layer_name: str = ""

    def set_layer(self, layer_name: str):
        self.layer_name = layer_name
        logger.debug(f"CEnumGenerator.set_layer: layer_name='{layer_name}'")

    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)

    def _state_value_name(self, state_name: str) -> str:
        pascal = self.naming.to_pascal_case(state_name) if state_name else "Unknown"
        if self.layer_name:
            return f"STATE_{self.layer_name}_{pascal}"
        return f"STATE_{pascal}"

    def _event_value_name(self, event_name: str) -> str:
        if not event_name:
            upper = "NONE"
        else:
            upper = self.naming.to_upper_snake(event_name)
        if self.layer_name:
            return f"EVENT_{self.layer_name}_{upper}"
        return f"EVENT_{upper}"

    def _flag_value_name(self, flag_name: str) -> str:
        upper = self.naming.to_upper_snake(flag_name)
        return f"FLAG_{upper}"

    def _state_type_name(self) -> str:
        if self.layer_name:
            return f"STATE_{self.layer_name}_t"
        return "STATE_t"

    def _event_type_name(self) -> str:
        if self.layer_name:
            return f"EVENT_{self.layer_name}_t"
        return "EVENT_t"

    def _flag_type_name(self) -> str:
        return "FLAG_t"

    def _state_max_name(self) -> str:
        if self.layer_name:
            return f"STATE_{self.layer_name}_MAX"
        return "STATE_MAX"

    def _event_max_name(self) -> str:
        if self.layer_name:
            return f"EVENT_{self.layer_name}_MAX"
        return "EVENT_MAX"

    def _flag_max_name(self) -> str:
        return "FLAG_MAX"

    def _generate_state_comment(self, state: State) -> str:
        comments = []
        if getattr(state, 'description', ''):
            comments.append(state.description)
        if getattr(state, 'type', None) and state.type != StateType.NORMAL:
            comments.append(f"Type: {state.type.name}")
        if getattr(state, 'title', ''):
            comments.append(f"Title: {state.title}")
        return ' '.join(comments)

    def _generate_event_comment(self, event: Event) -> str:
        comments = []
        if getattr(event, 'description', ''):
            comments.append(event.description)
        if getattr(event, 'kind', None) and event.kind != EventKind.SIGNAL:
            comments.append(f"Kind: {event.kind.name}")
        if getattr(event, 'title', ''):
            comments.append(f"Title: {event.title}")
        return ' '.join(comments)

    def _generate_flag_comment(self, flag: EventFlag) -> str:
        comments = []
        if getattr(flag, 'description', ''):
            comments.append(flag.description)
        if getattr(flag, 'title', ''):
            comments.append(f"Title: {flag.title}")
        return ' '.join(comments)

    def _generate_enum_values(self, items: List[Any],
                              value_name_func,
                              comment_func,
                              none_value: Optional[str] = None,
                              none_comment: str = "") -> str:
        T = self.ENUM_TEMPLATES
        parts = []

        if none_value is not None:
            none_name = value_name_func("")
            parts.append(T['value_with_comment'].substitute(
                name=none_name,
                value=0,
                comment=none_comment,
            ))
            start_index = 1
        else:
            start_index = 0

        for i, item in enumerate(items):
            value = start_index + i
            name = value_name_func(getattr(item, 'name', 'unnamed'))
            comment = comment_func(item)

            if comment:
                parts.append(T['value_with_comment'].substitute(
                    name=name, value=value, comment=comment,
                ))
            else:
                parts.append(T['value'].substitute(
                    name=name, value=value,
                ))

        return ''.join(parts)

    def generate_state_enum(self, states: List[State]) -> str:
        if not states:
            return ''

        self._log_debug(f"=== generate_state_enum START: {len(states)} states ===")
        T = self.ENUM_TEMPLATES
        parts = []

        desc = f"{self.layer_name} layer state definitions" if self.layer_name else "State definitions"
        parts.append(T['section_comment'].substitute(description=desc))

        parts.append(T['enum_start'])

        parts.append(self._generate_enum_values(
            items=states,
            value_name_func=self._state_value_name,
            comment_func=self._generate_state_comment,
            none_value=None,
        ))

        parts.append(T['max_value'].substitute(name=self._state_max_name()))
        parts.append(T['enum_end'].substitute(type_name=self._state_type_name()))

        result = ''.join(parts)
        self._log_debug(f"=== generate_state_enum END ===")
        return result

    def generate_event_enum(self, events: List[Event]) -> str:
        """
        Generate event enum (including NONE = 0).

        [v1.5 fix]
          Empty-name events (used for completion transitions, `name=""`)
          are already handled as NONE at the top, so exclude them from
          the main loop. This prevents duplicate EVENT_<Layer>_NONE.
        """
        if not events:
            return ''

        # v1.5 fix: exclude empty-name events
        non_empty_events = [
            e for e in events if getattr(e, 'name', '')
        ]
        filtered = len(events) - len(non_empty_events)
        if filtered:
            self._log_debug(
                f"generate_event_enum: filtered out {filtered} empty-name "
                f"event(s) (already processed as NONE)"
            )

        self._log_debug(f"=== generate_event_enum START: "
                        f"{len(non_empty_events)} events ===")
        T = self.ENUM_TEMPLATES
        parts = []

        desc = f"{self.layer_name} layer event definitions" if self.layer_name else "Event definitions"
        parts.append(T['section_comment'].substitute(description=desc))

        parts.append(T['enum_start'])

        parts.append(self._generate_enum_values(
            items=non_empty_events,
            value_name_func=self._event_value_name,
            comment_func=self._generate_event_comment,
            none_value="NONE",
            none_comment="completion transition",
        ))

        parts.append(T['max_value'].substitute(name=self._event_max_name()))
        parts.append(T['enum_end'].substitute(type_name=self._event_type_name()))

        result = ''.join(parts)
        self._log_debug(f"=== generate_event_enum END ===")
        return result

    def generate_flag_enum(self, flags: List[EventFlag]) -> str:
        if not flags:
            return ''

        self._log_debug(f"=== generate_flag_enum START: {len(flags)} flags ===")
        T = self.ENUM_TEMPLATES
        parts = []

        parts.append(T['section_comment'].substitute(description="Event flag definitions"))
        parts.append(T['enum_start'])

        parts.append(self._generate_enum_values(
            items=flags,
            value_name_func=self._flag_value_name,
            comment_func=self._generate_flag_comment,
            none_value=None,
        ))

        parts.append(T['max_value'].substitute(name=self._flag_max_name()))
        parts.append(T['enum_end'].substitute(type_name=self._flag_type_name()))

        result = ''.join(parts)
        self._log_debug(f"=== generate_flag_enum END ===")
        return result

    def generate_all_enums(self, states: List[State], events: List[Event],
                           flags: List[EventFlag] = None) -> str:
        self._log_debug(f"=== generate_all_enums START: "
                        f"{len(states)} states, {len(events)} events, "
                        f"{len(flags) if flags else 0} flags ===")
        parts = []

        state_enum = self.generate_state_enum(states)
        if state_enum:
            parts.append(state_enum)
            parts.append("")

        event_enum = self.generate_event_enum(events)
        if event_enum:
            parts.append(event_enum)
            parts.append("")

        if flags:
            flag_enum = self.generate_flag_enum(flags)
            if flag_enum:
                parts.append(flag_enum)

        result = '\n'.join(parts)
        self._log_debug(f"=== generate_all_enums END: {len(result)} chars ===")
        return result

    def generate_bit_mask_enum(self, flags: List[EventFlag]) -> str:
        if not flags:
            return ''

        self._log_debug(f"=== generate_bit_mask_enum START: {len(flags)} flags ===")
        T = self.ENUM_TEMPLATES
        parts = []

        parts.append('/* Event flag bitmask definitions */\n')
        parts.append('/* Used when managing flags as individual bits */\n')
        parts.append(T['enum_start'])

        for i, flag in enumerate(flags):
            bit_value = 1 << i
            upper = self.naming.to_upper_snake(getattr(flag, 'name', 'unnamed'))
            name = f"FLAG_MASK_{upper}"
            comment = self._generate_flag_comment(flag)
            if comment:
                parts.append(f"    {name} = 0x{bit_value:02X},    /* {comment} */\n")
            else:
                parts.append(f"    {name} = 0x{bit_value:02X},\n")

        parts.append(T['enum_end'].substitute(type_name="FLAG_MASK_t"))

        result = ''.join(parts)
        self._log_debug(f"=== generate_bit_mask_enum END ===")
        return result

    def generate_enum(self, enum_type: str, items: List[Any]) -> str:
        if enum_type == 'state':
            return self.generate_state_enum(items)
        elif enum_type == 'event':
            return self.generate_event_enum(items)
        elif enum_type == 'flag':
            return self.generate_flag_enum(items)
        else:
            logger.warning(f"Unknown enum_type: {enum_type}")
            return ""