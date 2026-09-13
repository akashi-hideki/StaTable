# StaTable アクションエディタ開発 引き継ぎ資料（全体まとめ）

---

## 1. プロジェクト概要

**StaTable** は状態遷移表エディタ。  
本スレッドでは **アクションエディタ（D&Dによる遷移条件・ロール関数編集画面）** を開発し、テストプログラムから本体（`main_window.py`）へ統合する作業を行った。

---

## 2. 解決済みの項目

| 項目 | 状態 |
|------|------|
| パレットからのD&Dでノード追加 | ✅ 完了 |
| 既存ノードのダブルクリックで編集ダイアログ起動 | ✅ 完了 |
| キャンバス内のノード移動を無効化（案C） | ✅ 完了 |
| ドラッグ試行時のメッセージ表示 | ✅ 完了 |
| transitionノードの3行表示（イベント名・条件・遷移先） | ✅ 完了 |
| 未定義項目の明示（「条件: なし」「→ 未設定」） | ✅ 完了 |
| 遷移条件ダイアログに遷移先/else遷移先のコンボボックス追加 | ✅ 完了 |
| 遷移条件ダイアログの初期値反映（既存の遷移先を表示） | ✅ 完了 |
| 共有ライブラリ（ロール関数・条件・リテラル）の本体統合 | ✅ 完了 |
| 共有ライブラリへのサンプルデータ登録 | ✅ 完了 |
| コード生成Widgetのプロトタイプ重複除去 | ✅ 完了 |
| コード生成Widgetの遷移先フォールバック | ✅ 完了 |
| XML保存/読込で共有ライブラリを保存 | ✅ 完了 |
| XML保存/読込でpre_actions/else_actionsを保存 | ✅ 完了 |
| `pre_actions` の1文字分解問題の修正 | ✅ 完了 |
| `RoleFunction.__init__` 引数エラーの修正 | ✅ 完了 |

---

## 3. 未解決の項目（別スレッドで対応予定）

### コード生成の重大な問題

| 問題 | 影響 | 対応ファイル |
|------|------|-------------|
| `transition_generator.py` が `pre_actions`/`else_actions`/`has_else`/`else_target` を無視 | アクションエディタの内容がコードに反映されない | `codegen/transition_generator.py` |
| ロール関数のシグネチャ不一致 | 生成コードとロール関数定義の呼び出しが食い違う | `codegen/role_function_generator.py` |
| `TransitionContext_t` 型が未定義 | コンパイルエラー | `codegen/code_templates.py`, `codegen/struct_generator.py` |
| `RoleFunctionLibrary` と `StateMachine.role_functions` が別管理 | 共有ライブラリの関数がコードに含まれない | `codegen/c_code_generator.py` |
| プロトタイプ宣言の重複 | コンパイル警告 | `codegen/c_code_generator.py` |
| 条件式が空の場合の未対応 | 生成コードが壊れる | `codegen/transition_generator.py` |
| enum値生成とライブラリ名の不一致（`Condition_XXX` vs `RoleFunc_XXX`） | リンクエラー | `codegen/transition_generator.py`, `codegen/role_function_generator.py` |

---

## 4. ファイル構成と役割

### 4.1 コアデータモデル

```
code/statable/
├── model.py                    # State, Event, Transition, RoleFunction の定義
├── state_machine.py            # StateMachine クラス（状態遷移の管理）
├── global_defs.py              # GlobalDefinitions（変数・フラグ・割り込み・タイマ・キュー）
├── xml_io.py                   # XML保存/読込（共有ライブラリ含む）★修正済
├── mermaid_gen.py              # Mermaid図生成
└── sample_data.py              # サンプルデータ生成
```

**`model.py` の主要データクラス:**
```python
@dataclass
class Transition:
    source: str
    event: str
    condition: str = ""
    pre_actions: List[str] = field(default_factory=list)
    target: str = ""
    has_else: bool = True
    else_target: str = ""
    else_actions: List[str] = field(default_factory=list)
    action: str = ""              # 旧フィールド（互換用・未使用）
    transition_type: str = "external"
    title: str = ""
```

### 4.2 アクションエディタ（transition_editor_direct）

```
code/statable_gui/transition_editor_direct/
├── dialog.py                   # メインダイアログ（ActionEditorDialog）★修正済
├── canvas_widget.py            # キャンバス（FlowCanvas, FlowNodeItem）★修正済
├── palette_widget.py           # パレット（PaletteWidget）★デバッグログ追加
├── draft.py                    # データモデル（ActionDraft, FlowItem）★修正済
├── code_widget.py              # コード表示（CodeWidget）★修正済
├── edit_dialogs.py             # ノード編集ダイアログ
└── system_global_dialog.py     # システムグローバルダイアログ
```

**`canvas_widget.py` の特徴:**
- `FlowNodeItem` は `ItemIsMovable = False` でドラッグ無効
- transitionノードは常に3行表示（イベント名・条件・遷移先）
- 未定義項目は「条件: なし」「→ 未設定」と明示
- 子ノード（pre_action, else, else_action）は親transitionの下に配置

