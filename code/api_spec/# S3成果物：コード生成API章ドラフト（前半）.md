# S3成果物：コード生成API章ドラフト（前半）

`c_code_generator.py`, `config.py` を受領しました。§4コード生成API章の前半を作成します。

---

## 0. S3分析サマリ

| 項目 | 結果 |
|------|------|
| 解析対象 | 2ファイル、計3クラス（`CCodeGenerator`, `CodeGenerationConfig`, `ConfigManager`） |
| `CCodeGenerator` 公開メソッド | 12 |
| `CCodeGenerator` 内部メソッド | 約75（`_step_*` 40、`_generate_*` 14、`_resolve_*` 4、他） |
| `CodeGenerationConfig` フィールド | 30 |
| SPEC_OVERVIEW との差分 | 5件（後述 §1） |
| S4への申し送り | 6件（後述 §5） |

### 1. SPEC_OVERVIEW_en.md との差分

| # | 差分 | 影響 | 対応 |
|---|------|------|------|
| D-15 | `CCodeGenerator` のモジュールバージョンが **v2.2.9**（MISRA 17.3 fix） | SPEC_OVERVIEW §7.1 は「v2.2.9」表記済み、一致 | 確認 |
| D-16 | `CodeGenerationConfig` の **`super_include_dir`** フィールド（`"common"`） | SPEC_OVERVIEW §3.5.4 / C-10 と一致（XML非永続） | 確認、§4.3で明記 |
| D-17 | `naming_prefix` / `state_prefix` / `event_prefix` / `flag_prefix` の4フィールド | SPEC_OVERVIEW 未記載。命名規則APIと関連 | §4.3で明記 |
| D-18 | `enable_debug_logs` / `enable_info_logs` / `enable_error_logs` / `enable_comments` / `enable_doxygen` / `enable_user_markers` の6フィールド | SPEC_OVERVIEW 未記載 | §4.3で明記 |
| D-19 | `project_dir_name` フィールド（**予約、未使用**） | SPEC_OVERVIEW C-14 と一致 | §4.3で「Reserved」注記 |

---

## 1. §4 コード生成API章ドラフト（前半）

### 4.1 概要

コード生成層は `CCodeGenerator` を中心とし、以下の3クラスで構成される。

| クラス | 役割 |
|--------|------|
| `CCodeGenerator` | 生成オーケストレータ。step-table driven で13ファイルを生成 |
| `CodeGenerationConfig` | 生成設定（30フィールドのdataclass） |
| `ConfigManager` | 設定のライフサイクル管理 |

**アーキテクチャ**：

```
CCodeGenerator
  ├── CodeGenerationConfig（設定）
  ├── ConfigManager（設定管理）
  ├── 内部ジェネレータ（12個）
  │   ├── CTypeMapper        (type_mapper.py)
  │   ├── CNamingConvention  (naming_convention.py)
  │   ├── CStructGenerator   (struct_generator.py)
  │   ├── CEnumGenerator     (enum_generator.py)
  │   ├── TransitionGenerator
  │   ├── RoleFunctionGenerator
  │   ├── VariableGenerator
  │   ├── EventQueueGenerator
  │   ├── InterruptGenerator
  │   ├── TimerGenerator
  │   ├── OSALGenerator
  │   └── CodeTemplates
  └── CodeMerger（マーカー方式マージ）
```

**生成方式**：各ファイルは **`FILE_STEPS` テーブル**（`action` のリスト）に従って生成される。`_run_steps_multi` が step executor を順次呼び出し、パーツを結合する。

---

### 4.2 `CCodeGenerator`

Cコード生成の中核クラス。

#### 4.2.1 モジュールバージョン

```
Version 2.2.9 (2026-09-20 / MISRA 17.3 fix)
```

主な変更履歴：

