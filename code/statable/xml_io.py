import xml.etree.ElementTree as ET
from typing import Optional, List, Tuple

from .model import State, Event, Transition, StateType, EventKind, RoleFunction
from .state_machine import StateMachine


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
        }
        ET.SubElement(trans_elem, "Transition", **attrs)

    return root


def state_machine_from_element(elem: ET.Element) -> StateMachine:
    """XML Element から StateMachine を構築する"""
    sm = StateMachine()

    # ★ 初期状態は States 追加後に設定するため、ここでは一旦読み飛ばす
    initial_state_name = elem.get("initial")

    # States を先に追加
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
        )
        sm.add_transition(trans)

    # ★ 初期状態を最後に設定
    if initial_state_name:
        sm.set_initial(initial_state_name)

    return sm


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
# プロジェクト全体（複数タブ）の保存/読み込み
# ----------------------------------------------------------------------
def project_to_xml(tabs: List[Tuple[str, StateMachine]], filepath: str) -> None:
    """プロジェクト全体（タブ名と各StateMachine）をXMLファイルに保存する"""
    root = ET.Element("Project")
    for name, sm in tabs:
        tab_elem = ET.SubElement(root, "Tab")
        tab_elem.set("name", name)
        sm_elem = state_machine_to_element(sm)
        tab_elem.append(sm_elem)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")
    tree.write(filepath, encoding="utf-8", xml_declaration=True)


def project_from_xml(filepath: str) -> List[Tuple[str, StateMachine]]:
    """プロジェクトXMLファイルからタブ一覧を読み込む"""
    tree = ET.parse(filepath)
    root = tree.getroot()
    tabs = []
    for tab_elem in root.findall("Tab"):
        name = tab_elem.get("name", "Untitled")
        sm_elem = tab_elem.find("StateMachine")
        if sm_elem is not None:
            sm = state_machine_from_element(sm_elem)
        else:
            sm = StateMachine()  # 空のタブ
        tabs.append((name, sm))
    return tabs