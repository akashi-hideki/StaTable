# ISR コンテキスト対応 仕様書

## 1. 目的

割り込み処理（ISR）内で **`ctx` ポインタとロール関数を簡単に使える** ようにする。また、生成された ISR は **ユーザーが編集可能** で、再生成後も編集内容が保持される。

---

## 2. 現状の問題

### 2-1. `ctx` が使えない

```c
void ISR_TIMER0(void)
{
    /* ctx が無い → ctx->data.xxx が書けない */
}
```

### 2-2. ロール関数が呼べない

ロール関数は `(transition, ctx)` の2引数が必要。
ISR には `transition` が無い。

### 2-3. ユーザー編集が消える

現状の `interrupt_generator.py` は
**毎回フル生成** するため、
ユーザーが加えた編集が
再生成時に**全て失われる**。

---

## 3. 実現したいこと

### 3-1. ISR で `ctx` を使えるようにする

ISR の先頭に自動挿入：

```c
void ISR_TIMER0(void)
{
    SystemContext_t *ctx = &g_ctx;   /* 自動生成 */
    (void)ctx;
    
    /* ユーザーコード: ctx->data.xxx が自由に書ける */
}
```

### 3-2. ロール関数を呼べるようにする

マクロ経由で NULL transition を渡す：

```c
RoleFunc_Application_HandleTick(NULL, ctx);
```

ロール関数側で `transition == NULL` ガード：

```c
if (transition != NULL) {
    /* transition 使用コード */
}
```

### 3-3. ユーザー編集を保持する

ISR 本体に **ユーザーコードマーカー** を埋め込む：

```c
void ISR_TIMER0(void)
{
    /* 自動生成部 */
    SystemContext_t *ctx = &g_ctx;
    LOG_DEBUG("Enter ISR");
    
    /* [[STABLE_USER_CODE_START:ISR_TIMER0]] */
    /* ユーザー実装コードをここに記述 */
    /* [[STABLE_USER_CODE_END:ISR_TIMER0]] */
    
    LOG_DEBUG("Exit ISR");
}
```

再生成時：
- マーカー内 = ユーザーコード → **保持**
- マーカー外 = 自動生成 → **更新**

### 3-4. GUI でロール関数を選択できる

割り込み設定ダイアログの Action 欄に
**ロール関数選択ボタン** を追加：

```
Action: [RoleFunc_Application_HandleTick] [参照...] [削除]
```

---

## 4. 生成コード仕様

### 4-1. ISR 構造

```c
/**
 * @brief  TIMER0 割り込みハンドラ
 * @note   1ms周期タイマ
 */
void ISR_TIMER0(void)
{
    /* ===== コンテキスト参照（自動生成） ===== */
    SystemContext_t *ctx = &g_ctx;
    (void)ctx;

    /* ===== 入場ログ（自動生成） ===== */
    LOG_DEBUG("Enter ISR: TIMER0");

    /* ===== アクション（自動生成） ===== */
    ctx->data.g_system_tick++;
    if (err_flag) {
        RoleFunc_Application_HandleError(NULL, ctx);
    }

    /* ===== ユーザー追加領域 ===== */
    /* [[STABLE_USER_CODE_START:ISR_TIMER0]] */
    /* ユーザー追加コードをここに記述 */
    /* [[STABLE_USER_CODE_END:ISR_TIMER0]] */

    /* ===== 退場ログ（自動生成） ===== */
    LOG_DEBUG("Exit ISR: TIMER0");
}
```

### 4-2. ロール関数の NULL transition ガード

```c
int RoleFunc_Application_HandleTick(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx)
{
    /* ★ NULL transition ガード */
    STATE_Application_t from_state = STATE_Application_MAX;
    EVENT_Application_t event = EVENT_Application_NONE;
    if (transition != NULL) {
        from_state = transition->from_state;
        event = transition->event;
    }
    (void)from_state;
    (void)event;

    /* ===== ctx->data へのローカルポインタ ===== */
    uint32_t *const counter = &ctx->data.counter;

    /* ===== 戻り値 ===== */
    int ret = 0;

    /* [[STABLE_USER_CODE_START:Application_HandleTick]] */
    /* [[STABLE_USER_CODE_END:Application_HandleTick]] */

    return ret;
}
```