| バージョン | 内容 |
|-----------|------|
| 2.2.9 | MISRA 17.3: `statable_transitions_<Layer>.c` が `statable_types_common.h` を直接include |
| 2.2.8 | get_next_event emission |
| 2.2.7 | MISRA 17.3: LOG マクロ + GetNextEvent プロトタイプ |
| 2.2.6 | MISRA 17.3: cross-layer include |
| 2.1 | ISR context support |
| 1.6 | by_layer suffix / common types |

#### 4.2.2 クラス定数（公開）

| 定数 | 型 | 説明 |
|------|-----|------|
| `FILE_STEPS` | `Dict[str, List[Dict]]` | 各ファイルの step 定義テーブル |
| `STRUCT_KIND_DISPATCH` | `Dict[str, str]` | struct種別 → 生成メソッド名 |
| `FILE_DISPATCH` | `Dict[str, str]` | ファイル名 → 生成メソッド名 |
| `FILE_CATEGORY` | `Dict[str, str]` | ファイル名 → カテゴリ（`include`/`src`/`common`） |
| `FOLDER_STRUCTURE_RESOLVERS` | `Dict[str, str]` | フォルダ構成名 → パス解決メソッド名 |
| `LAYER_SPECIFIC_FILES` | `Set[str]` | レイヤ別に生成されるファイル集合（5ファイル） |
| `COMMON_FILES` | `Set[str]` | レイヤ共通ファイル集合（8ファイル） |

**`LAYER_SPECIFIC_FILES`**（by_layer時にレイヤ名サフィックス付きで出力）：

- `statable_types.h`
- `statable_transitions.h`
- `statable_transitions.c`
- `statable_role_functions.h`
- `statable_role_functions.c`

**`COMMON_FILES`**：

- `statable_types_common.h`
- `statable_init.c`
- `statable_event_queue.c`
- `statable_interrupt.c`
- `statable_timer.c`
- `osal.h` / `osal.c`
- `statable_all.h`

#### 4.2.3 `__init__`

```python
def __init__(self, config: Optional[CodeGenerationConfig] = None)
```

**パラメータ**

| 名前 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|-----------|------|
| `config` | `Optional[CodeGenerationConfig]` | – | `None` | 生成設定。`None`時はデフォルト設定 |

**戻り値**：なし

**属性（公開）**

| 名前 | 型 | 説明 |
|------|-----|------|
| `config` | `CodeGenerationConfig` | 現在の設定 |
| `config_manager` | `ConfigManager` | 設定マネージャ |
| `mapper` | `CTypeMapper` | 型マッパー |
| `naming` | `CNamingConvention` | 命名規則 |
| `struct_gen` | `CStructGenerator` | 構造体生成 |
| `enum_gen` | `CEnumGenerator` | Enum生成 |
| `transition_gen` | `TransitionGenerator` | 遷移生成 |
| `role_func_gen` | `RoleFunctionGenerator` | ロール関数生成 |
| `variable_gen` | `VariableGenerator` | 変数生成 |
| `event_queue_gen` | `EventQueueGenerator` | イベントキュー生成 |
| `interrupt_gen` | `InterruptGenerator` | ISR生成 |
| `timer_gen` | `TimerGenerator` | タイマー生成 |
| `osal_gen` | `OSALGenerator` | OSAL生成 |
| `templates` | `CodeTemplates` | テンプレート辞書 |
| `merger` | `CodeMerger` | マーカー方式マージ |
| `generation_date` | `str` | 生成日時（`%Y-%m-%d %H:%M:%S`） |
| `super_loop_filename` | `str` | `f"{project_name}_run.c"` |

**使用例**

```python
from codegen.c_code_generator import CCodeGenerator
from codegen.config import CodeGenerationConfig

config = CodeGenerationConfig(project_name="Demo")
gen = CCodeGenerator(config=config)
```

#### 4.2.4 設定管理メソッド

##### `get_config`

```python
def get_config(self) -> CodeGenerationConfig
```

**戻り値**：現在の設定

##### `set_config`

