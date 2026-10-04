"""Shared helpers for cooking heater controller XML patches."""
from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

SCRIPT = Path(__file__).resolve()
CODE_DIR = SCRIPT.parent.parent.parent
XML_PATH = CODE_DIR / "docs" / "samples" / "cooking_heater_controller.xml"


def load_or_create() -> ET.Element:
    if XML_PATH.exists():
        return ET.parse(XML_PATH).getroot()
    return ET.Element("Project", {"name": "CookingHeaterController"})


def save(root: ET.Element) -> None:
    XML_PATH.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root, space="    ")
    body = ET.tostring(root, encoding="unicode")
    XML_PATH.write_text("<?xml version='1.0' encoding='utf-8'?>\n" + body + "\n",
                        encoding="utf-8", newline="\n")
    print(f"[OK] wrote {XML_PATH}")
    print(f"     size: {XML_PATH.stat().st_size} bytes")


def find_or_create(parent: ET.Element, tag: str, **attrs) -> ET.Element:
    """Find a child by tag (and attrs if any), or create it."""
    for child in parent.findall(tag):
        if all(child.get(k) == v for k, v in attrs.items()):
            return child
    return ET.SubElement(parent, tag, attrs)


def add_var(sv: ET.Element, name, typ, unit, desc) -> None:
    ET.SubElement(sv, "Variable", {
        "name": name, "type": typ, "unit": unit,
        "default_value": "0", "group": "Hardware",
        "description": desc, "title": desc, "array_size": "0",
    })


def add_rolefn(parent: ET.Element, name, ns, title, desc, ret="int") -> None:
    ET.SubElement(parent, "RoleFunction", {
        "name": name, "namespace": ns, "title": title,
        "description": desc, "return_type": ret,
        "arg1_type": "", "arg1_name": "", "arg2_type": "", "arg2_name": "",
    })


def add_tab(root: ET.Element, name: str, initial: str,
            priority: str, layer_name: str, desc: str) -> ET.Element:
    """Remove existing tab with same name, then add new one."""
    for t in root.findall("Tab"):
        if t.get("name") == name:
            root.remove(t)
    tab = ET.SubElement(root, "Tab", {"name": name})
    ET.SubElement(tab, "StateMachine", {
        "initial": initial, "layer_priority": priority,
        "layer_description": desc, "layer_name": layer_name,
    })
    return tab