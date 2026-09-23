# R-14 ① OSAL 移植ガイド作成

## 📄 `code/docs/OSAL_PORTING_GUIDE_ja.md`（新規）

以下を新規ファイルとして保存してください（**BOM なし UTF-8**）：

```markdown
# OSAL 移植ガイド

> **対象読者:** 新しい OS（FreeRTOS, ThreadX, Zephyr, RT-Thread など）や、
> 独自のベアメタル環境に StaTable 生成コードを移植したい開発者。
>
> **目的:** OSAL（OS Abstraction Layer）の契約を理解し、自分の環境に
> 合わせた実装を追加できるようになる。

---

## 1. OSAL とは

StaTable が生成する C コードは、OS に依存する処理を **OSAL** と呼ぶ
抽象化層に集約しています。生成コード本体は OSAL API だけを呼び出し、
OS 固有の処理は OSAL 実装側に閉じ込められています。

```
┌────────────────────────────────────┐
│  StaTable 生成コード                │
│  (statable_*.c, *_run.c)           │
│   → OSAL_* API を呼ぶだけ           │
└──────────────┬─────────────────────┘
               │
┌──────────────▼─────────────────────┐
│  OSAL API (osal.h)                 │
│  - Mutex / Semaphore / Queue       │
│  - Critical section                │
└──────────────┬─────────────────────┘
               │
┌──────────────▼─────────────────────┐
│  OSAL 実装 (osal_<os>.c)           │
│  - NonRTOS / FreeRTOS / ThreadX    │
│  - ★ あなたの環境用に追加する       │
└────────────────────────────────────┘
```

**メリット:**
- 生成コードを変更せずに、OS を差し替えられる
- OS 移植時に触るファイルは `osal_<os>.c` / `.h` の 2 つだけ

---

## 2. 契約（インターフェース一覧）

移植先で実装すべき**すべての関数**を以下に示します。
この一覧が「契約」であり、**すべて実装すれば生成コードは動作します**。

### 2.1 型定義

| 型 | 用途 |
|----|------|
| `OSAL_Status_t` | 戻り値（下記 enum） |
| `OSAL_Mutex_t` | Mutex ハンドル |
| `OSAL_Semaphore_t` | Semaphore ハンドル |
| `OSAL_Queue_t` | Queue ハンドル |

### 2.2 enum: `OSAL_Status_t`

| 値 | 意味 |
|----|------|
| `OSAL_OK` | 成功 |
| `OSAL_ERROR` | 一般エラー（引数不正等） |
| `OSAL_TIMEOUT` | タイムアウト |
| `OSAL_BUSY` | リソースビジー |

### 2.3 Mutex API

| 関数 | シグネチャ | 責務 |
|------|-----------|------|
| Create | `OSAL_Status_t OSAL_Mutex_Create(OSAL_Mutex_t *mutex)` | 初期化 |
| Lock   | `OSAL_Status_t OSAL_Mutex_Lock(OSAL_Mutex_t *mutex, uint32_t timeout_ms)` | 取得（timeout=0 は即時） |
| Unlock | `OSAL_Status_t OSAL_Mutex_Unlock(OSAL_Mutex_t *mutex)` | 解放 |

### 2.4 Semaphore API

| 関数 | シグネチャ | 責務 |
|------|-----------|------|
| Create | `OSAL_Status_t OSAL_Semaphore_Create(OSAL_Semaphore_t *sem, uint32_t max_count, uint32_t initial_count)` | 初期化 |
| Take   | `OSAL_Status_t OSAL_Semaphore_Take(OSAL_Semaphore_t *sem, uint32_t timeout_ms)` | 取得（カウント減） |
| Give   | `OSAL_Status_t OSAL_Semaphore_Give(OSAL_Semaphore_t *sem)` | 返却（カウント増） |

### 2.5 Queue API

| 関数 | シグネチャ | 責務 |
|------|-----------|------|
| Create  | `OSAL_Status_t OSAL_Queue_Create(OSAL_Queue_t *queue, void *buffer, uint32_t size, uint32_t item_size)` | 初期化 |
| Send    | `OSAL_Status_t OSAL_Queue_Send(OSAL_Queue_t *queue, const void *item, uint32_t timeout_ms)` | 送信 |
| Receive | `OSAL_Status_t OSAL_Queue_Receive(OSAL_Queue_t *queue, void *item, uint32_t timeout_ms)` | 受信 |

### 2.6 Critical Section API

| 関数 | シグネチャ | 責務 |
|------|-----------|------|
| Enter | `void OSAL_Critical_Enter(void)` | 割り込み禁止 |
| Exit  | `void OSAL_Critical_Exit(void)` | 割り込み許可 |

---

## 3. 移植手順

### Step 1: 既存実装をコピー

`code/tools/templates/` または生成済みの `osal.c`（NonRTOS 実装）を
参考に、新しいファイルを作成します。

```
osal_<あなたのOS>.h   ← API 宣言（既存の osal.h と同一内容でOK）
osal_<あなたのOS>.c   ← 実装
```

### Step 2: OSAL 型をマッピング

各ハンドル型を、移植先のネイティブ型に置き換えます。

**例（FreeRTOS）:**

| OSAL 型 | FreeRTOS 型 |
|---------|------------|
| `OSAL_Mutex_t` | `SemaphoreHandle_t` |
| `OSAL_Semaphore_t` | `SemaphoreHandle_t` |
| `OSAL_Queue_t` | `QueueHandle_t` |

**例（ThreadX）:**

| OSAL 型 | ThreadX 型 |
|---------|-----------|
| `OSAL_Mutex_t` | `TX_MUTEX` |
| `OSAL_Semaphore_t` | `TX_SEMAPHORE` |
| `OSAL_Queue_t` | `TX_QUEUE` |

### Step 3: 各関数を実装

契約（第2章）に従い、各 API を移植先のネイティブ API に**1対1で対応**させます。

**FreeRTOS の例:**

```c
OSAL_Status_t OSAL_Mutex_Create(OSAL_Mutex_t *mutex)
{
    if (mutex == NULL) {
        return OSAL_ERROR;
    }
    *mutex = xSemaphoreCreateMutex();
    return (*mutex != NULL) ? OSAL_OK : OSAL_ERROR;
}

