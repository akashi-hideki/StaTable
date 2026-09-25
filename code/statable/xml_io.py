# statable/xml_io.py
"""
XML I/O for StaTable.

Version History
---------------
v2.2   - State.entry / exit: str -> List[str]
         Transition.early_return / label
         Cell-level metadata: <Cells><Cell>...</Cell></Cells>
         §12-5: TransitionRelation.children (recursive nesting)

v3.7   - Reserved fields documented:
           * State.do
           * RoleFunction.return_type / arg1_type / arg1_name
                                    / arg2_type / arg2_name
         These are still read/written for backward compatibility,
         even though the GUI no longer exposes them.

v3.8   - RoleFunction: persist used_global_vars / used_events /
         used_literals as comma-separated attributes. Old XML
         without these attributes loads with empty lists.
         Also applies to the shared library (role_function_library).

v3.8.1 - Only emit used_* attributes when non-empty. This keeps
         the canonical XML of pre-v3.8 project files identical
         after a save, so that test_v2_2_p12_9.py's canonical
         tree comparison (Level 1) still passes.
         Empty values still load as [] via _split_csv().

v3.8.2 - role_function_library_to_element / _from_element now
         also emit / read the reserved signature fields
         (return_type / arg1_* / arg2_*) of the shared library.
         The test fixture tests/data/v22_features_test3.xml
         contains these attributes in <SharedLibraries>, so
         omitting them caused a canonical XML mismatch.
         libcntrl.RoleFunction carries these fields since v1.5.
"""

import xml.etree.ElementTree as ET
import logging
from typing import List, Tuple, Optional

from .model import (
    State, Event, Transition, StateType, EventKind, RoleFunction,
    EventDeliveryType, EventSourceLayer,
    ActionStep, TransitionRelation, EventTrigger,
)
from .state_machine import StateMachine
from .global_defs import (
    GlobalDefinitions, SystemVariable, EventFlag,
    InterruptHandlerDef, InterruptAction,
    DevicePlaceholderDef, TimerBaseDef, TimerDerivedDef,
    EventQueueDef, CustomTypeDef, StructMemberDef,
)

logger = logging.getLogger("statable.xml_io")

try:
    from statable_gui.libcntrl.role_function_library import (
        RoleFunctionLibrary, RoleFunction as LibRoleFunction)
    from statable_gui.libcntrl.condition_library import (
        ConditionLibrary, ConditionTemplate)
    from statable_gui.libcntrl.literal_library import (
        LiteralLibrary, LiteralDefinition)
except ImportError:
    RoleFunctionLibrary = ConditionLibrary = LiteralLibrary = None
    LibRoleFunction = ConditionTemplate = LiteralDefinition = None


# ======================================================================
# Helpers: string / list normalization
# ======================================================================
def _normalize_actions(value) -> List[str]:
    """Always normalize action collections to List[str]."""
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    if isinstance(value, list):
        if value and all(isinstance(s, str) and len(s) == 1 for s in value):
            joined = "".join(value)
            logger.warning(
                f"Detected 1-char split actions, joining: {value} -> ['{joined}']"
            )
            return [joined]
        return [str(s) for s in value if str(s).strip()]
    logger.warning(f"Unexpected type for actions: {type(value)}. Converting to str.")
    return [str(value)]


def _normalize_str_list(value) -> List[str]:
    return _normalize_actions(value)


def _split_csv(text: str) -> List[str]:
    """Split a comma-separated attribute value into a clean list."""
    if not text:
        return []
    return [x.strip() for x in text.split(",") if x.strip()]


def _add_used_attrs(attrs: dict, rf) -> None:
    """[v3.8.1] Attach used_* attributes only when non-empty.

    This keeps canonical XML identical for project files created
    before v3.8: a role function with no symbol references produces
    no used_* attributes at all, instead of three empty ones.
    """
    for attr_name, field_name in (
        ("used_global_vars", "used_global_vars"),
        ("used_events", "used_events"),
        ("used_literals", "used_literals"),
    ):
        values = list(getattr(rf, field_name, []) or [])
        if values:
            attrs[attr_name] = ",".join(str(v) for v in values)


# ======================================================================
# v2.2 §12-5: Recursive relation serialization
# ======================================================================
def _relation_to_element(rel) -> ET.Element:
    """Serialize one TransitionRelation recursively."""
    elem = ET.Element(
        "Relation",
        kind=getattr(rel, "kind", "sequential") or "sequential",
        members=",".join(getattr(rel, "members", []) or []),
        shared_condition=getattr(rel, "shared_condition", "") or "",
        note=getattr(rel, "note", "") or "",
    )
    children = getattr(rel, "children", None) or []
    if children:
        children_elem = ET.SubElement(elem, "Children")
        for c in children:
            children_elem.append(_relation_to_element(c))
    return elem


def _relation_from_element(elem) -> TransitionRelation:
    """Deserialize one TransitionRelation recursively."""
    members_str = elem.get("members", "")
    members = [m.strip() for m in members_str.split(",") if m.strip()]
    rel = TransitionRelation(
        kind=elem.get("kind", "sequential"),
        members=members,
        shared_condition=elem.get("shared_condition", ""),
        note=elem.get("note", ""),
    )
    children_elem = elem.find("Children")
    if children_elem is not None:
        rel.children = [
            _relation_from_element(c)
            for c in children_elem.findall("Relation")
        ]
    return rel