```python
def set_config(self, config: CodeGenerationConfig) -> None
```

**パラメータ**

| 名前 | 型 | 必須 | 説明 |
|------|-----|------|------|
| `config` | `CodeGenerationConfig` | ○ | 新しい設定 |

**動作**：`config_manager.set_config(config)` 後に `self.config` を再取得

##### `update_config`

```python
def update_config(self, **kwargs) -> None
```

**パラメータ**：`config` の任意のフィールドをキーワード引数で指定

**動作**：`config_manager.update(**kwargs)` → `self.config` 再取得

**使用例**

```python
gen.update_config(project_name="NewName", folder_structure="by_layer")
```

##### `reset_config`

```python
def reset_config(self) -> None
```

**動作**：設定をデフォルトに戻す

#### 4.2.5 生成メソッド

##### `generate_all`

単一の `StateMachine` から全ファイルを生成する。

```python
def generate_all(
    self,
    state_machine: StateMachine,
    global_defs: GlobalDefinitions,
    role_function_library=None,
) -> Dict[str, str]
```

**パラメータ**

| 名前 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|-----------|------|
| `state_machine` | `StateMachine` | ○ | – | 対象ステートマシン |
| `global_defs` | `GlobalDefinitions` | ○ | – | グローバル定義 |
| `role_function_library` | `RoleFunctionLibrary \| None` | – | `None` | 共有ロール関数ライブラリ |

**戻り値**：`Dict[str, str]` — ファイル名 → 生成コード

**動作**

- `role_function_library` を一時的に `self._current_role_function_library` に設定（生成中のロール関数統合用）
- `generate_super_include=False` の場合、`statable_all.h` をスキップ
- 各ファイルは `FILE_DISPATCH` 経由で生成メソッドを呼び出す

##### `generate_file`

単一ファイルのみ生成する。

```python
def generate_file(
    self,
    filename: str,
    state_machine: StateMachine,
    global_defs: GlobalDefinitions,
    role_function_library=None,
) -> str
```

**パラメータ**

| 名前 | 型 | 必須 | 説明 |
|------|-----|------|------|
| `filename` | `str` | ○ | 生成対象ファイル名（例：`"statable_transitions.c"`） |
| 他 | – | – | `generate_all` と同じ |

**戻り値**：`str` — 生成コード

**例外**

| 例外 | 条件 |
|------|------|
| `ValueError` | `filename` が `self.file_generators` に存在しない |

##### `generate_all_layers` ★中核

複数レイヤ（タブ）を統合して全ファイルを生成する。

```python
def generate_all_layers(
    self,
    layers,
    global_defs: GlobalDefinitions,
    role_function_library=None,
) -> Dict[str, str]
```

**パラメータ**

| 名前 | 型 | 必須 | 説明 |
|------|-----|------|------|
| `layers` | `List[Tuple[str, StateMachine]] \| StateMachine` | ○ | レイヤリスト、または単一のSM |
| `global_defs` | `GlobalDefinitions` | ○ | グローバル定義 |
| `role_function_library` | `RoleFunctionLibrary \| None` | – | 共有ライブラリ |

**戻り値**：`Dict[str, str]` — ファイル名 → 生成コード

**動作**

- `layers` は内部で `_normalize_layers()` により正規化
  - `StateMachine` 単体 → `[(layer_name, sm)]` に変換
  - `List` → `layer_priority` 昇順でソート
- `folder_structure == 'by_layer'` の場合、`_generate_all_by_layer()` に委譲
- それ以外は `_run_steps_multi()` で全レイヤを統合処理
- `generate_super_include=False` の場合、`statable_all.h` をスキップ

**使用例**

```python
layers = [("Application", sm1), ("Driver", sm2)]
files = gen.generate_all_layers(layers, global_defs)
# files: {"statable_types_common.h": "...", "statable_types.h": "...", ...}
```

**by_layer時の戻り値キー**

