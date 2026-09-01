# StaTable Cコード生成モジュール 詳細仕様書（完全版）

## 1. モジュール概要

StaTableのデータモデルからC言語コードを自動生成するモジュール。

### 1.1 設計方針

- **辞書駆動設計**: すべての分岐を辞書構造で管理し、追加・改変を容易にする
- **拡張性**: 新しい型・ファイル・生成ルールの追加が辞書への項目追加のみで完了
- **単一責任**: 各生成関数が特定の要素のみを担当
- **共通ロジックの再利用**: 共通パターンを基底関数として抽出
- **GUI定義の完全反映**: ロール関数の引数指定など、GUIで定義された内容を忠実に反映

### 1.2 モジュール構成

```
statable/codegen/
├── __init__.py              # パッケージ初期化・公開API
├── type_mapper.py           # 型マッピング
├── naming_convention.py     # 命名規則
├── struct_generator.py      # 構造体生成
├── enum_generator.py        # 列挙型生成
├── variable_generator.py    # 変数・フラグ生成
├── transition_generator.py  # 状態遷移関数生成
├── role_function_generator.py # ロール関数生成
└── c_code_generator.py      # メイン生成クラス
```

---

## 2. 型マッピング仕様（type_mapper.py）

### 2.1 基本型マッピング辞書

```python
TYPE_MAPPING = {
    'int': 'int',
    'int8': 'int8_t',
    'int16': 'int16_t',
    'int32': 'int32_t',
    'int64': 'int64_t',
    'uint': 'unsigned int',
    'uint8': 'uint8_t',
    'uint16': 'uint16_t',
    'uint32': 'uint32_t',
    'uint64': 'uint64_t',
    'float': 'float',
    'double': 'double',
    'bool': 'bool',
    'char': 'char',
    'string': 'char*',
    'void': 'void',
}
```

### 2.2 型カテゴリ辞書

```python
TYPE_CATEGORIES = {
    'int': 'integer',
    'int8': 'integer',
    'int16': 'integer',
    'int32': 'integer',
    'int64': 'integer',
    'uint': 'integer',
    'uint8': 'integer',
    'uint16': 'integer',
    'uint32': 'integer',
    'uint64': 'integer',
    'float': 'float',
    'double': 'float',
    'bool': 'boolean',
    'char': 'character',
    'string': 'string',
    'void': 'void',
}
```

### 2.3 ヘッダファイル要件辞書

```python
HEADER_REQUIREMENTS = {
    'integer': '#include <stdint.h>',
    'boolean': '#include <stdbool.h>',
    'string': '#include <string.h>',
    'float': '#include <math.h>',
}
```

---

## 3. 命名規則仕様（naming_convention.py）

### 3.1 変換パターン辞書

```python
CONVERSION_PATTERNS = {
    'upper_snake': {
        'patterns': [
            (r'(.)([A-Z][a-z]+)', r'\1_\2'),
            (r'([a-z0-9])([A-Z])', r'\1_\2'),
        ],
        'transform': str.upper,
    },
    'lower_snake': {
        'patterns': [
            (r'(.)([A-Z][a-z]+)', r'\1_\2'),
            (r'([a-z0-9])([A-Z])', r'\1_\2'),
        ],
        'transform': str.lower,
    },
    'camel': {
        'split': r'[_-]',
        'first': str.lower,
        'rest': str.capitalize,
    },
    'pascal': {
        'split': r'[_-]',
        'first': str.capitalize,
        'rest': str.capitalize,
    },
}
```

### 3.2 識別子生成ルール辞書

```python
IDENTIFIER_RULES = {
    'variable': 'to_lower_snake',      # 変数名
    'function': 'to_pascal_case',      # 関数名
    'type': 'to_pascal_case',          # 型名
    'enum': 'to_upper_snake',          # 列挙値
    'macro': 'to_upper_snake',         # マクロ名
    'pointer': 'to_lower_snake',       # ポインタ変数
}
```

