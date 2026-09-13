# StaTable 統合仕様書 v1.5

**版**: 1.5（2026-09-13 本スレッド成果反映・v1.4 バグ修正版）
**作成根拠**: v1.4 + 本スレッド共有 12 ファイル + 実機検証（IsrNamespaceTest.xml）
**v1.4 からの主な変更**: コード生成バグ根本修正（6 ファイル）、`RoleFunction` の `kw_only=True` 化、namespace 保持の完全化、新規発見 7 項目追加

---

## 0. v1.4 → v1.5 差分サマリ

| 項目 | v1.4 | v1.5 |
|------|------|------|
| `RoleFunction`（SM 側） | 位置引数許可 | **`kw_only=True` 化**（再発防止） |
| `SettingsPanel.apply_changes()` | 位置引数で構築 → namespace 汚染 | **kwarg 化 + namespace 列追加** |
| `RoleFunctionDialog` | `namespace` 未設定 | **namespace 入力欄追加** |
| `code_widget.py`（D&D プレビュー） | `void RoleFunc_X.Y(ctx, t)` 独自形式 | **実ファイル生成形式に統一** |
| `sample_data.py` の `Transition` | 位置引数で `pre_actions` に文字列 | **全 kwarg + `List[str]` 明示** |
| `role_function_generator` | 不正識別子を素通し | **識別子検証ガード追加** |
| 既知の制約 | 75 項目 | **+7 項目（計 82 項目）** |
| 実機検証 | 未実施 | **IsrNamespaceTest.xml で正常動作確認済** |

---

## 1. 全体アーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│  statable_gui/          GUI 層                       │
│   ├── main_window.py                                 │
│   ├── widgets.py        （StateMachineTab / SettingsPanel）│
│   ├── matrix_table.py   （遷移表）                    │
│   ├── role_function_dialog.py  ★ v1.5 namespace 欄追加│
│   ├── *_dialog.py       （各種編集ダイアログ）          │
│   └── transition_editor_direct/  （D&D 遷移エディタ）  │
│       └── code_widget.py  ★ v1.5 プレビュー形式統一  │
├─────────────────────────────────────────────────────┤
│  libcntrl/              共有ライブラリ層              │
│   ├── role_function_library.py                       │
│   ├── condition_library.py                           │
│   └── literal_library.py                             │
├─────────────────────────────────────────────────────┤
│  statable/              データモデル層                │
│   ├── model.py          ★ v1.5 RoleFunction kw_only  │
│   ├── state_machine.py                               │
│   ├── global_defs.py                                 │
│   ├── xml_io.py                                      │
│   └── sample_data.py    ★ v1.5 Transition kwarg 化   │
├─────────────────────────────────────────────────────┤
│  codegen/               コード生成層                  │
│   ├── c_code_generator.py 他 15 モジュール            │
│   ├── role_function_generator.py  ★ v1.5 識別子検証  │
│   └── validate/         検証・AI連携層                │
└─────────────────────────────────────────────────────┘
```

★ 印は v1.5 で変更されたファイル。

---

## 2. データモデル層（`statable/`）

### 2.1 `model.py` の Enum（変更なし）

| Enum | 値 |
|------|-----|
| `StateType` | `NORMAL` / `CONCURRENT` / `REGION` / `INITIAL` / `FINAL` / `CHOICE` / `JUNCTION`（7 種） |
| `EventKind` | `SIGNAL` / `CALL` / `TIME` / `CHANGE` |
| `EventDeliveryType` | `DIRECT` / `QUEUE` / `DOUBLE` |
| `EventSourceLayer` | `DRIVER` / `MIDDLEWARE` |

### 2.2 `RoleFunction`（SM 側）★ v1.5 重要変更

```python
@dataclass(kw_only=True)   # ★ v1.5 追加
class RoleFunction:
    name: str
    namespace: str = ""
    description: str = ""
    return_type: str = "void"
    arg1_type: str = ""
    arg1_name: str = ""
    arg2_type: str = ""
    arg2_name: str = ""
    title: str = ""
