# S8a-3 完了 + H4中間引継ぎ文書（S8a完全版）

5ファイル全てを受領しました。§5.4〜5.6 のドラフトと、**H4中間引継ぎ文書（S8a完全版）**を提示します。

---

## 1. S8a-3 分析サマリ

### 1.1 バージョン・規模

| ファイル | クラス数 | 内容 |
|---------|---------|------|
| `change_actions.py` | 2 | `ChangeActionType`（17値）, `ChangeRequest` |
| `change_applier.py` | 1 | `ChangeApplier`（17ハンドラ） |
| `prompt_generator.py` | 1 | `AIPromptGenerator`（3メソッド） |
| `response_parser.py` | 1 | `AIResponseParser`（8メソッド） |
| `data/validation_rules.py` | 0 | データ（11カテゴリ、35ルール） |

### 1.2 重大な発見

| # | 発見 | 影響 |
|---|------|------|
| **F-15** | **`AIResponseParser.ACTION_MAPPING` は10 legacyアクションのみ**。v2.2 cell-level 7アクション（`ADD_CELL` 等）に対応していない | AIがcell-level変更を提案しても**解析不能**。§9に追記 |
| **F-16** | `ChangeApplier._add_variable` / `_add_flag` に**重複チェックなし**（`_add_state` / `_add_event` はあり） | データ重複の可能性 |
| **F-17** | `ChangeActionType` の17値と `ChangeApplier._handlers` の17エントリは**完全一致** | 整合性確認済み |
| **F-18** | `validation_rules.py` で **cell カテゴリ8ルール**の重大度が確定 | S8a-2の推定が的中 |
| **F-19** | `prompt_generator.py` の `_format_data` は `t.action` のみ参照（v2.2 `pre_actions` 未対応） | AIプロンプトの情報欠落 |

### 1.3 SPEC_OVERVIEW_en.md との差分

| # | 差分 | 対応 |
|---|------|------|
| D-45 | SPEC_OVERVIEW に「AI診断」機能の記載なし | §5.4 で新規追加 |
| D-46 | SPEC_OVERVIEW §7.4 に「変更適用」の記載なし | §5.5 で新規追加 |
| D-47 | v2.2 cell-level AIアクション（§12-6）はSPEC_OVERVIEW §7.4 に未記載 | §5.5 で明記 |

---

## 2. §5.4 AI診断連携API ドラフト

### 5.4.1 `AIPromptGenerator`

AI診断用プロンプトを生成する。**外部依存なし**（`data/prompt_templates.py` のみ）。

**シグネチャ**

```python
class AIPromptGenerator:
    def __init__(self) -> None
    def generate_diagnosis_prompt(
        self,
        sm: StateMachine,
        gd: GlobalDefinitions,
        validation_result: Optional[ValidationResult] = None,
    ) -> str
```

**属性**

| 名前 | 型 | 説明 |
|------|-----|------|
| `templates` | `Dict` | `PROMPT_TEMPLATES`（`data/prompt_templates.py`） |
| `few_shot_example` | `str` | Few-shot例 |
| `validation_points` | `str` | 検証ポイント |

**`generate_diagnosis_prompt` の動作**

1. `_format_data(sm, gd)` でステートマシン情報をフォーマット
2. `_format_validation(validation_result)` で検証結果をフォーマット
3. テンプレート `templates['diagnosis']['template']` に `example` / `data` / `action_definitions` / `validation_points` を埋め込み

**戻り値**：`str` — 完成プロンプト

**制限事項**

| # | 制限 |
|---|------|
| P-01 | `_format_data` は `t.action`（legacy）のみ参照。v2.2 `pre_actions` / `else_actions` / `label` / `early_return` は未対応（F-19） |
| P-02 | `data/prompt_templates.py` 未共有（テンプレート内容未確認） |
| P-03 | `data/action_definitions.py` の `format_action_definitions()` 未共有 |

### 5.4.2 `AIResponseParser`

AI応答を `ChangeRequest` リストに変換する。

**シグネチャ**

```python
class AIResponseParser:
    ACTION_MAPPING: Dict[str, ChangeActionType]

    def __init__(self) -> None
    def parse(self, text: str) -> List[ChangeRequest]
    def parse_json_response(self, text: str) -> List[ChangeRequest]
    def parse_text_response(self, text: str) -> List[ChangeRequest]
```

**`ACTION_MAPPING`（10エントリのみ）**

