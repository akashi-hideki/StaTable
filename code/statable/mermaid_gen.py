from .state_machine import StateMachine


def generate_mermaid(sm: StateMachine) -> str:
    lines = ["stateDiagram-v2", "    direction LR"]

    # 初期状態
    if sm.initial_state:
        lines.append(f"    [*] --> {sm.initial_state}")

    # 遷移のみを出力（アクションは表示しない）
    for t in sm.transitions:
        label_parts = []
        if t.event:
            label_parts.append(t.event)
        if t.guard:
            label_parts.append(f"[{t.guard}]")
        # ★ アクション（動作）はMermaidには表示しない
        label = " ".join(label_parts).strip()

        if t.target:
            lines.append(f"    {t.source} --> {t.target} : {label}")
        else:
            # 内部遷移の場合もアクションを表示しない
            lines.append(f"    note right of {t.source} : internal: {label}")

    return "\n".join(lines)