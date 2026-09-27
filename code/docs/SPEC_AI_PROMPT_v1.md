# StaTable AI Prompt 仕様書 v1.1

Version: 1.1
Date: 2026-09-27
Status: Design finalized
Target: StaTable v2.8.0 以降
Related: `codegen/validate/` subsystem

---

## 1. 背景と目的

### 1.1 背景

`codegen/validate/` の AI 診断機能は、内部 Validation の結果を
LLM に投げて改善提案（Change リスト）を得る仕組みである。
現状のプロンプトは `[Task]` / `[Output format]` 形式で、以下の
7 つの構造的弱点を持つ:

| # | 弱点 | 影響 |
|---|------|------|
| P1 | コンテキスト不足 | `role_functions` / `cells` / `global_defs` が送信されない |
| P2 | `gd` 引数が無視 | GlobalDefinitions が AI に届かない |
| P3 | パーサの 7 アクション未対応 | cell-level 提案が破棄される |
| P4 | 出力スキーマ未定義 | パース失敗が頻発 |
| P5 | `<response>` マーカーなし | 抽出が脆弱 |
| P6 | `evidence` / `confidence` なし | 提案の根拠が不明 |
| P7 | Validation 詳細が severity のみ | suggestion 等が失われる |

### 1.2 目的

**確実な成果を生む AI 診断**を実現する。具体的には:

1. AI に**完全なコンテキスト**を渡す
2. AI 応答を**構造化スキーマ**で受ける
3. パース後、**適用前に検証**する
4. **全 17 アクション**に対応
5. 提案の**根拠・信頼度**を可視化

---

## 2. 設計方針

| 項目 | 決定 |
|------|------|
| タグ形式 | XML 風 `<tag>...</tag>` |
| プロンプト言語 | 英語（応答の JSON も英語キー） |
| 必須フィールド | `version` / `action` / `params` / `reason` |
| アクション | 全 17 種（legacy 10 + cell-level 7） |
| 検証レイヤー | スキーマ検証 + 参照整合性 |
| バージョン | プロンプト・応答の両方で `"1.0"` |
| few-shot | 2 件 |
| confidence の自動除外 | しない（情報提供のみ） |
| 多言語化 | 不要（英語のみ） |

---

## 3. プロンプト構造

### 3.1 全体構造

```
<system>          役割定義
<workflow>        AI 改訂ワークフロー
<task>            タスク
<constraints>     禁止事項
<output_schema>   JSON スキーマ
<examples>        few-shot 例（2 件）
<context>         完全なプロジェクト状態
<validation>      内部検証の詳細
<actions>         利用可能アクション
<response_format> 応答形式の指示
```

### 3.2 `<system>`

```
You are an expert in embedded software state transition design.
Your task is to diagnose a state machine design and propose minimal,
correct, and safe changes.
```

### 3.3 `<workflow>`

This section describes how this prompt fits into the
semi-automatic design-improvement loop.

```
This prompt is part of a semi-automatic design-improvement loop:

  1. The user runs internal validation
     -> an issues list is produced (<validation>).

  2. This prompt is generated, including:
       - the full current state machine design (<context>)
       - the internal validation results (<validation>)
       - the available actions (<actions>)

  3. You (the AI) diagnose the issues and propose changes as JSON.

  4. The user reviews each change and selects which ones to apply.
     Your output is a *proposal*, NOT an automatic change.

  5. The selected changes are applied to the design.

  6. Internal validation runs again -> the loop may repeat.

Therefore:
  - Prefer minimal, evidence-based changes that a human can trust.
  - One change per logical fix.
  - Always provide reasoning so the user can judge each item.
  - If no change is needed, return an empty "changes" array.
```

### 3.4 `<constraints>`

```
- Output ONLY the JSON inside <response>...</response> tags.
- Do NOT invent new state names, event names, or role function names
  unless explicitly required by an error.
- For every change, provide evidence (validation code or state/event name).
- Prefer minimal changes: one logical fix per change item.
```

### 3.5 `<output_schema>`

```json
{
  "version": "1.0",
  "summary": "<one-line overview, optional>",
  "changes": [
    {
      "id": "C-001",
      "action": "<one of the allowed actions>",
      "params": { ... },
      "reason": "<why this change is needed>",
      "evidence": ["<validation code or identifier>"],
      "priority": "high|medium|low",
      "confidence": 0.0
    }
  ]
}
```

### 3.6 `<context>` のサブタグ

| タグ | 内容 | 備考 |
|------|------|------|
| `<layer>` | name / priority / initial | 属性 |
| `<states>` | `<state>` + `<entry>` / `<exit>` / `<do>` | 全 ActionStep 含む |
| `<events>` | `<event>` + `<trigger>` | trigger_detail 含む |
| `<transitions>` | `<transition>` + `<pre_action>` / `<else_action>` | 全属性 |
| `<role_functions>` | `<role_function>` | name / namespace / return_type |
| `<cells>` | `<cell>` + `<actions>` / `<relations>` | 全 cell metadata |
| `<global_definitions>` | variables / flags / interrupts / timers / queues | 完全送信 |

