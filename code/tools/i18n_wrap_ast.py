# code/tools/i18n_wrap_ast.py
"""AST-based bulk-wrap of GUI strings with self.tr() for i18n.

Safety:
  - Uses Python's AST for precise detection
  - Only wraps ast.Constant string nodes
  - Skips f-strings, variables, already-wrapped strings
  - VERIFIES the result parses before writing
  - Idempotent (skips already wrapped)

Usage:
    cd code
    python tools/i18n_wrap_ast.py                       # dry-run
    python tools/i18n_wrap_ast.py --apply               # apply
    python tools/i18n_wrap_ast.py --apply path.py       # one file
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent
GUI = CODE / "statable_gui"

# name -> list of arg indices to wrap
TARGETS = {
    "QLabel": [0],
    "QPushButton": [0],
    "QCheckBox": [0],
    "QRadioButton": [0],
    "QGroupBox": [0],
    "QToolButton": [0],
    "setWindowTitle": [0],
    "setToolTip": [0],
    "setStatusTip": [0],
    "setWhatsThis": [0],
    "setText": [0],
    "setPlaceholderText": [0],
    "addItem": [0],
}


def get_call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def is_self_tr(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "tr"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "self"
    )


class Finder(ast.NodeVisitor):
    def __init__(self) -> None:
        self.hits: list[ast.Constant] = []

    def visit_Call(self, node: ast.Call) -> None:
        self.generic_visit(node)
        if is_self_tr(node):
            return
        name = get_call_name(node)
        if name not in TARGETS:
            return
        for idx in TARGETS[name]:
            if idx >= len(node.args):
                continue
            arg = node.args[idx]
            if not isinstance(arg, ast.Constant):
                continue
            if not isinstance(arg.value, str):
                continue
            self.hits.append(arg)


def wrap(source: str, hits: list[ast.Constant]) -> str:
    lines = source.splitlines(keepends=True)
    sorted_hits = sorted(
        hits,
        key=lambda h: (h.lineno, h.col_offset),
        reverse=True,
    )
    for arg in sorted_hits:
        l1 = arg.lineno - 1
        c1 = arg.col_offset
        l2 = arg.end_lineno - 1
        c2 = arg.end_col_offset
        if l1 == l2:
            line = lines[l1]
            lines[l1] = line[:c2] + ")" + line[c2:]
            line = lines[l1]
            lines[l1] = line[:c1] + "self.tr(" + line[c1:]
        else:
            lines[l2] = lines[l2][:c2] + ")" + lines[l2][c2:]
            lines[l1] = lines[l1][:c1] + "self.tr(" + lines[l1][c1:]
    return "".join(lines)


def process(path: Path, apply: bool) -> tuple[int, str]:
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return -1, f"source parse error: {e}"

    finder = Finder()
    finder.visit(tree)
    if not finder.hits:
        return 0, ""

    new_source = wrap(source, finder.hits)

    # SAFETY: never write unless result parses
    try:
        ast.parse(new_source)
    except SyntaxError as e:
        return -2, f"WRAP WOULD BREAK SYNTAX: {e}"

    if apply:
        path.write_text(new_source, encoding="utf-8")
    return len(finder.hits), ""


def resolve(f: str) -> Path:
    p = Path(f)
    if not p.is_absolute():
        p = (CODE / p).resolve()
    return p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("files", nargs="*")
    args = ap.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  i18n_wrap_ast  [{mode}]")
    print("=" * 70)

    if args.files:
        targets = [resolve(f) for f in args.files]
    else:
        targets = sorted(GUI.rglob("*.py"))

    total = 0
    changed = 0
    for f in targets:
        if not f.exists():
            continue
        n, err = process(f, args.apply)
        if n < 0:
            print(f"  [SKIP] {f.relative_to(CODE)}: {err}")
            continue
        if n == 0:
            continue
        changed += 1
        total += n
        print(f"  {f.relative_to(CODE)}: {n}")

    print()
    print(f"files changed: {changed}, replacements: {total}")
    if not args.apply:
        print("[DRY-RUN] no file written; pass --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())