### 3.3 主要メソッド

| メソッド | 説明 | 例 |
|---------|------|-----|
| `to_upper_snake(name)` | 大文字スネークケース | `system_status` → `SYSTEM_STATUS` |
| `to_lower_snake(name)` | 小文字スネークケース | `SystemStatus` → `system_status` |
| `to_camel_case(name)` | キャメルケース | `system_status` → `systemStatus` |
| `to_pascal_case(name)` | パスカルケース | `system_status` → `SystemStatus` |
| `sanitize_identifier(name)` | 識別子サニタイズ | `1test` → `_1test` |
| `create_identifier(name, kind)` | 種類別識別子生成 | `create_identifier("sys", "type")` → `Sys` |
| `create_type_name(name)` | 型名生成 | `system_status` → `SystemStatus_t` |
| `create_enum_value(prefix, name)` | 列挙値生成 | `("STATE", "INIT")` → `STATE_INIT` |
| `create_function_name(module, action)` | 関数名生成 | `("StateMachine", "Process")` → `StateMachine_Process` |
| `create_variable_name(name)` | 変数名生成 | `battery_voltage` → `battery_voltage` |

---

## 4. 構造体生成仕様（struct_generator.py）

### 4.1 メンバ生成ルール辞書

```python
member_generators = {
    'bit_field': '_generate_bit_field_member',  # ビットフィールド
    'array': '_generate_array_member',          # 配列
    'normal': '_generate_normal_member',        # 通常変数
}
```

### 4.2 構造体タイプ別生成辞書

```python
struct_generators = {
    'custom_type': '_generate_custom_type_struct',    # ユーザー定義型
    'system_data': '_generate_system_data_struct',    # SystemData_t
    'event_flags': '_generate_event_flags_struct',    # EventFlags_t
    'system_context': '_generate_system_context_struct', # SystemContext_t
}
```

### 4.3 生成される構造体

#### ユーザー定義型
```c
/* システム状態管理構造体 */
typedef struct {
    bool power_on : 1;
    /* 電源ON状態 */
    uint8_t error_code;
    /* エラーコード */
} SystemStatus_t;
```

#### SystemData_t（グローバル変数）
```c
/* グローバル変数構造体 */
/* システム全体で共有する変数を管理 */
typedef struct {
    /* === Power === */
    /* バッテリー電圧 [mV] */
    uint16_t battery_voltage;
    
    /* === Timer === */
    /* システムタイマ [ms] */
    uint32_t system_tick;
} SystemData_t;
```

#### EventFlags_t（イベントフラグ）
```c
/* イベントフラグ構造体 */
/* イベント発生を示すフラグを管理 */
typedef struct {
    /* === System === */
    /* 電源ON要求 */
    uint8_t EVT_POWER_ON_REQ;
} EventFlags_t;
```

#### SystemContext_t
```c
/* システム全体構造体 */
/* グローバル変数とイベントフラグを統合管理 */
typedef struct {
    SystemData_t data;     /* グローバル変数 */
    EventFlags_t flags;    /* イベントフラグ */
} SystemContext_t;
```

---

## 5. 列挙型生成仕様（enum_generator.py）

### 5.1 列挙型設定辞書

```python
enum_configs = {
    'state': {
        'prefix': 'STATE',
        'type_name': 'STATE_t',
        'max_name': 'STATE_MAX',
        'description': '状態遷移の状態を表す列挙型',
    },
    'event': {
        'prefix': 'EVENT',
        'type_name': 'EVENT_t',
        'max_name': 'EVENT_MAX',
        'description': '状態遷移を発生させるイベントの列挙型',
    },
    'flag': {
        'prefix': 'FLAG',
        'type_name': 'FLAG_t',
        'max_name': 'FLAG_MAX',
        'description': 'イベントフラグの識別子を表す列挙型',
    },
}
```

### 5.2 生成される列挙型