OSAL_Status_t OSAL_Mutex_Lock(OSAL_Mutex_t *mutex, uint32_t timeout_ms)
{
    if (mutex == NULL) {
        return OSAL_ERROR;
    }
    TickType_t ticks = (timeout_ms == 0) ? 0 : pdMS_TO_TICKS(timeout_ms);
    BaseType_t rc = xSemaphoreTake(*mutex, ticks);
    return (rc == pdTRUE) ? OSAL_OK : OSAL_TIMEOUT;
}

OSAL_Status_t OSAL_Mutex_Unlock(OSAL_Mutex_t *mutex)
{
    if (mutex == NULL) {
        return OSAL_ERROR;
    }
    BaseType_t rc = xSemaphoreGive(*mutex);
    return (rc == pdTRUE) ? OSAL_OK : OSAL_ERROR;
}
```

### Step 4: ビルド時に選択

StaTable の設定で `os_type` を新しい OS 名（例: `myos`）に変更し、
生成される `osal_myos.c` / `.h` をビルドに含めます。

---

## 4. 各関数の責務（詳細）

移植時に迷いやすいポイントをまとめます。

### 4.1 `OSAL_Mutex_Create`

- `mutex` が `NULL` → `OSAL_ERROR`
- 二重初期化の防止は**呼び出し側の責任**（OSAL は関与しない）
- 失敗時は `OSAL_ERROR` を返す

### 4.2 `OSAL_Mutex_Lock`

- `timeout_ms == 0` → **即時取得を試みる**（ブロックしない）
- `timeout_ms > 0` → 指定ミリ秒まで待機
- 取得失敗（他者が保持中）→ `OSAL_TIMEOUT` または `OSAL_BUSY`
- **`OSAL_BUSY` と `OSAL_TIMEOUT` の使い分け:**
  - `OSAL_BUSY`: リソースが使用中で即座に取得不可
  - `OSAL_TIMEOUT`: 待機したが時間切れ
  - **どちらを返すかは移植先の慣習に合わせて良い**（生成コードは両方を受け入れる）

### 4.3 `OSAL_Semaphore_Create`

- `max_count` を超える `initial_count` は**エラー**（`OSAL_ERROR`）
- カウント上限・下限の管理は実装側の責任

### 4.4 `OSAL_Semaphore_Take`

- カウント 0 の場合：
  - `timeout_ms == 0` → `OSAL_BUSY` 即時返却
  - `timeout_ms > 0` → 待機 → 時間切れなら `OSAL_TIMEOUT`

### 4.5 `OSAL_Semaphore_Give`

- カウントが `max_count` に達している → `OSAL_BUSY`
- それ以外 → カウント増加、`OSAL_OK`

### 4.6 `OSAL_Queue_Create`

- `buffer`, `size`, `item_size` をすべて保持
- `head` / `tail` / `count` の初期化は実装側
- リングバッファ形式を推奨

### 4.7 `OSAL_Queue_Send` / `Receive`

- アイテムサイズは `item_size` バイト
- **メモリコピー方式**（ポインタ渡しではない）
- `Send` 時: キュー満杯 → `OSAL_BUSY`
- `Receive` 時: キュー空 → `OSAL_BUSY`

### 4.8 `OSAL_Critical_Enter` / `Exit`

- `Enter`: グローバル割り込み禁止
- `Exit`: グローバル割り込み許可
- **ネスト対応は必須**（実装によっては `Enter` を2回呼ぶケースあり）

**ARM Cortex-M の例:**

```c
static volatile uint32_t g_critical_nesting = 0;