`_generate_all_by_layer` 経由の場合、キーが `f"{layer_name}/{filename}"` 形式になる（レイヤ別ファイル）。

#### 4.2.6 保存メソッド

##### `save_generated_code`

生成済みコードをディスクに保存する（マージなし）。

```python
def save_generated_code(
    self,
    generated_files: Dict[str, str],
    output_dir: str,
    layer_name: str = '',
) -> List[str]
```

**パラメータ**

| 名前 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|-----------|------|
| `generated_files` | `Dict[str, str]` | ○ | – | ファイル名 → コード |
| `output_dir` | `str` | ○ | – | 出力ディレクトリ |
| `layer_name` | `str` | – | `''` | レイヤ名（by_layer時のパス解決用） |

**戻り値**：`List[str]` — 保存された絶対/相対パス

**動作**

- `os.makedirs(output_dir, exist_ok=True)` で出力ディレクトリ作成
- 各ファイルは `_resolve_output_path(filename, layer_name)` で実パス解決
- 親ディレクトリも自動作成

##### `save_generated_code_with_merge` ★ユーザコード保持

生成コードと既存ファイルをマージして保存する。

```python
def save_generated_code_with_merge(
    self,
    generated_files: Dict[str, str],
    output_dir: str,
    layer_name: str = '',
) -> List[str]
```

**パラメータ**：`save_generated_code` と同じ

**戻り値**：`List[str]` — 保存パス

**動作**

1. `merger.merge_all_files(generated_files, output_dir, path_resolver=..., layer_name=...)` でマージ
2. `save_generated_code()` で保存

**使用例**

```python
saved = gen.save_generated_code_with_merge(files, "./output")
```

**備考**：`config.save_with_merge == True` の場合、GUIからはこちらが呼ばれる（`main_window.py` 参照）

##### `get_merge_summary`

既存ファイルのユーザコード量を集計する。

```python
def get_merge_summary(
    self,
    generated_files: Dict[str, str],
    output_dir: str,
    layer_name: str = '',
) -> Dict[str, Dict[str, int]]
```

**戻り値**：ファイル名 → `{'file_user_code': n, 'func_user_codes': n, 'file_tail_user_code': n}`

**動作**

- 既存ファイルが存在すれば `merger.get_user_code_summary(existing_content)` を呼び出し
- 存在しない場合は0埋め

#### 4.2.7 情報取得メソッド

##### `get_generated_file_list`

```python
def get_generated_file_list(self) -> List[str]
```

**戻り値**：`List[str]` — `file_generators` のキー一覧（登録順）

#### 4.2.8 内部メソッド（非公開）

SDKの公開APIには**含めない**が、内部構造として記録：

| カテゴリ | メソッド | 数 |
|---------|---------|-----|
| step executor | `_step_*` | 40 |
| ファイル生成ディスパッチャ | `_generate_*` | 14 |
| パス解決 | `_resolve_*` | 4 |
| レイヤ設定 | `_setup_layer_generators`, `_normalize_layers`, `_get_layer_name`, `_get_initial_state` | 4 |
| リスト取得 | `_get_states_list`, `_get_events_list`, `_get_role_functions_list` | 3 |
| step 実行 | `_run_steps`, `_run_steps_multi` | 2 |
| その他 | `_log_debug`, `_layer_filename`, `_layer_suffix`, `_generate_section_header`, `_generate_file_header`, `_generate_include_guard_*`, `_generate_include_section` | 8 |

**`_step_*` の一覧**（40メソッド、`FILE_STEPS` の `action` と1対1対応）：

