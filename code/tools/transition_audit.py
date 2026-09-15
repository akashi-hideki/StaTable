#!/usr/bin/env python3
"""
StaTable v1.6 移行支援ツール: dataclass kw_only 化 監査ツール

用途:
  - `Transition(...)` の全構築箇所を AST ベースで検出
  - 位置引数 / キーワード引数の分類
  - `kw_only=True` 化した際に TypeError になる箇所を事前に洗い出し
  - （任意）--fix で位置引数をキーワード引数に自動変換

使い方:
  python transition_audit.py .
  python transition_audit.py . --target Transition
  python transition_audit.py . --target RoleFunction --fields name,namespace,description,return_type,arg1_type,arg1_name,arg2_type,arg2_name,title
  python transition_audit.py . --show-ok
  python transition_audit.py . --json report.json
  python transition_audit.py . --fix --dry-run
  python transition_audit.py . --fix
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable, Optional


# ---------------------------------------------------------------------------
# v1.5 仕様書準拠: Transition のフィールド順
# ---------------------------------------------------------------------------
DEFAULT_FIELDS = [
    "source", "event", "condition", "pre_actions", "target",
    "has_else", "else_target", "else_actions",
    "action", "transition_type", "title",
]

DEFAULT_TARGET = "Transition"

EXCLUDE_DIRS = {
    ".git", ".hg", ".svn",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".venv", "venv", "env", ".env",
    "node_modules", "dist", "build", ".tox",
}


@dataclass
class Finding:
    file: str
    line: int
    col: int
    target: str
    positional_count: int
    keyword_names: list
    positional_reprs: list
    snippet: str
    source_line: str
    is_problematic: bool
    reason: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class FileReport:
    path: str
    findings: list = field(default_factory=list)
    parse_error: str = ""


# ---------------------------------------------------------------------------
# AST visitor
# ---------------------------------------------------------------------------
class TransitionCallVisitor(ast.NodeVisitor):
    def __init__(self, target: str, source_lines: list):
        self.target = target
        self.source_lines = source_lines
        self.findings: list = []

    def visit_Call(self, node: ast.Call):
        name = self._get_call_name(node.func)
        if name == self.target:
            self.findings.append(self._build_finding(node))
        self.generic_visit(node)

    def _get_call_name(self, func: ast.AST) -> Optional[str]:
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
        return None

    def _build_finding(self, node: ast.Call) -> Finding:
        positional = list(node.args)
        keywords = [kw for kw in node.keywords if kw.arg is not None]
        star_kwargs = [kw for kw in node.keywords if kw.arg is None]

        pos_reprs = [self._safe_unparse(a) for a in positional]
        kw_names = [kw.arg for kw in keywords]

        is_problematic = bool(positional)
        reason = ""
        if star_kwargs:
            reason = "**kwargs 展開あり（手動確認推奨）"
        if positional:
            reason = f"位置引数 {len(positional)} 個 → kw_only 化で TypeError"

        return Finding(
            file="",
            line=node.lineno,
            col=node.col_offset,
            target=self.target,
            positional_count=len(positional),
            keyword_names=kw_names,
            positional_reprs=pos_reprs,
            snippet=self._line_slice(node),
            source_line=self._get_line(node.lineno),
            is_problematic=is_problematic,
            reason=reason,
        )

    def _get_line(self, lineno: int) -> str:
        if 1 <= lineno <= len(self.source_lines):
            return self.source_lines[lineno - 1].rstrip("\n")
        return ""

    def _line_slice(self, node: ast.AST) -> str:
        start = getattr(node, "lineno", 0)
        end = getattr(node, "end_lineno", start)
        if not start:
            return ""
        return "\n".join(self.source_lines[start - 1 : end]).rstrip()

    def _safe_unparse(self, node: ast.AST) -> str:
        try:
            return ast.unparse(node)
        except Exception:
            return "<unparseable>"


# ---------------------------------------------------------------------------
# ファイル走査
# ---------------------------------------------------------------------------
def iter_python_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        yield path


def analyze_file(path: Path, target: str) -> FileReport:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            text = path.read_text(encoding="latin-1")
        except Exception as e:
            return FileReport(path=str(path), parse_error=f"read error: {e}")

    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        return FileReport(path=str(path), parse_error=f"syntax error: {e}")

    lines = text.splitlines()
    visitor = TransitionCallVisitor(target, lines)
    visitor.visit(tree)

    for f in visitor.findings:
        f.file = str(path)

    return FileReport(path=str(path), findings=visitor.findings)


# ---------------------------------------------------------------------------
# --fix: 位置引数 → キーワード引数 変換
# ---------------------------------------------------------------------------
class TransitionCallRewriter(ast.NodeTransformer):
    def __init__(self, target: str, fields: list):
        self.target = target
        self.fields = fields
        self.rewrites: list = []  # (start_line, end_line, new_text)

    def visit_Call(self, node: ast.Call):
        name = self._get_call_name(node.func)
        if name == self.target and node.args:
            new_keywords = list(node.keywords)
            for i, arg in enumerate(node.args):
                if i >= len(self.fields):
                    continue
                new_keywords.append(ast.keyword(arg=self.fields[i], value=arg))
            node.args = []
            node.keywords = new_keywords
            try:
                new_text = ast.unparse(node)
                self.rewrites.append((node.lineno, node.end_lineno, new_text))
            except Exception:
                pass
        self.generic_visit(node)
        return node

    def _get_call_name(self, func):
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
        return None


def apply_fixes(path: Path, target: str, fields: list, dry_run: bool) -> Optional[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return None

    rewriter = TransitionCallRewriter(target, fields)
    rewriter.visit(tree)
    if not rewriter.rewrites:
        return None

    lines = text.split("\n")
    for start, end, new_text in sorted(rewriter.rewrites, key=lambda x: -x[0]):
        lines[start - 1 : end] = new_text.split("\n")
    new_source = "\n".join(lines)

    if not dry_run:
        backup = path.with_suffix(path.suffix + ".bak")
        backup.write_text(text, encoding="utf-8")
        path.write_text(new_source, encoding="utf-8")
    return new_source


# ---------------------------------------------------------------------------
# レポート出力
# ---------------------------------------------------------------------------
def print_report(reports: list, target: str, show_ok: bool = False):
    total_files = len(reports)
    files_with_findings = [r for r in reports if r.findings]
    problem_files = [r for r in reports if any(f.is_problematic for f in r.findings)]
    parse_errors = [r for r in reports if r.parse_error]
    total_calls = sum(len(r.findings) for r in reports)
    problem_calls = sum(1 for r in reports for f in r.findings if f.is_problematic)

    print("=" * 72)
    print(f"  {target} 構築箇所 監査レポート")
    print("=" * 72)
    print(f"  スキャン対象ファイル数  : {total_files}")
    print(f"  {target}(...) 検出数     : {total_calls}")
    print(f"  修正必要（位置引数あり）: {problem_calls}")
    print(f"  修正必要ファイル数      : {len(problem_files)}")
    if parse_errors:
        print(f"  パースエラー            : {len(parse_errors)}")
    print()

    if problem_files:
        print("─" * 72)
        print("  【要修正】位置引数で構築されている箇所")
        print("─" * 72)
        for r in problem_files:
            print(f"\n  {r.path}")
            for f in r.findings:
                if not f.is_problematic:
                    continue
                print(f"   L{f.line}: {f.reason}")
                print(f"       位置引数: {f.positional_reprs}")
                if f.keyword_names:
                    print(f"       kwarg   : {f.keyword_names}")
                for sline in f.snippet.split("\n"):
                    print(f"       | {sline}")
        print()

    if show_ok:
        ok_files = [
            r for r in files_with_findings
            if not any(f.is_problematic for f in r.findings)
        ]
        if ok_files:
            print("─" * 72)
            print("  【OK】既に kwarg のみで構築されている箇所")
            print("─" * 72)
            for r in ok_files:
                print(f"\n  {r.path}")
                for f in r.findings:
                    print(f"   L{f.line}: kwargs={f.keyword_names}")
            print()

    if parse_errors:
        print("─" * 72)
        print("  【パースエラー】")
        print("─" * 72)
        for r in parse_errors:
            print(f"   {r.path}: {r.parse_error}")
        print()

    print("=" * 72)
    if problem_calls == 0:
        print(f"  OK: 位置引数構築はありません。{target} を kw_only=True 化できます。")
    else:
        print(f"  NG: {problem_calls} 箇所を kwarg に変換してから kw_only=True 化してください。")
    print("=" * 72)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="dataclass kw_only 化 移行支援ツール (StaTable v1.6 用)"
    )
    p.add_argument("root", nargs="?", default=".", help="スキャンするルートディレクトリ")
    p.add_argument("--target", default=DEFAULT_TARGET,
                   help=f"対象クラス名（デフォルト: {DEFAULT_TARGET}）")
    p.add_argument("--fields", default=",".join(DEFAULT_FIELDS),
                   help="フィールド順（カンマ区切り）。--fix 時に使用。")
    p.add_argument("--show-ok", action="store_true", help="問題なしの箇所も表示")
    p.add_argument("--json", metavar="PATH", help="JSON レポート出力先")
    p.add_argument("--fix", action="store_true", help="位置引数を kwarg に自動変換")
    p.add_argument("--dry-run", action="store_true", help="--fix 時のドライラン")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if not root.exists():
        print(f"error: {root} が存在しません", file=sys.stderr)
        return 2

    fields = [f.strip() for f in args.fields.split(",") if f.strip()]

    reports = [analyze_file(py, args.target) for py in iter_python_files(root)]

    if args.fix:
        print("=" * 72)
        print(f"  --fix モード ({'dry-run' if args.dry_run else '適用'})")
        print("=" * 72)
        fixed = 0
        for r in reports:
            if not any(f.is_problematic for f in r.findings):
                continue
            path = Path(r.path)
            result = apply_fixes(path, args.target, fields, args.dry_run)
            if result is not None:
                fixed += 1
                print(f"  {'[DRY]' if args.dry_run else '[FIX]'} {path}")
        print(f"\n  修正ファイル数: {fixed}\n")
        if not args.dry_run:
            reports = [analyze_file(Path(r.path), args.target) for r in reports]

    print_report(reports, args.target, show_ok=args.show_ok)

    if args.json:
        out = {
            "target": args.target,
            "fields": fields,
            "reports": [
                {
                    "path": r.path,
                    "parse_error": r.parse_error,
                    "findings": [f.to_dict() for f in r.findings],
                }
                for r in reports
            ],
        }
        Path(args.json).write_text(
            json.dumps(out, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  JSON レポート: {args.json}")

    has_problem = any(f.is_problematic for r in reports for f in r.findings)
    return 1 if has_problem else 0


if __name__ == "__main__":
    sys.exit(main())