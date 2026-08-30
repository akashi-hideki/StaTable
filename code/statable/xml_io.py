import xml.etree.ElementTree as ET
from typing import List, Tuple

from .model import (
    State, Event, Transition, StateType, EventKind, RoleFunction,
    EventDeliveryType, EventSourceLayer,
)
from .state_machine import StateMachine
from .global_defs import (
    GlobalDefinitions, SystemVariable, EventFlag,
    InterruptHandlerDef, InterruptAction,
    DevicePlaceholderDef, TimerBaseDef, TimerDerivedDef,
    EventQueueDef, CustomTypeDef, StructMemberDef,
)


def state_machine_to_element(sm: StateMachine) -> ET.Element:
    """Convert StateMachine to XML Element"""
    root = ET.Element("StateMachine")
    if sm.initial_state:
        root.set("initial", sm.initial_state)

    states_elem = ET.SubElement(root, "States")
    for state in sm.states.values():
        attrs = {
            "name": state.name,
            "type": state.type.value,
            "parent": state.parent or "",
            "entry": state.entry,
            "exit": state.exit,
            "do": state.do,
            "description": state.description,
        }
        ET.SubElement(states_elem, "State", **attrs)

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
        ET.SubElement(events_elem, "Event", **attrs)

    roles_elem = ET.SubElement(root, "RoleFunctions")
    for rf in sm.role_functions.values():
        attrs = {
            "name": rf.name,
            "description": rf.description,
            "return_type": rf.return_type,
            "arg1_type": rf.arg1_type,
            "arg1_name": rf.arg1_name,
            "arg2_type": rf.arg2_type,
            "arg2_name": rf.arg2_name,
            "title": rf.title,
        }
        ET.SubElement(roles_elem, "RoleFunction", **attrs)

    trans_elem = ET.SubElement(root, "Transitions")
    for t in sm.transitions:
        attrs = {
            "source": t.source,
            "event": t.event,
            "condition": t.condition,
            "action": t.action,
            "target": t.target,
            "transition_type": t.transition_type,
            "title": t.title,
        }
        ET.SubElement(trans_elem, "Transition", **attrs)

    return root


def state_machine_from_element(elem: ET.Element) -> StateMachine:
    """Build StateMachine from XML Element"""
    sm = StateMachine()
    initial_state_name = elem.get("initial")

    for state_elem in elem.find("States"):
        sm.add_state(State(
            name=state_elem.get("name", ""),
            type=StateType(state_elem.get("type", "normal")),
            parent=state_elem.get("parent") or None,
            entry=state_elem.get("entry", ""),
            exit=state_elem.get("exit", ""),
            do=state_elem.get("do", ""),
            description=state_elem.get("description", ""),
        ))

    for event_elem in elem.find("Events"):
        params_str = event_elem.get("params", "")
        params = [p.strip() for p in params_str.split(",") if p.strip()] if params_str else []
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
        ))

    for rf_elem in elem.find("RoleFunctions"):
        sm.add_role_function(RoleFunction(
            name=rf_elem.get("name", ""),
            description=rf_elem.get("description", ""),
            return_type=rf_elem.get("return_type", "int"),
            arg1_type=rf_elem.get("arg1_type", "int"),
            arg1_name=rf_elem.get("arg1_name", "arg1"),
            arg2_type=rf_elem.get("arg2_type", "int"),
            arg2_name=rf_elem.get("arg2_name", "arg2"),
            title=rf_elem.get("title", ""),
        ))

    for trans_elem in elem.find("Transitions"):
        sm.add_transition(Transition(
            source=trans_elem.get("source", ""),
            event=trans_elem.get("event", ""),
            condition=trans_elem.get("condition", ""),
            action=trans_elem.get("action", ""),
            target=trans_elem.get("target", ""),
            transition_type=trans_elem.get("transition_type", "external"),
            title=trans_elem.get("title", ""),
        ))

    if initial_state_name:
        sm.set_initial(initial_state_name)

    return sm


def _timer_to_element(parent: ET.Element, timer: TimerBaseDef, tag: str = "Timer"):
    """Convert TimerBaseDef to XML Element"""
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
    """Build TimerBaseDef from XML Element"""
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
    """Convert GlobalDefinitions to XML Element"""
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
    """Build GlobalDefinitions from XML Element"""
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
                unit=var_elem.get("unit", ""), default_value=var_elem.get("default_value", ""),
                group=var_elem.get("group", ""), description=var_elem.get("description", ""),
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
                name=flag_elem.get("name", ""), min_value=min_val, max_value=max_val,
                group=flag_elem.get("group", ""), description=flag_elem.get("description", ""),
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
            es = intr_elem.get("event_names", "")
            defs.interrupts.append(InterruptHandlerDef(
                name=intr_elem.get("name", ""), description=intr_elem.get("description", ""),
                event_names=[e.strip() for e in es.split(",") if e.strip()] if es else [],
                is_timer=intr_elem.get("is_timer", "false").lower() == "true",
                actions=actions, title=intr_elem.get("title", ""),
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
                description=q_elem.get("description", ""), title=q_elem.get("title", ""),
            ))

    defs.add_timer_variables()

    return defs


def state_machine_to_xml(sm: StateMachine, filepath: str) -> None:
    """Save StateMachine to XML file"""
    root = state_machine_to_element(sm)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")
    tree.write(filepath, encoding="utf-8", xml_declaration=True)


def state_machine_from_xml(filepath: str) -> StateMachine:
    """Load StateMachine from XML file"""
    tree = ET.parse(filepath)
    root = tree.getroot()
    return state_machine_from_element(root)


def project_to_xml(tabs: List[Tuple[str, StateMachine]], global_defs: GlobalDefinitions, filepath: str) -> None:
    """Save project to XML file"""
    root = ET.Element("Project")
    root.append(global_defs_to_element(global_defs))

    for name, sm in tabs:
        tab_elem = ET.SubElement(root, "Tab")
        tab_elem.set("name", name)
        tab_elem.append(state_machine_to_element(sm))

    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")
    tree.write(filepath, encoding="utf-8", xml_declaration=True)


def project_from_xml(filepath: str) -> Tuple[List[Tuple[str, StateMachine]], GlobalDefinitions]:
    """Load project from XML file"""
    tree = ET.parse(filepath)
    root = tree.getroot()

    gd_elem = root.find("GlobalDefinitions")
    global_defs = global_defs_from_element(gd_elem) if gd_elem is not None else GlobalDefinitions()

    tabs = []
    for tab_elem in root.findall("Tab"):
        name = tab_elem.get("name", "Untitled")
        sm_elem = tab_elem.find("StateMachine")
        sm = state_machine_from_element(sm_elem) if sm_elem is not None else StateMachine()
        tabs.append((name, sm))

    return tabs, global_defs