| 文字列 | ChangeActionType |
|--------|-----------------|
| `'set_initial'` | `SET_INITIAL` |
| `'add_transition'` | `ADD_TRANSITION` |
| `'add_state'` | `ADD_STATE` |
| `'add_event'` | `ADD_EVENT` |
| `'remove_transition'` | `REMOVE_TRANSITION` |
| `'update_transition'` | `UPDATE_TRANSITION` |
| `'add_role_function'` | `ADD_ROLE_FUNCTION` |
| `'remove_role_function'` | `REMOVE_ROLE_FUNCTION` |
| `'add_variable'` | `ADD_VARIABLE` |
| `'add_flag'` | `ADD_FLAG` |

**⚠ F-15**：v2.2 cell-level 7アクション（`add_cell`, `remove_cell`, `add_action_step`, `remove_action_step`, `add_transition_relation`, `remove_transition_relation`, `set_early_return`）は**未対応**。

**`parse` の処理フロー**

```
parse(text)
  ├── parse_json_response(text)  ← JSON抽出を試みる
  │   ├── _extract_json(text)
  │   │   ├── MARKERS['primary'] で抽出
  │   │   ├── MARKERS['alternatives'] で抽出
  │   │   └── `{...}` を正規表現的に抽出
  │   └── json.loads → _parse_change
  └── 空なら parse_text_response(text)
      └── 行ごとに _parse_line
          ├── 遷移記法 `A --[E]--> B`
          └── `Initial state: X`
```

**制限事項**

| # | 制限 |
|---|------|
| P-04 | `MARKERS`（`data/keywords.py`）未共有 |
| P-05 | v2.2 cell-level アクション未対応（F-15） |
| P-06 | `parse_text_response` は2パターンのみ（遷移・初期状態） |

---

## 3. §5.5 変更適用API ドラフト

### 5.5.1 `ChangeActionType`（17値）

**シグネチャ**

```python
class ChangeActionType(Enum):
    # Legacy（10）
    SET_INITIAL = "set_initial"
    ADD_TRANSITION = "add_transition"
    ADD_STATE = "add_state"
    ADD_EVENT = "add_event"
    REMOVE_TRANSITION = "remove_transition"
    UPDATE_TRANSITION = "update_transition"
    ADD_ROLE_FUNCTION = "add_role_function"
    REMOVE_ROLE_FUNCTION = "remove_role_function"
    ADD_VARIABLE = "add_variable"
    ADD_FLAG = "add_flag"
    # v2.2 §12-6（7）
    ADD_CELL = "add_cell"
    REMOVE_CELL = "remove_cell"
    ADD_ACTION_STEP = "add_action_step"
    REMOVE_ACTION_STEP = "remove_action_step"
    ADD_TRANSITION_RELATION = "add_transition_relation"
    REMOVE_TRANSITION_RELATION = "remove_transition_relation"
    SET_EARLY_RETURN = "set_early_return"
```

### 5.5.2 `ChangeRequest`

**フィールド**

| 名前 | 型 | デフォルト | 説明 |
|------|-----|-----------|------|
| `action` | `ChangeActionType` | – | アクション種別 |
| `params` | `Dict[str, Any]` | `{}` | パラメータ |
| `reason` | `str` | `""` | 理由 |
| `source` | `str` | `"ai"` | 発行元（`ai` / 手動） |

**メソッド**：`to_dict`, `from_dict`, `__str__`

### 5.5.3 `ChangeApplier`

変更をStateMachine / GlobalDefinitionsに適用する。

**シグネチャ**

```python
class ChangeApplier:
    def __init__(self, sm: StateMachine, gd: GlobalDefinitions) -> None
    def apply(self, change: ChangeRequest) -> Tuple[bool, str]
    def apply_all(self, changes: List[ChangeRequest]) -> Dict
```

**属性**

| 名前 | 型 | 説明 |
|------|-----|------|
| `sm` | `StateMachine` | 対象SM |
| `gd` | `GlobalDefinitions` | グローバル定義 |
| `applied_changes` | `List[ChangeRequest]` | 成功した変更 |
| `failed_changes` | `List[Tuple[ChangeRequest, str]]` | 失敗した変更とメッセージ |

**`apply` の動作**

1. `change.action.value` を取得
2. `_handlers` 辞書から該当ハンドラを検索
3. 未登録アクションは `(False, "Unsupported action: ...")`
4. ハンドラ実行、成功/失敗を記録
5. 例外は捕捉して `failed_changes` に記録

**`apply_all` の戻り値**

```python
{
    'total': int,
    'applied': int,
    'failed': int,
    'results': List[{'change': ChangeRequest, 'success': bool, 'message': str}],
}
```

