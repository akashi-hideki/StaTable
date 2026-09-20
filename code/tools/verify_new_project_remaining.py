#!/usr/bin/env python3
"""Verify remaining items (R-1/R-2/R-3) before implementing New Project.

R-1: close_all_tabs() / close_tab() の確認ダイアログ有無
R-2: save_project() の戻り値（bool か None か）
R-3: StateMachineTab の編集シグナル（setWindowModified のフック候補）

Read-only. Does NOT import PySide6.

Usage:
    cd code
    python tools/verify_new_project_remaining.py --out ../verify_remaining.md
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
# AST utilities
# ---------------------------------------------------------------------------

class FuncInfo:
    """Detailed view of a function/method."""

    def __init__(self, node: ast.FunctionDef, module_lines: List[str]):
        self.node = node
        self.name = node.name
        self.lineno = node.lineno
        self.end_lineno = node.end_lineno or node.lineno
        self.lines = module_lines[node.lineno - 1: self.end_lineno]
        self.returns: List[Tuple[int, str]] = []  # (line, source)
        self.return_values: List[Optional[str]] = []
        self.calls: List[str] = []
        self.has_qmessagebox = False
        self.qmessagebox_buttons: List[str] = []
        self.emit_signals: List[str] = []
        self._analyze()

    def _analyze(self) -> None:
        for child in ast.walk(self.node):
            if isinstance(child, ast.Return):
                line = self.node.lineno + (child.lineno - self.node.lineno)
                src = self.lines[child.lineno - self.node.lineno].strip() \
                    if child.lineno - self.node.lineno < len(self.lines) else ""
                self.returns.append((child.lineno, src))
                if child.value is None:
                    self.return_values.append(None)
                else:
                    try:
                        self.return_values.append(ast.unparse(child.value))
                    except Exception:
                        self.return_values.append("<?>")
            elif isinstance(child, ast.Call):
                try:
                    self.calls.append(ast.unparse(child.func))
                except Exception:
                    self.calls.append("<?>")
                # QMessageBox detection
                fname = ""
                try:
                    fname = ast.unparse(child.func)
                except Exception:
                    pass
                if "QMessageBox" in fname:
                    self.has_qmessagebox = True
                    # Extract button args
                    for arg in child.args:
                        try:
                            a = ast.unparse(arg)
                        except Exception:
                            continue
                        if "QMessageBox" in a and "Box" not in a:
                            # e.g. QMessageBox.Save
                            self.qmessagebox_buttons.append(a)
            elif isinstance(child, ast.Attribute):
                if child.attr == "emit":
                    try:
                        self.emit_signals.append(ast.unparse(child.value))
                    except Exception:
                        pass

    def signature(self) -> str:
        args = [a.arg for a in self.node.args.args]
        return f"def {self.name}({', '.join(args)})"

    def return_kind(self) -> str:
        """Classify the function's return behavior."""
        vals = self.return_values
        if not vals:
            return "no-return"
        has_value = any(v is not None for v in vals)
        has_bare = any(v is None for v in vals)
        if has_value and has_bare:
            return "mixed"
        if has_value:
            # Check if all are True/False
            if all(v in ("True", "False") for v in vals if v is not None):
                return "bool-literal"
            return "value"
        return "bare-only"


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
        self.classes: Dict[str, ast.ClassDef] = {}
        self.functions: Dict[str, FuncInfo] = {}
        self.class_methods: Dict[str, Dict[str, FuncInfo]] = {}
        if self.tree:
            for node in ast.walk(self.tree):
                if isinstance(node, ast.ClassDef):
                    self.classes[node.name] = node
                    self.class_methods[node.name] = {}
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            self.class_methods[node.name][item.name] = FuncInfo(item, self.lines)
                elif isinstance(node, ast.FunctionDef) and isinstance(
                    getattr(node, "parent", None), type(None)
                ):
                    pass
            # top-level functions
            for node in self.tree.body:
                if isinstance(node, ast.FunctionDef):
                    self.functions[node.name] = FuncInfo(node, self.lines)


def find_module(root: Path, basename: str) -> Optional[ModuleInfo]:
    for p in iter_py(root):
        if p.name == basename:
            return ModuleInfo(p, root)
    return None


# ---------------------------------------------------------------------------
# Investigations
# ---------------------------------------------------------------------------