### 3.7 `<validation>`

各 issue を以下で送信:

```xml
<issue severity="ERROR" category="state" code="STATE_UNREACHABLE"
       target="MotorRunning" suggestion="...">
  State "MotorRunning" is unreachable
</issue>
```

### 3.8 `<actions>`

`ACTION_DEFINITIONS` から構造化:

```xml
<action name="add_transition" description="Add transition">
  <param name="source" type="str" required="true"/>
  <param name="event" type="str" required="true"/>
  ...
</action>
```

---

## 4. 応答スキーマ

### 4.1 トップレベル

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|:---:|------|
| `version` | str | ✅ | `"1.0"` 固定 |
| `summary` | str | – | 全体所見 |
| `changes` | list | ✅ | Change の配列 |
| `no_change_needed` | bool | – | 変更不要の明示 |

### 4.2 `changes[]` の各要素

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|:---:|------|
| `id` | str | – | 識別子（例: `C-001`） |
| `action` | str | ✅ | アクション名（17 種のいずれか） |
| `params` | dict | ✅ | パラメータ |
| `reason` | str | ✅ | 理由 |
| `evidence` | list[str] | – | 根拠（validation code 等） |
| `priority` | str | – | `high` / `medium` / `low` |
| `confidence` | float | – | 0.0〜1.0 |

### 4.3 応答全体の例

```xml
<response>
{
  "version": "1.0",
  "summary": "Add an error recovery transition and fix an unreachable state.",
  "changes": [
    {
      "id": "C-001",
      "action": "add_transition",
      "params": {
        "source": "Error",
        "event": "RESET",
        "target": "Idle",
        "action_name": "ClearError"
      },
      "reason": "The Error state has no outgoing transition.",
      "evidence": ["STATE_NO_TRANSITION:Error"],
      "priority": "high",
      "confidence": 0.95
    },
    {
      "id": "C-002",
      "action": "add_transition_relation",
      "params": {
        "source": "Accumulating",
        "event": "ITEM_SELECT",
        "kind": "exclusive",
        "members": ["T1", "T2"]
      },
      "reason": "Make the two transitions mutually exclusive.",
      "evidence": ["CELL_EXCLUSIVE_NO_RETURN:Accumulating"],
      "priority": "medium",
      "confidence": 0.85
    }
  ]
}
</response>
```

---

## 5. パーサ仕様（`AIResponseParser`）

### 5.1 抽出優先順位

1. `<response>...</response>` マーカー
2. `<json>...</json>` マーカー（旧互換）
3. `{` ～ `}` の brace matching（最終フォールバック）

### 5.2 アクションマッピング（17 種）

`ChangeActionType` の `.value` から自動生成:

| カテゴリ | アクション |
|---------|-----------|
| Legacy (10) | `set_initial` / `add_transition` / `add_state` / `add_event` / `remove_transition` / `update_transition` / `add_role_function` / `remove_role_function` / `add_variable` / `add_flag` |
| Cell-level (7) | `add_cell` / `remove_cell` / `add_action_step` / `remove_action_step` / `add_transition_relation` / `remove_transition_relation` / `set_early_return` |

### 5.3 拡張フィールド

`ChangeRequest` に以下を追加:

| フィールド | 型 | デフォルト |
|-----------|-----|-----------|
| `id` | str | `""` |
| `evidence` | List[str] | `[]` |
| `priority` | str | `"medium"` |
| `confidence` | float | `1.0` |

`to_dict` / `from_dict` で往復可能。

---

## 6. 検証レイヤー仕様（`ResponseValidator`）

**新規モジュール**: `codegen/validate/response_validator.py`

### 6.1 検証段階

| 段階 | 内容 |
|------|------|
| 1. スキーマ検証 | `version` / `action` / `params` / `reason` の存在・型 |
| 2. アクション検証 | `action` が 17 種に含まれるか |
| 3. パラメータ検証 | `ACTION_DEFINITIONS` の required 充足 |
| 4. 参照整合性 | `source` / `target` / `event` / `role_function` の存在 |

### 6.2 検証結果

```python
@dataclass
class ResponseValidationResult:
    valid_requests: List[ChangeRequest]
    invalid_requests: List[Tuple[ChangeRequest, str]]  # (req, reason)
    warnings: List[str]
```

### 6.3 参照整合性ルール

| アクション | 検証対象 |
|-----------|---------|
| `add_transition` | `source` が states に存在 / `event` が events に存在 |
| `remove_transition` | 同一 (source, event, target) が transitions に存在 |
| `set_initial` | `state` が states に存在 |
| `add_action_step` | `role_function` が role_functions に存在 |
| `add_transition_relation` | `members` が cell 内の labels に存在 |
| （他） | `ACTION_DEFINITIONS` の required のみ |

### 6.4 エラー時の動作