# ======================================================================
# StateMachine -> XML
# ======================================================================
def _state_to_element(state: State) -> ET.Element:
    """Serialize one State (v2.2: entry/exit as child elements).

    [v3.7] `do` is a reserved field (not exposed in UI). It is
    still written to XML for backward compatibility.
    """
    attrs = {
        "name": state.name,
        "type": state.type.value,
        "parent": state.parent or "",
        # [Reserved] Not exposed in UI / not used by codegen.
        # Kept in XML output for backward compatibility.
        "do": state.do,
        "description": state.description,
    }
    elem = ET.Element("State", **attrs)

    entry_list = _normalize_str_list(getattr(state, 'entry', []))
    if entry_list:
        entry_elem = ET.SubElement(elem, "Entry")
        for a in entry_list:
            ET.SubElement(entry_elem, "Action", name=str(a))

    exit_list = _normalize_str_list(getattr(state, 'exit', []))
    if exit_list:
        exit_elem = ET.SubElement(elem, "Exit")
        for a in exit_list:
            ET.SubElement(exit_elem, "Action", name=str(a))

    return elem


def _state_from_element(elem: ET.Element) -> State:
    """Deserialize one State (supports old and new formats).

    [v3.7] `do` is a reserved field. It is still read from XML so
    that old projects round-trip without data loss, even though the
    GUI does not expose it.
    """
    entry_list: List[str] = []
    exit_list: List[str] = []

    entry_elem = elem.find("Entry")
    if entry_elem is not None:
        for action_elem in entry_elem.findall("Action"):
            n = action_elem.get("name", "")
            if n:
                entry_list.append(n)
    else:
        old_entry = elem.get("entry", "")
        if old_entry:
            entry_list = _normalize_str_list(old_entry)

    exit_elem = elem.find("Exit")
    if exit_elem is not None:
        for action_elem in exit_elem.findall("Action"):
            n = action_elem.get("name", "")
            if n:
                exit_list.append(n)
    else:
        old_exit = elem.get("exit", "")
        if old_exit:
            exit_list = _normalize_str_list(old_exit)

    return State(
        name=elem.get("name", ""),
        type=StateType(elem.get("type", "normal")),
        parent=elem.get("parent") or None,
        entry=entry_list,
        exit=exit_list,
        # [Reserved] preserved through XML I/O for backward compatibility.
        do=elem.get("do", ""),
        description=elem.get("description", ""),
    )


def _event_trigger_from_element(elem) -> Optional["EventTrigger"]:
    """[C-51 Step 3] Deserialize <Trigger> child element (or None)."""
    if elem is None:
        return None
    return EventTrigger.from_dict(dict(elem.attrib))


