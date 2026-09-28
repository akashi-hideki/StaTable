# Eclipse External Tools 連携ガイド

Eclipse IDE の **External Tools** 機能から `statable-cli` を呼び出し、
GUI を起動せずに設計 XML から C コードを生成する手順です。

---

## 1. 前提

- Python 3.10 以上（本ガイドでは 3.13 で検証）
- StaTable SDK のインストール
- Eclipse IDE（Pleiades 日本語化版でも可）

### 1.1 StaTable のインストール

    cd StaTable/code
    pip install -e .

これで `statable-cli` コマンドが PATH に追加されます。

**インストール確認**:

    statable-cli version

未インストールの場合は `python -m statable.cli` で代用できます（方法 B 参照）。

---

## 2. External Tools 設定（方法 A: statable-cli）

### 2.1 External Tools Configurations を開く

1. Eclipse メニュー: **Run → External Tools → External Tools Configurations...**
2. 左ペインで **Program** を選択
3. ツールバーの **New launch configuration** アイコンをクリック

### 2.2 基本設定

| フィールド | 値 |
|-----------|-----|
| **Name** | `StaTable Generate` |
| **Location** | `C:\Program Files\Python313\Scripts\statable-cli.exe` |
| **Working Directory** | `${project_loc}` |
| **Arguments** | `generate --xml ${resource_loc} --out ${project_loc}/generated --format json` |

> **Note**: `Location` は `pip install` 先によって異なります。
> 以下で確認できます:
>
>     python -c "import shutil; print(shutil.which('statable-cli'))"

### 2.3 Common タブ

- **Display in favorites menu**: チェック（External Tools ボタンから実行可能）
- **Allocate Console**: チェック（JSON 結果を Console ビューに表示）

### 2.4 実行

1. プロジェクト内の設計 XML を選択
2. **Run → External Tools → StaTable Generate**
3. Eclipse の Console ビューに JSON 結果が表示される
4. プロジェクトの `generated/` フォルダに C コードが出力される

---

## 3. External Tools 設定（方法 B: python -m）

`statable-cli` が PATH にない環境でも動作します。

| フィールド | 値 |
|-----------|-----|
| **Name** | `StaTable Generate (python -m)` |
| **Location** | `C:\Program Files\Python313\python.exe` |
| **Working Directory** | `${project_loc}` |
| **Arguments** | `-m statable.cli generate --xml ${resource_loc} --out ${project_loc}/generated --format json` |

> **注意**: 方法 B では StaTable の `code/` ディレクトリが `PYTHONPATH` に
> 含まれている必要があります。External Tools の **Environment** タブで:
>
> - **Variable**: `PYTHONPATH`
> - **Value**: `C:\path\to\StaTable\code`
>
> または `pip install -e .` で編集可能モードでインストールすれば
> `PYTHONPATH` 不要です。

---

## 4. 検証用 External Tool

設計 XML の検証のみを行う設定例:

| フィールド | 値 |
|-----------|-----|
| **Name** | `StaTable Validate` |
| **Location** | `C:\Program Files\Python313\Scripts\statable-cli.exe` |
| **Working Directory** | `${project_loc}` |
| **Arguments** | `validate --xml ${resource_loc} --format json --exit-on-error` |

- 検証エラーがある場合、終了コード 1 で Eclipse がエラーを通知
- 結果は Console ビューに JSON で表示

---

## 5. トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| `statable-cli` が見つからない | pip インストール未実施 | `pip install -e .` 実行、または方法 B を使用 |
| `ModuleNotFoundError: No module named 'statable'` | `PYTHONPATH` 未設定（方法 B） | Environment タブで設定 |
| `error: XML file not found` | `${resource_loc}` が XML 以外 | プロジェクト内の `.xml` を選択して実行 |
| 日本語パスで文字化け | Console エンコーディング | `Window → Preferences → General → Workspace → Text file encoding` を UTF-8 に |
| 出力先に書き込めない | アクセス権限 | `${project_loc}/generated` を手動作成、または Administrator で Eclipse 起動 |

---

## 6. 関連ドキュメント

- CLI コマンドリファレンス: [`examples/cli_guide.md`](../examples/cli_guide.md)
- SDK API リファレンス §2.6: [`SPEC_SDK_API_ja.md`](SPEC_SDK_API_ja.md)
- SmartConfig 連携: `SMARTCONFIG_INTEGRATION_ja.md`（v3.0 Phase S-6 で作成予定）

---

## 7. 改訂履歴

| 日付 | 版 | 内容 |
|------|----|------|
| 2026-09-29 | 1.0 | 初版（v3.0 Phase S-5） |
