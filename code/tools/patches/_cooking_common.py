"""Shared helpers for cooking heater controller XML patches.

Phase 7 対応: add_var を冪等化 + remove/reorder ヘルパー追加。
"""
from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

SCRIPT = Path(__file__).resolve()
CODE_DIR = SCRIPT.parent.parent.parent
XML_PATH = CODE_DIR / "docs" / "samples" / "cooking_heater_controller.xml"


# ------------------------------------------------------------------
# Load / Save
# ------------------------------------------------------------------
def load_or_create() -> ET.Element:
    if XML_PATH.exists():
        return ET.parse(XML_PATH).getroot()
    return ET.Element("Project", {"name": "CookingHeaterController"})


def save(root: ET.Element) -> None:
    XML_PATH.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root, space="    ")
    body = ET.tostring(root, encoding="unicode")
    XML_PATH.write_text(
        "<?xml version='1.0' encoding='utf-8'?>\n" + body + "\n",
        encoding="utf-8", newline="\n")
    print(f"[OK] wrote {XML_PATH}")
    print(f"     size: {XML_PATH.stat().st_size} bytes")


# ------------------------------------------------------------------
# Find helpers
# ------------------------------------------------------------------
def find_or_create(parent: ET.Element, tag: str, **attrs) -> ET.Element:
    for child in parent.findall(tag):
        if all(child.get(k) == v for k, v in attrs.items()):
            return child
    return ET.SubElement(parent, tag, attrs)


# ------------------------------------------------------------------
# Variables (idempotent)
# ------------------------------------------------------------------
def add_var(sv: ET.Element, name, typ, unit, desc,
            group: str = "Hardware") -> None:
    """Add a SystemVariable only if not already present."""
    for v in sv.findall("Variable"):
        if v.get("name") == name:
            print(f"[SKIP] var exists: {name}")
            return
    ET.SubElement(sv, "Variable", {
        "name": name, "type": typ, "unit": unit,
        "default_value": "0", "group": group,
        "description": desc, "title": desc, "array_size": "0",
    })
    print(f"[ADD]  var: {name} ({typ})")


def remove_var(sv: ET.Element, name: str) -> bool:
    for v in sv.findall("Variable"):
        if v.get("name") == name:
            sv.remove(v)
            print(f"[DEL]  var: {name}")
            return True
    return False


# ------------------------------------------------------------------
# Role functions
# ------------------------------------------------------------------
def add_rolefn(parent: ET.Element, name, ns, title, desc, ret="int") -> None:
    """Add a RoleFunction only if (namespace, name) not already present."""
    for rf in parent.findall("RoleFunction"):
        if rf.get("name") == name and rf.get("namespace") == ns:
            return
    ET.SubElement(parent, "RoleFunction", {
        "name": name, "namespace": ns, "title": title,
        "description": desc, "return_type": ret,
        "arg1_type": "", "arg1_name": "",
        "arg2_type": "", "arg2_name": "",
    })


def remove_rolefn_by_ns(parent: ET.Element, ns: str) -> int:
    removed = 0
    for rf in list(parent.findall("RoleFunction")):
        if rf.get("namespace") == ns:
            parent.remove(rf)
            removed += 1
    if removed:
        print(f"[DEL]  {removed} RoleFunction(s) in namespace '{ns}'")
    return removed


# ------------------------------------------------------------------
# Tabs
# ------------------------------------------------------------------
def add_tab(root: ET.Element, name: str, initial: str,
            priority: str, layer_name: str, desc: str) -> ET.Element:
    """Remove existing tab with same name, then add new one."""
    remove_tab(root, name)
    tab = ET.SubElement(root, "Tab", {"name": name})
    ET.SubElement(tab, "StateMachine", {
        "initial": initial, "layer_priority": priority,
        "layer_description": desc, "layer_name": layer_name,
    })
    return tab


def remove_tab(root: ET.Element, name: str) -> bool:
    for t in root.findall("Tab"):
        if t.get("name") == name:
            root.remove(t)
            print(f"[DEL]  tab: {name}")
            return True
    return False


def reorder_tabs(root: ET.Element, order: list[str]) -> None:
    """Reorder <Tab> elements according to `order`; unknown tabs go last."""
    tabs_by_name = {t.get("name"): t for t in root.findall("Tab")}
    for t in list(root.findall("Tab")):
        root.remove(t)
    for name in order:
        if name in tabs_by_name:
            root.append(tabs_by_name.pop(name))
    for t in tabs_by_name.values():      # leftovers
        root.append(t)
    print(f"[OK]   reordered tabs: {[t.get('name') for t in root.findall('Tab')]}")