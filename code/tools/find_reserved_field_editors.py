#!/usr/bin/env python3
"""
Find GUI editors that still expose reserved fields (v3.7).

Background
----------
In v3.7, the following fields were removed from the SettingsPanel UI
because they are never used by the code generator:

  - State.do
  - RoleFunction.return_type / arg1_type / arg1_name
                             / arg2_type / arg2_name

However, other dialogs (RoleFunctionDialog, RoleFunctionEditDialog,
ActionEditDialog, ...) may still expose editors for those fields.
This script scans the source tree and reports:

  1. Every occurrence of a reserved field (file / line / context)
  2. GUI files where a reserved field coexists with a dialog /
     editor widget (potential leak of the removed UI)
  3. A focused inspection of the key dialog files
  4. Whether codegen/ actually uses any reserved field
     (expected: NONE)
  5. Whether xml_io.py still preserves them
     (expected: ALL PRESENT)

Usage
-----
    python tools/find_reserved_field_editors.py
    python tools/find_reserved_field_editors.py --gui-only
    python tools/find_reserved_field_editors.py --context 3
    python tools/find_reserved_field_editors.py --root /path/to/code
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
RESERVED_FIELDS: Dict[str, re.Pattern] = {
    "return_type": re.compile(r"\breturn_type\b"),
    "arg1_type":   re.compile(r"\barg1_type\b"),
    "arg1_name":   re.compile(r"\barg1_name\b"),
    "arg2_type":   re.compile(r"\barg2_type\b"),
    "arg2_name":   re.compile(r"\barg2_name\b"),
    "State.do":    re.compile(r"\.do\b|\bdo\s*[:=]"),
}

SEARCH_DIRS_ALL = ["statable", "statable_gui", "codegen", "tests", "tools"]
SEARCH_DIRS_GUI = ["statable_gui"]

EXCLUDE_PARTS = {
    "__pycache__",
    "output",
    "misra_report",
    ".git",
    ".venv",
    "venv",
}

KEY_DIALOGS = [
    "statable_gui/role_function_dialog.py",
    "statable_gui/libcntrl/role_function_edit_dialog.py",
    "statable_gui/action_edit_dialog.py",
    "statable_gui/widgets.py",
    "statable_gui/main_window.py",
]

GUI_EDITOR_HINTS = re.compile(
    r"\b(QDialog|QLineEdit|QComboBox|QSpinBox|QFormLayout|"
    r"QDoubleSpinBox|QPlainTextEdit)\b"
)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def section(title: str, char: str = "=", width: int = 78) -> None:
    print()
    print(char * width)
    print(f"  {title}")
    print(char * width)


def iter_python_files(root: Path, dirs: List[str]):
    for d in dirs:
        base = root / d
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            if any(part in EXCLUDE_PARTS for part in p.parts):
                continue
            yield p


def relpath(root: Path, p: Path) -> str:
    try:
        return str(p.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(p)


def grep_file(path: Path, pattern: re.Pattern) -> List[Tuple[int, str]]:
    """Return list of (line_no, line_text) matches."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    hits = []
    for i, line in enumerate(text.splitlines(), start=1):
        if pattern.search(line):
            hits.append((i, line.rstrip()))
    return hits


# ----------------------------------------------------------------------
# Section 1: all occurrences
# ----------------------------------------------------------------------
def section1_all_occurrences(files: List[Path], root: Path) -> Dict[str, int]:
    section("1. All occurrences of reserved fields", char="-")
    counts: Dict[str, int] = {name: 0 for name in RESERVED_FIELDS}

    for name, pat in RESERVED_FIELDS.items():
        print()
        print(f"--- {name} ---")
        any_hit = False
        for f in files:
            hits = grep_file(f, pat)
            if not hits:
                continue
            any_hit = True
            rel = relpath(root, f)
            print(f"  {rel}")
            for line_no, text in hits:
                print(f"    L{line_no:<5}  {text.strip()}")
                counts[name] += 1
        if not any_hit:
            print("  (no hits)")
    return counts


# ----------------------------------------------------------------------
# Section 2: GUI editors
# ----------------------------------------------------------------------
def section2_gui_editors(files: List[Path], root: Path) -> List[Path]:
    section("2. GUI editors potentially bound to reserved fields", char="-")
    gui_files = [f for f in files if "statable_gui" in f.parts]
    print(f"  GUI files scanned: {len(gui_files)}")
    print()

    suspects: List[Path] = []
    for f in gui_files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not GUI_EDITOR_HINTS.search(text):
            continue

        field_hits = {}
        for name, pat in RESERVED_FIELDS.items():
            hits = [i for i, _ in grep_file(f, pat)]
            if hits:
                field_hits[name] = hits

        if field_hits:
            suspects.append(f)

    if not suspects:
        print("  [OK] No GUI dialog references any reserved field.")
        return suspects

    print("  [WARN] The following GUI files reference reserved fields:")
    for f in suspects:
        rel = relpath(root, f)
        print()
        print(f"  >> {rel}")
        for name, pat in RESERVED_FIELDS.items():
            hits = grep_file(f, pat)
            if hits:
                lines = ", ".join(str(n) for n, _ in hits)
                print(f"       {name:<12} hits={len(hits)}  lines={lines}")
    return suspects