### 4-3. インクルード

`statable_interrupt.c` の include セクション：

```c
#include "statable_all.h"    /* ★ ctx, g_ctx の参照 */
```

`statable_all.h` には既に
`extern SystemContext_t g_ctx;` が
含まれている前提。

---

## 5. GUI 仕様

### 5-1. 割り込み設定ダイアログ

**Action 入力欄：**

```
┌──────────────────────────────────────────────────┐
│ Action 一覧                                       │
├──────────────────────────────────────────────────┤
│ [条件]           [Action]              [操作]    │
│ ───────────────────────────────────────────────  │
│ [________]  [RoleFunc_Application_XXX] [参照][削除]│
│ [________]  [ctx->data.tick++         ] [参照][削除]│
│                                                   │
│                          [+ Action 追加]         │
└──────────────────────────────────────────────────┘
```

**「参照...」ボタン押下時：**

```
┌─ ロール関数を選択 ────────────────┐
│ ○ RoleFunc_Driver_Init            │
│ ○ RoleFunc_Driver_LogError        │
│ ● RoleFunc_Application_HandleTick │  ← 選択
│ ○ RoleFunc_Application_Stop       │
│                                    │
│              [OK]  [キャンセル]   │
└────────────────────────────────────┘
```

選択後、Action 欄に：
```
RoleFunc_Application_HandleTick
```

**判定ロジック：**

- ユーザーが **`RoleFunc_` で始まる識別子** を入れた場合
  → 生成時に **ロール関数呼び出し** として扱う
- それ以外は **そのまま C コード** として出力

---

## 6. 編集保持の仕組み

### 6-1. マーカー命名規則

| 種別 | マーカー |
|------|---------|
| 関数本体（ユーザー領域） | `[[STABLE_USER_CODE_START:ISR_<name>]]` ～ `[[STABLE_USER_CODE_END:ISR_<name>]]` |
| ファイル末尾ユーザー領域 | `[[STABLE_USER_CODE_TAIL_START]]` ～ `[[STABLE_USER_CODE_TAIL_END]]` |

### 6-2. 再生成時の動作

1. 既存ファイルから **マーカー内のユーザーコードを抽出**
2. 新規生成ファイルの **同名マーカー内に注入**
3. マーカー外は **完全に新規生成内容で上書き**

### 6-3. `code_merger.py` 対応

- `extract_func_user_code(content, "ISR_TIMER0")`
- `inject_func_user_code(content, "ISR_TIMER0", user_code)`

関数単位の抽出・注入は
**既存ロジックを流用** 可能。

---

## 7. 変更対象ファイル

### 7-1. 必須（機能実装）

| # | ファイル | 変更 |
|---|---------|------|
| 1 | `codegen/interrupt_generator.py` | ① ISR 先頭に `ctx` 自動挿入 ② ユーザーコードマーカー追加 ③ ロール関数呼び出し対応 |
| 2 | `codegen/role_function_generator.py` | `transition == NULL` ガード追加 |
| 3 | `statable_gui/interrupt_handler_edit_dialog.py` | Action 欄に「参照...」ボタン追加 |

### 7-2. 関連（影響確認）

| # | ファイル | 変更 |
|---|---------|------|
| 4 | `codegen/c_code_generator.py` | `statable_interrupt.c` の include に `statable_all.h` 追加 |
| 5 | `codegen/code_templates.py` | ISR テンプレート追加 |
| 6 | `codegen/code_merger.py` | `ISR_<name>` マーカー対応（既存ロジック流用可） |

### 7-3. 参照用

| # | ファイル | 用途 |
|---|---------|------|
| 7 | `statable/global_defs.py` | `InterruptHandlerDef` / `InterruptAction` 定義 |

