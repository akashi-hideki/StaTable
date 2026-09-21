#!/usr/bin/env python3
"""
Automated SPEC document updater for StaTable (v2).

Applies version bumps, section replacements, and new entries to
docs/SPEC_OVERVIEW_{ja,en}.md and docs/SPEC_SCREENS_{ja,en}.md.

Patch types
-----------
  - Replacement       : literal (old -> new) string replacement
  - RegexReplacement  : regex-based replacement
  - InsertAfter       : insert text after the first line matching an
                        anchor regex
  - InsertAfterBlock  : insert text after the last line of a
                        Markdown "row block" that starts at the anchor
                        (continuation lines starting with '|' are
                        consumed as part of the same block)
  - AppendTableRow    : append a row to the LAST consecutive row of a
                        Markdown table whose header matches header_regex

Run modes
---------
  --dry-run   (default) show what would change; write nothing
  --apply     apply changes; creates .bak copies unless --no-backup

Usage
-----
  python tools/update_spec_docs.py
  python tools/update_spec_docs.py --apply
  python tools/update_spec_docs.py --file SPEC_OVERVIEW_ja.md
"""

from __future__ import annotations

import argparse
import difflib
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


# ======================================================================
# Patch types
# ======================================================================
@dataclass
class Replacement:
    description: str
    old: str
    new: str
    required: bool = True
    count: int = 1


@dataclass
class RegexReplacement:
    description: str
    pattern: str
    repl: str
    required: bool = True
    flags: int = 0


@dataclass
class InsertAfter:
    description: str
    anchor: str
    insert_text: str
    required: bool = True


@dataclass
class InsertAfterBlock:
    """Insert text after the last line of a Markdown row block.

    The block starts at the first line matching `anchor` and continues
    while subsequent lines begin with '|' (continuation rows). Use this
    for multi-line table entries such as the Revision History.
    """
    description: str
    anchor: str
    insert_text: str
    required: bool = True


@dataclass
class AppendTableRow:
    description: str
    header_regex: str
    row: str
    required: bool = True


@dataclass
class FileUpdate:
    file_path: str
    patches: List = field(default_factory=list)


# ======================================================================
# Patch engine
# ======================================================================
class PatchResult:
    def __init__(self, description: str):
        self.description = description
        self.status = "PENDING"
        self.message = ""

    def ok(self, msg: str = ""):
        self.status = "APPLIED"
        self.message = msg

    def skip(self, msg: str = ""):
        self.status = "SKIPPED"
        self.message = msg

    def fail(self, msg: str = ""):
        self.status = "FAILED"
        self.message = msg


def _apply_replacement(text: str, p: Replacement):
    r = PatchResult(p.description)
    n = text.count(p.old)
    if n == 0:
        (r.fail if p.required else r.skip)(f"anchor not found: {p.old[:60]!r}")
        return r, text
    if p.count > 0 and n != p.count:
        r.fail(f"expected {p.count} occurrence(s), found {n}")
        return r, text
    new_text = text.replace(p.old, p.new, p.count if p.count > 0 else -1)
    r.ok(f"replaced {n} occurrence(s)")
    return r, new_text


def _apply_regex(text: str, p: RegexReplacement):
    r = PatchResult(p.description)
    flags = p.flags | re.MULTILINE
    matches = list(re.finditer(p.pattern, text, flags))
    if not matches:
        (r.fail if p.required else r.skip)(f"pattern not found: {p.pattern[:60]!r}")
        return r, text
    new_text = re.sub(p.pattern, p.repl, text, flags=flags)
    r.ok(f"replaced {len(matches)} match(es)")
    return r, new_text


def _apply_insert_after(text: str, p: InsertAfter):
    r = PatchResult(p.description)
    lines = text.splitlines(keepends=True)
    anchor_re = re.compile(p.anchor)
    for i, line in enumerate(lines):
        if anchor_re.search(line):
            lines.insert(i + 1, p.insert_text)
            r.ok(f"inserted after line {i + 1}")
            return r, "".join(lines)
    (r.fail if p.required else r.skip)(f"anchor not found: {p.anchor!r}")
    return r, text