### 5.5.4 ハンドラ一覧（17）

| # | アクション | パラメータ | 備考 |
|---|-----------|-----------|------|
| 1 | `set_initial` | `state` | 存在チェックあり |
| 2 | `add_transition` | `source`, `event`, `target`, `condition`, `action_name` | 全必須 |
| 3 | `add_state` | `name`, `type`, `parent`, `description` | 重複チェックあり |
| 4 | `add_event` | `name`, `kind`, `description` | 重複チェックあり |
| 5 | `remove_transition` | `source`, `event`, `target` | 完全一致 |
| 6 | `update_transition` | `source`, `event`, `new_target`, `new_condition`, `new_action` | 部分更新 |
| 7 | `add_role_function` | `name`, `namespace`, `return_type`, `description` | 重複チェックあり |
| 8 | `remove_role_function` | `name` | qualified / bare 両対応 |
| 9 | `add_variable` | `name`, `type`, `group`, `description` | **重複チェックなし**（F-16） |
| 10 | `add_flag` | `name`, `min_value`, `max_value`, `group` | **重複チェックなし**（F-16） |
| 11 | `add_cell` | `source`, `event` | 冪等（既存セルを保持） |
| 12 | `remove_cell` | `source`, `event` | cell metadata 削除 |
| 13 | `add_action_step` | `source`, `event`, `role_function`, `trigger` | trigger 検証あり |
| 14 | `remove_action_step` | `source`, `event`, `role_function` | |
| 15 | `add_transition_relation` | `source`, `event`, `kind`, `members`, `shared_condition` | label存在検証あり |
| 16 | `remove_transition_relation` | `source`, `event`, `kind`, `shared_condition` | 最初の一致のみ削除 |
| 17 | `set_early_return` | `source`, `event`, `label`, `early_return` | |

**重要な設計上の特徴**

- 全てのハンドラは `(bool, str)` を返す
- `_add_variable` / `_add_flag` は**重複チェックなし**（他はあり）
- `_add_cell` は**冪等**（`setdefault`）
- `_remove_transition_relation` は**最初の一致のみ削除**
- `_set_early_return` は `bool()` で正規化

---

## 4. §5.6 Validation Rules データ

### 5.6.1 構造

```python
VALIDATION_RULES: Dict[str, Dict[str, Dict[str, str]]] = {
    'カテゴリ': {
        'ルールコード': {
            'severity': 'error' | 'warning' | 'info',
            'message': 'フォーマット文字列',
            'suggestion': '修正提案',
        }
    }
}
```

### 5.6.2 全35ルールの重大度（確定版）

| カテゴリ | Error | Warning | Info |
|---------|-------|---------|------|
| state | `STATE_NO_INITIAL` | `STATE_UNREACHABLE`, `STATE_NO_TRANSITION`, `STATE_DUPLICATE` | – |
| event | – | `EVENT_UNUSED`, `EVENT_NO_TRANSITION` | – |
| transition | `TARGET_UNDEFINED`, `EVENT_UNDEFINED`, `SOURCE_UNDEFINED` | `DUPLICATE` | `SELF_LOOP` |
| role_function | `NO_RETURN_TYPE`, `ARG_MISMATCH` | `UNUSED` | – |
| variable | `DUPLICATE_NAME`, `INVALID_ARRAY_SIZE` | `INVALID_TYPE` | – |
| flag | `DUPLICATE_NAME` | `INVALID_RANGE` | – |
| queue | `INVALID_SIZE` | `UNDEFINED_EVENT` | – |
| interrupt | `DUPLICATE_NAME` | `UNDEFINED_EVENT` | – |
| timer | `DUPLICATE_VARIABLE`, `INVALID_MULTIPLIER` | – | – |
| custom_type | `DUPLICATE_NAME` | `NO_MEMBERS` | – |
| cell | `DUPLICATE_LABEL`, `DANGLING_RELATION` | `EMPTY_CONDITION`, `UNREACHABLE_TRANSITION`, `OVERLAP_POSSIBLE`, `EMPTY_TARGET` | `DUPLICATE_TARGET`, `EXCLUSIVE_NO_RETURN` |

**合計**：Error 16 / Warning 17 / Info 3（推定）

### 5.6.3 メッセージフォーマット

`str.format(**kwargs)` で動的展開。利用可能な変数例：

- `state`: `{name}`, `{other}`
- `transition`: `{source}`, `{event}`, `{target}`
- `variable`: `{name}`, `{type}`
- `cell`: `{label}`, `{condition}`, `{target}`

