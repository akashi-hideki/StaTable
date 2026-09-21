#!/usr/bin/env python3
"""Apply C-41 documentation patch to SPEC_OVERVIEW files.

Purpose:
    Add C-41 (role functions do not auto-detect the calling layer)
    to SPEC_OVERVIEW_ja.md and SPEC_OVERVIEW_en.md.

Insertions (4 total):
    1. ja §12: C-41 row right after C-39 row
    2. ja §3.2.7: Design principle section before §3.3
    3. en §12: C-41 row right after C-39 row
    4. en §3.2.7: Design principle section before §3.3

Safety:
    - Dry-run by default (--apply to execute)
    - Idempotent: refuses to re-insert if C-41 already present
    - Creates .bak backups
    - Shows unified diff after applying
    - Verifies insertion counts

Usage:
    cd C:/Users/user/OneDrive/ドキュメント/GitHub/StaTable/code
    python tools/apply_c41_patch.py              # dry-run
    python tools/apply_c41_patch.py --apply      # execute
    python tools/apply_c41_patch.py --apply --no-backup

Verification:
    After --apply, the tool prints:
      - Insertion count per file
      - Unified diff (using difflib)
      - Recommended: git diff code/docs/ for manual review
"""

from __future__ import annotations

import argparse
import difflib
import re
import shutil
import sys
from pathlib import Path

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS = REPO_ROOT / "code" / "docs"

# ----------------------------------------------------------------------
# Insertion content
# ----------------------------------------------------------------------

C41_JA_ROW = (
    "| C-41 | Role 関数は呼び出し元層を自動識別しない | "
    "**設計上の制約** | 各層の独立性を保つため、Role 関数は "
    "layer-agnostic に設計する。呼び出し元層が必要な場合は"
    "関数を分割する（§3.2.7 参照） |"
)

C41_EN_ROW = (
    "| C-41 | Role functions do not auto-detect the calling layer | "
    "**Design constraint** | To preserve layer independence, "
    "role functions are designed layer-agnostic. If caller-layer "
    "info is needed, split the function (see §3.2.7) |"
)

PRINCIPLE_JA = """\
**設計原則（v2.3）**：Role 関数は**各層の独立性を保つ**ため、
呼び出し元層に依存しない設計とする。

#### 背景

Driver / Middleware / Application の各層は、それぞれ独立して
設計・テスト・再利用できることが望ましい。Role 関数が呼び出し元層を
識別して動作を変えると、以下の問題が生じる：

- **層間の暗黙的結合**：Driver が Application の存在を意識することになる
- **再利用性の低下**：他プロジェクトで単独利用できなくなる
- **テスト困難**：呼び出し元層を再現しないとテストできない
- **MISRA C:2012 違反リスク**：未使用引数、複雑度増加

#### 望ましい設計

層ごとに異なる動作が必要な場合、**Role 関数を分割**する：

| 層 | 専用 Role 関数（例） |
|----|-------------------|
| Application から呼ぶ | `Driver.InitForApp` |
| Middleware から呼ぶ | `Driver.InitForMiddleware` |
| 層に依存しない共通処理 | `Driver.InitCommon` |

**利点**：

- 各層が独立して進化できる
- 呼び出し元が明示的（コードを読めば分かる）
- 単体テストが容易
- レイヤリング原則に準拠

#### アンチパターン

Role 関数の冒頭で呼び出し元層を判定し、全呼び出しで分岐させる実装は
**避ける**こと。これは各層の独立性を損ない、保守性を著しく低下させる。

#### 将来の拡張

`transition_id` と `call_sites` を活用した呼び出し元層取得は、
v3.1 以降で**オプトイン**機能として提供予定。ただし、上記の
「関数分割」が引き続き**推奨**される。
"""