```
_step_file_header, _step_blank, _step_guard_start, _step_guard_end,
_step_include_section, _step_section_header, _step_enums, _step_enums_common,
_step_layer_transition_context, _step_common_function_decls, _step_custom_types,
_step_struct, _step_var_macros, _step_state_machine_decl, _step_cell_prototypes,
_step_transition_table, _step_cell_functions, _step_process_func, _step_get_next_event,
_step_role_decls, _step_role_impls, _step_init_func, _step_event_queues,
_step_interrupts, _step_timer_struct, _step_timer_init, _step_timer_update,
_step_osal_header, _step_osal_source, _step_super_include_header,
_step_super_include_guard_start, _step_super_include_guard_end,
_step_super_include_common, _step_super_include_layer, _step_super_include_project,
_step_super_include_extern_vars, _step_super_include_extern_funcs,
_step_super_include_external, _step_super_include_user, _step_super_include_guard_end,
_step_super_loop_header, _step_super_loop_include, _step_super_loop_context_var,
_step_super_loop_state_var, _step_super_loop_init_func, _step_super_loop_run_func
```

---

### 4.3 `CodeGenerationConfig`

生成設定のdataclass（30フィールド）。**全て`kw_only=False`**（通常のdataclass）。

#### 4.3.1 フィールド一覧

| # | 名前 | 型 | デフォルト | 説明 |
|---|------|-----|-----------|------|
| 1 | `generation_style` | `str` | `"table_driven"` | 生成方式（`table_driven` / `switch_case`） |
| 2 | `table_type` | `str` | `"array"` | テーブル型（`array` / `switch` / `dictionary`） |
| 3 | `os_type` | `str` | `"non_rtos"` | OS種別（`non_rtos` / `freertos` / `threadx`） |
| 4 | `naming_prefix` | `str` | `""` | 名前空間プレフィックス |
| 5 | `state_prefix` | `str` | `"STATE"` | 状態enum prefix |
| 6 | `event_prefix` | `str` | `"EVENT"` | イベントenum prefix |
| 7 | `flag_prefix` | `str` | `"FLAG"` | フラグenum prefix |
| 8 | `enable_debug_logs` | `bool` | `True` | LOG_DEBUG有効 |
| 9 | `enable_info_logs` | `bool` | `True` | LOG_INFO有効 |
| 10 | `enable_error_logs` | `bool` | `True` | LOG_ERROR有効 |
| 11 | `enable_comments` | `bool` | `True` | コメント生成 |
| 12 | `enable_doxygen` | `bool` | `True` | Doxygen形式 |
| 13 | `enable_user_markers` | `bool` | `True` | ユーザマーカー出力 |
| 14 | `output_directory` | `str` | `""` | 出力先 |
| 15 | `save_with_merge` | `bool` | `True` | マージ保存 |
| 16 | `project_name` | `str` | `"MyProject"` | プロジェクト名 |
| 17 | `folder_structure` | `str` | `"by_type"` | フォルダ構成（`flat` / `by_layer` / `by_type`） |
| 18 | `include_dir_name` | `str` | `"include"` | include ディレクトリ |
| 19 | `source_dir_name` | `str` | `"src"` | src ディレクトリ |
| 20 | `common_dir_name` | `str` | `"common"` | common ディレクトリ |
| 21 | `project_dir_name` | `str` | `"project"` | **予約（未使用）** |
| 22 | `generate_super_include` | `bool` | `True` | スーパーinclude生成 |
| 23 | `super_include_file` | `str` | `"statable_all.h"` | スーパーincludeファイル名 |
| 24 | `super_include_dir` | `str` | `"common"` | スーパーinclude配置先 |
| 25 | `external_includes` | `List[str]` | `[]` | 外部include |
| 26 | `external_includes_in_super` | `bool` | `True` | super への外部include |
| 27 | `external_includes_in_role` | `bool` | `True` | role への外部include（**未実装**） |
| 28 | `external_includes_in_transitions` | `bool` | `False` | transitions への外部include（**未実装**） |
| 29 | `external_includes_in_common` | `bool` | `False` | common への外部include（**未実装**） |
| 30 | `max_consecutive_pending_events` | `int` | `16` | 連続pendingイベント上限 |

#### 4.3.2 制限事項（SPEC_OVERVIEW C-01〜C-14 との対応）

