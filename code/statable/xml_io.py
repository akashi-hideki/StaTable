import xml.etree.ElementTree as ET
from typing import List, Tuple

from .model import State, Event, Transition, StateType, EventKind, RoleFunction
from .state_machine import StateMachine
from .global_defs import GlobalDefinitions, SystemVariable, EventFlag


# ----------------------------------------------------------------------
# StateMachine <-> Element 変換
# ----------------------------------------------------------------------
def state_machine_to_element(sm: StateMachine) -> ET.Element:
    """StateMachine を XML Element に変換する"""
    root = ET.Element("StateMachine")
    if sm.initial_state:
        root.set("initial", sm.initial_state)

    # States
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
        }
        ET.SubElement(events_elem, "Event", **attrs)

    # RoleFunctions
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
        }
        ET.SubElement(roles_elem, "RoleFunction", **attrs)

    # Transitions
    trans_elem = ET.SubElement(root, "Transitions")
    for t in sm.transitions:
        attrs = {
            "source": t.source,
            "event": t.event,
            "guard": t.guard,
            "action": t.action,
            "target": t.target,
            "transition_type": t.transition_type,
            "title": t.title,   # ★ titleを保存
        }
        ET.SubElement(trans_elem, "Transition", **attrs)

    return root


def state_machine_from_element(elem: ET.Element) -> StateMachine:
    """XML Element から StateMachine を構築する"""
    sm = StateMachine()

    # ★ 初期状態は States 追加後に設定するため、ここでは一旦読み飛ばす
    initial_state_name = elem.get("initial")

    # States
    for state_elem in elem.find("States"):
        state = State(
            name=state_elem.get("name", ""),
            type=StateType(state_elem.get("type", "normal")),
            parent=state_elem.get("parent") or None,
            entry=state_elem.get("entry", ""),
            exit=state_elem.get("exit", ""),
            do=state_elem.get("do", ""),
            description=state_elem.get("description", ""),
        )
        sm.add_state(state)

    # Events
    for event_elem in elem.find("Events"):
        params_str = event_elem.get("params", "")
        params = [p.strip() for p in params_str.split(",") if p.strip()] if params_str else []
        event = Event(
            name=event_elem.get("name", ""),
            id=int(event_elem.get("id")) if event_elem.get("id") else None,
            kind=EventKind(event_elem.get("kind", "signal")),
            params=params,
            priority=int(event_elem.get("priority", 0)),
            description=event_elem.get("description", ""),
        )
        sm.add_event(event)

    # RoleFunctions
    for rf_elem in elem.find("RoleFunctions"):
        rf = RoleFunction(
            name=rf_elem.get("name", ""),
            description=rf_elem.get("description", ""),
            return_type=rf_elem.get("return_type", "int"),
            arg1_type=rf_elem.get("arg1_type", "int"),
            arg1_name=rf_elem.get("arg1_name", "arg1"),
            arg2_type=rf_elem.get("arg2_type", "int"),
            arg2_name=rf_elem.get("arg2_name", "arg2"),
        )
        sm.add_role_function(rf)

    # Transitions
    for trans_elem in elem.find("Transitions"):
        trans = Transition(
            source=trans_elem.get("source", ""),
            event=trans_elem.get("event", ""),
            guard=trans_elem.get("guard", ""),
            action=trans_elem.get("action", ""),
            target=trans_elem.get("target", ""),
            transition_type=trans_elem.get("transition_type", "external"),
            title=trans_elem.get("title", ""),   # ★ titleを復元
        )
        sm.add_transition(trans)

    # 初期状態はState追加後に設定
    if initial_state_name:
        sm.set_initial(initial_state_name)

    return sm