```c
/* 状態定義 */
typedef enum {
    STATE_INIT = 0,    /* 初期状態 */
    STATE_IDLE,        /* アイドル状態 */
    STATE_RUNNING,     /* 実行状態 */
    
    STATE_MAX           /* 状態数（システム用） */
} STATE_t;

/* イベント定義 */
typedef enum {
    EVENT_POWER_ON = 0,    /* 電源ONイベント */
    EVENT_START,           /* 開始イベント */
    
    EVENT_MAX              /* イベント数（システム用） */
} EVENT_t;

/* イベントフラグ定義 */
typedef enum {
    FLAG_EVT_POWER_ON_REQ = 0,    /* 電源ON要求 */
    
    FLAG_MAX                      /* フラグ数（システム用） */
} FLAG_t;
```

---

## 6. 変数・フラグ生成仕様（variable_generator.py）

### 6.1 変数生成ルール

| 変数タイプ | 生成パターン | 例 |
|-----------|-------------|-----|
| グローバル変数 | `ctx->data.{変数名}` | `ctx->data.battery_voltage` |
| イベントフラグ | `ctx->flags.{フラグ名}` | `ctx->flags.EVT_POWER_ON_REQ` |
| ローカル変数 | `{変数名}` | `battery_voltage` |
| ポインタ変数 | `*{変数名}` | `*battery_voltage` |

### 6.2 変数アクセスマクロ生成

```c
/* 変数アクセスマクロ */
#define DATA_BATTERY_VOLTAGE(ctx)    ((ctx)->data.battery_voltage)
#define FLAG_EVT_POWER_ON_REQ(ctx)   ((ctx)->flags.EVT_POWER_ON_REQ)
```

### 6.3 初期化関数生成

```c
/**
 * @brief  システムコンテキスト初期化
 * @param  ctx  システムコンテキストポインタ
 */
void SystemContext_Init(SystemContext_t *ctx)
{
    if (ctx == NULL) {
        return;
    }
    
    /* グローバル変数の初期化 */
    ctx->data.battery_voltage = 0;
    ctx->data.system_tick = 0;
    
    /* イベントフラグの初期化 */
    ctx->flags.EVT_POWER_ON_REQ = 0;
    ctx->flags.EVT_START_REQ = 0;
}
```

---

## 7. 状態遷移関数生成仕様（transition_generator.py）

### 7.1 状態遷移関数シグネチャ

```c
/**
 * @brief  状態遷移処理
 * @param  current_state  現在の状態
 * @param  event          発生したイベント
 * @param  ctx            システムコンテキストポインタ
 * @return 遷移後の状態
 */
STATE_t StateMachine_Process(
    STATE_t current_state,
    EVENT_t event,
    SystemContext_t *ctx
);
```

### 7.2 状態遷移テーブル生成

#### テーブル駆動方式
```c
/* 状態遷移テーブル */
typedef struct {
    STATE_t next_state;
    bool (*condition)(SystemContext_t *ctx);
    void (*action)(SystemContext_t *ctx);
} TransitionCell_t;

static const TransitionCell_t transition_matrix[STATE_MAX][EVENT_MAX] = {
    /* STATE_INIT */
    {
        /* EVENT_POWER_ON */ { STATE_IDLE, NULL, Action_PowerOn },
        /* EVENT_START    */ { STATE_INIT, NULL, NULL },
        /* EVENT_STOP     */ { STATE_INIT, NULL, NULL },
    },
    /* STATE_IDLE */
    {
        /* EVENT_POWER_ON */ { STATE_IDLE, NULL, NULL },
        /* EVENT_START    */ { STATE_RUNNING, Condition_StartOk, Action_Start },
        /* EVENT_STOP     */ { STATE_IDLE, NULL, NULL },
    },
    /* STATE_RUNNING */
    {
        /* EVENT_POWER_ON */ { STATE_RUNNING, NULL, NULL },
        /* EVENT_START    */ { STATE_RUNNING, NULL, NULL },
        /* EVENT_STOP     */ { STATE_IDLE, NULL, Action_Stop },
    },
};
```

