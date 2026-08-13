from .state_machine import StateMachine


def generate_mermaid(sm: StateMachine) -> str:
    lines = ["stateDiagram-v2"]

    # 初期状態
    if sm.initial_state:
        lines.append(f"    [*] --> {sm.initial_state}")

    # 状態定義（entry/exit/do はコメントとして付与）
    for state in sm.states.values():
        desc = []
        if state.entry:
            desc.append(f"entry / {state.entry}")
        if state.exit:
            desc.append(f"exit / {state.exit}")
        if state.do:
            desc.append(f"do / {state.do}")
        if desc:
            lines.append(f"    {state.name} : {'; '.join(desc)}")

    # 遷移
    for t in sm.transitions:
        label_parts = []
        if t.event:
            label_parts.append(t.event)
        if t.guard:
            label_parts.append(f"[{t.guard}]")
        if t.action:
            label_parts.append(f"/ {t.action}")
        label = " ".join(label_parts).strip()

        if t.target:
            # 外部遷移（自己遷移含む）
            lines.append(f"    {t.source} --> {t.target} : {label}")
        else:
            # 内部遷移
            lines.append(f"    note right of {t.source} : internal: {label}")

    return "\n".join(lines)