| フィールド | 制限 | 関連C番号 |
|-----------|------|----------|
| `generation_style` | `switch_case` は未実装 → 実質 `table_driven` 固定 | C-01, C-02 |
| `table_type` | `switch` / `dictionary` は未実装 → 実質 `array` 固定 | C-03, C-04 |
| `project_dir_name` | 予約、未使用 | C-14 |
| `external_includes_in_role` | 未実装 | C-05 |
| `external_includes_in_transitions` | 未実装 | C-06 |
| `external_includes_in_common` | 未実装 | C-07 |
| `super_include_dir` | XML非永続（`xml_io` で保存されない） | C-10 |

#### 4.3.3 `to_dict`

```python
def to_dict(self) -> Dict
```

**戻り値**：全30フィールドをキーとする辞書

#### 4.3.4 `from_dict`

```python
@classmethod
def from_dict(cls, data: Dict) -> 'CodeGenerationConfig'
```

**パラメータ**

| 名前 | 型 | 必須 | 説明 |
|------|-----|------|------|
| `data` | `Dict` | ○ | 復元元辞書 |

**戻り値**：`CodeGenerationConfig` — 復元された設定

**動作**

- `cls.__dataclass_fields__` に存在しないキーは無視（前方互換）

**使用例**

```python
cfg = CodeGenerationConfig.from_dict({"project_name": "Demo", "unknown": 123})
# → CodeGenerationConfig(project_name="Demo", ...)  # unknown は無視
```

---

### 4.4 `ConfigManager`

設定のライフサイクル管理クラス。

#### 4.4.1 `__init__`

```python
def __init__(self)
```

デフォルトの `CodeGenerationConfig()` を保持。

#### 4.4.2 メソッド

##### `get_config`

```python
def get_config(self) -> CodeGenerationConfig
```

現在の設定を返す。**コピーではなく同一インスタンス**を返す点に注意。

##### `set_config`

```python
def set_config(self, config: CodeGenerationConfig) -> None
```

設定を置換。

##### `update`

```python
def update(self, **kwargs) -> None
```

部分更新。`hasattr` チェックあり（未知キーは無視）。

##### `reset`

```python
def reset(self) -> None
```

デフォルト設定に戻す。

##### `get_available_styles`

```python
def get_available_styles(self) -> Dict[str, str]
```

**戻り値**

```python
{
    'table_driven': 'Table-driven style',
    'switch_case':  'switch-case style',
}
```

##### `get_available_table_types`

```python
def get_available_table_types(self) -> Dict[str, str]
```

**戻り値**

```python
{
    'array':      'Array style',
    'switch':     'switch-case style',
    'dictionary': 'Dictionary style (deprecated)',
}
```

##### `get_available_os_types`

```python
def get_available_os_types(self) -> Dict[str, str]
```

**戻り値**

```python
{
    'non_rtos': 'NonRTOS (bare metal)',
    'freertos': 'FreeRTOS',
    'threadx':  'ThreadX',
}
```

##### `get_available_folder_structures`

```python
def get_available_folder_structures(self) -> Dict[str, str]
```

**戻り値**

```python
{
    'flat':     'Flat',
    'by_layer': 'Per layer',
    'by_type':  'include/src separation',
}
```

---

### 4.5 出力ファイル一覧（14ファイル）

`FILE_STEPS` / `FILE_DISPATCH` / `FILE_CATEGORY` に基づく正式リスト（14ファイル）：

