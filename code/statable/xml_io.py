# statable/xml_io.py
"""
XML入出力（プロジェクト設定・レイヤ優先度・層名対応版）
- プロジェクト保存/読込で共有ライブラリ（ロール関数・遷移条件・リテラル）を保存
- Transitionのpre_actions/else_actions/has_else/else_targetも保存
- 文字列→リスト正規化、1文字分解の自動結合
- libcntrl.RoleFunction の引数互換対応
- レイヤ優先度・説明・層名（layer_name）・プロジェクト名の保存/復元
- 各段階でデバッグログを出力
"""

import xml.etree.ElementTree as ET
import logging
from typing import List, Tuple, Optional

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

logger = logging.getLogger("statable.xml_io")

# 共有ライブラリ（インポート失敗時はNone）
try:
    from libcntrl.role_function_library import RoleFunctionLibrary, RoleFunction as LibRoleFunction
    from libcntrl.condition_library import ConditionLibrary, ConditionTemplate
    from libcntrl.literal_library import LiteralLibrary, LiteralDefinition
except ImportError:
    try:
        from statable_gui.libcntrl.role_function_library import RoleFunctionLibrary, RoleFunction as LibRoleFunction
        from statable_gui.libcntrl.condition_library import ConditionLibrary, ConditionTemplate
        from statable_gui.libcntrl.literal_library import LiteralLibrary, LiteralDefinition
    except ImportError:
        RoleFunctionLibrary = ConditionLibrary = LiteralLibrary = None
        LibRoleFunction = ConditionTemplate = LiteralDefinition = None


# ======================================================================
# ヘルパー: 文字列/リストの正規化
# ======================================================================
def _normalize_actions(value) -> List[str]:
    """
    pre_actions / else_actions を必ず List[str] に正規化する。
    - None / "" → []
    - "init()" → ["init()"]
    - ["init()"] → ["init()"]
    - 1文字リスト ["i","n","i","t","(",")"] → ["init()"]  ※旧バージョンの壊れたデータ救済
    """
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    if isinstance(value, list):
        # 1文字ずつに分解された古いデータを検出して結合
        if value and all(isinstance(s, str) and len(s) == 1 for s in value):
            joined = "".join(value)
            logger.warning(f"Detected 1-char split actions, joining: {value} -> ['{joined}']")
            return [joined]
        # 通常のリスト
        return [str(s) for s in value if str(s).strip()]
    logger.warning(f"Unexpected type for actions: {type(value)}. Converting to str.")
    return [str(value)]


# ======================================================================
# StateMachine → XML
# ======================================================================
def state_machine_to_element(sm: StateMachine) -> ET.Element:
    """Convert StateMachine to XML Element"""
    logger.debug(f"state_machine_to_element: states={len(sm.states)}, events={len(sm.events)}, "
                 f"roles={len(sm.role_functions)}, transitions={len(sm.transitions)}")

    root = ET.Element("StateMachine")
    if sm.initial_state:
        root.set("initial", sm.initial_state)

    # ★ レイヤ設定
    root.set("layer_priority", str(getattr(sm, 'layer_priority', 5)))
    root.set("layer_description", getattr(sm, 'layer_description', ''))
    root.set("layer_name", getattr(sm, 'layer_name', ''))    # ★ 追加
    logger.debug(f"  layer_priority={getattr(sm, 'layer_priority', 5)}, "
                 f"layer_description='{getattr(sm, 'layer_description', '')}', "
                 f"layer_name='{getattr(sm, 'layer_name', '')}'")

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
    for idx, t in enumerate(sm.transitions):
        # ★ 正規化: 文字列や分解済みリストを必ず正しいリストに変換
        pre_actions = _normalize_actions(getattr(t, 'pre_actions', []))
        else_actions = _normalize_actions(getattr(t, 'else_actions', []))
        has_else = getattr(t, 'has_else', True)
        else_target = getattr(t, 'else_target', '')

        logger.debug(f"  transition[{idx}]: source={t.source}, event={t.event}, target={t.target}, "
                     f"pre_actions={pre_actions}, else_actions={else_actions}, "
                     f"has_else={has_else}, else_target={else_target}")

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
        }
        trans_child = ET.SubElement(trans_elem, "Transition", **attrs)

        for pre in pre_actions:
            ET.SubElement(trans_child, "PreAction", action=str(pre))
        for ea in else_actions:
            ET.SubElement(trans_child, "ElseAction", action=str(ea))

    return root


