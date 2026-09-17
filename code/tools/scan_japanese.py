#!/usr/bin/env python3
"""
StaTable 日本語テキスト調査ツール

【目的】
  リリース用に日本語 → 英語へ変換するため、
  どのファイルにどの日本語が含まれているかを調査する。

【スキャン対象】
  statable/     データモデル層
  statable_gui/ GUI 層
  codegen/      コード生成層
  tools/        開発支援ツール
  tests/        テスト

【カテゴリ分類】
  A: 生成 C コードコメント（最優先）
  B: GUI 表示文言（最優先）
  C: ログメッセージ
  D: エラー・警告メッセージ
  E: docstring / コメント
  F: サンプルデータ
  G: テスト期待値
  H: その他

【使い方】
  # 全スキャン
  python tools/scan_japanese.py

  # 特定カテゴリのみ
  python tools/scan_japanese.py --category A B

  # 特定ディレクトリのみ
  python tools/scan_japanese.py --dirs codegen statable_gui

  # 除外パターン
  python tools/scan_japanese.py --exclude "tests/*"
"""
import argparse
import csv
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple


# ============================================================
# 定数
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_SCAN_DIRS = [
    "statable",
    "statable_gui",
    "codegen",
    "tools",
    "tests",
]

# 日本語文字の Unicode 範囲
JP_PATTERN = re.compile(
    r'[\u3040-\u309F'    # ひらがな
    r'\u30A0-\u30FF'     # カタカナ
    r'\u4E00-\u9FFF'     # 漢字（CJK統合漢字）
    r'\uFF00-\uFFEF'     # 全角記号
    r']+'
)

# コメント・文字列のパターン
COMMENT_PATTERNS = {
    "python_line_comment": re.compile(r'#\s*(.+)$'),
    "python_docstring_triple": re.compile(r'"""(.+?)"""', re.DOTALL),
    "c_comment_line": re.compile(r'//\s*(.+)$'),
    "c_comment_block": re.compile(r'/\*(.+?)\*/', re.DOTALL),
}

# カテゴリ別のヒューリスティック
CATEGORY_RULES = [
    # 生成 C コードコメント（最優先）
    ("A", [
        r"codegen[/\\].*\.py$",
        r"codegen[/\\].*_generator\.py$",
        r"codegen[/\\]code_templates\.py$",
    ]),
    # GUI 表示文言（最優先）
    ("B", [
        r"statable_gui[/\\].*\.py$",
        r"statable_gui[/\\]dialogs\.py$",
    ]),
    # サンプルデータ
    ("F", [
        r"sample_data\.py$",
        r"statable[/\\]sample_data\.py$",
    ]),
    # テスト期待値
    ("G", [
        r"tests[/\\].*\.py$",
    ]),
    # tools 自体
    ("H", [
        r"tools[/\\].*\.py$",
    ]),
]


# ============================================================
# データクラス
# ============================================================

@dataclass
class JapaneseLine:
    """1 行の日本語検出結果"""
    file_path: str
    line_no: int
    category: str
    context: str          # 'comment', 'string', 'docstring', 'other'
    text: str             # 日本語部分を含む行
    jp_text: str          # 検出された日本語文字列
    en_hint: str = ""     # 英語化のヒント（例: 「状態」→ "state"）

    def key(self) -> str:
        return f"{self.file_path}:{self.line_no}"


@dataclass
class ScanResult:
    """スキャン結果"""
    total_files: int = 0
    files_with_jp: int = 0
    total_lines: int = 0
    lines: List[JapaneseLine] = field(default_factory=list)


# ============================================================
# カテゴリ判定
# ============================================================

def detect_category(rel_path: str) -> str:
    """相対パスからカテゴリを判定"""
    # 正規化（Windows パス → /）
    norm = rel_path.replace("\\", "/")

    for category, patterns in CATEGORY_RULES:
        for pattern in patterns:
            if re.search(pattern, norm):
                # さらに細分化
                if category == "A":
                    if "_generator.py" in norm or "code_templates.py" in norm:
                        return "A"    # 生成コード
                    return "C"        # codegen 配下のログ等
                return category

    return "H"


def detect_context(line: str, line_index: int,
                   all_lines: List[str]) -> str:
    """行の文脈を判定"""
    stripped = line.strip()

    # 行コメント
    if stripped.startswith("#"):
        return "comment"
    if stripped.startswith("//"):
        return "comment"

    # ブロックコメント内
    if stripped.startswith("*"):
        return "comment"

    # docstring 内（簡易判定）
    # 前の行に """ があるか、次の行に """ がある
    if line_index > 0:
        prev = all_lines[line_index - 1].strip()
        if '"""' in prev and not prev.endswith('"""'):
            return "docstring"

    # 文字列リテラル
    if '"' in line or "'" in line:
        # 日本語が文字列内にあるか
        if re.search(r'["\'][^"\']*' + JP_PATTERN.pattern + r'[^"\']*["\']', line):
            return "string"

    return "other"


