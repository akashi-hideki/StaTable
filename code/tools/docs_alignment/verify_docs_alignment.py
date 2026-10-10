"""Final cross-document validation."""
from __future__ import annotations
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent.parent
XML = ROOT / "code" / "docs" / "samples" / "cooking_heater_controller.xml"
DOCS = ROOT / "code" / "docs" / "samples"


def main() -> int:
    # Parse XML
    tree = ET.parse(XML)
    root = tree.getroot()
    tabs = root.findall("Tab")
    total_states = 0
    for tab in tabs:
        total_states += len(tab.findall("StateMachine/States/State"))
    rfl = root.find("SharedLibraries/RoleFunctionLibrary")
    total_roles = len(rfl.findall("RoleFunction")) if rfl is not None else 0

    print(f"XML truth:")
    print(f"  tabs        = {len(tabs)}")
    print(f"  states      = {total_states}")
    print(f"  roles       = {total_roles}")

    # Check docs
    checks = [
        ("LAYER_DESIGN_zh.md", [
            ("七层架构", "yes"),
            ("| 7 | **DriverOutput**", "yes"),
            ("| 6 | **DriverInput**", "yes"),
            ("**31 状态**", "maybe"),
        ]),
        ("ROLE_FUNCTIONS_zh.md", [
            ("## 3. DriverInput 层（6 个）", "yes"),
            ("## 4. DriverOutput 层（13 个）", "yes"),
            ("## 11. 变更历史", "yes"),
            ("Version: 1.1", "yes"),
        ]),
        ("README_zh.md", [
            ("七层架构", "yes"),
            ("**31**", "yes"),
            ("60 个 Role 函数", "yes"),
            ("DriverInput", "yes"),
            ("DriverOutput", "yes"),
        ]),
        ("INSTALL_GUIDE_zh.md", [
            ("[DriverInput] [DriverOutput]", "yes"),
        ]),
    ]

    print()
    for fname, patterns in checks:
        path = DOCS / fname
        if not path.exists():
            print(f"[MISS] {fname}")
            continue
        text = path.read_text(encoding="utf-8")
        print(f"\n{fname}:")
        for pat, _ in patterns:
            found = pat in text
            mark = "OK " if found else "MISS"
            print(f"  [{mark}] {pat!r}")

    return 0


if __name__ == "__main__":
    sys.exit(main())