void OSAL_Critical_Enter(void)
{
    __disable_irq();
    g_critical_nesting++;
}

void OSAL_Critical_Exit(void)
{
    if (g_critical_nesting > 0) {
        g_critical_nesting--;
    }
    if (g_critical_nesting == 0) {
        __enable_irq();
    }
}
```

> **注意:** `__disable_irq` / `__enable_irq` は ARM の組み込み関数です。
> 他のアーキテクチャでは `portSET_INTERRUPT_MASK_FROM_ISR()` 等に置き換えてください。

---

## 5. 移植時のテスト

OSAL を移植したら、以下を確認してください。

### 5.1 単体テスト（推奨）

| テスト項目 | 確認内容 |
|-----------|---------|
| Mutex 基本 | Create → Lock → Unlock が順に成功 |
| Mutex 競合 | 2 スレッド相当の Lock で排他が働く |
| Semaphore カウント | Give で増、Take で減 |
| Semaphore 上限 | max_count 到達時の Give で `OSAL_BUSY` |
| Queue FIFO | Send 順序と Receive 順序が一致 |
| Queue 満杯 | size 到達時の Send で `OSAL_BUSY` |
| Critical ネスト | Enter×2 → Exit×2 で正しく復帰 |

### 5.2 StaTable の CI で検証

```powershell
# 生成コードを strict モードでコンパイル
python tools\verify_c_syntax.py --root output --compiler both --strict
```

**`-Wall -Wextra -Werror` で警告ゼロを目指してください。**

---

## 6. よくある落とし穴

| # | 症状 | 原因 | 対処 |
|---|------|------|------|
| 1 | `unused parameter` 警告 | 引数を使っていない | `(void)param;` で明示的に破棄 |
| 2 | `OSAL_BUSY` と `OSAL_TIMEOUT` の混同 | 実装が未定義 | 第4章の使い分けを参照 |
| 3 | 割り込みネスト不整合 | `Enter`/`Exit` の対応漏れ | カウンタ方式を実装 |
| 4 | メモリコピー漏れ | Queue でポインタ渡し | `item_size` バイトをコピー |
| 5 | Critical 区間が長すぎる | 割り込み禁止を長く保持 | 最小限の処理に留める |
| 6 | Mutex の `max_count` | （Semaphore と混同） | Mutex は binary のみ |
| 7 | 割り込みコンテキストから Lock | RTOS により禁止 | ISR 用 API を別途使用 |

---

## 7. 参考: NonRTOS 実装（最小構成）

`code/tools/templates/osal.c` に NonRTOS 実装のサンプルがあります。
**移植の出発点として最適**です。

特徴:
- RTOS なしの**ベアメタル環境**
- Mutex / Semaphore は**フラグ管理のみ**（ブロッキングなし）
- Queue は**リングバッファ**による実装
- Critical section は**割り込み禁止**

**移植のコツ:** NonRTOS 実装を**コピー → 各関数を自分の OS の API に置換**するのが最短経路です。

---
## 8. 既存の OS 実装

StaTable には以下の実装が同梱されています（参考にどうぞ）。

| os_type | ファイル | 状態 |
|---------|---------|------|
| `non_rtos` | `osal.c` / `osal.h` | 完全実装 |
| `freertos` | `osal_freertos.c` / `.h` | 雛形（include のみ） |
| `threadx` | `osal_threadx.c` / `.h` | 雛形（include のみ） |

### 内部構造（参考）

OSAL テンプレートは `codegen/code_templates.py` の `OSAL` 辞書に定義されています。
新しい OS を StaTable 本体に統合する場合、この辞書に追加エントリを記述します：

```python
'os_types': {
    'non_rtos': {
        'name': 'NonRTOS',
        'description': 'No RTOS (bare metal)',
        'header': 'osal.h',
        'source': 'osal.c',
    },
    # 新しい OS を追加する例:
    # 'myos': {
    #     'name': 'MyOS',
    #     'description': 'My custom RTOS',
    #     'header': 'osal_myos.h',
    #     'source': 'osal_myos.c',
    # },
},
---

