# StaTable 通信モニター機能 仕様書 v1.2

| 項目 | 値 |
|---|---|
| 対象リリース | v3.6.0（マイナー） |
| 対象 MCU | STM32 シリーズ（F4 / F7 / H7 / G4） |
| ログ形式 | psblog/v1（`SPEC_PSBLOG.md` 準拠） |
| ステータス | 確定 |
| 最終更新 | 2026-11-08 |

---

## 1. 目的とスコープ

### 1.1 目的

1. 生成コードに **グローバル変数モニター** 通信プロトコルを組み込む
2. 外部モニターから **変数 ID を指定した読み出し** を可能にする
3. **PC 側 SDK（Python 先行 / C# は v3.6.1）** を提供する
4. SDK に **通信ログ機能** を内蔵し、**psblog/v1** 形式で出力する
5. **ターミナルソフト（TeraTerm 等）でそのままデバッグ** できる ASCII モードを提供する

**ログ取得は GET のみで完結する。変数の書き換え（SET）は本機能のスコープ外。**

### 1.2 スコープ

| 層 | 成果物 | 所有者 |
|---|---|---|
| デバイス側 | プロトコル層・変数レジストリ（生成 C コード） | StaTable |
| ワイヤ | ASCII フレーミング（`STX + 本文 + CR + ETX`） | StaTable |
| モニター SDK | Python（`statable-monitor`） / C#（`StaTable.Monitor`、v3.6.1） | StaTable |
| ログ形式 | psblog/v1（writer = StaTable / reader = PowerSimBuilder） | StaTable / PSB |
| GUI | ユーザーが SDK を使って構築 | ユーザー |

### 1.3 スコープ外

- 変数の書き換え（SET コマンド）
- バイナリモード（v3.7.0 候補）
- CRC 付きフレーム（v3.7.0 候補）
- 配列・構造体の要素アクセス
- 完成品 GUI アプリケーション
- STM32 以外の MCU / ベンダー対応

---

## 2. 全体アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│ ユーザー GUI（Python / C# / 任意）                        │
└─────────────────────────────────────────────────────────┘
              ▲ イベント / API
              │
┌─────────────────────────────────────────────────────────┐
│ モニター SDK                                              │
│  ├ ConnectionManager   （接続・再接続・タイムアウト）       │
│  ├ CommandClient       （ASCII フレーム送受信）            │
│  ├ VariableRegistry    （LIST 応答 / XML から構築）        │
│  ├ PollingController   （PC 側周期制御、最小 100 ms）      │
│  ├ EventDispatcher     （ValueUpdated 等）                │
│  ├ XmlMapper           （応答 → XML 要素）                │
│  └ PStaBlogLogger      （psblog/v1 writer）              │
└─────────────────────────────────────────────────────────┘
              ▲ UART（ASCII モードのみ）
              │
┌─────────────────────────────────────────────────────────┐
│ デバイス（STM32 生成コード）                              │
│  ├ comm_monitor.c      （受信状態機械・ディスパッチャ）     │
│  ├ comm_commands.c     （コマンドテーブル + ユーザー拡張）  │
│  ├ comm_registry.c     （変数レジストリ）                  │
│  ├ comm_ring.c         （SPSC リングバッファ）            │
│  └ ユーザー手動実装     （UART 初期化・ISR 登録・TX 登録）  │
└─────────────────────────────────────────────────────────┘
              │
              ▼ psblog/v1（PC 側で整形して出力）
       PowerSimBuilder（reader）
```

---

## 3. ASCII モード仕様

### 3.1 フレーミング

```
要求: STX  <command text>  CR  ETX
      0x02 ...              0x0D 0x03

