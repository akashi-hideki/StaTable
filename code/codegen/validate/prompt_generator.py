# codegen/validate/prompt_generator.py
"""
AI prompt generation class

[v2.8.0 / SPEC_AI_PROMPT_v1.1]
  - Full prompt refresh (XML-style tags).
  - `_format_data` extended to include role_functions, cells, and
    global_definitions (previously missing).
  - `_format_validation` now emits structured <issue> elements
    (severity / category / code / target / suggestion).
  - `_format_actions` renders the 17 ACTION_DEFINITIONS as XML.
  - Reserved role-function fields and used_* symbol trackers are
    deliberately NOT sent (not consumed by codegen / not actionable).
  - Backward compatible: `generate_diagnosis_prompt` signature is
    unchanged; the legacy FEW_SHOT_EXAMPLE / VALIDATION_POINTS
    constants remain importable from prompt_templates.

[v2.8.0-fix1]
  - `_format_cells` now returns "  <cells/>" for empty / missing
    sections, consistent with every other <context> sub-builder.

[v2.8.0-fix2]
  - `_format_global_definitions` now skips a pristine `timer_base`
    (a freshly constructed GlobalDefinitions() has a default
    TimerBaseDef that carries no user information). New helper
    `_has_timer_content` decides whether the timer section is
    worth emitting.
"""

import sys
import os
from typing import Any, Optional

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from .logger import logger
from .data.prompt_templates import (
    PROMPT_TEMPLATES,
    OUTPUT_SCHEMA,
    FEW_SHOT_EXAMPLE_1,
    FEW_SHOT_EXAMPLE_2,
)
from .data.action_definitions import ACTION_DEFINITIONS


# ======================================================================
# XML attribute escaping
# ======================================================================
def _esc(value) -> str:
    """Escape a value for safe inclusion in an XML attribute."""
    if value is None:
        return ""
    s = str(value)
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))


def _bool_attr(value: bool) -> str:
    return "true" if value else "false"


# ======================================================================
# Normalization helpers (mirrors xml_io._normalize_actions)
# ======================================================================
def _as_str_list(value):
    """Return a clean list of strings for legacy List[str] fields."""
    if value is None:
        return []
    if isinstance(value, str):
        s = value.strip()
        return [s] if s else []
    if isinstance(value, list):
        return [str(x) for x in value if str(x).strip()]
    return [str(value)]


