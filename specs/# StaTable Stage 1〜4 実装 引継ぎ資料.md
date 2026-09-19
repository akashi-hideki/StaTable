# StaTable Stage 1〜4 実装 引継ぎ資料

以下をそのまま `.md` ファイルとして保存してください。次スレッドの冒頭に貼り付ければ、前提を共有できます。

---

```markdown
# StaTable Stage 1〜4 実装 完了報告書

版: 1.0（2026-09-13 完了）
前スレッド: Stage 1〜4 実装 + GUI 実機確認

---

## 1. 完了した作業

| Stage | 内容 | 状態 |
|-------|------|------|
| Stage 1 | namespace データモデル（model / libcntrl / xml_io） | ✅ 完了 |
| Stage 2 | NULL transition ガード + ISR マーカー対応 | ✅ 完了 |
| Stage 3 | ISR コンテキスト対応（ctx 自動挿入 + RoleFunc 変換） | ✅ 完了 |
| Stage 4 | 遷移側 Namespace.Name 対応 | ✅ 完了 |
| GUI 検証 | ロール関数・遷移条件パレット表示 | ✅ 完了 |
| コード生成 | ISR 生成 + マージ保持 | ✅ 完了 |

テスト合計: **480+ 件全合格**（個別実行で確認済み）

---

## 2. 変更ファイル一覧

### データモデル層（Stage 1）

| ファイル | 主要変更 |
|---------|---------|
| `statable/model.py` | `RoleFunction.namespace` / `qualified_name` / `from_legacy_name` |
| `statable/xml_io.py` | namespace 保存/復元、`used_role_functions` / `used_variables`、レガシー移行 |
| `statable/global_defs.py` | `InterruptHandlerDef.used_role_functions` / `used_variables` |
| `statable_gui/libcntrl/role_function_library.py` | `namespace` フィールド、`to_dict` / `from_dict` |

### 生成器層（Stage 2, 4）

| ファイル | 主要変更 |
|---------|---------|
| `codegen/role_function_generator.py` | NULL ガード、`_normalize_func_ref`（qualified 保持）、`_extract_func_names_from_condition`（dot 対応）、`_get_call_sites_for_func` |
| `codegen/code_merger.py` | `FUNC_NAME_PATTERNS` で `RoleFunc_` / `ISR_` 両対応 |

### ISR 生成（Stage 3）

| ファイル | 主要変更 |
|---------|---------|
| `codegen/interrupt_generator.py` | **完全版**: ctx 自動挿入、アクション パース、used_* 抽出、マーカー出力 |
| `codegen/code_templates.py` | `ISR_TEMPLATES` 追加 |
| `codegen/c_code_generator.py` | `interrupt_c` に `statable_all.h` 追加、`_step_interrupts` で used_* 再計算 |
| `statable_gui/action_edit_dialog.py` | `insert_role_function` で `qualified_name` 挿入 |
| `statable_gui/interrupt_handler_edit_dialog.py` | `get_interrupt` で used_* 自動抽出 |

### GUI 連携（パレット修正）

| ファイル | 主要変更 |
|---------|---------|
| `statable_gui/matrix_table.py` | `open_transition_dialog` で共有ライブラリ + SM のロール関数をマージ |
| `statable_gui/main_window.py` | `open_project` でロール関数・遷移条件の自動補完 |

### テスト

| ファイル | 内容 |
|---------|------|
| `tests/test_role_function_namespace.py` | Stage 1（20 件） |
| `tests/test_xml_namespace.py` | Stage 1（9 件） |
| `tests/test_role_null_guard.py` | Stage 2（16 件） |
| `tests/test_code_merger_isr.py` | Stage 2（8 件） |
| `tests/test_isr_context.py` | Stage 3（43 件） |
| `tests/test_transition_namespace.py` | Stage 4（33 件） |
| `tests/test_stage12_integration.py` | Stage 1+2 統合（62 件） |

---

## 3. 重要な設計判断

### 3.1 namespace の表記

| 項目 | 決定 |
|------|------|
| 表記形式 | `Driver.Init`（ドット区切り） |
| XML 属性 | `name="Init"` + `namespace="Driver"`（分離） |
| 生成 C 名 | `RoleFunc_Driver_Init` |
| マーカー名 | `Driver_Init` |

### 3.2 旧形式からの移行

| 旧形式 | 新形式 |
|--------|--------|
| `name="Driver_Init"`（namespace 未設定、layer_name=Driver） | `name="Init"` + `namespace="Driver"` |
| 移行トリガ | `xml_io.state_machine_from_element` で自動判定 |

### 3.3 ISR アクションのパース規則

| 入力 | 出力 |
|------|------|
| `Driver.Init` | `RoleFunc_Driver_Init(NULL, ctx)` |
| `Driver.Init(arg1, arg2)` | `RoleFunc_Driver_Init(NULL, ctx)`（引数破棄） |
| `Sensor_Init(arg1, arg2)` + layer=Driver | `RoleFunc_Driver_SensorInit(NULL, ctx)` |
| `ctx->data.counter++` | そのまま |
| `RoleFunc_Xxx` | そのまま |

### 3.4 マーカー命名規則

| 種別 | 例 |
|------|-----|
| RoleFunc | `[[STABLE_USER_CODE_START:Driver_Init]]` |
| ISR | `[[STABLE_USER_CODE_START:TIMER0]]`（ISR_ なし） |
| ファイル末尾 | `[[STABLE_USER_CODE_TAIL_START]]` |

### 3.5 命名規約（運用ルール）

**ロール関数名・ISR 名は英数字のみ使用**（C コンパイラ制約）。
日本語は `title` / `description` に記述する。

---

## 4. 実装の核心部分（触るときの注意）

### 4.1 `role_function_generator._normalize_func_ref`

```python
'Driver.Init'              → 'Driver.Init'  # そのまま
'Driver.Init(arg1, arg2)'  → 'Driver.Init'  # 引数除去
'RoleFunc_Driver_Init'     → 'Driver.Init'  # layer_name 一致時
'Init'                     → 'Init'
```

### 4.2 `role_function_generator._extract_func_names_from_condition`

検出パターン 5 種:
1. `RoleFunc_XXX`
2. `Namespace.Name`
3. `func_name(...)`
4. 全体が bare identifier
5. 式中の PascalCase bare identifier

### 4.3 `interrupt_generator._parse_action`

```python
# 判定順序
1. Namespace.Name [args] 形式
2. identifier(args) 形式
3. それ以外は verbatim
```

### 4.4 `main_window.open_project` の自動補完

XML の `<SharedLibraries>` が空でも動作するよう:
- 各タブの SM の `role_functions` を共有ライブラリに登録
- 各遷移の非空 `condition` を `ConditionLibrary` に登録

---

## 5. 既知の制約

| # | 制約 | 影響 |
|---|------|------|
| 1 | 日本語の関数名は使用不可 | 運用ルールで対応（C 言語制約） |
| 2 | `switch_case` / `dictionary` 未実装 | warning + array フォールバック |
| 3 | `external_includes*` 未実装 | タスク C として保留 |
| 4 | FreeRTOS / ThreadX OSAL 未実装 | テンプレート定義のみ |
| 5 | `role_function_edit_dialog` で namespace 編集不可 | 将来課題 |

---

## 6. 未着手タスク（ロードマップ）

| # | タスク | 優先度 |
|---|--------|--------|
| C | 外部インクルード各ファイル展開 | 🟡 中 |
| F | `switch_case` 実装 | 🟢 低 |
| G | `dictionary` 実装 | 🟢 低 |
| H+ | `role_function_edit_dialog` の namespace 編集 | 🟢 低 |
| I | 識別子バリデーション（英数字チェック） | 🟡 中 |

---

## 7. 検証済みテストプロジェクト

### `specs/isr_namespace_test.xml`

- 3 層（Driver / Middleware / Application）
- ロール関数 14 件（namespace 付き）
- ISR 5 種（TIMER0, TIMER1, UART_RX, GPIO_INT, DRIVER_INT）
- 条件付き遷移 7 件

### 生成結果（by_layer 構成）

```
<output>/
├── Driver/         (5 ファイル)
├── Middleware/     (5 ファイル)
├── Application/    (5 ファイル)
├── statable_init.c / event_queue / interrupt / timer
├── osal.h / osal.c
├── statable_all.h
└── IsrNamespaceTest_run.c
合計 23 ファイル
```

---

## 8. テスト実行方法（推奨）

`run_all_tests.py` は未登録テストの扱いが不完全なため、**個別実行**を推奨:

```powershell
cd C:\Users\user\OneDrive\ドキュメント\GitHub\StaTable\code

