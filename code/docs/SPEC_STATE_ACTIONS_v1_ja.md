# StaTable 状態アクション仕様書 v1.1

Version: 1.1
Date: 2026-09-26
Status: Design finalized (実装準備完了)
Target: StaTable v2.7.0 以降
Related: C-57, TUTORIAL_ja §7, SPEC_OVERVIEW_ja §3.2.2

---

## 目次

1. 背景と目的
2. 用語定義
3. UML との対応
4. データモデル
5. XML I/O
6. コード生成
7. GUI
8. ユーザー編集領域
9. 既存実装との互換性
10. 実装フェーズ
11. テスト計画
12. 設計決定事項
13. 未解決事項
14. 改訂履歴

---

## 1. 背景と目的

### 1.1 背景

StaTable は純イベント駆動として設計されており、UML ステートマシンの
**do アクティビティ**（状態滞在中の継続処理）という概念を採用していない。
このため、以下の制約がある:

- 状態滞在中の定常処理を表現できない
- 周期監視は TIME イベント + 自己遷移で代用（TUTORIAL §7 参照）
- entry / exit は `List[str]`（RoleFunc 名のみ）で、条件付き実行が不可

### 1.2 目的

以下を実現する:

| # | 目的 | 効果 |
|---|------|------|
| 1 | 状態に紐づく処理（entry / exit / do）を統合 | 編集箇所の一元化 |
| 2 | do アクティビティを正式サポート | UML 意味論の充足 |
| 3 | ActionEditorDialog 風の GUI で編集 | 操作性向上 |
| 4 | ユーザー編集領域を各関数に付与 | 自由度確保 |
| 5 | GUI 編集とカスタムコードの共存 | 再生成時の保持 |

### 1.3 対象外

以下は本仕様の対象外:

- internal transition（自己遷移で代用）
- completion transition（既存実装のまま）
- 並行状態（CONCURRENT 型）の特殊処理

---

## 2. 用語定義

| 用語 | 定義 |
|------|------|
| **状態アクション** | 状態に紐づく処理。entry / exit / do の総称 |
| **Entry アクション** | 状態に入った瞬間に1回実行 |
| **Exit アクション** | 状態から出る瞬間に1回実行 |
| **Do アクティビティ** | 状態滞在中に毎ループ実行 |
| **ActionStep** | 1つのアクション単位。RoleFunc 呼び出し or イベント発火 + 条件 |
| **GUI 編集領域** | GUI で編集するアクションリスト（再生成で上書き） |
| **カスタムコード領域** | ユーザーが自由に書く C コード（`[[STABLE_USER_CODE]]` で保持） |
| **StateActionsDialog** | 状態アクション編集用の新規ダイアログ |
| **`STATE_<Layer>_MAX`** | 既存 enum の番兵。テーブルサイズに使用 |

---

## 3. UML との対応

| UML 概念 | StaTable での実装 | 実行タイミング |
|---------|-----------------|--------------|
| entry action | `State.entry`（`List[ActionStep]`） | 状態遷移時、新状態に入った瞬間 |
| exit action | `State.exit`（`List[ActionStep]`） | 状態遷移時、旧状態から出る瞬間 |
| do activity | `State.do_actions`（`List[ActionStep]`） | 毎ループ（イベント処理の前） |
| internal transition | （自己遷移で代用） | — |
| completion transition | 空イベント名 | — |

### 3.1 実行順序（状態遷移時）

```
[イベント到着]
  ↓
[旧状態の Exit アクション実行]
  ↓
[遷移の pre_actions 実行]
  ↓
[遷移の条件評価 → target 決定]
  ↓
[新状態の Entry アクション実行]
  ↓
[毎ループの Do アクティビティ実行]（次ループから）
```

---

## 4. データモデル

### 4.1 `ActionStep` の拡張

```python
@dataclass(kw_only=True)
class ActionStep:
    """状態アクション（v2.7.0 拡張）"""
    role_function: str = ""      # RoleFunc の qualified_name
    trigger: str = "before_transitions"  # 既存フィールド（セルアクション用）
    title: str = ""
    # ---- v2.7.0 追加 ----
    condition: str = ""          # 実行条件（C 式、空なら無条件）
    action_type: str = "role"    # "role" | "fire_event" | "custom"
    event_name: str = ""         # action_type="fire_event" 時のイベント名
```

### 4.2 `State` の拡張

