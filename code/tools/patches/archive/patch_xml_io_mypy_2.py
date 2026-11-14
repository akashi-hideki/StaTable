"""patch_xml_io_mypy_2.py"""
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

# --- C: for (source, event) in cell_keys (L406-421) ---
_must(
    "        for (source, event) in cell_keys:\n"
    "            cell_elem = ET.SubElement(\n"
    "                cells_elem, \"Cell\",\n"
    "                source=source, event=event,  # type: ignore[arg-type]\n"
    "            )\n"
    "\n"
    "            actions = sm.get_actions_for_cell(source, event)\n",
    "        for (source, ev_key) in cell_keys:\n"
    "            cell_elem = ET.SubElement(\n"
    "                cells_elem, \"Cell\",\n"
    "                source=source, event=ev_key,\n"
    "            )\n"
    "\n"
    "            actions = sm.get_actions_for_cell(source, ev_key)\n",
    "C: cell_keys event",
)

_must(
    "            relations = sm.get_relations_for_cell(source, event)\n",
    "            relations = sm.get_relations_for_cell(source, ev_key)\n",
    "C: relations_for_cell",
)

# --- E: append(Element | None) at L1114-1118 ---
_must(
    "        if role_function_library is not None:\n"
    "            libs_elem.append(role_function_library_to_element(role_function_library))\n"
    "        if condition_library is not None:\n"
    "            libs_elem.append(condition_library_to_element(condition_library))\n"
    "        if literal_library is not None:\n"
    "            libs_elem.append(literal_library_to_element(literal_library))\n",
    "        if role_function_library is not None:\n"
    "            _e = role_function_library_to_element(role_function_library)\n"
    "            if _e is not None:\n"
    "                libs_elem.append(_e)\n"
    "        if condition_library is not None:\n"
    "            _e = condition_library_to_element(condition_library)\n"
    "            if _e is not None:\n"
    "                libs_elem.append(_e)\n"
    "        if literal_library is not None:\n"
    "            _e = literal_library_to_element(literal_library)\n"
    "            if _e is not None:\n"
    "                libs_elem.append(_e)\n",
    "E: append None",
)

XML.write_text(t, encoding="utf-8")
print(f"[OK] wrote {XML}")