def state_machine_to_element(sm: StateMachine) -> ET.Element:
    """Convert StateMachine to XML Element."""
    logger.debug(
        f"state_machine_to_element: states={len(sm.states)}, "
        f"events={len(sm.events)}, roles={len(sm.role_functions)}, "
        f"transitions={len(sm.transitions)}"
    )

    root = ET.Element("StateMachine")
    if sm.initial_state:
        root.set("initial", sm.initial_state)

    root.set("layer_priority", str(getattr(sm, 'layer_priority', 5)))
    root.set("layer_description", getattr(sm, 'layer_description', ''))
    root.set("layer_name", getattr(sm, 'layer_name', ''))

    # States
    states_elem = ET.SubElement(root, "States")
    for state in sm.states.values():
        states_elem.append(_state_to_element(state))

    # Events
    events_elem = ET.SubElement(root, "Events")
    for event in sm.events.values():
        attrs = {
            "name": event.name,
            "id": str(event.id) if event.id is not None else "",
            "kind": event.kind.value,
            "params": ",".join(event.params),
            "priority": str(event.priority),
            "description": event.description,
            "delivery_type": event.delivery_type.value,
            "source_layer": event.source_layer.value,
            "data_type": event.data_type,
            "data_name": event.data_name,
            "title": event.title,
        }
        # [C-51 Step 2] Emit trigger only when non-empty, so
        # pre-C-51 projects round-trip with identical XML.
        _trigger = getattr(event, 'trigger', '') or ''
        if _trigger:
            attrs['trigger'] = _trigger
        event_elem = ET.SubElement(events_elem, "Event", **attrs)
        # [C-51 Step 3] Structured trigger detail (optional)
        _td = getattr(event, 'trigger_detail', None)
        if _td is not None:
            td_attrs = {k: str(v) for k, v in _td.to_dict().items()}
            ET.SubElement(event_elem, "Trigger", **td_attrs)

    # RoleFunctions
    # [v3.7] return_type / arg1_* / arg2_* are reserved fields
    # (not exposed in UI, not used by codegen). They are still
    # written to XML for backward compatibility.
    # [v3.8] used_global_vars / used_events / used_literals are
    # written as comma-separated attributes.
    # [v3.8.1] used_* attributes are only emitted when non-empty,
    # so pre-v3.8 files round-trip with identical canonical XML.
    roles_elem = ET.SubElement(root, "RoleFunctions")
    for rf in sm.role_functions.values():
        attrs = {
            "name": rf.name,
            "namespace": getattr(rf, 'namespace', ''),
            "description": rf.description,
            # [Reserved] kept for backward compatibility.
            "return_type": rf.return_type,
            "arg1_type": rf.arg1_type,
            "arg1_name": rf.arg1_name,
            "arg2_type": rf.arg2_type,
            "arg2_name": rf.arg2_name,
            "title": rf.title,
        }
        _add_used_attrs(attrs, rf)
        ET.SubElement(roles_elem, "RoleFunction", **attrs)

    # Transitions
    trans_elem = ET.SubElement(root, "Transitions")
    for t in sm.transitions:
        pre_actions = _normalize_actions(getattr(t, 'pre_actions', []))
        else_actions = _normalize_actions(getattr(t, 'else_actions', []))
        has_else = getattr(t, 'has_else', True)
        else_target = getattr(t, 'else_target', '')
        early_return = getattr(t, 'early_return', False)
        label = getattr(t, 'label', '')

        attrs = {
            "source": t.source,
            "event": t.event,
            "condition": t.condition,
            "action": t.action,
            "target": t.target,
            "transition_type": t.transition_type,
            "title": t.title,
            "has_else": "true" if has_else else "false",
            "else_target": else_target,
            "early_return": "true" if early_return else "false",
        }
        if label:
            attrs["label"] = label

        trans_child = ET.SubElement(trans_elem, "Transition", **attrs)
        for pre in pre_actions:
            ET.SubElement(trans_child, "PreAction", action=str(pre))
        for ea in else_actions:
            ET.SubElement(trans_child, "ElseAction", action=str(ea))

    # Cells (v2.2)
    cell_keys = sm.get_cell_keys()
    if cell_keys:
        cells_elem = ET.SubElement(root, "Cells")
        for (source, event) in cell_keys:
            cell_elem = ET.SubElement(
                cells_elem, "Cell",
                source=source, event=event,
            )

            actions = sm.get_actions_for_cell(source, event)
            if actions:
                actions_elem = ET.SubElement(cell_elem, "Actions")
                for a in actions:
                    ET.SubElement(actions_elem, "Action",
                                  role_function=a.role_function,
                                  trigger=a.trigger,
                                  title=a.title)

            relations = sm.get_relations_for_cell(source, event)
            if relations:
                rels_elem = ET.SubElement(cell_elem, "Relations")
                for r in relations:
                    rels_elem.append(_relation_to_element(r))

    return root


