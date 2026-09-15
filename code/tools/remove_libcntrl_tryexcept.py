#!/usr/bin/env python3
"""
StaTable v1.7 移行支援ツール: libcntrl try/except 一括削除

用途:
  - `try: from libcntrl.xxx import ...`
    `except ImportError: from statable_gui.libcntrl.xxx import ...`
    パターンを検出し、try/except を削除して
    `from statable_gui.libcntrl.xxx import ...` に統一。
  - try/except なしの `from libcntrl.xxx` も
    `from statable_gui.libcntrl.xxx` に置換。

【v2 修正】
  - Pattern A: try/except 削除 + except 本体を de-indent（正しい）
  - Pattern B: try/except 維持（de-indent しない）
  - try 直下の最初のコード行が libcntrl import の場合のみ処理
    （外側の try を誤検出しない）

使い方:
  python tools/remove_libcntrl_tryexcept.py .
  python tools/remove_libcntrl_tryexcept.py . --apply
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Iterable, Optional


EXCLUDE_DIRS = {
    ".git", ".hg", ".svn",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".venv", "venv", "env", ".env",
    "node_modules", "dist", "build", ".tox",
}

TRY_RE = re.compile(r'^(\s*)try:\s*$')
EXCEPT_ANY_RE = re.compile(r'^(\s*)except\s*.*:\s*$')
LIBCNTRL_IMPORT_RE = re.compile(r'^(\s*)from\s+libcntrl\.')
STATABLE_GUI_IMPORT_RE = re.compile(r'^\s*from\s+statable_gui\.libcntrl\.')


@dataclass
class FileReport:
    path: str
    changed: bool = False
    changes: list = field(default_factory=list)
    parse_error: str = ""


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------
def _count_leading_spaces(line: str) -> int:
    stripped = line.lstrip(' \t')
    return len(line) - len(stripped)


def _dedent_lines(lines: list, delta: int) -> list:
    if delta <= 0:
        return lines
    out = []
    for line in lines:
        if not line.strip():
            out.append(line)
            continue
        prefix = line[:delta]
        if prefix.strip() == '':
            out.append(line[delta:])
        else:
            out.append(line)
    return out


def _first_code_line(lines: list) -> Optional[str]:
    """コメント・空行を除いた最初のコード行を返す"""
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('#'):
            continue
        return line
    return None


# ---------------------------------------------------------------------------
# ブロック検出
# ---------------------------------------------------------------------------
def _collect_block(lines: list, start_idx: int) -> tuple:
    try_indent = _count_leading_spaces(lines[start_idx])

    try_body = []
    i = start_idx + 1
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            try_body.append(line)
            i += 1
            continue
        indent = _count_leading_spaces(line)
        if indent <= try_indent:
            break
        try_body.append(line)
        i += 1

    if i >= len(lines):
        return [], [], start_idx + 1, -1
    if not EXCEPT_ANY_RE.match(lines[i]):
        return [], [], start_idx + 1, -1

    except_indent = _count_leading_spaces(lines[i])
    if except_indent != try_indent:
        return [], [], start_idx + 1, -1

    except_header_idx = i
    except_body = []
    i += 1
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            except_body.append(line)
            i += 1
            continue
        indent = _count_leading_spaces(line)
        if indent <= except_indent:
            break
        except_body.append(line)
        i += 1

    return try_body, except_body, i, except_header_idx


# ---------------------------------------------------------------------------
# 変換ロジック
# ---------------------------------------------------------------------------
def _replace_libcntrl_in_lines(lines: list) -> list:
    out = []
    for line in lines:
        if LIBCNTRL_IMPORT_RE.match(line):
            new_line = re.sub(
                r'^(\s*)from\s+libcntrl\.',
                r'\1from statable_gui.libcntrl.',
                line,
            )
            out.append(new_line)
        else:
            out.append(line)
    return out


def _strip_trailing_blank(lines: list) -> list:
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def _strip_leading_blank(lines: list) -> list:
    while lines and not lines[0].strip():
        lines.pop(0)
    return lines


def transform_file(text: str) -> tuple:
    lines = text.split('\n')
    out = []
    changes = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        if TRY_RE.match(line):
            try_body, except_body, end_idx, except_header_idx = \
                _collect_block(lines, i)

            if except_header_idx >= 0 and try_body:
                try_indent = _count_leading_spaces(line)

                # ★ try 直下の最初のコード行が libcntrl import か
                first_code = _first_code_line(try_body)
                direct_libcntrl = (
                    first_code is not None
                    and LIBCNTRL_IMPORT_RE.match(first_code)
                )

                if direct_libcntrl:
                    except_has_statble = any(
                        STATABLE_GUI_IMPORT_RE.match(l)
                        for l in except_body
                    )

                    if except_has_statble:
                        # === Pattern A ===
                        # try/except を削除し、except 本体を de-indent して残す
                        kept_body = _strip_trailing_blank(
                            _strip_leading_blank(list(except_body))
                        )
                        if kept_body:
                            first_indent = _count_leading_spaces(kept_body[0])
                            delta = first_indent - try_indent
                            kept_body = _dedent_lines(kept_body, delta)
                        kept_body = _replace_libcntrl_in_lines(kept_body)

                        changes.append({
                            'line': i + 1,
                            'kind': 'remove_tryexcept',
                            'before': '\n'.join(lines[i:end_idx]),
                            'after': '\n'.join(kept_body),
                        })
                        out.extend(kept_body)
                        i = end_idx
                        continue
                    else:
                        # === Pattern B ===
                        # try/except 構造は維持。try 本体の libcntrl のみ置換。
                        # de-indent はしない！
                        new_try_body = _replace_libcntrl_in_lines(
                            list(try_body)
                        )
                        out.append(line)  # try:
                        out.extend(new_try_body)
                        out.append(lines[except_header_idx])  # except:
                        out.extend(except_body)

                        changes.append({
                            'line': i + 1,
                            'kind': 'replace_libcntrl_in_try',
                            'before': '\n'.join(try_body),
                            'after': '\n'.join(new_try_body),
                        })
                        i = end_idx
                        continue

                # direct_libcntrl でない → 外側の try。何もせず素通り。
                # （次の行から入れ子の try を個別に処理）

        # 単独の `from libcntrl.` を置換
        if LIBCNTRL_IMPORT_RE.match(line):
            new_line = re.sub(
                r'^(\s*)from\s+libcntrl\.',
                r'\1from statable_gui.libcntrl.',
                line,
            )
            changes.append({
                'line': i + 1,
                'kind': 'replace_libcntrl',
                'before': line,
                'after': new_line,
            })
            out.append(new_line)
            i += 1
            continue

        out.append(line)
        i += 1

    return '\n'.join(out), changes


# ---------------------------------------------------------------------------
# ファイル走査
# ---------------------------------------------------------------------------
def iter_python_files(root: Path, include_pattern: Optional[str] = None) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if include_pattern and not path.match(include_pattern):
            continue
        yield path


def analyze_file(path: Path) -> FileReport:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            text = path.read_text(encoding="latin-1")
        except Exception as e:
            return FileReport(path=str(path), parse_error=f"read error: {e}")

    try:
        new_text, changes = transform_file(text)
    except Exception as e:
        return FileReport(path=str(path), parse_error=f"transform error: {e}")

    return FileReport(
        path=str(path),
        changed=bool(changes),
        changes=changes,
    )


def apply_file(path: Path, backup: bool = True) -> FileReport:
    report = analyze_file(path)
    if not report.changed:
        return report

    try:
        original = path.read_text(encoding="utf-8")
    except Exception:
        return report

    try:
        new_text, _ = transform_file(original)
    except Exception as e:
        report.parse_error = f"transform error: {e}"
        return report

    if backup:
        bak = path.with_suffix(path.suffix + ".bak")
        bak.write_text(original, encoding="utf-8")

    path.write_text(new_text, encoding="utf-8")
    return report


# ---------------------------------------------------------------------------
# レポート出力
# ---------------------------------------------------------------------------
def print_report(reports: list, show_diff: bool = True):
    total = len(reports)
    changed = [r for r in reports if r.changed]
    errors = [r for r in reports if r.parse_error]

    print("=" * 72)
    print("  libcntrl try/except 削除レポート")
    print("=" * 72)
    print(f"  スキャン対象ファイル数 : {total}")
    print(f"  修正対象ファイル数     : {len(changed)}")
    if errors:
        print(f"  エラー                 : {len(errors)}")
    print()

    if changed:
        print("─" * 72)
        print("  【要修正】")
        print("─" * 72)
        for r in changed:
            print(f"\n  {r.path}")
            for c in r.changes:
                print(f"   L{c['line']}: [{c['kind']}]")
                if show_diff:
                    print("     --- before ---")
                    for ln in c['before'].split('\n'):
                        print(f"     | {ln}")
                    print("     --- after ---")
                    for ln in c['after'].split('\n'):
                        print(f"     | {ln}")
        print()

    if errors:
        print("─" * 72)
        print("  【エラー】")
        print("─" * 72)
        for r in errors:
            print(f"   {r.path}: {r.parse_error}")
        print()

    print("=" * 72)
    if changed:
        print(f"  {len(changed)} ファイルに修正候補があります。")
        print("  --apply オプションで適用できます（.bak バックアップ付き）。")
    else:
        print("  修正対象はありません。")
    print("=" * 72)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="libcntrl try/except 一括削除ツール (StaTable v1.7 用)"
    )
    p.add_argument("root", nargs="?", default=".", help="スキャンするルートディレクトリ")
    p.add_argument("--apply", action="store_true", help="実際にファイルを修正")
    p.add_argument("--include", default=None, help="glob パターン")
    p.add_argument("--json", metavar="PATH", help="JSON レポート出力先")
    p.add_argument("--no-diff", action="store_true", help="差分表示を省略")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if not root.exists():
        print(f"error: {root} が存在しません", file=sys.stderr)
        return 2

    files = list(iter_python_files(root, args.include))

    if args.apply:
        print("=" * 72)
        print("  --apply モード（.bak バックアップ付き）")
        print("=" * 72)
        reports = [apply_file(p, backup=True) for p in files]
        applied = [r for r in reports if r.changed]
        for r in applied:
            print(f"  [APPLIED] {r.path}")
        print(f"\n  適用ファイル数: {len(applied)}\n")
        print("=" * 72)
        print("  完了")
        print("=" * 72)
    else:
        reports = [analyze_file(p) for p in files]
        print_report(reports, show_diff=not args.no_diff)

    if args.json:
        out = {
            "root": str(root),
            "applied": args.apply,
            "reports": [
                {
                    "path": r.path,
                    "changed": r.changed,
                    "parse_error": r.parse_error,
                    "changes": r.changes,
                }
                for r in reports
            ],
        }
        Path(args.json).write_text(
            json.dumps(out, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  JSON レポート: {args.json}")

    has_change = any(r.changed for r in reports)
    return 1 if (has_change and not args.apply) else 0


if __name__ == "__main__":
    sys.exit(main())