# StaTable Handover — v3.5.0 Development Status

**Date:** 2026-10-11
**Target:** v3.4.3 released -> v3.5.0 in development (incremental)
**Repository:** https://github.com/akashi-hideki/StaTable

---

## 現状 (v3.5.0 開発中)

### リリース済みバージョン

| Version | PyPI | GitHub Release |
|---|:---:|:---:|
| v3.1.0 / v3.1.1 | OK | OK |
| v3.2.0 / v3.2.1 / v3.2.2 | OK | OK |
| v3.3.0 | OK | OK |
| v3.4.3 | OK | OK |

**v3.5.0 は未リリース** (段階的に開発中)

### 最新コミット (CI green 8 連続)

- `16237ff` refactor(v3.5.0): Phase 1b mypy cleanup (218 -> 58 errors)
- `29cf425` ci(v3.5.0): update GitHub Actions to Node.js 24 versions (S-5)
- `1825170` fix(ci): add tomli fallback for Python 3.10 (S-4)
- `6c39a34` ci(v3.5.0): add Python matrix (3.10-3.13) + coverage (S-4)
- `f11fea1` docs(v3.5.0): add HANDOVER_v3_5_0.md (development status)
- `76cd6c2` ci(v3.5.0): pin all jobs to ubuntu-24.04 (S-3 Step 1)
- `3cd1b45` feat(v3.5.0): add mypy foundation (Phase 1a, informational)
- `a203daa` feat(v3.5.0): expand frozen exe smoke tests to 4 levels

### 品質状態

- **CI: 完全 green (11 ジョブ全て成功)**
  - Unit tests は **Python 3.10 / 3.11 / 3.12 / 3.13** の 4 matrix
  - `mypy-check` (informational)
- **テスト: 46 suites / 1657 PASS / 0 FAIL (py3.10-3.13 全て)**
- **coverage: htmlcov を artifact 化 (matrix 毎に 4 種)**
- **mypy baseline: 58 errors / 16 files** (Phase 1b 後、218 から -73%)
- gcc + ARM 全ファイル構文検証: PASS
- ARM Cortex-M4 リンク検証: PASS
- MISRA C:2012: cppcheck 検出、10 hits 抑制

---
## v3.5.0 の主要変更 (これまで)

### S-1: frozen exe smoke test 拡充 (commit a203daa)

- `statable/smoke.py` 新規 (レベル 0-3)
  - L0: MainWindow + open_project regression (v3.2.2)
  - L1: widget presence (menuBar / centralWidget / QTabWidget)
  - L2: _ActionListWidget operation (v3.4.x combo/roundtrip)
  - L3: save/open roundtrip via tempdir
- `__main__.py`: `--smoke-level=N` パース (後方互換: L0)
- `tools/smoke_frozen.py`: `--smoke-level` passthrough
- `tests/test_v3_5_s1_smoke.py` 新規 (8 tests)
- `StaTable.spec`: `statable.smoke` を hiddenimports に追加
- CI: `Run smoke tests (levels 0-3)` ステップ追加
- README: 46 suites / 1657 PASS に更新

### S-2 Phase 1a: mypy 基盤 (commit 3cd1b45)

- `pyproject.toml`:
  - `dev` extras に `mypy>=1.10` 追加
  - `[tool.mypy]` セクション追加
  - `[[tool.mypy.overrides]]` で PySide6 / codegen のノイズ抑制
- CI: `mypy-check` ジョブ追加 (`continue-on-error: true`)
- `smoke.py` を mypy 準拠にリファクタ (`setattr` ベース monkeypatching)
- `.gitignore`: `code/mypy_report.txt` を除外
- **Baseline: 883 -> 218 errors (-75%)**

### S-3 Step 1: ubuntu-24.04 ピン留め (commit 76cd6c2)

- 全 8 ジョブの `runs-on: ubuntu-latest` -> `runs-on: ubuntu-24.04`
- 背景: ubuntu-latest が 2026-10-19〜2026-11-19 で Ubuntu 26.04 に移行
- 移行期間中の予期せぬ自動切替を防止

### S-4: Python matrix + coverage (commit 6c39a34, fix 1825170)

- `tests` ジョブを Python 3.10 / 3.11 / 3.12 / 3.13 の 4 matrix に
  - `fail-fast: false` で 1 つ落ちても他は継続