応答: STX  <response text>  CR  ETX
```

| 要素 | 値 | 備考 |
|---|---|---|
| STX | `0x02` | フレーム開始 |
| 本文 | ASCII（0x20〜0x7E） | コマンド・ID・値すべて ASCII |
| CR | `0x0D` | 本文終端 |
| ETX | `0x03` | フレーム終端 |
| CRC | **なし** | ターミナルで入力できないため廃止 |
| 最大本文長 | 96 B（`COMM_MONITOR_ASCII_BODY_MAX`） | 超過時はフレーム破棄 |

- CR の直後が ETX でなければフレーム破棄
- 不正文字（制御文字・非 ASCII）が来たらフレーム破棄して STX 待ちに戻る
- 先頭バイトが STX 以外は破棄（バイナリモードなし）

### 3.2 コマンド（要求）

| コマンド | 本文 | 説明 |
|---|---|---|
| `PING` | `PING` | 生存確認 + ファーム識別 |
| `LIST` | `LIST` | 変数レジストリ列挙 |
| `GET` | `GET <id>[,<id>,...] [compact]` | 1 つまたは複数 ID の読み出し |
| `HELP` | `HELP` | コマンド一覧 |

- `<id>` は 10 進 ASCII
- コマンド名は大文字小文字を区別しない
- `SET` は存在しない（送ると `NAK ret=5 reason=cmd`）

### 3.3 応答形式

```
ACK ret=0 <key>=<value> [<key>=<value> ...]
NAK ret=<n> reason=<理由> [<key>=<value> ...]
```

### 3.4 各コマンドの応答例

#### PING

```
要求: STX "PING" CR ETX
応答: STX "ACK ret=0 fw=3.6.0 crc=8A3F21C7 vars=30" CR ETX
```

| キー | 意味 |
|---|---|
| `fw` | ファームウェア版 |
| `crc` | XML の CRC32（§6.3 整合性検証用） |
| `vars` | 変数件数 |

#### LIST

`LIST` は **1 変数 1 応答**。

```
要求: STX "LIST" CR ETX
応答: STX "ACK ret=0 vars=30" CR ETX
応答: STX "ACK ret=0 id=0 name=g_system_tick type=uint32_t unit=1ms group=Timer" CR ETX
応答: STX "ACK ret=0 id=1 name=error_code type=uint8_t unit=- group=System" CR ETX
応答: STX "ACK ret=0 id=2 name=oven_target_temp type=uint16 unit=degC group=Hardware" CR ETX
...（30 変数分）
```

- 先頭応答で `vars=<n>` を通知
- 続く n 件を読む

#### GET（1 ID）

```
要求: STX "GET 3" CR ETX
応答: STX "ACK ret=0 id=3 name=oven_current_temp type=uint16 value=25 unit=degC" CR ETX
```

#### GET（複数 ID）

```
要求: STX "GET 3,7,15" CR ETX
応答: STX "ACK ret=0 id=3 name=oven_current_temp value=25 id=7 name=heater_top_duty value=100 id=15 name=thermistor_top value=31" CR ETX
```

#### GET（compact 形式）

高レートロギング用。メタデータを省き `<id>=<value>` のみ。

```
要求: STX "GET 3,7,15 compact" CR ETX
応答: STX "ACK ret=0 3=25 7=100 15=31" CR ETX
```

#### エラー

```
要求: STX "GET 99" CR ETX
応答: STX "NAK ret=2 id=99 reason=idx" CR ETX

要求: STX "GET abc" CR ETX
応答: STX "NAK ret=1 reason=parse" CR ETX

要求: STX "FOO" CR ETX
応答: STX "NAK ret=5 reason=cmd" CR ETX

要求: STX "GET" CR ETX
応答: STX "NAK ret=7 reason=args" CR ETX

要求: STX "SET 2 210" CR ETX
応答: STX "NAK ret=5 reason=cmd" CR ETX
```

#### HELP

```
要求: STX "HELP" CR ETX
応答: STX "ACK ret=0 cmds=PING,LIST,GET,HELP" CR ETX
```

### 3.5 TeraTerm 画面例

```
PING
ACK ret=0 fw=3.6.0 crc=8A3F21C7 vars=30

GET 3
ACK ret=0 id=3 name=oven_current_temp type=uint16 value=25 unit=degC

GET 3,7,15 compact
ACK ret=0 3=25 7=100 15=31

