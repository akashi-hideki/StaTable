"""Investigate StateActionsDialog role function registration gap.

Compares:
  - state_actions_dialog.py       (v2.7, suspect: missing role mgmt)
  - transition_editor_direct/actions_tab.py  (v2.5, reference: has role mgmt)
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUI = ROOT / "statable_gui"

TARGETS = {
    "state_actions_dialog":    GUI / "state_actions_dialog.py",
    "actions_tab (v2.5 ref)":  GUI / "transition_editor_direct" / "actions_tab.py",
    "role_function_dialog":    GUI / "role_function_dialog.py",
    "libcntrl/rf_library":     GUI / "libcntrl" / "role_function_library.py",
    "matrix_table":            GUI / "matrix_table.py",
    "widgets (SettingsPanel)": GUI / "widgets.py",
}

PATTERNS = {
    "role_function_library param": r"role_function_library",
    "state_machine param":         r"state_machine",
    "layer_names_provider":        r"layer_names_provider",
    "+ New button":                r"[+＋]\s*New|on_new_role_function|_on_new_role",
    "Edit button":                 r"Edit\s*Role|on_edit_role_function|_on_edit_role",
    "Delete button":               r"Delete\s*Role|on_delete_role_function|_on_delete_role",
    "RoleFunctionDialog import":   r"RoleFunctionDialog",
    "_find_rf_by_display":         r"_find_rf_by_display",
    "state_machine.role_functions":r"role_functions",
    "qualified_name":              r"qualified_name",
    "dataModified signal":         r"dataModified",
}


def hr(title: str) -> None:
    print()
    print("=" * 74)
    print(f"  {title}")
    print("=" * 74)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


def find_hits(text: str, pattern: str) -> list[tuple[int, str]]:
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        if re.search(pattern, line):
            hits.append((i, line.rstrip()))
    return hits


# ----------------------------------------------------------------------
# 1. File existence
# ----------------------------------------------------------------------
hr("1. File existence")
for name, path in TARGETS.items():
    mark = "[OK]  " if path.exists() else "[MISS]"
    size = path.stat().st_size if path.exists() else 0
    print(f"  {mark} {name:<30} {size:>7} bytes")
    print(f"         {path.relative_to(ROOT)}")


# ----------------------------------------------------------------------
# 2. Pattern scan
# ----------------------------------------------------------------------
hr("2. Feature presence matrix")
header = f"  {'feature':<30} | {'state_actions':<14} | {'actions_tab':<14}"
print(header)
print("  " + "-" * 66)

sa_text = read(TARGETS["state_actions_dialog"])
at_text = read(TARGETS["actions_tab (v2.5 ref)"])

for label, pat in PATTERNS.items():
    sa_hits = find_hits(sa_text, pat)
    at_hits = find_hits(at_text, pat)
    sa_mark = f"{len(sa_hits):>3} hits" if sa_hits else "  ---"
    at_mark = f"{len(at_hits):>3} hits" if at_hits else "  ---"
    flag = ""
    if at_hits and not sa_hits:
        flag = "  ← GAP"
    print(f"  {label:<30} | {sa_mark:<14} | {at_mark:<14}{flag}")


# ----------------------------------------------------------------------
# 3. Class / method inventory
# ----------------------------------------------------------------------
def inventory(text: str) -> None:
    print()
    for i, line in enumerate(text.splitlines(), 1):
        m = re.match(r"^(\s*)class\s+(\w+)", line)
        if m:
            indent = len(m.group(1))
            name = m.group(2)
            print(f"    {'  ' * (indent // 4)}class {name}  (L{i})")
            continue
        m = re.match(r"^(\s*)def\s+(\w+)", line)
        if m and "self" in line.split("def")[1].split("(")[1].split(")")[0]:
            indent = len(m.group(1))
            name = m.group(2)
            print(f"    {'  ' * (indent // 4)}  def {name}()  (L{i})")


hr("3. state_actions_dialog.py — class / method inventory")
inventory(sa_text)

hr("4. actions_tab.py (v2.5 reference) — class / method inventory")
inventory(at_text)


# ----------------------------------------------------------------------
# 5. Signature comparison
# ----------------------------------------------------------------------
hr("5. Constructor signatures")
for name in ("state_actions_dialog", "actions_tab (v2.5 ref)"):
    text = read(TARGETS[name])
    for i, line in enumerate(text.splitlines(), 1):
        if re.search(r"def __init__", line):
            # gather multi-line signature
            sig_lines = [line.rstrip()]
            depth = line.count("(") - line.count(")")
            j = i
            while depth > 0 and j < len(text.splitlines()):
                j += 1
                next_line = text.splitlines()[j - 1]
                sig_lines.append("      " + next_line.rstrip())
                depth += next_line.count("(") - next_line.count(")")
                if j - i > 15:
                    break
            print(f"\n  --- {name} (L{i}) ---")
            for s in sig_lines:
                print(f"  {s}")
            break


# ----------------------------------------------------------------------
# 6. Call sites (who instantiates these dialogs?)
# ----------------------------------------------------------------------
hr("6. Call sites of StateActionsDialog")
for src_name in ("matrix_table", "widgets (SettingsPanel)"):
    text = read(TARGETS[src_name])
    hits = find_hits(text, r"StateActionsDialog")
    print(f"\n  [{src_name}]  {len(hits)} hit(s)")
    for ln, line in hits:
        print(f"    L{ln}: {line.strip()[:110]}")


hr("7. Call sites of ActionEditorDialog")
for src_name in ("matrix_table", "widgets (SettingsPanel)"):
    text = read(TARGETS[src_name])
    hits = find_hits(text, r"ActionEditorDialog")
    print(f"\n  [{src_name}]  {len(hits)} hit(s)")
    for ln, line in hits:
        print(f"    L{ln}: {line.strip()[:110]}")


# ----------------------------------------------------------------------
# 8. _ActionListWidget internals (v2.7)
# ----------------------------------------------------------------------
hr("8. state_actions_dialog._ActionListWidget — column setup")
for i, line in enumerate(sa_text.splitlines(), 1):
    if re.search(r"setHorizontalHeaderLabels|QComboBox|setCellWidget|setEditTriggers|Target|Condition|Type", line):
        print(f"  L{i:>4}: {line.strip()[:110]}")

print()
print("=" * 74)
print("  END OF REPORT")
print("=" * 74)