# tools/purge_unused_files.py
"""
未使用ファイル削除ツール（Git 前提・物理削除版）

前提: プロジェクトが git 管理下にあり、working tree が clean であること。

使い方:
    cd C:\\Users\\user\\OneDrive\\ドキュメント\\GitHub\\StaTable\\code

    # 1. 調査のみ
    python tools\\purge_unused_files.py --report

    # 2. 物理削除（git rm --cached は使わず、ファイル削除のみ）
    python tools\\purge_unused_files.py --purge

    # 3. 削除後に git で復元する場合
    #    (削除前にコミット済みなら)
    git checkout -- <path>         # 個別
    git reset --hard HEAD          # 全部

設計:
  - 入口: gui_main.py
  - 追跡: ast で import 解析、再帰探索
  - 削除: Path.unlink() で物理削除
  - 削除前に git 状態をチェック
"""

import argparse
import ast
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional


# ============================================================
# 設定
# ============================================================
CODE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = CODE_DIR.parent  # git リポジトリルート（要調整）

ENTRY_POINTS = ["gui_main.py"]

EXCLUDE_DIRS = {
    "__pycache__",
    "_archive",
    "_generated",
    "_generated_ccodegen",
    "_generated_test",
    "_logs",
    "logs",
    "Resources",
    ".git",
    ".vscode",
    ".idea",
}

EXCLUDE_FILES = {"__init__.py", "conftest.py", "setup.py"}

# 動的 import で使われるモジュール（誤削除防止）
FORCE_KEEP = {
    "codegen.c_code_generator",
    "codegen.sample_data",
    "codegen.config",
    "codegen.transition_generator",
    "codegen.role_function_generator",
    "codegen.interrupt_generator",
    "codegen.struct_generator",
    "codegen.enum_generator",
    "codegen.variable_generator",
    "codegen.event_queue_generator",
    "codegen.timer_generator",
    "codegen.osal_generator",
    "codegen.code_templates",
    "codegen.code_merger",
    "codegen.type_mapper",
    "codegen.naming_convention",
    "statable.model",
    "statable.state_machine",
    "statable.global_defs",
    "statable.xml_io",
    "statable.mermaid_gen",
    "statable.sample_data",
    "statable_gui.main_window",
    "statable_gui.widgets",
    "statable_gui.matrix_table",
    "statable_gui.libcntrl.role_function_library",
    "statable_gui.libcntrl.condition_library",
    "statable_gui.libcntrl.literal_library",
}


# ============================================================
# git 状態チェック
# ============================================================
def check_git_status() -> bool:
    """git リポジトリの状態をチェック"""
    print("\n[git 状態チェック]")

    # git リポジトリかどうか
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=str(CODE_DIR),
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            print("  ❌ git リポジトリではありません。")
            print(f"     場所: {CODE_DIR}")
            return False
    except FileNotFoundError:
        print("  ❌ git コマンドが見つかりません。")
        return False
    except Exception as e:
        print(f"  ❌ git 実行エラー: {e}")
        return False

    # working tree が clean か
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(CODE_DIR),
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            print(f"  ❌ git status 失敗: {result.stderr}")
            return False

        changes = result.stdout.strip()
        if not changes:
            print("  ✅ working tree は clean です。")
            return True
        else:
            lines = changes.splitlines()
            print(f"  ⚠️  未コミットの変更が {len(lines)} 件あります:")
            for line in lines[:10]:
                print(f"     {line}")
            if len(lines) > 10:
                print(f"     ... 他 {len(lines) - 10} 件")
            print("\n  → 削除前にコミットすることを強く推奨します:")
            print("     git add . && git commit -m 'Before cleanup'")
            return False
    except Exception as e:
        print(f"  ❌ git status 実行エラー: {e}")
        return False


def get_git_tracked_files() -> Set[str]:
    """git で追跡されているファイルの相対パス集合"""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=str(CODE_DIR),
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return set()
        return set(result.stdout.splitlines())
    except Exception:
        return set()