GET 99
NAK ret=2 id=99 reason=idx
```

`grep ACK` で成功のみ、`grep "ret=2"` で IDX エラーのみ抽出できる。

### 3.6 ターミナルでの入力方法

STX / ETX は制御文字のため、TeraTerm の通常入力では打てない。

| 方法 | 手順 |
|---|---|
| **TeraTerm マクロ**（推奨） | `tools/teraterm/statable.ttl` を同梱。ショートカットで自動付与 |
| HEX 送信モード | `02 47 45 54 20 33 0D 03` を貼り付け |
| SDK の `--ascii` モード | SDK が自動で STX/CR/ETX を付与 |

---

## 4. リターンコード（STATUS）

ASCII / バイナリ共通。

| 値 | 名前 | 意味 | ASCII `reason=` |
|:---:|---|---|---|
| `0` | OK | 成功 | — |
| `1` | PARSE | 構文エラー | `parse` |
| `2` | IDX | 変数 ID 範囲外 | `idx` |
| `3` | **予約**（旧 RO） | — | — |
| `4` | **予約**（旧 RANGE） | — | — |
| `5` | CMD | 未知のコマンド | `cmd` |
| `6` | **予約**（旧 NAME） | — | — |
| `7` | ARGS | 引数不足・過剰 | `args` |
| `8` | BUSY | 処理中（予約、v3.6.0 未使用） | `busy` |

`3` / `4` / `6` は将来の拡張用に番号を予約（歯抜けにしない）。

---

## 5. 変数レジストリ

### 5.1 ID の決定

変数 ID は **StaTable XML の変数宣言順**で 0 から連番。PC とデバイスが同じ XML から同じ順序を得る。

### 5.2 デバイス側レジストリ

```c
typedef struct {
    const void *ptr;   /* &g_ctx.data.<name> */
    uint8_t     size;  /* 1 / 2 / 4 */
} VarEntry_t;

const VarEntry_t g_var_registry[] = {
    { &g_ctx.data.g_system_tick,     4 },
    { &g_ctx.data.oven_current_temp, 2 },
    { &g_ctx.data.oven_target_temp,  2 },
    /* ... XML 宣言順 ... */
};
const uint8_t g_var_count = ARRAY_SIZE(g_var_registry);
```

- デバイスは名前・型・単位を持たない（フラッシュ節約）
- 書込み可否（`flags`）も持たない（書込みなし）

### 5.3 整合性検証（XML CRC32）

XML とファームの変数順不一致は誤読に直結するため、`PING` 応答の `crc=` で照合する。

- ビルド時：`codegen` が XML から CRC32 を計算し、生成ヘッダに埋め込む
  ```c
  #define COMM_MONITOR_XML_CRC32  0x8A3F21C7u
  #define COMM_MONITOR_VAR_COUNT  30u
  ```
- PC 側：起動時に XML から同じ CRC32 を計算し、`ping()` の `crc=` と照合
- 不一致なら **接続を拒否** し、「XML とファームウェアが一致しません」とエラー表示

### 5.4 型マッピング

| XML `type` | psblog `<type>` | VAL | ASCII `value=` |
|---|---|---|---|
| `uint8_t` / `uint16_t` / `uint32_t` | 同名 | ゼロ拡張 | 10 進 |
| `int8_t` / `int16_t` / `int32_t` | 同名 | 符号拡張 | 10 進 |
| `float` | `float32` | ビットパターン | `%.6g` |
| `bool` | `bool` | 0/1 | 0/1 |

`volatile` / `const` は無視し基本型に正規化。

---

## 6. 割り込み駆動アーキテクチャ

### 6.1 基本方針

- **ISR はリングバッファへの 1 バイト出し入れのみ**
- **メインループで解析・応答作成**
- 送信は TX リング + TXE 割込みで自動送出

### 6.2 リングバッファ（SPSC）

```c
static volatile uint8_t rx_buf[64], rx_head, rx_tail;
static volatile uint8_t tx_buf[64], tx_head, tx_tail;
```

### 6.3 ISR

```c
void USART2_IRQHandler(void)
{
    if (USART2->SR & USART_SR_RXNE) {
        uint8_t b = USART2->DR;
        uint8_t next = (rx_head + 1) & (RX_BUF_SIZE - 1);
        if (next != rx_tail) { rx_buf[rx_head] = b; rx_head = next; }
    }
    if (USART2->SR & USART_SR_TXE) {
        if (tx_tail != tx_head) {
            USART2->DR = tx_buf[tx_tail];
            tx_tail = (tx_tail + 1) & (TX_BUF_SIZE - 1);
        } else {
            USART2->CR1 &= ~USART_CR1_TXEIE;
        }
    }
}
```

### 6.4 メインループ

```c
void comm_monitor_poll(void)
{
    while (rx_available() > 0) {
        comm_monitor_on_rx_byte(rx_pop());
    }
}
```

### 6.5 ユーザーが手動実装する部分（STM32 HAL 例）

```c
comm_monitor_init();
HAL_UART_Receive_IT(&huart2, &rx_byte, 1);

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
    if (huart->Instance == USART2) {
        comm_monitor_on_rx_byte(rx_byte);
        HAL_UART_Receive_IT(&huart2, &rx_byte, 1);
    }
}

