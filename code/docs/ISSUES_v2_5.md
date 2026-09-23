# StaTable v2.5 対応予定

Version: 1.1
Date: 2026-09-22
対象: v2.5 で対応する項目

---

## この文書について

v2.5 で対応する項目を記録します。TUTORIAL 作成中に発見した
改善候補のうち、**「今回対応する」と確定したもの**のみを記載します。

その他の候補は、投稿後のユーザフィードバックを経て、
別途検討します。

---

## Issue 1: ActionEditorDialog に「New Role Function」ボタンを追加

**Priority**: 🔴 High
**Estimated**: 1〜2時間
**Type**: Enhancement / GUI
**Status**: ✅ **完了**（2026-09-22）

### Summary

ユーザーが遷移・セルアクションを編集中に、Role 関数をその場で
新規作成できるボタンを追加する。

### Problem

現状、新しい Role 関数が必要になった場合、以下の手順が必要:

1. ActionEditorDialog を一旦閉じる
2. SettingsPanel → Role function タブへ移動
3. Add ボタンで新規作成
4. 再びセルをダブルクリック
5. 作成した Role 関数を選択

→ **11ステップ**。作業の流れが分断される。

### Proposal

ActionEditorDialog の以下2タブに操作ボタンを追加:

- **Transitions タブ**（条件式・pre_actions 用）
  → `+ New Role Function` ボタン1個
- **Pre / Post Actions タブ**（セルアクション用）
  → `+ New Role Function` / `Edit Role Function` /
     `Delete Role Function` の3ボタン

### Behavior

1. ボタンクリック
2. RoleFunctionDialog を開く（既存を再利用）
3. 入力 → OK
4. 自動的にリストに追加 + 選択状態
5. StateMachine にも登録される

### Implementation

**Files modified**:

| ファイル | 変更内容 |
|---------|---------|
| `statable_gui/transition_editor_direct/actions_tab.py` | `ActionsTab` / `_ActionGroup` に `role_function_library`, `literal_library`, `layer_names_provider` を追加。3ボタン追加。`_find_rf_by_display()` 追加 |
| `statable_gui/transition_editor_direct/transitions_tab.py` | 同様の引数追加 + `+ New Role Function` ボタン |
| `statable_gui/transition_editor_direct/dialog.py` | `TransitionsTab` / `ActionsTab` への新引数渡し |

**変更不要だったファイル**:

- `statable_gui/matrix_table.py`（既に必要な引数を渡していた）
- `statable_gui/role_function_dialog.py`（既存の再利用で対応）
- `statable_gui/widgets.py`（SettingsPanel は変更なし）

### Acceptance Criteria

- [x] Pre / Post Actions タブに「+ New Role Function」ボタンがある
- [x] Transitions タブにも同様のボタンがある
- [x] ボタンから RoleFunctionDialog が開く
- [x] 新規作成後、自動的にリストに追加される
- [x] 名前重複時は警告が出る
- [x] Namespace コンボボックスに現タブのレイヤ名が候補表示される
      （※ 全タブのレイヤ名は別 Issue に分離）
- [x] Pre / Post Actions タブに Edit / Delete ボタンもある
- [x] 選択行の Role 関数を編集できる（qualified_name 逆引き対応）
- [x] 選択行の Role 関数を削除できる（確認ダイアログ付き）
- [x] テストが PASS する（既存14スイート 576 PASS / 2 SKIP）

### 追加実装（当初計画外）

| 項目 | 理由 |
|------|------|
| `Edit Role Function` / `Delete Role Function` | 実装中に「編集・削除も同じ場所で行いたい」という要望に対応 |
| `_find_rf_by_display()` | `StateMachine.role_functions` は **pure name** でキー管理、UI 表示は **qualified_name** のため逆引きが必要だった |
| デバッグログ（`_dump_sm_roles`, `logger.debug` 群） | 上記の名前解決バグを将来再発させないため |

### 既知の制約（v2.5 スコープ外）

- Namespace コンボ候補は「現タブ + 登録済みロール関数」のみ
  （全タブの layer 名を候補にする配線は別 Issue）
- `TransitionsTab` には編集/削除ボタンなし
  （対象行がなく UI 的に不自然なため）

### Labels

`enhancement`, `gui`, `v2.5`, `completed`

---

## その他の候補（v2.5 スコープ外、別 Issue として検討）

以下は TUTORIAL 作成中に発見したが、**v2.5 には含めない**と判断した項目:

### 候補 1: Namespace 全タブ対応

- **現状**: Namespace コンボは「現タブ + 登録済み」のみ
- **要望**: `MainWindow._get_all_layer_names()` を
  `StateMachineTab → MatrixTableWidget → ActionEditorDialog`
  まで配線し、全タブのレイヤ名を候補に
- **影響**: 4ファイル変更、v2.5 の見積もりを超過

### 候補 2: RoleFunctionDialog 内に「+ New Literal」ボタン

- **現状**: Literal は SettingsPanel で作成
- **要望**: Role 関数編集中に Literal も作成

### 候補 3: ConditionBuilderDialog 内に「+ New Template」ボタン

- **現状**: 条件テンプレートは SettingsPanel で作成
- **要望**: 条件編集中にテンプレートも作成

### 候補 4: TransitionsTab のラベルリネームダイアログ