def _apply_insert_after_block(text: str, p: InsertAfterBlock):
    """Insert after the LAST line of the row block starting at anchor.

    A "row block" starts at the anchor line and continues while the
    next line begins with '|' (Markdown table continuation).
    """
    r = PatchResult(p.description)
    lines = text.splitlines(keepends=True)
    anchor_re = re.compile(p.anchor)

    start = None
    for i, line in enumerate(lines):
        if anchor_re.search(line):
            start = i
            break
    if start is None:
        (r.fail if p.required else r.skip)(f"anchor not found: {p.anchor!r}")
        return r, text

    # Advance while lines still start with '|'
    end = start
    j = start + 1
    while j < len(lines) and lines[j].lstrip().startswith("|"):
        end = j
        j += 1

    insert_at = end + 1
    lines.insert(insert_at, p.insert_text)
    r.ok(f"inserted after block ending at line {end + 1}")
    return r, "".join(lines)


def _apply_append_table_row(text: str, p: AppendTableRow):
    r = PatchResult(p.description)
    lines = text.splitlines(keepends=True)
    header_re = re.compile(p.header_regex)

    header_idx = None
    for i, line in enumerate(lines):
        if header_re.search(line):
            header_idx = i
            break
    if header_idx is None:
        (r.fail if p.required else r.skip)(
            f"table header not found: {p.header_regex!r}")
        return r, text

    # Skip separator row "|---|"
    j = header_idx + 1
    if j < len(lines) and "---" in lines[j]:
        j += 1
    last_row = j - 1
    while j < len(lines) and lines[j].lstrip().startswith("|"):
        last_row = j
        j += 1

    insert_at = last_row + 1
    lines.insert(insert_at, p.row if p.row.endswith("\n") else p.row + "\n")
    r.ok(f"appended row after line {insert_at}")
    return r, "".join(lines)


def _apply_patch(text: str, patch):
    if isinstance(patch, Replacement):
        return _apply_replacement(text, patch)
    if isinstance(patch, RegexReplacement):
        return _apply_regex(text, patch)
    if isinstance(patch, InsertAfter):
        return _apply_insert_after(text, patch)
    if isinstance(patch, InsertAfterBlock):
        return _apply_insert_after_block(text, patch)
    if isinstance(patch, AppendTableRow):
        return _apply_append_table_row(text, patch)
    raise TypeError(f"Unknown patch type: {type(patch)}")


# ======================================================================
# Patch definitions (v2.4)
# ======================================================================
TODAY = "2026-09-22"
NEW_SPEC_VERSION = "2.4"


