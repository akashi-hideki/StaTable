# StaTable コード生成モジュール 詳細仕様書

対象: `code/codegen/` 配下および関連 GUI モジュール  
版: 2.0（2026-09-13 時点のソースコードに基づく）  
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
13. [付録: 完了済みタスク実績](#13-付録-完了済みタスク実績)
14. [★ 次タスク（H）: ISR コンテキスト対応](#14--次タスクhisr-コンテキスト対応)

---

## 1. 概要

### 1.1 目的

StaTable の状態遷移モデル（`StateMachine` + `GlobalDefinitions`）から C 言語コードを生成する。ユーザー編集領域を保持するマージ機構、設定による生成方式切替、層（layer）ごとの多層ステートマシン対応、フォルダ構成反映、スーパーインクルード/ループ生成を含む。

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
| スーパーインクルード | 全生成ヘッダを一括 include する `statable_all.h` |
| スーパーループ | 全層のメインループを提供する `{project}_run.c` |

---

## 2. モジュール構成と責務

| モジュール | 責務 |
|-----------|------|
| `c_code_generator.py` | 生成の統括。ステップテーブル・ディスパッチ・フォルダ解決・保存 |
| `code_merger.py` | 生成コードと既存コードのマージ |
| `config.py` | 設定 dataclass と ConfigManager |
| `transition_generator.py` | セル関数・遷移テーブル・Process 関数生成 |
| `role_function_generator.py` | ロール関数宣言/実装・call_sites・Transition_GetId |
| `struct_generator.py` | 構造体（SystemData / EventFlags / SystemContext / TransitionContext） |
| `enum_generator.py` | 列挙型（STATE / EVENT / FLAG） |
| `code_templates.py` | 固定文字列・テンプレート・OSAL / スーパーインクルード / スーパーループ |
| `type_mapper.py` / `naming_convention.py` | 型変換・命名変換 |
| `variable_generator.py` 他 | 変数マクロ・初期化関数・イベントキュー・割り込み・タイマ・OSAL |
| `code_generation_dialog.py` | 生成 GUI・WarningCollector |
| `code_generation_settings_dialog.py` | 設定 GUI |

---

## 3. データ仕様

### 3.1 `CodeGenerationConfig`（`config.py`）

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
| `folder_structure` | str | `"by_type"` | `flat` / `by_type` / `by_layer`（**全て実装済**） |
| `include_dir_name` | str | `"include"` | – |
| `source_dir_name` | str | `"src"` | – |
| `common_dir_name` | str | `"common"` | – |
| `project_dir_name` | str | `"project"` | – |
| `generate_super_include` | bool | `True` | ✅ 実装済 |
| `super_include_file` | str | `"statable_all.h"` | ✅ 実装済 |
| `super_include_dir` | str | `"common"` | ✅ 実装済（by_type時） |
| `external_includes` | List[str] | `[]` | 未実装（タスク C） |
| `external_includes_in_super` | bool | `True` | 未実装 |
| `external_includes_in_role` | bool | `True` | 未実装 |
| `external_includes_in_transitions` | bool | `False` | 未実装 |
| `external_includes_in_common` | bool | `False` | 未実装 |
| `max_consecutive_pending_events` | int | `16` | 保留イベント連続処理上限 |

**メソッド**
- `to_dict() -> Dict` — 全フィールドを dict 化
- `from_dict(data: Dict) -> CodeGenerationConfig` — 未知キーは無視

### 3.2 `ConfigManager`

| メソッド | 説明 |
|---------|------|
| `get_config() -> CodeGenerationConfig` | 現在の設定 |
| `set_config(config)` | 設定を置換 |
| `update(**kwargs)` | `hasattr` チェック後に `setattr` |
| `reset()` | 既定値に戻す |
| `get_available_styles()` | `table_driven` / `switch_case` |
| `get_available_table_types()` | `array` / `switch` / `dictionary` |
| `get_available_os_types()` | `non_rtos` / `freertos` / `threadx` |
| `get_available_folder_structures()` | `flat` / `by_layer` / `by_type` |

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
| `statable_all.h` | スーパーインクルード | `STATABLE_ALL_H` |
| `{project}_run.c` | スーパーループ | `None` |

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