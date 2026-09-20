#!/usr/bin/env python3
"""Final code-fact verification before implementing the New Project feature.

Verifies the remaining code-level facts (B-1 to B-6) that must be confirmed
before writing the implementation.

  B-1  _get_current_state_machine() return type / body
  B-2  CodeGenerationConfig() default values
  B-3  StateMachine() default values (esp. layer_priority)
  B-4  QKeySequence.StandardKey.New usage / availability
  B-5  MainWindow base class
  B-6  open_project() beginning - existing unsaved-changes check?

Read-only. Does NOT import PySide6.

Usage:
    cd code
    python tools/verify_new_project_code_facts.py --out ../verify_code_facts.md
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
        self.class_bases: Dict[str, List[str]] = {}
        if self.tree:
            for node in ast.walk(self.tree):
                if isinstance(node, ast.ClassDef):
                    self.classes[node.name] = node
                    bases = []
                    for b in node.bases:
                        try:
                            bases.append(ast.unparse(b))
                        except Exception:
                            bases.append("<?>")
                    self.class_bases[node.name] = bases

    def range_of(self, cls: str, method: str) -> Optional[Tuple[int, int]]:
        c = self.classes.get(cls)
        if not c:
            return None
        for item in c.body:
            if isinstance(item, ast.FunctionDef) and item.name == method:
                return (item.lineno, item.end_lineno or item.lineno)
        return None

    def show(self, start: int, end: int) -> List[str]:
        start = max(1, start)
        end = min(len(self.lines), end)
        return [f"{i:5d}| {self.lines[i-1]}" for i in range(start, end + 1)]


def find_module(root: Path, basename: str, class_name: str = "") -> Optional[ModuleInfo]:
    for p in iter_py(root):
        if p.name != basename:
            continue
        m = ModuleInfo(p, root)
        if not class_name or class_name in m.classes:
            return m
    return None


# ---------------------------------------------------------------------------
# B-1: _get_current_state_machine()
# ---------------------------------------------------------------------------

def b1_get_current_sm(root: Path) -> List[str]:
    out = ["## B-1: `MainWindow._get_current_state_machine()` の戻り値", ""]
    m = find_module(root, "main_window.py", "MainWindow")
    if m is None:
        return out + ["main_window.py / MainWindow 未発見"]

    rng = m.range_of("MainWindow", "_get_current_state_machine")
    if rng is None:
        out.append("**未定義**")
        return out

    out.append(f"lines {rng[0]}-{rng[1]}")
    out.append("")
    out.append("```python")
    out.extend(m.show(*rng))
    out.append("```")
    out.append("")

    # 戻り値解析
    body = "\n".join(m.lines[rng[0]-1:rng[1]])
    if re.search(r"return\s+None", body):
        out.append("**判定**: `None` を返す経路あり → `Optional[StateMachine]`")
        out.append("")
        out.append("**テスト注意**: `assert sm is not None` を先に置くこと。")
    else:
        out.append("**判定**: 常に `StateMachine` を返すと推定")
    out.append("")
    return out


# ---------------------------------------------------------------------------
# B-2: CodeGenerationConfig() default values
# ---------------------------------------------------------------------------

def b2_codegen_config(root: Path) -> List[str]:
    out = ["## B-2: `CodeGenerationConfig()` のデフォルト値", ""]
    m = find_module(root, "config.py", "CodeGenerationConfig")
    if m is None:
        return out + ["config.py / CodeGenerationConfig 未発見"]

    c = m.classes["CodeGenerationConfig"]
    out.append(f"lines {c.lineno}-{c.end_lineno or c.lineno}")
    out.append("")
    out.append("### フィールドとデフォルト値")
    out.append("")
    out.append("| line | field | default |")
    out.append("|-----:|-------|---------|")
    for item in c.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            name = item.target.id
            default = ast.unparse(item.value) if item.value else "(none)"
            safe = default.replace("|", "\\|")
            out.append(f"| {item.lineno} | `{name}` | `{safe}` |")
        elif isinstance(item, ast.Assign):
            for tgt in item.targets:
                if isinstance(tgt, ast.Name):
                    try:
                        default = ast.unparse(item.value)
                    except Exception:
                        default = "<?>"
                    safe = default.replace("|", "\\|")
                    out.append(f"| {item.lineno} | `{tgt.id}` | `{safe}` |")
    out.append("")

    # output_directory のデフォルト確認（テストで期待）
    body = "\n".join(m.lines[c.lineno-1: c.end_lineno or c.lineno])
    if re.search(r"output_directory\s*[:=]\s*str\s*=\s*[\"']{2}", body):
        out.append("**判定**: `output_directory` のデフォルトは空文字列 → テスト期待値 OK")
    elif re.search(r"output_directory\s*[:=][^\n]*=\s*[\"'][^\"']+[\"']", body):
        match = re.search(r"output_directory\s*[:=][^\n]*=\s*[\"']([^\"']+)[\"']", body)
        out.append(f"**警告**: `output_directory` のデフォルトは `\"{match.group(1)}\"` → テスト期待値を修正必要")
    else:
        out.append("**注意**: `output_directory` の明示的デフォルトなし → 実装を確認")
    out.append("")
    return out


# ---------------------------------------------------------------------------
# B-3: StateMachine() default values
# ---------------------------------------------------------------------------

def b3_state_machine_defaults(root: Path) -> List[str]:
    out = ["## B-3: `StateMachine()` のデフォルト値", ""]
    m = find_module(root, "state_machine.py", "StateMachine")
    if m is None:
        return out + ["state_machine.py / StateMachine 未発見"]

    c = m.classes["StateMachine"]
    out.append(f"lines {c.lineno}-{c.end_lineno or c.lineno}")
    out.append("")
    out.append("### フィールドとデフォルト値")
    out.append("")
    out.append("| line | field | default |")
    out.append("|-----:|-------|---------|")
    for item in c.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            name = item.target.id
            default = ast.unparse(item.value) if item.value else "(none)"
            safe = default.replace("|", "\\|")
            out.append(f"| {item.lineno} | `{name}` | `{safe}` |")
        elif isinstance(item, ast.Assign):
            for tgt in item.targets:
                if isinstance(tgt, ast.Name):
                    try:
                        default = ast.unparse(item.value)
                    except Exception:
                        default = "<?>"
                    safe = default.replace("|", "\\|")
                    out.append(f"| {item.lineno} | `{tgt.id}` | `{safe}` |")
    out.append("")

    # layer_priority の確認
    body = "\n".join(m.lines[c.lineno-1: c.end_lineno or c.lineno])
    if re.search(r"layer_priority[^\n]*=\s*5", body):
        out.append("**判定**: `layer_priority` デフォルト = 5 → テスト期待値 OK")
    else:
        out.append("**警告**: `layer_priority` デフォルトが 5 でない可能性 → 確認要")
    out.append("")

    # __init__ の signature 確認
    rng = m.range_of("StateMachine", "__init__")
    if rng:
        out.append("### `__init__` シグネチャ")
        out.append("")
        out.append("```python")
        out.extend(m.show(rng[0], min(rng[0] + 5, rng[1])))
        out.append("```")
        out.append("")
    return out


# ---------------------------------------------------------------------------
# B-4: QKeySequence.StandardKey.New usage
# ---------------------------------------------------------------------------

def b4_qkeysequence(root: Path) -> List[str]:
    out = ["## B-4: `QKeySequence` / ショートカットの既存使用", ""]
    out.append("### `QKeySequence` の使用箇所（全 .py）")
    out.append("")
    out.append("| file | line | text |")
    out.append("|------|-----:|------|")
    hits = 0
    for p in iter_py(root):
        src = read_text(p)
        for i, line in enumerate(src.splitlines(), 1):
            if "QKeySequence" in line:
                hits += 1
                rel = str(p.relative_to(root))
                txt = line.strip().replace("|", "\\|")
                out.append(f"| {rel} | {i} | `{txt}` |")
    if hits == 0:
        out.append("| (none) | | |")
    out.append("")

    out.append("### `setShortcut` の使用箇所")
    out.append("")
    out.append("| file | line | text |")
    out.append("|------|-----:|------|")
    hits2 = 0
    for p in iter_py(root):
        src = read_text(p)
        for i, line in enumerate(src.splitlines(), 1):
            if "setShortcut" in line:
                hits2 += 1
                rel = str(p.relative_to(root))
                txt = line.strip().replace("|", "\\|")
                out.append(f"| {rel} | {i} | `{txt}` |")
    if hits2 == 0:
        out.append("| (none) | | |")
    out.append("")

    # import 状況
    out.append("### `QKeySequence` import の有無")
    out.append("")
    for p in iter_py(root):
        src = read_text(p)
        for i, line in enumerate(src.splitlines(), 1):
            if re.search(r"from\s+PySide6\.QtGui\s+import.*QKeySequence", line) or \
               re.search(r"import\s+QKeySequence", line):
                rel = str(p.relative_to(root))
                out.append(f"- `{rel}:{i}`: `{line.strip()}`")
    out.append("")
    out.append("**判定**: QKeySequence を import しているファイルがなければ、")
    out.append("main_window.py に `from PySide6.QtGui import QKeySequence` を追加。")
    out.append("")
    return out


# ---------------------------------------------------------------------------
# B-5: MainWindow base class
# ---------------------------------------------------------------------------

def b5_mainwindow_base(root: Path) -> List[str]:
    out = ["## B-5: `MainWindow` の基底クラス", ""]
    m = find_module(root, "main_window.py", "MainWindow")
    if m is None:
        return out + ["main_window.py / MainWindow 未発見"]

    bases = m.class_bases.get("MainWindow", [])
    out.append(f"**基底クラス**: `{', '.join(bases)}`")
    out.append("")

    is_qmainwindow = any("QMainWindow" in b for b in bases)
    if is_qmainwindow:
        out.append("**判定**: `QMainWindow` 継承 → `statusBar()` 利用可能 ✅")
    else:
        out.append("**警告**: `QMainWindow` を継承していない可能性 → `statusBar()` 利用不可の恐れ")
    out.append("")

    # class 定義行
    c = m.classes["MainWindow"]
    out.append("### class 定義")
    out.append("")
    out.append("```python")
    out.extend(m.show(c.lineno, min(c.lineno + 10, c.end_lineno or c.lineno)))
    out.append("```")
    out.append("")
    return out


# ---------------------------------------------------------------------------
# B-6: open_project() beginning
# ---------------------------------------------------------------------------

def b6_open_project(root: Path) -> List[str]:
    out = ["## B-6: `open_project()` 冒頭の既存未保存確認", ""]
    m = find_module(root, "main_window.py", "MainWindow")
    if m is None:
        return out + ["main_window.py / MainWindow 未発見"]

    rng = m.range_of("MainWindow", "open_project")
    if rng is None:
        return out + ["open_project 未定義"]

    out.append(f"lines {rng[0]}-{rng[1]}")
    out.append("")
    out.append("### 冒頭 30 行")
    out.append("")
    out.append("```python")
    out.extend(m.show(rng[0], min(rng[0] + 30, rng[1])))
    out.append("```")
    out.append("")

    # QMessageBox の有無を冒頭 30 行で確認
    head = "\n".join(m.lines[rng[0]-1: min(rng[0] + 30, rng[1])])
    if "QMessageBox" in head:
        out.append("**判定**: 冒頭30行以内に `QMessageBox` あり → 既存確認と二重になる可能性")
        out.append("**対応**: `_maybe_save()` との統合を検討")
    else:
        out.append("**判定**: 冒頭30行以内に `QMessageBox` なし → 既存未保存確認なし")
        out.append("**対応**: `_maybe_save()` を冒頭に追加して問題なし ✅")
    out.append("")

    # save_project 呼び出しの有無
    if "save_project" in head:
        out.append("**注意**: 冒頭で `save_project` を呼んでいる → 詳細確認")
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

    sections: List[str] = ["# New Project Feature - Code Facts Verification (B-1 to B-6)", ""]
    sections.append(f"- root: `{root}`")
    sections.append("- excludes: `tools/`")
    sections.append("")
    for fn in (
        b1_get_current_sm,
        b2_codegen_config,
        b3_state_machine_defaults,
        b4_qkeysequence,
        b5_mainwindow_base,
        b6_open_project,
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