PRINCIPLE_EN = """\
**Design Principle (v2.3)**: Role functions must be **layer-agnostic**
to preserve the independence of each layer.

#### Background

The Driver / Middleware / Application layers should be designed,
tested, and reused independently. If a role function changes its
behavior based on the calling layer, the following problems arise:

- **Implicit coupling**: Driver becomes aware of Application's existence
- **Reduced reusability**: The function cannot be used standalone in other projects
- **Testing difficulty**: Tests must reproduce the caller layer
- **MISRA C:2012 risks**: Unused arguments, increased complexity

#### Recommended Design

When layer-specific behavior is needed, **split the role function**:

| Called from | Dedicated role function (example) |
|-------------|----------------------------------|
| Application | `Driver.InitForApp` |
| Middleware  | `Driver.InitForMiddleware` |
| Layer-agnostic common | `Driver.InitCommon` |

**Benefits**:

- Each layer can evolve independently
- The caller is explicit (visible in code)
- Unit testing is straightforward
- Complies with layering principles

#### Anti-pattern

Checking the calling layer at the top of a role function and branching
for all calls should be **avoided**. This harms layer independence and
severely reduces maintainability.

#### Future Extension

A caller-layer retrieval helper based on `transition_id` and
`call_sites` may be provided as an **opt-in** feature in v3.1+.
However, the "split functions" approach above remains **recommended**.
"""

# ----------------------------------------------------------------------
# Patch definitions
# ----------------------------------------------------------------------

