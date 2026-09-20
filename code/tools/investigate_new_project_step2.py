#!/usr/bin/env python3
"""Second-pass investigation for the New Project feature.

Focus:
  Q1  ConfigManager.reset() body
  Q2  MainWindow ConfigManager references (with context)
  Q3  code_generation_settings_dialog config_manager origin
  Q4  open_project library swap block (lines 680-710)
  Q5  MainWindow __init__ sample-data block (lines 80-125)
  Q6  create_menus File menu block (for adding New action)
  Q7  Existing methods named new/clear/reset/create on MainWindow

Excludes tools/ from search to avoid self-reference.
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


class Mod:
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
        if self.tree:
            for n in ast.walk(self.tree):
                if isinstance(n, ast.ClassDef):
                    self.classes[n.name] = n

    def range_of(self, cls: str, m: str) -> Optional[Tuple[int, int]]:
        c = self.classes.get(cls)
        if not c:
            return None
        for item in c.body:
            if isinstance(item, ast.FunctionDef) and item.name == m:
                return (item.lineno, item.end_lineno or item.lineno)
        return None

    def show_range(self, start: int, end: int) -> List[str]:
        start = max(1, start)
        end = min(len(self.lines), end)
        return [f"{i:5d}| {self.lines[i-1]}" for i in range(start, end + 1)]


def find_mod(root: Path, basename: str, class_name: str = "") -> Optional[Mod]:
    for p in iter_py(root):
        if p.name != basename:
            continue
        m = Mod(p, root)
        if not class_name or class_name in m.classes:
            return m
    return None


# ---------------------------------------------------------------------------


def q1_config_reset(root: Path) -> List[str]:
    out = ["## Q1: ConfigManager.reset() body", ""]
    m = find_mod(root, "config.py", "ConfigManager")
    if m is None:
        out.append("config.py / ConfigManager not found")
        return out
    rng = m.range_of("ConfigManager", "reset")
    if rng is None:
        out.append("ConfigManager.reset 未定義")
        return out
    out.append(f"file: {m.rel}  lines {rng[0]}-{rng[1]}")
    out.append("```python")
    out.extend(m.show_range(*rng))
    out.append("```")
    return out


def q2_mainwindow_config_refs(root: Path) -> List[str]:
    out = ["## Q2: MainWindow の ConfigManager 参照（前後3行）", ""]
    m = find_mod(root, "main_window.py", "MainWindow")
    if m is None:
        out.append("main_window.py / MainWindow not found")
        return out
    regex = re.compile(r"config_manager|ConfigManager")
    hits = [i for i, ln in enumerate(m.lines, 1) if regex.search(ln)]
    out.append(f"hit lines: {hits}")
    out.append("")
    shown = set()
    for ln in hits:
        for j in range(max(1, ln - 3), min(len(m.lines), ln + 3) + 1):
            if j in shown:
                continue
            shown.add(j)
            out.append(f"{j:5d}| {m.lines[j-1]}")
        out.append("     | ---")
    return out


def q3_settings_dialog_origin(root: Path) -> List[str]:
    out = ["## Q3: code_generation_settings_dialog の config_manager 供給元", ""]
    out.append("### 定義側 (line 33-40)")
    m = find_mod(root, "code_generation_settings_dialog.py", "CodeGenerationSettingsDialog")
    if m:
        out.extend(m.show_range(33, 40))
    out.append("")
    out.append("### 呼び出し側 (全 .py から grep)")
    pat = re.compile(r"CodeGenerationSettingsDialog\(")
    for p in iter_py(root):
        if p.name == "code_generation_settings_dialog.py":
            continue
        src = read_text(p)
        for i, ln in enumerate(src.splitlines(), 1):
            if pat.search(ln):
                rel = str(p.relative_to(root))
                out.append(f"{rel}:{i}: {ln.strip()}")
    return out


def q4_open_project_swap(root: Path) -> List[str]:
    out = ["## Q4: open_project のライブラリ差し替えブロック", ""]
    m = find_mod(root, "main_window.py", "MainWindow")
    if m is None:
        return out + ["not found"]
    rng = m.range_of("MainWindow", "open_project")
    if rng is None:
        return out + ["open_project 未定義"]
    # 690付近を中心に表示
    out.append(f"open_project range: {rng[0]}-{rng[1]}")
    out.append("")
    out.extend(m.show_range(max(rng[0], 680), min(rng[1], 710)))
    return out


def q5_init_sample_block(root: Path) -> List[str]:
    out = ["## Q5: MainWindow.__init__ のサンプルデータ生成ブロック", ""]
    m = find_mod(root, "main_window.py", "MainWindow")
    if m is None:
        return out + ["not found"]
    rng = m.range_of("MainWindow", "__init__")
    if rng is None:
        return out + ["__init__ 未定義"]
    out.append(f"__init__ range: {rng[0]}-{rng[1]}")
    out.append("")
    out.extend(m.show_range(80, min(rng[1], 125)))
    return out


def q6_file_menu(root: Path) -> List[str]:
    out = ["## Q6: create_menus の File メニュー部分", ""]
    m = find_mod(root, "main_window.py", "MainWindow")
    if m is None:
        return out + ["not found"]
    rng = m.range_of("MainWindow", "create_menus")
    if rng is None:
        return out + ["create_menus 未定義"]
    out.append(f"create_menus range: {rng[0]}-{rng[1]}")
    out.append("")
    out.extend(m.show_range(rng[0], min(rng[0] + 40, rng[1])))
    return out


def q7_existing_methods(root: Path) -> List[str]:
    out = ["## Q7: MainWindow の new/clear/reset/create 系メソッド一覧", ""]
    m = find_mod(root, "main_window.py", "MainWindow")
    if m is None:
        return out + ["not found"]
    names = []
    c = m.classes.get("MainWindow")
    if c:
        for item in c.body:
            if isinstance(item, ast.FunctionDef):
                names.append((item.name, item.lineno))
    out.append("| method | line |")
    out.append("|--------|-----:|")
    for name, ln in names:
        out.append(f"| {name} | {ln} |")
    return out


def q8_library_holder_widgets(root: Path) -> List[str]:
    out = ["## Q8: ライブラリ参照を保持する子ウィジェット", ""]
    pat = re.compile(r"(role_function_library|condition_library|literal_library)\s*=")
    for p in iter_py(root):
        if "libcntrl" in str(p):
            continue
        src = read_text(p)
        for i, ln in enumerate(src.splitlines(), 1):
            if pat.search(ln) and "if" in ln and "else" in ln:
                rel = str(p.relative_to(root))
                out.append(f"{rel}:{i}: {ln.strip()}")
    return out


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

    sections: List[str] = ["# New Project Feature - Investigation Report (Step 2)", ""]
    sections.append(f"- root: `{root}`")
    sections.append("- excludes: `tools/` (self-reference)")
    sections.append("")
    for fn in (
        q1_config_reset,
        q2_mainwindow_config_refs,
        q3_settings_dialog_origin,
        q4_open_project_swap,
        q5_init_sample_block,
        q6_file_menu,
        q7_existing_methods,
        q8_library_holder_widgets,
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