```

#### kw_only 化の根拠

v1.4 まで位置引数構築が可能で、`namespace` フィールドが後から挿入された結果、**全フィールドが 1 つずつずれる事故**が発生（v1.5 §9.6 #76）。

| 引数 | 渡した値 | 旧: 入るフィールド | 新: kw_only 化 |
|---|---|---|---|
| `RoleFunction("Connect", "接続処理", "int")` | position | `namespace="接続処理"`, `description="int"` ❌ | **TypeError で即検出** ✅ |

#### 影響範囲（kw_only 化への対応が必要な箇所）

| ファイル | 対応 | 状態 |
|---|---|---|
| `statable/xml_io.py` | 元から全 kwarg | ✅ 変更不要 |
| `statable_gui/widgets.py` | kwarg 化修正 | ✅ v1.5 修正済 |
| `statable_gui/role_function_dialog.py` | kwarg 化修正 | ✅ v1.5 修正済 |
| `statable/sample_data.py` | kwarg 化修正 | ✅ v1.5 修正済 |
| `codegen/validate/change_applier.py` | 元から全 kwarg | ✅ 変更不要 |
| `statable_gui/transition_editor_direct/draft.py` | `Transition` 経由のみ | ✅ 変更不要 |

### 2.3 `Transition`（変更なし、kw_only 化は v1.6 予定）

`Transition` も同じ地雷を抱えているが、`sample_data.py` の修正（v1.5 実施済）と他呼び出し元の確認を経て、**v1.6 で kw_only 化予定**。

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
    action: str = ""
    transition_type: str = "external"
    title: str = ""
```

### 2.4 `sample_data.py` ★ v1.5 修正

#### 修正前（v1.4）

```python
sm.add_transition(Transition("Idle", "START", "", "init()", "Active", title="起動"))
# → pre_actions に文字列 "init()" が入り、XML 保存時に 1 文字ずつ分解される
```

#### 修正後（v1.5）

```python
sm.add_transition(Transition(
    source="Idle",
    event="START",
    condition="",
    pre_actions=["init()"],   # ★ List[str] で明示
    target="Active",
    title="起動",
))
```

全 6 遷移・全 2 ロール関数を kwarg 化。

---

## 3. 共有ライブラリ層（`libcntrl/`）

v1.4 から変更なし。`RoleFunction`（libcntrl 側）は SM 側とは別クラスで、`kw_only` 化の影響を受けない。

| 項目 | libcntrl 側 |
|---|---|
| フィールド | `name` / `namespace` / `description` / `title` / `used_global_vars` / `used_events` / `used_literals` |
| 一意キー | `qualified_name` |

---

## 4. 状態遷移エンジン

v1.4 から変更なし。

---

## 5. コード生成層（`codegen/`）

### 5.1 `role_function_generator.py` ★ v1.5 修正

#### 修正① 識別子検証ガード

```python
_VALID_C_IDENTIFIER = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
_VALID_QUALIFIED = re.compile(
    r'^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?$'
)

def _normalize_func_ref(self, ref: str) -> str:
    ...
    # ★ v1.5 追加: 識別子検証
    if not _VALID_QUALIFIED.match(name):
        self._log_debug(
            f"_normalize_func_ref: reject invalid identifier: {ref!r}",
            'warning',
        )
        return ""
    return name
```

**効果**: `retry_count++` / `g_system_tick++` / `a + b` などの C 演算子混入参照を弾き、`RoleFunc_retry_count++` の生成を防止。

#### 修正② 未定義参照の警告ログ

`generate_all_implementations()` 内で、`call_map` に登録されたが `role_functions` に存在しないキーを警告出力。

### 5.2 `c_code_generator.py`（変更なし）

### 5.3 その他（変更なし）

---

## 6. GUI 層（`statable_gui/`）

### 6.1 `widgets.py` / `SettingsPanel` ★ v1.5 修正

#### 修正① `role_table` の列追加（8 列 → 9 列）

```python
# v1.4 まで: 8 列（namespace 列なし）
self.role_table = QTableWidget(0, 8)
self.role_table.setHorizontalHeaderLabels([
    "タイトル", "関数名", "説明", "戻り値型",
    "引数1型", "引数1名", "引数2型", "引数2名"
])

# v1.5: 9 列（名前空間列を挿入）
self.role_table = QTableWidget(0, 9)
self.role_table.setHorizontalHeaderLabels([
    "タイトル", "関数名", "名前空間", "説明", "戻り値型",
    "引数1型", "引数1名", "引数2型", "引数2名"
])
```