#### switch文方式
```c
STATE_t StateMachine_Process(
    STATE_t current_state,
    EVENT_t event,
    SystemContext_t *ctx
)
{
    STATE_t next_state = current_state;
    
    switch (current_state) {
        case STATE_INIT:
            switch (event) {
                case EVENT_POWER_ON:
                    Action_PowerOn(ctx);
                    next_state = STATE_IDLE;
                    break;
                default:
                    break;
            }
            break;
            
        case STATE_IDLE:
            switch (event) {
                case EVENT_START:
                    if (Condition_StartOk(ctx)) {
                        Action_Start(ctx);
                        next_state = STATE_RUNNING;
                    }
                    break;
                default:
                    break;
            }
            break;
            
        default:
            break;
    }
    
    return next_state;
}
```

### 7.3 状態遷移関数の実装パターン

```c
STATE_t StateMachine_Process(
    STATE_t current_state,
    EVENT_t event,
    SystemContext_t *ctx
)
{
    STATE_t next_state = current_state;
    
    /* NULLチェック */
    if (ctx == NULL) {
        return current_state;
    }
    
    /* 範囲チェック */
    if (current_state >= STATE_MAX || event >= EVENT_MAX) {
        return current_state;
    }
    
    /* 遷移テーブルから該当セルを取得 */
    const TransitionCell_t *cell = &transition_matrix[current_state][event];
    
    /* 条件チェック */
    if (cell->condition != NULL) {
        if (!cell->condition(ctx)) {
            return current_state;  /* 条件不成立 */
        }
    }
    
    /* アクション実行 */
    if (cell->action != NULL) {
        cell->action(ctx);
    }
    
    /* 状態遷移 */
    if (cell->next_state != STATE_MAX) {
        next_state = cell->next_state;
    }
    
    return next_state;
}
```

---

## 8. ロール関数生成仕様（role_function_generator.py）

### 8.1 ロール関数データモデル

```python
class RoleFunction:
    def __init__(self, name, description="", return_type="void",
                 arg1_type="", arg1_name="", 
                 arg2_type="", arg2_name="",
                 title=""):
        self.name = name                    # 関数名
        self.description = description       # 説明
        self.return_type = return_type      # 戻り値型
        self.arg1_type = arg1_type          # 引数1の型
        self.arg1_name = arg1_name          # 引数1の名前
        self.arg2_type = arg2_type          # 引数2の型
        self.arg2_name = arg2_name          # 引数2の名前
        self.title = title                  # タイトル
```

### 8.2 ロール関数シグネチャ生成ルール

```python
# 引数パターン辞書
arg_patterns = {
    0: '_generate_no_args',      # 引数なし
    1: '_generate_one_arg',      # 引数1つ
    2: '_generate_two_args',     # 引数2つ
}
```

### 8.3 生成されるロール関数の例

#### 引数なしの場合
```c
/**
 * @brief  ロール関数: 電源ON処理
 * @param  current_state  現在の状態ポインタ
 * @param  ctx            システムコンテキストポインタ
 * @return 実行結果（0: 成功, 0以外: エラー）
 */
int RoleFunc_PowerOn(
    STATE_t *current_state,
    SystemContext_t *ctx
);
```

#### 引数1つの場合
```c
/**
 * @brief  ロール関数: データ送信
 * @param  current_state  現在の状態ポインタ
 * @param  ctx            システムコンテキストポインタ
 * @param  data           送信データ
 * @return 実行結果（0: 成功, 0以外: エラー）
 */
int RoleFunc_SendData(
    STATE_t *current_state,
    SystemContext_t *ctx,
    uint8_t *data
);
```