def verify_r1_close_tabs(root: Path) -> List[str]:
    out = ["## R-1: `close_all_tabs` / `close_tab` の確認ダイアログ有無", ""]
    m = find_module(root, "main_window.py")
    if m is None:
        return out + ["main_window.py not found"]

    for method_name in ("close_all_tabs", "close_tab"):
        methods = m.class_methods.get("MainWindow", {})
        if method_name not in methods:
            out.append(f"### MainWindow.{method_name}: **未定義**")
            out.append("")
            continue
        fi = methods[method_name]
        out.append(f"### MainWindow.{method_name} (lines {fi.lineno}-{fi.end_lineno})")
        out.append("")
        out.append(f"- signature: `{fi.signature()}`")
        out.append(f"- QMessageBox 使用: **{'あり' if fi.has_qmessagebox else 'なし'}**")
        if fi.qmessagebox_buttons:
            out.append(f"- ボタン: {', '.join(fi.qmessagebox_buttons)}")
        out.append(f"- return kind: `{fi.return_kind()}`")
        out.append("")
        out.append("```python")
        for i, line in enumerate(fi.lines, start=fi.lineno):
            out.append(f"{i:5d}| {line}")
        out.append("```")
        out.append("")

    # close_tab が close_all_tabs から呼ばれているか
    if "close_all_tabs" in m.class_methods.get("MainWindow", {}):
        fi = m.class_methods["MainWindow"]["close_all_tabs"]
        out.append("### 呼び出し解析")
        if "self.close_tab" in "\n".join(fi.lines):
            out.append("- `close_all_tabs` → `self.close_tab` 呼び出しあり")
        else:
            out.append("- `close_all_tabs` → `self.close_tab` 呼び出し**なし**（直接 removeTab の可能性）")
        out.append("")

    # 全モジュールで close_all_tabs / close_tab の利用箇所
    out.append("### 利用箇所")
    out.append("")
    out.append("| file | line | text |")
    out.append("|------|-----:|------|")
    for p in iter_py(root):
        src = read_text(p)
        for i, line in enumerate(src.splitlines(), 1):
            if re.search(r"\bclose_all_tabs\b|\bclose_tab\b", line):
                rel = str(p.relative_to(root))
                txt = line.strip().replace("|", "\\|")
                out.append(f"| {rel} | {i} | `{txt}` |")
    out.append("")
    return out


def verify_r2_save_project(root: Path) -> List[str]:
    out = ["## R-2: `save_project()` の戻り値解析", ""]
    m = find_module(root, "main_window.py")
    if m is None:
        return out + ["main_window.py not found"]

    methods = m.class_methods.get("MainWindow", {})
    if "save_project" not in methods:
        return out + ["MainWindow.save_project 未定義"]

    fi = methods["save_project"]
    out.append(f"### MainWindow.save_project (lines {fi.lineno}-{fi.end_lineno})")
    out.append("")
    out.append(f"- signature: `{fi.signature()}`")
    out.append(f"- return kind: **`{fi.return_kind()}`**")
    out.append(f"- return 文の数: {len(fi.returns)}")
    out.append("")
    out.append("### Return 文一覧")
    out.append("")
    out.append("| line | source | value |")
    out.append("|-----:|--------|-------|")
    for (ln, src), val in zip(fi.returns, fi.return_values):
        v = val if val is not None else "**None (bare)**"
        s = src.replace("|", "\\|")
        out.append(f"| {ln} | `{s}` | `{v}` |")
    out.append("")

    # QMessageBox の有無
    out.append(f"### QMessageBox 使用: **{'あり' if fi.has_qmessagebox else 'なし'}**")
    out.append("")

    # save_project が bool 化可能か判定
    out.append("### bool 化判定")
    out.append("")
    kind = fi.return_kind()
    if kind == "no-return":
        out.append("- 現状: **return 文なし** → 成功/失敗を返すには全 return を追加する必要あり")
        out.append("- 推奨: 成功パスに `return True`、失敗パスに `return False` を追加")
    elif kind == "bare-only":
        out.append("- 現状: **bare return のみ** → 呼び出し側は常に `None` を受け取る")
        out.append("- 推奨: 各 bare return を `return False` に、成功パスに `return True` を追加")
    elif kind == "bool-literal":
        out.append("- 現状: **既に bool を返却** → そのまま利用可能")
    elif kind == "value":
        out.append("- 現状: **値を返却**（bool 以外） → 呼び出し側で解釈が必要")
    elif kind == "mixed":
        out.append("- 現状: **mixed**（bare と value が混在） → 正規化が必要")
    out.append("")

    # save_project の利用箇所
    out.append("### save_project の利用箇所（戻り値の扱いを確認）")
    out.append("")
    out.append("| file | line | text | 戻り値使用 |")
    out.append("|------|-----:|------|-----------|")
    for p in iter_py(root):
        src = read_text(p)
        for i, line in enumerate(src.splitlines(), 1):
            if "save_project" in line and "def save_project" not in line:
                rel = str(p.relative_to(root))
                txt = line.strip().replace("|", "\\|")
                used = "yes" if re.search(r"=\s*self\.save_project|return\s+self\.save_project", line) else "no"
                out.append(f"| {rel} | {i} | `{txt}` | {used} |")
    out.append("")

    # 本体表示
    out.append("### 本体")
    out.append("")
    out.append("```python")
    for i, line in enumerate(fi.lines, start=fi.lineno):
        out.append(f"{i:5d}| {line}")
    out.append("```")
    out.append("")
    return out