```python
@dataclass
class State:
    name: str
    type: StateType = StateType.NORMAL
    parent: Optional[str] = None
    # ---- 拡張: List[str] → List[ActionStep] ----
    entry: List[ActionStep] = field(default_factory=list)
    exit: List[ActionStep] = field(default_factory=list)
    # ---- 新規 ----
    do_actions: List[ActionStep] = field(default_factory=list)
    do: str = ""  # [Reserved] 後方互換用（v2.7.0 以降は未使用）
    description: str = ""

    def __post_init__(self):
        # 後方互換: List[str] → List[ActionStep] 自動変換
        self.entry = _normalize_action_list(self.entry)
        self.exit = _normalize_action_list(self.exit)
        self.do_actions = _normalize_action_list(self.do_actions)
```

### 4.3 後方互換ヘルパー

```python
def _normalize_action_list(value) -> List[ActionStep]:
    """旧形式（str / List[str]）を List[ActionStep] に正規化。"""
    if value is None:
        return []
    if isinstance(value, str):
        return [ActionStep(role_function=value)] if value.strip() else []
    if isinstance(value, list):
        result = []
        for item in value:
            if isinstance(item, str):
                if item.strip():
                    result.append(ActionStep(role_function=item))
            elif isinstance(item, ActionStep):
                result.append(item)
            elif isinstance(item, dict):
                result.append(ActionStep.from_dict(item))
        return result
    return []
```

---

## 5. XML I/O

### 5.1 新 XML 構造

```xml
<State name="Idle" type="initial" ...>
  <Entry>
    <Action role_function="Driver.IdleEntry"
            condition="" action_type="role" />
    <Action role_function="Driver.ResetCounter"
            condition="ctx->reset_needed" action_type="role" />
  </Entry>
  <Exit>
    <Action role_function="Driver.IdleExit"
            condition="" action_type="role" />
  </Exit>
  <Do>
    <Action role_function="Driver.PollSensor"
            condition="" action_type="role" />
    <Action role_function="Driver.UpdateLed"
            condition="ctx->led_dirty" action_type="role" />
    <Action event_name="Driver.TICK_10MS"
            condition="" action_type="fire_event" />
  </Do>
</State>
```

### 5.2 後方互換

旧形式:
```xml
<Entry>
  <Action name="Driver.IdleEntry"/>
</Entry>
```

`from_dict` で以下に正規化:
```python
ActionStep(role_function="Driver.IdleEntry", action_type="role")
```

### 5.3 属性一覧

| 属性 | 必須 | 型 | 説明 |
|------|:---:|-----|------|
| `role_function` | △ | str | `action_type="role"` 時に必須 |
| `event_name` | △ | str | `action_type="fire_event"` 時に必須 |
| `condition` | – | str | 実行条件（C 式） |
| `action_type` | – | str | `"role"` / `"fire_event"` / `"custom"`（省略時 `"role"`） |
| `title` | – | str | 表示名（未設定時は自動生成） |

### 5.4 空属性の抑制

`condition` / `action_type` が空 or デフォルト値の場合は**属性を出力しない**
（既存 v3.8.1 の方針を踏襲）。

---

## 6. コード生成

### 6.1 生成ファイル構成

```
output_vending/
├── Driver/
│   ├── statable_state_actions_Driver.h    ← 新規
│   ├── statable_state_actions_Driver.c    ← 新規
│   ├── ...
├── Middleware/
│   ├── statable_state_actions_Middleware.h ← 新規
│   ├── statable_state_actions_Middleware.c ← 新規
│   ├── ...
└── Vending/
    ├── statable_state_actions_Vending.h    ← 新規
    ├── statable_state_actions_Vending.c    ← 新規
    ├── ...
```

### 6.2 ヘッダ（`statable_state_actions_<Layer>.h`）

```c
#ifndef STATABLE_STATE_ACTIONS_DRIVER_H
#define STATABLE_STATE_ACTIONS_DRIVER_H

#include "statable_types_common.h"
#include "statable_types_Driver.h"

/* Entry / Exit / Do ディスパッチ */
void Driver_Entry(STATE_Driver_t state, SystemContext_t *ctx);
void Driver_Exit(STATE_Driver_t state, SystemContext_t *ctx);
void Driver_Do(STATE_Driver_t state, SystemContext_t *ctx);

#endif /* STATABLE_STATE_ACTIONS_DRIVER_H */
```

