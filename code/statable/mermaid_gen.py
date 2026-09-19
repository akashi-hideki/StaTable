from .state_machine import StateMachine


# ============================================================
# Mermaid label sanitization (v2.0 / v2.2)
#   All replacements use ASCII to satisfy the English-only policy.
# ============================================================
_MERMAID_LABEL_REPLACEMENTS = (
    (":",  "-"),   # colon -> dash
    ("[",  "("),   # opening bracket -> paren
    ("]",  ")"),   # closing bracket -> paren
    ('"',  "'"),
    ("`",  "'"),
    ("\n", " "),
    ("\r", " "),
)


def _sanitize_label(text: str) -> str:
    """Sanitize the Mermaid label string."""
    if not text:
        return ""
    for src, dst in _MERMAID_LABEL_REPLACEMENTS:
        text = text.replace(src, dst)
    text = " ".join(text.split())
    return text


def _truncate_condition(condition: str, max_chars: int = 50) -> str:
    """Show long state transition conditions abbreviated."""
    if not condition:
        return ""
    lines = condition.split('\n')
    first_line = lines[0].strip() if lines else ""
    if not first_line:
        return ""
    if len(first_line) > max_chars:
        return first_line[:max_chars].rstrip() + "..."
    if len(lines) > 1:
        return first_line + " ..."
    return first_line


def _mode_suffix(trans) -> str:
    """
    v2.2: Return a short mode suffix for the transition label.

    "C" -> Commit    (early_return=True)
    "T" -> Tentative (early_return=False)
    Empty string is returned when early_return is not set (backward compat).
    """
    er = getattr(trans, 'early_return', None)
    if er is True:
        return " [Commit]"
    return ""


def _build_label(trans, *, short_mode: bool = True) -> str:
    """Build the Mermaid label for a single transition."""
    label_parts = []

    # ---- Title ----
    title_raw = getattr(trans, 'title', '') or ""
    title_safe = _sanitize_label(title_raw)
    if title_safe and title_safe != "(untitled transition)":
        label_parts.append(title_safe)
    else:
        if getattr(trans, 'target', ''):
            label_parts.append(_sanitize_label(trans.target))
        else:
            label_parts.append("(internal)")

    # ---- Event ----
    ev = getattr(trans, 'event', '') or ""
    if ev:
        ev_safe = _sanitize_label(ev)
        if ev_safe:
            label_parts.append(f"({ev_safe})")

    # ---- Condition ----
    cond = getattr(trans, 'condition', '') or ""
    if cond:
        cond_text = _sanitize_label(_truncate_condition(cond))
        if cond_text:
            label_parts.append(f"[{cond_text}]")

    # ---- Mode (v2.2) ----
    mode = _mode_suffix(trans)
    if mode:
        label_parts.append(mode)

    return " ".join(label_parts).strip()


def generate_mermaid(sm: StateMachine) -> str:
    """
    Generate a Mermaid stateDiagram-v2 string from a StateMachine.

    [v2.2 changes]
      - Each transition in a cell becomes its own edge.
      - else_target is emitted as a separate edge (dashed style not
        available in stateDiagram-v2, so we use label "else").
      - early_return=True adds " [Commit]" to the label.
      - entry / exit are NOT rendered (metadata only).
    """
    lines = ["stateDiagram-v2", "    direction LR"]

    if sm.initial_state:
        lines.append(f"    [*] --> {sm.initial_state}")

    for t in sm.transitions:
        # ---- Primary edge (target) ----
        if t.target:
            label = _build_label(t)
            lines.append(f"    {t.source} --> {t.target} : {label}")
        else:
            # No target: internal action only -> attach a note
            label = _build_label(t)
            lines.append(f"    note right of {t.source} : internal: {label}")

        # ---- Secondary edge (else_target) ----
        else_target = getattr(t, 'else_target', '') or ''
        has_else = getattr(t, 'has_else', True)
        if has_else and else_target:
            else_label_parts = []
            # Show event name (if any) so the edge is identifiable
            ev = getattr(t, 'event', '') or ""
            if ev:
                ev_safe = _sanitize_label(ev)
                if ev_safe:
                    else_label_parts.append(f"({ev_safe})")
            else:
                else_label_parts.append("(completion)")
            else_label_parts.append("else")
            # Add mode suffix
            mode = _mode_suffix(t)
            if mode:
                else_label_parts.append(mode)
            else_label = " ".join(else_label_parts)
            lines.append(
                f"    {t.source} --> {else_target} : {else_label}"
            )

    return "\n".join(lines)