def verify_r3_edit_signals(root: Path) -> List[str]:
    out = ["## R-3: StateMachineTab の編集シグナル / 編集確定メソッド", ""]

    # StateMachineTab 定義
    m = find_module(root, "widgets.py")
    if m is None:
        return out + ["widgets.py not found"]

    if "StateMachineTab" not in m.classes:
        return out + ["StateMachineTab 未定義"]

    out.append("### StateMachineTab のシグナル定義")
    out.append("")
    out.append("| signal | line | 意味推定 |")
    out.append("|--------|-----:|---------|")
    sig_pattern = re.compile(r"(\w+)\s*=\s*Signal\(")
    tab_cls = m.classes["StateMachineTab"]
    for i in range(tab_cls.lineno, tab_cls.end_lineno or tab_cls.lineno):
        line = m.lines[i - 1]
        mo = sig_pattern.search(line)
        if mo:
            out.append(f"| `{mo.group(1)}` | {i} | — |")
    out.append("")

    # Signal が 1 つもなければ注意
    if "Signal" not in "\n".join(m.lines[tab_cls.lineno - 1: (tab_cls.end_lineno or tab_cls.lineno)]):
        out.append("**注意**: StateMachineTab に Signal 定義なし → `dataModified` を新規追加する必要あり")
        out.append("")

    # StateMachineTab のメソッド一覧（編集操作候補）
    out.append("### StateMachineTab のメソッド一覧")
    out.append("")
    out.append("| method | line | 編集系推定 |")
    out.append("|--------|-----:|-----------|")
    edit_keywords = re.compile(
        r"(add|remove|delete|edit|update|set|change|rename|clear|modify|on_)",
        re.IGNORECASE,
    )
    for name, fi in m.class_methods.get("StateMachineTab", {}).items():
        flag = "✓" if edit_keywords.search(name) else ""
        out.append(f"| `{name}` | {fi.lineno} | {flag} |")
    out.append("")

    # 各編集メソッドで emit しているシグナル
    out.append("### 編集系メソッドの emit 状況")
    out.append("")
    for name, fi in m.class_methods.get("StateMachineTab", {}).items():
        if not edit_keywords.search(name):
            continue
        if fi.emit_signals:
            out.append(f"- **{name}** (line {fi.lineno}): emits {', '.join(fi.emit_signals)}")
        else:
            out.append(f"- **{name}** (line {fi.lineno}): emit なし")
    out.append("")

    # MainWindow が StateMachineTab のシグナルに connect しているか
    mw = find_module(root, "main_window.py")
    if mw is not None:
        out.append("### MainWindow での StateMachineTab シグナル接続")
        out.append("")
        out.append("| line | text |")
        out.append("|-----:|------|")
        for i, line in enumerate(mw.lines, 1):
            if re.search(r"tab\.\w+\.connect|\.dataModified|\.modified|StateMachineTab\(", line):
                txt = line.strip().replace("|", "\\|")
                out.append(f"| {i} | `{txt}` |")
        out.append("")

    # MatrixTableWidget の編集シグナル
    out.append("### MatrixTableWidget の編集系シグナル")
    out.append("")
    mm = find_module(root, "matrix_table.py")
    if mm is not None:
        cls = mm.classes.get("MatrixTableWidget")
        if cls:
            out.append("| signal | line |")
            out.append("|--------|-----:|")
            for i in range(cls.lineno, cls.end_lineno or cls.lineno):
                line = mm.lines[i - 1]
                mo = sig_pattern.search(line)
                if mo:
                    out.append(f"| `{mo.group(1)}` | {i} |")
            out.append("")
            out.append("**editingFinished / dataChanged 系メソッド**:")
            out.append("")
            for name, fi in mm.class_methods.get("MatrixTableWidget", {}).items():
                if re.search(r"(edit|commit|change|update|on_)", name, re.IGNORECASE):
                    emits = ", ".join(fi.emit_signals) if fi.emit_signals else "(emit なし)"
                    out.append(f"- `{name}` (line {fi.lineno}) → {emits}")
            out.append("")

    # 推奨フック候補
    out.append("### `setWindowModified(True)` を呼ぶべき場所（推奨）")
    out.append("")
    out.append("| 経路 | 実装場所 | 方法 |")
    out.append("|------|---------|------|")
    out.append("| セル編集 | `MatrixTableWidget` の編集確定 | `dataChanged` シグナル経由で MainWindow に伝播 |")
    out.append("| 状態/イベント編集 | `SettingsPanel` | 同様にシグナル化 |")
    out.append("| タブ追加/削除 | `MainWindow.add_new_tab` / `close_tab` | メソッド内で直接 `setWindowModified(True)` |")
    out.append("| グローバル定義 | `GlobalDefinitionsDialog.exec()` 後 | 戻り値 `Accepted` で判定 |")
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

    sections: List[str] = ["# New Project Feature - Remaining Verification (R-1/R-2/R-3)", ""]
    sections.append(f"- root: `{root}`")
    sections.append("- excludes: `tools/` (self-reference)")
    sections.append("")
    sections.extend(verify_r1_close_tabs(root))
    sections.append("")
    sections.extend(verify_r2_save_project(root))
    sections.append("")
    sections.extend(verify_r3_edit_signals(root))

    report = "\n".join(sections)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))