def state_machine_from_element(elem: ET.Element) -> StateMachine:
    """Build StateMachine from XML Element"""
    logger.debug(f"state_machine_from_element: tag={elem.tag}")

    sm = StateMachine()
    initial_state_name = elem.get("initial")
    logger.debug(f"  initial_state_name={initial_state_name}")

    # ★ レイヤ設定
    try:
        sm.layer_priority = int(elem.get("layer_priority", "5"))
    except ValueError:
        sm.layer_priority = 5
    sm.layer_description = elem.get("layer_description", "")
    sm.layer_name = elem.get("layer_name", "")    # ★ 追加
    logger.debug(f"  layer_priority={sm.layer_priority}, "
                 f"layer_description='{sm.layer_description}', "
                 f"layer_name='{sm.layer_name}'")

    states_elem = elem.find("States")
    if states_elem is None:
        logger.error("  <States> element not found!")
        return sm
    for state_elem in states_elem:
        logger.debug(f"  state: name={state_elem.get('name')}, type={state_elem.get('type')}")
        try:
            sm.add_state(State(
                name=state_elem.get("name", ""),
                type=StateType(state_elem.get("type", "normal")),
                parent=state_elem.get("parent") or None,
                entry=state_elem.get("entry", ""),
                exit=state_elem.get("exit", ""),
                do=state_elem.get("do", ""),
                description=state_elem.get("description", ""),
            ))
        except Exception as e:
            logger.error(f"  Failed to load state: {e}", exc_info=True)

    events_elem = elem.find("Events")
    if events_elem is None:
        logger.error("  <Events> element not found!")
    else:
        for event_elem in events_elem:
            params_str = event_elem.get("params", "")
            params = [p.strip() for p in params_str.split(",") if p.strip()] if params_str else []
            logger.debug(f"  event: name='{event_elem.get('name')}', kind={event_elem.get('kind')}, "
                         f"delivery={event_elem.get('delivery_type')}, params={params}")
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
                ))
            except Exception as e:
                logger.error(f"  Failed to load event: {e}", exc_info=True)

    roles_elem = elem.find("RoleFunctions")
    if roles_elem is None:
        logger.debug("  <RoleFunctions> element not found (optional)")
    else:
        for rf_elem in roles_elem:
            logger.debug(f"  role_function: name={rf_elem.get('name')}")
            try:
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
            except Exception as e:
                logger.error(f"  Failed to load role_function: {e}", exc_info=True)

    trans_elem = elem.find("Transitions")
    if trans_elem is None:
        logger.error("  <Transitions> element not found!")
    else:
        for trans_elem_child in trans_elem:
            # ★ 生のリストを取得
            pre_actions_raw = [p.get("action", "") for p in trans_elem_child.findall("PreAction")]
            else_actions_raw = [e.get("action", "") for e in trans_elem_child.findall("ElseAction")]

            # ★ 正規化（1文字分解されていれば結合）
            pre_actions = _normalize_actions(pre_actions_raw)
            else_actions = _normalize_actions(else_actions_raw)

            has_else_str = trans_elem_child.get("has_else", "true")
            has_else = has_else_str.lower() == "true"
            else_target = trans_elem_child.get("else_target", "")

            logger.debug(f"  transition: source={trans_elem_child.get('source')}, "
                         f"event='{trans_elem_child.get('event')}', "
                         f"target={trans_elem_child.get('target')}, "
                         f"pre_actions(raw={pre_actions_raw})->normalized={pre_actions}, "
                         f"else_actions(raw={else_actions_raw})->normalized={else_actions}, "
                         f"has_else={has_else}(from '{has_else_str}'), else_target='{else_target}'")

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
                ))
            except Exception as e:
                logger.error(f"  Failed to load transition: {e}", exc_info=True)

    if initial_state_name:
        sm.set_initial(initial_state_name)

    logger.debug(f"state_machine_from_element: loaded states={len(sm.states)}, events={len(sm.events)}, "
                 f"roles={len(sm.role_functions)}, transitions={len(sm.transitions)}")

    return sm


