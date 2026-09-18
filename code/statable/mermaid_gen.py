from .state_machine import StateMachine


# ============================================================
# Mermaid ラベル用サニタイズ（v2.0 Add）
# ============================================================
#
# Mermaid stateDiagram-v2 のラベルで問題になる文字と代替:
#
#   ":"  状態遷移ラベルの区切り文字と誤認される
#        例: "Halt --> Active : RETRY: battery_voltage >600"
#        → Title内の ":" でパースError
#
#   "[" "]"
#        条件ブロック記法と競合する可能性
#        → 二重の "[ ]" が混ざるとパース失敗
#
#   '"'  引用符がラベル全体の終端と誤認される
#
#   "\n" ラベルは 1 行のみEnabled → 空白に正規化
#
#   "`"  コードブロックと誤認される可能性
#
_MERMAID_LABEL_REPLACEMENTS = (
    (":",  "："),   # コロン → 全角コロン
    ("[",  "［"),   # 開き角括弧 → 全角
    ("]",  "］"),   # 閉じ角括弧 → 全角
    ('"',  "'"),    # ダブルクォート → シングル
    ("`",  "'"),    # バッククォート → シングル
    ("\n", " "),    # 改行 → 空白
    ("\r", " "),
)


def _sanitize_label(text: str) -> str:
    """
    Mermaid のラベル文字列を安全化する。

    ユーザー入力のTitle・Event name・条件式に
    Mermaid のメタ文字が含まれていても、パースErrorを
    起こさないように置換する。

    例:
      "RETRY: battery_voltage >600"
        → "RETRY： battery_voltage >600"
    """
    if not text:
        return ""
    for src, dst in _MERMAID_LABEL_REPLACEMENTS:
        text = text.replace(src, dst)
    # 連続空白を単一に正規化
    text = " ".join(text.split())
    return text


def _truncate_condition(condition: str, max_chars: int = 50) -> str:
    """長いState transition conditionを省略表示する（改行は先頭行のみ）"""
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
    """
    StateMachine から Mermaid stateDiagram-v2 形式の文字列を生成する。

    ラベル（Title / Event name / 条件式）はすべて
    _sanitize_label で正規化してパースErrorを防止する。
    """
    lines = ["stateDiagram-v2", "    direction LR"]

    if sm.initial_state:
        lines.append(f"    [*] --> {sm.initial_state}")

    for t in sm.transitions:
        label_parts = []

        # ---- Title（無題遷移以外） ----
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

        # ---- ガード条件（短縮 + サニタイズ） ----
        if t.condition:
            cond_text = _sanitize_label(
                _truncate_condition(t.condition)
            )
            if cond_text:
                label_parts.append(f"[{cond_text}]")

        # ---- ラベル結合 ----
        label = " ".join(label_parts).strip()

        # ---- 遷移行を出力 ----
        if t.target:
            lines.append(f"    {t.source} --> {t.target} : {label}")
        else:
            lines.append(
                f"    note right of {t.source} : internal: {label}"
            )

    return "\n".join(lines)