def _overview_patches(ja: bool) -> List:
    """SPEC_OVERVIEW_{ja,en}.md patches."""
    p = []

    # 1) Version header
    p.append(Replacement(
        description="Version header: 2.3 -> 2.4",
        old="Version: 2.3\nDate: 2026-09-21",
        new=f"Version: {NEW_SPEC_VERSION}\nDate: {TODAY}",
        required=False,
    ))

    # 2) Known Constraints rows (language-specific)
    if ja:
        # Japanese header is "| # | 項目 | 状態 | 影響 |"
        header = r"^\|\s*#\s*\|\s*項目\s*\|"
        rows = [
            "| C-42 | RoleFunction 予約フィールドの GUI 非表示化 | **v2.4 で変更** | return_type / arg1_* / arg2_* は UI から削除。RoleFunctionDialog は `_original` から引き継ぎ |",
            "| C-43 | `libcntrl.RoleFunction` の予約フィールド | **v1.5 で追加** | return_type / arg1_* / arg2_* を保持し XML ラウンドトリップで予約値を維持 |",
            "| C-44 | Namespace コンボボックスの候補 | **v3.11 で全タブ対応** | `layer_names_provider` 経由で全タブ名を候補に追加 |",
            "| C-45 | 空の `used_*` 属性 | **v3.8.1 で出力抑制** | 空の used_global_vars / used_events / used_literals は XML 属性として出力しない |",
            "| C-46 | State.do / RoleFunction の予約フィールド | **予約（Reserved）** | UI 非表示。codegen 未使用。XML I/O で保持（v3.7 以降） |",
        ]
    else:
        header = r"^\|\s*#\s*\|\s*Item\s*\|"
        rows = [
            "| C-42 | RoleFunction reserved fields hidden from GUI | **Changed in v2.4** | return_type / arg1_* / arg2_* removed from UI. RoleFunctionDialog carries them forward from `_original` |",
            "| C-43 | Reserved fields in `libcntrl.RoleFunction` | **Added in v1.5** | return_type / arg1_* / arg2_* kept and preserved through XML round-trip |",
            "| C-44 | Namespace combo box candidates | **v3.11 covers all tabs** | `layer_names_provider` supplies every tab name |",
            "| C-45 | Empty `used_*` attributes | **Suppressed in v3.8.1** | Empty used_global_vars / used_events / used_literals are not written to XML |",
            "| C-46 | State.do / RoleFunction reserved fields | **Reserved** | Not shown in UI. Not used by codegen. Preserved in XML I/O (since v3.7) |",
        ]
    for row in rows:
        p.append(AppendTableRow(
            description=f"Known Constraints: {row.split('|')[1].strip()}",
            header_regex=header,
            row=row,
            required=False,
        ))

    # 3) Revision history: insert AFTER the full v2.3 block
    if ja:
        rev = (
            f"| {NEW_SPEC_VERSION} | {TODAY} | UI 整理・予約フィールド・Namespace コンボ対応： |\n"
            f"| | | - §1.4: テストスイートは 551 PASS / 2 SKIP のまま |\n"
            f"| | | - §3.2.7: `RoleFunction.used_global_vars/events/literals` 追加を明記 |\n"
            f"| | | - §3.5.2: 空の `used_*` は属性出力しない（v3.8.1） |\n"
            f"| | | - §4.2: MainWindow v2.4（`_get_all_layer_names()` 追加） |\n"
            f"| | | - §4.3: StateMachineTab v3.11（`layer_names_provider` 配線） |\n"
            f"| | | - §4.6: State list 5列 / Role function 4列 / Namespace インラインコンボ |\n"
            f"| | | - §5.3: libcntrl.RoleFunction v1.5（予約フィールド追加） |\n"
            f"| | | - §12: C-42〜C-46 追加 |\n"
            f"| | | - §15: 本エントリ |"
        )
        anchor = r"^\|\s*2\.3\s*\|"
    else:
        rev = (
            f"| {NEW_SPEC_VERSION} | {TODAY} | UI cleanup / reserved fields / namespace combo: |\n"
            f"| | | - §1.4: test suites remain 551 PASS / 2 SKIP |\n"
            f"| | | - §3.2.7: documented `RoleFunction.used_global_vars/events/literals` |\n"
            f"| | | - §3.5.2: empty `used_*` attributes are not written (v3.8.1) |\n"
            f"| | | - §4.2: MainWindow v2.4 (added `_get_all_layer_names()`) |\n"
            f"| | | - §4.3: StateMachineTab v3.11 (`layer_names_provider` wiring) |\n"
            f"| | | - §4.6: State list 5 cols / Role function 4 cols / Namespace inline combo |\n"
            f"| | | - §5.3: libcntrl.RoleFunction v1.5 (reserved fields added) |\n"
            f"| | | - §12: C-42..C-46 added |\n"
            f"| | | - §15: this entry |"
        )
        anchor = r"^\|\s*2\.3\s*\|"
    p.append(InsertAfterBlock(
        description="Revision history: insert v2.4 entry",
        anchor=anchor,
        insert_text=rev,
        required=False,
    ))

    return p


def _screens_patches(ja: bool) -> List:
    """SPEC_SCREENS_{ja,en}.md patches."""
    p = []

    p.append(Replacement(
        description="Version header: 2.3 -> 2.4",
        old="Version: 2.3\nDate: 2026-09-21",
        new=f"Version: {NEW_SPEC_VERSION}\nDate: {TODAY}",
        required=False,
    ))

    # §5.4 layer_names_provider note
    if ja:
        note = (
            "\n### 5.4 v3.11 追加配線\n\n"
            "| 項目 | 内容 |\n"
            "|------|------|\n"
            "| `layer_names_provider` | `StateMachineTab` が `SettingsPanel` に伝播 |\n"
            "| 用途 | Namespace コンボボックスに全タブのレイヤ名を候補表示 |\n"
            "| 追加元 | `MainWindow._get_all_layer_names()`（v2.4） |\n"
        )
    else:
        note = (
            "\n### 5.4 v3.11 Wiring Addition\n\n"
            "| Item | Content |\n"
            "|------|---------|\n"
            "| `layer_names_provider` | Forwarded by `StateMachineTab` to `SettingsPanel` |\n"
            "| Purpose | Populate the Namespace combo box with all tab names |\n"
            "| Source | `MainWindow._get_all_layer_names()` (v2.4) |\n"
        )
    p.append(InsertAfter(
        description="§5.4 layer_names_provider note",
        anchor=r"^self\.settings\.settings_changed\.connect\(self\.dataModified\)",
        insert_text=note,
        required=False,
    ))

    # Revision history
    if ja:
        rev = (
            f"| {NEW_SPEC_VERSION} | {TODAY} | UI 整理・Namespace コンボ対応： |\n"
            f"| | | - §5.4: `layer_names_provider` 配線を追記 |\n"
            f"| | | - §11: 改訂履歴（本エントリ） |"
        )
        anchor = r"^\|\s*2\.3\s*\|"
    else:
        rev = (
            f"| {NEW_SPEC_VERSION} | {TODAY} | UI cleanup / namespace combo: |\n"
            f"| | | - §5.4: documented `layer_names_provider` wiring |\n"
            f"| | | - §11: revision history (this entry) |"
        )
        anchor = r"^\|\s*2\.3\s*\|"
    p.append(InsertAfterBlock(
        description="Revision history: insert v2.4 entry",
        anchor=anchor,
        insert_text=rev,
        required=False,
    ))

    return p


