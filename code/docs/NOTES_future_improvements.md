# StaTable 将来の改善候補（保管）

Version: 1.0
Date: 2026-09-22
Status: **保管中**（投稿後のユーザーフィードバックを経て再評価）
対象: GUI 改善候補

\---

## この文書について

v2.4.1 の作業中、特に **TUTORIAL\_ja.md を作成する過程** で
発見した改善候補を保管します。

**重要**: ここに記載された項目は「思いついた候補」であり、
v2.5 で対応することを確定したものではありません。

v2.5 で対応する項目は `ISSUES\_v2\_5.md` に記載します。

投稿後のユーザーフィードバックを経て、優先度を再評価します。

\---

## 🔴 優先度：高（投稿後に再評価）

### 候補1: entry / exit 編集の視認性向上

**Estimated**: 1時間

#### Problem

State list の entry / exit 列の編集導線が分かりにくい。
セルをダブルクリックで編集できるが、視覚的な手がかりがない。

チュートリアル作成時、「ダブルクリック」と明記せざるを得なかった。

#### Proposal

* セルに点線枠を表示（編集可能を示す）
* ツールチップを「▶ クリックして開く」に変更

#### 対象ファイル

* `statable\_gui/widgets.py` の `SettingsPanel.populate()`

\---

### 候補2: Namespace コンボボックスの動的更新

**Estimated**: 30分

#### Problem

ダイアログを開いた瞬間の候補が固定される。
タブを追加した直後、別のダイアログで候補が更新されない場合がある。

#### Proposal

* コンボボックスの `showPopup()` 時に候補を再取得
* 現在のタブの `layer\_name` をデフォルト選択

#### 対象ファイル

* `statable\_gui/role\_function\_dialog.py`

\---

### 候補3: 遷移編集の軽量モード

**Estimated**: 2〜3時間

#### Problem

単純な遷移を1つ追加するのに、5タブ構成の ActionEditorDialog を
開く必要がある（6ステップ）。

#### Proposal

* セル選択状態で Enter キー → インライン入力
* または、右クリック → コンテキストメニュー「遷移を追加」

\---

## 🟡 優先度：中

### 候補4: Event definitions への入り口改善

**Estimated**: 1時間

#### Problem

Event definitions が SettingsPanel の Role function タブ内にあり、
カテゴリ分類が不自然。

#### Proposal

* SettingsPanel に独立した「Events」タブを追加
* または、ツールバーに「Events」ボタン追加

\---

### 候補5: 新規タブ作成時のデフォルト名

**Estimated**: 30分

#### Problem

File → New State Machine で名前入力が必須。連続追加時に面倒。

#### Proposal

* デフォルト名 `Layer1`, `Layer2`, ... を自動入力
* または、名前候補をドロップダウン表示

\---

## 🟢 優先度：低

### 候補6: マトリクスのセルサイズ改善

**Estimated**: 2〜3時間

#### Problem

状態数・イベント数が増えると、セルが小さくなりすぎる。

#### Proposal

* セル幅の最小値を保証
* セル内のテキスト折り返し
* 水平スクロール許容

\---

### 候補7: Role 関数ダイアログのフォーカス移動

**Estimated**: 15分

#### Problem

ダイアログ表示時、最初のフィールドに自動フォーカスしない。

#### Proposal

* Function name に自動フォーカス

\---

### 候補8: 条件式ビルダーへの導線

**Estimated**: 1時間

#### Problem

`ConditionBuilderDialog` が存在するが、導線が不明。

#### Proposal

* 条件式入力欄の横に `\[...]` ボタン
* クリックで ConditionBuilderDialog を起動

\---

### 候補9: 検証結果からのジャンプ機能

**Estimated**: 1〜2時間

#### Problem

ValidationDialog で問題が表示されても、該当セルへの
ジャンプ機能がない。

#### Proposal

* 警告行をダブルクリック → 該当セルを選択・スクロール

\---

### 候補10: Mermaid 図のエクスポート

**Estimated**: 1時間

#### Proposal

* MermaidWidget に「Save as PNG」ボタン
* または右クリックメニュー

\---

### 候補11: キーボードショートカット一覧

**Estimated**: 1時間

#### Proposal

* メニュー Help → Keyboard Shortcuts
* F1 で一覧ダイアログ

\---

### 候補12: タブの並び替え

**Estimated**: 1〜2時間

#### Problem

タブの順序 = 追加順。ドラッグで並び替えできない。

#### Proposal

* タブをドラッグで並び替え
* または、Layer Settings の優先度変更でタブ順も連動

\---

## サマリ

|優先度|件数|推定時間|
|-|-|-|
|🔴 高|3件|約4時間|
|🟡 中|2件|約1.5時間|
|🟢 低|7件|約7〜10時間|
|**合計**|**12件**|**約13〜16時間**|

\---

## 参考：TUTORIAL 作成時に気になった3点

### A. entry / exit の編集導線

チュートリアル 7.2 で「ダブルクリック」と明記せざるを得なかった。

### B. Events が Role function タブ内

「Role function タブ内の」と注記が必要だった。

### C. 遷移編集のダイアログが重い

単純な遷移追加に6ステップ。

\---

## 次のアクション

1. **投稿を実施**（HN / Reddit / CSDN / 知乎）
2. **ユーザーフィードバックを収集**
3. **優先度を再評価**
4. **v2.5 で対応する項目を `ISSUES\_v2\_5.md` に移動**

\---

## 変更履歴

|バージョン|日付|内容|
|-|-|-|
|1.0|2026-09-22|初版。TUTORIAL\_ja.md 作成中に発見した 12件の候補を保管|