class AIPromptGenerator:
    """AI prompt generation class."""

    def __init__(self):
        logger.debug("AIPromptGenerator.__init__ started")
        self.templates = PROMPT_TEMPLATES
        self.output_schema = OUTPUT_SCHEMA
        self.example_1 = FEW_SHOT_EXAMPLE_1
        self.example_2 = FEW_SHOT_EXAMPLE_2
        logger.debug("AIPromptGenerator.__init__ completed")

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def generate_diagnosis_prompt(self, sm, gd, validation_result=None) -> str:
        """Build the full diagnosis prompt as a single string."""
        template = self.templates['diagnosis']['template']
        return template.format(
            output_schema=self.output_schema,
            example_1=self.example_1,
            example_2=self.example_2,
            context=self._format_data(sm, gd),
            validation=self._format_validation(validation_result),
            actions=self._format_actions(),
        )

    # ------------------------------------------------------------------
    # <context> builder
    # ------------------------------------------------------------------
    def _format_data(self, sm, gd) -> str:
        """Build the inner content of <context>...</context> as XML.

        Includes: <layer>, <states>, <events>, <transitions>,
        <role_functions>, <cells>, <global_definitions>.
        Empty sections are emitted as self-closing tags so the AI
        can tell them apart from a missing section.
        """
        parts = [
            self._format_layer(sm),
            self._format_states(sm),
            self._format_events(sm),
            self._format_transitions(sm),
            self._format_role_functions(sm),
            self._format_cells(sm),
            self._format_global_definitions(gd),
        ]
        return "\n".join(p for p in parts if p)

    # ---------- <layer> ----------
    def _format_layer(self, sm) -> str:
        name = getattr(sm, 'layer_name', '') or 'Untitled'
        priority = getattr(sm, 'layer_priority', 5)
        attrs = [f'name="{_esc(name)}"', f'priority="{priority}"']
        initial = getattr(sm, 'initial_state', None)
        if initial:
            attrs.append(f'initial="{_esc(initial)}"')
        desc = getattr(sm, 'layer_description', '') or ''
        if desc:
            attrs.append(f'description="{_esc(desc)}"')
        return f"  <layer {' '.join(attrs)}/>"

    # ---------- <states> ----------
    def _format_states(self, sm) -> str:
        states = getattr(sm, 'states', None) or {}
        if not states:
            return "  <states/>"
        lines = ["  <states>"]
        for state in states.values():
            attrs = [f'name="{_esc(state.name)}"',
                     f'type="{state.type.value}"']
            if state.parent:
                attrs.append(f'parent="{_esc(state.parent)}"')
            if state.description:
                attrs.append(f'description="{_esc(state.description)}"')

            entry = self._format_action_list(getattr(state, 'entry', []) or [])
            exit_ = self._format_action_list(getattr(state, 'exit', []) or [])
            do = self._format_action_list(
                getattr(state, 'do_actions', []) or [])

            if not (entry or exit_ or do):
                lines.append(f"    <state {' '.join(attrs)}/>")
                continue

            lines.append(f"    <state {' '.join(attrs)}>")
            if entry:
                lines.append("      <entry>")
                lines.extend(entry)
                lines.append("      </entry>")
            if exit_:
                lines.append("      <exit>")
                lines.extend(exit_)
                lines.append("      </exit>")
            if do:
                lines.append("      <do>")
                lines.extend(do)
                lines.append("      </do>")
            lines.append("    </state>")
        lines.append("  </states>")
        return "\n".join(lines)

    def _format_action_list(self, actions) -> list:
        """Render List[ActionStep] as indented <action/> lines.

        Simple role-only actions are emitted as
        `<action role_function="X"/>` to match xml_io's canonical
        output. action_type="custom" is skipped: it is user code,
        not an AI-actionable change.
        """
        result = []
        for a in actions or []:
            role = getattr(a, 'role_function', '') or ''
            cond = getattr(a, 'condition', '') or ''
            atype = getattr(a, 'action_type', 'role') or 'role'
            ename = getattr(a, 'event_name', '') or ''

            if atype == 'custom':
                continue

            attrs = []
            if atype == 'fire_event':
                attrs.append('action_type="fire_event"')
                if ename:
                    attrs.append(f'event_name="{_esc(ename)}"')
                if not ename:
                    continue
            else:
                if not role:
                    continue
                attrs.append(f'role_function="{_esc(role)}"')

            if cond:
                attrs.append(f'condition="{_esc(cond)}"')

            result.append(f'        <action {" ".join(attrs)}/>')
        return result

    # ---------- <events> ----------
    def _format_events(self, sm) -> str:
        events = getattr(sm, 'events', None) or {}
        if not events:
            return "  <events/>"
        lines = ["  <events>"]
        for event in events.values():
            attrs = [
                f'name="{_esc(event.name)}"',
                f'kind="{event.kind.value}"',
                f'delivery_type="{event.delivery_type.value}"',
                f'source_layer="{event.source_layer.value}"',
            ]
            if event.description:
                attrs.append(f'description="{_esc(event.description)}"')

            trigger = self._format_trigger(event)
            if trigger:
                lines.append(f"    <event {' '.join(attrs)}>")
                lines.append(trigger)
                lines.append("    </event>")
            else:
                lines.append(f"    <event {' '.join(attrs)}/>")
        lines.append("  </events>")
        return "\n".join(lines)

    def _format_trigger(self, event) -> str:
        """Render an <event>'s trigger, type-specifically."""
        td = getattr(event, 'trigger_detail', None)
        trigger_text = getattr(event, 'trigger', '') or ''

        if td is None:
            if not trigger_text:
                return ""
            return (
                '      <trigger type="manual" '
                f'description="{_esc(trigger_text)}"/>'
            )

        t = (getattr(td, 'type', 'manual') or 'manual').lower()
        attrs = [f'type="{_esc(t)}"']

        def _opt(name, val):
            if val:
                attrs.append(f'{name}="{_esc(val)}"')

        def _int(name, val):
            if val:
                attrs.append(f'{name}="{int(val)}"')

        if t == "edge":
            _opt("source", getattr(td, 'source', ''))
            _opt("edge", getattr(td, 'edge', ''))
            _int("debounce_ms", getattr(td, 'debounce_ms', 0))
            _opt("description", getattr(td, 'description', ''))
        elif t == "polling":
            _opt("source", getattr(td, 'source', ''))
            _int("period_ms", getattr(td, 'period_ms', 0))
            _opt("description", getattr(td, 'description', ''))
        elif t == "timer":
            _opt("source", getattr(td, 'source', ''))
            _int("period_ms", getattr(td, 'period_ms', 0))
            if not getattr(td, 'auto_reload', True):
                attrs.append('auto_reload="false"')
            _opt("description", getattr(td, 'description', ''))
        elif t == "call":
            _opt("caller", getattr(td, 'caller', ''))
            _opt("description", getattr(td, 'description', ''))
        elif t == "comparison":
            _opt("condition", getattr(td, 'condition', ''))
            _int("poll_period_ms", getattr(td, 'poll_period_ms', 0))
            _opt("description", getattr(td, 'description', ''))
        else:  # manual / unknown
            _opt("source", getattr(td, 'source', ''))
            _opt("description", getattr(td, 'description', ''))

        return f'      <trigger {" ".join(attrs)}/>'

    # ---------- <transitions> ----------
    def _format_transitions(self, sm) -> str:
        transitions = getattr(sm, 'transitions', None) or []
        if not transitions:
            return "  <transitions/>"
        lines = ["  <transitions>"]
        for t in transitions:
            attrs = [
                f'source="{_esc(t.source)}"',
                f'event="{_esc(t.event)}"',
                f'target="{_esc(t.target)}"',
            ]
            if t.condition:
                attrs.append(f'condition="{_esc(t.condition)}"')
            attrs.append(f'early_return="{_bool_attr(t.early_return)}"')
            if t.label:
                attrs.append(f'label="{_esc(t.label)}"')
            attrs.append(f'has_else="{_bool_attr(t.has_else)}"')
            if t.else_target:
                attrs.append(f'else_target="{_esc(t.else_target)}"')

            pre = _as_str_list(getattr(t, 'pre_actions', []))
            els = _as_str_list(getattr(t, 'else_actions', []))

            if not (pre or els):
                lines.append(f"    <transition {' '.join(attrs)}/>")
                continue

            lines.append(f"    <transition {' '.join(attrs)}>")
            if pre:
                lines.append("      <pre_actions>")
                for p in pre:
                    lines.append(f'        <action name="{_esc(p)}"/>')
                lines.append("      </pre_actions>")
            if els:
                lines.append("      <else_actions>")
                for e in els:
                    lines.append(f'        <action name="{_esc(e)}"/>')
                lines.append("      </else_actions>")
            lines.append("    </transition>")
        lines.append("  </transitions>")
        return "\n".join(lines)

    # ---------- <role_functions> ----------
    def _format_role_functions(self, sm) -> str:
        """Send only name / namespace / description.

        Reserved fields (return_type, arg1_*, arg2_*) and GUI-only
        symbol trackers (used_*) are deliberately omitted:
          - Reserved fields do not affect codegen or the prompt's
            semantic content.
          - used_* mirrors are GUI metadata, not actionable by AI.
        """
        rfs = getattr(sm, 'role_functions', None) or {}
        if not rfs:
            return "  <role_functions/>"
        lines = ["  <role_functions>"]
        for rf in rfs.values():
            attrs = [f'name="{_esc(rf.name)}"']
            ns = getattr(rf, 'namespace', '') or ''
            if ns:
                attrs.append(f'namespace="{_esc(ns)}"')
            desc = getattr(rf, 'description', '') or ''
            if desc:
                attrs.append(f'description="{_esc(desc)}"')
            lines.append(f"    <role_function {' '.join(attrs)}/>")
        lines.append("  </role_functions>")
        return "\n".join(lines)

    # ---------- <cells> ----------
    def _format_cells(self, sm) -> str:
        """Render <cells>. Empty/missing section still emits <cells/>.

        [v2.8.0-fix1]
          Consistency: every other <context> sub-builder emits a
          self-closing tag for empty sections. This method now matches
          that convention so the AI can always tell whether a section
          was intentionally empty vs. missing entirely.
        """
        try:
            cell_keys = sm.get_cell_keys()
        except AttributeError:
            return "  <cells/>"
        if not cell_keys:
            return "  <cells/>"

        lines = ["  <cells>"]
        for (source, event) in cell_keys:
            lines.append(
                f'    <cell source="{_esc(source)}" event="{_esc(event)}">'
            )

            actions: list[Any] = []
            try:
                actions = sm.get_actions_for_cell(source, event) or []
            except Exception:
                actions: list[Any] = []
            relations: list[Any] = []
            try:
                relations = sm.get_relations_for_cell(source, event) or []
            except Exception:
                relations: list[Any] = []

            if actions:
                lines.append("      <actions>")
                for a in actions:
                    a_attrs = []
                    role = getattr(a, 'role_function', '') or ''
                    trig = getattr(a, 'trigger', 'before_transitions') \
                        or 'before_transitions'
                    if role:
                        a_attrs.append(f'role_function="{_esc(role)}"')
                    if trig and trig != 'before_transitions':
                        a_attrs.append(f'trigger="{_esc(trig)}"')
                    if not a_attrs:
                        continue
                    lines.append(f'        <action {" ".join(a_attrs)}/>')
                lines.append("      </actions>")

            if relations:
                lines.append("      <relations>")
                for r in relations:
                    lines.extend(self._format_relation(r, indent=8))
                lines.append("      </relations>")

            lines.append("    </cell>")
        lines.append("  </cells>")
        return "\n".join(lines)

    def _format_relation(self, rel, indent: int) -> list:
        pad = ' ' * indent
        attrs = [f'kind="{_esc(getattr(rel, "kind", "sequential"))}"']
        members = getattr(rel, 'members', None) or []
        if members:
            joined = ",".join(_esc(m) for m in members)
            attrs.append(f'members="{joined}"')
        shared = getattr(rel, 'shared_condition', '') or ''
        if shared:
            attrs.append(f'shared_condition="{_esc(shared)}"')

        children = getattr(rel, 'children', None) or []
        if not children:
            return [f'{pad}<relation {" ".join(attrs)}/>']

        result = [f'{pad}<relation {" ".join(attrs)}>']
        for c in children:
            result.extend(self._format_relation(c, indent + 2))
        result.append(f'{pad}</relation>')
        return result

    def _timer_variable_names(self, gd) -> set:
        """Names of variables auto-generated by add_timer_variables().

        [v2.8.0-fix3]
          GlobalDefinitions.__init__ calls add_timer_variables(),
          which registers the timer_base and derived timers into
          gd.variables so the code generator can emit them. Those
          entries are already shown in <timers>, so we exclude them
          from <variables> to avoid duplication and to allow an
          empty GlobalDefinitions() to collapse to <global_definitions/>.
        """
        names = set()
        tb = getattr(gd, 'timer_base', None)
        if tb is not None:
            if getattr(tb, 'variable_name', ''):
                names.add(tb.variable_name)
            for d in getattr(tb, 'derived', None) or []:
                if getattr(d, 'variable_name', ''):
                    names.add(d.variable_name)
        for et in getattr(gd, 'extra_timers', None) or []:
            if getattr(et, 'variable_name', ''):
                names.add(et.variable_name)
            for d in getattr(et, 'derived', None) or []:
                if getattr(d, 'variable_name', ''):
                    names.add(d.variable_name)
        return names

    # ---------- <global_definitions> ----------
    def _format_global_definitions(self, gd) -> str:
        if gd is None:
            return "  <global_definitions/>"

        sections = []

        # Variables
        # [v2.8.0-fix3] Exclude auto-generated timer variables;
        # they are already shown in <timers>.
        timer_names = self._timer_variable_names(gd)
        variables = [
            v for v in (getattr(gd, 'variables', None) or [])
            if v.name not in timer_names
        ]
        if variables:
            v_lines = ["    <variables>"]
            for v in variables:
                v_attrs = [f'name="{_esc(v.name)}"',
                           f'type="{_esc(v.type)}"']
                if getattr(v, 'group', ''):
                    v_attrs.append(f'group="{_esc(v.group)}"')
                if getattr(v, 'description', ''):
                    v_attrs.append(
                        f'description="{_esc(v.description)}"')
                v_lines.append(
                    f'      <variable {" ".join(v_attrs)}/>')
            v_lines.append("    </variables>")
            sections.append("\n".join(v_lines))

        # Flags
        flags = getattr(gd, 'flags', None) or []
        if flags:
            f_lines = ["    <flags>"]
            for f in flags:
                f_attrs = [
                    f'name="{_esc(f.name)}"',
                    f'min_value="{getattr(f, "min_value", 0)}"',
                    f'max_value="{getattr(f, "max_value", 0)}"',
                ]
                if getattr(f, 'group', ''):
                    f_attrs.append(f'group="{_esc(f.group)}"')
                if getattr(f, 'description', ''):
                    f_attrs.append(
                        f'description="{_esc(f.description)}"')
                f_lines.append(f'      <flag {" ".join(f_attrs)}/>')
            f_lines.append("    </flags>")
            sections.append("\n".join(f_lines))

        # Interrupts
        interrupts = getattr(gd, 'interrupts', None) or []
        if interrupts:
            i_lines = ["    <interrupts>"]
            for intr in interrupts:
                i_attrs = [f'name="{_esc(intr.name)}"']
                evs = getattr(intr, 'event_names', None) or []
                if evs:
                    i_attrs.append(
                        f'event_names="{",".join(_esc(e) for e in evs)}"')
                if getattr(intr, 'is_timer', False):
                    i_attrs.append('is_timer="true"')
                if getattr(intr, 'description', ''):
                    i_attrs.append(
                        f'description="{_esc(intr.description)}"')

                actions = getattr(intr, 'actions', None) or []
                if not actions:
                    i_lines.append(
                        f'      <interrupt {" ".join(i_attrs)}/>')
                else:
                    i_lines.append(
                        f'      <interrupt {" ".join(i_attrs)}>')
                    for act in actions:
                        a_attrs = []
                        if getattr(act, 'condition', ''):
                            a_attrs.append(
                                f'condition="{_esc(act.condition)}"')
                        if getattr(act, 'action', ''):
                            a_attrs.append(
                                f'action="{_esc(act.action)}"')
                        if a_attrs:
                            i_lines.append(
                                f'        <action {" ".join(a_attrs)}/>')
                    i_lines.append("      </interrupt>")
            i_lines.append("    </interrupts>")
            sections.append("\n".join(i_lines))

        # Timers (timer_base + extra_timers)
        # [v2.8.0-fix2] A freshly constructed GlobalDefinitions() has
        # a default timer_base with only pristine values. That carries
        # no information for the AI, so skip it. Only emit the timers
        # section when the timer_base has been customized or when
        # extra timers exist.
        tb = getattr(gd, 'timer_base', None)
        if tb is not None and not self._has_timer_content(tb):
            tb = None
        extra = getattr(gd, 'extra_timers', None) or []
        if tb is not None or extra:
            t_lines = ["    <timers>"]
            if tb is not None:
                t_lines.extend(self._format_timer(tb, 'timer_base', 6))
            for et in extra:
                t_lines.extend(self._format_timer(et, 'extra_timer', 6))
            t_lines.append("    </timers>")
            sections.append("\n".join(t_lines))

        # Event queues
        queues = getattr(gd, 'event_queues', None) or []
        if queues:
            q_lines = ["    <event_queues>"]
            for q in queues:
                q_attrs = [
                    f'name="{_esc(q.name)}"',
                    f'size="{getattr(q, "size", 8)}"',
                    f'element_type="{_esc(getattr(q, "element_type", "uint8_t"))}"',
                ]
                if getattr(q, 'priority_enabled', False):
                    q_attrs.append('priority_enabled="true"')
                if not getattr(q, 'interrupt_safe', True):
                    q_attrs.append('interrupt_safe="false"')
                if getattr(q, 'rtos_enabled', False):
                    q_attrs.append('rtos_enabled="true"')
                if getattr(q, 'description', ''):
                    q_attrs.append(
                        f'description="{_esc(q.description)}"')
                q_lines.append(f'      <queue {" ".join(q_attrs)}/>')
            q_lines.append("    </event_queues>")
            sections.append("\n".join(q_lines))

        if not sections:
            return "  <global_definitions/>"

        return ("  <global_definitions>\n"
                + "\n".join(sections)
                + "\n  </global_definitions>")

    def _has_timer_content(self, tb) -> bool:
        """Return True if the timer_base has user-meaningful content.

        [v2.8.0-fix2]
          A freshly constructed GlobalDefinitions() has a default
          TimerBaseDef with only pristine values. Those defaults
          carry no information for the AI, so a pristine timer_base
          can be skipped in <global_definitions>. Any deviation
          from the defaults (or any derived timers) makes this
          method return True.

        [v2.8.0-fix4]
          `TimerBaseDef.title` is auto-populated to
          "Timer base: <variable_name>" by __post_init__, so it is
          NOT a reliable indicator of user customization. The title
          field is excluded from the pristine comparison; the
          semantic identity of a timer is determined by
          variable_name / unit / data_type / derived.
        """
        if getattr(tb, 'derived', None):
            return True
        defaults = {
            'variable_name': 'g_system_tick',
            'unit': '1ms',
            'data_type': 'volatile uint32_t',
            'interrupt_name': '',
        }
        for attr, expected in defaults.items():
            if getattr(tb, attr, '') != expected:
                return True
        return False

    def _format_timer(self, timer, tag: str, indent: int) -> list:
        pad = ' ' * indent
        attrs = [f'variable_name="{_esc(timer.variable_name)}"']
        if getattr(timer, 'unit', ''):
            attrs.append(f'unit="{_esc(timer.unit)}"')
        if getattr(timer, 'data_type', ''):
            attrs.append(f'data_type="{_esc(timer.data_type)}"')

        derived = getattr(timer, 'derived', None) or []
        if not derived:
            return [f'{pad}<{tag} {" ".join(attrs)}/>']

        result = [f'{pad}<{tag} {" ".join(attrs)}>']
        for d in derived:
            d_attrs = [
                f'period_name="{_esc(d.period_name)}"',
                f'multiplier="{getattr(d, "multiplier", 1)}"',
            ]
            if getattr(d, 'variable_name', ''):
                d_attrs.append(
                    f'variable_name="{_esc(d.variable_name)}"')
            if getattr(d, 'data_type', ''):
                d_attrs.append(f'data_type="{_esc(d.data_type)}"')
            result.append(f'{pad}  <derived {" ".join(d_attrs)}/>')
        result.append(f'{pad}</{tag}>')
        return result

    # ------------------------------------------------------------------
    # <validation> builder
    # ------------------------------------------------------------------
    def _format_validation(self, validation_result) -> str:
        """Emit each issue as a structured <issue> element.

        Only category/code/target/suggestion are guaranteed to be
        ASCII-safe metadata; `message` is passed through verbatim
        (may be localized) so the AI can use it as context.
        """
        issues: list[Any] = []
        if validation_result is not None:
            issues = getattr(validation_result, 'issues', None) or []

        if not issues:
            return "    <!-- No issues -->"

        lines = []
        for issue in issues:
            sev = issue.severity.value.upper()
            attrs = [f'severity="{sev}"']
            if issue.category:
                attrs.append(f'category="{_esc(issue.category)}"')
            if issue.code:
                attrs.append(f'code="{_esc(issue.code)}"')
            if issue.target:
                attrs.append(f'target="{_esc(issue.target)}"')
            if issue.suggestion:
                attrs.append(
                    f'suggestion="{_esc(issue.suggestion)}"')
            msg = _esc(issue.message or '')
            lines.append(f'    <issue {" ".join(attrs)}>{msg}</issue>')
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # <actions> builder
    # ------------------------------------------------------------------
    def _format_actions(self) -> str:
        """Render the 17 ACTION_DEFINITIONS as XML."""
        lines = []
        for name, definition in ACTION_DEFINITIONS.items():
            desc = _esc(definition.get('description', ''))
            lines.append(
                f'    <action name="{_esc(name)}" description="{desc}">'
            )
            for pname, pinfo in definition.get('params', {}).items():
                p_attrs = [
                    f'name="{_esc(pname)}"',
                    f'type="{_esc(pinfo.get("type", "str"))}"',
                    f'required="{_bool_attr(bool(pinfo.get("required")))}"',
                ]
                if 'values' in pinfo:
                    vals = ",".join(_esc(v) for v in pinfo['values'])
                    p_attrs.append(f'values="{vals}"')
                lines.append(f'      <param {" ".join(p_attrs)}/>')
            lines.append('    </action>')
        return "\n".join(lines)