#### 引数2つの場合
```c
/**
 * @brief  ロール関数: データ処理
 * @param  current_state  現在の状態ポインタ
 * @param  ctx            システムコンテキストポインタ
 * @param  data           データポインタ
 * @param  len            データ長
 * @return 実行結果（0: 成功, 0以外: エラー）
 */
int RoleFunc_ProcessData(
    STATE_t *current_state,
    SystemContext_t *ctx,
    uint8_t *data,
    uint16_t len
);
```

### 8.4 ロール関数の空実装

```c
int RoleFunc_ProcessData(
    STATE_t *current_state,
    SystemContext_t *ctx,
    uint8_t *data,
    uint16_t len
)
{
    /* TODO: 実装を記述すること */
    (void)current_state;  /* 未使用引数の警告抑制 */
    (void)ctx;            /* 未使用引数の警告抑制 */
    (void)data;           /* 未使用引数の警告抑制 */
    (void)len;            /* 未使用引数の警告抑制 */
    
    return 0;  /* 成功を返す */
}
```

### 8.5 戻り値型のデフォルト値辞書

```python
default_return_values = {
    'void': '',
    'bool': 'false',
    'int': '0',
    'int8': '0',
    'int16': '0',
    'int32': '0',
    'int64': '0',
    'uint': '0',
    'uint8': '0',
    'uint16': '0',
    'uint32': '0',
    'uint64': '0',
    'float': '0.0f',
    'double': '0.0',
}
```

### 8.6 ロール関数呼び出しコード

```c
/* 状態遷移内でのロール関数呼び出し */
if (RoleFunc_CheckCondition(current_state, ctx)) {
    RoleFunc_PerformAction(current_state, ctx);
    *current_state = STATE_RUNNING;
}

/* 引数付きロール関数呼び出し */
uint8_t data[64];
RoleFunc_ProcessData(current_state, ctx, data, sizeof(data));
```

---

## 9. 状態遷移ロジック生成仕様

### 9.1 遷移候補の優先順位処理

```c
/* 優先順位付き遷移処理 */
STATE_t StateMachine_Process(
    STATE_t current_state,
    EVENT_t event,
    SystemContext_t *ctx
)
{
    STATE_t next_state = current_state;
    
    /* 優先順位1: 条件付き遷移 */
    if (Condition_HighPriority(ctx)) {
        Action_HighPriority(ctx);
        next_state = STATE_HIGH_PRIORITY;
    }
    /* 優先順位2: 通常遷移 */
    else if (Condition_NormalPriority(ctx)) {
        Action_NormalPriority(ctx);
        next_state = STATE_NORMAL_PRIORITY;
    }
    /* 優先順位3: デフォルト遷移 */
    else {
        Action_Default(ctx);
        next_state = STATE_DEFAULT;
    }
    
    return next_state;
}
```

### 9.2 遷移アクション・条件関数

```c
/* 遷移アクション関数 */
void Action_PowerOn(SystemContext_t *ctx)
{
    /* アクション処理 */
    ctx->flags.EVT_POWER_ON_REQ = 1;
}

/* 遷移条件関数 */
bool Condition_StartOk(SystemContext_t *ctx)
{
    /* 条件チェック */
    return (ctx->data.battery_voltage > 3000);
}
```

---

## 10. メイン生成クラス仕様（c_code_generator.py）

### 10.1 ファイル生成設定辞書

```python
file_generators = {
    'statable_types.h': {
        'method': '_generate_types_header',
        'description': '状態遷移システムの型定義',
        'guard_name': 'STATABLE_TYPES_H',
    },
    'statable_transitions.h': {
        'method': '_generate_transitions_header',
        'description': '状態遷移関数宣言',
        'guard_name': 'STATABLE_TRANSITIONS_H',
    },
    'statable_transitions.c': {
        'method': '_generate_transitions_source',
        'description': '状態遷移ロジック',
        'guard_name': None,
    },
    'statable_role_functions.h': {
        'method': '_generate_role_functions_header',
        'description': 'ロール関数宣言',
        'guard_name': 'STATABLE_ROLE_FUNCTIONS_H',
    },
    'statable_role_functions.c': {
        'method': '_generate_role_functions_source',
        'description': 'ロール関数実装',
        'guard_name': None,
    },
    'statable_init.c': {
        'method': '_generate_init_source',
        'description': '初期化処理',
        'guard_name': None,
    },
}
```