# ======================================================================
# GlobalDefinitions → XML
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
    logger.debug(f"global_defs_to_element: vars={len(defs.variables)}, flags={len(defs.flags)}, "
                 f"custom_types={len(defs.custom_types)}, interrupts={len(defs.interrupts)}, "
                 f"placeholders={len(defs.placeholders)}, queues={len(defs.event_queues)}")
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
    logger.debug(f"global_defs_from_element: tag={elem.tag}")
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

    logger.debug(f"global_defs_from_element: loaded vars={len(defs.variables)}, flags={len(defs.flags)}, "
                 f"custom_types={len(defs.custom_types)}, interrupts={len(defs.interrupts)}, "
                 f"placeholders={len(defs.placeholders)}, queues={len(defs.event_queues)}")
    return defs


# ======================================================================
# 共有ライブラリ → XML
# ======================================================================
def role_function_library_to_element(lib) -> Optional[ET.Element]:
    if lib is None:
        logger.debug("role_function_library_to_element: lib is None")
        return None
    root = ET.Element("RoleFunctionLibrary")
    items = lib.list_all()
    logger.debug(f"role_function_library_to_element: {len(items)} items")
    for rf in items:
        ET.SubElement(root, "RoleFunction", **{
            "name": rf.name,
            "title": getattr(rf, 'title', ''),
            "description": getattr(rf, 'description', ''),
            "return_type": getattr(rf, 'return_type', ''),
            "arg1_type": getattr(rf, 'arg1_type', ''),
            "arg1_name": getattr(rf, 'arg1_name', ''),
            "arg2_type": getattr(rf, 'arg2_type', ''),
            "arg2_name": getattr(rf, 'arg2_name', ''),
        })
    return root


def role_function_library_from_element(elem: Optional[ET.Element]):
    """
    libcntrl.RoleFunction は name/title/description のみ受け付けるため、
    それ以外の属性は hasattr で確認してから setattr する。
    """
    if elem is None:
        logger.debug("role_function_library_from_element: elem is None")
        return RoleFunctionLibrary() if RoleFunctionLibrary else None
    lib = RoleFunctionLibrary()
    count = 0
    for rf_elem in elem.findall("RoleFunction"):
        name = rf_elem.get("name", "")
        try:
            # ★ libcntrl.RoleFunction が受け付ける引数のみで生成
            rf = LibRoleFunction(
                name=name,
                title=rf_elem.get("title", ""),
                description=rf_elem.get("description", ""),
            )
            # 追加属性は存在する場合のみ設定
            for attr in ('return_type', 'arg1_type', 'arg1_name', 'arg2_type', 'arg2_name'):
                if hasattr(rf, attr):
                    setattr(rf, attr, rf_elem.get(attr, ''))
            lib.add(rf)
            count += 1
            logger.debug(f"role_function_library_from_element: loaded role '{name}'")
        except Exception as e:
            logger.error(
                f"role_function_library_from_element: failed to load '{name}': {e}",
                exc_info=True
            )
    logger.debug(f"role_function_library_from_element: loaded {count} items")
    return lib


def condition_library_to_element(lib) -> Optional[ET.Element]:
    if lib is None:
        return None
    root = ET.Element("ConditionLibrary")
    items = lib.list_all()
    logger.debug(f"condition_library_to_element: {len(items)} items")
    for ct in items:
        ET.SubElement(root, "Condition", **{
            "name": ct.name,
            "condition": getattr(ct, 'condition', ''),
        })
    return root


def condition_library_from_element(elem: Optional[ET.Element]):
    if elem is None:
        logger.debug("condition_library_from_element: elem is None")
        return ConditionLibrary() if ConditionLibrary else None
    lib = ConditionLibrary()
    count = 0
    for ct_elem in elem.findall("Condition"):
        try:
            ct = ConditionTemplate(
                name=ct_elem.get("name", ""),
                condition=ct_elem.get("condition", ""),
            )
            lib.add(ct)
            count += 1
        except Exception as e:
            logger.error(f"condition_library_from_element: failed to load {ct_elem.get('name')}: {e}", exc_info=True)
    logger.debug(f"condition_library_from_element: loaded {count} items")
    return lib