### 6.3 実装（`statable_state_actions_<Layer>.c`）

```c
/**
 * @file    statable_state_actions_Driver.c
 * @brief   Driver layer state actions (entry / exit / do)
 * @note    C89-compatible: ordered initializer only.
 *          Table order MUST match STATE_Driver_t enum order.
 */
#include "statable_state_actions_Driver.h"

/* ---- forward declarations ---- */
static void Driver_Entry_Waiting(SystemContext_t *ctx);
static void Driver_Exit_Waiting(SystemContext_t *ctx);
static void Driver_Do_Waiting(SystemContext_t *ctx);
/* ... 各状態分 ... */

/* ---- dispatch tables ---- */
typedef void (*Driver_StateFunc_t)(SystemContext_t *ctx);

static const Driver_StateFunc_t g_Driver_EntryTable[STATE_Driver_MAX] = {
    Driver_Entry_Waiting,        /* [0] STATE_Driver_Waiting */
    Driver_Entry_CoinPulse,      /* [1] STATE_Driver_CoinPulse */
    /* ... */
};

static const Driver_StateFunc_t g_Driver_ExitTable[STATE_Driver_MAX] = {
    Driver_Exit_Waiting,         /* [0] */
    Driver_Exit_CoinPulse,       /* [1] */
    /* ... */
};

static const Driver_StateFunc_t g_Driver_DoTable[STATE_Driver_MAX] = {
    Driver_Do_Waiting,           /* [0] */
    Driver_Do_CoinPulse,         /* [1] */
    /* ... */
};

/* ---- dispatchers ---- */
void Driver_Entry(STATE_Driver_t state, SystemContext_t *ctx)
{
    if ((unsigned)state < (unsigned)STATE_Driver_MAX) {
        Driver_StateFunc_t fn = g_Driver_EntryTable[state];
        if (fn != NULL) { fn(ctx); }
    }
}

void Driver_Exit(STATE_Driver_t state, SystemContext_t *ctx)
{
    if ((unsigned)state < (unsigned)STATE_Driver_MAX) {
        Driver_StateFunc_t fn = g_Driver_ExitTable[state];
        if (fn != NULL) { fn(ctx); }
    }
}

void Driver_Do(STATE_Driver_t state, SystemContext_t *ctx)
{
    if ((unsigned)state < (unsigned)STATE_Driver_MAX) {
        Driver_StateFunc_t fn = g_Driver_DoTable[state];
        if (fn != NULL) { fn(ctx); }
    }
}

/* ---- Entry functions (user-editable) ---- */
static void Driver_Entry_Waiting(SystemContext_t *ctx)
{
    /* --- GUI-edited actions (regenerated) --- */
    (void)RoleFunc_Driver_InitLed(NULL, ctx);
    (void)RoleFunc_Driver_ResetCounter(NULL, ctx);
    /* --- end GUI-edited actions --- */

    /* --- user custom code (preserved) --- */
    /* [[STABLE_USER_CODE_START:Driver_Entry_Waiting_custom]] */
    (void)ctx;
    /* [[STABLE_USER_CODE_END:Driver_Entry_Waiting_custom]] */
}

/* ---- Do functions (user-editable) ---- */
static void Driver_Do_Waiting(SystemContext_t *ctx)
{
    /* --- GUI-edited actions (regenerated) --- */
    (void)RoleFunc_Driver_PollSensor(NULL, ctx);
    if (ctx->led_dirty) {
        (void)RoleFunc_Driver_UpdateLed(NULL, ctx);
    }
    /* --- end GUI-edited actions --- */

    /* --- user custom code (preserved) --- */
    /* [[STABLE_USER_CODE_START:Driver_Do_Waiting_custom]] */
    (void)ctx;
    /* [[STABLE_USER_CODE_END:Driver_Do_Waiting_custom]] */
}

/* ---- Exit functions (user-editable) ---- */
static void Driver_Exit_Waiting(SystemContext_t *ctx)
{
    /* --- GUI-edited actions (regenerated) --- */
    (void)RoleFunc_Driver_SaveState(NULL, ctx);
    /* --- end GUI-edited actions --- */

    /* --- user custom code (preserved) --- */
    /* [[STABLE_USER_CODE_START:Driver_Exit_Waiting_custom]] */
    (void)ctx;
    /* [[STABLE_USER_CODE_END:Driver_Exit_Waiting_custom]] */
}
```