# Stage 1
python -m tests.test_role_function_namespace
python -m tests.test_xml_namespace

# Stage 2
python -m tests.test_role_function_generator
python -m tests.test_code_merger_isr
python -m tests.test_role_null_guard

# Stage 3
python -m tests.test_isr_context

# Stage 4
python -m tests.test_transition_namespace

# 統合
python -m tests.test_stage12_integration

# 既存回帰
python -m tests.test_c_code_generator
python -m tests.test_folder_structure
python -m tests.test_super_include
python -m tests.test_super_loop
python -m tests.test_layer_name
python -m tests.test_multi_layer
python -m tests.test_by_layer
python -m tests.test_warning_collector
python -m tests.test_transition_config
```

---

## 9. 診断ツール

### `tests/diagnose_isr_project.py`

XML 単体の読込状態を確認:

```powershell
python tests\diagnose_isr_project.py "path\to\project.xml"
```

出力内容:
- 各タブの状態 / イベント / ロール関数 / 遷移数
- グローバル定義の変数 / フラグ / 割り込み
- 共有ライブラリの内容
- 各遷移の `condition`

### `tools/write_isr_test_xml.py`

`isr_namespace_test.xml` (v2) を自動書き出し:

```powershell
python tools\write_isr_test_xml.py
```

---

## 10. 次スレッドでの作業開始手順

1. **この資料をスレッド冒頭に貼り付ける**
2. 対象タスクを明示（例: 「タスク C 外部インクルードを実装したい」）
3. 変更対象ファイルを共有（該当ファイルの現行版を貼り付け）
4. 関連する既存テストの合否状況を共有

### 確認しておくと良いこと

- [ ] Python / PySide6 のバージョン
- [ ] 変更対象ファイルの現行ソース
- [ ] 直近のテスト結果（どのテストが通っているか）
- [ ] 実運用で発見した問題（あれば）

---

## 11. 運用で問題が起きたときの初動

| 症状 | 確認箇所 |
|------|---------|
| ISR に `ctx` が出ない | `codegen/interrupt_generator.py` の `_execute_context_step` |
| `RoleFunc_*` 未変換 | `_parse_action` の判定順序 |
| パレットが空 | `matrix_table.open_transition_dialog` の `role_func_names` |
| マージで追加コードが消える | `code_merger.py` の `FUNC_NAME_PATTERNS` |
| XML が読み込めない | `tests/diagnose_isr_project.py` で診断 |

---

## 12. おわりに

Stage 1〜4 は完了し、GUI 実機確認まで通っています。
今後は**運用しながらの追加要望・不具合発見**を別スレッドで対応するフェーズです。

この資料を出発点として、新しいスレッドで作業を進めてください。

以上。
```

---

## 📌 保存方法

1. 上記コードブロック内をコピー
2. テキストエディタで **`StaTable Stage1-4 引継ぎ資料.md`** として保存（UTF-8）
3. 保存先は任意（例: `docs/` フォルダ、またはプロジェクトルート）

---

## 💡 次スレッドでの使い方

次スレッドの **最初のメッセージ** に以下を含めると、前提がスムーズに共有されます：

```
【引継ぎ資料】
（上記 .md の内容を貼り付け）

【今回の作業】
タスク C（外部インクルード）を実装したい。
対象ファイル: codegen/c_code_generator.py, codegen/code_templates.py

【現状】
- Stage 1〜4 完了、GUI 実機確認まで通っている
- 対象ファイルの現行版を以下に添付
（ファイル内容を貼り付け）
```

これで、次スレッドの担当者が **ゼロから状況を再構築する手間なく** 作業を開始できます。

---

長いセッション、本当にお疲れさまでした。運用フェーズでのご健闘をお祈りします。