while (1) {
    comm_monitor_poll();
}
```

---

## 7. ホットプラグ耐性

| 機構 | 仕様 |
|---|---|
| **ステートレス** | セッション・ハンドシェイクなし。再接続後いきなり `PING` 可能 |
| **フレーム破棄** | CR 直後が ETX でない、または不正文字混入でフレーム破棄 → STX 待ちに戻る |
| **アイドルタイムアウト** | 部分受信フレームが 100 ms（`COMM_MONITOR_IDLE_MS`）受信途絶で自動クリア |
| **冪等性** | `PING` / `LIST` / `GET` / `HELP` はすべて冪等 |
| **再接続検出** | PC 側は `PING` 応答で生存確認。`crc=` で XML 整合性も同時検証 |
| **応答欠落時** | PC 側でタイムアウト + リトライ（既定 3 回） |

再接続後の最初のコマンドは必ず正常処理される。

---

## 8. コマンドテーブル管理

### 8.1 テーブル構造

```c
typedef struct {
    const char *args;
    char        resp_text[96];
} CmdContext_t;

typedef void (*CmdHandler_t)(CmdContext_t *ctx);

typedef struct {
    const char  *name;
    CmdHandler_t handler;
    const char  *help;
} CmdEntry_t;
```

### 8.2 組込みテーブル（生成コード）

```c
static const CmdEntry_t g_builtin_cmds[] = {
    { "PING", cmd_ping, "PING" },
    { "LIST", cmd_list, "LIST" },
    { "GET",  cmd_get,  "GET <id>[,<id>...] [compact]" },
    { "HELP", cmd_help, "HELP" },
};

/* ===== [[STABLE_USER_CODE_START:USER_COMMANDS]] ===== */
static const CmdEntry_t g_user_cmds[] = {
    /* 例:
    { "MYCMD", cmd_mycmd, "MYCMD <arg>" },
    */
};
/* ===== [[STABLE_USER_CODE_END:USER_COMMANDS]] ===== */
```

- ユーザーコマンドはマーカー間にエントリを足すだけで追加できる
- 再生成時もマーカー間は保持される
- `HELP` は組込み + ユーザーの両テーブルから自動生成

### 8.3 ディスパッチャ

```c
static void dispatch(char *line)
{
    char name[16]; const char *args;
    split_name_args(line, name, sizeof(name), &args);
    for (size_t i = 0; i < ARRAY_SIZE(g_builtin_cmds); i++) {
        if (strcasecmp(name, g_builtin_cmds[i].name) == 0) {
            CmdContext_t ctx = { .args = args };
            g_builtin_cmds[i].handler(&ctx);
            respond(ctx.resp_text);
            return;
        }
    }
    /* ユーザーテーブルも同様に走査 */
    nak(5, "cmd");
}
```

---

## 9. PC 側 SDK

### 9.1 優先順位

| 版 | 内容 |
|---|---|
| **v3.6.0** | Python SDK（`statable-monitor`） + psblog ロガー |
| **v3.6.1** | C# SDK（`StaTable.Monitor` NuGet） + F7/H7/G4 テンプレート |

### 9.2 Python SDK API

```python
from statable_monitor import StaTableMonitor