# ============================================================
# import 解析（前回と同じ）
# ============================================================
def parse_imports(file_path: Path) -> Set[str]:
    try:
        source = file_path.read_text(encoding="utf-8")
    except Exception:
        return set()

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return set()

    imports: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    return imports


def resolve_module(module_name: str) -> Optional[Path]:
    parts = module_name.split('.')
    candidates = [
        CODE_DIR.joinpath(*parts).with_suffix(".py"),
        CODE_DIR.joinpath(*parts) / "__init__.py",
    ]
    for c in candidates:
        if c.is_file():
            return c

    for sub in ["codegen", "statable", "statable_gui"]:
        p = CODE_DIR / sub / f"{module_name.replace('.', '/')}.py"
        if p.is_file():
            return p

    return None


def trace_reachable(entry_points: List[str]) -> Set[Path]:
    reachable: Set[Path] = set()
    queue: List[str] = list(entry_points)
    queue.extend(FORCE_KEEP)

    while queue:
        module = queue.pop(0)
        path = resolve_module(module)
        if path is None or path in reachable:
            continue
        reachable.add(path)
        for imp in parse_imports(path):
            if imp.startswith('.'):
                continue
            sub_path = resolve_module(imp)
            if sub_path and sub_path not in reachable:
                queue.append(imp)

    return reachable