def state_machine_from_element(elem: ET.Element) -> StateMachine:
    """Build StateMachine from XML Element.

    [v3.7] Reserved role-function fields (return_type / arg1_* /
    arg2_*) are still read here so that old projects round-trip
    without data loss.

    [v3.8] used_global_vars / used_events / used_literals are read
    from comma-separated attributes; missing -> [].
    """
    logger.debug(f"state_machine_from_element: tag={elem.tag}")

    sm = StateMachine()
    initial_state_name = elem.get("initial")

    try:
        sm.layer_priority = int(elem.get("layer_priority", "5"))
    except ValueError:
        sm.layer_priority = 5
    sm.layer_description = elem.get("layer_description", "")
    sm.layer_name = elem.get("layer_name", "")

    # States
    states_elem = elem.find("States")
    if states_elem is None:
        logger.error("  <States> element not found!")
        return sm
    for state_elem in states_elem:
        try:
            sm.add_state(_state_from_element(state_elem))
        except Exception as e:
            logger.error(f"  Failed to load state: {e}", exc_info=True)

    # Events
    events_elem = elem.find("Events")
    if events_elem is not None:
        for event_elem in events_elem:
            params_str = event_elem.get("params", "")
            params = [p.strip() for p in params_str.split(",") if p.strip()] if params_str else []
            try:
                sm.add_event(Event(
                    name=event_elem.get("name", ""),
                    id=int(event_elem.get("id")) if event_elem.get("id") else None,
                    kind=EventKind(event_elem.get("kind", "signal")),
                    params=params,
                    priority=int(event_elem.get("priority", 0)),
                    description=event_elem.get("description", ""),
                    delivery_type=EventDeliveryType(event_elem.get("delivery_type", "direct")),
                    source_layer=EventSourceLayer(event_elem.get("source_layer", "driver")),
                    data_type=event_elem.get("data_type", ""),
                    data_name=event_elem.get("data_name", ""),
                    title=event_elem.get("title", ""),
                    # [C-51 Step 2] Free-text trigger; missing -> ""
                    trigger=event_elem.get("trigger", ""),
                    # [C-51 Step 3] Structured trigger detail
                    trigger_detail=_event_trigger_from_element(
                        event_elem.find("Trigger")),
                ))
            except Exception as e:
                logger.error(f"  Failed to load event: {e}", exc_info=True)

    # RoleFunctions
    # [v3.7] return_type / arg1_* / arg2_* are reserved fields.
    # [v3.8] used_global_vars / used_events / used_literals are read
    # from comma-separated attributes; missing -> [].
    roles_elem = elem.find("RoleFunctions")
    if roles_elem is not None:
        for rf_elem in roles_elem:
            raw_name = rf_elem.get("name", "")
            namespace = rf_elem.get("namespace", "")
            if not namespace and sm.layer_name:
                legacy_prefix = f"{sm.layer_name}_"
                if raw_name.startswith(legacy_prefix):
                    namespace = sm.layer_name
                    raw_name = raw_name[len(legacy_prefix):]
            try:
                sm.add_role_function(RoleFunction(
                    name=raw_name,
                    namespace=namespace,
                    description=rf_elem.get("description", ""),
                    # [Reserved] preserved for backward compatibility.
                    return_type=rf_elem.get("return_type", "int"),
                    arg1_type=rf_elem.get("arg1_type", "int"),
                    arg1_name=rf_elem.get("arg1_name", "arg1"),
                    arg2_type=rf_elem.get("arg2_type", "int"),
                    arg2_name=rf_elem.get("arg2_name", "arg2"),
                    title=rf_elem.get("title", ""),
                    # [v3.8] GUI symbol tracking.
                    used_global_vars=_split_csv(
                        rf_elem.get("used_global_vars", "")),
                    used_events=_split_csv(
                        rf_elem.get("used_events", "")),
                    used_literals=_split_csv(
                        rf_elem.get("used_literals", "")),
                ))
            except Exception as e:
                logger.error(f"  Failed to load role_function: {e}", exc_info=True)

    # Transitions
    trans_elem = elem.find("Transitions")
    if trans_elem is not None:
        for trans_elem_child in trans_elem:
            pre_actions_raw = [
                p.get("action", "")
                for p in trans_elem_child.findall("PreAction")
            ]
            else_actions_raw = [
                e.get("action", "")
                for e in trans_elem_child.findall("ElseAction")
            ]
            pre_actions = _normalize_actions(pre_actions_raw)
            else_actions = _normalize_actions(else_actions_raw)

            has_else = trans_elem_child.get("has_else", "true").lower() == "true"
            else_target = trans_elem_child.get("else_target", "")
            early_return = trans_elem_child.get("early_return", "false").lower() == "true"
            label = trans_elem_child.get("label", "")

            try:
                sm.add_transition(Transition(
                    source=trans_elem_child.get("source", ""),
                    event=trans_elem_child.get("event", ""),
                    condition=trans_elem_child.get("condition", ""),
                    action=trans_elem_child.get("action", ""),
                    target=trans_elem_child.get("target", ""),
                    transition_type=trans_elem_child.get("transition_type", "external"),
                    title=trans_elem_child.get("title", ""),
                    pre_actions=pre_actions,
                    has_else=has_else,
                    else_target=else_target,
                    else_actions=else_actions,
                    early_return=early_return,
                    label=label,
                ))
            except Exception as e:
                logger.error(f"  Failed to load transition: {e}", exc_info=True)

    # Cells (v2.2)
    cells_elem = elem.find("Cells")
    if cells_elem is not None:
        for cell_elem in cells_elem.findall("Cell"):
            source = cell_elem.get("source", "")
            event = cell_elem.get("event", "")

            actions_elem = cell_elem.find("Actions")
            if actions_elem is not None:
                actions = []
                for a_elem in actions_elem.findall("Action"):
                    actions.append(ActionStep(
                        role_function=a_elem.get("role_function", ""),
                        trigger=a_elem.get("trigger", "before_transitions"),
                        title=a_elem.get("title", ""),
                    ))
                sm.set_actions_for_cell(source, event, actions)

            rels_elem = cell_elem.find("Relations")
            if rels_elem is not None:
                relations = [
                    _relation_from_element(r_elem)
                    for r_elem in rels_elem.findall("Relation")
                ]
                sm.set_relations_for_cell(source, event, relations)

    if initial_state_name:
        sm.set_initial(initial_state_name)

    logger.debug(
        f"state_machine_from_element: loaded states={len(sm.states)}, "
        f"events={len(sm.events)}, roles={len(sm.role_functions)}, "
        f"transitions={len(sm.transitions)}, "
        f"cells={len(sm.get_cell_keys())}"
    )
    return sm


# ======================================================================
# GlobalDefinitions -> XML  (unchanged)
# ======================================================================
def _timer_to_element(parent: ET.Element, timer: TimerBaseDef, tag: str = "Timer"):
    elem = ET.SubElement(parent, tag)
    elem.set("variable_name", timer.variable_name)
    elem.set("unit", timer.unit)
    elem.set("data_type", timer.data_type)
    elem.set("title", timer.title)
    elem.set("interrupt_name", timer.interrupt_name)
    for derived in timer.derived:
        ET.SubElement(elem, "Derived", **{
            "period_name": derived.period_name,
            "multiplier": str(derived.multiplier),
            "variable_name": derived.variable_name,
            "data_type": derived.data_type,
            "title": derived.title,
        })
    return elem