#### 修正② `apply_changes()` の kwarg 化

```python
# v1.4 まで（バグ）
self.sm.add_role_function(
    RoleFunction(name, desc, ret, a1t, a1n, a2t, a2n, title)
)   # → namespace に desc が混入

# v1.5（修正後）
self.sm.add_role_function(RoleFunction(
    name=name,
    namespace=namespace,
    description=desc,
    return_type=ret,
    arg1_type=a1t,
    arg1_name=a1n,
    arg2_type=a2t,
    arg2_name=a2n,
    title=title,
))
```

### 6.2 `role_function_dialog.py` ★ v1.5 修正

```python
# namespace 入力欄を追加
self.namespace_edit = QLineEdit()
self.namespace_edit.setText(role_function.namespace if role_function else "")
self.namespace_edit.setPlaceholderText("例: Driver（空なら層なし）")
layout.addRow("名前空間", self.namespace_edit)

# get_role_function()
return RoleFunction(
    name=...,
    namespace=self.namespace_edit.text().strip(),   # ★ 追加
    description=...,
    ...
)
```

### 6.3〜6.20（v1.4 から変更なし）

---

## 7. 遷移エディタ層（`transition_editor_direct/`）

### 7.1 `code_widget.py` ★ v1.5 修正（重要）

#### 修正前（v1.4 まで）の問題

```python
# プレビュー生成（独自形式）
lines.append(f"void RoleFunc_{name}(SystemContext_t *ctx, const TransitionContext_t *transition);")
```

**症状**: `void RoleFunc_Middleware.HandleErr(ctx, transition)` など、実ファイル生成と全く異なる形式を D&D エディタの「コード」タブに表示。

#### 修正後（v1.5）

```python
# 実ファイル生成（role_function_generator.py）と一致する形式
def _role_func_name(self, ref: str) -> str:
    """'Middleware.HandleErr' → 'RoleFunc_Middleware_HandleErr'"""
    ...

def _context_type(self) -> str:
    layer = self._get_layer_name()
    return f"TransitionContext_{layer}_t" if layer else "TransitionContext_t"

# プロトタイプ
lines.append(
    f"int {func_name}("
    f"const {context_type} *transition, "
    f"SystemContext_t *ctx);"
)

# 本体
lines.append(f"    {func_name}(transition, ctx);")
```

#### 層名推定ロジック（新規）

```python
def _get_layer_name(self) -> str:
    """参照関数の namespace を集計し、最頻値を層名として採用"""
    ns_count = {}
    for item in self.draft.flow_items:
        names = ...
        for n in names:
            if '.' in n:
                ns = n.split('.', 1)[0]
                ns_count[ns] = ns_count.get(ns, 0) + 1
    if ns_count:
        return max(ns_count.items(), key=lambda kv: kv[1])[0]
    return ''
```

### 7.2 その他（変更なし）

---

## 8. 検証・AI連携層（`validate/`）

v1.4 から変更なし（v1.4 で完全解明済）。

---

## 9. 既知の制約・未実装項目

### 9.1〜9.5 v1.0〜v1.4 から継続

v1.4 から変更なし（75 項目）。

### 9.6 v1.5 で新規発見・修正済み（★ 7 項目追加）

| # | 項目 | 対象 | 状態 |
|---|------|------|------|
| 76 | **`SettingsPanel.apply_changes()` が `RoleFunction` を位置引数で構築 → `namespace` に `description` が混入** | `widgets.py` | ✅ 修正済 |
| 77 | **`role_table` に namespace 列がなく round-trip で消失** | `widgets.py` | ✅ 修正済 |
| 78 | **`role_function_dialog.py` が `namespace` を設定しない** | `role_function_dialog.py` | ✅ 修正済 |
| 79 | **`update_mermaid()` → `apply_changes()` の副作用で XML ロード直後に namespace が破壊される** | `widgets.py` | ✅ #76 で解消 |
| 80 | **`model.py` の `RoleFunction` を `kw_only=True` 化していない** | `model.py` | ✅ 修正済 |
| 81 | **`code_widget.py` のプレビューが実ファイルと形式不一致（`void` / `.` / 引数逆順 / 層名欠落）** | `code_widget.py` | ✅ 修正済 |
| 82 | **`role_function_generator._normalize_func_ref` に識別子検証なし → `retry_count++` 等の混入** | `role_function_generator.py` | ✅ 修正済 |