### 10.2 生成されるファイル一覧

| ファイル名 | 内容 | 説明 |
|-----------|------|------|
| `statable_types.h` | 型定義 | 列挙型・構造体・マクロの定義 |
| `statable_transitions.h` | 遷移関数宣言 | 状態遷移関数のプロトタイプ |
| `statable_transitions.c` | 遷移関数実装 | 状態遷移ロジック |
| `statable_role_functions.h` | ロール関数宣言 | ロール関数のプロトタイプ |
| `statable_role_functions.c` | ロール関数実装 | ロール関数の空実装 |
| `statable_init.c` | 初期化処理 | システム初期化関数 |

---

## 11. 生成される全ファイル構成

### 11.1 statable_types.h

```c
/**
 * @file    statable_types.h
 * @brief   状態遷移システムの型定義
 * @note    StaTableにより自動生成されたコード
 * @date    2025-01-15 10:30:00
 */

#ifndef STATABLE_TYPES_H
#define STATABLE_TYPES_H

/*==============================================================
 *  インクルードファイル
 *============================================================*/
#include <stdint.h>
#include <stdbool.h>

/*==============================================================
 *  型定義
 *============================================================*/

/* 状態定義 */
typedef enum {
    STATE_INIT = 0,
    STATE_IDLE,
    STATE_RUNNING,
    STATE_MAX
} STATE_t;

/* イベント定義 */
typedef enum {
    EVENT_POWER_ON = 0,
    EVENT_START,
    EVENT_STOP,
    EVENT_MAX
} EVENT_t;

/* イベントフラグ定義 */
typedef enum {
    FLAG_EVT_POWER_ON_REQ = 0,
    FLAG_EVT_START_REQ,
    FLAG_MAX
} FLAG_t;

/* ユーザー定義型 */
typedef struct {
    bool power_on : 1;
    uint8_t error_code;
} SystemStatus_t;

/* システム構造体 */
typedef struct {
    uint16_t battery_voltage;
    uint32_t system_tick;
} SystemData_t;

typedef struct {
    uint8_t EVT_POWER_ON_REQ;
    uint8_t EVT_START_REQ;
} EventFlags_t;

typedef struct {
    SystemData_t data;
    EventFlags_t flags;
} SystemContext_t;

/* 変数アクセスマクロ */
#define DATA_BATTERY_VOLTAGE(ctx)    ((ctx)->data.battery_voltage)
#define DATA_SYSTEM_TICK(ctx)        ((ctx)->data.system_tick)
#define FLAG_EVT_POWER_ON_REQ(ctx)   ((ctx)->flags.EVT_POWER_ON_REQ)
#define FLAG_EVT_START_REQ(ctx)      ((ctx)->flags.EVT_START_REQ)

#endif /* STATABLE_TYPES_H */
```

### 11.2 statable_transitions.h

```c
/**
 * @file    statable_transitions.h
 * @brief   状態遷移関数宣言
 * @note    StaTableにより自動生成されたコード
 */

#ifndef STATABLE_TRANSITIONS_H
#define STATABLE_TRANSITIONS_H

#include "statable_types.h"

/*==============================================================
 *  関数宣言
 *============================================================*/

/**
 * @brief  状態遷移処理
 * @param  current_state  現在の状態
 * @param  event          発生したイベント
 * @param  ctx            システムコンテキストポインタ
 * @return 遷移後の状態
 */
STATE_t StateMachine_Process(
    STATE_t current_state,
    EVENT_t event,
    SystemContext_t *ctx
);

#endif /* STATABLE_TRANSITIONS_H */
```