def _timer_from_element(elem: ET.Element) -> TimerBaseDef:
    derived_list = []
    for d_elem in elem.findall("Derived"):
        try:
            mult = int(d_elem.get("multiplier", "1"))
        except ValueError:
            mult = 1
        derived_list.append(TimerDerivedDef(
            period_name=d_elem.get("period_name", ""),
            multiplier=mult,
            variable_name=d_elem.get("variable_name", ""),
            data_type=d_elem.get("data_type", "uint8_t"),
            title=d_elem.get("title", ""),
        ))
    return TimerBaseDef(
        variable_name=elem.get("variable_name", "g_system_tick"),
        unit=elem.get("unit", "1ms"),
        data_type=elem.get("data_type", "volatile uint32_t"),
        derived=derived_list,
        title=elem.get("title", ""),
        interrupt_name=elem.get("interrupt_name", ""),
    )


def global_defs_to_element(defs: GlobalDefinitions) -> ET.Element:
    root = ET.Element("GlobalDefinitions")

    if defs.custom_types:
        ct_elem = ET.SubElement(root, "CustomTypes")
        for ct in defs.custom_types:
            ct_child = ET.SubElement(ct_elem, "CustomType", **{
                "name": ct.name, "description": ct.description, "title": ct.title,
            })
            for member in ct.members:
                ET.SubElement(ct_child, "Member", **{
                    "name": member.name, "data_type": member.data_type,
                    "bit_width": str(member.bit_width),
                    "description": member.description, "title": member.title,
                    "array_size": str(member.array_size),
                })

    vars_elem = ET.SubElement(root, "SystemVariables")
    for var in defs.variables:
        ET.SubElement(vars_elem, "Variable", **{
            "name": var.name, "type": var.type, "unit": var.unit,
            "default_value": var.default_value, "group": var.group,
            "description": var.description, "title": var.title,
            "array_size": str(var.array_size),
        })

    flags_elem = ET.SubElement(root, "EventFlags")
    for flag in defs.flags:
        ET.SubElement(flags_elem, "Flag", **{
            "name": flag.name, "min_value": str(flag.min_value),
            "max_value": str(flag.max_value), "group": flag.group,
            "description": flag.description, "title": flag.title,
        })

    if defs.interrupts:
        intrs_elem = ET.SubElement(root, "Interrupts")
        for intr in defs.interrupts:
            intr_child = ET.SubElement(intrs_elem, "Interrupt", **{
                "name": intr.name, "description": intr.description,
                "event_names": ",".join(intr.event_names),
                "is_timer": "true" if intr.is_timer else "false",
                "title": intr.title,
            })
            for act in intr.actions:
                ET.SubElement(intr_child, "Action", **{
                    "condition": act.condition, "action": act.action,
                })
            for ref in getattr(intr, 'used_role_functions', []):
                ET.SubElement(intr_child, "UsedRoleFunction", ref=ref)
            for var in getattr(intr, 'used_variables', []):
                ET.SubElement(intr_child, "UsedVariable", name=var)

    if defs.placeholders:
        ph_elem = ET.SubElement(root, "DevicePlaceholders")
        for ph in defs.placeholders:
            ET.SubElement(ph_elem, "Placeholder", **{
                "name": ph.name, "description": ph.description, "title": ph.title,
            })

    timer_elem = ET.SubElement(root, "TimerBase")
    _timer_to_element(timer_elem, defs.timer_base, tag="Timer")

    if defs.extra_timers:
        extras_elem = ET.SubElement(root, "ExtraTimers")
        for timer in defs.extra_timers:
            _timer_to_element(extras_elem, timer, tag="Timer")

    if defs.event_queues:
        queues_elem = ET.SubElement(root, "EventQueues")
        for q in defs.event_queues:
            ET.SubElement(queues_elem, "Queue", **{
                "name": q.name, "size": str(q.size),
                "element_type": q.element_type,
                "event_ids": ",".join(q.event_ids),
                "priority_enabled": "true" if q.priority_enabled else "false",
                "interrupt_safe": "true" if q.interrupt_safe else "false",
                "rtos_enabled": "true" if q.rtos_enabled else "false",
                "description": q.description, "title": q.title,
            })

    return root


