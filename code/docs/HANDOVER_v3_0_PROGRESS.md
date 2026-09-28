# v3.0 進捗記録 — S-6 スキップ + Eclipse 検証完了

Version: 3.0 (progress notes)
Date: 2026-09-29
Base: v2.8.0 (aca01bd) → b4a288d

---

## S-6 スキップ決定

**SmartConfig（ルネサス専用ツール）は対応不要。**

理由:
- S-5 Eclipse 連携で「外部ツール連携」の柱は達成
- SmartConfig は特定ベンダ専用、汎用性なし
- G-1/G-2 の SDK 本質作業を優先

代替: **Eclipse External Tools 等価検証を実施**（S-6-Verify）

---

## Eclipse External Tools 等価検証（2026-09-29）

Eclipse 未インストール環境のため、External Tools が実行する
コマンドを PowerShell で完全再現して検証。

### 検証結果

| 検証項目 | 期待値 | 実測値 | 判定 |
|---------|-------|-------|------|
| Method A Generate (`python -m statable.cli generate`) | status ok | 16ファイル生成 | OK |
| Method A Validate (`python -m statable.cli validate`) | exit 0 | 0 | OK |
| Method B Generate (`statable-cli.exe` フルパス) | status ok | 16ファイル生成 | OK |
| Method B Validate | exit 0 | 0 | OK |
| Missing file | exit 2 | 2 | OK |
| Success case | exit 0 | 0 | OK |

### 環境

- Python: `C:\Program Files\Python313\python.exe`
- statable-cli: `%APPDATA%\Python\Python313\Scripts\statable-cli.exe`
- pip install: user install (`pip install -e .`)

### PowerShell の注意点

`statable-cli validate` は stderr にログを出力する。
PowerShell は stderr 出力を `NativeCommandError` として扱い、
`$LASTEXITCODE = -1` を返す場合がある。

**対処**: `2>$null 1>$null` で stdout/stderr を抑制すれば
正しい exit code が取得できる。

**Eclipse では影響なし** — Eclipse は stdout/stderr を別扱いし、
exit code を直接受け取るため。

### ガイドへの反映

`docs/ECLIPSE_INTEGRATION_ja.md` v1.1:
- 方法 A（推奨）: `python -m` 経由（PATH 非依存）
- 方法 B: `statable-cli.exe` 直接指定（%APPDATA% パス例示）

---

## v3.0 進捗サマリ（2026-09-29 時点）

| Phase | 状態 | commit | 成果 |
|-------|------|--------|------|
| S-1 パッケージング | 完了 | `c150be0` | pyproject.toml / `__version__` |
| S-2 公開 API | 完了 | `3897c6b` | `__all__` / validate lazy |
| S-3 CLI | 完了 | `aa2f55b` | `statable-cli` 3サブコマンド |
| S-4 ドキュメント | 完了 | `a7bbb29` | SPEC §2.6 / examples / README |
| S-5 Eclipse 連携 | 完了 | `f124ef0` | `ECLIPSE_INTEGRATION_ja.md` |
| S-6 SmartConfig | スキップ | `b4a288d` (fix) | ルネサス専用、対応不要 |
| G-1 GUI 分離 | 次 | — | — |
| G-2 libcntrl → shared | 待機 | — | — |

---

## 次フェーズ: G-1（GUI パッケージ分離）

### 現状把握（引継ぎ資料より）

- `code/statable_gui/` に GUI 一式（30+ ファイル）
- `code/statable_gui/libcntrl/` に共有ライブラリ
- `pyproject.toml` の `[project.optional-dependencies] gui = ["PySide6>=6.0"]`
- `packages.find` で `statable_gui*` を含めている

### G-1 の目的

`statable[gui]` extras 経由でのみ GUI を提供。
SDK 単体（`pip install statable`）では GUI 依存を入れない。

### 事前確認項目

- `statable_gui` の PySide6 依存箇所
- `statable_gui` が SDK コアから参照される箇所（逆依存）
- `pyproject.toml` の packages 指定
- CI（check.yml）での GUI テスト扱い

---

## 改訂履歴

| 日付 | 内容 |
|------|------|
| 2026-09-29 | 初版（S-6 スキップ + Eclipse 検証記録） |