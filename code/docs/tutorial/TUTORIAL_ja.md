# StaTable TUTORIAL — 自動販売機で学ぶ3層ステートマシン

Version: 1.0
Date: 2026-09-23
対象: StaTable v2.5.2 以降
---

## 1. はじめに

このチュートリアルでは、**StaTable** を使って自動販売機の制御ロジックを
設計し、C コードを生成し、コンパイル検証まで行う一連の流れを学びます。

### 1.1 完成するもの

| 項目 | 内容 |
|------|------|
| 題材 | 自動販売機の制御ロジック |
| 層構成 | Driver / Middleware / Application の3層 |
| 状態数 | 合計16（Driver 5 + Middleware 6 + Application 5） |
| イベント数 | 合計19 |
| 遷移数 | 合計40 |
| 生成コード | C99 準拠、`static` 関数多用、MISRA C:2012 対応 |
| 検証 | gcc + arm-none-eabi-gcc の両方で `-Wall -Wextra` パス |

### 1.2 前提

- StaTable がセットアップ済み（`python -m statable_gui.main` が起動）
- `docs/tutorial/vending_machine.xml` が存在
---

## 2. 題材: 自動販売機

### 2.1 3層アーキテクチャ

自動販売機の制御を、責務ごとに3層に分割します。

```

┌──────────────────────────────────────────────────┐
│  Application 層（優先度 5）                       │
│  - ユーザー向けフロー                            │
│  - 状態: Idle / HasCredit / Dispensing /         │
│         ReturningChange / Error                  │
│  - 名前空間: Vending.*                           │
├──────────────────────────────────────────────────┤
│  Middleware 層（優先度 3）                        │
│  - 決済・在庫管理                                │
│  - 状態: Waiting / Accumulating / Ready /        │
│         CheckingStock / Releasing / MwError      │
│  - 名前空間: Middleware.*                        │
├──────────────────────────────────────────────────┤
│  Driver 層（優先度 1）                            │
│  - ハードウェア抽象化                            │
│  - 状態: Waiting / CoinPulse / ButtonPressed /   │
│         MotorRunning / HardwareFault             │
│  - 名前空間: Driver.*                            │
└──────────────────────────────────────────────────┘

```

**優先度が小さい層ほど先に実行されます。** これにより、
「ハードウェア読み取り → 決済判定 → ユーザー表示」という
自然な順序が保証されます。

### 2.2 状態遷移図（Application 層）

```mermaid

stateDiagram-v2
    direction LR
    [*] --> Idle
    Idle --> HasCredit : Accept first coin (INSERT_COIN)
    HasCredit --> HasCredit : More coins (INSERT_COIN)
    HasCredit --> Dispensing : Start dispensing (SELECT_ITEM) [balance >= price]
    HasCredit --> HasCredit : Insufficient (SELECT_ITEM) [balance < price]
    HasCredit --> ReturningChange : Cancel (CANCEL)
    Dispensing --> ReturningChange : Return change (DISPENSE_DONE) [balance > price]
    Dispensing --> Idle : Exact - done (DISPENSE_DONE) [balance == price]
    ReturningChange --> Idle : Change returned (CHANGE_RETURNED)
    Idle --> Error : Fault
    HasCredit --> Error : Fault
    Dispensing --> Error : Fault
    ReturningChange --> Error : Fault
    Error --> Idle : Maintenance reset (RESET)

```

---

## 3. GUI で XML を開く

### 3.1 起動

```powershell

cd C:...\StaTable\code
python -m statable_gui.main

```

> **環境変数の注意**: `QT_QPA_PLATFORM=offscreen` が設定されていると
> 画面に表示されません。`Remove-Item Env:QT_QPA_PLATFORM` で解除してください。

### 3.2 XML を開く

**File > Open Project...** で `docs/tutorial/vending_machine.xml` を選択。
**3つのタブ**（Driver / Middleware / Application）が表示されます。

### 3.3 各タブで確認できること

| 領域 | 内容 |
|------|------|
| マトリクス（上） | 状態 × イベント の遷移セル |
| Mermaid 図（中） | 状態遷移図 |
| SettingsPanel（右） | 状態一覧 / ロール関数一覧 |

---

## 4. Driver 層（ハードウェア抽象化）

### 4.1 状態

| 状態 | 種別 | 説明 |
|------|------|------|
| `Waiting` | initial | ハードウェアイベント待ち |
| `CoinPulse` | normal | コインセンサーエッジ検出 |
| `ButtonPressed` | normal | 商品ボタン押下 |
| `MotorRunning` | normal | ディスペンスモーター動作中 |
| `HardwareFault` | normal | ハードウェアフォルト |

### 4.2 イベント