def build_patches() -> List[FileUpdate]:
    return [
        FileUpdate("docs/SPEC_OVERVIEW_ja.md", _overview_patches(ja=True)),
        FileUpdate("docs/SPEC_OVERVIEW_en.md", _overview_patches(ja=False)),
        FileUpdate("docs/SPEC_SCREENS_ja.md", _screens_patches(ja=True)),
        FileUpdate("docs/SPEC_SCREENS_en.md", _screens_patches(ja=False)),
    ]


# ======================================================================
# Driver
# ======================================================================
def process_file(update: FileUpdate, root: Path, apply: bool,
                 backup: bool) -> bool:
    path = root / update.file_path
    print()
    print("=" * 78)
    print(f"  {update.file_path}")
    print("=" * 78)

    if not path.exists():
        print(f"  [SKIP] file not found: {path}")
        return True

    original = path.read_text(encoding="utf-8")
    text = original

    results: List[PatchResult] = []
    for patch in update.patches:
        res, text = _apply_patch(text, patch)
        results.append(res)
        marker = {
            "APPLIED": "OK  ",
            "SKIPPED": "SKIP",
            "FAILED": "FAIL",
        }.get(res.status, "??  ")
        print(f"  [{marker}] {res.description}")
        if res.message:
            print(f"         {res.message}")

    failures = [r for r in results if r.status == "FAILED"]
    applied = [r for r in results if r.status == "APPLIED"]

    print()
    print(f"  Applied : {len(applied)}")
    print(f"  Skipped : {len([r for r in results if r.status == 'SKIPPED'])}")
    print(f"  Failed  : {len(failures)}")

    if text == original:
        print("  [INFO] no changes")
        return len(failures) == 0

    print()
    print("  --- diff preview (first 40 lines) ---")
    diff = list(difflib.unified_diff(
        original.splitlines(keepends=True),
        text.splitlines(keepends=True),
        fromfile="before", tofile="after", n=1,
    ))
    for line in diff[:40]:
        sys.stdout.write("    " + line if line.endswith("\n")
                         else "    " + line + "\n")
    if len(diff) > 40:
        print(f"    ... ({len(diff) - 40} more lines)")

    if not apply:
        print()
        print("  [DRY-RUN] not written (use --apply)")
        return len(failures) == 0

    if backup:
        bak = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, bak)
        print(f"  [BACKUP] {bak}")

    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"  [WRITTEN] {path}")
    return len(failures) == 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Repository root")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    ap.add_argument("--file", default=None)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    apply = args.apply
    backup = not args.no_backup

    print("=" * 78)
    print("  StaTable SPEC document updater")
    print("=" * 78)
    print(f"  Root      : {root}")
    print(f"  Mode      : {'APPLY' if apply else 'DRY-RUN'}")
    print(f"  Backup    : {backup}")
    print(f"  Spec ver  : {NEW_SPEC_VERSION}")
    print(f"  Date      : {TODAY}")

    all_ok = True
    for update in build_patches():
        if args.file and Path(update.file_path).name != args.file:
            continue
        all_ok = process_file(update, root, apply, backup) and all_ok

    print()
    print("=" * 78)
    print(f"  Overall: {'OK' if all_ok else 'SOME PATCHES FAILED'}")
    print("=" * 78)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())