**`draft.py` の主要機能:**
- `ensure_list()`: 文字列→リスト変換（`"init()"` → `["init()"]`）
- `transition_to_flow_item()`: Transition → FlowItem 変換
- `flow_item_to_transition()`: FlowItem → Transition 変換

### 4.3 共有ライブラリ（libcntrl）

```
code/statable_gui/libcntrl/
├── role_function_library.py    # RoleFunctionLibrary, RoleFunction
├── condition_library.py        # ConditionLibrary, ConditionTemplate
├── literal_library.py          # LiteralLibrary, LiteralDefinition
├── role_function_edit_dialog.py # ロール関数編集ダイアログ
└── literal_management_dialog.py # リテラル管理ダイアログ
```

**`libcntrl.RoleFunction` の注意点:**
- コンストラクタは `name`, `title`, `description` のみ受け付ける
- `return_type`, `arg1_type` などは `hasattr` で確認後に `setattr`

### 4.4 条件ビルダー

```
code/statable_gui/
├── condition_builder_dialog.py  # 条件ビルダー（ConditionBuilderDialog）★修正済
└── symbol_picker.py             # シンボルピッカー（旧）
```

**`ConditionBuilderDialog` の特徴:**
- イベント名、遷移先、else遷移先の入力欄
- コンボボックスに現在値を反映（`set_current_targets()`）
- シンボルツリー、リテラル化機能

### 4.5 状態遷移表

```
code/statable_gui/
├── matrix_table.py              # MatrixTableWidget（セルダブルクリックでエディタ起動）★デバッグログ追加
├── widgets.py                   # StateMachineTab（メインタブ）★デバッグログ追加
└── main_window.py               # MainWindow（アプリ全体）★修正済
```

### 4.6 コード生成（codegen）

```
code/codegen/
├── c_code_generator.py          # CCodeGenerator（メイン）★要修正
├── transition_generator.py      # TransitionGenerator ★要修正
├── role_function_generator.py   # RoleFunctionGenerator ★要修正
├── type_mapper.py               # CTypeMapper（型マッピング）
├── naming_convention.py         # CNamingConvention（命名規則）
├── struct_generator.py          # CStructGenerator
├── enum_generator.py            # CEnumGenerator
├── variable_generator.py        # VariableGenerator
├── event_queue_generator.py     # EventQueueGenerator
├── interrupt_generator.py       # InterruptGenerator
├── timer_generator.py           # TimerGenerator
├── osal_generator.py            # OSALGenerator
├── code_templates.py            # CodeTemplates ★要修正
├── code_merger.py               # CodeMerger
├── config.py                    # ConfigManager, CodeGenerationConfig
└── sample_data.py               # SampleDataGenerator
```

### 4.7 テスト

```
code/tests/
├── test_all_dialogs_gui.py          # 全ダイアログ表示テスト
├── test_drop_indicator_overlap.py   # 挿入位置インジケータ評価テスト
├── test_transition_editor_direct.py # メソッドテスト
└── test_condition_builder_gui.py    # 条件ビルダーGUIテスト
```

---

## 5. 主要な変更履歴

### 5.1 `canvas_widget.py`
- **ノード移動の無効化**：`ItemIsMovable = False`、ドラッグ試行時にメッセージ表示
- **transitionノードの3行表示**：イベント名・条件・遷移先を改行で表示
- **未定義項目の明示**：「条件: なし」「→ 未設定」

### 5.2 `dialog.py`
- **遷移条件ダイアログに遷移先を渡す**：`target_state` / `else_target_state` 引数追加

### 5.3 `condition_builder_dialog.py`
- **遷移先コンボボックス追加**：`target_combo`, `else_target_combo`
- **現在値の反映**：`set_current_targets()` メソッド追加

### 5.4 `draft.py`
- **`ensure_list` 改善**：文字列を単一要素のリストに変換

### 5.5 `code_widget.py`
- **プロトタイプ重複除去**：`set()` で一意化
- **遷移先フォールバック**：`draft.default_target` を使用
- **空条件対応**：`if (1) { ... }` で else ブロックを保持

### 5.6 `main_window.py`
- **共有ライブラリへのサンプルデータ登録**：`RoleFunction`, `ConditionTemplate`, `LiteralDefinition` を追加
- **プロジェクト保存/読込**：共有ライブラリを一緒に保存・復元（5値タプル）
- **既存タブのライブラリ参照更新**：読込後に各タブのライブラリを差し替え

### 5.7 `xml_io.py`
- **共有ライブラリのシリアライズ**：`RoleFunctionLibrary`, `ConditionLibrary`, `LiteralLibrary`
- **`pre_actions`/`else_actions` の保存**：`PreAction`, `ElseAction` 子要素
- **`_normalize_actions`**：文字列→リスト、1文字分解の自動結合
- **`RoleFunction.__init__` 互換対応**：`name`/`title`/`description` のみで生成、追加属性は `setattr`

### 5.8 `matrix_table.py`, `widgets.py`
- **デバッグログ追加**：共有ライブラリの件数、遷移情報を出力

---

## 6. デバッグログの確認ポイント