- 各テストスイートを `coverage run --parallel-mode` でラップ
  - `test_v3_5_s1_smoke.py` は `os._exit(0)` のため除外（coverage の atexit が走らない）
- `coverage combine` + `coverage report` + `coverage html` を実行
- `coverage-py3.1x` として HTML を artifact 化
- `code/.coveragerc` 追加、`pyproject.toml` に `coverage>=7.0`
- Python 3.10 の `tomllib` 不在対応:
  - 4 テストファイルに `try: import tomllib / except: import tomli`
  - `pyproject.toml` に `tomli>=2.0; python_version < '3.11'`
  - `check.yml` の install に `tomli` 追加

### S-5: GitHub Actions Node.js 24 対応 (commit 29cf425)

- `actions/checkout@v4` -> `v5`（8 箇所）
- `actions/setup-python@v5` -> `v6`（8 箇所）
- `actions/upload-artifact@v4` -> `v5`（5 箇所）
- 効果: Node.js 20 deprecation 警告が 21 件 -> 1 件に削減
  - 残る 1 件は `upload-artifact@v5` 側の問題（GitHub 側の対応待ち）

### Phase 1b: mypy 218 -> 58 errors (commit 16237ff)

- `CodeTemplates` の 15 dict に `dict[str, Any]` 注釈
- 各ジェネレータの `*_TEMPLATES` 26 dict に `dict[str, Any]` 注釈
- `xml_io.py` の truthy-function 6 件 (`X is not None`)
- 7 ファイルの var-annotated 12 件（dict/list 型注釈）
- `SubElement(..., **attrs)` 15 行に `# type: ignore[arg-type]`
  - mypy の dict invariance 由来、実行時は問題なし
- **結果: 218 -> 58 errors (-73%)**

### 配布パッケージ構造 (v3.4.3 以降、変更なし)