def literal_library_to_element(lib) -> Optional[ET.Element]:
    if lib is None:
        return None
    root = ET.Element("LiteralLibrary")
    items = lib.list_all()
    logger.debug(f"literal_library_to_element: {len(items)} items")
    for lit in items:
        ET.SubElement(root, "Literal", **{
            "name": lit.name,
            "value": getattr(lit, 'value', ''),
            "literal_type": getattr(lit, 'literal_type', ''),
            "description": getattr(lit, 'description', ''),
        })
    return root


def literal_library_from_element(elem: Optional[ET.Element]):
    if elem is None:
        logger.debug("literal_library_from_element: elem is None")
        return LiteralLibrary() if LiteralLibrary else None
    lib = LiteralLibrary()
    count = 0
    for lit_elem in elem.findall("Literal"):
        try:
            lit = LiteralDefinition(
                name=lit_elem.get("name", ""),
                value=lit_elem.get("value", ""),
                literal_type=lit_elem.get("literal_type", "int"),
                description=lit_elem.get("description", ""),
            )
            lib.add(lit)
            count += 1
        except Exception as e:
            logger.error(f"literal_library_from_element: failed to load {lit_elem.get('name')}: {e}", exc_info=True)
    logger.debug(f"literal_library_from_element: loaded {count} items")
    return lib


# ======================================================================
# プロジェクト設定 → XML
# ======================================================================
def _project_settings_to_element(settings: Optional[dict]) -> ET.Element:
    """プロジェクト設定をXML要素に変換"""
    logger.debug(f"_project_settings_to_element: settings={settings is not None}")
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
        cg.set("super_include_file", settings.get('super_include_file', 'statable_all.h'))
        cg.set("max_consecutive_pending_events",
               str(settings.get('max_consecutive_pending_events', 16)))

        # 外部インクルード
        ext_includes = settings.get('external_includes', [])
        if ext_includes:
            ext_elem = ET.SubElement(cg, "ExternalIncludes")
            for inc in ext_includes:
                ET.SubElement(ext_elem, "Include", name=inc)
            logger.debug(f"  external_includes: {ext_includes}")

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
    """XML要素からプロジェクト設定を復元"""
    logger.debug(f"_project_settings_from_element: elem={elem is not None}")
    settings = {}

    if elem is None:
        return settings

    cg = elem.find("CodeGeneration")
    if cg is None:
        logger.debug("  <CodeGeneration> element not found")
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
        settings['max_consecutive_pending_events'] = int(cg.get("max_consecutive_pending_events", "16"))
    except ValueError:
        settings['max_consecutive_pending_events'] = 16

    ext_elem = cg.find("ExternalIncludes")
    if ext_elem is not None:
        settings['external_includes'] = [inc.get("name", "") for inc in ext_elem.findall("Include")]
    else:
        settings['external_includes'] = []

    settings['external_includes_in_super'] = cg.get("external_includes_in_super", "true").lower() == "true"
    settings['external_includes_in_role'] = cg.get("external_includes_in_role", "true").lower() == "true"
    settings['external_includes_in_transitions'] = cg.get("external_includes_in_transitions", "false").lower() == "true"
    settings['external_includes_in_common'] = cg.get("external_includes_in_common", "false").lower() == "true"

    logger.debug(f"  loaded project_settings: project_name='{settings['project_name']}', "
                 f"external_includes={settings['external_includes']}")
    return settings