### 6.1 共有ライブラリの流れ
```
MainWindow shared libraries initialized: roles=X, conditions=Y, literals=Z
add_state_machine_tab: roles=X, ...
StateMachineTab shared libraries: roles=X, ...
MatrixTableWidget.__init__: roles=X, ...
open_transition_dialog: roles=X, ...
```

### 6.2 プロジェクト保存/読込
```
=== project_to_xml START ===
=== project_to_xml END: saved to ...
=== project_from_xml START ===
  SharedLibraries found: True
  role_function_library: N items
=== project_from_xml END ===
```

### 6.3 アクションエディタ
```
=== MatrixTableWidget.open_transition_dialog ===
existing transitions count = N
converted flow_item: FlowItem(...)
-> D&D editor accepted, N transitions
```

---

## 7. 既知の課題と注意点

### 7.1 XMLファイルの `pre_actions` 分解問題
**過去のバージョンで保存されたXMLファイル**は `pre_actions` が1文字ずつ分解されている可能性がある。  
`_normalize_actions` で自動結合するように修正済み。

### 7.2 `QGraphicsView::dragLeaveEvent` 警告
`drag leave received before drag enter` という警告が頻出するが、動作には影響なし（Qtの既知の挙動）。

### 7.3 `pre_actions` の重複
複数の transition で同じ関数が `pre_actions` に含まれる場合、プロトタイプ宣言が重複する。  
`code_widget.py` では `set()` で除去済みだが、`c_code_generator.py` では未対応。

### 7.4 空イベント（完了遷移）
`event=""` の遷移は「完了遷移」として扱われ、`matrix_table.py` で `event_name=""` にマッピングされる。  
enum生成時に `EVENT_` の空文字列にならないよう、`EVENT_NONE` などの固定名割り当てが必要。

---

## 8. コード生成の引継ぎ事項

### 8.1 修正すべき問題

| 問題 | 対象ファイル | 優先度 |
|------|-------------|--------|
| `pre_actions`/`else_actions`/`has_else`/`else_target` が反映されない | `transition_generator.py` | 最高 |
| ロール関数のシグネチャ不一致 | `role_function_generator.py` | 最高 |
| `TransitionContext_t` が未定義 | `code_templates.py`, `struct_generator.py` | 高 |
| `RoleFunctionLibrary` と `StateMachine.role_functions` の統合 | `c_code_generator.py` | 高 |
| プロトタイプ重複除去 | `c_code_generator.py` | 中 |
| 空条件対応 | `transition_generator.py` | 中 |
| 関数名の `RoleFunc_` 統一 | `transition_generator.py`, `role_function_generator.py` | 中 |

### 8.2 共有が必要なファイル（新スレッド用）

**最優先:**
- `code/codegen/transition_generator.py`
- `code/codegen/role_function_generator.py`
- `code/codegen/c_code_generator.py`
- `code/codegen/code_templates.py`

**高:**
- `code/codegen/struct_generator.py`
- `code/codegen/variable_generator.py`
- `code/codegen/enum_generator.py`
- `code/codegen/code_merger.py`

**中:**
- `code/codegen/code_generation_dialog.py`
- `code/codegen/config.py`
- `code/codegen/naming_convention.py`
- `code/codegen/osal_generator.py`
- `code/codegen/interrupt_generator.py`
- `code/codegen/event_queue_generator.py`

**参照:**
- `code/statable/model.py`
- `code/statable_gui/transition_editor_direct/code_widget.py`
- `code/statable_gui/transition_editor_direct/draft.py`

---

## 9. 新スレッドでの推奨作業手順

1. **上記ファイルを共有**
2. **`transition_generator.py` の修正から着手**
   - `_generate_switch_case_process` で `pre_actions`/`else_actions`/`has_else`/`else_target` を反映
   - 空条件の場合は `next_state = target;` のみ出力
3. **`role_function_generator.py` のシグネチャ統一**
   - `(SystemContext_t *ctx, const TransitionContext_t *transition)` に変更
4. **`TransitionContext_t` の型定義追加**（`code_templates.py` / `struct_generator.py`）
5. **`c_code_generator.py` で共有ライブラリをマージ**
6. **テスト用 StateMachine でコード生成し、反映を確認**

---

## 10. 参考: 生成されるべきコードの例

```c
// プロトタイプ宣言（重複除去）
void RoleFunc_Sensor_Init(SystemContext_t *ctx, const TransitionContext_t *transition);
void RoleFunc_Error_Log(SystemContext_t *ctx, const TransitionContext_t *transition);

// 遷移処理
STATE_t StateMachine_Process(STATE_t current_state, EVENT_t event, SystemContext_t *ctx) {
    STATE_t next_state = current_state;
    TransitionContext_t transition;

    switch (current_state) {
    case STATE_Error:
        switch (event) {
        case EVENT_NONE:  // 完了遷移
            RoleFunc_Retry_Count(ctx, &transition);  // pre_actions
            if (retry_count < 3) {
                next_state = STATE_Active;
            } else {
                RoleFunc_Error_Log(ctx, &transition);  // else_actions
                next_state = STATE_Halt;  // else_target
            }
            break;
        }
        break;
    }
    return next_state;
}
```

---

この資料を新スレッドに引き継いでください。