def global_defs_from_element(elem: ET.Element) -> GlobalDefinitions:
    defs = GlobalDefinitions()

    ct_elem = elem.find("CustomTypes")
    if ct_elem is not None:
        for ct in ct_elem:
            members = []
            for m in ct.findall("Member"):
                try:
                    bw = int(m.get("bit_width", "0"))
                except ValueError:
                    bw = 0
                try:
                    arr = int(m.get("array_size", "0"))
                except ValueError:
                    arr = 0
                members.append(StructMemberDef(
                    name=m.get("name", ""), data_type=m.get("data_type", ""),
                    bit_width=bw, description=m.get("description", ""),
                    title=m.get("title", ""), array_size=arr,
                ))
            defs.custom_types.append(CustomTypeDef(
                name=ct.get("name", ""), description=ct.get("description", ""),
                members=members, title=ct.get("title", ""),
            ))

    vars_elem = elem.find("SystemVariables")
    if vars_elem is not None:
        for var_elem in vars_elem:
            try:
                arr = int(var_elem.get("array_size", "0"))
            except ValueError:
                arr = 0
            defs.variables.append(SystemVariable(
                name=var_elem.get("name", ""), type=var_elem.get("type", ""),
                unit=var_elem.get("unit", ""),
                default_value=var_elem.get("default_value", ""),
                group=var_elem.get("group", ""),
                description=var_elem.get("description", ""),
                title=var_elem.get("title", ""), array_size=arr,
            ))

    flags_elem = elem.find("EventFlags")
    if flags_elem is not None:
        for flag_elem in flags_elem:
            try:
                min_val = int(flag_elem.get("min_value", "0"))
                max_val = int(flag_elem.get("max_value", "0"))
            except ValueError:
                min_val, max_val = 0, 0
            defs.flags.append(EventFlag(
                name=flag_elem.get("name", ""), min_value=min_val,
                max_value=max_val, group=flag_elem.get("group", ""),
                description=flag_elem.get("description", ""),
                title=flag_elem.get("title", ""),
            ))

    intrs_elem = elem.find("Interrupts")
    if intrs_elem is not None:
        for intr_elem in intrs_elem:
            actions = []
            for act_elem in intr_elem.findall("Action"):
                actions.append(InterruptAction(
                    condition=act_elem.get("condition", ""),
                    action=act_elem.get("action", ""),
                ))
            used_rfs = [r.get("ref", "")
                        for r in intr_elem.findall("UsedRoleFunction")
                        if r.get("ref")]
            used_vars = [v.get("name", "")
                         for v in intr_elem.findall("UsedVariable")
                         if v.get("name")]
            es = intr_elem.get("event_names", "")
            defs.interrupts.append(InterruptHandlerDef(
                name=intr_elem.get("name", ""),
                description=intr_elem.get("description", ""),
                event_names=[e.strip() for e in es.split(",") if e.strip()] if es else [],
                is_timer=intr_elem.get("is_timer", "false").lower() == "true",
                actions=actions,
                title=intr_elem.get("title", ""),
                used_role_functions=used_rfs,
                used_variables=used_vars,
            ))

    ph_elem = elem.find("DevicePlaceholders")
    if ph_elem is not None:
        for ph in ph_elem:
            defs.placeholders.append(DevicePlaceholderDef(
                name=ph.get("name", ""), description=ph.get("description", ""),
                title=ph.get("title", ""),
            ))

    timer_elem = elem.find("TimerBase")
    if timer_elem is not None:
        inner = timer_elem.find("Timer")
        if inner is not None:
            defs.timer_base = _timer_from_element(inner)

    extras_elem = elem.find("ExtraTimers")
    if extras_elem is not None:
        for inner in extras_elem.findall("Timer"):
            defs.extra_timers.append(_timer_from_element(inner))

    queues_elem = elem.find("EventQueues")
    if queues_elem is not None:
        for q_elem in queues_elem:
            es = q_elem.get("event_ids", "")
            try:
                size = int(q_elem.get("size", "8"))
            except ValueError:
                size = 8
            defs.event_queues.append(EventQueueDef(
                name=q_elem.get("name", ""), size=size,
                element_type=q_elem.get("element_type", "uint8_t"),
                event_ids=[e.strip() for e in es.split(",") if e.strip()] if es else [],
                priority_enabled=q_elem.get("priority_enabled", "false").lower() == "true",
                interrupt_safe=q_elem.get("interrupt_safe", "true").lower() == "true",
                rtos_enabled=q_elem.get("rtos_enabled", "false").lower() == "true",
                description=q_elem.get("description", ""),
                title=q_elem.get("title", ""),
            ))

    defs.add_timer_variables()
    return defs


# ======================================================================
# Shared library -> XML
# ======================================================================
def role_function_library_to_element(lib) -> Optional[ET.Element]:
    """Serialize the shared role function library.

    [v3.8]
      libcntrl.RoleFunction has used_global_vars / used_events /
      used_literals. They are written as comma-separated attributes.

    [v3.8.1]
      used_* attributes are only emitted when non-empty, so the
      canonical XML of pre-v3.8 projects is unchanged after a
      round-trip through the GUI.

    [v3.8.2]
      Also emit the reserved signature fields
      (return_type / arg1_* / arg2_*). The test fixture
      tests/data/v22_features_test3.xml contains these attributes
      in the <SharedLibraries> section, so omitting them caused a
      canonical XML mismatch in test_v2_2_p12_9.py.
      libcntrl.RoleFunction carries these fields since v1.5.
    """
    if lib is None:
        return None
    root = ET.Element("RoleFunctionLibrary")
    for rf in lib.list_all():
        attrs = {
            "name": rf.name,
            "namespace": getattr(rf, 'namespace', ''),
            "description": getattr(rf, 'description', ''),
            # [v3.8.2] Reserved signature fields: preserved for
            # canonical XML equality with pre-v3.8 fixtures.
            "return_type": getattr(rf, 'return_type', ''),
            "arg1_type": getattr(rf, 'arg1_type', ''),
            "arg1_name": getattr(rf, 'arg1_name', ''),
            "arg2_type": getattr(rf, 'arg2_type', ''),
            "arg2_name": getattr(rf, 'arg2_name', ''),
            "title": getattr(rf, 'title', ''),
        }
        _add_used_attrs(attrs, rf)
        ET.SubElement(root, "RoleFunction", **attrs)
    return root