- サブフォルダレイアウト:
  - `StaTable-CookingHeater-Package-v3.4.3.zip` (174 MB)
  - 解凍後: `StaTable\StaTable.exe`
  - **`_internal\` と一緒に使う必要あり** (単独コピー不可)

---
## 次期開発の候補

### 優先度 S

1. **v3.5.0 続行**
   - Phase 1c: 残り 58 errors の削減（`statable/xml_io.py` 中心）
   - S-3 Step 2: ubuntu-26.04 preview ジョブ追加 (**10/19 以降**)
   - **GUI 生成時の output クリア問題**（下記「未解決の問題」参照）
   - 完了済み: S-4, S-5, Phase 1b

2. **ビジネス側から要望された機能**
   - ビジネススレッドからのフィードバック待ち

### 優先度 A

3. **型ヒント厳格化の継続** (Phase 1a 完了 -> 1b -> 1c)
4. **リリース補助 GUI Phase 3** (`tools/release_helper.py` 拡張)

### 優先度 B

5. **Gitee ミラー対応**
   - サポート返信待ち (日本から +86 認証不可)
   - 2026-10-10 に Gitee WiKi 機能の案内メールのみ受信 (サポート返信ではない)

---

## 開発スタイル (維持)

- **パッチスクリプト + git_runner + 対話的進行**
- **テスト必須** (新機能には対応テスト追加)
- **README 一貫性** (`test_readme_consistency.py` を通す)
- **CI 登録整合性** (`test_ci_registration.py` で自動検出)
- **コミットメッセージ**: Conventional Commits 準拠
- **CI green を維持**

### パッチスクリプト運用の注意

**Python コードを PowerShell に直接貼らない**こと。
here-string で一度ファイルに保存してから `python` で実行する。
(v3.5.0 開発中に 2 回この罠に陥った)

---

## 現状確認コマンド

PowerShell で以下を実行:

- cd C:\Users\user\OneDrive\ドキュメント\GitHub\StaTable
- git log --oneline -10
- git status --short
- git tag --list "v3.*"
- gh release list --limit 5
- gh run list --limit 3
- cd code
- python tests\test_readme_consistency.py
- python tests\test_ci_registration.py
- python -m statable --smoke-test --smoke-level=3
- mypy statable statable_gui codegen 2>&1 | Select-Object -Last 3

---
## 注意事項

### セキュリティ

- **API トークン・リカバリーコードは絶対にチャットに貼らない**
- 保管場所: `C:\secure_statable\`
- PyPI / GitHub / Microsoft の 3 サービス 2FA 有効

### リリース手順

- リリース時は `tools\release_helper.py` を使用
- タグ push 後は GitHub Release にアセット 3 ファイル添付:
  - Portable ZIP / wheel / sdist
  - `gh release upload <tag> <files> --clobber` で可能

### PowerShell 注意点

- `Set-Content -Encoding UTF8` は BOM 付き -> .NET API で BOM なし書き込み
- `2>nul` は使えない -> `2>$null` または `Select-String`
- 長い `git diff` はページャーで止まる -> `q` で抜ける、または `--no-pager`

### 配布パッケージ構造 (v3.4.3 以降)

- サブフォルダ構造に注意:
  - ZIP 解凍 -> `StaTable\StaTable.exe` + `StaTable\_internal\`
  - **`_internal\` を一緒に配布する必要あり**
  - ビジネススレッドの WeChat 投稿文にも注記済み

### CI 登録漏れ防止

- `test_ci_registration.py` が `check.yml` の登録漏れを自動検出
- 新テストファイル追加時は必ず `check.yml` に登録

### Ubuntu 26.04 移行 (2026-10-19 開始)

- **Step 1 完了**: 全ジョブを `ubuntu-24.04` にピン留め
- **Step 2 予定**: `ubuntu-26.04` preview ジョブ追加 (10/19 以降、ラベル提供確認後)
- 移行リスク: Qt 依存パッケージは 26.04 でも提供予定、arm-none-eabi-gcc は 15.x 系

---

## ビジネススレッドとの連携

### 現在のビジネス側タスク

- **v3.4.3 の WeChat 投稿準備中**
  - 投稿文 3 パターン (A: 推奨 / B: 短文 / C: 詳細) 作成済み
  - 画像生成ツール作成済み (`tools/make_wechat_images.py`、未コミット)
  - `wechat_images/` 出力ディレクトリあり (未コミット)

### 連携ポイント

- 新機能完成 -> ビジネススレッドへ報告 (デモ素材提供)
- 顧客要望 -> ビジネススレッドから開発スレッドへ
- リリースタイミングは両スレッドで調整

### ビジネス側の未完了事項

- WeChat 投稿実行
- 知財弁護士候補リスト
- 元同僚 (ハード設計者) へ打診
- 技術白書の骨子

### 未コミットのビジネス関連ファイル

- `code/tools/make_wechat_images.py`
- `wechat_images/`

これらは**ビジネススレッドでコミット**する予定。開発スレッドでは追跡しない。

---

## 未解決の問題: GUI コード生成時の output クリア漏れ

### 症状
- GUI でプロジェクトを生成時、`output/` をクリアしないため、
  古いアーキテクチャ（例: v3.3.x の `Driver/` 層）のファイルが残存
- 新プロジェクトで未定義の変数（`retry_count` 等）を参照 → コンパイル失敗

### 再現手順（2026-10-11 確認済み）
1. v3.3.x の XML を GUI で読み込み、`output/` に生成
2. v3.4.3 以降の XML（7 層調理器サンプル）を読み込み、同じ `output/` に生成
   （クリアせず）
3. `output/Driver/` の古いファイルが残り、`arm-none-eabi-gcc` で失敗

### 確認済みの事実
- `output/` 完全削除 → 再生成で **LINK PASS**（firmware.bin 28540 bytes）
- `statable_types_common.h` の `SystemData_t` に `retry_count` なし
- しかし `Driver/statable_role_functions_Driver.c` が参照（古いファイル）
- **codegen 側のバグではなく、GUI 側の運用問題**

### 対処案（未決定）
- A. 生成前に自動クリア（オプション or 常時）
- B. 生成後に古いファイルを警告
- C. 「クリーン生成」ボタン追加
- D. output/ を一時ディレクトリに生成してから同期

---

## 新スレッド開始時の推奨アクション

1. **現状確認** (上記コマンド実行)
2. **Phase 1b 着手** (`CodeTemplates` の型問題解消)
3. **ビジネススレッドからの要望確認**
4. **10/19 以降**: S-3 Step 2 実施 (ubuntu-26.04 preview)

---

## v3.5.0 コミット履歴

- `16237ff` refactor(v3.5.0): Phase 1b mypy cleanup (218 -> 58 errors)
- `29cf425` ci(v3.5.0): update GitHub Actions to Node.js 24 versions (S-5)
- `1825170` fix(ci): add tomli fallback for Python 3.10 (S-4)
- `6c39a34` ci(v3.5.0): add Python matrix (3.10-3.13) + coverage (S-4)
- `f11fea1` docs(v3.5.0): add HANDOVER_v3_5_0.md (development status)
- `76cd6c2` ci(v3.5.0): pin all jobs to ubuntu-24.04 (S-3 Step 1)
- `3cd1b45` feat(v3.5.0): add mypy foundation (Phase 1a, informational)
- `a203daa` feat(v3.5.0): expand frozen exe smoke tests to 4 levels

---

## mypy Baseline (Phase 1b 完了時点)

| File | errors |
|---|---:|
| `statable/xml_io.py` | ~30 |
| `codegen/validate/validation_dialog.py` | ~9 |
| PySide6 `type[Qt]` 系 | ~7 |
| others | ~12 |
| **Total** | **58** |

**Phase 1c の主眼**:
- `statable/xml_io.py` の残り（型注釈・`# type: ignore`）
- `statable_gui.*` の PySide6 stub 問題（overrides で抑制可）
- `Optional[X]` -> `X | None` 統一 (88 箇所)