# ============================================================
# 英語化ヒント辞書（よく使う用語）
# ============================================================

EN_HINTS = {
    "状態": "state",
    "イベント": "event",
    "遷移": "transition",
    "ロール関数": "role function",
    "初期化": "initialization",
    "起動": "start",
    "停止": "stop",
    "待機": "idle",
    "動作中": "running",
    "エラー": "error",
    "成功": "success",
    "失敗": "failure",
    "完了": "completed",
    "実行": "execute",
    "設定": "settings",
    "定義": "definition",
    "変数": "variable",
    "フラグ": "flag",
    "割り込み": "interrupt",
    "タイマ": "timer",
    "キュー": "queue",
    "カウンタ": "counter",
    "接続": "connection",
    "切断": "disconnection",
    "再試行": "retry",
    "タイトル": "title",
    "説明": "description",
    "名称": "name",
    "名前空間": "namespace",
    "戻り値": "return value",
    "引数": "argument",
    "条件": "condition",
    "アクション": "action",
    "関数": "function",
    "型": "type",
    "層": "layer",
    "優先度": "priority",
    "レイヤ": "layer",
    "ドライバ": "driver",
    "ミドルウェア": "middleware",
    "アプリ": "application",
    "アプリケーション": "application",
    "システム": "system",
    "コンテキスト": "context",
    "ポインタ": "pointer",
    "ガード": "guard",
    "マーカー": "marker",
    "ユーザー": "user",
    "警告": "warning",
    "情報": "info",
    "デバッグ": "debug",
    "エラーコード": "error code",
    "リトライ": "retry",
    "カウンタ": "counter",
    "閾値": "threshold",
    "超過": "exceed",
    "無視": "ignore",
    "強制": "forced",
    "正常": "normal",
    "異常": "abnormal",
    "準備": "ready",
    "接続中": "connecting",
    "接続済": "connected",
    "一時停止": "pause",
    "再開": "resume",
}


def get_en_hint(jp_text: str) -> str:
    """日本語文字列から英語のヒントを生成"""
    hints = []
    for jp, en in EN_HINTS.items():
        if jp in jp_text:
            hints.append(en)
    return " / ".join(hints) if hints else ""


# ============================================================
# スキャナ
# ============================================================

def scan_file(file_path: Path, project_root: Path) -> List[JapaneseLine]:
    """1 ファイルをスキャンして日本語行を返す"""
    results = []

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = file_path.read_text(encoding="shift-jis")
        except Exception:
            return results
    except Exception:
        return results

    rel_path = str(file_path.relative_to(project_root))
    category = detect_category(rel_path)
    lines = content.split("\n")

    for i, line in enumerate(lines, start=1):
        matches = JP_PATTERN.findall(line)
        if not matches:
            continue

        jp_text = " ".join(matches)
        context = detect_context(line, i - 1, lines)
        en_hint = get_en_hint(jp_text)

        results.append(JapaneseLine(
            file_path=rel_path,
            line_no=i,
            category=category,
            context=context,
            text=line.strip()[:120],
            jp_text=jp_text[:80],
            en_hint=en_hint,
        ))

    return results


def scan_project(project_root: Path, scan_dirs: List[str],
                 exclude_patterns: List[str] = None) -> ScanResult:
    """プロジェクト全体をスキャン"""
    result = ScanResult()
    exclude_patterns = exclude_patterns or []

    py_files = []
    for dir_name in scan_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            continue
        py_files.extend(dir_path.rglob("*.py"))

    # 除外パターンを適用
    def is_excluded(path: Path) -> bool:
        rel = str(path.relative_to(project_root)).replace("\\", "/")
        for pattern in exclude_patterns:
            if re.search(pattern, rel):
                return True
        return False

    py_files = [f for f in py_files if not is_excluded(f)]

    result.total_files = len(py_files)

    for f in py_files:
        lines = scan_file(f, project_root)
        if lines:
            result.files_with_jp += 1
            result.lines.extend(lines)
            result.total_lines += len(lines)

    return result


# ============================================================
# レポート生成
# ============================================================

CATEGORY_NAMES = {
    "A": "生成 C コードコメント（最優先）",
    "B": "GUI 表示文言（最優先）",
    "C": "コード生成層のログ等",
    "D": "エラー・警告メッセージ",
    "E": "docstring / コメント",
    "F": "サンプルデータ",
    "G": "テスト期待値",
    "H": "その他",
}


