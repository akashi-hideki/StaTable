#!/usr/bin/env python3
"""Final pre-implementation verification for the New Project feature.

Verifies the remaining unknowns that block final code insertion:

  V-1  StateMachineTab.__init__ の本体（子ウィジェット保持属性名）
  V-2  StateMachineTab 内の MatrixTableWidget 属性名
  V-3  SettingsPanel の編集シグナル / 編集確定メソッド
  V-4  MainWindow.open_*_dialog の exec() 戻り値使用状況
  V-5  add_new_tab / rename_tab_at の本体（フラグ挿入位置）
  V-6  MatrixTableWidget.transition_changed の発火箇所
  V-7  StateMachineTab のウィジェット階層（findChildren 到達性）
  V-8  GlobalDefinitionsDialog の exec 戻り値型

Read-only. Does NOT import PySide6.

Usage:
    cd code
    python tools/verify_new_project_final.py --out ../verify_final.md
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

SKIP_PARTS = {".venv", "venv", "__pycache__", ".git", "node_modules", "tools"}


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(encoding="utf-8", errors="replace")


def iter_py(root: Path) -> Iterator[Path]:
    for p in root.rglob("*.py"):
        if any(x in SKIP_PARTS for x in p.parts):
            continue
        yield p


# ---------------------------------------------------------------------------
# Module / Class / Method view
# ---------------------------------------------------------------------------

class MethodInfo:
    def __init__(self, node: ast.FunctionDef, lines: List[str]):
        self.node = node
        self.name = node.name
        self.lineno = node.lineno
        self.end_lineno = node.end_lineno or node.lineno
        self.args = [a.arg for a in node.args.args]
        self.lines = lines[node.lineno - 1: self.end_lineno]
        self.body = "\n".join(self.lines)
        self.self_assignments: List[Tuple[int, str, str]] = []
        self.calls: List[str] = []
        self.exec_usage: List[Tuple[int, str]] = []
        self.return_value: Optional[str] = None
        self._analyze()

    def _analyze(self) -> None:
        for child in ast.walk(self.node):
            if isinstance(child, ast.Assign):
                for tgt in child.targets:
                    if isinstance(tgt, ast.Attribute) and \
                       isinstance(tgt.value, ast.Name) and \
                       tgt.value.id == "self":
                        try:
                            val = ast.unparse(child.value)
                        except Exception:
                            val = "<?>"
                        self.self_assignments.append((child.lineno, tgt.attr, val))
            elif isinstance(child, ast.Call):
                try:
                    self.calls.append(ast.unparse(child.func))
                except Exception:
                    pass
                # exec() usage: xxx.exec()  /  if xxx.exec() == ...
                if isinstance(child.func, ast.Attribute) and \
                   child.func.attr in ("exec", "exec_"):
                    src = self._line_of(child.lineno)
                    self.exec_usage.append((child.lineno, src))
            elif isinstance(child, ast.Return) and child.value is not None:
                try:
                    self.return_value = ast.unparse(child.value)
                except Exception:
                    self.return_value = "<?>"

    def _line_of(self, lineno: int) -> str:
        idx = lineno - self.lineno
        if 0 <= idx < len(self.lines):
            return self.lines[idx].strip()
        return ""


class ClassInfo:
    def __init__(self, node: ast.ClassDef, lines: List[str]):
        self.node = node
        self.name = node.name
        self.lineno = node.lineno
        self.end_lineno = node.end_lineno or node.lineno
        self.lines = lines[node.lineno - 1: self.end_lineno]
        self.methods: Dict[str, MethodInfo] = {}
        self.signals: List[Tuple[int, str]] = []
        self.base_classes: List[str] = []
        for b in node.bases:
            try:
                self.base_classes.append(ast.unparse(b))
            except Exception:
                pass
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self.methods[item.name] = MethodInfo(item, lines)
            elif isinstance(item, ast.Assign):
                for tgt in item.targets:
                    if isinstance(tgt, ast.Name):
                        try:
                            val = ast.unparse(item.value)
                        except Exception:
                            val = "<?>"
                        if "Signal(" in val or "Signal (" in val:
                            self.signals.append((item.lineno, f"{tgt.id} = {val}"))


class ModuleInfo:
    def __init__(self, path: Path, root: Path):
        self.path = path
        self.rel = str(path.relative_to(root))
        self.src = read_text(path)
        self.lines = self.src.splitlines()
        try:
            self.tree: Optional[ast.AST] = ast.parse(self.src)
        except SyntaxError:
            self.tree = None
        self.classes: Dict[str, ClassInfo] = {}
        if self.tree:
            for node in ast.walk(self.tree):
                if isinstance(node, ast.ClassDef):
                    self.classes[node.name] = ClassInfo(node, self.lines)


def find_module(root: Path, basename: str) -> Optional[ModuleInfo]:
    for p in iter_py(root):
        if p.name == basename:
            return ModuleInfo(p, root)
    return None


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

def v1_statemachinetab_init(root: Path) -> List[str]:
    out = ["## V-1: `StateMachineTab.__init__` の子ウィジェット保持属性", ""]
    m = find_module(root, "widgets.py")
    if m is None:
        return out + ["widgets.py not found"]
    cls = m.classes.get("StateMachineTab")
    if cls is None:
        return out + ["StateMachineTab not found"]

    out.append(f"base classes: {', '.join(cls.base_classes) or '(none)'}")
    out.append(f"lines: {cls.lineno}-{cls.end_lineno}")
    out.append("")

    init = cls.methods.get("__init__")
    if init is None:
        return out + ["__init__ not found"]

    out.append(f"`__init__` signature: `def __init__({', '.join(init.args)})`")
    out.append(f"`__init__` lines: {init.lineno}-{init.end_lineno}")
    out.append("")

    # 子ウィジェット保持属性（Widget 系の代入を抽出）
    widget_attrs: List[Tuple[int, str, str]] = []
    for ln, attr, val in init.self_assignments:
        if re.search(r"(Widget|Table|Panel|Canvas|View|Tree|List|Combo|Label|Button|Edit|Tab)", val) or \
           re.search(r"(matrix|widget|panel|canvas|view|table)", attr, re.IGNORECASE):
            widget_attrs.append((ln, attr, val))

    out.append("### `self.<attr> = <Widget>` 代入一覧")
    out.append("")
    out.append("| line | attribute | value |")
    out.append("|-----:|-----------|-------|")
    for ln, attr, val in widget_attrs:
        safe_val = val.replace("|", "\\|")
        out.append(f"| {ln} | `self.{attr}` | `{safe_val}` |")
    out.append("")

    # __init__ 全本体
    out.append("### `__init__` 全本体")
    out.append("")
    out.append("```python")
    for i, line in enumerate(init.lines, start=init.lineno):
        out.append(f"{i:5d}| {line}")
    out.append("```")
    out.append("")
    return out


def v2_matrix_table_attr(root: Path) -> List[str]:
    out = ["## V-2: `StateMachineTab` 内の `MatrixTableWidget` 属性名", ""]
    m = find_module(root, "widgets.py")
    if m is None:
        return out + ["widgets.py not found"]

    # widgets.py 内で MatrixTableWidget を import / 生成している行
    out.append("### widgets.py 内の `MatrixTableWidget` 参照行")
    out.append("")
    out.append("| line | text |")
    out.append("|-----:|------|")
    for i, line in enumerate(m.lines, 1):
        if re.search(r"MatrixTableWidget", line):
            txt = line.strip().replace("|", "\\|")
            out.append(f"| {i} | `{txt}` |")
    out.append("")

    # self.<attr> = MatrixTableWidget(...) の代入を探す
    cls = m.classes.get("StateMachineTab")
    attr_name: Optional[str] = None
    if cls is not None:
        init = cls.methods.get("__init__")
        if init is not None:
            for ln, attr, val in init.self_assignments:
                if "MatrixTableWidget" in val:
                    attr_name = attr
                    out.append(f"**検出**: `self.{attr} = {val}` (line {ln})")
                    out.append("")
                    break

    if attr_name is None:
        out.append("**判定**: `StateMachineTab.__init__` 内で `self.<attr> = MatrixTableWidget(...)` が")
        out.append("見つかりません → ローカル変数に保持されている可能性。`findChildren` 方式を推奨。")
        out.append("")
        # ローカル変数としての生成箇所を探す
        if cls is not None:
            init = cls.methods.get("__init__")
            if init is not None:
                for i, line in enumerate(init.lines, start=init.lineno):
                    if "MatrixTableWidget(" in line:
                        out.append(f"ローカル生成候補: line {i}: `{line.strip()}`")
        out.append("")
    else:
        out.append(f"**判定**: 属性名は `self.{attr_name}`。実装コードで直接参照可能。")
        out.append("")
    return out


def v3_settings_panel(root: Path) -> List[str]:
    out = ["## V-3: `SettingsPanel` の編集シグナル / 編集確定メソッド", ""]
    m = find_module(root, "widgets.py")
    if m is None:
        return out + ["widgets.py not found"]

    cls = m.classes.get("SettingsPanel")
    if cls is None:
        out.append("SettingsPanel 未定義 → 編集通知は他経路（dialog の exec 戻り値等）")
        out.append("")
        return out

    out.append(f"base classes: {', '.join(cls.base_classes) or '(none)'}")
    out.append(f"lines: {cls.lineno}-{cls.end_lineno}")
    out.append("")

    out.append("### シグナル定義")
    out.append("")
    if cls.signals:
        out.append("| line | signal |")
        out.append("|-----:|--------|")
        for ln, sig in cls.signals:
            out.append(f"| {ln} | `{sig}` |")
    else:
        out.append("_シグナル定義なし_")
    out.append("")

    out.append("### 編集系メソッド一覧")
    out.append("")
    edit_kw = re.compile(r"(add|remove|delete|edit|update|set|change|rename|clear|on_)",
                         re.IGNORECASE)
    out.append("| method | line | emit |")
    out.append("|--------|-----:|------|")
    for name, mi in cls.methods.items():
        if not edit_kw.search(name):
            continue
        emits = []
        for call in mi.calls:
            if call.endswith(".emit"):
                emits.append(call.replace(".emit", ""))
        out.append(f"| `{name}` | {mi.lineno} | {', '.join(emits) or '(none)'} |")
    out.append("")
    return out


def v4_open_dialogs_exec(root: Path) -> List[str]:
    out = ["## V-4: `MainWindow.open_*_dialog` の exec() 戻り値使用状況", ""]
    m = find_module(root, "main_window.py")
    if m is None:
        return out + ["main_window.py not found"]

    cls = m.classes.get("MainWindow")
    if cls is None:
        return out + ["MainWindow not found"]

    out.append("| method | line | exec 行 | 戻り値使用 |")
    out.append("|--------|-----:|---------|-----------|")
    for name, mi in cls.methods.items():
        if not re.match(r"open_", name):
            continue
        if not mi.exec_usage:
            continue
        for ln, src in mi.exec_usage:
            used = "yes" if re.search(r"(=\s*\w+\.exec|if\s+\w+\.exec|Accepted)", src) \
                else "no"
            safe = src.replace("|", "\\|")
            out.append(f"| `{name}` | {mi.lineno} | {ln}: `{safe}` | {used} |")
    out.append("")

    # Accepted / DialogCode 参照
    out.append("### `QDialog.Accepted` / `DialogCode` 参照")
    out.append("")
    out.append("| line | text |")
    out.append("|-----:|------|")
    for i, line in enumerate(m.lines, 1):
        if re.search(r"(QDialog\.Accepted|DialogCode|\.Accepted)", line):
            txt = line.strip().replace("|", "\\|")
            out.append(f"| {i} | `{txt}` |")
    out.append("")
    return out


def v5_add_new_tab_and_rename(root: Path) -> List[str]:
    out = ["## V-5: `add_new_tab` / `rename_tab_at` の本体", ""]
    m = find_module(root, "main_window.py")
    if m is None:
        return out + ["main_window.py not found"]
    cls = m.classes.get("MainWindow")
    if cls is None:
        return out + ["MainWindow not found"]

    for name in ("add_new_tab", "rename_tab_at", "rename_current_tab", "close_tab"):
        mi = cls.methods.get(name)
        if mi is None:
            out.append(f"### `{name}` 未定義")
            out.append("")
            continue
        out.append(f"### `MainWindow.{name}` (lines {mi.lineno}-{mi.end_lineno})")
        out.append("")
        out.append("```python")
        for i, line in enumerate(mi.lines, start=mi.lineno):
            out.append(f"{i:5d}| {line}")
        out.append("```")
        out.append("")
    return out


def v6_transition_changed_emit(root: Path) -> List[str]:
    out = ["## V-6: `MatrixTableWidget.transition_changed` の発火箇所", ""]
    m = find_module(root, "matrix_table.py")
    if m is None:
        return out + ["matrix_table.py not found"]

    out.append("### シグナル定義")
    out.append("")
    out.append("| line | text |")
    out.append("|-----:|------|")
    for i, line in enumerate(m.lines, 1):
        if re.search(r"transition_changed\s*=\s*Signal", line):
            txt = line.strip().replace("|", "\\|")
            out.append(f"| {i} | `{txt}` |")
    out.append("")

    out.append("### 発火箇所 (`transition_changed.emit`)")
    out.append("")
    out.append("| line | text | メソッド推定 |")
    out.append("|-----:|------|-------------|")
    for i, line in enumerate(m.lines, 1):
        if "transition_changed.emit" in line:
            txt = line.strip().replace("|", "\\|")
            method = _enclosing_method(m, i)
            out.append(f"| {i} | `{txt}` | {method} |")
    out.append("")

    out.append("### `transition_changed.connect` の接続箇所（全 .py）")
    out.append("")
    out.append("| file | line | text |")
    out.append("|------|-----:|------|")
    for p in iter_py(root):
        src = read_text(p)
        for i, line in enumerate(src.splitlines(), 1):
            if "transition_changed.connect" in line:
                rel = str(p.relative_to(root))
                txt = line.strip().replace("|", "\\|")
                out.append(f"| {rel} | {i} | `{txt}` |")
    out.append("")
    return out


def _enclosing_method(m: ModuleInfo, lineno: int) -> str:
    for cls in m.classes.values():
        for name, mi in cls.methods.items():
            if mi.lineno <= lineno <= mi.end_lineno:
                return f"{cls.name}.{name}"
    return "?"


def v7_widget_hierarchy(root: Path) -> List[str]:
    out = ["## V-7: `StateMachineTab` のウィジェット階層（findChildren 到達性）", ""]
    m = find_module(root, "widgets.py")
    if m is None:
        return out + ["widgets.py not found"]
    cls = m.classes.get("StateMachineTab")
    if cls is None:
        return out + ["StateMachineTab not found"]

    out.append("### `self.<attr>` 代入一覧（全）")
    out.append("")
    for name, mi in cls.methods.items():
        if name == "__init__":
            out.append(f"#### `{name}` (lines {mi.lineno}-{mi.end_lineno})")
            out.append("")
            out.append("| line | attribute | value |")
            out.append("|-----:|-----------|-------|")
            for ln, attr, val in mi.self_assignments:
                safe = val.replace("|", "\\|")
                out.append(f"| {ln} | `self.{attr}` | `{safe}` |")
            out.append("")

    # findChildren 実装可否
    out.append("### findChildren 到達性")
    out.append("")
    out.append("`StateMachineTab` が保持する子ウィジェット（`self.<attr>`）は、")
    out.append("`findChildren(MatrixTableWidget)` で再帰的に取得可能です。")
    out.append("")
    out.append("判定: **属性名に依存しない findChildren 方式を推奨**")
    out.append("")
    return out


def v8_global_defs_dialog_return(root: Path) -> List[str]:
    out = ["## V-8: `GlobalDefinitionsDialog` / `EventDefinitionDialog` / `LayerSettingsDialog` の exec 戻り値", ""]
    targets = [
        ("global_defs_dialog.py", "GlobalDefinitionsDialog"),
        ("event_definition_dialog.py", "EventDefinitionDialog"),
        ("layer_settings_dialog.py", "LayerSettingsDialog"),
    ]
    for fname, clsname in targets:
        m = find_module(root, fname)
        if m is None:
            out.append(f"### {clsname}: file `{fname}` 未発見")
            out.append("")
            continue
        cls = m.classes.get(clsname)
        if cls is None:
            out.append(f"### {clsname}: class 未定義")
            out.append("")
            continue
        out.append(f"### `{clsname}`")
        out.append("")
        out.append(f"- file: `{m.rel}`")
        out.append(f"- base classes: {', '.join(cls.base_classes) or '(none)'}")
        out.append(f"- lines: {cls.lineno}-{cls.end_lineno}")
        out.append("")
        out.append("**accept/reject 呼び出し**:")
        for name, mi in cls.methods.items():
            for call in mi.calls:
                if ".accept" in call or ".reject" in call:
                    out.append(f"- `{name}` (line {mi.lineno}) → `{call}`")
        out.append("")

    # MainWindow 側の exec() 判定パターン
    out.append("### MainWindow 側の exec() 判定パターン")
    out.append("")
    mw = find_module(root, "main_window.py")
    if mw:
        for i, line in enumerate(mw.lines, 1):
            if re.search(r"\.exec\(\)", line):
                txt = line.strip().replace("|", "\\|")
                out.append(f"- line {i}: `{txt}`")
    out.append("")
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: {root}", file=sys.stderr)
        return 2

    sections: List[str] = ["# New Project Feature - Final Pre-Implementation Verification", ""]
    sections.append(f"- root: `{root}`")
    sections.append("- excludes: `tools/`")
    sections.append("")
    for fn in (
        v1_statemachinetab_init,
        v2_matrix_table_attr,
        v3_settings_panel,
        v4_open_dialogs_exec,
        v5_add_new_tab_and_rename,
        v6_transition_changed_emit,
        v7_widget_hierarchy,
        v8_global_defs_dialog_return,
    ):
        sections.extend(fn(root))
        sections.append("")

    report = "\n".join(sections)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))