# ----------------------------------------------------------------------
# Section 3: key dialog inspection
# ----------------------------------------------------------------------
def section3_key_dialogs(root: Path) -> None:
    section("3. Key dialog inspection", char="-")
    for rel in KEY_DIALOGS:
        p = root / rel
        if not p.exists():
            print(f"  [MISSING] {rel}")
            continue
        print()
        print(f"  >> {rel}")
        any_field = False
        for name, pat in RESERVED_FIELDS.items():
            hits = grep_file(p, pat)
            if hits:
                any_field = True
                print(f"     [HIT] {name}:")
                for line_no, text in hits:
                    print(f"           L{line_no:<5} {text.strip()}")
        if not any_field:
            print("     (no reserved field references)")


# ----------------------------------------------------------------------
# Section 4: codegen usage
# ----------------------------------------------------------------------
def section4_codegen(root: Path) -> None:
    section("4. Code generation usage (expected: NONE)", char="-")
    codegen = root / "codegen"
    if not codegen.exists():
        print("  [SKIP] codegen/ not found")
        return

    files = [p for p in codegen.rglob("*.py")
             if not any(part in EXCLUDE_PARTS for part in p.parts)]
    for name, pat in RESERVED_FIELDS.items():
        total = 0
        hit_files: List[str] = []
        for f in files:
            hits = grep_file(f, pat)
            if hits:
                total += len(hits)
                hit_files.append(relpath(root, f))
        if total == 0:
            print(f"  [OK]   {name:<12} not used in codegen")
        else:
            print(f"  [WARN] {name:<12} used {total} time(s) in: "
                  f"{', '.join(hit_files)}")


# ----------------------------------------------------------------------
# Section 5: xml_io preservation
# ----------------------------------------------------------------------
def section5_xml_io(root: Path) -> None:
    section("5. XML I/O preservation (expected: ALL PRESENT)", char="-")
    xmlio = root / "statable" / "xml_io.py"
    if not xmlio.exists():
        print("  [SKIP] statable/xml_io.py not found")
        return
    for name, pat in RESERVED_FIELDS.items():
        hits = grep_file(xmlio, pat)
        if hits:
            print(f"  [OK]   {name:<12} preserved ({len(hits)} refs)")
        else:
            print(f"  [WARN] {name:<12} not found in xml_io.py")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find GUI editors for reserved fields (v3.7)."
    )
    parser.add_argument(
        "--root", default=".",
        help="Root of the code/ directory (default: current)",
    )
    parser.add_argument(
        "--gui-only", action="store_true",
        help="Scan statable_gui/ only",
    )
    parser.add_argument(
        "--context", type=int, default=2,
        help="(accepted for compatibility; ignored)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    dirs = SEARCH_DIRS_GUI if args.gui_only else SEARCH_DIRS_ALL

    section("StaTable: Reserved-field editor search")
    print(f"  Root        : {root}")
    print(f"  Search dirs : {', '.join(dirs)}")
    print(f"  GuiOnly     : {args.gui_only}")

    files = list(iter_python_files(root, dirs))
    print(f"  Python files: {len(files)}")
    if not files:
        print()
        print("[ERROR] No Python files found. Check --root.")
        return 1

    counts = section1_all_occurrences(files, root)
    suspects = section2_gui_editors(files, root)
    section3_key_dialogs(root)
    section4_codegen(root)
    section5_xml_io(root)

    section("Summary")
    print()
    print("  Reserved field occurrences (all dirs):")
    for name in RESERVED_FIELDS:
        print(f"    {name:<12} {counts[name]:>4}")

    print()
    if suspects:
        print("  [ACTION REQUIRED]")
        print("  The following GUI files still reference reserved fields:")
        for f in suspects:
            print(f"    - {relpath(root, f)}")
        print()
        print("  Review each file and decide whether to remove the")
        print("  UI editors for those fields, or leave them as-is")
        print("  (e.g. shared-library editors may intentionally keep them).")
        return 2

    print("  [OK] No GUI file references reserved fields.")
    print()
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())