### 6.4 アクションの生成パターン

| `action_type` | 条件 | 生成コード |
|--------------|:---:|-----------|
| `role` | なし | `(void)RoleFunc_<NS>_<Name>(NULL, ctx);` |
| `role` | あり | `if (<condition>) { (void)RoleFunc_<NS>_<Name>(NULL, ctx); }` |
| `fire_event` | なし | `FIRE_EVENT_<Layer>(<EVENT>);` |
| `fire_event` | あり | `if (<condition>) { FIRE_EVENT_<Layer>(<EVENT>); }` |
| `custom` | — | GUI では生成せず、Custom Code タブで編集 |

**RoleFunc 呼び出しの第1引数は `NULL`**（設計決定 #1 / 案 A）。
既存 RoleFunc のシグネチャをそのまま使用する。

### 6.5 `{project}_run.c` の変更

```c
void VendingMachineTutorial_Run(void)
{
    while (1) {
        /* Per-layer state-do dispatch (v2.7.0) */
        Driver_Do(g_Driver_state, &g_ctx);
        Middleware_Do(g_Middleware_state, &g_ctx);
        Application_Do(g_Application_state, &g_ctx);

        /* Existing event processing */
        {
            EVENT_Driver_t evt = StateMachine_GetNextEvent_Driver(&g_ctx);
            if (evt != EVENT_Driver_NONE) {
                g_Driver_state = StateMachine_Process_Driver(
                    g_Driver_state, evt, &g_ctx);
            }
        }
        /* ... 他層 ... */
    }
}
```

### 6.6 Entry / Exit の呼び出し

既存の `StateMachine_Process_<Layer>` 内で、遷移の前後に呼び出す:

```c
/* statable_transitions_Driver.c（生成コードに組込） */
STATE_Driver_t StateMachine_Process_Driver(
    STATE_Driver_t from_state, EVENT_Driver_t event, SystemContext_t *ctx)
{
    STATE_Driver_t next_state = from_state;

    /* ... セル関数呼び出しで next_state 決定 ... */

    if (next_state != from_state) {
        Driver_Exit(from_state, ctx);       /* Exit アクション */
        Driver_Entry(next_state, ctx);      /* Entry アクション */
    }
    return next_state;
}
```

---

## 7. GUI

### 7.1 起動導線

| 案 | 操作 | 採用 |
|:---:|------|:---:|
| **A** | SettingsPanel の状態行を**ダブルクリック** | ✅ |
| **B** | 右クリック → コンテキストメニュー `Edit Actions...` | 補助 |
| **C** | 専用ボタン列 | 将来検討 |

**競合回避**: 状態行の **Name 列以外**をダブルクリックで起動。
Name 列はインライン編集（既存動作を維持）。

### 7.2 StateActionsDialog の構成

```
┌──────────────────────────────────────────────────────────┐
│ State Actions — Driver.Waiting                           │
├──────────────────────────────────────────────────────────┤
│ [Entry] [Exit] [Do] [Preview]                            │
├──────────────────────────────────────────────────────────┤
│ Actions (executed every loop while in Waiting)           │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ 1. [RoleFunc ▼] Driver.PollSensor                    │ │
│ │    Condition: (none)                                 │ │
│ │ 2. [RoleFunc ▼] Driver.UpdateLed                     │ │
│ │    Condition: ctx->led_dirty                         │ │
│ │ 3. [FIRE_EVENT ▼] Driver.TICK_10MS                   │ │
│ │    Condition: (none)                                 │ │
│ │ [+] [−] [↑] [↓]                                      │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                          │
│ Custom Code (user-editable, preserved)                   │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ /* [[STABLE_USER_CODE_START:..._custom]] */          │ │
│ │ /* Your code here */                                 │ │
│ │ /* [[STABLE_USER_CODE_END:..._custom]] */            │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                          │
│                              [OK] [Cancel]               │
└──────────────────────────────────────────────────────────┘
```

### 7.3 タブ構成

| # | タブ | 内容 |
|---|------|------|
| 1 | **Entry** | 状態に入った瞬間のアクション |
| 2 | **Exit** | 状態から出る瞬間のアクション |
| 3 | **Do** | 状態滞在中の周期アクション |
| 4 | **Preview** | 生成コードをリアルタイム表示 |