---

End of handover.

---

## v3.5.0 リリース確定 (2026-10-11)

### 追加コミット (v3.5.0 リリース分)

- `27e2fbf` docs(v3.5.0): update README test counts (47 suites / 1682 PASS)
- `9e6e38a` test(v3.5.0): add test_v3_5_gui_output_clean.py (25 tests)
- `7044d2c` feat(v3.5.0): add stale-file warning + Clean & Regenerate UI
- `d58a6d9` feat(v3.5.0): record last_orphans in save_generated_code
- `7d9cd02` feat(v3.5.0): add find_orphan_files public API

### S-GUI 完了: GUI output クリア問題 (優先度 S)

**症状**: GUI コード生成時、output/ をクリアせず生成するため、
旧アーキテクチャの残骸 (Driver/ 層等) が残存し、リンク失敗。

**解決策 (B + C 併用)**:

1. **公開 API** `statable/output_utils.find_orphan_files()`
   - `output_dir` を再帰走査、`saved_files` に無いファイルを返す
   - codegen / GUI / CLI から再利用可能

2. **codegen 側記録** `CCodeGenerator.last_orphans`
   - `save_generated_code` 直後に orphan 一覧を保持
   - API 互換 (戻り値は `saved_files` のまま)

3. **GUI 警告** `statable_gui/output_warning.show_orphan_warning()`
   - 警告ダイアログに [Clean && Regenerate] [Ignore]
   - main_window / code_generation_dialog の両経路から呼ぶ

4. **堅牢削除** `statable_gui/fs_cleanup.robust_rmtree()`
   - `os.chmod(path, stat.S_IWRITE)` + 3 回リトライ
   - Windows + OneDrive (PINNED / REPARSE_POINT) の
     WinError 5 を解消

5. **UI 追加** main_window に `clean_generate_code()`
   - toolbar / menu に「Clean generate」アクション
   - `skip_confirm=True` で警告ダイアログから直接呼び出し

### 検証結果

- **新テスト**: `test_v3_5_gui_output_clean.py` 25 PASS
- **CI 登録**: 47 test files / all registered
- **README**: 47 suites / 1682 PASS に更新
- **ビルド検証** (Clean & Regenerate 後):
  - gcc 構文: 27/27 PASS
  - ARM 構文: 27/27 PASS
  - ARM リンク: LINK PASS
  - firmware.bin: **28540 bytes** (v3.4.3 と同一)
- **GUI 実機**: WinError 5 解消、警告ダイアログに
  Clean && Regenerate ボタン表示確認

### v3.5.0 の残課題 (v3.5.1 以降)

- Phase 1c: mypy 残 58 errors (statable/xml_io.py 中心)
- S-3 Step 2: ubuntu-26.04 preview (2026-10-19 以降)
- ビジネススレッド: WeChat 投稿、知財弁護士候補

---

End of v3.5.0 release section.