| # | ファイル名 | カテゴリ | レイヤ別 | 役割 |
|---|-----------|---------|---------|------|
| 1 | `statable_types_common.h` | `include` | – | 共通型・enum・構造体 |
| 2 | `statable_types.h` | `include` | ○ | レイヤ別enum + `TransitionContext_<Layer>_t` |
| 3 | `statable_transitions.h` | `include` | ○ | Process / GetNextEvent プロトタイプ |
| 4 | `statable_transitions.c` | `src` | ○ | Cell関数、遷移テーブル、Process、GetNextEvent |
| 5 | `statable_role_functions.h` | `include` | ○ | `RoleFunc_<NS>_<Name>` 宣言 |
| 6 | `statable_role_functions.c` | `src` | ○ | ロール関数実装 + call_sites + Transition_GetId |
| 7 | `statable_init.c` | `src` | – | `SystemContext_Init` |
| 8 | `statable_event_queue.c` | `src` | – | イベントキュー実装 |
| 9 | `statable_interrupt.c` | `src` | – | ISR |
| 10 | `statable_timer.c` | `src` | – | タイマー構造体 + Init / Update |
| 11 | `osal.h` | `common` | – | OS抽象化ヘッダ |
| 12 | `osal.c` | `common` | – | OS抽象化実装 |
| 13 | `statable_all.h` | `common`（推定） | – | スーパーinclude |
| 14 | `{project_name}_run.c` | `src` | – | スーパーループ |

**注意**：SPEC_OVERVIEW §7.2 は「13ファイル」と記載しているが、`__init__` で `super_loop_filename` を追加するため、**動的には14ファイル**（`generate_super_include=False` なら13ファイル）。

---

### 4.6 フォルダ構成

`folder_structure` により出力レイアウトが変わる。パス解決は `_resolve_output_path` 経由。

#### 4.6.1 `flat`

全ファイルを出力ディレクトリ直下に配置。

```
output_dir/
├── statable_types_common.h
├── statable_types.h
├── statable_transitions.h
├── ...
└── MyProject_run.c
```

**実装**：`_resolve_path_flat` — ファイル名をそのまま返す

#### 4.6.2 `by_type`

`FILE_CATEGORY` に応じて `include/` / `src/` / `common/` に振り分け。

```
output_dir/
├── include/
│   ├── statable_types_common.h
│   ├── statable_types.h
│   ├── statable_transitions.h
│   └── statable_role_functions.h
├── src/
│   ├── statable_transitions.c
│   ├── statable_role_functions.c
│   ├── statable_init.c
│   ├── statable_event_queue.c
│   ├── statable_interrupt.c
│   ├── statable_timer.c
│   └── MyProject_run.c
└── common/
    ├── osal.h
    ├── osal.c
    └── statable_all.h
```

**実装**：`_resolve_path_by_type` — `FILE_CATEGORY.get(filename)` で分岐

#### 4.6.3 `by_layer`

レイヤ別ファイルは `<layer_name>/` 配下に出力、共通ファイルはルート直下。

```
output_dir/
├── Application/
│   ├── statable_types_Application.h
│   ├── statable_transitions_Application.h
│   ├── statable_transitions_Application.c
│   ├── statable_role_functions_Application.h
│   └── statable_role_functions_Application.c
├── Driver/
│   ├── statable_types_Driver.h
│   └── ...
├── statable_types_common.h
├── statable_init.c
├── statable_event_queue.c
├── statable_interrupt.c
├── statable_timer.c
├── osal.h
├── osal.c
├── statable_all.h
└── MyProject_run.c
```

**実装**：`_resolve_path_by_layer` + `_layer_filename`（`stem_layer.ext` 形式）

**注意**

- `LAYER_SPECIFIC_FILES` のみサフィックス付与
- 共通ファイル（`COMMON_FILES`）はサフィックスなし
- **SPEC_OVERVIEW C-18**：複数レイヤの `by_type` は1ファイルにマージされる（レイヤ区別不可）

---

## 2. §8 エラーコード（S3分の追記）

| 例外 | 発生箇所 | 条件 |
|------|---------|------|
| `ValueError` | `CCodeGenerator.generate_file` | `filename` が未登録 |
| `FileNotFoundError` / `OSError` | `save_generated_code` | 出力パス作成失敗 |
| `ImportError` | モジュール先頭 | `statable` 未インストール時（フォールバックあり） |