### 7.4 アクション編集ウィジェット

| # | 要素 | 内容 |
|---|------|------|
| 1 | アクション種別 | `RoleFunc` / `FIRE_EVENT` |
| 2 | 対象選択 | RoleFunc ドロップダウン or イベントドロップダウン |
| 3 | Condition | 条件式入力欄（空なら無条件） |
| 4 | 順序変更 | ↑↓ ボタン |
| 5 | 追加 / 削除 | `[+]` / `[−]` ボタン |

### 7.5 Custom Code タブ

各アクションタブの下部に**折りたたみ可能な Custom Code エリア**を配置。

| 項目 | 内容 |
|------|------|
| 編集対象 | `[[STABLE_USER_CODE_START:<state>_<kind>_custom]]` 内 |
| 保存先 | XML の `<Entry>` / `<Exit>` / `<Do>` の `custom_code` 属性 |
| 再生成時 | `code_merger` が保持 |

### 7.6 生成コードプレビュー

Preview タブで、現在の設定から生成される C コードを表示:

```c
static void Driver_Do_Waiting(SystemContext_t *ctx)
{
    /* --- GUI-edited actions --- */
    (void)RoleFunc_Driver_PollSensor(NULL, ctx);
    if (ctx->led_dirty) {
        (void)RoleFunc_Driver_UpdateLed(NULL, ctx);
    }
    /* --- end GUI-edited actions --- */

    /* [[STABLE_USER_CODE_START:Driver_Do_Waiting_custom]] */
    /* ... */
    /* [[STABLE_USER_CODE_END:Driver_Do_Waiting_custom]] */
}
```

### 7.7 既存 ActionEditorDialog との共通化

| # | 共通化対象 | 抽出先 |
|---|-----------|-------|
| 1 | アクション編集行ウィジェット | `ActionStepWidget` |
| 2 | RoleFunc 選択ドロップダウン | 既存を流用 |
| 3 | イベント選択ドロップダウン | 新規（`FIRE_EVENT` 用） |
| 4 | Preview 機能 | `CodeWidget` を流用 |
| 5 | Custom Code エディタ | 新規 |

**共通ウィジェット抽出は Phase 5 で判断**（設計決定 #6）。

---

## 8. ユーザー編集領域

### 8.1 2層構造

各状態アクション関数は**2層の編集領域**を持つ:

| 層 | マーカー | 編集元 | 再生成時 |
|:---:|---------|--------|:---:|
| 1 | （なし、関数本体） | GUI | 上書き |
| 2 | `<State>_<Kind>_custom` | 手書き | **保持** |

### 8.2 生成コードの構造

```c
static void Driver_Do_Waiting(SystemContext_t *ctx)
{
    /* --- GUI-edited actions (regenerated) --- */
    (void)RoleFunc_Driver_PollSensor(NULL, ctx);
    if (ctx->led_dirty) {
        (void)RoleFunc_Driver_UpdateLed(NULL, ctx);
    }
    /* --- end GUI-edited actions --- */

    /* --- user custom code (preserved) --- */
    /* [[STABLE_USER_CODE_START:Driver_Do_Waiting_custom]] */
    (void)ctx;
    /* [[STABLE_USER_CODE_END:Driver_Do_Waiting_custom]] */
}
```

### 8.3 マーカー命名規則

```
[[STABLE_USER_CODE_START:<Layer>_<Kind>_<State>_custom]]
[[STABLE_USER_CODE_END:<Layer>_<Kind>_<State>_custom]]
```

| 要素 | 値 |
|------|-----|
| `<Layer>` | 層名（Driver / Middleware / Vending 等） |
| `<Kind>` | `Entry` / `Exit` / `Do` |
| `<State>` | 状態名（英数字のみ、空白は `_`） |

### 8.4 既存マーカーとの衝突回避

既存の `[[STABLE_USER_CODE_START:<func_name>]]` と**衝突しない**よう、
`_custom` サフィックスを付与。

---

## 9. 既存実装との互換性

### 9.1 データモデル

| 項目 | 旧 | 新 | 互換性 |
|------|:---:|:---:|:---:|
| `State.entry` | `List[str]` | `List[ActionStep]` | 後方互換（`__post_init__` で自動変換） |
| `State.exit` | `List[str]` | `List[ActionStep]` | 同上 |
| `State.do_actions` | なし | `List[ActionStep]` | 新規 |
| `State.do` | `str`（予約） | `str`（予約のまま） | 維持 |

