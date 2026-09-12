# StaTable コード生成モジュール 詳細仕様書

対象: `code/codegen/` 配下および関連 GUI モジュール  
版: 1.0（2026-09-12 時点のソースコードに基づく）  
テスト仕様は対象外。

---

## 目次

1. [概要](#1-概要)
2. [モジュール構成と責務](#2-モジュール構成と責務)
3. [データ仕様](#3-データ仕様)
4. [API 仕様](#4-api-仕様)
5. [設定仕様](#5-設定仕様)
6. [処理フロー](#6-処理フロー)
7. [マーカー仕様](#7-マーカー仕様)
8. [命名規則](#8-命名規則)
9. [生成ファイル仕様](#9-生成ファイル仕様)
10. [エラー・警告仕様](#10-エラー警告仕様)
11. [GUI 連携仕様](#11-gui-連携仕様)
12. [既知の制約・未実装項目](#12-既知の制約未実装項目)
13. [付録: 引継ぎ事項（タスク B）](#13-付録-引継ぎ事項タスク-b)

---

## 1. 概要

### 1.1 目的

StaTable の状態遷移モデル（`StateMachine` + `GlobalDefinitions`）から C 言語コード（全 11 ファイル）を生成する。ユーザー編集領域を保持するマージ機構、設定による生成方式切替、層（layer）ごとの多層ステートマシン対応を含む。

### 1.2 スコープ

| 対象 | 内容 |
|------|------|
| 対象 | `codegen/` 全モジュール + GUI 側の呼び出し |
| 対象外 | テストコード、XML I/O 詳細、状態遷移表 GUI |

### 1.3 用語

| 用語 | 定義 |
|------|------|
| 層（layer） | タブ名で識別される状態機械グループ。命名プレフィックスに使われる |
| セル | (state, event) の組。遷移関数の最小単位 |
| セル関数 | 1 セル分の遷移を処理する `static` 関数 |
| ロール関数 | 遷移時・条件判定時に呼ばれる `RoleFunc_*` 関数 |
| マーカー | ユーザーコード領域を示すコメント |
| 遷移テーブル | セル関数ポインタの 2 次元配列 |
| call_sites | ロール関数ごとの呼び出し元セル一覧（transition_id 用） |
| transition_id | call_sites 内のインデックス。0xFFFF = 未一致 |

---

## 2. モジュール構成と責務

| モジュール | 責務 |
|-----------|------|
| `c_code_generator.py` | 生成の統括。ステップテーブル・ディスパッチ・保存 |
| `code_merger.py` | 生成コードと既存コードのマージ |
| `config.py` | 設定 dataclass と ConfigManager |
| `transition_generator.py` | セル関数・遷移テーブル・Process 関数生成 |
| `role_function_generator.py` | ロール関数宣言/実装・call_sites・Transition_GetId |
| `struct_generator.py` | 構造体（SystemData / EventFlags / SystemContext / TransitionContext） |
| `enum_generator.py` | 列挙型（STATE / EVENT / FLAG） |
| `code_templates.py` | 固定文字列・テンプレート・OSAL テンプレート |
| `type_mapper.py` / `naming_convention.py` | 型変換・命名変換 |
| `variable_generator.py` 他 | 変数マクロ・初期化関数・イベントキュー・割り込み・タイマ・OSAL |
| `code_generation_dialog.py` | 生成 GUI・WarningCollector |
| `code_generation_settings_dialog.py` | 設定 GUI |

---

## 3. データ仕様

### 3.1 `CodeGenerationConfig`（`config.py`）

全フィールドと既定値。

| フィールド | 型 | 既定値 | 許容値 / 備考 |
|-----------|---|-------|--------------|
| `generation_style` | str | `"table_driven"` | `table_driven` / `switch_case`（後者は未実装→フォールバック） |
| `table_type` | str | `"array"` | `array` / `switch` / `dictionary`（後 2 者未実装→フォールバック） |
| `os_type` | str | `"non_rtos"` | `non_rtos` / `freertos` / `threadx` |
| `naming_prefix` | str | `""` | 任意 |
| `state_prefix` | str | `"STATE"` | 任意 |
| `event_prefix` | str | `"EVENT"` | 任意 |
| `flag_prefix` | str | `"FLAG"` | 任意 |
| `enable_debug_logs` | bool | `True` | – |
| `enable_info_logs` | bool | `True` | – |
| `enable_error_logs` | bool | `True` | – |
| `enable_comments` | bool | `True` | – |
| `enable_doxygen` | bool | `True` | – |
| `enable_user_markers` | bool | `True` | – |
| `output_directory` | str | `""` | 空なら保存不可 |
| `save_with_merge` | bool | `True` | – |
| `project_name` | str | `"MyProject"` | 生成ファイル名に使用 |
| `folder_structure` | str | `"by_type"` | `flat` / `by_type` / `by_layer`（**未実装**） |
| `include_dir_name` | str | `"include"` | – |
| `source_dir_name` | str | `"src"` | – |
| `common_dir_name` | str | `"common"` | – |
| `project_dir_name` | str | `"project"` | – |
| `generate_super_include` | bool | `True` | 未実装 |
| `super_include_file` | str | `"statable_all.h"` | 未実装 |
| `super_include_dir` | str | `"common"` | 未実装 |
| `external_includes` | List[str] | `[]` | 未実装 |
| `external_includes_in_super` | bool | `True` | 未実装 |
| `external_includes_in_role` | bool | `True` | 未実装 |
| `external_includes_in_transitions` | bool | `False` | 未実装 |
| `external_includes_in_common` | bool | `False` | 未実装 |
| `max_consecutive_pending_events` | int | `16` | 保留イベント連続処理上限 |

**メソッド**
- `to_dict() -> Dict` — 全フィールドを dict 化
- `from_dict(data: Dict) -> CodeGenerationConfig` — 未知キーは無視（`__dataclass_fields__` でフィルタ）

### 3.2 `ConfigManager`

| メソッド | 説明 |
|---------|------|
| `get_config() -> CodeGenerationConfig` | 現在の設定 |
| `set_config(config)` | 設定を置換 |
| `update(**kwargs)` | `hasattr` チェック後に `setattr`。未知キーは無視 |
| `reset()` | 既定値に戻す |
| `get_available_styles() -> Dict[str,str]` | `table_driven` / `switch_case` |
| `get_available_table_types() -> Dict[str,str]` | `array` / `switch` / `dictionary` |
| `get_available_os_types() -> Dict[str,str]` | `non_rtos` / `freertos` / `threadx` |
| `get_available_folder_structures() -> Dict[str,str]` | `flat` / `by_layer` / `by_type` |

### 3.3 生成ファイルメタ（`CCodeGenerator.file_generators`）

| ファイル名 | description | guard_name |
|-----------|-------------|-----------|
| `statable_types.h` | 状態遷移システムの型定義 | `STATABLE_TYPES_H` |
| `statable_transitions.h` | 状態遷移関数宣言 | `STATABLE_TRANSITIONS_H` |
| `statable_transitions.c` | 状態遷移ロジック | `None` |
| `statable_role_functions.h` | ロール関数宣言 | `STATABLE_ROLE_FUNCTIONS_H` |
| `statable_role_functions.c` | ロール関数実装 | `None` |
| `statable_init.c` | 初期化処理 | `None` |
| `statable_event_queue.c` | イベントキュー実装 | `None` |
| `statable_interrupt.c` | 割り込み処理 ISR | `None` |
| `statable_timer.c` | タイマ処理 | `None` |
| `osal.h` | OSAL ヘッダ | `OSAL_H` |
| `osal.c` | OSAL ソース | `None` |

### 3.4 インクルード定義（`include_headers`）

| キー | 内容 |
|------|------|
| `types` | `<stdint.h>` `<stdbool.h>` `<string.h>` |
| `transitions_h` | `"statable_types.h"` |
| `transitions_c` | `"statable_transitions.h"` `"statable_role_functions.h"` |
| `role_functions_h` | `"statable_types.h"` |
| `role_functions_c` | `"statable_role_functions.h"` |
| `init_c` / `event_queue_c` / `interrupt_c` / `timer_c` | `"statable_types.h"` |

### 3.5 `RoleFuncCallSite`

```python
class RoleFuncCallSite:
    __slots__ = ('func_name', 'kind', 'from_state', 'event', 'target')
```

- `kind`: `"condition"` / `"pre_action"` / `"else_action"`
- `key()`: `(from_state, event)` のタプル

---

## 4. API 仕様

### 4.1 `CCodeGenerator`

#### コンストラクタ

```python
def __init__(self, config: Optional[CodeGenerationConfig] = None)
```

- `config` 未指定時は `ConfigManager()` の既定値を使用
- `generation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")`
- `_current_role_function_library: Optional = None`（`generate_all` 中のみ有効）

#### 設定操作

| メソッド | 戻り | 説明 |
|---------|------|------|
| `get_config()` | `CodeGenerationConfig` | 現在の設定 |
| `set_config(config)` | – | ConfigManager 経由で置換 |
| `update_config(**kwargs)` | – | 部分更新 |
| `reset_config()` | – | リセット |

#### 生成 API

```python
def generate_all(
    self,
    state_machine: StateMachine,
    global_defs: GlobalDefinitions,
    role_function_library: Optional = None,
) -> Dict[str, str]
```

- 戻り: `{ファイル名: 内容文字列}`（順序は `file_generators` の定義順）
- `role_function_library` 指定時、`state_machine.role_functions` とマージ（**衝突時は state_machine 優先**）
- `_current_role_function_library` は `try/finally` で復元

```python
def generate_file(self, filename, state_machine,
                  global_defs, role_function_library=None) -> str
```

- 未知名は `ValueError(f"Unknown file: {filename}")`

#### 保存 API

```python
def save_generated_code(self, generated_files: Dict[str,str],
                        output_dir: str) -> List[str]
```

- `os.makedirs(output_dir, exist_ok=True)`
- 全ファイルを `output_dir/filename` に UTF-8 書込
- 戻り: 保存した絶対/相対パスリスト
- **注意**: 現状フォルダ分け未対応（タスク B で改修予定）

```python
def save_generated_code_with_merge(self, generated_files,
                                   output_dir) -> List[str]
```

- `merger.merge_all_files(generated_files, output_dir)` を呼び、`save_generated_code` に委譲

#### その他

| メソッド | 説明 |
|---------|------|
| `get_merge_summary(generated_files, output_dir) -> Dict` | ファイルごとのユーザーコード長サマリ |
| `get_generated_file_list() -> List[str]` | 生成対象ファイル名一覧 |

#### 内部ステップ実行

- `_run_steps(filename, sm, gd) -> str`
  - `FILE_STEPS[filename]` を走査
  - `step['when'](context)` が `False` ならスキップ
  - `step_executors[step['action']](step, context)` を実行
  - 戻り `list` は `extend`、`str` は `append`、`None` はスキップ
  - `'\n'.join(parts)` で連結

- `_log_debug(message, level='debug')` — `logger.<level>` を動的取得

### 4.2 `CodeMerger`

#### マーカー定義（クラス定数）

```python
MARKERS = {
    'file_user_start':      '/* [[STABLE_USER_CODE_START]] */',
    'file_user_end':        '/* [[STABLE_USER_CODE_END]] */',
    'func_user_start':      '/* [[STABLE_USER_CODE_START:{func_name}]] */',
    'func_user_end':        '/* [[STABLE_USER_CODE_END:{func_name}]] */',
    'auto_start':           '/* [[STABLE_AUTO_GENERATED_START]] */',
    'auto_end':             '/* [[STABLE_AUTO_GENERATED_END]] */',
    'file_tail_user_start': '/* [[STABLE_USER_CODE_TAIL_START]] */',
    'file_tail_user_end':   '/* [[STABLE_USER_CODE_TAIL_END]] */',
}
```

#### 抽出 API

| メソッド | 戻り | 説明 |
|---------|------|------|
| `extract_file_user_code(content)` | str | ファイル全体のユーザーコード |
| `extract_func_user_code(content, func_name)` | str | 指定関数のユーザーコード |
| `extract_all_func_user_codes(content)` | Dict[str,str] | 全関数（`RoleFunc_(\w+)` で検出） |
| `extract_file_tail_user_code(content)` | str | ファイル末尾のユーザーコード |

#### 注入 API

| メソッド | 説明 |
|---------|------|
| `inject_file_user_code(content, user_code)` | 最後の `#include` 直後に挿入。無ければ先頭 |
| `inject_func_user_code(content, func_name, user_code)` | 既存マーカーブロックを置換（**マーカー必須**） |
| `inject_file_tail_user_code(content, user_code)` | 末尾マーカー内を置換 |

#### マージ API

```python
def merge_file(self, generated_content: str,
               existing_content: Optional[str]) -> str
```

処理順:
1. `existing_content` が空/None → `generated_content` をそのまま返す
2. `extract_file_user_code` → `inject_file_user_code`
3. `extract_all_func_user_codes` → 各関数に `inject_func_user_code`
4. `extract_file_tail_user_code` → `inject_file_tail_user_code`

```python
def merge_all_files(self, generated_files: Dict[str,str],
                    existing_dir: str) -> Dict[str,str]
```

- 各ファイルについて `existing_dir/filename` の存在を確認して `merge_file`

#### その他

| メソッド | 説明 |
|---------|------|
| `has_user_code(content)` | ファイルユーザーマーカー有無 |
| `has_func_user_code(content, func_name)` | 関数ユーザーマーカー有無 |
| `get_user_code_summary(content)` | `{'file_user_code': int, 'func_user_codes': int, 'file_tail_user_code': int}` |

### 4.3 `TransitionGenerator`

#### クラス定数

| 定数 | 値 | 説明 |
|------|----|----|
| `SHORT_CELL_NAMES` | `True` | セル関数名を `t_<State>_<Event>` 形式に |
| `TABLE_MIN_COL_WIDTH` | `14` | テーブル最小列幅 |
| `DEFAULT_TABLE_TYPE` | `'array'` | – |
| `DEFAULT_GENERATION_STYLE` | `'table_driven'` | – |

#### Dispatch テーブル

```python
self.table_generators = {
    'array':      self._generate_table_array,
    'switch':     self._generate_table_switch,     # 未実装→array
    'dictionary': self._generate_table_dictionary, # 未実装→array
}
self.process_generators = {
    'table_driven': self._generate_process_table_driven,
    'switch_case':  self._generate_process_switch_case,  # 未実装→table_driven
}
```

#### 公開 API

| メソッド | 説明 |
|---------|------|
| `set_layer(layer_name)` | 層名設定 |
| `generate_transition_cell_prototypes(sm) -> str` | セル関数前方宣言 |
| `generate_transition_cell_functions(sm) -> str` | セル関数実装 |
| `generate_transition_table(sm, table_type=None) -> str` | 遷移テーブル（dispatch） |
| `generate_transition_table_header(sm) -> str` | extern 宣言 |
| `generate_function_dictionary(sm) -> str` | デバッグ用ディクショナリ |
| `generate_process_function(sm, generation_style=None) -> str` | Process 関数（dispatch） |
| `generate_get_next_event_function(sm) -> str` | 保留イベント取得 |
| `generate_all(sm) -> Dict[str,str]` | 上記 7 種を dict で返す |
| `generate_all_transitions(sm, table_type, process_type) -> str` | 後方互換 |

#### フォールバック挙動

- 未知名 `table_type` → `self._log_debug(..., 'warning')` の上 `array` へ
- `switch` / `dictionary` 明示 → warning の上 `array` へ
- 同様に `generation_style` もフォールバック

### 4.4 `RoleFunctionGenerator`

#### 生成順（`generate_all_implementations`）

`state_machine` 指定時:
1. `TRANSITION_ID_NONE` 定数
2. `RoleFuncCallSiteEntry_<Layer>_t` 共通構造体
3. `Transition_GetId` プロトタイプ
4. 各関数の `call_sites_<Short>[]` テーブル（name 順）
5. 各ロール関数の実装（name 順）
6. `Transition_GetId` 本体（ファイル末尾、static）
7. ファイル末尾のユーザー追加領域

`state_machine` 未指定時: 5 と 7 のみ（`transition_id` なし）

#### 主要公開 API

| メソッド | 説明 |
|---------|------|
| `set_layer(layer_name)` | 層名設定 |
| `generate_none_define() -> str` | `TRANSITION_ID_NONE` |
| `generate_entry_struct() -> str` | 共通構造体 |
| `generate_transition_id_prototype() -> str` | プロトタイプ |
| `generate_transition_id_function() -> str` | 本体 |
| `generate_call_sites_table(func, call_sites) -> str` | テーブル＋COUNT マクロ |
| `generate_tail_user_section() -> str` | 末尾ユーザー領域 |
| `generate_declaration(func) -> str` | 宣言 |
| `generate_implementation(func, global_defs=None, call_sites=None, include_transition_id=True) -> str` | 実装 |
| `generate_call(func_name) -> str` | 呼び出し式 |
| `generate_all_declarations(role_functions) -> str` | 一括宣言 |
| `generate_all_implementations(role_functions, state_machine=None, global_defs=None) -> str` | 一括実装 |

#### 重複除去

- `_dedupe_by_name(funcs)` — `name` 未設定は warning スキップ、重複は最初のみ採用

#### call_sites 収集

- `_collect_call_sites(sm)` が `{func_name: [RoleFuncCallSite, ...]}` を返す
- 抽出元: `condition` / `pre_actions` / `else_actions`
- 条件式からの関数抽出:
  - `RoleFunc_\w+` パターン
  - `\b([A-Za-z_]\w*)\s*\(` パターン（C キーワード除外）
  - 単独識別子（C キーワード除外）

### 4.5 `CStructGenerator`

| メソッド | 説明 |
|---------|------|
| `set_layer(layer_name)` | 層名設定 |
| `generate_all_structs(gd) -> str` | custom_type + system_data + event_flags + system_context |
| `generate_all(gd) -> Dict[str,str]` | 6 種を dict で返す |
| `generate_common_transition_context() -> str` | 基底 `TransitionContext_t` |
| `generate_layer_transition_context(state_type, event_type) -> str` | 層別版 |
| `generate_pending_event_macros() -> str` | `FIRE_EVENT` / `MAX_CONSECUTIVE...` |
| `generate_struct(struct_type, item) -> str` | 後方互換 |

#### 生成物キー

| キー | 内容 |
|------|------|
| `custom_types` | ユーザー定義型 |
| `system_data` | `SystemData_t` |
| `event_flags` | `EventFlags_t` |
| `system_context` | `SystemContext_t`（`pending_event` / `pending_event_valid` 含む） |
| `common_transition_context` | 基底 `TransitionContext_t` |
| `pending_event_macros` | `FIRE_EVENT` / `MAX_CONSECUTIVE_PENDING_EVENTS` |

### 4.6 `CEnumGenerator`

| メソッド | 説明 |
|---------|------|
| `set_layer(layer_name)` | 層名設定 |
| `generate_state_enum(states) -> str` | `STATE_<Layer>_t` |
| `generate_event_enum(events) -> str` | `EVENT_<Layer>_t`（NONE = 0 含む） |
| `generate_flag_enum(flags) -> str` | `FLAG_t`（層非依存） |
| `generate_all_enums(states, events, flags=None) -> str` | 3 種連結 |
| `generate_bit_mask_enum(flags) -> str` | `FLAG_MASK_t` |
| `generate_enum(enum_type, items) -> str` | 後方互換 |

#### 値の採番

- 状態: 登録順 0 始まり、末尾に `<PREFIX>_MAX`
- イベント: `NONE = 0` 先頭、以降 1 始まり、末尾に `EVENT_..._MAX`
- フラグ: 登録順 0 始まり、末尾に `FLAG_MAX`

---

## 5. 設定仕様

### 5.1 生成スタイル

| 設定値 | 状態 | 挙動 |
|--------|------|------|
| `table_driven` | 実装済 | セル関数 + 関数テーブル |
| `switch_case` | 未実装 | warning の上 `table_driven` にフォールバック |

### 5.2 テーブル方式

| 設定値 | 状態 | 挙動 |
|--------|------|------|
| `array` | 実装済 | 2 次元配列 |
| `switch` | 未実装 | warning の上 `array` |
| `dictionary` | 未実装 | warning の上 `array` |

### 5.3 OS 種別

| 設定値 | ラベル | OSAL ヘッダ |
|--------|--------|------------|
| `non_rtos` | NonRTOS（ベアメタル） | `osal.h` / `osal.c` |
| `freertos` | FreeRTOS | `osal_freertos.h` / `.c`（テンプレート定義のみ） |
| `threadx` | ThreadX | `osal_threadx.h` / `.c`（同上） |

### 5.4 フォルダ構成

| 設定値 | 状態 | 出力 |
|--------|------|------|
| `flat` | 実装済 | `<output_dir>/<filename>` |
| `by_type` | **既定値・未実装** | `include/` `src/` `common/` 想定 |
| `by_layer` | 未実装 | `<layer>/<filename>` |

> 詳細は [13 章](#13-付録-引継ぎ事項タスク-b) 参照。

---

## 6. 処理フロー

### 6.1 `generate_all` シーケンス

```
generate_all(sm, gd, lib?)
  ├─ prev = _current_role_function_library
  ├─ _current_role_function_library = lib
  ├─ for filename in file_generators.keys():
  │     ├─ method_name = FILE_DISPATCH[filename]
  │     ├─ if None → warning, continue
  │     ├─ method = getattr(self, method_name)
  │     └─ generated_files[filename] = method(sm, gd)
  │           └─ _run_steps(filename, sm, gd)
  │                 ├─ context 構築
  │                 ├─ for step in FILE_STEPS[filename]:
  │                 │     ├─ when 述語判定
  │                 │     └─ step_executors[action](step, ctx)
  │                 └─ '\n'.join(parts)
  └─ finally: _current_role_function_library = prev
```

### 6.2 マージフロー

```
save_generated_code_with_merge(files, dir)
  ├─ merged = merger.merge_all_files(files, dir)
  │     └─ for each file:
  │           ├─ existing = read(dir/filename) or None
  │           └─ merge_file(generated, existing)
  │                 ├─ extract_file_user_code → inject
  │                 ├─ extract_all_func_user_codes → inject each
  │                 └─ extract_file_tail_user_code → inject
  └─ save_generated_code(merged, dir)
```

### 6.3 ロール関数マージ

```
_get_role_functions_list(sm)
  ├─ funcs = dict(sm.role_functions)
  ├─ for rf in lib.list_all():
  │     └─ if rf.name not in funcs: funcs[rf.name] = rf
  └─ return list(funcs.values())
```

---

## 7. マーカー仕様

### 7.1 マーカー一覧

| マーカー | 用途 | 検出 regex |
|---------|------|-----------|
| `/* [[STABLE_USER_CODE_START]] */` ～ `/* [[STABLE_USER_CODE_END]] */` | ファイル全体 | `re.DOTALL` |
| `/* [[STABLE_USER_CODE_START:<name>]] */` ～ `/* [[STABLE_USER_CODE_END:<name>]] */` | 関数単位 | 同上 |
| `/* [[STABLE_USER_CODE_TAIL_START]] */` ～ `/* [[STABLE_USER_CODE_TAIL_END]] */` | ファイル末尾 | 同上 |

### 7.2 注入規則

| 種別 | 規則 |
|------|------|
| ファイル全体 | 最後の `#include` 直後に挿入（無ければ先頭） |
| 関数単位 | 既存マーカーブロックの内部を置換（**マーカー必須**） |
| 末尾 | 末尾マーカー内部を置換 |

### 7.3 マーカー名

- 関数マーカー名: `_get_marker_name(func)`
  - 層あり: `{layer}_{PascalName}`
  - 層なし: `{PascalName}`

---

## 8. 命名規則

### 8.1 型名

| 種別 | 層あり | 層なし |
|------|--------|--------|
| 状態型 | `STATE_<Layer>_t` | `STATE_t` |
| イベント型 | `EVENT_<Layer>_t` | `EVENT_t` |
| フラグ型 | `FLAG_t` | `FLAG_t` |
| 遷移コンテキスト | `TransitionContext_<Layer>_t` | `TransitionContext_t` |
| 遷移関数ポインタ | `TransitionFunc_<Layer>_t` | `TransitionFunc_t` |
| call_sites 構造体 | `RoleFuncCallSiteEntry_<Layer>_t` | `RoleFuncCallSiteEntry_t` |

### 8.2 値名

| 種別 | 形式 |
|------|------|
| 状態値 | `STATE_<Layer>_<Pascal>` |
| イベント値 | `EVENT_<Layer>_<UPPER_SNAKE>`（空は `_NONE`） |
| フラグ値 | `FLAG_<UPPER_SNAKE>`（層非依存） |
| MAX | `<PREFIX>_<Layer>_MAX` |

### 8.3 関数名

| 種別 | 形式 |
|------|------|
| セル関数 | `t_<PascalState>_<UPPER_EVENT>`（`SHORT_CELL_NAMES=True`） |
| Process | `StateMachine_Process_<Layer>` |
| GetNextEvent | `StateMachine_GetNextEvent_<Layer>` |
| ロール関数 | `RoleFunc_<Layer>_<Pascal>` |
| transition_id | `Transition_GetId`（static） |
| call_sites テーブル | `call_sites_<PascalShort>` |
| COUNT マクロ | `CALL_SITES_<PascalShort>_COUNT` |

### 8.4 遷移テーブル

| 種別 | 形式 |
|------|------|
| テーブル変数 | `transition_table_<Layer>` / 層なし `transition_matrix` |
| ディクショナリ | `transition_dict_<Layer>` / 層なし `transition_dict` |
| ディクショナリ型 | `TransitionDictEntry_<Layer>_t` / `TransitionDictEntry_t` |
| SIZE マクロ | `TRANSITION_DICT_<LAYER>_SIZE` / `TRANSITION_DICT_SIZE` |

---

## 9. 生成ファイル仕様

### 9.1 ファイル別ステップ数

| ファイル | ステップ数 | 主なアクション |
|---------|-----------|---------------|
| `statable_types.h` | 22 | header/guard/enums/custom_types/struct×3/var_macros |
| `statable_transitions.h` | 9 | header/guard/include/state_machine_decl |
| `statable_transitions.c` | 15 | header/include/cell_prototypes/transition_table/cell_functions/process_func |
| `statable_role_functions.h` | 9 | header/guard/include/role_decls |
| `statable_role_functions.c` | 6 | header/include/role_impls |
| `statable_init.c` | 6 | header/include/init_func |
| `statable_event_queue.c` | 4 | header/include/event_queues |
| `statable_interrupt.c` | 4 | header/include/interrupts |
| `statable_timer.c` | 13 | header/include/timer_struct/timer_init/timer_update |
| `osal.h` | 1 | osal_header |
| `osal.c` | 1 | osal_source |

### 9.2 struct 種別 dispatch

```python
STRUCT_KIND_DISPATCH = {
    'system_data':    'system_data',
    'event_flags':    'event_flags',
    'system_context': 'system_context',
}
```

### 9.3 ファイル→生成メソッド dispatch

```python
FILE_DISPATCH = {
    'statable_types.h':          '_generate_types_header',
    'statable_transitions.h':    '_generate_transitions_header',
    'statable_transitions.c':    '_generate_transitions_source',
    'statable_role_functions.h': '_generate_role_functions_header',
    'statable_role_functions.c': '_generate_role_functions_source',
    'statable_init.c':           '_generate_init_source',
    'statable_event_queue.c':    '_generate_event_queue_source',
    'statable_interrupt.c':      '_generate_interrupt_source',
    'statable_timer.c':          '_generate_timer_source',
    'osal.h':                    '_generate_osal_header',
    'osal.c':                    '_generate_osal_source',
}
```

---

## 10. エラー・警告仕様

### 10.1 WarningCollector

```python
class WarningCollector(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.records: List[str] = []

    def emit(self, record):
        if record.levelno >= logging.WARNING:
            self.records.append(record.getMessage())
```

#### 使用方法

```python
collector = WarningCollector()
root = logging.getLogger()
root.addHandler(collector)
try:
    ...
finally:
    root.removeHandler(collector)

if collector.records:
    # 重複除去して表示
```

### 10.2 主要警告メッセージ

| 発生箇所 | メッセージ |
|---------|-----------|
| `_run_steps` | `Unknown step action: {action}` |
| `_step_struct` | `Unknown struct kind: {kind}` |
| `generate_all` | `No dispatch for {filename}` |
| `generate_all` | `No method {method_name}` |
| `generate_transition_table` | `Unknown table_type '{x}', falling back to 'array'` |
| `generate_transition_table` | `table_type '{x}' is not implemented yet, falling back to 'array'` |
| `generate_process_function` | `Unknown generation_style '{x}', falling back to 'table_driven'` |
| `generate_process_function` | `generation_style '{x}' is not implemented yet, ...` |
| `inject_func_user_code` | `関数 {name} のマーカーが見つかりません` |
| `inject_file_tail_user_code` | `末尾マーカーが見つかりません` |
| `_dedupe_by_name` | `_dedupe_by_name: skip (no name)` |

### 10.3 例外

| メソッド | 例外 | 条件 |
|---------|------|------|
| `generate_file` | `ValueError` | 未知名 |
| `save_generated_code` | `OSError` | ディレクトリ作成/書込失敗 |
| `save_generated_code_with_merge` | `OSError` | 同上 |

---

## 11. GUI 連携仕様

### 11.1 `CodeGenerationDialog`

| 属性 | 型 | 説明 |
|------|----|----|
| `state_machine` | `StateMachine` | 対象 SM |
| `global_defs` | `GlobalDefinitions` | 対象 GD |
| `generated_files` | `Dict[str,str]` | 生成結果 |
| `config_manager` | `ConfigManager` | 設定 |
| `settings_file` | `str` | JSON 保存先（既定: `codegen_settings.json`） |
| `role_function_library` | `RoleFunctionLibrary` | 共有ライブラリ |

#### 主要メソッド

| メソッド | 説明 |
|---------|------|
| `_generate_code()` | WarningCollector をアタッチして `generate_all` 実行 |
| `_save_code()` | `save_with_merge` に応じて保存メソッド切替 |
| `_open_settings_dialog()` | 設定ダイアログ起動、承認時に ConfigManager 更新 |
| `_load_saved_settings()` / `_save_settings()` | JSON 永続化 |
| `get_generated_files()` | 生成結果取得 |
| `get_config()` | 設定取得 |

#### 保存呼び出し

```python
if config.save_with_merge:
    saved_files = generator.save_generated_code_with_merge(
        self.generated_files, output_dir)
else:
    saved_files = generator.save_generated_code(
        self.generated_files, output_dir)
```

> **本タスク B で `layer_name` 引数追加が必要**。

### 11.2 `MainWindow.save_generated_code_direct`

- `WarningCollector` を root logger にアタッチ
- `CCodeGenerator.generate_all(...)` 実行
- `config.save_with_merge` で保存メソッド切替
- 完了メッセージ + 警告ダイアログ

> こちらも `layer_name` 引数追加が将来必要。

### 11.3 `CodeGenerationSettingsDialog`

- タブ: 基本設定 / ログ設定 / 外部インクルード / 出力設定
- 生成方式・テーブル方式は**固定表示**（`table_driven` + `array` を強制）
- 承認時 `_save_config()` で ConfigManager 更新

---

## 12. 既知の制約・未実装項目

### 12.1 未実装（設定は存在）

| 設定 | 状態 |
|------|------|
| `switch_case` 生成スタイル | フォールバックのみ |
| `switch` テーブル方式 | 同上 |
| `dictionary` テーブル方式 | 同上 |
| `folder_structure` 反映 | 完全未実装（**タスク B**） |
| `generate_super_include` | 未実装（**タスク A**） |
| `super_include_file` / `super_include_dir` | 未実装 |
| `external_includes*` | 未実装（**タスク C**） |
| スーパーループ（`_run.c`） | 未実装（**タスク D**） |
| `freertos` / `threadx` OSAL | テンプレート定義のみ |
| `TransitionContext_<Layer>_t` 生成 | struct_generator に定義あるが c_code_generator のステップに未統合 |
| `pending_event_macros` 生成 | 同上（ステップ未統合） |

### 12.2 後方互換 API

| 旧 API | 新 API |
|--------|--------|
| `generate_all_transitions(sm, table_type, process_type)` | `generate_all(sm)` |
| `generate_struct(struct_type, item)` | `generate_all(gd)` |
| `generate_enum(enum_type, items)` | `generate_all_enums(states, events, flags)` |

### 12.3 ログ出力

- `_log_debug(message, level='debug')` — `logger.<level>` を動的取得
- 既定 logger 名: `codegen.<module>`

---

## 13. 付録: 引継ぎ事項（タスク B）

### 13.1 現状

`save_generated_code` / `save_generated_code_with_merge` は全ファイルを `output_dir` 直下に保存。`config.folder_structure` は参照されていない。

### 13.2 改修対象

| # | ファイル | 内容 |
|---|---------|------|
| 1 | `c_code_generator.py` | `FILE_CATEGORY` / `FOLDER_STRUCTURE_RESOLVERS` 追加、`_resolve_output_path` ほか 3 ヘルパー追加、`save_generated_code` / `save_generated_code_with_merge` 修正 |
| 2 | `code_merger.py` | `merge_all_files` に `path_resolver` / `layer_name` 引数追加 |
| 3 | GUI | 変更不要（`layer_name=''` 既定） |
| 4 | テスト | `tests/test_folder_structure.py` 新規 |

### 13.3 追加テーブル（予定）

```python
FILE_CATEGORY = {
    'statable_types.h':          'include',
    'statable_transitions.h':    'include',
    'statable_role_functions.h': 'include',
    'statable_transitions.c':    'src',
    'statable_role_functions.c': 'src',
    'statable_init.c':           'src',
    'statable_event_queue.c':    'src',
    'statable_interrupt.c':      'src',
    'statable_timer.c':          'src',
    'osal.h':                    'common',
    'osal.c':                    'common',
}

FOLDER_STRUCTURE_RESOLVERS = {
    'flat':     '_resolve_path_flat',
    'by_type':  '_resolve_path_by_type',
    'by_layer': '_resolve_path_by_layer',
}
```

### 13.4 新シグネチャ（予定）

```python
def save_generated_code(self, generated_files, output_dir,
                        layer_name: str = '') -> List[str]

def save_generated_code_with_merge(self, generated_files,
                                   output_dir, layer_name: str = '') -> List[str]

def merge_all_files(self, generated_files, existing_dir,
                    path_resolver=None,
                    layer_name: str = '') -> Dict[str, str]
```

### 13.5 未確定事項

| # | 質問 | 選択肢 |
|---|------|--------|
| 1 | `by_layer` を今回実装するか | (a) 実装 / (b) スタブのみ |
| 2 | `layer_name` の供給元 | タブ名 / 設定 / 未定 |
| 3 | デフォルト `folder_structure` | `by_type` 継続か `flat` に戻すか |
| 4 | GUI での切替 | 設定ダイアログで選択可（既存）|

---

以上。本詳細仕様書は 2026-09-12 時点のソースコード（`c_code_generator.py` / `code_merger.py` / `config.py` / `transition_generator.py` / `role_function_generator.py` / `code_templates.py` / `struct_generator.py` / `enum_generator.py` / `code_generation_settings_dialog.py` / `code_generation_dialog.py` / `main_window.py`）に基づく。