PATCHES = [
    {
        "file": "SPEC_OVERVIEW_ja.md",
        "anchor_pattern": re.compile(r"^\|\s*C-39\s*\|"),
        "insert_text": C41_JA_ROW,
        "skip_if_contains": re.compile(r"^\|\s*C-41\s*\|", re.MULTILINE),
        "description": "ja §12: add C-41 row",
    },
    {
        "file": "SPEC_OVERVIEW_ja.md",
        "anchor_pattern": re.compile(r"^### 3\.3\b"),
        "insert_text": PRINCIPLE_JA + "\n",
        "skip_if_contains": re.compile(r"設計原則（v2\.3）"),
        "description": "ja §3.2.7: add design principle",
    },
    {
        "file": "SPEC_OVERVIEW_en.md",
        "anchor_pattern": re.compile(r"^\|\s*C-39\s*\|"),
        "insert_text": C41_EN_ROW,
        "skip_if_contains": re.compile(r"^\|\s*C-41\s*\|", re.MULTILINE),
        "description": "en §12: add C-41 row",
    },
    {
        "file": "SPEC_OVERVIEW_en.md",
        "anchor_pattern": re.compile(r"^### 3\.3\b"),
        "insert_text": PRINCIPLE_EN + "\n",
        "skip_if_contains": re.compile(r"Design Principle \(v2\.3\)"),
        "description": "en §3.2.7: add design principle",
    },
]


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def read_lines(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.split("\n")


def write_lines(path: Path, lines: list[str]) -> None:
    text = "\n".join(lines)
    path.write_text(text, encoding="utf-8", newline="\n")


def find_anchor_index(lines: list[str], pattern: re.Pattern) -> int | None:
    for i, line in enumerate(lines):
        if pattern.search(line):
            return i
    return None


# ----------------------------------------------------------------------
# Apply
# ----------------------------------------------------------------------

def apply_patch(patch: dict, apply: bool, backup: bool) -> dict:
    path = DOCS / patch["file"]
    result = {
        "description": patch["description"],
        "file": patch["file"],
        "status": "unknown",
        "detail": "",
        "anchor_line": None,
    }

    if not path.exists():
        result["status"] = "MISSING"
        result["detail"] = f"file not found: {path}"
        return result

    original_text = path.read_text(encoding="utf-8")
    lines = read_lines(path)

    if patch["skip_if_contains"].search(original_text):
        result["status"] = "ALREADY_APPLIED"
        result["detail"] = "target text already present"
        return result

    anchor_idx = find_anchor_index(lines, patch["anchor_pattern"])
    if anchor_idx is None:
        result["status"] = "ANCHOR_NOT_FOUND"
        result["detail"] = (
            f"anchor pattern not found: {patch['anchor_pattern'].pattern}"
        )
        return result

    result["anchor_line"] = anchor_idx + 1

    # --- Insert strategy depends on patch ---
    insert_text = patch["insert_text"]
    if "\n" in insert_text:
        # Multi-line: insert before anchor (add blank line separation)
        new_lines = lines[:anchor_idx] + [""] + insert_text.split("\n") + lines[anchor_idx:]
    else:
        # Single-line (table row): insert after anchor
        new_lines = (
            lines[: anchor_idx + 1]
            + [insert_text]
            + lines[anchor_idx + 1 :]
        )

    result["status"] = "WOULD_APPLY" if not apply else "APPLIED"
    result["detail"] = f"anchor at line {anchor_idx + 1}"

    if apply:
        if backup:
            bak = path.with_suffix(path.suffix + ".bak")
            shutil.copy2(path, bak)
        write_lines(path, new_lines)

    return result


# ----------------------------------------------------------------------
# Diff display
# ----------------------------------------------------------------------

def show_diff(path: Path) -> None:
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        print(f"  (no backup for diff: {bak})")
        return

    old = bak.read_text(encoding="utf-8").splitlines(keepends=True)
    new = path.read_text(encoding="utf-8").splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        old, new,
        fromfile=f"a/{path.name}",
        tofile=f"b/{path.name}",
        lineterm="",
        n=2,
    ))
    if not diff:
        print("  (no diff)")
        return
    for line in diff:
        print(f"  {line.rstrip()}")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true",
                    help="Execute the patch (default is dry-run).")
    ap.add_argument("--no-backup", action="store_true",
                    help="Skip creating .bak files.")
    ap.add_argument("--show-diff", action="store_true",
                    help="Show unified diff after applying (uses .bak).")
    return ap.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    apply = args.apply
    backup = not args.no_backup

    print("=" * 70)
    print(f"  C-41 doc patch  root={REPO_ROOT}")
    print(f"  mode   = {'APPLY' if apply else 'DRY-RUN'}")
    print(f"  backup = {backup}")
    print("=" * 70)

    results = [apply_patch(p, apply=apply, backup=backup) for p in PATCHES]

    print("\n--- Results ---")
    for r in results:
        print(f"  {r['status']:<18} {r['file']:<25} {r['detail']}")

    # Summary
    applied = sum(1 for r in results if r["status"] in ("APPLIED", "WOULD_APPLY"))
    skipped = sum(1 for r in results if r["status"] == "ALREADY_APPLIED")
    errors = [r for r in results if r["status"] in ("MISSING", "ANCHOR_NOT_FOUND")]

    print(f"\n  Applied: {applied}  Skipped: {skipped}  Errors: {len(errors)}")

    if errors:
        print("\n  ERROR: some patches failed. See above.")
        return 1

    if not apply:
        print("\n" + "=" * 70)
        print("  DRY-RUN complete. Re-run with --apply to execute.")
        print("=" * 70)
        return 0

    # --- Applied: show diff if requested ---
    if args.show_diff:
        print("\n--- Unified diff (from .bak) ---")
        for fname in sorted({r["file"] for r in results}):
            path = DOCS / fname
            print(f"\n### {fname}")
            show_diff(path)

    # --- Verification ---
    print("\n--- Verification ---")
    for fname in sorted({r["file"] for r in results}):
        path = DOCS / fname
        text = path.read_text(encoding="utf-8")
        c41_count = len(re.findall(r"^\|\s*C-41\s*\|", text, re.MULTILINE))
        principle_count = len(re.findall(r"設計原則（v2\.3）|Design Principle \(v2\.3\)", text))
        print(f"  {fname}:")
        print(f"    C-41 rows        : {c41_count} (expected 1)")
        print(f"    Design principle : {principle_count} (expected 1)")

    print("\n" + "=" * 70)
    print("  DONE. Recommended for manual review:")
    print("    git diff code/docs/SPEC_OVERVIEW_ja.md")
    print("    git diff code/docs/SPEC_OVERVIEW_en.md")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))