---

## 10. 付録: バージョン差分まとめ

| 変更 | v1.0 | v1.1 | v1.2 | v1.3 | v1.4 | **v1.5** |
|------|------|------|------|------|------|----------|
| スコープ | 5 層 | +遷移エディタ | +GUI 詳細 | +GUI 全容 | +validate 層 | **+バグ根本修正** |
| データモデル | 正式化 | – | – | – | 大幅拡充 | **kw_only 化** |
| 共有ライブラリ | 追加 | – | – | – | 構造差異確定 | – |
| GUI 層 | 追加 | – | 詳細化 | 更に詳細化 | +編集ダイアログ 3 件 | **+namespace 列** |
| コード生成層 | v3.0 要約 | 主要 12 詳細化 | – | – | – | **識別子検証追加** |
| 遷移エディタ層 | 概要 | 詳細章化 | 起動元追記 | – | – | **プレビュー形式統一** |
| validate 層 | – | – | – | 存在判明 | 完全解明 | – |
| 2 つの `RoleFunction` | 中核明記 | – | – | namespace 消失追記 | 構造差異確定 | **SM 側 kw_only 化** |
| 既知の制約 | 23 | 32 | 47 | 65 | 75 | **82** |
| 実機検証 | – | – | – | – | – | **IsrNamespaceTest で成功** |

---

## 11. 残課題（次版 v1.6 で対応）

### 11.1 ファイル共有で解決可能

| # | 課題 | 必要なファイル | 優先 |
|---|------|--------------|------|
| 1 | 遷移エディタ層の中核未精査 | `palette_widget.py` / `flow_widget.py`（共有済だが改修余地） | ★★ |
| 2 | `codegen/sample_data.py`（GUI 側でない方）の見直し | 同ファイル | ★★ |
| 3 | 残り codegen モジュール（`struct_generator.py` / `enum_generator.py` / `variable_generator.py` / `event_queue_generator.py` / `timer_generator.py` / `osal_generator.py`） | 各ファイル | ★ |
| 4 | `__init__.py` 群 4 件（v1.4 §11 #3 から継続） | 各ファイル | ★ |
| 5 | `main_window.py` の残メソッド精査 | 同ファイル | ★ |

### 11.2 方針確定待ち（ファイル共有では解決しない）

| # | 項目 | 優先 |
|---|------|------|
| 1 | **`Transition` の `kw_only=True` 化**（`sample_data.py` 修正済のため実施可能） | ★★★ |
| 2 | `add_state` の `type` 列挙不足（`CONCURRENT` / `REGION` / `CHOICE` / `JUNCTION` 追加） | ★★ |
| 3 | `remove_role_function` の不一致（`ChangeActionType` にあるが `ACTION_DEFINITIONS` / `_handlers` にない） | ★★ |
| 4 | `code_widget.py` の層名推定を `ActionDraft.layer_name` 属性で正式化 | ★★ |
| 5 | `role_function_generator` の未定義参照を **エラー扱い** に昇格するか | ★ |
| 6 | `event` / `transition` バリデータの logger 追加 | ★ |
| 7 | v1.3 §9.5 #58-60（DIRECT→DOUBLE 変換）を仕様許容 or バグ修正 | ★★★ |
| 8 | `parser.py` スタブの実装予定を仕様に明記 | ★ |

---

## 12. v1.5 の最重要発見

1. **`RoleFunction` の位置引数構築が namespace 汚染の根本原因**（v1.4 §9.6 #69 の真実）
2. **`kw_only=True` 化により、同種の事故を構造的に防止可能**
3. **`code_widget.py` のプレビューが実ファイル生成と不一致**（D&D エディタ表示のみ別系統だった）
4. **`update_mermaid()` → `apply_changes()` の副作用で XML ロード直後に namespace が破壊される**
5. **`sample_data.py` の位置引数バグ #67 が `retry_count++` 症状の根本原因**
6. **`role_function_generator` に識別子検証がなく、不正参照を素通ししていた**

