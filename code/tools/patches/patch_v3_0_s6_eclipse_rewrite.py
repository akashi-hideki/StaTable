# code/tools/patches/patch_v3_0_s6_eclipse_rewrite.py
r"""
v3.0 fix: rewrite Eclipse guide with correct paths.

- Method A (recommended): python -m statable.cli (PATH-independent)
- Method B: statable-cli.exe (user-install path %APPDATA%)

Usage:
    cd code
    python tools\patches\patch_v3_0_s6_eclipse_rewrite.py
    python tools\patches\patch_v3_0_s6_eclipse_rewrite.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
TARGET = CODE / "docs" / "ECLIPSE_INTEGRATION_ja.md"

GUIDE = r"""# Eclipse External Tools 連携ガイド

Eclipse IDE の **External Tools** 機能から StaTable の CLI を呼び出し、
GUI を起動せずに設計 XML から C コードを生成する手順です。

---

## 1. 前提

- Python 3.10 以上（本ガイドでは 3.13 で検証）
- StaTable SDK のインストール
- Eclipse IDE

### 1.1 StaTable のインストール

    cd StaTable/code
    pip install -e .

### 1.2 インストール先の確認

`pip install -e .` 直後、`statable-cli.exe` は次のいずれかに配置されます:

- **システムインストール**: `C:\Program Files\Python313\Scripts\`
- **ユーザーインストール**: `%APPDATA%\Python\Python313\Scripts\`
  （`C:\Users\<you>\AppData\Roaming\Python\Python313\Scripts\`）

確認コマンド:

    python -c "import shutil; print(shutil.which('statable-cli') or 'NOT FOUND')"

**NOT FOUND** の場合はユーザーインストール先にあります。以下で確認:

    Get-ChildItem "$env:APPDATA\Python\Python313\Scripts\statable-cli.exe"

---

## 2. 方法 A（推奨）: python -m 経由

**PATH の影響を受けない**ため、どのインストール形態でも動作します。

### 2.1 External Tools Configurations を開く

1. **Run → External Tools → External Tools Configurations...**
2. 左ペインで **Program** を選択
3. **New launch configuration** アイコンをクリック

### 2.2 設定値

| フィールド | 値 |
|-----------|-----|
| **Name** | `StaTable Generate` |
| **Location** | `C:\Program Files\Python313\python.exe` |
| **Working Directory** | `${project_loc}` |
| **Arguments** | `-m statable.cli generate --xml ${resource_loc} --out ${project_loc}/generated --format json` |

### 2.3 Environment タブ（重要）

`pip install -e .` を実行していない場合は、StaTable の `code/` を `PYTHONPATH` に追加:

- **Variable**: `PYTHONPATH`
- **Value**: `C:\path\to\StaTable\code`

### 2.4 Common タブ

- **Display in favorites menu**: チェック
- **Allocate Console**: チェック

### 2.5 実行

1. プロジェクト内の設計 XML を選択
2. **Run → External Tools → StaTable Generate**
3. Console ビューに JSON 結果が表示され、`generated/` に C コードが出力される

---

## 3. 方法 B: statable-cli.exe 直接指定

PATH が通っている、またはフルパス指定で使う場合の方法です。

| フィールド | 値 |
|-----------|-----|
| **Name** | `StaTable Generate (direct)` |
| **Location** | `%APPDATA%\Python\Python313\Scripts\statable-cli.exe` |
| **Working Directory** | `${project_loc}` |
| **Arguments** | `generate --xml ${resource_loc} --out ${project_loc}/generated --format json` |

> **注意**: システムインストールの場合は
> `C:\Program Files\Python313\Scripts\statable-cli.exe` を指定してください。

---

## 4. 検証用 External Tool

設計 XML の検証のみを行う設定例:

| フィールド | 値 |
|-----------|-----|
| **Name** | `StaTable Validate` |
| **Location** | `C:\Program Files\Python313\python.exe` |
| **Working Directory** | `${project_loc}` |
| **Arguments** | `-m statable.cli validate --xml ${resource_loc} --format json --exit-on-error` |

- 検証エラー時は終了コード 1 で Eclipse がエラー通知
- 結果は Console ビューに JSON で表示

---

## 5. トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| `statable-cli` が見つからない | ユーザーインストール先に配置、PATH 未登録 | 方法 A を使用するか、フルパス指定 |
| `No module named 'statable'` | pip インストール未実施 | `pip install -e .` 実行 |
| `No module named 'statable'` (方法 A) | PYTHONPATH 未設定 | Environment タブで設定 |
| `XML file not found` | XML 以外を選択 | プロジェクト内の `.xml` を選択して実行 |
| 日本語パスで文字化け | Console エンコーディング | `Window → Preferences → General → Workspace → Text file encoding` を UTF-8 に |
| 出力先に書き込めない | アクセス権限 | `${project_loc}/generated` を手動作成、または Administrator で Eclipse 起動 |

---

## 6. 関連ドキュメント

- CLI コマンドリファレンス: [`examples/cli_guide.md`](../examples/cli_guide.md)
- SDK API リファレンス §2.6: [`SPEC_SDK_API_ja.md`](SPEC_SDK_API_ja.md)

---

## 7. 改訂履歴

| 日付 | 版 | 内容 |
|------|----|------|
| 2026-09-29 | 1.0 | 初版（v3.0 Phase S-5） |
| 2026-09-29 | 1.1 | 方法 A/B を実環境に合わせて修正、PATH 非依存化 |
"""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_0_s6_eclipse_rewrite  [{mode}]")
    print("=" * 70)

    if TARGET.exists():
        old = TARGET.read_text(encoding="utf-8")
        if "python -m statable.cli generate" in old and \
           "%APPDATA%" in old:
            print("[SKIP] already rewritten")
            return 0
        print(f"[APPLY] backup and rewrite {TARGET.name}")
        if not args.apply:
            print()
            print("[DRY-RUN] no file written; pass --apply to execute.")
            return 0
        bak = TARGET.with_suffix(TARGET.suffix + ".bak_s6")
        if not bak.exists():
            bak.write_text(old, encoding="utf-8")
            print(f"  Backup: {bak.name}")
    else:
        print(f"[APPLY] create {TARGET.name}")
        if not args.apply:
            print()
            print("[DRY-RUN] no file written; pass --apply to execute.")
            return 0

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(GUIDE, encoding="utf-8")
    print(f"[DONE] {TARGET.name} written ({len(GUIDE)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