---

## 3. §9 制限事項（S3分の追記）

| # | 制限 | 関連C番号 |
|---|------|----------|
| L-01 | `generation_style="switch_case"` は実質無効（`table_driven` 固定） | C-01, C-02 |
| L-02 | `table_type="switch"` / `"dictionary"` は実質無効（`array` 固定） | C-03, C-04 |
| L-03 | `project_dir_name` は予約、未使用 | C-14 |
| L-04 | `external_includes_in_role/transitions/common` は未実装 | C-05〜C-07 |
| L-05 | `super_include_dir` はXML非永続 | C-10 |
| L-06 | `by_type` 複数レイヤは1ファイルにマージされる | C-18 |
| L-07 | `generate_all` は単一SM向け、複数レイヤには `generate_all_layers` を使用 | – |

---

## 4. H2中間引継ぎへの反映事項（前半）

| # | 反映先 | 内容 |
|---|--------|------|
| H2-01 | §4.2 | `CCodeGenerator` 12公開メソッド |
| H2-02 | §4.3 | `CodeGenerationConfig` 30フィールド |
| H2-03 | §4.4 | `ConfigManager` 8メソッド |
| H2-04 | §4.5 | 出力ファイル14ファイル |
| H2-05 | §4.6 | フォルダ構成3種 |
| H2-06 | §9 | L-01〜L-07 |

---

## 5. S4への申し送り

### 5.1 S4で扱うソース

| # | ファイル | 行数目安 | 役割 |
|---|---------|---------|------|
| 1 | `codegen/role_function_generator.py` | ~950 | ロール関数の宣言・実装・call_sites |
| 2 | `codegen/transition_generator.py` | ~700 | Cell関数・遷移テーブル・Process・GetNextEvent |
| 3 | `codegen/code_templates.py` | ~750 | テンプレート辞書 |

### 5.2 S4で確認すべき項目

| # | 項目 | 内容 |
|---|------|------|
| S4-01 | `RoleFunctionGenerator` の公開メソッド（`generate_declaration` / `generate_implementation` / `generate_call_sites_table` 等） |
| S4-02 | `TransitionGenerator` の公開メソッド（`generate_transition_cell_functions` / `generate_transition_table` / `generate_process_function` / `generate_get_next_event_function`） |
| S4-03 | `TransitionGenerator._role_func_call_expr` / `_role_func_call_action` の **(void)キャスト分岐**（SPEC_OVERVIEW §7.4.5の核心） |
| S4-04 | `CodeTemplates` の公開辞書（`STRINGS` / `FORMATS` / `SECTION_HEADERS` / `SUPER_INCLUDE_TEMPLATES` / `SUPER_LOOP_TEMPLATES`） |
| S4-05 | `codegen/validate/` の章立て判断（U-01）— **S4では扱わず、S5またはS8で検討** |
| S4-06 | `TemplateCustomizer` 相当APIの有無（引継ぎ書 §2.3 で言及） |

### 5.3 S4で判断が必要な事項

- `RoleFunctionGenerator` / `TransitionGenerator` の**公開境界**（内部ジェネレータだが、SDK利用者が直接使うか）
- `CodeTemplates` の**カスタマイズAPI**の有無（SPEC_OVERVIEW §2.3「TemplateCustomizer」の実在確認）

---

## 6. 次のアクション

**S4の3ファイルを共有してください。**

| # | ファイル | 優先度 | 備考 |
|---|---------|--------|------|
| 1 | `codegen/role_function_generator.py` | 高 | ~950行。call_sites と Transition_GetId が中核 |
| 2 | `codegen/transition_generator.py` | 高 | ~700行。MISRA 17.7 分岐が重要 |
| 3 | `codegen/code_templates.py` | 中 | ~750行。テンプレート辞書 |

受領後、§4後半（サブジェネレータAPI）を作成し、続けて **H2中間引継ぎ文書（S3+S4統合版）** を提示します。