## 9. お問い合わせ・貢献

移植実装が完成したら、以下の情報を添えて共有してください。

| 項目 | 内容 |
|------|------|
| OS 名 | 例: FreeRTOS v10.4.3 |
| 対象 MCU | 例: STM32F407 |
| テスト結果 | `verify_c_syntax.py --strict` の PASS 可否 |

**StaTable 本体への統合**を希望する場合は、`osal_<os>.c/.h` を
`code/tools/templates/` に追加し、PR を送ってください。

---

## 変更履歴

| バージョン | 日付 | 内容 |
|-----------|------|------|
| 1.0 | 2026-09-23 | 初版（R-14 ① として作成） |
```

---

## 📋 ファイル作成後の手順

### Step 1: 構文確認（マークダウンなので目視のみ）

```powershell
cd C:\Users\user\OneDrive\ドキュメント\GitHub\StaTable\code

# 文字化け・BOM チェック
Format-Hex docs\OSAL_PORTING_GUIDE_ja.md | Select-Object -First 3
```

**期待:** 先頭が `23`（`#`）で始まる。`EF BB BF` なら BOM 付き → 保存し直し。

### Step 2: 既存ドキュメントとの整合性確認

```powershell
# 「No Japanese characters」CI ジョブへの影響確認
# (docs/ 配下は除外されているはず)
python tools\find_all_japanese.py
```

**もし `docs/OSAL_PORTING_GUIDE_ja.md` が CI で引っかかる場合:** `find_all_japanese.py` の除外対象を確認してください（既存の `TUTORIAL_ja.md` と同様に扱われるはず）。

---

## 📋 次のアクション

1. **`code/docs/OSAL_PORTING_GUIDE_ja.md` を新規作成**（上記内容、BOM なし UTF-8）
2. **Step 1〜2 を実行** → 結果を貼ってください
3. OK なら **コミット** → プッシュ → CI 確認

**ファイル作成後の確認結果をお待ちしています。**

> **補足:** 内容の追加・修正のご希望があれば、お知らせください。特に：
> - FreeRTOS / ThreadX の実装サンプルを増やす
> - 特定の MCU（STM32 / ESP32 等）向けの記述を追加
> - CI 統合の方法を詳述
>