### 9.2 XML

旧形式の `<Entry><Action name="..."/></Entry>` は
`from_dict` で `ActionStep(role_function="...")` に正規化。

### 9.3 コード生成

既存の entry / exit 生成コードは、**新しい関数ベースに完全移行**（設計決定 #3）。
ただし、旧 XML の読込は後方互換で対応。

### 9.4 GUI

既存の SettingsPanel の entry / exit 列は、**読み取り専用表示**に変更
（編集は StateActionsDialog に集約）。

---

## 10. 実装フェーズ

| Phase | 内容 | 依存 | 工数 |
|:---:|------|:---:|:---:|
| **1** | データモデル拡張（`ActionStep` / `State`） | — | 小 |
| **2** | XML I/O 拡張（`<Entry>` / `<Exit>` / `<Do>`） | Phase 1 | 小 |
| **3** | codegen: StateActions 生成（Entry / Exit / Do + テーブル） | Phase 1 | 中 |
| **4** | codegen: `{project}_run.c` 更新 | Phase 3 | 小 |
| **5** | GUI: StateActionsDialog 骨子（4タブ） | Phase 2 | 大 |
| **6** | GUI: アクション編集（順序・条件） | Phase 5 | 中 |
| **7** | GUI: Preview / Custom Code | Phase 5 | 中 |
| **8** | テスト / TUTORIAL / SPEC | 全 Phase | 中 |

### 10.1 各 Phase の完了条件

| Phase | 完了条件 |
|:---:|---------|
| 1 | `test_v2_7_p1.py` PASS（データモデル） |
| 2 | `test_v2_7_p2.py` PASS（XML round-trip） |
| 3 | `test_v2_7_p3.py` PASS（codegen） + gcc / arm 構文検証 |
| 4 | 生成 `_run.c` の構文検証 PASS |
| 5 | `test_v2_7_p5.py` PASS（GUI 起動・タブ表示） |
| 6 | `test_v2_7_p6.py` PASS（編集操作） |
| 7 | `test_v2_7_p7.py` PASS（Preview / Custom） |
| 8 | 全テスト PASS + CI グリーン |

---

## 11. テスト計画

### 11.1 単体テスト

| # | テスト | 対象 |
|---|--------|------|
| 1 | `ActionStep` の `to_dict` / `from_dict` | データモデル |
| 2 | `State.entry` の後方互換変換 | データモデル |
| 3 | `<Do>` XML round-trip | XML I/O |
| 4 | 空 `condition` の属性抑制 | XML I/O |
| 5 | StateActions コード生成（条件なし） | codegen |
| 6 | StateActions コード生成（条件あり） | codegen |
| 7 | `FIRE_EVENT` 生成 | codegen |
| 8 | テーブルの順序一致検証 | codegen |
| 9 | `{project}_run.c` の Do 呼び出し | codegen |
| 10 | StateActionsDialog の起動 | GUI |

### 11.2 統合テスト

| # | テスト | 内容 |
|---|--------|------|
| 1 | `vending_machine.xml` に Do アクション追加 → 生成 → 構文検証 | E2E |
| 2 | 再生成時に Custom Code が保持されるか | マージ |
| 3 | 既存 XML（entry / exit が `List[str]`）の読込 | 後方互換 |

### 11.3 構文検証

| # | ツールチェーン | 対象 |
|---|--------------|------|
| 1 | gcc | 全生成ファイル |
| 2 | arm-none-eabi-gcc | 全生成ファイル |

---

## 12. 設計決定事項

| # | 項目 | 決定 | 理由 |
|---|------|------|------|
| 1 | RoleFunc シグネチャ | **`transition=NULL` を渡す（既存シグネチャ維持）** | 生成コード変更最小。RoleFunc 実装側で `transition` を使わなければ問題なし |
| 2 | `custom` アクション種別 | **GUI では扱わない、Custom Code タブで編集** | GUI の複雑化回避 |
| 3 | Entry / Exit の互換モード | **完全移行**（旧 XML のみ後方互換） | v2.7.0 の破壊的変更として文書化 |
| 4 | GUI 起動導線 | **SettingsPanel の状態行ダブルクリック（Name 列以外）** | ActionEditorDialog との統一感 |
| 5 | 状態名 C 識別子化 | **ASCII 以外は生成時エラー** | 日本語状態名は非推奨 |
| 6 | 共通ウィジェット抽出 | **Phase 5 で判断** | まず独立実装 → 後で抽出 |
| 7 | MISRA 対応 | **Phase 3 完了時に測定** | 既存水準（10 hits）以内を目標 |
| 8 | テーブルサイズ | **`STATE_<Layer>_MAX` を使用** | 既存 enum の番兵。`#define` 追加不要 |