### 11.3 statable_transitions.c

```c
/**
 * @file    statable_transitions.c
 * @brief   状態遷移ロジック
 * @note    StaTableにより自動生成されたコード
 */

#include "statable_transitions.h"
#include "statable_role_functions.h"

/*==============================================================
 *  状態遷移テーブル
 *============================================================*/

typedef struct {
    STATE_t next_state;
    bool (*condition)(SystemContext_t *ctx);
    void (*action)(SystemContext_t *ctx);
} TransitionCell_t;

static const TransitionCell_t transition_matrix[STATE_MAX][EVENT_MAX] = {
    /* STATE_INIT */
    {
        { STATE_IDLE, NULL, Action_PowerOn },
        { STATE_INIT, NULL, NULL },
        { STATE_INIT, NULL, NULL },
    },
    /* STATE_IDLE */
    {
        { STATE_IDLE, NULL, NULL },
        { STATE_RUNNING, Condition_StartOk, Action_Start },
        { STATE_IDLE, NULL, NULL },
    },
    /* STATE_RUNNING */
    {
        { STATE_RUNNING, NULL, NULL },
        { STATE_RUNNING, NULL, NULL },
        { STATE_IDLE, NULL, Action_Stop },
    },
};

/*==============================================================
 *  状態遷移関数
 *============================================================*/

STATE_t StateMachine_Process(
    STATE_t current_state,
    EVENT_t event,
    SystemContext_t *ctx
)
{
    STATE_t next_state = current_state;
    
    if (ctx == NULL) {
        return current_state;
    }
    
    if (current_state >= STATE_MAX || event >= EVENT_MAX) {
        return current_state;
    }
    
    const TransitionCell_t *cell = &transition_matrix[current_state][event];
    
    /* 条件チェック */
    if (cell->condition != NULL) {
        if (!cell->condition(ctx)) {
            return current_state;
        }
    }
    
    /* アクション実行 */
    if (cell->action != NULL) {
        cell->action(ctx);
    }
    
    /* 状態遷移 */
    if (cell->next_state != STATE_MAX) {
        next_state = cell->next_state;
    }
    
    return next_state;
}
```

### 11.4 statable_role_functions.h

```c
/**
 * @file    statable_role_functions.h
 * @brief   ロール関数宣言
 * @note    StaTableにより自動生成されたコード
 */

#ifndef STATABLE_ROLE_FUNCTIONS_H
#define STATABLE_ROLE_FUNCTIONS_H

#include "statable_types.h"

/*==============================================================
 *  ロール関数宣言
 *============================================================*/

/**
 * @brief  ロール関数: 電源ON処理
 * @param  current_state  現在の状態ポインタ
 * @param  ctx            システムコンテキストポインタ
 * @return 実行結果（0: 成功, 0以外: エラー）
 */
int RoleFunc_PowerOn(
    STATE_t *current_state,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: データ処理
 * @param  current_state  現在の状態ポインタ
 * @param  ctx            システムコンテキストポインタ
 * @param  data           データポインタ
 * @param  len            データ長
 * @return 実行結果（0: 成功, 0以外: エラー）
 */
int RoleFunc_ProcessData(
    STATE_t *current_state,
    SystemContext_t *ctx,
    uint8_t *data,
    uint16_t len
);

#endif /* STATABLE_ROLE_FUNCTIONS_H */
```

### 11.5 statable_role_functions.c

```c
/**
 * @file    statable_role_functions.c
 * @brief   ロール関数実装
 * @note    StaTableにより自動生成されたコード
 *          - 各関数は空実装
 *          - 実装者はTODO部分に処理を記述すること
 */

#include "statable_role_functions.h"

/*==============================================================
 *  ロール関数実装
 *============================================================*/

int RoleFunc_PowerOn(
    STATE_t *current_state,
    SystemContext_t *ctx
)
{
    /* TODO: 実装を記述すること */
    (void)current_state;
    (void)ctx;
    
    return 0;
}

int RoleFunc_ProcessData(
    STATE_t *current_state,
    SystemContext_t *ctx,
    uint8_t *data,
    uint16_t len
)
{
    /* TODO: 実装を記述すること */
    (void)current_state;
    (void)ctx;
    (void)data;
    (void)len;
    
    return 0;
}
```