def collect_all_py_files(
    include_tests: bool = False,
    only_tests: bool = False,
) -> List[Path]:
    result = []
    for root, dirs, files in os.walk(CODE_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        rel_root = Path(root).relative_to(CODE_DIR)

        if only_tests:
            if not str(rel_root).startswith("tests"):
                continue
        elif not include_tests:
            if str(rel_root).startswith("tests"):
                continue

        for f in files:
            if not f.endswith(".py") or f in EXCLUDE_FILES:
                continue
            result.append(Path(root) / f)
    return result


def classify_unused(unused: List[Path]) -> Dict[str, List[Path]]:
    cats: Dict[str, List[Path]] = {
        "tests": [], "tools": [], "sample": [], "debug": [], "other": [],
    }
    for p in unused:
        rel = str(p.relative_to(CODE_DIR)).replace("\\", "/")
        if rel.startswith("tests/"):
            cats["tests"].append(p)
        elif rel.startswith("tools/"):
            cats["tools"].append(p)
        elif "debug" in p.stem.lower():
            cats["debug"].append(p)
        elif "sample" in p.stem.lower():
            cats["sample"].append(p)
        else:
            cats["other"].append(p)
    return cats


# ============================================================
# レポート
# ============================================================
def print_report(
    all_files: List[Path],
    reachable: Set[Path],
    unused: List[Path],
):
    print("\n" + "=" * 76)
    print("  未使用ファイル検出レポート")
    print("=" * 76)
    print(f"\n[サマリ]")
    print(f"  全 .py ファイル:   {len(all_files)}")
    print(f"  到達可能（本体）:   {len(reachable)}")
    print(f"  未到達（削除候補）: {len(unused)}")

    cats = classify_unused(unused)
    print(f"\n[カテゴリ別内訳]")
    for cat, items in cats.items():
        if items:
            print(f"  {cat:10s}: {len(items):3d} 件")

    for cat in ["other", "sample", "debug", "tools", "tests"]:
        items = cats.get(cat, [])
        if not items:
            continue
        print(f"\n[カテゴリ: {cat}]  ({len(items)} 件)")
        for p in sorted(items):
            rel = p.relative_to(CODE_DIR)
            size = p.stat().st_size
            print(f"  - {rel}  ({size:,} bytes)")

    print("\n" + "=" * 76)


# ============================================================
# 物理削除
# ============================================================
def purge_files(unused: List[Path]) -> int:
    """未使用ファイルを物理削除"""
    if not unused:
        print("\n[INFO] 削除対象がありません。")
        return 0

    print("\n" + "=" * 76)
    print(f"  {len(unused)} 件のファイルを物理削除します")
    print("=" * 76)

    deleted = 0
    errors = 0

    for p in unused:
        rel = p.relative_to(CODE_DIR)
        try:
            p.unlink()
            deleted += 1
        except Exception as e:
            print(f"  [NG] {rel}: {e}")
            errors += 1

    # 空ディレクトリ掃除
    _cleanup_empty_dirs(CODE_DIR, exclude={"__pycache__", "_archive"})

    print(f"\n  削除: {deleted} 件 / 失敗: {errors} 件")
    print("\n  ※ 復元方法（削除前にコミット済みの場合）:")
    print("     git checkout -- <path>   # 個別")
    print("     git reset --hard HEAD    # 全部")
    print("=" * 76)
    return deleted


def _cleanup_empty_dirs(root: Path, exclude: Set[str]):
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        p = Path(dirpath)
        rel = p.relative_to(root)
        if any(part in exclude or part in EXCLUDE_DIRS for part in rel.parts):
            continue
        try:
            if not any(p.iterdir()):
                p.rmdir()
                print(f"  [削除] 空ディレクトリ: {rel}")
        except Exception:
            pass


# ============================================================
# main
# ============================================================
def parse_args():
    p = argparse.ArgumentParser(description="未使用ファイル物理削除ツール")
    p.add_argument("--report", action="store_true", help="調査のみ")
    p.add_argument("--purge", action="store_true", help="物理削除実行")
    p.add_argument("--only-tests", action="store_true", help="tests/ のみ")
    p.add_argument("--include-tests", action="store_true",
                   help="tests/ も対象に含める（既定 OFF）")
    p.add_argument("--force", action="store_true",
                   help="git 状態チェックをスキップ（非推奨）")
    return p.parse_args()


def main():
    args = parse_args()

    print("=" * 76)
    print("  StaTable 未使用ファイル物理削除ツール")
    print("=" * 76)
    print(f"  CODE_DIR: {CODE_DIR}")

    # git 状態チェック（--purge のときだけ）
    if args.purge and not args.force:
        if not check_git_status():
            print("\n  削除を中止しました。")
            print("  強制実行するには --force を付けてください（非推奨）。")
            return 1

    # 追跡
    print("\n[1/3] 到達可能ファイルを追跡中...")
    reachable = trace_reachable(ENTRY_POINTS)
    print(f"  到達可能: {len(reachable)} ファイル")

    # 収集
    print("\n[2/3] 全 .py ファイルを収集中...")
    include_tests = args.include_tests or args.only_tests
    all_files = collect_all_py_files(
        include_tests=include_tests,
        only_tests=args.only_tests,
    )
    print(f"  収集: {len(all_files)} ファイル")

    # 未使用特定
    print("\n[3/3] 未到達ファイルを特定中...")
    unused = [f for f in all_files if f not in reachable]

    print_report(all_files, reachable, unused)

    # 削除
    if args.purge:
        if not unused:
            print("\n[INFO] 削除対象がありません。")
            return 0

        # git 追跡状況を表示
        tracked = get_git_tracked_files()
        tracked_count = 0
        untracked_count = 0
        for p in unused:
            rel = str(p.relative_to(CODE_DIR)).replace("\\", "/")
            if rel in tracked:
                tracked_count += 1
            else:
                untracked_count += 1

        print(f"\n  [git 追跡状況]")
        print(f"    追跡済み（復元可能）:   {tracked_count} 件")
        print(f"    未追跡（復元不可）:     {untracked_count} 件")

        if untracked_count > 0:
            print(f"\n  ⚠️  未追跡ファイル {untracked_count} 件は git で復元できません。")
            print(f"     → 事前に 'git add . && git commit' を実行してください。")

        print(f"\n  ※ 削除後に GUI を起動して動作確認してください。")
        answer = input("\n  削除を実行しますか？ [yes/N]: ").strip().lower()
        if answer not in ("yes", "y"):
            print("  キャンセルしました。")
            return 0

        purge_files(unused)

    return 0


if __name__ == "__main__":
    sys.exit(main())