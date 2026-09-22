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

## 変更履歴

| バージョン | 日付 | 内容 |
|-----------|------|------|
| 1.0 | 2026-09-22 | 初版。Issue 1 のみ記載 |
| 1.1 | 2026-09-22 | Issue 1 完了。編集/削除ボタン追加、`_find_rf_by_display` の実装記録、別 Issue 候補5件を追記 |