m = StaTableMonitor()
m.connect("COM3", baudrate=115200, xml_path="cooking_heater_controller.xml")
# 接続時に PING の crc= と XML の CRC32 を照合

vars_info = m.list_variables()
v = m.get("oven_current_temp")                       # → 25
vals = m.get_many(["oven_current_temp", "heater_top_duty"])

with m.create_logger("session.psblog", vars_info) as log:
    log.start()
    m.start_polling(["oven_current_temp", "oven_target_temp"], period_ms=200,
                    on_sample=log.write)
    m.stop_polling()
    log.stop()
```

### 9.3 ポーリング周期仕様

| 項目 | 値 |
|---|---|
| 制御主体 | **PC 側 SDK**（デバイスは周期概念を持たない） |
| 最小周期 | **100 ms**（`MIN_POLL_PERIOD_MS`） |
| 既定周期 | **200 ms** |
| 最大周期 | **60,000 ms** |
| 範囲外の扱い | SDK が `ValueError` を送出 |

帯域根拠：ASCII compact 応答（30 変数）≈ 180 B。100 ms 周期 = 10 Hz → 約 1.8 KB/s = 14.4 kbps。115200 bps に対し約 16% の使用率で余裕あり。

### 9.4 SDK 内部モジュール

| モジュール | 役割 |
|---|---|
| `connection.py` | シリアル接続、再接続、タイムアウト、フレーム送受信 |
| `registry.py` | XML パース、`IDX → VariableInfo` マップ |
| `polling.py` | PC 側周期制御、リトライ |
| `xml_mapper.py`（予定） | 応答 → XML 要素への変換 |
| `psblog_logger.py` | psblog/v1 ライター |

### 9.5 XML 写像ヘルパ

応答の key=value を XML 属性にそのまま写像する。

```python
def frame_to_xml(line: str, t_ms: int) -> str:
    parts = line.split()
    kind, status = parts[0], parts[1]
    kv = dict(p.split("=", 1) for p in parts[2:] if "=" in p)
    attrs = " ".join(f'{k}="{v}"' for k, v in kv.items())
    return f'<sample t="{t_ms}" kind="{kind}" status="{status}"><var {attrs}/></sample>'