### 修正の本質（一言）

> **「フィールド順序変更 + 位置引数構築」の掛け算で、namespace ↔ description ↔ title が 1 つずつずれていた**

---

## 13. 実機検証結果（IsrNamespaceTest.xml）

### 検証項目と結果

| # | 検証項目 | 結果 |
|---|---------|------|
| 1 | 3 層（Driver / Middleware / Application）が表示される | ✅ |
| 2 | `RoleFunction` が namespace 付きで表示される | ✅ |
| 3 | 割り込み処理タブに 5 件の ISR が表示される | ✅ |
| 4 | 遷移セル編集で「ロール関数」「遷移条件」両リストに候補が表示される | ✅ |
| 5 | コード生成後、`statable_interrupt.c` に `ctx` 挿入と `RoleFunc_*` 呼び出し | ✅ |
| 6 | マージ再生成でユーザー追加コードが保持される | ✅ |

### 生成コード（成功例）

```c
/* statable_role_functions.c */
int RoleFunc_Middleware_Connect(
    const TransitionContext_Middleware_t *transition,
    SystemContext_t *ctx)
{ ... }

int RoleFunc_Middleware_HandleErr(
    const TransitionContext_Middleware_t *transition,
    SystemContext_t *ctx)
{ ... }

int RoleFunc_Driver_Init(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx)
{ ... }
```

**日本語関数名・`.` 混入・引数逆順が全て消滅。**

---

## 14. 次版 v1.6 への引き継ぎ

### 最優先事項

1. **`Transition` の `kw_only=True` 化**（★★★）
   - `sample_data.py` は v1.5 で修正済みのため、他呼び出し元の kwarg 確認後すぐに実施可能
   - 対象: `statable/model.py`

2. **`codegen/sample_data.py`（GUI 側でない方）の精査**（★★）
   - v1.5 を通じて未共有のまま
   - `SampleDataGenerator` の役割確認と形式統一

3. **`add_state` の `type` 列挙拡張**（★★）
   - `CONCURRENT` / `REGION` / `CHOICE` / `JUNCTION` 追加
   - 対象: `codegen/validate/change_applier.py` の `_add_state` メソッド

### 次スレッド冒頭に貼るテンプレート

```
# StaTable 統合仕様書 v1.5 引き継ぎ

## 作業目的
StaTable 統合仕様書の完成。v1.5 から v1.6 へ。

## 前スレッドの成果
- コード生成バグ根本修正（6 ファイル）
- RoleFunction の kw_only=True 化（再発防止）
- namespace 保持の完全化
- IsrNamespaceTest.xml で実機検証成功

## 修正済みファイル（v1.5）
1. statable/model.py                （RoleFunction kw_only 化）
2. statable_gui/role_function_dialog.py （namespace 欄追加）
3. statable_gui/widgets.py           （namespace 列追加 + kwarg 化）
4. statable_gui/transition_editor_direct/code_widget.py（プレビュー形式統一）
5. statable/sample_data.py           （Transition kwarg 化）
6. codegen/role_function_generator.py（識別子検証追加）

## 次に共有すべきファイル
1. codegen/sample_data.py          （GUI 側でない方）
2. statable_gui/transition_editor_direct/palette_widget.py
3. codegen/struct_generator.py / enum_generator.py / variable_generator.py
4. codegen/event_queue_generator.py / timer_generator.py / osal_generator.py
5. __init__.py 群 4 件

## 方針確定待ち
1. Transition の kw_only=True 化（★★★）
2. add_state の type 列挙拡張（★★）
3. remove_role_function の不一致（★★）
```

---

**以上、本スレッドの成果を反映した StaTable 統合仕様書 v1.5 を完成させました。**

**v1.4 からの主な進展**:
- コード生成の根本バグ 6 ファイル修正
- `RoleFunction` の `kw_only=True` 化（同種事故の構造的防止）
- D&D エディタプレビューと実ファイル生成の形式統一
- 実機検証（IsrNamespaceTest.xml）で全 6 項目成功

**次スレッドへの引き継ぎ**:
- 本 v1.5 を冒頭に貼付
- §11.1 の優先順にファイルを共有
- §11.2 の方針確定項目を順次判断
- §14 の最優先事項 3 件から着手