def role_function_library_from_element(elem: Optional[ET.Element]):
    """Deserialize the shared role function library.

    [v3.8]
      used_global_vars / used_events / used_literals are read from
      comma-separated attributes; missing -> [].

    [v3.8.2]
      Reserved signature fields (return_type / arg1_* / arg2_*) are
      read back so that the values round-trip unchanged.
    """
    if elem is None:
        return RoleFunctionLibrary() if RoleFunctionLibrary else None
    lib = RoleFunctionLibrary()
    for rf_elem in elem.findall("RoleFunction"):
        name = rf_elem.get("name", "")
        namespace = rf_elem.get("namespace", "")
        try:
            try:
                rf = LibRoleFunction(
                    name=name, namespace=namespace,
                    title=rf_elem.get("title", ""),
                    description=rf_elem.get("description", ""),
                )
            except TypeError:
                # Older libcntrl.RoleFunction without namespace kwarg
                rf = LibRoleFunction(
                    name=name,
                    title=rf_elem.get("title", ""),
                    description=rf_elem.get("description", ""),
                )
                if hasattr(rf, 'namespace'):
                    rf.namespace = namespace

            # [v3.8.2] Reserved signature fields
            for attr in ('return_type', 'arg1_type', 'arg1_name',
                         'arg2_type', 'arg2_name'):
                if hasattr(rf, attr):
                    setattr(rf, attr, rf_elem.get(attr, ''))

            # [v3.8] symbol references
            for attr in ('used_global_vars', 'used_events',
                         'used_literals'):
                if hasattr(rf, attr):
                    setattr(rf, attr,
                            _split_csv(rf_elem.get(attr, "")))
            lib.add(rf)
        except Exception as e:
            logger.error(f"load role function failed: {e}", exc_info=True)
    return lib


def condition_library_to_element(lib) -> Optional[ET.Element]:
    if lib is None:
        return None
    root = ET.Element("ConditionLibrary")
    for ct in lib.list_all():
        ET.SubElement(root, "Condition", **{
            "name": ct.name,
            "condition": getattr(ct, 'condition', ''),
        })
    return root


def condition_library_from_element(elem: Optional[ET.Element]):
    if elem is None:
        return ConditionLibrary() if ConditionLibrary else None
    lib = ConditionLibrary()
    for ct_elem in elem.findall("Condition"):
        try:
            ct = ConditionTemplate(
                name=ct_elem.get("name", ""),
                condition=ct_elem.get("condition", ""),
            )
            lib.add(ct)
        except Exception as e:
            logger.error(f"condition load failed: {e}", exc_info=True)
    return lib


def literal_library_to_element(lib) -> Optional[ET.Element]:
    if lib is None:
        return None
    root = ET.Element("LiteralLibrary")
    for lit in lib.list_all():
        ET.SubElement(root, "Literal", **{
            "name": lit.name,
            "value": getattr(lit, 'value', ''),
            "literal_type": getattr(lit, 'literal_type', ''),
            "description": getattr(lit, 'description', ''),
        })
    return root


def literal_library_from_element(elem: Optional[ET.Element]):
    if elem is None:
        return LiteralLibrary() if LiteralLibrary else None
    lib = LiteralLibrary()
    for lit_elem in elem.findall("Literal"):
        try:
            lit = LiteralDefinition(
                name=lit_elem.get("name", ""),
                value=lit_elem.get("value", ""),
                literal_type=lit_elem.get("literal_type", "int"),
                description=lit_elem.get("description", ""),
            )
            lib.add(lit)
        except Exception as e:
            logger.error(f"literal load failed: {e}", exc_info=True)
    return lib


# ======================================================================
# Project settings -> XML  (unchanged)
# ======================================================================
def _project_settings_to_element(settings: Optional[dict]) -> ET.Element:
    elem = ET.Element("ProjectSettings")
    if settings:
        cg = ET.SubElement(elem, "CodeGeneration")
        cg.set("project_name", settings.get('project_name', 'MyProject'))
        cg.set("table_type", settings.get('table_type', 'array'))
        cg.set("generation_style", settings.get('generation_style', 'table_driven'))
        cg.set("os_type", settings.get('os_type', 'non_rtos'))
        cg.set("folder_structure", settings.get('folder_structure', 'by_type'))
        cg.set("include_dir_name", settings.get('include_dir_name', 'include'))
        cg.set("source_dir_name", settings.get('source_dir_name', 'src'))
        cg.set("common_dir_name", settings.get('common_dir_name', 'common'))
        cg.set("project_dir_name", settings.get('project_dir_name', 'project'))
        cg.set("generate_super_include",
               "true" if settings.get('generate_super_include', True) else "false")
        cg.set("super_include_file",
               settings.get('super_include_file', 'statable_all.h'))
        cg.set("max_consecutive_pending_events",
               str(settings.get('max_consecutive_pending_events', 16)))
        ext_includes = settings.get('external_includes', [])
        if ext_includes:
            ext_elem = ET.SubElement(cg, "ExternalIncludes")
            for inc in ext_includes:
                ET.SubElement(ext_elem, "Include", name=inc)
        cg.set("external_includes_in_super",
               "true" if settings.get('external_includes_in_super', True) else "false")
        cg.set("external_includes_in_role",
               "true" if settings.get('external_includes_in_role', True) else "false")
        cg.set("external_includes_in_transitions",
               "true" if settings.get('external_includes_in_transitions', False) else "false")
        cg.set("external_includes_in_common",
               "true" if settings.get('external_includes_in_common', False) else "false")
    return elem


