from .state_machine import StateMachine


def _truncate_condition(condition: str, max_chars: int = 50) -> str:
    """長い状態遷移条件を省略表示する（改行は先頭行のみ）"""
    if not condition:
        return ""

    # 改行がある場合は先頭行だけ使用
    lines = condition.split('\n')
    first_line = lines[0].strip() if lines else ""
    if not first_line:
        return ""

    if len(first_line) > max_chars:
        return first_line[:max_chars].rstrip() + "..."
    # 2行目以降があれば省略記号を付与
    if len(lines) > 1:
        return first_line + " ..."
    return first_line


def generate_mermaid(sm: StateMachine) -> str:
    lines = ["stateDiagram-v2", "    direction LR"]

    if sm.initial_state:
        lines.append(f"    [*] --> {sm.initial_state}")

    for t in sm.transitions:
        label_parts = []
        if t.event:
            label_parts.append(t.event)

        # ガード条件は短縮して表示
        if t.condition:
            label_parts.append(f"[{_truncate_condition(t.condition)}]")

        # アクション（動作）は表示しない
        label = " ".join(label_parts).strip()

        if t.target:
            lines.append(f"    {t.source} --> {t.target} : {label}")
        else:
            lines.append(f"    note right of {t.source} : internal: {label}")

    return "\n".join(lines)