```

---

## 10. psblog/v1 ログ出力

ログ整形は **すべて PC 側で行う**。デバイスは生値を返すだけ。

### 10.1 セクション生成

| セクション | 書込みタイミング |
|---|---|
| `[Header]` | `logger.start()` 時 |
| `[VarTable]` | `logger.start()` 時（`LIST` 応答 or XML から生成） |
| `[Data]` | `on_sample` コールバックごと |
| `[Footer]` | `logger.stop()` 時 |

### 10.2 Header の生成値

| キー | 値 |
|---|---|
| `@schema` | `psblog/v1` |
| `@captured_at` | `logger.start()` 時の PC 時刻（ISO 8601 with TZ） |
| `@source` | `uart:<portName>` |
| `@firmware` | `PING` 応答の `fw` から `StaTable v<ver>` に整形 |
| `@protocol` | `pstable-uart/v1` |
| `@baud` | 接続ボーレート |
| `@period_ms` | ポーリング周期（100 以上保証） |

### 10.3 VarTable の生成

```
@var oven_current_temp uint16_t degC Hardware "Current oven temperature"
```

### 10.4 Data 行の生成

```
@<t_ms> <name>=<value>
```

`t_ms` は `@captured_at` からの PC 受信時刻の経過ミリ秒。バッチ受信時は 1 行に複数 `key=value` を書いてよい（psblog 仕様 §8）。

### 10.5 破損・欠落への対処

| 状況 | SDK の動作 | ログへの影響 |
|---|---|---|
| タイムアウト（リトライ超過） | サンプルスキップ | `@dropped` に加算 |
| 数値パース失敗 | 該当値をスキップ | 該当トークンのみ欠落 |
| 未知変数 | スキップ | 書かない |
| NaN / Inf（float） | サンプルスキップ | 書かない |

### 10.6 ログローテーション

```python
LogOptions(max_file_size_bytes=10 * 1024 * 1024, rotate_suffix=".{index}")
```

10 MB でローテーション。Footer を書き、新ファイルに Header + VarTable を再出力。

---

## 11. 生成ファイル一覧

| ファイル | 種別 | 内容 |
|---|---|---|
| `statable_comm_monitor.h` | 生成 | 公開 API（`init` / `on_rx_byte` / `poll` / `set_tx`） |
| `statable_comm_monitor.c` | 生成 | 状態機械、ディスパッチャ、応答送出 |
| `statable_comm_commands.c` | 生成（ユーザー編集可） | 組込み + ユーザーコマンドテーブル（マーカー保持） |
| `statable_comm_registry.h` | 生成 | `VarEntry_t` 定義、`g_var_registry[]` 宣言 |
| `statable_comm_registry.c` | 生成 | レジストリ実体、`comm_registry_read` |
| `statable_comm_ring.h/.c` | 生成 | SPSC リングバッファ（RX/TX） |
| `statable_comm_config.h` | 生成 | バッファ長、タイムアウト、`XML_CRC32`、機能有効化マクロ |
| `main_demo.c` | Installer テンプレート | 手動フックのサンプル（STM32 HAL 版） |

再生成時は `[[STABLE_USER_CODE_START:*]]` / `END` マーカー間を保持。

---

## 12. 設定マクロ

| マクロ | 既定 | 説明 |
|---|---|---|
| `COMM_MONITOR_ENABLED` | 1 | 機能全体の有効化 |
| `COMM_MONITOR_ASCII_BODY_MAX` | 96 | ASCII 本文最大長 |
| `COMM_MONITOR_RX_RING_SIZE` | 64 | RX リング長（2 の冪） |
| `COMM_MONITOR_TX_RING_SIZE` | 64 | TX リング長（2 の冪） |
| `COMM_MONITOR_IDLE_MS` | 100 | 部分フレームクリアのアイドル時間 |
| `COMM_MONITOR_ACK_UNIT` | 1 | GET 応答に `unit=` を含める |
| `COMM_MONITOR_ACK_NAME` | 1 | GET 応答に `name=` を含める |
| `COMM_MONITOR_XML_CRC32` | （生成値） | XML 整合性検証用 |
| `COMM_MONITOR_VAR_COUNT` | （生成値） | 変数件数 |

---

## 13. テスト計画

| # | テスト | 内容 |
|---|---|---|
| T1 | `test_v3_6_0_comm_monitor_generator.py` | 変数モデル → レジストリ生成、CRC32 安定性、生成ファイル一式 |
| T2 | `test_v3_6_0_comm_monitor_ascii.py` | ホスト gcc + stdin/stdout で PING/LIST/GET/HELP |
| T3 | `test_v3_6_0_comm_monitor_hotplug.py` | 部分フレーム→タイムアウト→復帰、CR 直後 ETX 以外で破棄 |
| T4 | `test_v3_6_0_comm_monitor_table.py` | HELP 網羅性、ユーザーコマンド追加反映 |
| T5 | `test_v3_6_0_comm_monitor_safety.py` | IDX 範囲外、パース失敗、引数不足、SET 送信で CMD エラー |
| T6 | `test_v3_6_0_comm_monitor_response.py` | key=value パース、XML 写像 |
| T7 | `test_v3_6_0_psblog_format.py` | `.psblog` 出力のバイト単位検証（BOM なし・LF・セクション順序） |
| T8 | `test_v3_6_0_psblog_roundtrip.py` | 参照パーサで読込み、値一致 |
| T9 | `test_v3_6_0_sdk_python.py` | pyserial モックで接続・LIST・GET・ポーリング・ログ |
| T10 | E2E（QEMU） | UART 経由で PING→LIST→GET→ログ生成→参照パーサ |
| T11 | `test_readme_consistency.py` / `test_ci_registration.py` | 既存規約維持 |

CI 登録：`check.yml` に T1〜T9 を追加。T10 は既存 E2E ジョブに統合。

---

## 14. 実機なしでの評価戦略

| L | 対象 | 手段 | 実機要否 |
|:---:|---|---|:---:|
| L1 | C プロトコル層（単体） | ホスト gcc + stdin/stdout | 不要 |
| L2 | C プロトコル層（結合） | socat PTY / com0com | 不要 |
| L3 | Python SDK（単体） | pyserial モック + pytest | 不要 |
| L4 | SDK ↔ C 統合 | PTY 経由で実 C バイナリと往復 | 不要 |
| L5 | ARM バイナリ（QEMU） | QEMU netduinoplus2 + TCP シリアル | 不要 |
| L6 | psblog 出力 | 参照パーサ roundtrip | 不要 |

実機が必要なのは「実 UART のノイズ・タイミング・電気的特性」のみ。ロジックは L1〜L6 で検証可能。

---

## 15. リリース計画

| 版 | 内容 |
|---|---|
| **v3.6.0** | デバイス（ASCII、割り込み駆動、レジストリ、GET のみ） + Python SDK + psblog ロガー + TeraTerm マクロ |
| **v3.6.1** | C# SDK（`StaTable.Monitor` NuGet） + F7/H7/G4 テンプレート（Installer v0.1.2） |
| v3.7.0（候補） | バイナリモード、CRC 付きフレーム、配列アクセス、SDK asyncio 版 |

バージョン更新対象：`code/pyproject.toml` / `code/statable/__init__.py` / `code/codegen/__init__.py` → `3.6.0`。SDK は独立バージョン（`statable-monitor 0.1.0`）。

---

## 16. 確定事項サマリ

| 項目 | 確定内容 |
|---|---|
| モード | **ASCII のみ** |
| フレーミング | `STX + 本文 + CR + ETX` |
| コマンド | `PING` / `LIST` / `GET` / `HELP` |
| 書込み | **なし**（GET 専用） |
| CRC | なし |
| ポーリング | PC 側制御、最小 100 ms、既定 200 ms、最大 60,000 ms |
| デバイス | 完全受動（要求応答のみ、周期概念なし） |
| 割り込み | RX/TX ともリングバッファ + ISR、解析はメイン |
| ログ | PC 側で psblog/v1 に整形 |
| XML CRC32 照合 | 接続時に照合、不一致なら拒否 |
| ユーザーコマンド | マーカー間にエントリ追加で拡張可能 |
```


