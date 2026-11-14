"""psblog/v1 XML mapper (spec §9.5).

Maps device response frames (and psblog data lines) to XML elements
for consumption by downstream tools (e.g. PowerSimBuilder).
"""
from __future__ import annotations


def _escape(value: str) -> str:
    """XML-escape an attribute value (order matters: & first)."""
    return (str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))


def _is_id_key(k: str) -> bool:
    return k.isdigit()


def _kv_to_attrs(kv: dict) -> str:
    """Convert key=value dict to XML attributes.

    Keys that are all digits are treated as variable IDs and expanded
    to id="N" value="V" (compact format support).
    """
    out = []
    for k, v in kv.items():
        v_esc = _escape(v)
        if _is_id_key(k):
            out.append(f'id="{k}" value="{v_esc}"')
        else:
            out.append(f'{k}="{v_esc}"')
    return " ".join(out)


def frame_to_xml(line: str, t_ms: int) -> str:
    """Map a device response to a <sample> XML element.

    Handles (spec §3.4 / §9.5):
      ACK ret=0 id=1 name=X value=25         -> <var id="1" name="X" value="25"/>
      ACK ret=0 3=25 7=100 15=31  (compact)   -> <var id="3" value="25"/> ...
      NAK ret=2 id=99 reason=idx              -> <var id="99" reason="idx"/>
      ACK ret=0 fw=3.6.0 crc=... vars=30
      ""  or single token                     -> <sample .../> (no <var>)

    Values are XML-escaped (& < > " ').
    """
    if line is None:
        line = ""
    line = line.strip()
    if not line:
        return f'<sample t="{t_ms}" kind="EMPTY" status=""/>'

    parts = line.split()
    if len(parts) < 2:
        return (f'<sample t="{t_ms}" kind="{_escape(parts[0])}"'
                f' status=""/>')

    kind = parts[0]
    status = parts[1]
    kv: dict = {}
    for p in parts[2:]:
        if "=" in p:
            k, v = p.split("=", 1)
            kv[k] = v

    kind_esc = _escape(kind)
    status_esc = _escape(status)

    numeric_keys = [k for k in kv if _is_id_key(k)]
    named_keys = [k for k in kv if not _is_id_key(k)]

    # Compact form: each N=V is its own <var id="N" value="V"/>
    if numeric_keys and not named_keys:
        vars_xml = ''.join(
            f'<var id="{k}" value="{_escape(kv[k])}"/>'
            for k in numeric_keys
        )
        return (f'<sample t="{t_ms}" kind="{kind_esc}" '
                f'status="{status_esc}">{vars_xml}</sample>')

    # Mixed (unexpected) or named-only: single <var> with all attrs
    attrs = _kv_to_attrs(kv)
    if attrs:
        return (f'<sample t="{t_ms}" kind="{kind_esc}" '
                f'status="{status_esc}"><var {attrs}/></sample>')
    return (f'<sample t="{t_ms}" kind="{kind_esc}" '
            f'status="{status_esc}"/>')


def data_line_to_xml(line: str) -> str:
    """Map a psblog Data line (@<t_ms> k=v k=v ...) to XML.

    Example: '@200 a=1 b=2' -> '<sample t="200" kind="DATA"><var a="1" b="2"/></sample>'
    """
    line = (line or "").strip()
    if not line.startswith("@"):
        return ""
    rest = line[1:]
    parts = rest.split()
    if not parts:
        return ""
    try:
        t_ms = int(parts[0])
    except ValueError:
        return ""
    kv: dict = {}
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            kv[k] = v
    attrs = _kv_to_attrs(kv)
    if attrs:
        return f'<sample t="{t_ms}" kind="DATA"><var {attrs}/></sample>'
    return f'<sample t="{t_ms}" kind="DATA"/>'