def generate_report(result: ScanResult, output_path: Path):
    """Markdown レポートを生成"""
    lines = []
    lines.append("# StaTable 日本語テキスト調査レポート")
    lines.append("")
    lines.append("## サマリ")
    lines.append("")
    lines.append(f"- スキャンファイル数: {result.total_files}")
    lines.append(f"- 日本語を含むファイル数: {result.files_with_jp}")
    lines.append(f"- 日本語を含む行数: {result.total_lines}")
    lines.append("")

    # カテゴリ別集計
    by_category: Dict[str, List[JapaneseLine]] = {}
    for jl in result.lines:
        by_category.setdefault(jl.category, []).append(jl)

    lines.append("## カテゴリ別集計")
    lines.append("")
    lines.append("| カテゴリ | 説明 | 行数 | ファイル数 |")
    lines.append("|---|---|---|---|")
    for cat in sorted(by_category.keys()):
        items = by_category[cat]
        files = {j.file_path for j in items}
        lines.append(f"| {cat} | {CATEGORY_NAMES.get(cat, '?')} | "
                     f"{len(items)} | {len(files)} |")
    lines.append("")

    # ファイル別集計
    lines.append("## ファイル別集計（行数の多い順）")
    lines.append("")
    lines.append("| ファイル | カテゴリ | 行数 |")
    lines.append("|---|---|---|")
    by_file: Dict[str, List[JapaneseLine]] = {}
    for jl in result.lines:
        by_file.setdefault(jl.file_path, []).append(jl)
    sorted_files = sorted(by_file.items(), key=lambda x: -len(x[1]))
    for fpath, items in sorted_files[:50]:  # 上位 50 ファイル
        cats = sorted({j.category for j in items})
        lines.append(f"| `{fpath}` | {', '.join(cats)} | {len(items)} |")
    lines.append("")

    # カテゴリ別詳細
    for cat in sorted(by_category.keys()):
        items = by_category[cat]
        lines.append(f"## カテゴリ {cat}: {CATEGORY_NAMES.get(cat, '?')}")
        lines.append("")

        # ファイル別にグループ化
        by_file_cat: Dict[str, List[JapaneseLine]] = {}
        for jl in items:
            by_file_cat.setdefault(jl.file_path, []).append(jl)

        for fpath, file_items in sorted(by_file_cat.items()):
            lines.append(f"### `{fpath}` （{len(file_items)} 行）")
            lines.append("")
            lines.append("| 行 | 種別 | 日本語 | 英語ヒント |")
            lines.append("|---|---|---|---|")
            for jl in file_items[:30]:  # 各ファイル上位 30 行
                text = jl.jp_text.replace("|", "\\|")[:60]
                hint = jl.en_hint.replace("|", "\\|")[:60]
                lines.append(f"| {jl.line_no} | {jl.context} | "
                             f"`{text}` | {hint} |")
            if len(file_items) > 30:
                lines.append(f"| ... | ... | （他 {len(file_items) - 30} 行）| |")
            lines.append("")

    report = "\n".join(lines)
    output_path.write_text(report, encoding="utf-8")


def generate_csv(result: ScanResult, output_path: Path):
    """CSV レポートを生成"""
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "file", "line", "category", "context", "jp_text", "en_hint"
        ])
        for jl in result.lines:
            writer.writerow([
                jl.file_path,
                jl.line_no,
                jl.category,
                jl.context,
                jl.jp_text,
                jl.en_hint,
            ])


# ============================================================
# メイン
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="StaTable 日本語テキスト調査ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dirs", nargs="+", default=DEFAULT_SCAN_DIRS,
        help="スキャン対象ディレクトリ",
    )
    parser.add_argument(
        "--category", nargs="+", default=None,
        help="抽出するカテゴリ（A/B/C/...）",
    )
    parser.add_argument(
        "--exclude", nargs="+", default=[],
        help="除外パターン（正規表現）",
    )
    parser.add_argument(
        "--report", default="japanese_scan_report.md",
        help="Markdown レポート出力先",
    )
    parser.add_argument(
        "--csv", default="japanese_scan_report.csv",
        help="CSV レポート出力先",
    )
    parser.add_argument(
        "--root", default=None,
        help="プロジェクトルート（既定: スクリプトの親ディレクトリ）",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else PROJECT_ROOT

    print(f"=== 日本語テキスト調査 ===")
    print(f"プロジェクトルート: {root}")
    print(f"スキャン対象: {', '.join(args.dirs)}")
    if args.exclude:
        print(f"除外パターン: {', '.join(args.exclude)}")
    print()

    result = scan_project(root, args.dirs, args.exclude)

    # カテゴリフィルタ
    if args.category:
        categories = set(args.category)
        result.lines = [jl for jl in result.lines
                        if jl.category in categories]

    # サマリ表示
    print(f"スキャンファイル数: {result.total_files}")
    print(f"日本語を含むファイル数: {result.files_with_jp}")
    print(f"日本語を含む行数: {result.total_lines}")
    print()

    # カテゴリ別
    by_category: Dict[str, int] = {}
    for jl in result.lines:
        by_category[jl.category] = by_category.get(jl.category, 0) + 1

    print("カテゴリ別:")
    for cat in sorted(by_category.keys()):
        name = CATEGORY_NAMES.get(cat, "?")
        print(f"  {cat}: {name} - {by_category[cat]} 行")
    print()

    # レポート出力
    report_path = root / args.report
    csv_path = root / args.csv
    generate_report(result, report_path)
    generate_csv(result, csv_path)

    print(f"Markdown レポート: {report_path}")
    print(f"CSV レポート: {csv_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())