---

## 17. 実装ノート v3.6.0（追記）

本仕様書 §1-§16 は設計仕様です。以下は v3.6.0 実装時点での差分・補足です。

### 17.1 実装済み

| 項目 | 実装 | 備考 |
|---|---|---|
| ASCII フレーミング | OK | STX + body + CR + ETX |
| コマンド | OK | PING / LIST / GET / HELP |
| GET compact | OK | `ACK ret=0 3=25 7=100` |
| GET 厳格 parse | OK | `GET 1x` / `GET 0,` → NAK ret=1 |
| ホットプラグ復帰 | OK | STX reentry in RX_BODY / RX_CR |
| psblog/v1 writer | OK | `write_many()` バッチ形式 |
| Python SDK | OK | `statable-monitor` |
| PC 側 GUI | OK | `statable_monitor_gui` + EXE |
| PowerSimBuilder 連携 | OK | `.psblog` 直接読み込み |

### 17.2 v3.6.1 以降の TODO

| 項目 | 理由 |
|---|---|
| `statable_comm_commands.c` 生成 | §8 / §11 ユーザーコマンドテーブル（マーカー保持） |
| `COMM_MONITOR_IDLE_MS` 実装 | §7 アイドルタイムアウト（現状 STX reentry で復帰） |
| CRC 付きフレーム / バイナリモード | §1.3 スコープ外 |
| 配列アクセス | §1.3 スコープ外 |

### 17.3 実装上の注意

- `psblog_logger.py` は `@var` 行で description を常に `"..."` で出力（空でも `""`）。§10.3 準拠。
- `frame_to_xml()`（§9.5 サンプル）は compact 形式 `3=25` を `<var id="3" value="25"/>` として展開（複数 `<var>` 要素）。
- GUI の `Start Log` は即時 1 サンプル書き込み（QTimer は 1 interval 後に発火）。
- ARM リンクは `_sbrk` スタブ（`tools/arm_template/stub_main.c`）で newlib の `snprintf` 依存を解決。
