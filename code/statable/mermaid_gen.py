from .state_machine import StateMachine


# ============================================================
# Mermaid ラベル用サニタイズ（v2.0 Add）
# ============================================================
#
# Characters causing problems in Mermaid labels:
#
#   : misidentified as label separator
#        Example: \"Halt --> Active : RETRY\"
#        → Title内の ":" でパースError
#
#   "[" "]"
#        may conflict with condition block notation
#        -> parse fails if double [ ]
#
#   quote misidentified as label end
#
#   "\n" ラベルは 1 RowのみEnabled → 空白に正規化
#
#   backquote may be misidentified as code block
#
_MERMAID_LABEL_REPLACEMENTS = (
    (":",  ":"),   # Colon -> full-width colon
    ("[",  "["),   # Open bracket -> full-width
    ("]",  "]"),   # Close bracket -> full-width
    ('"',  "'"),    # Double quote -> single
    ("`",  "'"),    # Backquote -> single
    ("\n", " "),    # Newline -> space
    ("\r", " "),
)


def _sanitize_label(text: str) -> str:
    """
    Mermaid のラベル文字列を安全化する。

    ユーザー入力のTitle・Event name・Condition式に
    Mermaid のメタ文字が含まれていても、パースErrorを
    起こさないように置換する。

    例:
      "RETRY: battery_voltage >600"
        → "RETRY: battery_voltage >600"
    """
    if not text:
        return ""
    for src, dst in _MERMAID_LABEL_REPLACEMENTS:
        text = text.replace(src, dst)
    # Normalize consecutive whitespace
    text = " ".join(text.split())
    return text


def _truncate_condition(condition: str, max_chars: int = 50) -> str:
    """長いState transition conditionを省略表示する（改Rowは先頭Rowのみ）"""
    if not condition:
        return ""

    # If newline, use only first line
    lines = condition.split('\n')
    first_line = lines[0].strip() if lines else ""
    if not first_line:
        return ""

    if len(first_line) > max_chars:
        return first_line[:max_chars].rstrip() + "..."
    # Append ellipsis if 2nd line or later
    if len(lines) > 1:
        return first_line + " ..."
    return first_line


def generate_mermaid(sm: StateMachine) -> str:
    """
    StateMachine から Mermaid stateDiagram-v2 形式の文字列を生成する。

    ラベル（Title / Event name / Condition式）はすべて
    _sanitize_label で正規化してパースErrorを防止する。
    """
    lines = ["stateDiagram-v2", "    direction LR"]

    if sm.initial_state:
        lines.append(f"    [*] --> {sm.initial_state}")

    for t in sm.transitions:
        label_parts = []

        # ---- Title（無題Transition以外） ----
        title_raw = t.title or ""
        title_safe = _sanitize_label(title_raw)
        if title_safe and title_safe != "(untitled transition)":
            label_parts.append(title_safe)
        else:
            # TitleNone → Targetを表示
            if t.target:
                label_parts.append(_sanitize_label(t.target))
            else:
                label_parts.append("(internal)")

        # ---- Event name ----
        if t.event:
            event_safe = _sanitize_label(t.event)
            if event_safe:
                label_parts.append(f"({event_safe})")

        # ---- Guard condition (shortened) ----
        if t.condition:
            cond_text = _sanitize_label(
                _truncate_condition(t.condition)
            )
            if cond_text:
                label_parts.append(f"[{cond_text}]")

        # ---- Label combine ----
        label = " ".join(label_parts).strip()

        # ---- Output transition lines ----
        if t.target:
            lines.append(f"    {t.source} --> {t.target} : {label}")
        else:
            lines.append(
                f"    note right of {t.source} : internal: {label}"
            )

    return "\n".join(lines)