### 11.6 statable_init.c

```c
/**
 * @file    statable_init.c
 * @brief   初期化処理
 * @note    StaTableにより自動生成されたコード
 */

#include "statable_types.h"

/*==============================================================
 *  初期化関数
 *============================================================*/

void SystemContext_Init(SystemContext_t *ctx)
{
    if (ctx == NULL) {
        return;
    }
    
    /* グローバル変数の初期化 */
    ctx->data.battery_voltage = 0;
    ctx->data.system_tick = 0;
    
    /* イベントフラグの初期化 */
    ctx->flags.EVT_POWER_ON_REQ = 0;
    ctx->flags.EVT_START_REQ = 0;
}
```

---

## 12. 拡張方法

### 12.1 新しい型マッピングの追加

```python
# type_mapper.py の TYPE_MAPPING に追加
TYPE_MAPPING = {
    'uint128': 'unsigned __int128',
}
```

### 12.2 新しい列挙型の追加

```python
# enum_generator.py の enum_configs に追加
enum_configs = {
    'priority': {
        'prefix': 'PRIORITY',
        'type_name': 'PRIORITY_t',
        'max_name': 'PRIORITY_MAX',
        'description': '優先度を表す列挙型',
    },
}
```

### 12.3 新しいファイル生成の追加

```python
# c_code_generator.py の file_generators に追加
file_generators = {
    'statable_config.c': {
        'method': '_generate_config_source',
        'description': '設定値の定義',
        'guard_name': None,
    },
}
```

### 12.4 新しい変数タイプの追加

```python
# variable_generator.py の variable_generators に追加
variable_generators = {
    'timer': '_generate_timer_variable',
    'queue': '_generate_queue_variable',
}
```

### 12.5 新しい引数パターンの追加

```python
# role_function_generator.py の arg_patterns に追加
arg_patterns = {
    3: '_generate_three_args',  # 引数3つ
}
```

---

## 13. 制約事項

1. **ビットフィールドと配列の併用不可**: 1つのメンバに両方を指定しない
2. **配列サイズは正の整数**: `array_size` は0以上（0は配列なし）
3. **ビット幅は正の整数**: `bit_width` は0以上（0はビットフィールドなし）
4. **識別子の一意性**: サニタイズ後に重複しないよう注意
5. **予約語の回避**: C言語の予約語は自動的に`_`を付加
6. **NULLポインタチェック**: すべての公開関数でNULLチェックを行う
7. **未使用引数の警告抑制**: 空実装では`(void)`キャストを使用
8. **状態遷移テーブルの境界チェック**: 配列アクセス前に範囲チェックを行う
9. **ロール関数の引数**: 最大2つまでの引数をサポート
10. **ポインタ経由アクセス**: すべての関数にポインタ経由でアクセスできる引数を追加

---

## 14. テスト方針

### 14.1 ユニットテスト
- 型マッピングの正確性
- 命名規則の一貫性
- 構造体生成の正確性
- 列挙型生成の正確性
- 変数アクセスマクロの正確性
- 状態遷移テーブルの正確性
- ロール関数のシグネチャ正確性
- ロール関数の引数生成の正確性

### 14.2 統合テスト
- 全ファイル生成の整合性
- 生成コードのC言語としての妥当性
- コンパイル確認
- リンク確認

### 14.3 実行テスト
- 状態遷移の正確性
- 条件分岐の正確性
- アクション実行の正確性
- 初期化処理の正確性
- ロール関数呼び出しの正確性

---
