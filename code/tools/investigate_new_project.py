#!/usr/bin/env python3
"""StaTable New Project feature - pre-implementation investigation tool.

Read-only static analysis. Does NOT import PySide6, does NOT instantiate MainWindow.

Usage:
    cd code
    python tools/investigate_new_project.py
    python tools/investigate_new_project.py --out report.md
    python tools/investigate_new_project.py --root /path/to/code

Purpose:
    Verify the 10 design decisions for the "New Project" feature against the
    actual codebase, before implementation begins.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class Hit:
    file: str
    line: int
    text: str
    note: str = ""


@dataclass
class Section:
    key: str
    title: str
    hits: List[Hit] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    risk: str = "info"  # info | caution | blocker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SKIP_PARTS = {".venv", "venv", "__pycache__", ".git", "node_modules"}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def iter_py_files(root: Path) -> Iterator[Path]:
    for p in root.rglob("*.py"):
        if any(part in SKIP_PARTS for part in p.parts):
            continue
        yield p


def grep(path: Path, pattern: str, flags: int = 0) -> List[Tuple[int, str]]:
    regex = re.compile(pattern, flags)
    result: List[Tuple[int, str]] = []
    for i, line in enumerate(read_text(path).splitlines(), 1):
        if regex.search(line):
            result.append((i, line.rstrip()))
    return result


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# AST analysis of a single Python file
# ---------------------------------------------------------------------------

class ModuleInfo:
    """Lightweight AST view of one module."""

    def __init__(self, path: Path, root: Path):
        self.path = path
        self.rel_path = rel(path, root)
        self.source = read_text(path)
        self.lines = self.source.splitlines()
        self.tree: Optional[ast.AST] = None
        try:
            self.tree = ast.parse(self.source, filename=str(path))
        except SyntaxError:
            self.tree = None
        self.classes: Dict[str, ast.ClassDef] = {}
        self.methods: Dict[str, Dict[str, ast.FunctionDef]] = {}
        self.imports: List[str] = []
        self.assignments: List[Tuple[int, str, str]] = []  # line, target, value_repr
        if self.tree is not None:
            self._walk()

    def _walk(self) -> None:
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                self.classes[node.name] = node
                self.methods.setdefault(node.name, {})
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        self.methods[node.name][item.name] = item
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = getattr(node, "module", None) or ""
                names = ",".join(a.name for a in node.names)
                self.imports.append(f"{mod}:{names}")
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute):
                        tgt = f"{self._expr(target.value)}.{target.attr}"
                    elif isinstance(target, ast.Name):
                        tgt = target.id
                    else:
                        continue
                    self.assignments.append((node.lineno, tgt, self._expr(node.value)))

    def _expr(self, node: ast.AST) -> str:
        try:
            return ast.unparse(node)
        except Exception:
            return "<?>"

    def method_lines(self, class_name: str, method_name: str) -> List[Tuple[int, str]]:
        m = self.methods.get(class_name, {}).get(method_name)
        if not m or m.end_lineno is None:
            return []
        return [(i, self.lines[i - 1]) for i in range(m.lineno, m.end_lineno + 1)]

    def has_method(self, class_name: str, method_name: str) -> bool:
        return method_name in self.methods.get(class_name, {})


# ---------------------------------------------------------------------------
# Investigations
# ---------------------------------------------------------------------------

class Investigator:
    def __init__(self, root: Path):
        self.root = root
        self.sections: List[Section] = []
        self.modules: Dict[str, ModuleInfo] = {}
        self._cache_modules()

    def _cache_modules(self) -> None:
        for p in iter_py_files(self.root):
            key = rel(p, self.root)
            self.modules[key] = ModuleInfo(p, self.root)

    # -- utility --------------------------------------------------------------

    def _find(self, basename: str) -> List[ModuleInfo]:
        return [m for k, m in self.modules.items() if Path(k).name == basename]

    def _main_window(self) -> Optional[ModuleInfo]:
        matches = self._find("main_window.py")
        for m in matches:
            if "MainWindow" in m.classes:
                return m
        return matches[0] if matches else None

    def _grep_all(self, pattern: str, flags: int = 0) -> List[Hit]:
        hits: List[Hit] = []
        for m in self.modules.values():
            for line_no, text in grep(Path(m.rel_path if False else m.path), pattern, flags):
                hits.append(Hit(m.rel_path, line_no, text))
        return hits

    # -- investigations -------------------------------------------------------

    def inv_01_startup_sample(self) -> Section:
        s = Section("1", "起動時サンプル維持 (決定: 維持)")
        mw = self._main_window()
        if mw is None:
            s.notes.append("main_window.py が見つかりません")
            s.risk = "blocker"
            return s
        # __init__ 内のサンプル生成呼び出し
        for line_no, text in mw.method_lines("MainWindow", "__init__"):
            if re.search(r"create_sample_|sample_", text):
                s.hits.append(Hit(mw.rel_path, line_no, text, "sample data call"))
        # 起動シーケンスのメソッド定義
        for name in ("create_sample_state_machine", "create_sample_global_defs",
                     "add_state_machine_tab"):
            if mw.has_method("MainWindow", name):
                s.notes.append(f"MainWindow.{name} 存在")
        # sample_data.py の公開関数
        for m in self._find("sample_data.py"):
            for node in m.tree.body if m.tree else []:
                if isinstance(node, ast.FunctionDef) and node.name.startswith("create_sample"):
                    s.notes.append(f"{m.rel_path}: {node.name} (line {node.lineno})")
        return s

    def inv_02_tab_count(self) -> Section:
        s = Section("2", "新規時タブ数: 1個 Application (決定済)")
        mw = self._main_window()
        if mw is None:
            s.risk = "blocker"
            return s
        for line_no, text in mw.method_lines("MainWindow", "add_state_machine_tab"):
            s.hits.append(Hit(mw.rel_path, line_no, text, "tab add signature"))
        # StateMachine のデフォルト引数
        for m in self._find("state_machine.py"):
            for node in m.tree.body if m.tree else []:
                if isinstance(node, ast.ClassDef) and node.name == "StateMachine":
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign):
                            tgt = item.target.id if isinstance(item.target, ast.Name) else "?"
                            if tgt in ("layer_name", "layer_priority", "states", "events", "transitions"):
                                s.notes.append(
                                    f"StateMachine.{tgt} default = {m._expr(item.value)}"
                                )
        return s

    def inv_03_unsaved_confirmation(self) -> Section:
        s = Section("3", "未保存確認: New / Open / Close (推奨)")
        mw = self._main_window()
        if mw is None:
            s.risk = "blocker"
            return s
        for name in ("save_project", "open_project", "closeEvent", "maybe_save",
                     "_maybe_save", "on_save", "on_open", "file_save", "file_open"):
            if mw.has_method("MainWindow", name):
                for line_no, text in mw.method_lines("MainWindow", name):
                    if re.search(r"QMessageBox|Save|Discard|Cancel|SaveChanges", text):
                        s.hits.append(Hit(mw.rel_path, line_no, text, f"in {name}"))
        # 既存の未保存確認ダイアログ
        for h in self._grep_all(r"QMessageBox\.(warning|question).*[Ss]ave"):
            s.hits.append(Hit(h.file, h.line, h.text, "existing confirm dialog"))
        # closeEvent の有無
        if not mw.has_method("MainWindow", "closeEvent"):
            s.notes.append("closeEvent 未実装 → 新規追加が必要")
            s.risk = "caution"
        return s

    def inv_04_window_modified(self) -> Section:
        s = Section("4", "windowModified 流用 (決定済)")
        hits = self._grep_all(r"(setWindowModified|isWindowModified|windowModified)")
        s.hits = hits
        if not hits:
            s.notes.append("windowModified は未使用 → 新規導入")
        else:
            s.notes.append(f"既存使用箇所: {len(hits)}")
        return s

    def inv_05_libcntrl_libraries(self) -> Section:
        s = Section("5", "libcntrl ライブラリ保持 (決定済: 要確認)")
        mw = self._main_window()
        if mw is None:
            return s
        # MainWindow 内のライブラリ属性代入
        for line_no, target, value in mw.assignments:
            if target.startswith("self.") and re.search(
                r"(role_function_library|condition_library|literal_library)",
                target, re.IGNORECASE
            ):
                s.hits.append(Hit(mw.rel_path, line_no,
                                  f"{target} = {value}", "MainWindow attr"))
        # libcntrl 内のクラス定義確認
        for m in self.modules.values():
            if "libcntrl" in m.rel_path:
                for cname, cnode in m.classes.items():
                    s.notes.append(f"{m.rel_path}: class {cname} (line {cnode.lineno})")
        # 明示的なクリア処理があるか
        for h in self._grep_all(r"\.clear\(\)|=\s*(RoleFunctionLibrary|ConditionLibrary|LiteralLibrary)\(\)"):
            s.hits.append(Hit(h.file, h.line, h.text, "library reset candidate"))
        return s

    def inv_06_config_manager(self) -> Section:
        s = Section("6", "ConfigManager リセット (推奨)")
        # ConfigManager への全参照を列挙（安全性確認が目的）
        refs = self._grep_all(r"ConfigManager|config_manager")
        s.hits = refs
        s.notes.append(f"ConfigManager 参照箇所: {len(refs)}")
        # MainWindow 内での参照
        mw = self._main_window()
        if mw is not None:
            mw_refs = [h for h in refs if h.file == mw.rel_path]
            s.notes.append(f"うち MainWindow 内: {len(mw_refs)}")
        # reset_to_defaults の有無
        for m in self._find("config.py"):
            for cname, cnode in m.classes.items():
                if cname == "ConfigManager":
                    methods = [x.name for x in cnode.body if isinstance(x, ast.FunctionDef)]
                    s.notes.append(f"ConfigManager methods: {', '.join(methods)}")
                    if "reset_to_defaults" not in methods:
                        s.notes.append("reset_to_defaults() 未実装 → 再生成方式を推奨")
        if len(refs) > 5:
            s.risk = "caution"
        return s

    def inv_07_preferences(self) -> Section:
        s = Section("7", "Preferences 保持 (決定済)")
        mw = self._main_window()
        if mw is not None:
            for line_no, target, value in mw.assignments:
                if re.search(r"preferences", target, re.IGNORECASE):
                    s.hits.append(Hit(mw.rel_path, line_no,
                                      f"{target} = {value}", "MainWindow attr"))
        for h in self._grep_all(r"Preferences\(\)|self\.preferences"):
            s.hits.append(Hit(h.file, h.line, h.text))
        return s

    def inv_08_traceball(self) -> Section:
        s = Section("8", "TraceBall ログ保持 (決定済)")
        for h in self._grep_all(r"TraceBall|traceball"):
            s.hits.append(Hit(h.file, h.line, h.text))
        s.notes.append(f"TraceBall 参照: {len(s.hits)}")
        return s

    def inv_09_shortcut_ctrl_n(self) -> Section:
        s = Section("9", "Ctrl+N ショートカット (決定済)")
        hits = self._grep_all(r"QKeySequence\.(New|StandardKey\.New)|Ctrl\+N|Qt\.CTRL")
        s.hits = hits
        if any("New" in h.text for h in hits):
            s.notes.append("Ctrl+N は既に割当済みの可能性 → 競合確認")
            s.risk = "caution"
        else:
            s.notes.append("Ctrl+N 未使用 → 新規割当可能")
        # メニュー生成メソッドの存在確認
        mw = self._main_window()
        if mw is not None:
            for name in ("create_menus", "create_toolbar", "create_actions"):
                if mw.has_method("MainWindow", name):
                    line = mw.methods["MainWindow"][name].lineno
                    s.notes.append(f"MainWindow.{name} (line {line}) 存在")
        return s

    def inv_10_statusbar(self) -> Section:
        s = Section("10", "ステータスバー通知 (決定済)")
        for h in self._grep_all(r"statusBar\(\)|QStatusBar|showMessage"):
            s.hits.append(Hit(h.file, h.line, h.text))
        s.notes.append(f"statusBar 参照: {len(s.hits)}")
        return s

    def inv_11_test_impact(self) -> Section:
        s = Section("11", "既存テストへの影響 (MainWindow 直接生成)")
        for m in self.modules.values():
            if "/tests/" not in m.rel_path and not m.rel_path.startswith("tests/"):
                continue
            for line_no, text in grep(m.path, r"MainWindow\(|MainWindow\(\)"):
                s.hits.append(Hit(m.rel_path, line_no, text, "test instantiates MainWindow"))
        s.notes.append(f"MainWindow() を直接生成するテスト: {len(s.hits)}")
        if s.hits:
            s.risk = "caution"
            s.notes.append("windowModified 導入で初期状態 False を前提にできるか要確認")
        return s

    def inv_12_menu_structure(self) -> Section:
        s = Section("12", "メニュー / ツールバー構造")
        mw = self._main_window()
        if mw is None:
            return s
        for name in ("create_menus", "create_toolbar"):
            for line_no, text in mw.method_lines("MainWindow", name):
                if re.search(r"addMenu|addAction|addToolBar|QAction|QMenu", text):
                    s.hits.append(Hit(mw.rel_path, line_no, text, f"in {name}"))
        return s

    def inv_13_libcntrl_reset_impact(self) -> Section:
        s = Section("13", "libcntrl 再生成の影響範囲")
        for h in self._grep_all(r"RoleFunctionLibrary\(|ConditionLibrary\(|LiteralLibrary\("):
            s.hits.append(Hit(h.file, h.line, h.text, "library instantiation"))
        s.notes.append(f"ライブラリ生成箇所: {len(s.hits)}")
        if len(s.hits) > 3:
            s.risk = "caution"
        return s

    # -- runner ---------------------------------------------------------------

    def run(self) -> List[Section]:
        self.sections = [
            self.inv_01_startup_sample(),
            self.inv_02_tab_count(),
            self.inv_03_unsaved_confirmation(),
            self.inv_04_window_modified(),
            self.inv_05_libcntrl_libraries(),
            self.inv_06_config_manager(),
            self.inv_07_preferences(),
            self.inv_08_traceball(),
            self.inv_09_shortcut_ctrl_n(),
            self.inv_10_statusbar(),
            self.inv_11_test_impact(),
            self.inv_12_menu_structure(),
            self.inv_13_libcntrl_reset_impact(),
        ]
        return self.sections


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def render_report(sections: List[Section], root: Path) -> str:
    out: List[str] = []
    out.append("# New Project Feature - Investigation Report")
    out.append("")
    out.append(f"- root: `{root}`")
    out.append(f"- sections: {len(sections)}")
    out.append("")

    blockers = [s for s in sections if s.risk == "blocker"]
    cautions = [s for s in sections if s.risk == "caution"]
    out.append(f"- blockers: **{len(blockers)}**")
    out.append(f"- cautions: **{len(cautions)}**")
    out.append("")

    for s in sections:
        out.append(f"## [{s.key}] {s.title}")
        out.append(f"risk: `{s.risk}`")
        out.append("")
        if s.notes:
            out.append("**Notes**")
            for n in s.notes:
                out.append(f"- {n}")
            out.append("")
        if s.hits:
            out.append(f"**Hits ({len(s.hits)})**")
            out.append("")
            out.append("| file | line | text | note |")
            out.append("|------|-----:|------|------|")
            for h in s.hits[:40]:
                txt = h.text.strip().replace("|", "\\|")
                if len(txt) > 120:
                    txt = txt[:117] + "..."
                out.append(f"| {h.file} | {h.line} | `{txt}` | {h.note} |")
            if len(s.hits) > 40:
                out.append(f"| ... | | ({len(s.hits) - 40} more) | |")
            out.append("")
        else:
            out.append("_no hits_")
            out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="code root directory (default: .)")
    parser.add_argument("--out", default="", help="write report to file (default: stdout)")
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: root not a directory: {root}", file=sys.stderr)
        return 2

    inv = Investigator(root)
    sections = inv.run()
    report = render_report(sections, root)

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(report, encoding="utf-8")
        print(f"wrote {out_path} ({len(sections)} sections)")
    else:
        print(report)

    blockers = sum(1 for s in sections if s.risk == "blocker")
    cautions = sum(1 for s in sections if s.risk == "caution")
    return 1 if blockers else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))