# ----------------------------------------------------------------------
# GlobalDefinitions <-> Element 変換
# ----------------------------------------------------------------------
def global_defs_to_element(defs: GlobalDefinitions) -> ET.Element:
    root = ET.Element("GlobalDefinitions")

    # SystemVariables
    vars_elem = ET.SubElement(root, "SystemVariables")
    for var in defs.variables:
        attrs = {
            "name": var.name,
            "type": var.type,
            "unit": var.unit,
            "default_value": var.default_value,
            "group": var.group,
            "description": var.description,
        }
        ET.SubElement(vars_elem, "Variable", **attrs)

    # EventFlags
    flags_elem = ET.SubElement(root, "EventFlags")
    for flag in defs.flags:
        attrs = {
            "name": flag.name,
            "min_value": str(flag.min_value),
            "max_value": str(flag.max_value),
            "group": flag.group,
            "description": flag.description,
        }
        ET.SubElement(flags_elem, "Flag", **attrs)

    return root


def global_defs_from_element(elem: ET.Element) -> GlobalDefinitions:
    defs = GlobalDefinitions()

    # SystemVariables
    vars_elem = elem.find("SystemVariables")
    if vars_elem is not None:
        for var_elem in vars_elem:
            var = SystemVariable(
                name=var_elem.get("name", ""),
                type=var_elem.get("type", ""),
                unit=var_elem.get("unit", ""),
                default_value=var_elem.get("default_value", ""),
                group=var_elem.get("group", ""),
                description=var_elem.get("description", ""),
            )
            defs.variables.append(var)

    # EventFlags
    flags_elem = elem.find("EventFlags")
    if flags_elem is not None:
        for flag_elem in flags_elem:
            try:
                min_val = int(flag_elem.get("min_value", "0"))
                max_val = int(flag_elem.get("max_value", "0"))
            except ValueError:
                min_val, max_val = 0, 0
            flag = EventFlag(
                name=flag_elem.get("name", ""),
                min_value=min_val,
                max_value=max_val,
                group=flag_elem.get("group", ""),
                description=flag_elem.get("description", ""),
            )
            defs.flags.append(flag)

    return defs


# ----------------------------------------------------------------------
# 単一 StateMachine のファイル保存/読み込み（互換用）
# ----------------------------------------------------------------------
def state_machine_to_xml(sm: StateMachine, filepath: str) -> None:
    """StateMachine を XML ファイルに保存する"""
    root = state_machine_to_element(sm)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")
    tree.write(filepath, encoding="utf-8", xml_declaration=True)


def state_machine_from_xml(filepath: str) -> StateMachine:
    """XML ファイルから StateMachine を読み込む"""
    tree = ET.parse(filepath)
    root = tree.getroot()
    return state_machine_from_element(root)


# ----------------------------------------------------------------------
# プロジェクト全体（複数タブ＋グローバル定義）の保存/読み込み
# ----------------------------------------------------------------------
def project_to_xml(
    tabs: List[Tuple[str, StateMachine]],
    global_defs: GlobalDefinitions,
    filepath: str
) -> None:
    """プロジェクト全体（タブ＋グローバル定義）をXMLファイルに保存する"""
    root = ET.Element("Project")

    # グローバル定義
    root.append(global_defs_to_element(global_defs))

    # 各タブ
    for name, sm in tabs:
        tab_elem = ET.SubElement(root, "Tab")
        tab_elem.set("name", name)
        sm_elem = state_machine_to_element(sm)
        tab_elem.append(sm_elem)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")
    tree.write(filepath, encoding="utf-8", xml_declaration=True)


def project_from_xml(
    filepath: str
) -> Tuple[List[Tuple[str, StateMachine]], GlobalDefinitions]:
    """プロジェクトXMLファイルからタブ一覧とグローバル定義を読み込む"""
    tree = ET.parse(filepath)
    root = tree.getroot()

    # グローバル定義
    gd_elem = root.find("GlobalDefinitions")
    if gd_elem is not None:
        global_defs = global_defs_from_element(gd_elem)
    else:
        # 後方互換：グローバル定義がない旧形式
        global_defs = GlobalDefinitions()

    # 各タブ
    tabs = []
    for tab_elem in root.findall("Tab"):
        name = tab_elem.get("name", "Untitled")
        sm_elem = tab_elem.find("StateMachine")
        if sm_elem is not None:
            sm = state_machine_from_element(sm_elem)
        else:
            sm = StateMachine()
        tabs.append((name, sm))

    return tabs, global_defs