---

## 13. 未解決事項

| # | 項目 | 内容 | 検討時期 |
|---|------|------|:---:|
| 1 | 状態名の C 識別子化詳細 | ASCII 以外を含む場合の**具体的なエラーメッセージと検出タイミング** | Phase 1 |
| 2 | `_MAX` の C89 互換性 | `[STATE_Driver_MAX]` を配列サイズに使う際の厳密な C89 適合性 | Phase 1（検証） |
| 3 | Custom Code の XML 保存 | `custom_code` 属性を XML に保存するか、マーカーのみで管理するか | Phase 2 |
| 4 | Preview タブの編集連動 | 編集内容がリアルタイムで Preview に反映されるか | Phase 7 |

---

## 14. 改訂履歴

| バージョン | 日付 | 内容 |
|-----------|------|------|
| 1.0 | 2026-09-26 | 初版（設計段階） |
| 1.1 | 2026-09-26 | 設計決定事項 8項目を確定。`STATE_<Layer>_MAX` の使用を追記。§12 を新設、旧 §12 を §13 に繰下 |
```

---

## 配置手順

### 1. GitHub Web UI で既存ファイルを編集

1. ブラウザで以下を開く:
   ```
   https://github.com/akashi-hideki/StaTable/edit/main/code/docs/SPEC_STATE_ACTIONS_v1.md
   ```

2. **Ctrl+A → Delete で全消去**

3. 上記 Markdown を**一括貼り付け**（` ```markdown ` の外側の説明文は含めず、` # StaTable 状態アクション仕様書 v1.1 ` から末尾まで）

4. **Commit changes**（コミットメッセージ例: `docs(spec): SPEC_STATE_ACTIONS v1.1 - design decisions finalized`）

### 2. ローカル確認

```powershell
cd C:\Users\user\OneDrive\ドキュメント\GitHub\StaTable
git pull
cd code
python -c "from pathlib import Path; t = Path('docs/SPEC_STATE_ACTIONS_v1.md').read_text(encoding='utf-8'); lines = t.splitlines(); print(f'lines: {len(lines)}'); print(f'L1: {lines[0]}'); import re; [print(f'{i+1:4d}: {l}') for i, l in enumerate(lines) if re.match(r'^## \d+\.', l)]"
```

**期待**:
```
lines: 約 800
L1: # StaTable 状態アクション仕様書 v1.1
    1: ## 1. 背景と目的
    2: ## 2. 用語定義
    3: ## 3. UML との対応
    4: ## 4. データモデル
    5: ## 5. XML I/O
    6: ## 6. コード生成
    7: ## 7. GUI
    8: ## 8. ユーザー編集領域
    9: ## 9. 既存実装との互換性
   10: ## 10. 実装フェーズ
   11: ## 11. テスト計画
   12: ## 12. 設計決定事項
   13: ## 13. 未解決事項
   14: ## 14. 改訂履歴
```

---

## 主な変更点（v1.0 → v1.1）

| # | 変更 |
|---|------|
| 1 | §4.2 `State.do` の記述を「後方互換用」に明記 |
| 2 | §6.3 テーブルサイズを `STATE_<Layer>_MAX` に変更（`#define` 不使用） |
| 3 | §6.4 RoleFunc 呼び出しを `RoleFunc_...(NULL, ctx)` に変更（設計決定 #1） |
| 4 | §6.4 `fire_event` の生成コードを明記 |
| 5 | §6.6 Entry / Exit の呼び出しを `StateMachine_Process_<Layer>` 内に組込む形に修正 |
| 6 | §7.7 共通化を「Phase 5 で判断」と明記 |
| 7 | §9.3 を「完全移行」と明記（設計決定 #3） |
| 8 | **§12 設計決定事項（新設）** — 8項目を表形式で明文化 |
| 9 | §13 未解決事項（旧 §12） — 4項目に整理 |
| 10 | §14 改訂履歴（旧 §13） |

---