---

## 8. テスト計画

### 8-1. 単体テスト

**`tests/test_isr_context.py`（新規）**

| # | 内容 |
|---|------|
| 1 | ISR に `ctx` ポインタが自動挿入される |
| 2 | `(void)ctx;` が含まれる |
| 3 | ユーザーコードマーカー `ISR_<name>` が含まれる |
| 4 | Action が `ctx->...` 形式なら そのまま出力 |
| 5 | Action が `RoleFunc_XXX` なら `RoleFunc_XXX(NULL, ctx);` に変換 |
| 6 | `statable_interrupt.c` の include に `statable_all.h` が含まれる |

**`tests/test_role_function_generator.py`（既存に追加）**

| # | 内容 |
|---|------|
| 7 | `transition == NULL` ガードが含まれる |
| 8 | ガード内で `from_state` / `event` のデフォルト値設定 |
| 9 | `(void)from_state;` / `(void)event;` 出力 |

### 8-2. 統合テスト

| # | 内容 |
|---|------|
| 10 | 生成 → ISR にユーザーコード追加 → 再生成 → 保持確認 |
| 11 | マーカー外の変更は上書きされることを確認 |

### 8-3. GUI テスト

手動確認（GUI 自動テストは対象外）：

- [ ] 割り込み設定ダイアログに「参照...」ボタン表示
- [ ] ロール関数選択ダイアログが開く
- [ ] 選択後 Action 欄に反映
- [ ] OK で保存

---

## 9. 将来拡張

| # | 項目 | 備考 |
|---|------|------|
| 1 | ISR 専用ロール関数（`ISR_RoleFunc_XXX`） | `transition` 引数を省略した専用シグネチャ |
| 2 | `ISR_CALL_ROLEFUNC` マクロ | NULL チェックを1箇所に集約 |
| 3 | ISR 実行コンテキスト情報（名前・優先度） | `InterruptContext_t` 構造体 |
| 4 | 割り込み優先度管理 | NVIC 設定コード生成 |
| 5 | ISR のデバッグログ強化 | 入退場タイムスタンプ |

---

## 10. 実装の流れ（次スレッド以降）

1. **共有**：3ファイル（interrupt_generator / role_function_generator / interrupt_handler_edit_dialog）
2. **完全版 `interrupt_generator.py`** 出力
3. **`role_function_generator.py`** の NULL ガード追加（完全版）
4. **`interrupt_handler_edit_dialog.py`** の GUI 拡張（完全版）
5. **`code_templates.py`** の ISR テンプレート追加
6. **`c_code_generator.py`** の include 追加
7. **`tests/test_isr_context.py`** 新規追加
8. **既存回帰テスト実行**

---

## 11. スコープ確認

### 今回実装する

- ✅ ISR 内 `ctx` ポインタ自動挿入
- ✅ ISR ユーザーコードマーカー
- ✅ ロール関数の NULL transition ガード
- ✅ GUI でロール関数選択
- ✅ 再生成時の編集保持

### 将来実装（今回は対象外）

- ⏸ ISR 専用ロール関数シグネチャ
- ⏸ NVIC 設定生成
- ⏸ 割り込み優先度管理

---

## 12. 新スレッドで最初にやること

以下を **貼り付けて** 開始：

```
前スレッドの続きです。
ISR コンテキスト対応を実装します。

仕様：
- ISR 先頭に ctx ポインタを自動挿入
- ISR 本体にユーザーコードマーカーを埋め込み、再生成時も編集を保持
- ロール関数に NULL transition ガード追加
- GUI で Action 欄にロール関数選択ボタン追加

以下ファイルを共有します：
- code/codegen/interrupt_generator.py
- code/codegen/role_function_generator.py
- code/statable_gui/interrupt_handler_edit_dialog.py
```

---

以上。**この仕様でよろしいですか？**

- (a) OK → 新スレッドで3ファイルを共有
- (b) 修正 → ご指摘箇所をお聞かせください