- **検証失敗の request は適用対象から除外**
- ユーザーに **warning** として通知（GUI の change list タブに表示）
- 除外理由を message で表示

---

## 7. 実装 Phase 分割

| Phase | 内容 | ファイル |
|:---:|------|---------|
| **A** | プロンプトテンプレート刷新 + `_format_data` 拡張 | `prompt_templates.py` / `prompt_generator.py` |
| **B** | 応答スキーマ + `ChangeRequest` 拡張 + パーサ 17 アクション対応 | `change_actions.py` / `response_parser.py` |
| **C** | `ResponseValidator` 新規 + `validation_dialog` 統合 | `response_validator.py` / `validation_dialog.py` |
| **D** | 回帰テスト | `tests/test_v2_8_p1_ai_prompt.py` |

### 7.1 Phase A 完了条件

- `<context>` / `<validation>` / `<actions>` が完全送信される
- 生成プロンプトに `role_functions` / `cells` / `global_defs` が含まれる
- 手動確認: TUTORIAL XML で全情報が出力される

### 7.2 Phase B 完了条件

- 全 17 アクションが `ACTION_MAPPING` に存在
- `<response>` マーカーで抽出可能
- `ChangeRequest` の往復テスト PASS

### 7.3 Phase C 完了条件

- 不正な `action` / 存在しない `state` が除外される
- GUI で warning 表示される

### 7.4 Phase D 完了条件

- `test_v2_8_p1_ai_prompt.py` 全 PASS
- 既存 `test_v2_2_p12_6.py`（AI アクション）の回帰 PASS

---

## 8. テスト計画

### 8.1 単体テスト

| # | テスト | 対象 |
|---|--------|------|
| 1 | `_format_data` に role_functions 含まれる | prompt_generator |
| 2 | `_format_data` に cells / global_defs 含まれる | prompt_generator |
| 3 | `<response>` マーカー抽出 | response_parser |
| 4 | 全 17 アクションのパース | response_parser |
| 5 | `ChangeRequest.to_dict` / `from_dict` | change_actions |
| 6 | スキーマ検証（必須フィールド） | response_validator |
| 7 | 参照整合性（存在しない state） | response_validator |
| 8 | 17 アクションの `ACTION_MAPPING` 網羅 | response_parser |

### 8.2 統合テスト

| # | テスト | 内容 |
|---|--------|------|
| 1 | TUTORIAL XML → プロンプト生成 → 全情報含む | E2E |
| 2 | 定型応答 → パース → 検証 → 適用 | E2E |
| 3 | 不正応答 → 検証で除外 → warning | 異常系 |

### 8.3 回帰テスト

- `test_v2_2_p12_6.py`（既存 AI アクション）
- `test_v2_2_p12_2.py`（CellValidator）

---

## 9. 後方互換性

| 項目 | 対応 |
|------|------|
| 旧プロンプト | 使用しない（全面刷新） |
| 旧応答（10 アクションのみ） | パーサで受理継続 |
| 旧 `<json>` マーカー | フォールバックで受理 |
| `ChangeRequest` 旧フィールド | デフォルト値で補完 |

---

## 10. 未解決事項

| # | 項目 | 検討時期 |
|---|------|:---:|
| 1 | confidence の GUI 表示方法（ソート / フィルタ） | Phase C |
| 2 | priority の自動ソート | Phase C |
| 3 | few-shot 2 件目の内容 | Phase A |
| 4 | 検証失敗時のログ出力先 | Phase C |

---

## 11. 改訂履歴

| バージョン | 日付 | 内容 |
|-----------|------|------|
| 1.0 | 2026-09-27 | 初版（設計確定） |
| 1.1 | 2026-09-27 | `<workflow>` セクション追加（AI 改訂フローの明示） |
```

---

## 検証コマンド

```powershell
cd C:\Users\user\OneDrive\ドキュメント\GitHub\StaTable\code
python -c "from pathlib import Path; t = Path('docs/SPEC_AI_PROMPT_v1.md').read_text(encoding='utf-8'); lines = t.splitlines(); print(f'lines: {len(lines)}'); print(f'L1: {lines[0]}'); print(f'L3: {lines[2]}'); import re; [print(f'{i+1:4d}: {l}') for i, l in enumerate(lines) if re.match(r'^## \d+\.', l) or re.match(r'^### 3\.', l)]"
```

**期待**:
```
lines: 約 470
L1: # StaTable AI Prompt 仕様書 v1.1
L3: Version: 1.1
   ## 1. 背景と目的
   ## 2. 設計方針
   ## 3. プロンプト構造
   ### 3.1 全体構造
   ### 3.2 `<system>`
   ### 3.3 `<workflow>`
   ### 3.4 `<constraints>`
   ### 3.5 `<output_schema>`
   ### 3.6 `<context>` のサブタグ
   ### 3.7 `<validation>`
   ### 3.8 `<actions>`
   ## 4. 応答スキーマ
   ...
   ## 11. 改訂履歴


