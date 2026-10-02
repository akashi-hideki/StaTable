# 開発スレッド引継ぎ資料

Version: v3.1 (2026-10-01 完了)
最終 commit: `ea73d13`

---

## 1. 現在の状態

| 項目 | 値 |
|------|-----|
| リポジトリ | https://github.com/akashi-hideki/StaTable |
| ブランチ | main |
| 最新 commit | ea73d13 |
| 作業ツリー | clean |
| テスト | 40 suites / 1479 PASS |
| CI | green |

### 完了済み

| Version | 内容 | commit |
|---------|------|--------|
| v2.8.0 | AI Diagnosis Refresh | aca01bd |
| v3.0 | SDK Foundation | 59c552a |
| v3.1 | 中国語対応 + Language menu | ea73d13 |

---

## 2. 開発スタイル

| # | 慣習 |
|---|------|
| 1 | パッチスクリプト tools/patches/patch_*.py |
| 2 | backup / literal anchor / idempotent |
| 3 | 対話的進行（1ステップずつ確認） |
| 4 | git_runner (tools/git_ops.txt) |
| 5 | テスト必須 |
| 6 | 回帰確認 |
| 7 | 引継ぎ markdown |
| 8 | README 一貫性 (test_readme_consistency.py) |
| 9 | .bak_* は .gitignore 対象 |
| 10 | PowerShell 形式 |

---

## 3. v3.2 候補

### 優先度 S

| # | 項目 |
|---|------|
| 1 | 日本語翻訳 (statable_ja.ts) |
| 2 | 中国語ドキュメント (SPEC_*_zh-CN.md) |
| 3 | PyPI 正式公開 |

### 優先度 A

| # | 項目 |
|---|------|
| 4 | RT-Thread 連携 |
| 5 | MISRA コンプライアンスレポート |
| 6 | statable-cli spec コマンド |
| 7 | examples/ にサンプル XML |

### 優先度 B

| # | 項目 |
|---|------|
| 8 | VS Code 拡張 |
| 9 | Web ベース版 |
| 10 | 商用ライセンス機構 |

---

## 4. 主要ファイル

| パス | 役割 |
|------|------|
| code/statable/ | SDK コア |
| code/statable/shared/ | 共有ライブラリ |
| code/codegen/ | C コード生成 |
| code/codegen/validate/ | 検証 + AI 診断 |
| code/statable_gui/ | PySide6 GUI |
| code/statable_gui/i18n/ | 翻訳リソース |
| code/tools/ | 開発ツール |
| code/tests/ | 40 テストスイート |

---

## 5. よく使うコマンド

```powershell
cd C:\Users\user\OneDrive\ドキュメント\GitHub\StaTable\code
git log --oneline -7
git status --short

python tests\test_v3_0_s1_packaging.py
python tests\test_v3_0_s2_public_api.py
python tests\test_v3_0_s3_cli.py
python tests\test_v3_0_s4_docs.py
python tests\test_v3_0_g1_shared.py
python tests\test_readme_consistency.py

python tools\i18n_status.py
python tools\i18n_extract.py
python tools\i18n_compile.py

notepad tools\git_ops.txt
python tools\git_runner.py --list
python tools\git_runner.py --dry-run
python tools\git_runner.py
```

---

## 6. 新スレッド開始チェック

- git log --oneline -7
- git status --short
- docs/HANDOVER_v3_0_PROGRESS.md 参照
- 開発スタイル（§2）厳守

---

## 7. 改訂履歴

| 日付 | 内容 |
|------|------|
| 2026-10-02 | 初版 |