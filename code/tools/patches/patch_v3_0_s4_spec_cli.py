# code/tools/patches/patch_v3_0_s4_spec_cli.py
r"""
Phase S-4 patch (A): add CLI section to SPEC_SDK_API_ja.md / _en.md.

Inserts section 2.6 (CLI usage) before section 3 in both files.

Usage:
    cd code
    python tools\patches\patch_v3_0_s4_spec_cli.py
    python tools\patches\patch_v3_0_s4_spec_cli.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
DOCS = CODE / "docs"
SPEC_JA = DOCS / "SPEC_SDK_API_ja.md"
SPEC_EN = DOCS / "SPEC_SDK_API_en.md"
ANCHOR = "## 3. "

JA_SECTION = '''### 2.6 CLI 使用法

`statable-cli` コマンドで GUI なしで実行できます。

**インストール**

    pip install statable          # SDK + CLI
    pip install "statable[gui]"   # GUI も含む

**バージョン確認**

    statable-cli version

**コード生成**

    statable-cli generate --xml design.xml --out generated/ --format json

**検証**

    statable-cli validate --xml design.xml --format json --exit-on-error

**終了コード**

| コード | 意味 |
|:---:|------|
| 0 | 成功 |
| 1 | 検証エラー |
| 2 | 内部エラー |

**出力形式**

- `--format json`（デフォルト）: stdout に JSON
- `--format text`: 人間可読テキスト
- ログ・エラーは stderr に出力

'''

EN_SECTION = '''### 2.6 CLI Usage

The `statable-cli` command runs without the GUI.

**Installation**

    pip install statable
    pip install "statable[gui]"

**Version**

    statable-cli version

**Code generation**

    statable-cli generate --xml design.xml --out generated/ --format json

**Validation**

    statable-cli validate --xml design.xml --format json --exit-on-error

**Exit codes**

| Code | Meaning |
|:---:|------|
| 0 | Success |
| 1 | Validation error |
| 2 | Internal error |

**Output**

- `--format json`: JSON on stdout (default)
- `--format text`: human-readable
- Logs go to stderr

'''


def _hdr(mode):
    print("=" * 70)
    print(f"  patch_v3_0_s4_spec_cli  [{mode}]")
    print("=" * 70)


def _backup_once(path):
    bak = path.with_suffix(path.suffix + ".bak_s4")
    if not bak.exists():
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"  Backup: {bak.name}")


def edit_spec(path, section, skip_marker, tag, apply):
    rel = path.relative_to(CODE.parent)
    if not path.exists():
        print(f"[FAIL] {tag}: not found: {rel}")
        return 1
    text = path.read_text(encoding="utf-8")
    if skip_marker in text:
        print(f"[SKIP] {tag}: already has section 2.6")
        return 0
    n = text.count(ANCHOR)
    if n == 0:
        print(f"[FAIL] {tag}: anchor not found")
        return 1
    if n > 1:
        print(f"[FAIL] {tag}: anchor found {n} times")
        return 1
    idx = text.find(ANCHOR)
    new_text = text[:idx] + section + text[idx:]
    print(f"[APPLY] {tag}: insert before anchor at offset {idx}")
    if not apply:
        return 0
    _backup_once(path)
    path.write_text(new_text, encoding="utf-8")
    print(f"[DONE] {rel} updated")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    mode = "APPLY" if args.apply else "DRY-RUN"
    _hdr(mode)
    rc = 0
    rc |= edit_spec(SPEC_JA, JA_SECTION, "### 2.6 CLI 使用法",
                    "E1 SPEC_SDK_API_ja.md", args.apply)
    print()
    rc |= edit_spec(SPEC_EN, EN_SECTION, "### 2.6 CLI Usage",
                    "E2 SPEC_SDK_API_en.md", args.apply)
    print()
    if not args.apply:
        print("[DRY-RUN] no file written; pass --apply to execute.")
    else:
        print("Verify:")
        print("  Select-String docs\\SPEC_SDK_API_ja.md -Pattern '### 2.6'")
    return rc


if __name__ == "__main__":
    sys.exit(main())