| イベント | 配送方式 | 付随データ |
|---------|---------|-----------|
| `COIN_SENSOR` | queue | `coin_value`（uint32_t） |
| `BUTTON_SENSOR` | queue | `item_id`（uint8_t） |
| `MOTOR_COMPLETE` | direct | – |
| `HW_FAULT` | queue | `err_code`（uint8_t）、優先度 9 |
| `CLEAR_FAULT` | direct | – |

### 4.3 設計ポイント

- **キュー配送**: センサーイベントは `queue` で取りこぼし防止
- **優先度 9 の FAULT**: 通常イベントより先に処理される
- **セルアクション**: `Waiting + COIN_SENSOR` で Pre/Post を実演
---

## 5. Middleware 層（決済・在庫）

### 5.1 状態

| 状態 | 種別 | 説明 |
|------|------|------|
| `Waiting` | initial | 要求待ち |
| `Accumulating` | normal | コイン累積中 |
| `Ready` | normal | 決済可能 |
| `CheckingStock` | normal | 在庫確認中 |
| `Releasing` | normal | リリース中 |
| `MwError` | normal | ミドルウェアエラー |

### 5.2 排他リレーションの例

`Accumulating + ITEM_SELECT` セルには**排他リレーション**があります:

```xml

<Relation kind="exclusive" members="T1,T2" />

```

これにより、T1（残高十分）と T2（残高不足）は
**最大1つしか発火しない**ことが保証されます。

### 5.3 ネスト group の例

`Releasing + RELEASE_DONE` セルには**ネストされた group**:

```xml

<Relation kind="group" members="T1,T2"
          shared_condition="RoleFunc_Middleware_CheckStock(transition, ctx) != 0">
  <Children>
    <Relation kind="exclusive" members="T1,T2" />
  </Children>
</Relation>

```

**生成される C コード:**

```c

if (RoleFunc_Middleware_CheckStock(transition, ctx) != 0) {
    if (cond_with_change) {
        /* T1: お釣りあり */
    } else if (cond_exact) {
        /* T2: ちょうど */
    }
}

```

---

## 6. Application 層（ユーザー向けフロー）

### 6.1 状態

| 状態 | 種別 | 説明 |
|------|------|------|
| `Idle` | initial | コイン投入待ち |
| `HasCredit` | normal | クレジットあり |
| `Dispensing` | normal | ディスペンス中 |
| `ReturningChange` | normal | お釣り返却中 |
| `Error` | final | 致命的エラー |

### 6.2 セルアクション

`Idle + INSERT_COIN` セルには**セルアクション**があります:

```xml

<Actions>
  <Action role_function="Vending.PreCheck"
          trigger="before_transitions" />
  <Action role_function="Vending.PostCommit"
          trigger="after_transitions" />
</Actions>

```

**生成される C コード（順序）:**

```c

static STATE_Vending_t t_Idle_INSERT_COIN(...)
{
    STATE_Vending_t next_state = transition->from_state;
    /* Cell actions (before_transitions) */
    (void)RoleFunc_Vending_PreCheck(transition, ctx);
    /* Transition[T1] (Commit) */
    if (1) {
        next_state = STATE_Vending_HasCredit;
    }
    /* Cell actions (after_transitions) */
    (void)RoleFunc_Vending_PostCommit(transition, ctx);
    return next_state;
}

```

- **Pre**: 遷移評価の**前**（遷移が発火しなくても実行）
- **Post**: 遷移評価の**後**（Commit で early return しても実行）

### 6.3 ネスト group の実例

`Dispensing + DISPENSE_DONE` セル:

```xml

<Relation kind="group" members="T1,T2"
          shared_condition="ctx->data.stock > 0">
  <Children>
    <Relation kind="exclusive" members="T1,T2" />
  </Children>
</Relation>

```

「在庫がある場合のみ、お釣り返却または完了処理の**どちらか一方**を実行」。
---

## 7. コード生成

### 7.1 GUI から生成

1. **Generate > Code Generation...**
2. 出力先・生成方式・OS 種別を確認
3. **Generate** ボタン

### 7.2 CLI から生成（推奨）

```powershell

cd C:...\StaTable\code
python tools\gen_output_from_xml.py `
    --xml docs\tutorial\vending_machine.xml `
    --out output_vending

```

**期待:**

```

Loading: docs\tutorial\vending_machine.xml
  tabs:  ['Driver', 'Middleware', 'Application']
  gd:    variables=8, flags=2, interrupts=1
  roles: 27
  layers: 3
  config: folder_structure=by_layer, project_name=VendingMachineTutorial
Generating C code ...
  generated 24 files
  saved 24 files to ...\output_vending
Result: 12 .c / 12 .h under output_vending

```