# ======================================================================
# プロジェクト保存/読込
# ======================================================================
def project_to_xml(
        tabs: List[Tuple[str, StateMachine]],
        global_defs: GlobalDefinitions,
        filepath: str,
        role_function_library=None,
        condition_library=None,
        literal_library=None,
        project_settings: Optional[dict] = None,
) -> None:
    """Save project to XML file（共有ライブラリ + プロジェクト設定含む）"""
    logger.debug(f"=== project_to_xml START ===")
    logger.debug(f"  filepath={filepath}")
    logger.debug(f"  tabs={len(tabs)}")
    for name, sm in tabs:
        logger.debug(f"    tab '{name}': states={len(sm.states)}, transitions={len(sm.transitions)}, "
                     f"layer_priority={getattr(sm, 'layer_priority', 5)}, "
                     f"layer_name='{getattr(sm, 'layer_name', '')}'")
    logger.debug(f"  global_defs: vars={len(global_defs.variables)}, flags={len(global_defs.flags)}")
    logger.debug(f"  role_function_library={role_function_library is not None}")
    logger.debug(f"  condition_library={condition_library is not None}")
    logger.debug(f"  literal_library={literal_library is not None}")
    logger.debug(f"  project_settings={project_settings is not None}")

    root = ET.Element("Project")

    # ★ プロジェクト設定
    project_name = "MyProject"
    if project_settings:
        project_name = project_settings.get('project_name', 'MyProject')
        root.append(_project_settings_to_element(project_settings))
    root.set("name", project_name)
    logger.debug(f"  project_name='{project_name}'")

    root.append(global_defs_to_element(global_defs))

    if role_function_library is not None or condition_library is not None or literal_library is not None:
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
    logger.debug(f"=== project_to_xml END: saved to {filepath} ===")


def project_from_xml(filepath: str):
    """
    Load project from XML file.
    Returns:
        (tabs, global_defs, role_lib, cond_lib, lit_lib, project_settings)
    """
    logger.debug(f"=== project_from_xml START ===")
    logger.debug(f"  filepath={filepath}")

    tree = ET.parse(filepath)
    root = tree.getroot()
    logger.debug(f"  root tag={root.tag}")

    # プロジェクト設定
    project_settings = _project_settings_from_element(root.find("ProjectSettings"))
    if 'project_name' not in project_settings and root.get("name"):
        project_settings['project_name'] = root.get("name")
        logger.debug(f"  project_name from root attr: '{root.get('name')}'")

    gd_elem = root.find("GlobalDefinitions")
    logger.debug(f"  GlobalDefinitions found: {gd_elem is not None}")
    global_defs = global_defs_from_element(gd_elem) if gd_elem is not None else GlobalDefinitions()

    # 共有ライブラリを読込
    role_function_library = RoleFunctionLibrary() if RoleFunctionLibrary else None
    condition_library = ConditionLibrary() if ConditionLibrary else None
    literal_library = LiteralLibrary() if LiteralLibrary else None

    libs_elem = root.find("SharedLibraries")
    logger.debug(f"  SharedLibraries found: {libs_elem is not None}")
    if libs_elem is not None:
        rl_elem = libs_elem.find("RoleFunctionLibrary")
        cl_elem = libs_elem.find("ConditionLibrary")
        ll_elem = libs_elem.find("LiteralLibrary")
        logger.debug(f"    RoleFunctionLibrary elem: {rl_elem is not None}")
        logger.debug(f"    ConditionLibrary elem: {cl_elem is not None}")
        logger.debug(f"    LiteralLibrary elem: {ll_elem is not None}")
        role_function_library = role_function_library_from_element(rl_elem)
        condition_library = condition_library_from_element(cl_elem)
        literal_library = literal_library_from_element(ll_elem)

    tabs = []
    for tab_elem in root.findall("Tab"):
        name = tab_elem.get("name", "Untitled")
        logger.debug(f"  Tab: name='{name}'")
        sm_elem = tab_elem.find("StateMachine")
        sm = state_machine_from_element(sm_elem) if sm_elem is not None else StateMachine()
        tabs.append((name, sm))

    logger.debug(f"  Loaded tabs: {len(tabs)}")
    logger.debug(f"  role_function_library: {len(role_function_library.list_all()) if role_function_library else 0}")
    logger.debug(f"  condition_library: {len(condition_library.list_all()) if condition_library else 0}")
    logger.debug(f"  literal_library: {len(literal_library.list_all()) if literal_library else 0}")
    logger.debug(f"  project_settings keys: {list(project_settings.keys())}")
    logger.debug(f"=== project_from_xml END ===")

    return tabs, global_defs, role_function_library, condition_library, literal_library, project_settings