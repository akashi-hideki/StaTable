"""patch_xml_io_mypy_1.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
XML = ROOT / "statable" / "xml_io.py"
t = XML.read_text(encoding="utf-8")

def _must(old, new, label):
    global t
    if old not in t:
        raise SystemExit(f"[FAIL] {label}: not found")
    if t.count(old) != 1:
        raise SystemExit(f"[FAIL] {label}: not unique ({t.count(old)})")
    t = t.replace(old, new, 1)
    print(f"[OK] {label}")

# --- A: try/except import fallback (L58-67) ---
_must(
    "except ImportError:\n"
    "    RoleFunctionLibrary = ConditionLibrary = LiteralLibrary = None\n"
    "    LibRoleFunction = ConditionTemplate = LiteralDefinition = None\n",
    "except ImportError:\n"
    "    RoleFunctionLibrary = None  # type: ignore[misc,assignment]\n"
    "    ConditionLibrary = None  # type: ignore[misc,assignment]\n"
    "    LiteralLibrary = None  # type: ignore[misc,assignment]\n"
    "    LibRoleFunction = None  # type: ignore[misc,assignment]\n"
    "    ConditionTemplate = None  # type: ignore[misc,assignment]\n"
    "    LiteralDefinition = None  # type: ignore[misc,assignment]\n",
    "A: import fallback",
)

# --- B: Element(**attrs) at L177 ---
_must(
    '    elem = ET.Element("State", **attrs)\n',
    '    elem = ET.Element("State", **attrs)  # type: ignore[arg-type]\n',
    "B: Element kwargs",
)

# --- D: int(None) at L472 ---
_must(
    "            try:\n"
    "                sm.add_event(Event(\n"
    "                    name=event_elem.get(\"name\", \"\"),\n"
    "                    id=int(event_elem.get(\"id\")) if event_elem.get(\"id\") else None,\n",
    "            try:\n"
    "                _id_str = event_elem.get(\"id\")\n"
    "                _event_id = int(_id_str) if _id_str else None\n"
    "                sm.add_event(Event(\n"
    "                    name=event_elem.get(\"name\", \"\"),\n"
    "                    id=_event_id,\n",
    "D: int(None)",
)

XML.write_text(t, encoding="utf-8")
print(f"[OK] wrote {XML}")