- **現状**: ラベルは `T1`, `T2`... で自動採番、`transitions_tab.py` に
  「Reserved for future "Rename Label..." dialog.」のコメントあり
- **要望**: ユーザが任意のラベルを付けられるように

### 候補 5: namespace と layer_name の不一致警告

- **現状**: `Tab name="Application"` で `namespace="App"` のような
  データを読み込むと、Namespace コンボに両方が候補表示される
- **背景**: v3.11 の設計通り（layer_name と namespace は独立）。
  ただし UX 上は紛らわしい
- **対応案**:
  - B: 現タブの layer_name を候補の先頭に固定（非破壊的）
  - C: layer_name と一致しない namespace に印を付ける
  - D: XML 読み込み時に namespace を自動同期（**破壊的**）
- **判断**: データ起因であり、正しい XML なら問題は発生しない。
  投稿後のフィードバック次第で対応

---

### 候補 6: RoleFunction.namespace の「前方一致制約」を緩和

**Priority**: 🟡 Medium
**Type**: Bug / Enhancement
**Status**: ✅ v2.5.1 で解消（`_should_declare_here` に call_map フォールバック追加）

#### 現状
`role_function_generator._should_declare_here`（および `_should_emit_implementation`）
は以下の場合のみ、その層のヘッダに宣言を出力する：

- `namespace == layer_name`（完全一致）
- `min(len(ns), len(layer)) >= 3` かつ
  `layer.lower().startswith(ns.lower())` または
  `namespace.lower().startswith(layer.lower())`（双方向の前方一致）

#### 問題
不一致の場合：
- **呼び出し**（`RoleFunc_<NS>_<Name>`）は `transition_generator` が生成する
- **宣言**は `role_function_generator` が生成しない
- → `implicit declaration of function 'RoleFunc_<NS>_*'` でコンパイルエラー

#### 再現例（v2.5 TUTORIAL で実証）
| namespace | layer_name | 判定 | 結果 |
|-----------|-----------|------|------|
| `App` | `Application` | 前方一致（3文字） | ✅ 12/12 PASS |
| `Vending` | `Application` | 双方向不一致 | ❌ 11/12 FAIL（gcc / arm 両方） |

#### 対応案
| # | 案 | 変更ファイル | リスク |
|---|----|------------|-------|
| A | SPEC に明記（v2.5 で C-50 として追加済み） | 文書のみ | なし |
| B | `_should_declare_here` を「その層から呼ばれる関数」基準に変更 | `role_function_generator.py` | 中 |
| C | XML 読み込み時に前方一致を自動補正 or 警告 | `xml_io.py` | 中 |
| D | 呼び出し側も宣言側と同じ判定を行う | 両 generator | 大 |

#### 回避策（現実的）
namespace を層の短縮名（`App`、`Drv`、`Mw` など）にする。
TUTORIAL では `Vending` → `App` に変更して解決（`tools/fix_vending_namespace_v2.py`）。

---

### 候補 7: イベントの「発生条件」定義（trigger）

**Priority**: 🟡 Medium
**Type**: Enhancement / Data model
**Status**: v2.5.2 で発見（設計ギャップ）

#### 現状

`<Event>` 要素には以下の属性がある:

- `kind`（signal / call / time / change）
- `delivery_type`（direct / queue / double）
- `source_layer`（driver / middleware）
- `priority`, `data_type`, `data_name`

しかし **「いつ発生するか」を書く場所がない**。
`description` に自由記述はできるが、構造化されていない:

| 不足情報 | 例（SELECT_ITEM） |
|---------|-----------------|
| 発生源 | 商品ボタン GPIO |
| トリガー種別 | エッジ検出 |
| デバウンス | 20ms |
| ポーリング周期 | 10ms |
| データ生成 | `item_id = ボタン index` |

#### 影響

- 状態遷移表のセルを見ても「そのイベントがいつ来るか」が分からない
- `StateMachine_GetNextEvent_<Layer>` はユーザー実装（codegen は空関数を出力）
- バリデーションで「time イベントなのに周期未定義」を検出できない

#### 対応案（段階的）

| # | 案 | 工数 | codegen |
|---|----|------|---------|
| A | `trigger` 自由記述属性を追加 | 1〜2h | 影響なし |
| B | `<Trigger type="..." source="..."/>` 構造化 | 4〜6h | v2.6 で活用 |
| C | GUI に「イベントカタログ」タブ | 1日 | – |

#### 推奨

段階的に進める:

1. SPEC に C-51 として記録（本 Issue で実施）
2. 投稿後のフィードバックを待つ
3. v2.6 で案 A → 案 B の順に実装

#### 対象ファイル（将来）

- `statable/model.py`（`EventTrigger` dataclass 追加）
- `statable/xml_io.py`（`<Trigger>` 子要素の I/O）
- `statable_gui/event_definition_dialog.py`（トリガー編集 UI）
- `codegen/transition_generator.py`（v2.6 で GetNextEvent 自動生成）

---

## 変更履歴

| バージョン | 日付 | 内容 |
|-----------|------|------|
| 1.0 | 2026-09-22 | 初版。Issue 1 のみ記載 |
| 1.1 | 2026-09-22 | Issue 1 完了。編集/削除ボタン追加、`_find_rf_by_display` の実装記録、別 Issue 候補5件を追記 |