### 7.3 生成ファイル構成

```

output_vending/
├── statable_all.h
├── statable_types_common.h
├── statable_init.c
├── statable_interrupt.c
├── statable_timer.c
├── statable_event_queue.c
├── osal.c / osal.h
├── VendingMachineTutorial_run.c
├── Driver/
│   ├── statable_types_Driver.h
│   ├── statable_role_functions_Driver.h / .c
│   └── statable_transitions_Driver.h / .c
├── Middleware/
│   └── （同様）
└── Vending/               ← layer_name="Vending"
    ├── statable_types_Vending.h
    ├── statable_role_functions_Vending.h / .c
    └── statable_transitions_Vending.h / .c

```

---

## 8. コンパイル検証

### 8.1 単一ツールチェーン

```powershell

python tools\verify_c_syntax.py --root output_vending --compiler gcc
python tools\verify_c_syntax.py --root output_vending --compiler arm

```

### 8.2 両ツールチェーン同時（推奨）

```powershell

python tools\verify_c_syntax.py --root output_vending --compiler both

```

**期待:**

```

==============================================================================
  Summary
==============================================================================
  gcc      PASS     (12/12)
  arm      PASS     (12/12)
  Overall:  ALL PASS
==============================================================================
  Log saved to: ...verify_report\verify_c_syntax_YYYYMMDD_HHMMSS.log
==============================================================================

```

### 8.3 エビデンスログ

実行のたびに `verify_report/verify_c_syntax_YYYYMMDD_HHMMSS.log` が
自動保存されます。**タイムスタンプ・git コミット・環境情報**が
含まれるため、リリース時の証跡として利用できます。
---

## 9. よくある落とし穴

### 9.1 C-50: namespace は layer_name と前方一致が必要（v2.5.1 以前）

**症状:**

```

error: implicit declaration of function 'RoleFunc_Vending_PreCheck'

```

**原因:** `layer_name="Application"` で `namespace="Vending"` を使うと、
呼び出しは生成されるが**宣言が欠落**します。
**対処:**
- v2.5.1 以前: `namespace="App"` のように前方一致する名前を使う
- **v2.5.2 以降**: 任意の namespace が使用可能（C-50 解消済み）

### 9.2 (void) 抑制のユーザー編集（v2.5.2 以降）

生成された Role 関数は、`ctx->data.*` のローカルポインタを宣言し、
未使用警告を避けるため `(void)` で明示的に破棄します。

```c

uint32_t *const balance = &ctx->data.balance;
...
/* [[STABLE_USER_CODE_START:...]] */
/* --- auto-generated: unused-variable suppression --- */
(void)balance;
...
/* [[STABLE_USER_CODE_END:...]] */

```

**v2.5.2 以降、`(void)` 群はユーザー編集可能領域（マーカー内）に移動しました。**
- 初回生成: `(void)` 群がマーカー内に表示される
- ユーザーが不要な行を削除 → 再生成しても**復活しない**

### 9.3 マージ動作の理解

StaTable は再生成時に**ユーザー編集を保持**します。

| マーカー | 用途 |
|---------|------|
| `[[STABLE_USER_CODE_START]]` ... `END` | ファイル全体のユーザー領域 |
| `[[STABLE_USER_CODE_START:Driver_Init]]` ... `END:Driver_Init` | 関数単位のユーザー領域 |
| `[[STABLE_USER_CODE_TAIL_START]]` ... `END` | ファイル末尾のユーザー領域 |

**マーカー内の編集は保持、外は上書き**されます。
---

## 10. 演習問題

### 演習1: 新しい状態を追加

Application 層に `Refunding` 状態を追加し、
`ReturningChange → Refunding → Idle` の遷移を作ってください。

### 演習2: タイムアウト処理

Application 層で「`HasCredit` 状態が 60秒続いたら自動でキャンセル」
する遷移を追加してください。
**ヒント:** `EventKind.TIME` を使う。

### 演習3: 在庫切れ時の表示

Middleware 層で `STOCK_EMPTY` を受けたとき、
Application 層に「在庫切れ表示」を促すイベントを追加してください。
---

## 11. 参考資料

| 資料 | 場所 |
|------|------|
| 全体仕様書 | `docs/SPEC_OVERVIEW_ja.md` |
| Issue 記録 | `docs/ISSUES_v2_5.md` |
| TUTORIAL XML | `docs/tutorial/vending_machine.xml` |
| Vending タブ版 XML | `docs/tutorial/vending_machine_vending_tab.xml` |
| コンパイル検証ツール | `tools/verify_c_syntax.py` |
| 生成ツール | `tools/gen_output_from_xml.py` |
