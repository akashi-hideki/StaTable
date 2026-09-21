#!/usr/bin/env python3
"""Inspect actual dependencies used in the StaTable codebase.

Scans all .py files under the specified directories, extracts import
statements via AST, and classifies them:

    - stdlib      : Python standard library
    - third_party : external packages (PySide6, pycparser, etc.)
    - local       : project-internal modules
    - unknown     : packages not yet classified (need manual review)

Usage:
    cd code
    python tools/inspect_dependencies.py
    python tools/inspect_dependencies.py --root .
    python tools/inspect_dependencies.py --out deps_report.md
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
import sysconfig
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DEFAULT_ROOTS = ["statable", "statable_gui", "codegen"]
EXCLUDE_PARTS = {"__pycache__", ".venv", "venv", ".git",
                 "build", "dist", "output", "logs",
                 "misra_report", "tools", "tests",
                 "sdk_doc_tools", "api_spec"}

# Known third-party top-level packages and their PyPI names.
KNOWN_THIRD_PARTY = {
    "PySide6": "PySide6",
    "shiboken6": "PySide6",
    "pycparser": "pycparser",
    "PIL": "Pillow",
    "pytest": "pytest",
    "setuptools": "setuptools",
    "numpy": "numpy",
    "yaml": "PyYAML",
}

# Local top-level names (project internal).
LOCAL_TOP_NAMES = {"statable", "statable_gui", "codegen"}


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def stdlib_names() -> Set[str]:
    """Return the set of standard library top-level module names."""
    names = set(sys.stdlib_module_names)
    # Additional names sometimes not listed
    names.update({"__future__", "typing_extensions"})
    return names


def iter_py_files(root: Path, subdirs: List[str]):
    for sub in subdirs:
        base = root / sub
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            if any(part in EXCLUDE_PARTS for part in p.parts):
                continue
            yield p


def extract_imports(path: Path) -> List[Tuple[int, str]]:
    """Return list of (line_number, top_level_module_name)."""
    try:
        src = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []

    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError:
        return []

    imports: List[Tuple[int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                imports.append((node.lineno, top))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top = node.module.split(".")[0]
                imports.append((node.lineno, top))
            elif node.level > 0:
                # Relative import (from . import x)
                imports.append((node.lineno, "<relative>"))

    return imports


def classify(top: str, stdlib: Set[str]) -> str:
    if top == "<relative>":
        return "local"
    if top in LOCAL_TOP_NAMES:
        return "local"
    if top in stdlib:
        return "stdlib"
    if top in KNOWN_THIRD_PARTY:
        return "third_party"
    return "unknown"


# ----------------------------------------------------------------------
# Main analysis
# ----------------------------------------------------------------------
def analyze(root: Path, subdirs: List[str]) -> Dict[str, dict]:
    stdlib = stdlib_names()

    # top -> {category, files: set, lines: [(file, line)]}
    result: Dict[str, dict] = {}

    def ensure(top: str) -> dict:
        if top not in result:
            result[top] = {
                "category": classify(top, stdlib),
                "files": set(),
                "count": 0,
            }
        return result[top]

    for path in iter_py_files(root, subdirs):
        rel = path.relative_to(root)
        for lineno, top in extract_imports(path):
            entry = ensure(top)
            entry["files"].add(str(rel))
            entry["count"] += 1

    return result


# ----------------------------------------------------------------------
# Report
# ----------------------------------------------------------------------
def render_report(result: Dict[str, dict], root: Path, subdirs: List[str]) -> str:
    out: List[str] = []
    out.append("# Dependency Inspection Report")
    out.append("")
    out.append(f"- Root: `{root}`")
    out.append(f"- Scanned: `{', '.join(subdirs)}`")
    out.append(f"- Unique top-level modules: **{len(result)}**")
    out.append("")

    # Group by category
    groups: Dict[str, List[Tuple[str, dict]]] = defaultdict(list)
    for top, entry in result.items():
        groups[entry["category"]].append((top, entry))

    # Order for presentation
    order = ["third_party", "unknown", "local", "stdlib"]

    for cat in order:
        items = groups.get(cat, [])
        if not items:
            continue
        items.sort(key=lambda x: (-x[1]["count"], x[0]))

        out.append(f"## {cat} ({len(items)})")
        out.append("")

        if cat == "third_party":
            out.append("External packages required at runtime or for tests.")
        elif cat == "unknown":
            out.append("Not classified. **Manual review required** — "
                       "these may be third-party or missing from the map.")
        elif cat == "local":
            out.append("Project-internal modules (`statable`, `statable_gui`, `codegen`).")
        elif cat == "stdlib":
            out.append("Python standard library (no installation needed).")

        out.append("")
        out.append("| module | imports | files |")
        out.append("|--------|--------:|------:|")
        for top, entry in items:
            out.append(f"| `{top}` | {entry['count']} | {len(entry['files'])} |")
        out.append("")

    # Mapping suggestion
    out.append("## Suggested `requirements.txt`")
    out.append("")
    out.append("Based on the `third_party` list above:")
    out.append("")
    out.append("```")
    seen_pypi: Set[str] = set()
    for top, entry in sorted(groups.get("third_party", [])):
        pypi = KNOWN_THIRD_PARTY.get(top, top)
        if pypi not in seen_pypi:
            seen_pypi.add(pypi)
            out.append(pypi)
    out.append("```")
    out.append("")

    return "\n".join(out)


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def parse_args(argv):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--root", default=".",
                    help="code root directory (default: .)")
    ap.add_argument("--dirs", default=",".join(DEFAULT_ROOTS),
                    help=f"comma-separated subdirs (default: {','.join(DEFAULT_ROOTS)})")
    ap.add_argument("--out", default="",
                    help="write report to file (default: stdout)")
    return ap.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    subdirs = [s.strip() for s in args.dirs.split(",") if s.strip()]

    result = analyze(root, subdirs)
    report = render_report(result, root, subdirs)

    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"wrote {args.out}")

    # Always print a short summary to stdout
    print()
    print("=" * 60)
    print("  Dependency Summary")
    print("=" * 60)

    groups: Dict[str, int] = defaultdict(int)
    for top, entry in result.items():
        groups[entry["category"]] += 1

    for cat in ["third_party", "unknown", "local", "stdlib"]:
        print(f"  {cat:<12}: {groups.get(cat, 0)}")

    print()
    print("  Third-party packages:")
    for top, entry in sorted(
        [(t, e) for t, e in result.items() if e["category"] == "third_party"]
    ):
        pypi = KNOWN_THIRD_PARTY.get(top, top)
        print(f"    - {top} (PyPI: {pypi}, imports: {entry['count']})")

    unknown = [
        (t, e) for t, e in result.items() if e["category"] == "unknown"
    ]
    if unknown:
        print()
        print("  ⚠ Unknown (manual review):")
        for top, entry in sorted(unknown):
            files = list(sorted(entry["files"]))[:3]
            print(f"    - {top} (imports: {entry['count']}, e.g. {files})")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))