def _project_settings_from_element(elem: Optional[ET.Element]) -> dict:
    settings = {}
    if elem is None:
        return settings
    cg = elem.find("CodeGeneration")
    if cg is None:
        return settings
    settings['project_name'] = cg.get("project_name", "MyProject")
    settings['table_type'] = cg.get("table_type", "array")
    settings['generation_style'] = cg.get("generation_style", "table_driven")
    settings['os_type'] = cg.get("os_type", "non_rtos")
    settings['folder_structure'] = cg.get("folder_structure", "by_type")
    settings['include_dir_name'] = cg.get("include_dir_name", "include")
    settings['source_dir_name'] = cg.get("source_dir_name", "src")
    settings['common_dir_name'] = cg.get("common_dir_name", "common")
    settings['project_dir_name'] = cg.get("project_dir_name", "project")
    settings['generate_super_include'] = cg.get("generate_super_include", "true").lower() == "true"
    settings['super_include_file'] = cg.get("super_include_file", "statable_all.h")
    try:
        settings['max_consecutive_pending_events'] = int(
            cg.get("max_consecutive_pending_events", "16"))
    except ValueError:
        settings['max_consecutive_pending_events'] = 16
    ext_elem = cg.find("ExternalIncludes")
    if ext_elem is not None:
        settings['external_includes'] = [
            inc.get("name", "") for inc in ext_elem.findall("Include")]
    else:
        settings['external_includes'] = []
    settings['external_includes_in_super'] = cg.get("external_includes_in_super", "true").lower() == "true"
    settings['external_includes_in_role'] = cg.get("external_includes_in_role", "true").lower() == "true"
    settings['external_includes_in_transitions'] = cg.get("external_includes_in_transitions", "false").lower() == "true"
    settings['external_includes_in_common'] = cg.get("external_includes_in_common", "false").lower() == "true"
    return settings


def project_to_xml(
        tabs: List[Tuple[str, StateMachine]],
        global_defs: GlobalDefinitions,
        filepath: str,
        role_function_library=None,
        condition_library=None,
        literal_library=None,
        project_settings: Optional[dict] = None,
) -> None:
    root = ET.Element("Project")

    project_name = "MyProject"
    if project_settings:
        project_name = project_settings.get('project_name', 'MyProject')
        root.append(_project_settings_to_element(project_settings))
    root.set("name", project_name)

    root.append(global_defs_to_element(global_defs))

    if (role_function_library is not None
            or condition_library is not None
            or literal_library is not None):
        libs_elem = ET.SubElement(root, "SharedLibraries")
        if role_function_library is not None:
            libs_elem.append(role_function_library_to_element(role_function_library))
        if condition_library is not None:
            libs_elem.append(condition_library_to_element(condition_library))
        if literal_library is not None:
            libs_elem.append(literal_library_to_element(literal_library))

    for name, sm in tabs:
        tab_elem = ET.SubElement(root, "Tab")
        tab_elem.set("name", name)
        tab_elem.append(state_machine_to_element(sm))

    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")
    tree.write(filepath, encoding="utf-8", xml_declaration=True)


def project_from_xml(filepath: str):
    tree = ET.parse(filepath)
    root = tree.getroot()

    project_settings = _project_settings_from_element(root.find("ProjectSettings"))
    if 'project_name' not in project_settings and root.get("name"):
        project_settings['project_name'] = root.get("name")

    gd_elem = root.find("GlobalDefinitions")
    global_defs = (global_defs_from_element(gd_elem)
                   if gd_elem is not None else GlobalDefinitions())

    role_function_library = (RoleFunctionLibrary() if RoleFunctionLibrary else None)
    condition_library = (ConditionLibrary() if ConditionLibrary else None)
    literal_library = (LiteralLibrary() if LiteralLibrary else None)

    libs_elem = root.find("SharedLibraries")
    if libs_elem is not None:
        role_function_library = role_function_library_from_element(
            libs_elem.find("RoleFunctionLibrary"))
        condition_library = condition_library_from_element(
            libs_elem.find("ConditionLibrary"))
        literal_library = literal_library_from_element(
            libs_elem.find("LiteralLibrary"))

    tabs = []
    for tab_elem in root.findall("Tab"):
        name = tab_elem.get("name", "Untitled")
        sm_elem = tab_elem.find("StateMachine")
        sm = (state_machine_from_element(sm_elem)
              if sm_elem is not None else StateMachine())
        tabs.append((name, sm))

    return (tabs, global_defs, role_function_library,
            condition_library, literal_library, project_settings)