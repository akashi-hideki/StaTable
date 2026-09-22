# StaTable v2.5 対応予定

Version: 1.0
Date: 2026-09-22
対象: v2.5 で対応する項目

---

## この文書について

v2.5 で対応する項目を記録します。TUTORIAL 作成中に発見した
改善候補のうち、**「今回対応する」と確定したもの**のみを記載します。

その他の候補は、投稿後のユーザーフィードバックを経て、
別途検討します。

---

## Issue 1: ActionEditorDialog に「New Role Function」ボタンを追加

**Priority**: 🔴 High
**Estimated**: 1〜2時間
**Type**: Enhancement / GUI
**Status**: 未着手

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

ActionEditorDialog の以下2タブに「+ New Role Function」
ボタンを追加:

- **Transitions タブ**（条件式・pre_actions 用）
- **Pre / Post Actions タブ**（セルアクション用）

### Behavior

1. ボタンクリック
2. RoleFunctionDialog を開く（既存を再利用）
3. 入力 → OK
4. 自動的にリストに追加 + 選択状態
5. StateMachine にも登録される

### Implementation

**Files to modify**:

| ファイル | 変更内容 |
|---------|---------|
| `statable_gui/transition_editor_direct/actions_tab.py` | `ActionsTab` / `_ActionGroup` に `role_function_library`, `literal_library`, `namespace_choices_provider` を追加。`+ New Role Function` ボタン追加 |
| `statable_gui/transition_editor_direct/transitions_tab.py` | 同様のボタン追加 |
| `statable_gui/transition_editor_direct/dialog.py` | `ActionsTab` / `TransitionsTab` への引数渡し |
| `statable_gui/matrix_table.py` | `ActionEditorDialog` 呼び出し時に新引数を渡す |

**Required data（既に取得可能）**:

| データ | 現状 |
|-------|------|
| `state_machine` | ✅ `ActionEditorDialog` が保持（L72） |
| `global_defs` | ✅ 同上（L71） |
| `role_function_library` | ✅ 同上（L74-77） |
| `literal_library` | ✅ 同上（L82-85） |
| `layer_names_provider` | ⚠️ 間接的に取得可能 |

**Reuse**:
- `RoleFunctionDialog`（既存、v3.9）
- `widgets.py._role_function_dialog_kwargs`（参考）

### Acceptance Criteria

- [ ] Pre / Post Actions タブに「+ New Role Function」ボタンがある
- [ ] Transitions タブにも同様のボタンがある
- [ ] ボタンから RoleFunctionDialog が開く
- [ ] 新規作成後、自動的にリストに追加される
- [ ] 名前重複時は警告が出る
- [ ] Namespace コンボボックスに全タブのレイヤ名が候補表示される
- [ ] テストが PASS する（既存14スイート）

### Labels

`enhancement`, `gui`, `v2.5`

---

## 変更履歴

| バージョン | 日付 | 内容 |
|-----------|------|------|
| 1.0 | 2026-09-22 | 初版。Issue 1 のみ記載 |