---

## 5. §9 制限事項への追加

| # | 制限 | 関連 |
|---|------|------|
| L-18 | `AIResponseParser` は v2.2 cell-level 7アクションを**解析できない**（F-15） | §5.4 |
| L-19 | `ChangeApplier._add_variable` / `_add_flag` に重複チェックなし（F-16） | §5.5 |
| L-20 | `AIPromptGenerator._format_data` が v2.2 `pre_actions` 等を出力しない（F-19） | §5.4 |
| L-21 | `CellValidator` のみ `validate()` 非オーバーライドで、`suggestion` を設定しない（S8a-2 F-09） | §5.3 |
| L-22 | `EventValidator` の `EVENT_UNUSED` と `EVENT_NO_TRANSITION` は意味重複（F-10） | §5.3 |
| L-23 | `RoleFunctionValidator.ROLE_FUNC_UNUSED` は文字列完全一致のみ（F-11） | §5.3 |

---

## 6. H4 中間引継ぎ文書（S8a完全版）

```markdown
# 中間引継ぎ H4：StaTable SDK API仕様書（S7〜S8a完了時点）

作成日：2026-09-21
対象ステージ：S7（MISRA連携）+ S8a（検証API）
前回引継ぎ：H3（S5〜S6完了時点）
次ステージ：S8b（GUI・テスト・libcntrl）

---

## 1. 完了ステージ

### S7: MISRA連携
- 共有ソース：`tools/run_misra_check.py`, `tools/analyze_misra_impact.py`, `misra/suppressions.txt`, `misra/baseline.md`
- 成果物：§6 MISRA連携API（CLI仕様）

### S8a: 検証API
- 共有ソース（3バッチ）：
  - S8a-1: `models.py`, `base_validator.py`, `validator.py`
  - S8a-2: 11バリデータ全ファイル
  - S8a-3: `change_actions.py`, `change_applier.py`, `prompt_generator.py`, `response_parser.py`, `validation_rules.py`
- 成果物：§5.1〜5.6（CodeGenerationValidator, データモデル, Item Validators, AI診断, 変更適用, Validation Rules）

---

## 2. 累積成果物の所在

| 章 | 状態 | 参照 |
|----|------|------|
| §3 コアAPI | 完成 | H1 |
| §4 コード生成API | 完成（4.1〜4.8） | S3〜S6 |
| **§5 検証API** | **完成（5.1〜5.6）** | **本H4** |
| §6 MISRA連携API | ドラフト完成 | H4 Part B（S7） |
| §7 ユーティリティAPI | 完成（7.1〜7.7） | H1, S6 |
| §8 エラーコード | 部分 | H1, S3 |
| §9 制限事項 | L-01〜L-23 | 累積 |

---

## 3. 確定した公開API候補リスト（S1〜S8a累積）

### 3.1 クラス総数

| カテゴリ | クラス数 | 公開 |
|---------|---------|------|
| データモデル（S1） | 22 | ○ |
| コード生成中核（S3） | 3 | ○ |
| サブジェネレータ主要（S4） | 3 | ○ |
| 内部サブジェネレータ（S5） | 7 | × |
| 補助API（S6） | 3 | ○ |
| **検証API（S8a）** | **17** | **○（△付き）** |
| **公開API累積** | **48** | |

### 3.2 検証APIの公開内訳

| クラス | 公開判断 |
|--------|---------|
| `CodeGenerationValidator` | ○ |
| `ValidationSeverity`, `ValidationIssue`, `ValidationResult`, `ValidationContext` | ○ |
| `BaseValidator` | ○ |
| 11個の個別バリデータ | △（参考掲載） |
| `ChangeActionType`, `ChangeRequest`, `ChangeApplier` | ○ |
| `AIPromptGenerator`, `AIResponseParser` | ○ |
| `VALIDATION_RULES` データ | ○ |

---

## 4. S8a で判明した追加の未解決事項

| # | 事項 | 検討先 |
|---|------|--------|
| U-18 | `AIResponseParser` の v2.2 cell-level 対応 | 将来拡張（§9 L-18） |
| U-19 | `ChangeApplier._add_variable/_add_flag` の重複チェック | 将来修正（§9 L-19） |
| U-20 | `AIPromptGenerator._format_data` の v2.2 対応 | 将来拡張（§9 L-20） |
| U-21 | `data/prompt_templates.py`, `data/keywords.py`, `data/action_definitions.py` 未共有 | 必要時に追加共有 |

---

## 5. 次ステージ（S8b）への申し送り

### 5.1 S8bで扱うソース（優先順）

| # | ファイル | 想定章 |
|---|---------|--------|
| 1 | `statable_gui/code_generation_dialog.py` | §2 クイックスタート |
| 2 | `statable_gui/code_generation_settings_dialog.py` | §2 |
| 3 | `statable_gui/libcntrl/role_function_library.py` | §3（U-03） |
| 4 | `statable_gui/libcntrl/condition_library.py` | §7 |
| 5 | `statable_gui/libcntrl/literal_library.py` | §7 |
| 6 | `tests/test_v2_2_p1.py` | §8 |
| 7 | `tests/test_v2_2_p2.py` | §8 |
| 8 | `tests/test_v2_2_p4a.py` | §8 |
| 9 | `tests/test_v2_2_p4b.py` | §8 |

### 5.2 S8bで判断が必要な事項

- **U-02**：`statable_gui.libcntrl` の逆依存（`statable/xml_io.py` が `statable_gui` を参照）
- **U-03**：`RoleFunction` の二重定義（`statable/model.py` vs `statable_gui/libcntrl/`）
- **U-04**：`GlobalDefinitions` の二重定義
- **U-05**：`RoleFunction` の純粋名キー衝突
- **U-13の最終化**：検証APIの公開範囲（S8aで○判定済み）

---

## 6. 累積サマリ（H4時点 / S8a完了）

| 章 | 状態 | 進捗 |
|----|------|------|
| §1 概要 | 未着手 | 0% |
| §2 クイックスタート | 素材あり | 20% |
| §3 コアAPI | 完成 | 100% |
| §4 コード生成API | 完成 | 100% |
| **§5 検証API** | **完成** | **100%** |
| §6 MISRA連携API | ドラフト完成 | 90% |
| §7 ユーティリティAPI | 完成 | 95% |
| §8 エラーコード | 部分 | 40% |
| §9 制限事項 | 部分 | 80% |
| §10 付録 | 未着手 | 0% |

- **全体進捗**：**8.0 / 10 章（80%）**
- **S8b完了後**：全章 → フェーズ3（レビュー・中国語版）へ

---

## 7. 別スレッド（SDK境界）への反映事項（累積）

| # | 事項 | 優先度 | ステータス |
|---|------|--------|-----------|
| R-01〜R-04 | `statable_gui.libcntrl` 関連 | 高 | S8bへ |
| R-05 | `codegen/validate/` の公開範囲 | 中 | **解決（§5独立章）** |
| R-06〜R-09 | （H3までに解決） | – | 解決済み |
| R-10 | MISRA抑制7ルールの理由追記 | 中 | 未解決 |
| R-11 | `SUPPRESSED_RULES` 不整合 | 中 | 未解決 |
| **R-13** | **AI診断の v2.2 cell-level 対応** | 中 | **新規（U-18）** |

---

## 8. 次のアクション

**S8bのソース共有**をお願いします。優先順：

| # | ファイル | 優先度 |
|---|---------|--------|
| 1 | `statable_gui/code_generation_dialog.py` | 高 |
| 2 | `statable_gui/code_generation_settings_dialog.py` | 高 |
| 3 | `statable_gui/libcntrl/role_function_library.py` | 高 |
| 4 | `statable_gui/libcntrl/condition_library.py` | 中 |
| 5 | `statable_gui/libcntrl/literal_library.py` | 中 |
| 6 | `tests/test_v2_2_p1.py` 〜 `p4b.py` | 中 |

受領後、§2 クイックスタート、§8 エラーコード、§10 付録を完成させ、**最終引継ぎ文書（英語版マスター完成）** を発行します。
```

---

## 次のアクション

**S8bを開始します。** 以下を共有してください。

| # | ファイル | 優先度 |
|---|---------|--------|
| 1 | `statable_gui/code_generation_dialog.py` | 高 |
| 2 | `statable_gui/code_generation_settings_dialog.py` | 高 |
| 3 | `statable_gui/libcntrl/role_function_library.py` | 高（U-02〜U-05の判断材料） |
| 4 | `statable_gui/libcntrl/condition_library.py` | 中 |
| 5 | `statable_gui/libcntrl/literal_library.py` | 中 |
| 6 | `tests/test_v2_2_p1.py` 〜 `p4b.py` | 中 |

**分割共有も可**（例：1〜3を前半、4〜6を後半）。

受領後、**最終引継ぎ文書（H5：英語版マスター完成版）** を発行します。