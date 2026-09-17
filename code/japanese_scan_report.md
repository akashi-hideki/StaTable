# StaTable 日本語テキスト調査レポート

## サマリ

- スキャンファイル数: 119
- 日本語を含むファイル数: 118
- 日本語を含む行数: 4149

## カテゴリ別集計

| カテゴリ | 説明 | 行数 | ファイル数 |
|---|---|---|---|
| A | 生成 C コードコメント（最優先） | 905 | 12 |
| B | GUI 表示文言（最優先） | 1363 | 41 |
| C | コード生成層のログ等 | 502 | 32 |
| F | サンプルデータ | 57 | 1 |
| G | テスト期待値 | 532 | 16 |
| H | その他 | 790 | 16 |

## ファイル別集計（行数の多い順）

| ファイル | カテゴリ | 行数 |
|---|---|---|
| `codegen\transition_generator.py` | A | 185 |
| `tools\scan_japanese.py` | H | 180 |
| `codegen\c_code_generator.py` | A | 174 |
| `codegen\code_templates.py` | A | 143 |
| `statable_gui\code_generation_settings_dialog.py` | B | 131 |
| `statable_gui\main_window.py` | B | 111 |
| `codegen\struct_generator.py` | A | 108 |
| `codegen\role_function_generator.py` | A | 103 |
| `statable_gui\interrupt_handler_edit_dialog.py` | B | 98 |
| `statable_gui\code_generation_dialog.py` | B | 91 |
| `tools\write_isr_test_xml.py` | H | 89 |
| `tools\consistency_check.py` | H | 85 |
| `tools\purge_unused_files.py` | H | 83 |
| `codegen\code_merger.py` | C | 78 |
| `statable_gui\validation_dialog.py` | B | 75 |
| `codegen\validate\validation_dialog.py` | C | 72 |
| `statable_gui\common_widgets.py` | B | 61 |
| `codegen\variable_generator.py` | A | 60 |
| `statable\sample_data.py` | F | 57 |
| `statable_gui\event_definition_dialog.py` | B | 57 |
| `tests\test_gui_roundtrip.py` | G | 56 |
| `codegen\validate\data\validation_rules.py` | C | 55 |
| `tests\test_role_function_generator.py` | G | 54 |
| `statable_gui\global_defs_dialog.py` | B | 53 |
| `statable_gui\widgets.py` | B | 53 |
| `tests\test_c_code_generator.py` | G | 52 |
| `statable_gui\condition_builder_dialog.py` | B | 50 |
| `codegen\sample_data.py` | C | 50 |
| `statable\model.py` | H | 49 |
| `codegen\validate\data\action_definitions.py` | C | 49 |
| `codegen\interrupt_generator.py` | A | 47 |
| `statable_gui\transition_editor_direct\canvas_widget.py` | B | 46 |
| `tests\test_xml_io.py` | G | 46 |
| `tools\remove_libcntrl_tryexcept.py` | H | 45 |
| `tests\test_mermaid_gen.py` | G | 44 |
| `statable\global_defs.py` | H | 43 |
| `codegen\validate\change_applier.py` | C | 43 |
| `statable\xml_io.py` | H | 42 |
| `statable_gui\dialogs.py` | B | 42 |
| `statable_gui\event_queue_dialog.py` | B | 42 |
| `tests\test_state_machine.py` | G | 42 |
| `statable_gui\symbol_picker.py` | B | 40 |
| `statable_gui\transition_editor_direct\code_widget.py` | B | 40 |
| `statable\parser.py` | H | 39 |
| `tests\test_interrupt_generator.py` | G | 38 |
| `statable\mermaid_gen.py` | H | 37 |
| `tools\transition_audit.py` | H | 37 |
| `codegen\config.py` | C | 36 |
| `statable_gui\transition_editor_direct\palette_widget.py` | B | 32 |
| `statable_gui\event_delivery_settings_dialog.py` | B | 31 |

## カテゴリ A: 生成 C コードコメント（最優先）

### `codegen\c_code_generator.py` （174 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `コード生成メインクラス` |  |
| 4 | other | `（ステップテーブル駆動版・ ファイル対応・複数層対応・ 対応・ 対応）` | layer |
| 6 | other | `設計方針` |  |
| 7 | other | `ファイルごとの生成手順は テーブルで宣言` |  |
| 8 | other | `各ステップは 辞書で実行関数に紐付け` | execute / function |
| 9 | other | `がステップ列を順に実行` | execute |
| 10 | other | `条件付きステップは 述語で宣言的に表現` | condition |
| 11 | other | `ファイル間ディスパッチは 辞書で管理` |  |
| 12 | other | `フォルダ構成は で解決` |  |
| 13 | other | `スーパーインクルード スーパーループは常に生成` |  |
| 14 | other | `複数層は で一括生成` | layer |
| 15 | other | `では層固有ファイルを層フォルダに分離` | layer |
| 17 | other | `版 （ コンテキスト対応）` | context |
| 18 | other | `に を追加（ 宣言取得）` |  |
| 19 | other | `で を再計算` |  |
| 22 | other | `時に層固有ファイルへ サフィックスを付与` | layer |
| 24 | other | `層固有ファイル内の 文を連動変更` | layer |
| 25 | other | `名にも層サフィックスを付与（衝突回避）` | layer |
| 26 | other | `共通ファイルは 時に各層の を個別` | layer |
| 27 | other | `スーパーインクルードの層固有 パスもサフィックス対応` | layer |
| 29 | other | `（案 ）` |  |
| 30 | other | `共通 （` |  |
| 31 | other | `）を` |  |
| 32 | other | `新規 に集約` |  |
| 33 | other | `層固有 は のみを出力` | layer |
| 34 | other | `層固有 は を` | layer |
| 35 | other | `も共通部に移動（層で重複させない）` | layer |
| 86 | other | `コード生成メインクラス` |  |
| 87 | docstring | `（ステップテーブル駆動・ ファイル対応・複数層対応）` | layer |
| 90 | comment | `テーブル ファイル別ステップ定義` | definition |
| ... | ... | （他 144 行）| |

### `codegen\code_templates.py` （143 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `コード生成用テンプレート定義（多層ステートマシン対応・ 対応版）` | definition / layer |
| 4 | other | `すべての固定文字列を一元管理する` |  |
| 6 | other | `版 （ ）` |  |
| 7 | other | `追加（ ）` |  |
| 8 | other | `既存テンプレートは変更なし` |  |
| 12 | string | `コード生成用テンプレート辞書` |  |
| 14 | comment | `基本文字列定義` | definition |
| 39 | string | `実装を記述すること` |  |
| 40 | string | `未使用引数の警告抑制` | argument / warning |
| 41 | string | `により自動生成されたコード` |  |
| 42 | string | `手動での編集は推奨しない` |  |
| 43 | string | `変更する場合は で行うこと` |  |
| 50 | comment | `セクションヘッダ定義` | definition |
| 52 | string | `インクルードファイル` |  |
| 53 | string | `型定義` | definition / type |
| 54 | string | `ユーザー定義型` | definition / type / user |
| 55 | string | `システム構造体` | system |
| 56 | string | `遷移コンテキスト` | transition / context |
| 57 | string | `保留イベント制御` | event |
| 58 | string | `層別型定義` | definition / type / layer |
| 59 | string | `関数宣言` | function |
| 60 | string | `ロール関数宣言` | role function / function |
| 61 | string | `ロール関数実装` | role function / function |
| 62 | string | `状態遷移テーブル` | state / transition |
| 63 | string | `セル単位遷移関数` | transition / function |
| 64 | string | `状態遷移関数` | state / transition / function |
| 65 | string | `イベント取得関数` | event / function |
| 66 | string | `初期化関数` | initialization / function |
| 67 | string | `変数アクセスマクロ` | variable |
| 68 | string | `スーパーインクルード` |  |
| ... | ... | （他 113 行）| |

### `codegen\enum_generator.py` （20 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `列挙型コード生成モジュール（多層ステートマシン対応版）` | type / layer |
| 5 | other | `修正` |  |
| 6 | other | `空名イベントを本体ループから除外` | event |
| 7 | other | `（ として先頭で処理済みのため 重複定義を防ぐ）` | definition |
| 32 | string | `列挙型コード生成クラス（多層ステートマシン対応）` | type / layer |
| 46 | string | `要素数（システム用）` | system |
| 222 | string | `層の状態定義 状態定義` | state / definition / layer |
| 243 | other | `イベント を生成（ を含む）` | event |
| 245 | other | `修正` |  |
| 246 | other | `空名イベント（完了遷移用の ）は として` | event / transition / completed |
| 247 | other | `先頭で定義されるため 本体ループから除外する` | definition |
| 248 | other | `これにより の重複定義を防ぐ` | definition |
| 253 | comment | `修正 空名イベントを除外` | event |
| 261 | string | `として処理済み` |  |
| 269 | string | `層のイベント定義 イベント定義` | event / definition / layer |
| 275 | other | `空名除外後を渡す` |  |
| 279 | string | `完了遷移` | transition / completed |
| 297 | string | `イベントフラグ定義` | event / definition / flag |
| 348 | string | `イベントフラグビットマスク定義` | event / definition / flag |
| 349 | string | `ビット単位でフラグを管理する場合に使用` | flag |

### `codegen\event_queue_generator.py` （26 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `イベントキューコード生成モジュール（完全データ駆動版）` | event / queue |
| 28 | string | `イベントキューコード生成クラス（完全データ駆動）` | event / queue |
| 37 | comment | `生成ステップ定義` | definition |
| 65 | comment | `ステップ実行辞書` | execute |
| 97 | comment | `名前生成` |  |
| 104 | comment | `構造体生成ステップ` |  |
| 109 | string | `イベントキュー` | event / queue |
| 142 | comment | `エンキュー生成ステップ` | queue |
| 148 | string | `イベントをエンキューする（ ）` | event / queue |
| 149 | string | `キュー` | queue |
| 150 | string | `イベント` | event |
| 151 | string | `成功 失敗` | success / failure |
| 166 | string | `イベントをデキューする（ ）` | event / queue |
| 167 | string | `キュー` | queue |
| 168 | string | `取り出したイベント` | event |
| 169 | string | `成功 失敗` | success / failure |
| 199 | string | `キュー満杯` | queue |
| 207 | string | `キュー空` | queue |
| 236 | comment | `公開メソッド` |  |
| 238 | string | `イベントキュー構造体生成` | event / queue |
| 249 | string | `エンキュー関数生成` | queue / function |
| 260 | string | `デキュー関数生成` | queue / function |
| 271 | string | `キュー関連の全コード生成` | queue |
| 282 | string | `全イベントキュー構造体生成` | event / queue |
| 290 | string | `全イベントキュー関数生成` | event / queue / function |
| 300 | string | `全イベントキューコード生成` | event / queue |

### `codegen\interrupt_generator.py` （47 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `割り込み処理 生成モジュール（ コンテキスト対応版）` | interrupt / context |
| 5 | other | `機能` |  |
| 6 | other | `ポインタの自動挿入（ ）` | pointer |
| 7 | other | `アクションの 変換` | action |
| 8 | other | `旧形式 変換` |  |
| 9 | other | `ユーザーマーカー` | marker / user |
| 10 | other | `の自動抽出` |  |
| 11 | other | `入場・退場ログ` |  |
| 13 | other | `マーカー命名規則` | marker |
| 40 | comment | `予約語（関数呼び出し形式で誤変換しないよう除外）` | function |
| 52 | string | `割り込み処理 生成クラス（ コンテキスト対応）` | interrupt / context |
| 55 | comment | `クラス定数` |  |
| 69 | comment | `生成ステップ` |  |
| 96 | string | `層名を設定（旧形式 の 名生成に使用）` | settings / layer |
| 104 | comment | `名前生成` |  |
| 117 | string | `ログ用表示名（元の名前そのまま）` |  |
| 121 | comment | `アクション パース` | action |
| 125 | other | `アクション文字列を コードに変換` | action |
| 128 | other | `入力アクション文字列` | action |
| 133 | other | `変換規則` |  |
| 136 | other | `それ以外 そのまま` |  |
| 146 | comment | `形式` |  |
| 159 | comment | `関数呼び出し形式` | function |
| 166 | comment | `既に で始まるものはそのまま` |  |
| 169 | comment | `キーワードはそのまま` |  |
| 172 | comment | `名に変換（引数は破棄）` | argument |
| 183 | comment | `そのまま` |  |
| 189 | string | `付きアクションを 行の コードに変換` | action |
| 193 | comment | `末尾セミコロンを正規化` |  |
| 201 | comment | `使用シンボル抽出` |  |
| ... | ... | （他 17 行）| |

### `codegen\osal_generator.py` （11 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `（ 抽象化レイヤ）コード生成モジュール（テンプレート分離版）` | layer |
| 24 | string | `コード生成クラス（テンプレート分離版）` |  |
| 33 | comment | `ヘッダ生成ステップ` |  |
| 46 | comment | `ソース生成ステップ` |  |
| 56 | comment | `ステップ実行辞書` | execute |
| 77 | comment | `ステップ実行関数` | execute / function |
| 196 | comment | `公開メソッド` |  |
| 198 | string | `ヘッダ生成` |  |
| 217 | string | `ソース生成` |  |
| 235 | string | `全コード生成` |  |
| 243 | string | `利用可能な 種別を取得` |  |

### `codegen\role_function_generator.py` （103 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `ロール関数生成モジュール（多層ステートマシン対応・ 対応版）` | role function / function / layer |
| 5 | other | `版 （ 遷移側 対応）` | transition |
| 6 | other | `が を保持` |  |
| 7 | other | `が 形式を検出` |  |
| 8 | other | `で 両対応の検索` |  |
| 10 | other | `追加` |  |
| 11 | other | `ガードを に追加` | guard |
| 12 | other | `等の 演算子混入参照を弾く` |  |
| 13 | other | `に未定義参照の警告ログを追加` | definition / warning |
| 15 | other | `追加` |  |
| 16 | other | `を追加（層フィルタ・案 ）` | layer |
| 17 | other | `で自層の関数と呼び出し元ありの関数のみ` | function / layer |
| 18 | other | `実装を出力するようフィルタ（空スタブ削減）` |  |
| 47 | comment | `追加 識別子検証用正規表現` |  |
| 56 | comment | `ヘルパー` |  |
| 81 | string | `つのロール関数呼び出しサイト（ ）` | role function / function |
| 100 | string | `ロール関数生成クラス（多層ステートマシン対応・ 対応）` | role function / function / layer |
| 103 | comment | `テーブル 宣言用テンプレート` |  |
| 108 | string | `ロール関数` | role function / function |
| 110 | string | `遷移コンテキスト（ 可 から呼ばれる場合）` | transition / context |
| 111 | string | `システムコンテキストポインタ` | system / context / pointer |
| 112 | string | `成功 以外 エラー（条件判定にも使用可）` | error / success / condition |
| 117 | string | `ロール関数` | role function / function |
| 118 | string | `遷移コンテキスト（ 可 から呼ばれる場合）` | transition / context |
| 119 | string | `システムコンテキストポインタ` | system / context / pointer |
| 120 | string | `成功 以外 エラー（条件判定にも使用可）` | error / success / condition |
| 132 | comment | `テーブル 実装用テンプレート（ ガード付き）` | guard |
| 137 | string | `ロール関数` | role function / function |
| 144 | string | `ロール関数` | role function / function |
| 156 | string | `ガード（ からの呼び出し対応）` | guard |
| ... | ... | （他 73 行）| |

### `codegen\struct_generator.py` （108 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `構造体コード生成モジュール（多層ステートマシン対応版）` | layer |
| 5 | other | `生成する構造体` |  |
| 6 | other | `ユーザー定義型（変更なし）` | definition / type / user |
| 7 | other | `グローバル変数（変更なし）` | variable |
| 8 | other | `イベントフラグ（変更なし）` | event / flag |
| 9 | other | `（ 追加）` |  |
| 10 | other | `共通 （ 新規・基底型）` | type |
| 11 | other | `（ 新規・層ごと）` | layer |
| 12 | other | `マクロ（ 新規）` |  |
| 14 | other | `設計方針` |  |
| 15 | other | `テンプレートは でデータテーブル化` |  |
| 16 | other | `は （層の 値を汎用保持）` | layer |
| 17 | other | `層ごとの と 共通の基底型 を両方提供` | type / layer |
| 43 | string | `構造体コード生成クラス（多層ステートマシン対応）` | layer |
| 46 | comment | `データテーブル 共通構造体テンプレート（ 等）` |  |
| 49 | comment | `セクションコメント` |  |
| 55 | comment | `開始` |  |
| 60 | comment | `メンバー` |  |
| 62 | string | `グローバル変数` | variable |
| 65 | string | `イベントフラグ` | event / flag |
| 68 | comment | `メンバー` |  |
| 70 | string | `保留中のイベント` | event |
| 73 | string | `保留イベント有効フラグ` | event / flag |
| 76 | comment | `終了（ に修正）` |  |
| 83 | comment | `データテーブル 共通マクロテンプレート` |  |
| 86 | comment | `セクションコメント` |  |
| 90 | string | `保留イベント制御` | event |
| 94 | comment | `マクロ` |  |
| 97 | string | `イベント発火マクロ` | event |
| 98 | string | `ロール関数内で使用` | role function / function |
| ... | ... | （他 78 行）| |

### `codegen\timer_generator.py` （16 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `タイマ変数生成モジュール（完全データ駆動版）` | variable / timer |
| 5 | other | `修正` |  |
| 6 | other | `を廃止` |  |
| 7 | other | `タイマ変数は 内に 経由で` | variable / timer |
| 8 | other | `既に展開されているため 未使用の を出力しない` |  |
| 33 | string | `タイマ変数生成クラス（完全データ駆動）` | variable / timer |
| 117 | string | `タイマ変数構造体 システム全体で使用するタイマ変数を管理` | variable / timer / system |
| 149 | string | `タイマ変数初期化` | initialization / variable / timer |
| 150 | string | `システムコンテキストポインタ` | system / context / pointer |
| 204 | string | `タイマ更新処理` | timer |
| 205 | string | `システムコンテキストポインタ` | system / context / pointer |
| 232 | other | `タイマ変数構造体生成` | variable / timer |
| 234 | other | `変更` |  |
| 235 | other | `タイマ変数は 内に既に展開されており` | variable / timer |
| 236 | other | `は使用されていなかった（ ）` |  |
| 237 | other | `後方互換のため関数自体は残すが 空文字列を返すように変更` | function |

### `codegen\transition_generator.py` （185 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `状態遷移関数生成モジュール（多層ステートマシン対応版）` | state / transition / function / layer |
| 5 | other | `生成物` |  |
| 6 | other | `セル単位の遷移関数（ 短縮名 ）` | transition / function |
| 7 | other | `前方宣言（プロトタイプ）` |  |
| 8 | other | `実装本体` |  |
| 9 | other | `遷移テーブル（グローバル 宣言付き）` | transition |
| 10 | other | `関数ディクショナリ（デバッグ・リフレクション用）` | function / debug |
| 11 | other | `関数` | function |
| 12 | other | `関数` | function |
| 14 | other | `設計方針` |  |
| 15 | other | `遷移テーブルは外部から参照可能（グローバル）` | transition |
| 16 | other | `セル関数は （内部実装詳細）` | function |
| 17 | other | `セル関数は前方宣言してから テーブル・実装を出力（順序非依存）` | function |
| 18 | other | `テーブルは行 状態 列 イベントの横並び仕様書形式` | state / event |
| 20 | other | `修正` |  |
| 21 | other | `形式（例 ）を` |  |
| 22 | other | `正しく に変換` |  |
| 23 | other | `旧 コンパイルエラー` | error |
| 24 | other | `新 正しい` |  |
| 51 | comment | `ヘルパー` |  |
| 54 | string | `文字列 リストを に正規化` |  |
| 66 | string | `状態遷移関数生成クラス（多層ステートマシン対応）` | state / transition / function / layer |
| 68 | comment | `セル関数の短縮名を使うか（ のため推奨 ）` | function |
| 71 | comment | `遷移テーブルの最小列幅` | transition |
| 74 | comment | `デフォルト設定値` | settings |
| 79 | comment | `テンプレート群` |  |
| 82 | comment | `ヘッダーコメント` |  |
| 85 | string | `セル遷移` | transition |
| 89 | comment | `関数シグネチャ` | function |
| 98 | comment | `状態変数初期化` | state / initialization / variable |
| ... | ... | （他 155 行）| |

### `codegen\validate\prompt_generator.py` （12 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `プロンプト生成クラス` |  |
| 6 | other | `を削除（未使用・呼び出し元なし）` |  |
| 23 | string | `プロンプト生成クラス` |  |
| 34 | string | `状態` | state |
| 37 | string | `イベント` | event |
| 40 | string | `遷移` | transition |
| 45 | string | `条件` | condition |
| 47 | string | `アクション` | action |
| 50 | string | `遷移なし` | transition |
| 51 | string | `初期状態 未設定` | state / settings |
| 56 | string | `内部検証結果 問題なし` |  |
| 57 | string | `内部検証で検出された問題` |  |

### `codegen\variable_generator.py` （60 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `変数・フラグ生成モジュール（多層ステートマシン対応版）` | variable / flag / layer |
| 5 | other | `修正` |  |
| 6 | other | `でカスタム構造体変数を で初期化` | initialization / variable |
| 7 | other | `（ までは でコンパイルエラー）` | error |
| 9 | other | `修正` |  |
| 10 | other | `アクセスマクロのフィールド名を修正` |  |
| 11 | other | `バグ` |  |
| 12 | other | `修正後` |  |
| 13 | other | `マクロ名は大文字（ ） フィールド名は を使用` |  |
| 15 | other | `修正` |  |
| 16 | other | `サフィックス付き標準型（ 等）を正しく認識` | type |
| 17 | string | `旧 に はあるが がない` |  |
| 18 | other | `標準型がカスタム型扱いされて冗長な を生成` | type |
| 19 | other | `新 に 付き型を追加` | type |
| 20 | other | `で 修飾子を除去してから判定` |  |
| 50 | string | `変数・フラグ生成クラス（多層ステートマシン対応）` | variable / flag / layer |
| 55 | string | `システムコンテキスト初期化` | initialization / system / context |
| 56 | string | `システムコンテキストポインタ` | system / context / pointer |
| 64 | string | `チェック` |  |
| 74 | string | `グローバル変数の初期化` | initialization / variable |
| 77 | string | `イベントフラグの初期化` | event / initialization / flag |
| 80 | string | `保留イベントの初期化` | event / initialization |
| 118 | comment | `修正 サフィックス付き標準型を追加` | type |
| 119 | comment | `の と整合` |  |
| 120 | comment | `に変換されるため` |  |
| 121 | comment | `生成コード側でも を標準型として扱う必要がある` | type |
| 124 | comment | `符号付き整数` |  |
| 128 | comment | `符号なし整数` |  |
| 132 | comment | `浮動小数` |  |
| 134 | comment | `真偽 文字` |  |
| ... | ... | （他 30 行）| |

## カテゴリ B: GUI 表示文言（最優先）

### `statable_gui\__init__.py` （12 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `層` | layer |
| 5 | other | `追加` |  |
| 6 | other | `再エクスポートは最小限に留める` |  |
| 7 | other | `依存の重いモジュール（ 等）は` |  |
| 8 | other | `明示的に することを推奨` |  |
| 11 | comment | `設定・環境` | settings |
| 14 | comment | `ロガー（軽量・依存小）` |  |
| 26 | comment | `注意` |  |
| 27 | comment | `等は再エクスポートしない` |  |
| 28 | comment | `の 生成前にロードするとエラーの原因になるため` | error |
| 29 | comment | `利用側で と` |  |
| 30 | comment | `明示的に すること` |  |

### `statable_gui\action_edit_dialog.py` （17 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 18 | string | `遷移の動作を編集するダイアログ（ 挿入対応）` | transition |
| 23 | string | `動作編集` |  |
| 41 | string | `ロール関数` | role function / function |
| 45 | string | `挿入` |  |
| 48 | string | `新規ロール関数` | role function / function |
| 70 | string | `動作コード` |  |
| 104 | comment | `を優先表示` |  |
| 116 | comment | `変更 を使用` |  |
| 119 | other | `ロール関数を動作欄に挿入` | role function / function |
| 121 | other | `あり の参照形式（引数なし）` | argument |
| 122 | other | `なし 旧形式 を維持` |  |
| 135 | comment | `形式 参照のみ挿入` |  |
| 138 | comment | `旧形式 引数付き呼び出しを維持` | argument |
| 151 | string | `警告 同名のロール関数が既に存在します` | role function / function / warning |
| 165 | string | `をグローバル変数として登録` | variable |
| 166 | string | `をイベントフラグとして登録` | event / flag |
| 203 | string | `無題動作` |  |

### `statable_gui\code_generation_dialog.py` （91 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `コード生成ダイアログ（ 対応・複数層対応版）` | layer |
| 21 | comment | `パス設定` | settings |
| 47 | comment | `設定ダイアログをインポート` | settings |
| 59 | comment | `デフォルト設定ファイルパス` | settings |
| 67 | comment | `警告収集クラス` | warning |
| 71 | other | `以上のログを収集するハンドラ` |  |
| 78 | other | `処理` |  |
| 103 | string | `コード生成ダイアログ（複数層対応）` | layer |
| 119 | comment | `複数層リスト（外部から設定）` | settings / layer |
| 124 | string | `コード生成` |  |
| 131 | comment | `設定読み書き` | settings |
| 151 | string | `前回の設定を読み込みました` | settings |
| 153 | string | `設定読み込みに失敗` | failure / settings |
| 156 | string | `現在の設定を保存` | settings |
| 174 | string | `設定を保存しました` | settings |
| 176 | string | `設定保存に失敗` | failure / settings |
| 180 | string | `を構築` |  |
| 183 | comment | `設定情報グループ` | settings / info |
| 184 | string | `生成設定情報` | settings / info |
| 187 | comment | `出力先` |  |
| 190 | string | `出力先ディレクトリを選択` |  |
| 193 | string | `参照` |  |
| 200 | string | `出力先` |  |
| 202 | comment | `生成スタイル` |  |
| 205 | string | `テーブル駆動方式` |  |
| 207 | string | `方式` |  |
| 210 | string | `生成スタイル` |  |
| 212 | comment | `種別ラベル` |  |
| 214 | string | `種別` |  |
| 216 | comment | `マージ設定ラベル` | settings |
| ... | ... | （他 61 行）| |

### `statable_gui\code_generation_settings_dialog.py` （131 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `コード生成設定ダイアログ` | settings |
| 4 | other | `基本設定 ログ設定 外部インクルード 出力設定のタブ構成` | settings |
| 5 | other | `生成方式・テーブル方式は固定（テーブル駆動 配列方式のみ）` |  |
| 22 | comment | `パス設定` | settings |
| 35 | string | `コード生成設定ダイアログ` | settings |
| 42 | string | `コード生成設定` | settings |
| 49 | string | `を構築` |  |
| 52 | comment | `タブウィジェット` |  |
| 56 | comment | `タブ` |  |
| 59 | string | `基本設定` | settings |
| 61 | comment | `ログ設定タブ` | settings |
| 64 | string | `ログ設定` | settings |
| 66 | comment | `出力設定タブ` | settings |
| 69 | string | `外部インクルード` |  |
| 73 | string | `出力設定` | settings |
| 75 | comment | `ボタン` |  |
| 79 | string | `リセット` |  |
| 83 | string | `キャンセル` |  |
| 94 | string | `基本設定タブ` | settings |
| 97 | comment | `プロジェクト名` |  |
| 98 | string | `プロジェクト設定` | settings |
| 102 | string | `例` |  |
| 103 | string | `生成ファイル名 に使用されます` |  |
| 104 | string | `プロジェクト名` |  |
| 108 | comment | `生成スタイル（固定表示）` |  |
| 109 | string | `生成スタイル` |  |
| 112 | comment | `生成方式 固定` |  |
| 113 | string | `テーブル駆動方式（セル単位関数 関数テーブル）` | function |
| 115 | string | `生成方式` |  |
| 117 | comment | `テーブル方式 固定` |  |
| ... | ... | （他 101 行）| |

### `statable_gui\common_widgets.py` （61 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 1 | string | `共通 コンポーネント` |  |
| 19 | string | `タイトル入力ウィジェット` | title |
| 21 | string | `一覧に表示されるラベル（空なら自動設定）` | settings |
| 26 | string | `タイトル` | title |
| 33 | string | `この項目のタイトルを入力してください 空の場合は自動で仮タイトルが設定されます` | settings / title |
| 49 | string | `型選択用コンボボックス` | type |
| 63 | string | `追加` |  |
| 64 | string | `ユーザー定義型を追加・編集` | definition / type / user |
| 103 | string | `グループ選択用コンボボックス` |  |
| 117 | string | `追加` |  |
| 118 | string | `新しいグループを追加` |  |
| 153 | string | `イベント選択用コンボボックス` | event |
| 165 | string | `状態選択用コンボボックス` | state |
| 176 | string | `グループ追加ダイアログ` |  |
| 180 | string | `グループ追加` |  |
| 188 | string | `新しいグループ名を入力` |  |
| 189 | string | `グループ名` |  |
| 198 | string | `警告 グループ名を入力してください` | warning |
| 207 | string | `ユーザー定義型管理ダイアログ` | definition / type / user |
| 212 | string | `ユーザー定義型管理` | definition / type / user |
| 218 | string | `タイトル 型名 メンバ数` | title / type |
| 227 | string | `追加` |  |
| 229 | string | `編集` |  |
| 231 | string | `削除` |  |
| 239 | string | `閉じる` |  |
| 269 | string | `警告 型名を入力してください` | type / warning |
| 272 | string | `警告 型 は既に存在します` | type / warning |
| 286 | string | `警告 型名を入力してください` | type / warning |
| 300 | string | `確認 型 を削除しますか？` | type |
| 310 | string | `ユーザー定義型編集ダイアログ` | definition / type / user |
| ... | ... | （他 31 行）| |

### `statable_gui\condition_builder_dialog.py` （50 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `遷移条件ビルダーダイアログ（リテラル化対応・イベント名編集欄追加・遷移先ステート指定対応）` | event / transition / condition |
| 10 | comment | `パス設定` | settings |
| 28 | comment | `共有リテラルライブラリ` |  |
| 31 | string | `遷移条件式を で構築するダイアログ` | transition / condition |
| 38 | other | `追加：現在の遷移先` | transition |
| 39 | other | `追加：現在の 遷移先` | transition |
| 42 | string | `遷移条件ビルダー` | transition / condition |
| 50 | comment | `遷移先ステート選択肢（外部から渡されたリスト なければステートマシンから取得）` | transition |
| 56 | comment | `構築後に現在値をコンボボックスへ反映` |  |
| 64 | string | `ステートマシンから状態名リストを取得` | state |
| 74 | comment | `イベント名編集欄` | event |
| 76 | string | `イベント名` | event |
| 81 | comment | `遷移先ステート選択` | transition |
| 83 | string | `遷移先` | transition |
| 85 | other | `未設定用` | settings |
| 90 | comment | `遷移先ステート選択` | transition |
| 92 | string | `遷移先` | transition |
| 94 | other | `未設定用` | settings |
| 101 | comment | `左ペイン` |  |
| 102 | string | `挿入するシンボル` |  |
| 114 | string | `数値リテラル` |  |
| 115 | string | `挿入` |  |
| 123 | comment | `右ペイン` |  |
| 124 | string | `条件式（シンボル名で記述）` | condition |
| 129 | comment | `リテラル化ボタン` |  |
| 130 | string | `リテラル化` |  |
| 135 | string | `例` |  |
| 147 | comment | `クリアボタン` |  |
| 148 | string | `クリア` |  |
| 159 | comment | `下部： 形式の コード表示` |  |
| ... | ... | （他 20 行）| |

### `statable_gui\condition_edit_dialog.py` （15 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 16 | string | `状態遷移条件を編集するダイアログ` | state / transition / condition |
| 20 | string | `状態遷移条件編集` | state / transition / condition |
| 32 | comment | `タイトル入力ウィジェット` | title |
| 36 | comment | `ロール関数選択・挿入バー` | role function / function |
| 38 | string | `ロール関数` | role function / function |
| 42 | string | `挿入` |  |
| 47 | comment | `左右分割` |  |
| 51 | comment | `左側：シンボルピッカー` |  |
| 59 | comment | `右側：条件式編集` | condition |
| 62 | string | `条件式` | condition |
| 69 | comment | `論理演算子コンボ` |  |
| 71 | string | `論理演算子` |  |
| 104 | string | `ボタン：タイトルが空なら仮タイトルを自動設定` | settings / title |
| 107 | comment | `条件式の先頭 文字を仮タイトルに` | title / condition |
| 111 | string | `無題条件` | condition |

### `statable_gui\config.py` （1 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 4 | comment | `ウィンドウ・プレビューのサイズ定数` |  |

### `statable_gui\dialogs.py` （42 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `遷移編集ダイアログ（ 編集対応 条件ビルダー直接起動対応）` | transition / start / condition |
| 20 | comment | `エディタ連携` |  |
| 24 | comment | `条件ビルダー` | condition |
| 29 | string | `ダブルクリックイベントを確実に捕捉するためのテーブル` | event |
| 48 | string | `セル内の複数の遷移を一括編集するダイアログ（ 編集対応 条件ビルダー直接起動）` | transition / start / condition |
| 54 | string | `遷移編集（ ビジュアル編集）` | transition |
| 63 | string | `イベント 完了遷移` | event / transition / completed |
| 66 | string | `タイトル 状態遷移条件 動作 遷移先 表示タイトル` | state / transition / title / condition |
| 75 | string | `行追加` |  |
| 77 | string | `行削除` |  |
| 79 | string | `上へ` |  |
| 81 | string | `下へ` |  |
| 84 | string | `編集` |  |
| 85 | string | `選択中の行をビジュアルエディタで編集します` |  |
| 110 | comment | `ダブルクリック処理` |  |
| 113 | string | `列に応じて編集ダイアログを切り替える` |  |
| 115 | comment | `状態遷移条件列 条件ビルダー` | state / transition / condition |
| 118 | comment | `動作列 表示タイトル列 エディタ` | title |
| 121 | comment | `その他は何もしない` |  |
| 125 | string | `条件ビルダーを開いて条件式を編集する` | condition |
| 140 | other | `シンボル名テキスト` |  |
| 147 | string | `指定行に対して エディタを開く` |  |
| 152 | comment | `編集` |  |
| 157 | string | `警告 編集する行を選択してください` | warning |
| 190 | other | `変換` |  |
| 192 | other | `変更 を渡す（ ）` |  |
| 193 | other | `がこれを最優先で参照するため` |  |
| 194 | other | `ここで の層名を明示的に引き継ぐ` | layer |
| 196 | comment | `の を取得（空ならフォールバックに任せる）` |  |
| 202 | other | `追加` |  |
| ... | ... | （他 12 行）| |

### `statable_gui\event_definition_dialog.py` （57 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 1 | string | `状態遷移イベント定義ダイアログ` | state / event / transition / definition |
| 22 | string | `ダブルクリックを捕捉するテーブル` |  |
| 38 | string | `状態遷移イベント編集ダイアログ` | state / event / transition |
| 43 | string | `状態遷移イベント編集` | state / event / transition |
| 50 | comment | `タイトル入力欄（必須・仮タイトル自動設定）` | settings / title |
| 54 | comment | `イベント名` | event |
| 56 | string | `イベント名` | event |
| 58 | comment | `イベント` | event |
| 63 | string | `イベント` | event |
| 65 | comment | `説明` | description |
| 67 | string | `説明` | description |
| 69 | comment | `イベント種類` | event |
| 77 | string | `イベント種類` | event |
| 79 | comment | `発生源レイヤ` | layer |
| 80 | string | `ドライバ層` | layer / driver |
| 81 | string | `ミドル層` | layer |
| 93 | string | `発生源レイヤ` | layer |
| 95 | comment | `配送タイプ` |  |
| 104 | string | `配送タイプ` |  |
| 106 | comment | `付随データ` |  |
| 107 | string | `付随データを使用する` |  |
| 114 | string | `データ型` | type |
| 117 | string | `データ変数名` | variable |
| 135 | string | `ボタン：タイトルが空なら仮タイトルを自動設定` | settings / title |
| 136 | string | `イベント 無名` | event |
| 158 | string | `状態遷移イベント定義一覧ダイアログ` | state / event / transition / definition |
| 164 | string | `状態遷移イベント定義` | state / event / transition / definition |
| 169 | comment | `検索` |  |
| 171 | string | `検索（前方一致）` |  |
| 173 | string | `タイトル・イベント名・説明` | event / title / description |
| ... | ... | （他 27 行）| |

### `statable_gui\event_delivery_settings_dialog.py` （31 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 1 | string | `イベント配送設定ダイアログ` | event / settings |
| 18 | string | `ダブルクリックを捕捉するテーブル` |  |
| 33 | string | `イベント配送タイプ（ ）を設定し 使用状況に応じて 自動変換を表示するダイアログ` | event / settings |
| 40 | string | `イベント配送設定` | event / settings |
| 45 | comment | `グローバル設定チェックボックス` | settings |
| 46 | string | `で使用される イベントを に自動変換する` | event |
| 50 | comment | `イベント一覧テーブル` | event |
| 52 | string | `タイトル イベント名 発生源 配送タイプ 使用 変換後` | event / title |
| 57 | comment | `ヘルプ` |  |
| 59 | string | `イベントが から通知される場合 自動的に へ変換されます` | event |
| 60 | string | `イベントの回数やデータが必要な場合は を選択してください` | event |
| 77 | string | `テーブルを構築する` |  |
| 83 | comment | `タイトル（読み取り専用）` | title |
| 88 | comment | `イベント名（読み取り専用）` | event |
| 89 | string | `（完了）` | completed |
| 93 | comment | `発生源（読み取り専用）` |  |
| 98 | comment | `配送タイプコンボ` |  |
| 109 | comment | `使用列（読み取り専用）` |  |
| 111 | string | `あり` |  |
| 115 | comment | `変換後列（読み取り専用）` |  |
| 125 | string | `割り込み処理からイベントが使用されているか判定する` | event / interrupt |
| 130 | comment | `リストをチェック` |  |
| 135 | comment | `内のコードをチェック` |  |
| 145 | string | `イベント名から行番号を探す` | event |
| 153 | string | `配送タイプコンボ変更時に変換後列を更新` |  |
| 157 | string | `変換後列を現在の設定から再計算して表示する` | settings |
| 162 | string | `（完了）` | completed |
| 169 | string | `あり` |  |
| 178 | string | `ボタン：各イベントの配送タイプを更新して閉じる` | event |
| 182 | string | `（完了）` | completed |
| ... | ... | （他 1 行）| |

### `statable_gui\event_queue_dialog.py` （42 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 1 | string | `イベントキュー定義ダイアログ` | event / definition / queue |
| 39 | string | `イベントキュー編集` | event / queue |
| 46 | comment | `タイトル入力欄（必須・仮タイトル自動設定）` | settings / title |
| 50 | comment | `キュー名` | queue |
| 52 | string | `キュー名` | queue |
| 54 | comment | `サイズ` |  |
| 58 | string | `サイズ` |  |
| 60 | comment | `要素型` | type |
| 64 | string | `要素型` | type |
| 66 | comment | `関連イベント選択リスト` | event |
| 73 | string | `関連イベント` | event |
| 75 | comment | `優先度付き` | priority |
| 78 | string | `優先度付き` | priority |
| 80 | comment | `割込保護` |  |
| 83 | string | `割込保護` |  |
| 85 | comment | `使用` |  |
| 88 | string | `使用` |  |
| 90 | comment | `説明` | description |
| 92 | string | `説明` | description |
| 102 | string | `ボタン：タイトルが空なら仮タイトルを自動設定` | settings / title |
| 103 | string | `キュー 無名` | queue |
| 127 | string | `イベントキュー定義一覧ダイアログ` | event / definition / queue |
| 132 | string | `イベントキュー定義` | event / definition / queue |
| 137 | comment | `検索` |  |
| 139 | string | `検索（前方一致）` |  |
| 141 | string | `タイトル・キュー名・説明` | queue / title / description |
| 146 | comment | `一覧テーブル（タイトル列追加・直接編集可能）` | title |
| 148 | string | `タイトル キュー名 サイズ 要素型 関連イベント 優先度 割込保護 説明` | event / queue / title / description / type / priority |
| 154 | comment | `ボタン` |  |
| 156 | string | `追加` |  |
| ... | ... | （他 12 行）| |

### `statable_gui\global_defs.py` （22 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 1 | string | `グローバル変数・イベントフラグ・割り込み処理・デバイスリソース・タイマ設定のデータモデル` | event / settings / variable / flag / interrupt / timer |
| 9 | string | `システム全体で共有するグローバル変数` | variable / system |
| 20 | string | `変数` | variable |
| 25 | string | `ビットフィールドで扱うイベントフラグ` | event / flag |
| 35 | string | `フラグ` | flag |
| 46 | string | `割り込み処理内の条件付きアクション` | interrupt / condition / action |
| 53 | string | `割り込み処理定義` | definition / interrupt |
| 63 | string | `割り込み` | interrupt |
| 68 | string | `デバイスリソース仮定義` | definition |
| 75 | string | `デバイス` |  |
| 80 | string | `派生タイマ変数定義` | definition / variable / timer |
| 89 | string | `タイマ` | timer |
| 94 | string | `タイマ刻み変数定義` | definition / variable / timer |
| 100 | other | `このタイマを駆動する割り込み名` | interrupt / timer |
| 104 | string | `タイマ基準` | timer |
| 109 | string | `イベントキュー定義` | event / definition / queue |
| 122 | string | `キュー` | queue |
| 126 | string | `グローバル変数・イベントフラグ・割り込み処理・デバイスリソース・タイマ設定・イベントキューの管理クラス` | event / settings / variable / flag / interrupt / timer / que |
| 134 | other | `追加タイマ基準` | timer |
| 138 | string | `全タイマ基準変数・派生タイマ変数をグローバル変数として登録する` | variable / timer |
| 149 | string | `タイマ基準変数` | variable / timer |
| 159 | string | `派生タイマ変数（ ）` | variable / timer |

### `statable_gui\global_defs_dialog.py` （53 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 1 | string | `グローバル変数・イベントフラグ定義管理画面` | event / definition / variable / flag |
| 60 | string | `行を追加` |  |
| 75 | string | `グローバル変数編集` | variable |
| 84 | string | `名前` |  |
| 89 | string | `型` | type |
| 91 | string | `配列を使用する` |  |
| 98 | string | `配列サイズ` |  |
| 104 | string | `単位` |  |
| 107 | string | `初期値` |  |
| 112 | string | `グループ` |  |
| 115 | string | `説明` | description |
| 126 | string | `変数 無名` | variable |
| 128 | string | `無名` |  |
| 150 | string | `イベントフラグ編集` | event / flag |
| 159 | string | `フラグ名` | flag |
| 164 | string | `最小値` |  |
| 169 | string | `最大値` |  |
| 175 | string | `ビット幅` |  |
| 180 | string | `グループ` |  |
| 183 | string | `説明` | description |
| 194 | string | `エラー 最大値 最小値` | error |
| 202 | string | `フラグ 無名` | flag |
| 218 | string | `グローバル変数 一括登録ダイアログ` | variable |
| 224 | string | `グローバル変数 一括登録` | variable |
| 229 | string | `タイトル 名前 型 配列 単位 初期値 グループ 説明` | title / description / type |
| 241 | string | `行追加` |  |
| 243 | string | `行削除` |  |
| 308 | string | `変数` | variable |
| 332 | string | `変数` | variable |
| 338 | string | `イベントフラグ 一括登録ダイアログ` | event / flag |
| ... | ... | （他 23 行）| |

### `statable_gui\interrupt_handler_edit_dialog.py` （98 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 1 | string | `割り込み処理・デバイスリソース・タイマ設定の管理ダイアログ（複数タイマ対応版・ 対応）` | settings / interrupt / timer |
| 57 | string | `割り込み処理編集` | interrupt |
| 65 | string | `割り込み処理編集` | interrupt |
| 76 | string | `一覧に表示されるラベル（空なら自動設定）` | settings |
| 77 | string | `この割り込み処理のタイトルを入力してください 空の場合は自動で仮タイトルが設定されます` | settings / interrupt / title |
| 78 | string | `タイトル` | title |
| 83 | string | `割り込み名を入力してください（例： ）` | interrupt |
| 84 | string | `割り込み名` | interrupt |
| 89 | string | `この割り込み処理の説明を入力してください` | interrupt / description |
| 90 | string | `説明` | description |
| 100 | string | `から通知する状態遷移イベント名を選択または入力してください` | state / event / transition |
| 101 | string | `新しいイベント名を入力すると そのまま登録されます` | event |
| 103 | string | `イベント名` | event |
| 107 | string | `タイマ割り込みの場合にチェックしてください` | interrupt / timer |
| 108 | string | `タイマ割り込み` | interrupt / timer |
| 110 | string | `条件付きアクション一覧` | condition / action |
| 112 | string | `各行に 状態遷移条件 と 動作コード を記述します` | state / transition / condition |
| 113 | string | `状態遷移条件が空の場合は無条件で動作が実行されます` | state / transition / execute / condition |
| 114 | string | `ダブルクリックで各セルを編集できます` |  |
| 120 | string | `状態遷移条件 動作コード` | state / transition / condition |
| 126 | string | `行追加` |  |
| 128 | string | `行削除` |  |
| 153 | string | `ダブルクリックで状態遷移条件を編集` | state / transition / condition |
| 158 | string | `ダブルクリックで動作コードを編集` |  |
| 204 | string | `割り込み 無名` | interrupt |
| 209 | comment | `を自動抽出` |  |
| 236 | comment | `使用ロール関数・変数を自動抽出` | role function / variable / function |
| 258 | string | `デバイスリソース仮定義編集` | definition |
| 266 | string | `一覧に表示されるラベル（空なら自動設定）` | settings |
| 267 | string | `タイトル` | title |
| ... | ... | （他 68 行）| |

### `statable_gui\layer_settings_dialog.py` （28 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `レイヤ設定ダイアログ` | settings / layer |
| 4 | other | `各タブ（層）の実行優先度・層名を一括設定` | execute / settings / layer / priority |
| 23 | string | `レイヤ設定ダイアログ` | settings / layer |
| 34 | string | `レイヤ設定` | settings / layer |
| 43 | comment | `説明` | description |
| 44 | string | `設定項目について` | settings |
| 48 | string | `・層名 生成コードの識別子に使用（例` | layer |
| 49 | string | `）` |  |
| 50 | string | `空欄にすると層名なし版（ ）が生成されます` | layer |
| 51 | string | `・優先度 の範囲 （低）が最初に実行・初期化` | initialization / execute / priority |
| 52 | string | `・タブ名 表示用の名前（変更はタブ名変更メニューから）` |  |
| 59 | comment | `層一覧テーブル（ 列）` | layer |
| 62 | string | `タブ名 層名 優先度 説明` | description / layer / priority |
| 81 | comment | `ボタン` |  |
| 85 | string | `キャンセル` |  |
| 98 | comment | `優先度の昇順でソート` | priority |
| 105 | comment | `タブ名（編集不可）` |  |
| 112 | comment | `層名（編集可）` | layer |
| 117 | comment | `優先度（スピンボックス）` | priority |
| 124 | comment | `説明` | description |
| 132 | comment | `優先度の重複チェック` | priority |
| 141 | string | `確認` |  |
| 142 | string | `優先度が重複しています このまま続けますか？` | priority |
| 151 | string | `設定を各 に反映` | settings |
| 155 | comment | `対応する を検索` |  |
| 165 | comment | `層名` | layer |
| 170 | comment | `優先度` | priority |
| 175 | comment | `説明` | description |

### `statable_gui\libcntrl\__init__.py` （1 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `共有ライブラリ管理パッケージ` |  |

### `statable_gui\libcntrl\condition_library.py` （5 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `共有遷移条件ライブラリ` | transition / condition |
| 12 | string | `共有遷移条件テンプレート` | transition / condition |
| 13 | other | `テンプレート名` |  |
| 14 | other | `条件式（リテラル名含む）` | condition |
| 34 | string | `プロジェクト全体で共有する遷移条件ライブラリ` | transition / condition |

### `statable_gui\libcntrl\literal_library.py` （5 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `共有リテラルライブラリ` |  |
| 12 | string | `共有リテラル定義` | definition |
| 13 | other | `一意なリテラル名` |  |
| 14 | other | `値` |  |
| 37 | string | `プロジェクト全体で共有するリテラルライブラリ` |  |

### `statable_gui\libcntrl\literal_management_dialog.py` （25 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `リテラル管理ダイアログ（表形式・編集修正版）` |  |
| 17 | string | `共有リテラルの管理ダイアログ（表形式）` |  |
| 23 | string | `リテラル管理` |  |
| 33 | string | `名前 値 型 説明` | description / type |
| 41 | string | `追加` |  |
| 43 | string | `編集` |  |
| 45 | string | `削除` |  |
| 52 | string | `閉じる` |  |
| 87 | string | `警告` | warning |
| 92 | string | `情報 編集するリテラルを選択してください` | info |
| 103 | comment | `編集時は常に旧エントリを削除してから追加する` |  |
| 109 | comment | `失敗した場合は元に戻す` | failure |
| 111 | string | `警告` | warning |
| 116 | string | `情報 削除するリテラルを選択してください` | info |
| 121 | string | `確認` |  |
| 122 | string | `リテラル を削除しますか？` |  |
| 123 | string | `このリテラルを使用している遷移条件がある場合は` | transition / condition |
| 124 | string | `該当の条件式からも削除する必要があります` | condition |
| 133 | string | `リテラルの追加・編集用ダイアログ` |  |
| 139 | string | `リテラル編集 リテラル追加` |  |
| 148 | string | `名前` |  |
| 153 | string | `値` |  |
| 158 | string | `型` | type |
| 163 | string | `説明` | description |
| 175 | string | `警告 名前を入力してください` | warning |

### `statable_gui\libcntrl\role_function_edit_dialog.py` （12 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `ロール関数編集ダイアログ` | role function / function |
| 18 | string | `共有ロール関数の編集ダイアログ` | role function / function |
| 31 | string | `ロール関数編集` | role function / function |
| 42 | string | `関数名` | function |
| 44 | string | `表示名` |  |
| 46 | string | `説明` | description |
| 49 | comment | `使用グローバル変数` | variable |
| 50 | string | `使用グローバル変数` | variable |
| 62 | comment | `使用イベント` | event |
| 63 | string | `使用イベント` | event |
| 75 | comment | `使用リテラル` |  |
| 76 | string | `使用リテラル（既存から選択）` |  |

### `statable_gui\libcntrl\role_function_library.py` （14 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `共有ロール関数ライブラリ` | role function / function |
| 12 | other | `共有ロール関数定義` | role function / definition / function |
| 14 | other | `層名・機能グループ名（例 ）` | layer |
| 15 | other | `のように参照可能` |  |
| 16 | other | `空文字の場合は層なし扱い` | layer |
| 18 | other | `純粋名（例 ）` |  |
| 19 | string | `名前空間（例 ）` | namespace |
| 32 | string | `表示用 または` |  |
| 62 | string | `プロジェクト全体で共有するロール関数ライブラリ` | role function / function |
| 68 | string | `ライブラリ内での一意キー` |  |
| 78 | string | `は でも純粋名でも` |  |
| 82 | comment | `純粋名での検索` |  |
| 89 | string | `は でも純粋名でも` |  |
| 113 | other | `重複は無視` | ignore |

### `statable_gui\logger.py` （1 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 7 | string | `専用ロガー（シングルトン）` |  |

### `statable_gui\main_window.py` （111 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `メインウィンドウ` |  |
| 4 | other | `コード生成機能・検証 連携機能・共有ライブラリ管理を統合` |  |
| 5 | other | `（複数層対応版）` | layer |
| 7 | other | `修正` |  |
| 8 | other | `の 登録で を渡す（バグ ）` |  |
| 45 | comment | `共有ライブラリ（ に統合済）` |  |
| 52 | comment | `コード生成モジュール` |  |
| 78 | comment | `検証・ 連携モジュール` |  |
| 93 | comment | `環境設定` | settings |
| 96 | comment | `コード生成設定マネージャ` | settings |
| 99 | comment | `グローバル変数・イベントフラグ・割り込み・` | event / variable / flag / interrupt |
| 100 | comment | `デバイス・タイマ設定` | settings / timer |
| 112 | comment | `共有ライブラリ（プロジェクト全体で共有）` |  |
| 117 | comment | `サンプルステートマシンから共有ライブラリへデータ登録` |  |
| 121 | comment | `修正 ロール関数を共有ライブラリへ登録` | role function / function |
| 122 | comment | `も渡す（ ）` |  |
| 133 | other | `追加` |  |
| 150 | comment | `条件テンプレートを追加` | condition |
| 165 | comment | `リテラルを追加` |  |
| 170 | string | `リトライ回数閾値` | retry / threshold |
| 174 | string | `最小電圧` |  |
| 181 | comment | `デバッグログ 共有ライブラリの内容を出力` | debug |
| 195 | comment | `ボタン` |  |
| 205 | comment | `ダブルクリックでタブ名変更` |  |
| 217 | comment | `初期タブ` |  |
| 225 | comment | `ツールバー` |  |
| 228 | string | `メインツールバー` |  |
| 233 | string | `グローバル定義` | definition |
| 235 | string | `グローバル変数・イベントフラグ定義を開く` | event / definition / variable / flag |
| 240 | string | `型定義` | definition / type |
| ... | ... | （他 81 行）| |

### `statable_gui\matrix_table.py` （26 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `状態遷移表ウィジェット（ エディタ直接起動対応）` | state / transition / start |
| 41 | string | `タイトル` | title |
| 42 | string | `遷移先 内部` | transition |
| 44 | string | `イベント` | event |
| 46 | string | `イベント 完了遷移` | event / transition / completed |
| 48 | string | `状態遷移条件` | state / transition / condition |
| 76 | comment | `デバッグログ 初期化時の共有ライブラリ内容` | initialization / debug |
| 109 | string | `完了` | completed |
| 127 | string | `遷移なし` | transition |
| 152 | string | `無題遷移` | transition |
| 158 | string | `内部` |  |
| 171 | string | `内部` |  |
| 178 | other | `遷移編集ダイアログを開く` | transition |
| 180 | other | `変更 に を渡す（ ）` |  |
| 181 | other | `がこれを最優先で参照するため` |  |
| 182 | other | `ここで の層名を明示的に引き継ぐ` | layer |
| 191 | string | `完了` | completed |
| 202 | comment | `の を取得（空なら 側のフォールバックに任せる）` |  |
| 208 | other | `追加` |  |
| 215 | comment | `共有ライブラリ 現在の のロール関数をマージ` | role function / function |
| 216 | comment | `（共有ライブラリが空でも のローカル関数を選べるようにする）` | function |
| 217 | comment | `以降 ロール関数は （ 等）で扱う` | role function / function |
| 221 | comment | `共有ライブラリから` |  |
| 228 | comment | `現在の のロール関数から` | role function / function |
| 237 | comment | `デバッグログ に渡す内容` | debug |
| 276 | string | `完了` | completed |

### `statable_gui\preference_keys.py` （12 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 1 | other | `環境設定の定義（キー名とデフォルト値）` | settings / definition |
| 3 | other | `設定項目を追加・変更する場合は このファイルの に` | settings |
| 4 | other | `エントリを追加 編集するだけでよい` |  |
| 10 | comment | `設定項目の定義（キー名 デフォルト値）` | settings / definition |
| 11 | comment | `ここに項目を追加するだけで クラスから属性アクセス可能になる` |  |
| 14 | comment | `最終使用フォルダ` |  |
| 15 | other | `プロジェクト` |  |
| 16 | other | `ソース出力先` |  |
| 17 | other | `仕様書類の場所` |  |
| 18 | other | `エクスポート先` |  |
| 20 | comment | `イベント配送設定` | event / settings |
| 21 | other | `で使われる を へ自動変換` |  |

### `statable_gui\preferences.py` （14 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 9 | other | `アプリケーション設定を ファイルで保持する（キー名は別ファイルで定義）` | settings / definition / application / application |
| 11 | other | `の に登録されたキーは` |  |
| 12 | other | `のように属性アクセスで読み書きできる` |  |
| 24 | string | `定義されたキーが未保存ならデフォルト値を設定` | settings / definition |
| 34 | string | `ファイルから設定を読み込む` | settings |
| 43 | string | `現在の設定を ファイルに保存する` | settings |
| 49 | comment | `書き込み失敗時は無視（必要に応じてログ出力）` | failure / ignore |
| 53 | string | `設定値をキー名で取得する（従来方式）` | settings |
| 57 | string | `設定値をキー名で更新し 即座に保存する` | settings |
| 62 | comment | `属性アクセス（ など）` |  |
| 65 | comment | `定義済みキーなら値を返す` | definition |
| 68 | comment | `未定義の属性は通常のエラー` | error / definition |
| 72 | comment | `定義済みキーなら設定と保存を行う` | settings / definition |
| 77 | comment | `定義済み以外は通常の属性として設定` | settings / definition |

### `statable_gui\role_function_dialog.py` （26 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 10 | string | `ロール関数の新規登録・編集用ダイアログ` | role function / function |
| 13 | string | `ロール関数編集` | role function / function |
| 17 | comment | `タイトル入力欄（必須・仮タイトル自動設定）` | settings / title |
| 20 | string | `一覧に表示されるラベル（空なら自動設定）` | settings |
| 21 | string | `このロール関数のタイトルを入力してください 空の場合は自動で仮タイトルが設定されます` | role function / settings / title / function |
| 22 | string | `タイトル` | title |
| 26 | string | `関数名` | function |
| 28 | comment | `新規 名前空間（ ）入力欄` | namespace |
| 33 | string | `例 （空なら層なし）` | layer |
| 35 | string | `名前空間（層名・機能グループ名）` | namespace / layer |
| 36 | string | `指定すると の形式で参照できます` |  |
| 37 | string | `空の場合は層なし扱い（ ）となります` | layer |
| 39 | string | `名前空間` | namespace |
| 43 | string | `説明` | description |
| 47 | string | `戻り値型` | return value / type |
| 51 | string | `引数 型` | argument / type |
| 54 | string | `引数 名` | argument |
| 58 | string | `引数 型` | argument / type |
| 61 | string | `引数 名` | argument |
| 71 | string | `ボタン：タイトルが空なら仮タイトルを自動設定` | settings / title |
| 73 | string | `ロール関数 無名` | role function / function |
| 80 | other | `変更` |  |
| 81 | other | `を設定 および全引数を で指定` | settings / argument |
| 82 | other | `の が 化されたため` |  |
| 83 | other | `位置引数では構築できません` | argument |
| 87 | other | `新規追加` |  |

### `statable_gui\sample_data.py` （1 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 1 | string | `サンプルデータ生成（ 層リエクスポート）` | layer |

### `statable_gui\symbol_picker.py` （40 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 14 | string | `グローバル変数・イベントフラグ・ロール関数戻り値を選択する共通ウィジェット` | event / role function / variable / flag / return value / fun |
| 25 | comment | `タイトル` | title |
| 26 | string | `グローバル変数・イベントフラグ・戻り値一覧` | event / variable / flag / return value |
| 30 | comment | `検索` |  |
| 31 | string | `検索（前方一致）` |  |
| 34 | string | `タイトル・メンバ名・グループ名を入力` | title |
| 38 | comment | `一覧` |  |
| 43 | comment | `登録ボタン` |  |
| 45 | string | `変数登録` | variable |
| 49 | string | `フラグ登録` | flag |
| 54 | comment | `グローバル定義を開く` | definition |
| 55 | string | `グローバル定義を開く` | definition |
| 63 | comment | `一覧更新` |  |
| 71 | comment | `グローバル変数` | variable |
| 74 | string | `変数` | variable |
| 77 | string | `種別 グローバル変数` | variable |
| 78 | string | `タイトル` | title |
| 79 | string | `名前` |  |
| 80 | string | `型` | type |
| 81 | string | `単位` |  |
| 82 | string | `初期値` |  |
| 83 | string | `グループ` |  |
| 84 | string | `説明` | description |
| 88 | comment | `イベントフラグ` | event / flag |
| 91 | string | `フラグ` | flag |
| 94 | string | `種別 イベントフラグ` | event / flag |
| 95 | string | `タイトル` | title |
| 96 | string | `名前` |  |
| 97 | string | `最小値` |  |
| 98 | string | `最大値` |  |
| ... | ... | （他 10 行）| |

### `statable_gui\transition_editor_direct\__init__.py` （1 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `動作編集 パッケージ` |  |

### `statable_gui\transition_editor_direct\canvas_widget.py` （46 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `キャンバスウィジェット（案 ：順序リスト方式対応版）` |  |
| 4 | other | `ノードのドラッグ移動を無効化` |  |
| 5 | other | `ドラッグ試行時にメッセージ表示` |  |
| 6 | other | `フローアイテムの順序に基づく自動整列（子ノード込み）` |  |
| 7 | other | `ノードは常に 行表示（イベント名・条件・遷移先）` | event / transition / condition |
| 8 | other | `未定義項目は 条件 なし 未設定 と明示` | settings / definition / condition |
| 9 | other | `テキスト色を白に変更し視認性向上` |  |
| 10 | other | `ドロップ時のターゲット検出を改善（テキストアイテムを透過）` |  |
| 11 | other | `の上へのドロップも親 に追加` |  |
| 57 | comment | `デバッグログ 受け取ったテキストを出力` | debug |
| 64 | comment | `テキストアイテムを作成` |  |
| 68 | comment | `テキストアイテムがマウスイベントを受け取らないようにする` | event |
| 71 | comment | `ノードのサイズと表示内容を設定` | settings |
| 73 | comment | `常に 行表示（イベント名・条件・遷移先）に固定` | event / transition / condition |
| 79 | comment | `条件式が空なら 条件 なし を表示` | condition |
| 81 | string | `条件` | condition |
| 83 | string | `条件 なし` | condition |
| 84 | comment | `遷移先が空なら 未設定 を表示` | transition / settings |
| 88 | string | `未設定` | settings |
| 90 | comment | `が無い場合も 行を維持` |  |
| 91 | string | `条件 なし` | condition |
| 92 | string | `未設定` | settings |
| 103 | comment | `矩形を設定` | settings |
| 109 | comment | `キャンバス内でのドラッグ移動を完全に無効化（案 ）` |  |
| 114 | comment | `ドラッグ試行検出用` |  |
| 124 | comment | `ダブルクリックを正しく処理するため はしない` |  |
| 133 | string | `操作不可` |  |
| 134 | string | `キャンバス内でのノード移動はできません 順序リストで並べ替えてください` |  |
| 162 | string | `編集` |  |
| 166 | string | `上へ` |  |
| ... | ... | （他 16 行）| |

### `statable_gui\transition_editor_direct\code_widget.py` （40 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `コード表示ウィジェット（読み取り専用 対応）` |  |
| 4 | other | `デバッグログ強化版` | debug |
| 5 | other | `各 の処理内容を詳細に出力` |  |
| 7 | other | `修正` |  |
| 8 | other | `という古い形式を廃止` |  |
| 9 | other | `実ファイル生成（ ）と整合する形式に統一` |  |
| 10 | comment | `戻り値 （ の規約に合わせる）` | return value |
| 11 | comment | `関数名 （ドットを に変換）` | function |
| 12 | comment | `引数順` | argument |
| 13 | other | `（ ）から と を分離` |  |
| 25 | comment | `識別子として有効な形式（ などを弾く）` |  |
| 56 | comment | `層名と型名の解決` | type / layer |
| 60 | other | `から層名を推定` | layer |
| 62 | other | `等から推測できないため` |  |
| 63 | string | `関数名に含まれる （ の ）` | function |
| 64 | other | `を集計し 最頻値を採用する` |  |
| 65 | other | `判定不能なら空文字（層なし）` | layer |
| 67 | comment | `に 属性があればそれを使う（将来拡張）` |  |
| 72 | comment | `参照関数の を集計` | function |
| 96 | comment | `参照名 関数名` | function |
| 100 | other | `参照文字列を に変換` |  |
| 102 | other | `入力例` |  |
| 106 | other | `（既にプレフィックス付き）` |  |
| 107 | other | `（不正な識別子）` |  |
| 115 | comment | `引数部分を除去` | argument |
| 119 | comment | `既に で始まる場合はそのまま` |  |
| 136 | comment | `単純名` |  |
| 146 | comment | `コード生成` |  |
| 154 | comment | `システムグローバル定義（あれば）` | definition / system |
| 160 | comment | `ロール関数プロトタイプ収集（重複除去）` | role function / function |
| ... | ... | （他 10 行）| |

### `statable_gui\transition_editor_direct\dialog.py` （13 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `動作編集メインダイアログ（共有ライブラリ対応・ノード編集対応）` |  |
| 59 | string | `動作編集` |  |
| 70 | string | `自動整列` |  |
| 83 | comment | `ライブラリオブジェクトを直接渡す` |  |
| 96 | string | `フロー編集` |  |
| 99 | string | `コード` |  |
| 101 | comment | `シグナル接続` | connection |
| 112 | string | `システムグローバル` | system |
| 118 | string | `キャンセル` |  |
| 212 | comment | `遷移先ステートの選択肢をステートマシンから取得` | transition |
| 221 | other | `現在の遷移先を渡す` | transition |
| 222 | other | `現在の 遷移先を渡す` | transition |
| 241 | string | `確認 このノードを削除しますか？` |  |

### `statable_gui\transition_editor_direct\draft.py` （22 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `動作編集用ドラフトモデル（ノード位置保存対応）` |  |
| 5 | other | `変更` |  |
| 6 | other | `に 属性を追加（ ）` |  |
| 7 | other | `がこれを最優先で参照する` |  |
| 8 | other | `従来の 最頻値推定 はフォールバックとして残る` |  |
| 20 | other | `値がリストでなければリストに変換して返す` |  |
| 21 | other | `や空文字列は空リスト` |  |
| 22 | other | `文字列が来た場合は単一要素のリストとして扱う` |  |
| 23 | other | `リストならそのまま返す` |  |
| 81 | comment | `ノード位置保存用（ で自由移動を保持）` |  |
| 115 | comment | `追加 層名（ の第一候補）` | layer |
| 116 | comment | `等の生成側で を渡す` |  |
| 117 | comment | `空文字の場合は 側で 最頻値フォールバックが動く` |  |
| 136 | comment | `は この が属する層 を表すため` | layer |
| 137 | comment | `では保持する（リセットしない）` |  |
| 150 | other | `追加` |  |
| 164 | other | `追加` |  |
| 175 | string | `変換` |  |
| 183 | comment | `イベント名が空の場合は をデフォルトにする` | event |
| 191 | string | `無題遷移` | transition |
| 205 | string | `変換` |  |
| 228 | string | `無題遷移` | transition |

### `statable_gui\transition_editor_direct\edit_dialogs.py` （16 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `ノード編集ダイアログ（ 有無チェックボックス対応 条件ビルダー対応）` | condition |
| 22 | string | `キャンセル` |  |
| 34 | string | `ロール関数編集` | role function / function |
| 39 | string | `関数名` | function |
| 55 | string | `状態遷移イベント編集` | state / event / transition |
| 64 | string | `イベント` | event |
| 70 | string | `条件式` | condition |
| 74 | string | `条件を編集` | condition |
| 79 | string | `遷移直前処理` | transition |
| 88 | string | `追加` |  |
| 91 | string | `削除` |  |
| 96 | string | `条件を使用する` | condition |
| 101 | string | `遷移先` | transition |
| 110 | string | `遷移先` | transition |
| 149 | string | `直前` |  |
| 160 | other | `今後対応` |  |

### `statable_gui\transition_editor_direct\flow_widget.py` （15 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `ビジュアル編集フローリスト（ ダブルクリック編集）` |  |
| 18 | string | `と行挿入をサポートするフローリスト` |  |
| 42 | comment | `パレットからのドロップ` |  |
| 47 | comment | `挿入位置を決定` |  |
| 59 | comment | `を作成して挿入` |  |
| 67 | comment | `内部移動（並べ替え）は標準動作に任せる` |  |
| 72 | comment | `親の に通知` |  |
| 79 | string | `ビジュアル編集ウィジェット` |  |
| 94 | string | `動作フロー（ で配置・ダブルクリックで編集）` |  |
| 96 | comment | `カスタムリスト` |  |
| 102 | comment | `デフォルト遷移先` | transition |
| 104 | string | `デフォルト遷移先` | transition |
| 112 | comment | `ドラフト読み込み` |  |
| 121 | comment | `リスト変更時の同期` |  |
| 141 | comment | `ダブルクリック編集` |  |

### `statable_gui\transition_editor_direct\palette_widget.py` （32 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `カテゴリ別折りたたみパレット` |  |
| 4 | other | `（共有ライブラリ対応・ダブルクリック編集対応・ドラッグ開始対応）` |  |
| 6 | other | `修正` |  |
| 7 | other | `（バグ ）` |  |
| 8 | other | `と が同じ で表示され` |  |
| 9 | other | `編集対象が誤る問題を解消` |  |
| 10 | other | `衝突チェックを追加` |  |
| 53 | string | `ドラッグ開始をオーバーライドして確実に を実行` | execute |
| 95 | string | `カテゴリ別折りたたみパレット（イベント選択画面）` | event |
| 114 | string | `イベント選択画面` | event |
| 119 | comment | `ロール関数セクション` | role function / function |
| 120 | string | `ロール関数` | role function / function |
| 131 | string | `ロール関数追加` | role function / function |
| 135 | comment | `遷移条件セクション` | transition / condition |
| 136 | string | `遷移条件` | transition / condition |
| 147 | string | `遷移条件追加` | transition / condition |
| 157 | other | `一意名を生成` |  |
| 159 | other | `改善` |  |
| 160 | other | `は で` |  |
| 161 | other | `キー管理されているため 既存キーとの衝突チェックは` |  |
| 162 | other | `（純粋名）と の両方で行う` |  |
| 173 | comment | `の末尾一致も検出` |  |
| 216 | other | `ロール関数の編集要求` | role function / function |
| 218 | other | `修正` |  |
| 219 | other | `は または` |  |
| 220 | other | `純粋名 後段の は` |  |
| 221 | other | `で解決するため` |  |
| 222 | other | `どちらでも正しく動作する` |  |
| 239 | other | `ロール関数・遷移条件リストを再構築` | transition / role function / condition / function |
| 241 | other | `修正` |  |
| ... | ... | （他 2 行）| |

### `statable_gui\transition_editor_direct\system_global_dialog.py` （6 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `システムグローバル変数 別画面` | variable / system |
| 15 | string | `システムグローバル変数` | variable / system |
| 23 | string | `追加` |  |
| 26 | string | `削除` |  |
| 31 | string | `閉じる` |  |
| 43 | string | `追加 変数名` | variable |

### `statable_gui\validation_dialog.py` （75 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `検証・ 連携ダイアログ` |  |
| 4 | other | `対応` |  |
| 35 | string | `検証・ 連携ダイアログ` |  |
| 48 | string | `コード生成前検証・ 診断` |  |
| 55 | string | `を構築` |  |
| 58 | comment | `タブウィジェット` |  |
| 62 | comment | `検証結果タブ` |  |
| 65 | string | `検証結果` |  |
| 67 | comment | `プロンプトタブ` |  |
| 70 | string | `プロンプト` |  |
| 72 | comment | `回答タブ` |  |
| 75 | string | `回答取り込み` |  |
| 77 | comment | `変更一覧タブ` |  |
| 80 | string | `変更一覧・反映` |  |
| 82 | comment | `閉じるボタン` |  |
| 84 | string | `閉じる` |  |
| 91 | string | `検証結果タブのセットアップ` |  |
| 94 | comment | `サマリーラベル` |  |
| 99 | comment | `問題リスト` |  |
| 101 | string | `重大度 カテゴリ メッセージ 対象 修正提案` |  |
| 109 | comment | `再検証ボタン` |  |
| 110 | string | `再検証` |  |
| 115 | string | `プロンプトタブのセットアップ` |  |
| 118 | comment | `説明ラベル` | description |
| 120 | string | `以下の手順で 診断を行います：` |  |
| 121 | string | `コピー ボタンでプロンプトをクリップボードにコピー` |  |
| 122 | string | `等に貼り付けて質問` |  |
| 123 | string | `の回答をコピー` |  |
| 124 | string | `回答取り込み タブで回答を貼り付け` |  |
| 129 | comment | `コピーボタン` |  |
| ... | ... | （他 45 行）| |

### `statable_gui\widgets.py` （53 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `メインウィジェット（共有ライブラリ対応版）` |  |
| 6 | other | `判定用` |  |
| 19 | comment | `自体を環境変数で分岐` | variable |
| 20 | comment | `のとき しない` |  |
| 21 | comment | `ランタイムが初期化されず リーク警告が出ない` | initialization / warning |
| 22 | comment | `通常時 従来通り` |  |
| 61 | other | `図のプレビューウィジェット` |  |
| 63 | other | `環境変数 で を無効化できる` | variable |
| 64 | other | `（テスト時に の リーク警告を避けるため）` | warning |
| 76 | comment | `テストモード を生成しない` |  |
| 88 | comment | `通常モード` |  |
| 105 | string | `が利用できません` |  |
| 106 | string | `をインストールしてください` |  |
| 116 | comment | `テストモード 何もしない` |  |
| 196 | string | `名称 説明 関数 関数 関数 タイプ` | description / name / function |
| 201 | string | `追加` |  |
| 203 | string | `削除` |  |
| 208 | string | `状態一覧` | state |
| 212 | comment | `変更 列 列（名前空間列を挿入）` | namespace |
| 215 | string | `タイトル 関数名 名前空間 説明 戻り値型` | title / description / namespace / return value / function /  |
| 216 | string | `引数 型 引数 名 引数 型 引数 名` | argument / type |
| 222 | string | `追加` |  |
| 224 | string | `削除` |  |
| 230 | string | `イベント定義` | event / definition |
| 234 | string | `ロール関数` | role function / function |
| 256 | string | `ダブルクリックで編集` |  |
| 259 | string | `ダブルクリックで編集` |  |
| 262 | string | `ダブルクリックで編集` |  |
| 273 | other | `変更 名前空間列 を追加` | namespace |
| 274 | other | `旧 列 新 列` |  |
| ... | ... | （他 23 行）| |

## カテゴリ C: コード生成層のログ等

### `codegen\__init__.py` （9 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `コード生成層` | layer |
| 5 | other | `追加` |  |
| 6 | other | `再エクスポートは最小限に留める` |  |
| 7 | other | `は生成時に多数のサブモジュールを読み込むため` |  |
| 8 | other | `トップレベルで再エクスポートしない（起動時間短縮のため）` | start |
| 20 | other | `遅延インポート` |  |
| 22 | other | `のように使われた時のみ` |  |
| 23 | other | `実際のモジュールをロードする` |  |
| 24 | other | `起動時間を抑えつつ 利便性を確保する` | start |

### `codegen\code_merger.py` （78 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `生成コードと既存コードのマージ処理` |  |
| 4 | other | `ユーザー編集部分を保持しながら自動生成コードを更新する` | user |
| 6 | other | `対応マーカー` | marker |
| 7 | other | `ファイル全体ユーザー領域` | user |
| 8 | other | `関数単位ユーザー領域` | function / user |
| 9 | other | `の は 形式（層名込み）` | layer |
| 10 | other | `の は 形式（層名なし）` | layer |
| 11 | other | `ファイル末尾ユーザー領域` | user |
| 13 | other | `修正` |  |
| 14 | other | `既存 ブロックがあればその中身を` |  |
| 15 | other | `置換するよう変更 旧実装は常に の後に新規挿入していたため` |  |
| 16 | other | `生成コード元のブロックが残骸化し プレースホルダが残り続けていた` |  |
| 28 | string | `生成コードと既存コードのマージクラス` |  |
| 30 | comment | `マーカー定義` | definition / marker |
| 38 | comment | `ファイル末尾ユーザー領域` | user |
| 43 | comment | `関数名抽出パターン（ 両対応）` | function |
| 56 | comment | `抽出処理` |  |
| 58 | string | `ファイル全体のユーザーコードを抽出` | user |
| 66 | string | `ファイルユーザーコードを抽出しました` | user |
| 72 | string | `関数単位のユーザーコードを抽出` | function / user |
| 80 | string | `関数 のユーザーコードを抽出しました` | function / user |
| 87 | other | `全関数のユーザーコードを抽出` | function / user |
| 89 | other | `と の両方に対応` |  |
| 90 | other | `キー` |  |
| 91 | other | `キー` |  |
| 113 | comment | `ファイル末尾ユーザーコード抽出` | user |
| 115 | string | `ファイル末尾のユーザーコードを抽出` | user |
| 123 | string | `末尾ユーザーコードを抽出しました` | user |
| 127 | comment | `注入処理` |  |
| 131 | other | `生成コードにファイル全体のユーザーコードを注入` | user |
| ... | ... | （他 48 行）| |

### `codegen\config.py` （36 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `コード生成設定管理モジュール` | settings |
| 4 | other | `生成オプションを一元管理する` |  |
| 13 | string | `コード生成設定` | settings |
| 15 | comment | `生成スタイル` |  |
| 18 | comment | `遷移テーブル方式` | transition |
| 21 | comment | `種別` |  |
| 24 | comment | `命名規則` |  |
| 30 | comment | `デバッグログ` | debug |
| 35 | comment | `コメント生成` |  |
| 39 | comment | `マーカー` | marker |
| 42 | comment | `出力設定` | settings |
| 46 | comment | `プロジェクト設定` | settings |
| 49 | comment | `フォルダ構成` |  |
| 56 | comment | `スーパーインクルード` |  |
| 61 | comment | `外部インクルード` |  |
| 68 | comment | `予約イベント制限` | event |
| 72 | string | `辞書に変換` |  |
| 108 | string | `辞書から復元` |  |
| 109 | comment | `未知のキーは無視` | ignore |
| 116 | string | `設定管理クラス` | settings |
| 122 | string | `現在の設定を取得` | settings |
| 126 | string | `設定を更新` | settings |
| 130 | string | `設定を部分的に更新` | settings |
| 136 | string | `設定をリセット` | settings |
| 140 | string | `利用可能な生成スタイル` |  |
| 142 | string | `テーブル駆動方式` |  |
| 143 | string | `方式` |  |
| 147 | string | `利用可能なテーブル方式` |  |
| 149 | string | `配列方式` |  |
| 150 | string | `方式` |  |
| ... | ... | （他 6 行）| |

### `codegen\naming_convention.py` （4 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `言語命名規則モジュール（辞書駆動版）` |  |
| 19 | string | `言語の命名規則を管理するクラス` |  |
| 101 | string | `パスカルケースに変換（キャメルケースの区切りを維持）` |  |
| 110 | comment | `既にキャメルケースの場合は先頭のみ大文字化` |  |

### `codegen\sample_data.py` （50 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `コード生成テスト用サンプルデータ` |  |
| 4 | other | `とは独立したテストデータを提供する` |  |
| 6 | other | `修正` |  |
| 7 | other | `の を に移行（バグ ）` |  |
| 8 | other | `フィールドは で 互換用・未使用 と定義され` | definition |
| 9 | other | `は のみ参照するため` |  |
| 10 | other | `では呼び出しがコード生成に反映されない` |  |
| 29 | string | `サンプルデータ生成クラス` |  |
| 38 | string | `初期状態` | state |
| 39 | string | `アイドル状態` | state |
| 40 | string | `実行状態` | state / execute |
| 41 | string | `エラー状態` | state / error |
| 44 | string | `電源 イベント` | event |
| 45 | string | `開始イベント` | event |
| 46 | string | `停止イベント` | event / stop |
| 47 | string | `エラー検出イベント` | event / error |
| 50 | comment | `修正` |  |
| 57 | string | `電源` |  |
| 65 | string | `開始` |  |
| 72 | string | `停止` | stop |
| 79 | string | `エラー処理` | error |
| 84 | string | `電源 処理` |  |
| 88 | string | `開始条件チェック` | condition |
| 92 | string | `開始処理` |  |
| 96 | string | `停止処理` | stop |
| 100 | string | `エラー処理` | error |
| 106 | string | `データ処理` |  |
| 117 | string | `バッテリー電圧` |  |
| 119 | string | `システムタイマ` | timer / system |
| 121 | string | `温度センサ値` |  |
| ... | ... | （他 20 行）| |

### `codegen\type_mapper.py` （2 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `言語型マッピングモジュール（辞書駆動版）` | type |
| 19 | string | `の型を 言語の型にマッピングするクラス` | type |

### `codegen\validate\__init__.py` （1 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `検証・ 連携パッケージ` |  |

### `codegen\validate\change_actions.py` （3 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `変更アクション定義` | definition / action |
| 12 | string | `変更アクション種別` | action |
| 27 | string | `変更リクエスト` |  |

### `codegen\validate\change_applier.py` （43 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `変更適用エンジン（修正版）` |  |
| 5 | other | `変更` |  |
| 6 | other | `に を追加（ との不一致解消）` |  |
| 7 | other | `メソッドを実装` |  |
| 21 | string | `変更リクエストをシステムに適用する` | system |
| 29 | comment | `ハンドラ辞書を文字列キーで定義` | definition |
| 38 | other | `追加` |  |
| 45 | string | `変更を適用` |  |
| 48 | comment | `の値（文字列）でハンドラを取得` |  |
| 55 | string | `未対応のアクション` | action |
| 72 | string | `全変更を適用` |  |
| 94 | string | `状態 が存在しません` | state |
| 96 | string | `初期状態を に設定しました` | state / settings |
| 107 | string | `遷移の情報が不足しています` | transition / info |
| 117 | string | `遷移 を追加しました` | transition |
| 126 | string | `状態名が指定されていません` | state |
| 128 | string | `状態 は既に存在します` | state |
| 130 | comment | `に存在しない値は にフォールバック` |  |
| 138 | comment | `パラメータを受理（ 用）` |  |
| 147 | string | `状態 を追加しました` | state |
| 154 | string | `イベント名が指定されていません` | event |
| 156 | string | `イベント は既に存在します` | event |
| 160 | string | `イベント を追加しました` | event |
| 170 | string | `遷移 を削除しました` | transition |
| 172 | string | `該当する遷移が見つかりません` | transition |
| 186 | string | `遷移 を更新しました` | transition |
| 188 | string | `該当する遷移が見つかりません` | transition |
| 195 | string | `関数名が指定されていません` | function |
| 197 | string | `関数 は既に存在します` | function |
| 206 | string | `ロール関数 を追加しました` | role function / function |
| ... | ... | （他 13 行）| |

### `codegen\validate\clipboard_manager.py` （2 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `クリップボード管理` |  |
| 15 | string | `クリップボード管理クラス` |  |

### `codegen\validate\data\__init__.py` （1 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `検証データパッケージ` |  |

### `codegen\validate\data\action_definitions.py` （49 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `アクション定義（データのみ）` | definition / action |
| 5 | other | `変更` |  |
| 6 | other | `の 列挙を 種類に拡張（ と一致）` |  |
| 7 | other | `を追加（ との不一致解消）` |  |
| 12 | string | `初期状態を設定` | state / settings |
| 14 | string | `状態名` | state |
| 18 | string | `遷移を追加` | transition |
| 20 | string | `遷移元` | transition |
| 21 | string | `イベント名` | event |
| 22 | string | `遷移先` | transition |
| 23 | string | `条件` | condition |
| 24 | string | `アクション名` | action |
| 28 | string | `状態を追加` | state |
| 30 | string | `状態名` | state |
| 43 | string | `状態タイプ` | state |
| 45 | string | `説明` | description |
| 49 | string | `イベントを追加` | event |
| 51 | string | `イベント名` | event |
| 52 | string | `イベント種類` | event |
| 53 | string | `説明` | description |
| 57 | string | `遷移を削除` | transition |
| 59 | string | `遷移元` | transition |
| 60 | string | `イベント名` | event |
| 61 | string | `遷移先` | transition |
| 65 | string | `遷移を更新` | transition |
| 67 | string | `遷移元` | transition |
| 68 | string | `イベント名` | event |
| 69 | string | `新しい遷移先` | transition |
| 70 | string | `新しい条件` | condition |
| 71 | string | `新しいアクション` | action |
| ... | ... | （他 19 行）| |

### `codegen\validate\data\keywords.py` （21 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `キーワード定義（データのみ）` | definition |
| 7 | string | `承知しました 了解しました かしこまりました はい こんにちは` |  |
| 8 | string | `以下に 分析結果 検証しました 確認しました 以下は` |  |
| 9 | string | `です ます と考え と思い です` |  |
| 10 | string | `なお ちなみに 参考までに 補足` |  |
| 11 | string | `以上です 以上が ご確認ください よろしくお願い` |  |
| 30 | string | `エラー 重大` | error |
| 31 | string | `警告` | warning |
| 32 | string | `情報` | info |
| 35 | string | `状態` | state |
| 36 | string | `イベント` | event |
| 37 | string | `遷移` | transition |
| 38 | string | `ロール関数 関数` | role function / function |
| 39 | string | `変数` | variable |
| 40 | string | `フラグ` | flag |
| 41 | string | `キュー` | queue |
| 42 | string | `割り込み` | interrupt |
| 43 | string | `タイマ` | timer |
| 44 | string | `型 構造体` | type |
| 46 | string | `修正方法 修正案 提案 対応 解決策` |  |
| 47 | string | `対象 状態 関数 変数 イベント` | state / event / variable / function |

### `codegen\validate\data\prompt_templates.py` （23 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `プロンプトテンプレート定義（データのみ）` | definition |
| 6 | other | `未使用の キーを削除` |  |
| 7 | other | `（ と共に削除）` |  |
| 12 | other | `あなたは組み込みソフトウェアの状態遷移設計の専門家です` | state / transition |
| 14 | other | `タスク` |  |
| 15 | other | `状態遷移設計データを検証し 必要な変更を 形式で出力してください` | state / transition |
| 17 | other | `出力形式` |  |
| 18 | other | `純粋な のみを出力してください` |  |
| 19 | other | `挨拶 説明 補足 マーカー コードブロック記号は一切不要です` | description / marker |
| 21 | other | `出力例` |  |
| 24 | other | `実際のデータ` |  |
| 27 | other | `指示` |  |
| 28 | other | `出力例と同じ 形式で 実際のデータに対する変更を提案してください` |  |
| 29 | other | `以外は出力しないでください` |  |
| 43 | string | `初期状態が未設定のため` | state / settings |
| 53 | string | `エラー状態からの回復遷移がないため` | state / transition / error |
| 58 | other | `検証観点` |  |
| 59 | docstring | `初期状態が設定されているか` | state / settings |
| 60 | other | `すべての状態に遷移が定義されているか` | state / transition / definition |
| 61 | other | `エラー状態からの回復遷移があるか` | state / transition / error |
| 62 | other | `各状態で処理すべきイベントが網羅されているか` | state / event |
| 63 | other | `到達不能な状態がないか` | state |
| 64 | other | `デッドロックの可能性がないか` |  |

### `codegen\validate\data\validation_rules.py` （55 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `検証ルール定義（データのみ）` | definition |
| 10 | string | `初期状態が設定されていません` | state / settings |
| 11 | string | `で初期状態を設定してください` | state / settings |
| 15 | string | `状態 は到達不能です` | state |
| 16 | string | `遷移を追加するか 状態を削除してください` | state / transition |
| 20 | string | `状態 からの遷移がありません` | state / transition |
| 21 | string | `遷移を追加するか 終端状態として明示してください` | state / transition |
| 25 | string | `状態名 と は大文字小文字の違いのみです` | state |
| 26 | string | `命名規則を統一してください` |  |
| 32 | string | `イベント はどの遷移にも使用されていません` | event / transition |
| 33 | string | `遷移を追加するか イベントを削除してください` | event / transition |
| 37 | string | `イベント に対する遷移が定義されていません` | event / transition / definition |
| 38 | string | `遷移を追加してください` | transition |
| 44 | string | `遷移先 が定義されていません` | transition / definition |
| 45 | string | `遷移先の状態を定義してください` | state / transition / definition |
| 49 | string | `イベント が定義されていません` | event / definition |
| 50 | string | `イベントを定義してください` | event / definition |
| 54 | string | `遷移元 が定義されていません` | transition / definition |
| 55 | string | `遷移元の状態を定義してください` | state / transition / definition |
| 59 | string | `遷移 が重複しています` | transition |
| 60 | string | `重複した遷移を削除してください` | transition |
| 64 | string | `自己遷移` | transition |
| 65 | string | `自己遷移が意図的か確認してください` | transition |
| 71 | string | `ロール関数 の戻り値型が未定義です` | role function / definition / return value / function / type |
| 72 | string | `戻り値型を設定してください` | settings / return value / type |
| 76 | string | `ロール関数 の引数定義が不完全です` | role function / definition / argument / function |
| 77 | string | `引数名と引数型を正しく設定してください` | settings / argument / type |
| 81 | string | `ロール関数 は使用されていません` | role function / function |
| 82 | string | `使用するか削除してください` |  |
| 88 | string | `変数名 が重複しています` | variable |
| ... | ... | （他 25 行）| |

### `codegen\validate\items\__init__.py` （1 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `項目別バリデータパッケージ` |  |

### `codegen\validate\items\base_validator.py` （2 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `バリデータ基底クラス` |  |
| 16 | string | `バリデータ基底クラス` |  |

### `codegen\validate\items\custom_type_validator.py` （2 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `カスタム型検証` | type |
| 19 | string | `カスタム型検証クラス` | type |

### `codegen\validate\items\event_validator.py` （5 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `イベント検証` | event |
| 6 | other | `と 出力を統一` |  |
| 7 | other | `の開始・完了ログを追加` | completed |
| 8 | other | `ルール実行を で囲み 失敗時は で記録` | failure / execute |
| 24 | string | `イベント検証クラス` | event |

### `codegen\validate\items\flag_validator.py` （2 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `フラグ検証` | flag |
| 19 | string | `フラグ検証クラス` | flag |

### `codegen\validate\items\interrupt_validator.py` （2 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `割り込み検証` | interrupt |
| 19 | string | `割り込み検証クラス` | interrupt |

### `codegen\validate\items\queue_validator.py` （2 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `キュー検証` | queue |
| 19 | string | `キュー検証クラス` | queue |

### `codegen\validate\items\role_function_validator.py` （2 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `ロール関数検証` | role function / function |
| 19 | string | `ロール関数検証クラス` | role function / function |

### `codegen\validate\items\state_validator.py` （2 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `状態検証` | state |
| 19 | string | `状態検証クラス` | state |

### `codegen\validate\items\timer_validator.py` （2 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `タイマ検証` | timer |
| 19 | string | `タイマ検証クラス` | timer |

### `codegen\validate\items\transition_validator.py` （5 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `遷移検証` | transition |
| 6 | other | `と 出力を統一` |  |
| 7 | other | `の開始・完了ログを追加` | completed |
| 8 | other | `ルール実行を で囲み 失敗時は で記録` | failure / execute |
| 24 | string | `遷移検証クラス` | transition |

### `codegen\validate\items\variable_validator.py` （2 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `変数検証` | variable |
| 19 | string | `変数検証クラス` | variable |

### `codegen\validate\logger.py` （5 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `検証モジュール用ロガー設定` | settings |
| 12 | string | `ロガーをセットアップ` |  |
| 20 | comment | `コンソールハンドラ` |  |
| 30 | comment | `ファイルハンドラ` |  |
| 52 | comment | `デフォルトロガー（ として公開）` |  |

### `codegen\validate\models.py` （11 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `検証データモデル定義` | definition |
| 12 | string | `検証重大度` |  |
| 19 | string | `文字列から変換` |  |
| 27 | string | `エラー` | error |
| 28 | string | `警告` | warning |
| 29 | string | `情報` | info |
| 36 | string | `検証問題` |  |
| 46 | string | `辞書に変換` |  |
| 59 | string | `辞書から復元` |  |
| 76 | string | `検証結果` |  |
| 129 | string | `検証コンテキスト` | context |

### `codegen\validate\response_parser.py` （3 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `回答パーサー` |  |
| 20 | string | `回答パーサー` |  |
| 125 | string | `初期状態` | state |

### `codegen\validate\validation_dialog.py` （72 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `検証・ 連携ダイアログ` |  |
| 4 | other | `対応` |  |
| 35 | string | `検証・ 連携ダイアログ` |  |
| 48 | string | `コード生成前検証・ 診断` |  |
| 55 | string | `を構築` |  |
| 58 | comment | `タブウィジェット` |  |
| 62 | comment | `検証結果タブ` |  |
| 65 | string | `検証結果` |  |
| 67 | comment | `プロンプトタブ` |  |
| 70 | string | `プロンプト` |  |
| 72 | comment | `回答タブ` |  |
| 75 | string | `回答取り込み` |  |
| 77 | comment | `変更一覧タブ` |  |
| 80 | string | `変更一覧・反映` |  |
| 82 | comment | `閉じるボタン` |  |
| 84 | string | `閉じる` |  |
| 91 | string | `検証結果タブのセットアップ` |  |
| 94 | comment | `サマリーラベル` |  |
| 99 | comment | `問題リスト` |  |
| 101 | string | `重大度 カテゴリ メッセージ 対象 修正提案` |  |
| 109 | comment | `再検証ボタン` |  |
| 110 | string | `再検証` |  |
| 115 | string | `プロンプトタブのセットアップ` |  |
| 118 | comment | `説明ラベル` | description |
| 120 | string | `以下の手順で 診断を行います：` |  |
| 121 | string | `コピー ボタンでプロンプトをクリップボードにコピー` |  |
| 122 | string | `等に貼り付けて質問` |  |
| 123 | string | `の回答をコピー` |  |
| 124 | string | `回答取り込み タブで回答を貼り付け` |  |
| 129 | comment | `コピーボタン` |  |
| ... | ... | （他 42 行）| |

### `codegen\validate\validator.py` （5 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `検証メインクラス` |  |
| 12 | comment | `ロガーは直接参照` |  |
| 15 | comment | `モデル` |  |
| 18 | comment | `バリデータ` |  |
| 32 | string | `コード生成検証メインクラス` |  |

## カテゴリ F: サンプルデータ

### `statable\sample_data.py` （57 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 1 | string | `サンプルデータ生成（ビジネスロジック層）` | layer |
| 19 | string | `初期状態` | state |
| 20 | string | `動作中` | running |
| 21 | string | `エラー状態` | state / error |
| 22 | string | `停止状態` | state / stop |
| 24 | string | `起動要求` | start |
| 27 | string | `起動要求` | start |
| 28 | string | `停止要求` | stop |
| 31 | string | `停止要求` | stop |
| 32 | string | `エラー通知` | error |
| 36 | string | `エラー通知` | error |
| 37 | string | `タイマ満了` | timer |
| 40 | string | `タイマ満了` | timer |
| 41 | string | `完了遷移` | transition / completed |
| 44 | string | `完了遷移` | transition / completed |
| 49 | comment | `修正 位置引数バグの根本修正（ ）` | argument |
| 57 | string | `起動` | start |
| 65 | string | `停止` | stop |
| 73 | string | `エラーへ` | error |
| 81 | string | `リトライ` | retry |
| 89 | string | `停止へ` | stop |
| 97 | string | `無視` | ignore |
| 103 | string | `センサ初期化` | initialization |
| 109 | string | `センサ初期化` | initialization |
| 114 | string | `エラーログ出力` | error |
| 120 | string | `エラーログ出力` | error |
| 129 | comment | `ユーザー定義型（構造体＋ビットフィールド＋配列）` | definition / type / user |
| 132 | string | `システムステータス構造体` | system |
| 133 | string | `システムステータス` | system |
| 136 | string | `電源 フラグ 電源` | flag |
| ... | ... | （他 27 行）| |

## カテゴリ G: テスト期待値

### `tests\conftest.py` （12 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `共通設定` | settings |
| 5 | other | `テスト用` |  |
| 6 | other | `を モードで起動` | start |
| 7 | other | `を環境変数で無効化` | variable |
| 8 | other | `ランタイムをロードさせない` |  |
| 9 | other | `警告を根本から抑制` | warning |
| 13 | comment | `環境変数は他の より前に設定する` | settings / variable |
| 23 | string | `セッション終了時に のウィジェットをクリーンアップ` |  |
| 32 | comment | `セッション終了後` |  |
| 33 | comment | `は無効化されているため トップレベルウィジェットの` |  |
| 34 | comment | `解放とイベントループの処理だけで十分` | event |
| 54 | string | `各テスト間で を実行し のリークを防ぐ` | execute |

### `tests\test_c_code_generator.py` （52 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `のユニットテスト` |  |
| 5 | other | `目的` |  |
| 6 | other | `コード生成統括クラスの回帰防止` |  |
| 7 | other | `単層` | layer |
| 8 | other | `複数層 （ ）` | layer |
| 9 | other | `の層サフィックス付与（ ）` | layer |
| 10 | other | `の生成（ ）` |  |
| 11 | other | `の層別展開` | layer |
| 12 | other | `出力パス解決` |  |
| 13 | other | `保存（マージなし マージあり）` |  |
| 15 | other | `対象` |  |
| 32 | comment | `ヘルパー` |  |
| 44 | string | `起動` | start |
| 55 | string | `カウンタ カウンタ` | counter |
| 58 | string | `初期化 初期化` | initialization |
| 74 | comment | `初期化` | initialization |
| 101 | comment | `単層` | layer |
| 119 | comment | `主要ファイル` |  |
| 126 | string | `に共通型が含まれる` | type |
| 135 | comment | `共通型なので は含まれない（層固有側）` | type / layer |
| 139 | string | `（層固有）に が含まれる` | layer |
| 145 | comment | `のみ` |  |
| 160 | comment | `複数層` | layer |
| 166 | string | `層固有ファイルに サフィックス` | layer |
| 177 | comment | `キーに が含まれる` |  |
| 185 | string | `層固有 は のみ（共通型は含まない）` | type / layer |
| 193 | comment | `層固有` | layer |
| 197 | comment | `は含む` |  |
| 199 | comment | `共通型は含まない` | type |
| 203 | string | `層固有 は を` | layer |
| ... | ... | （他 22 行）| |

### `tests\test_code_merger.py` （27 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `のユニットテスト` |  |
| 5 | other | `目的` |  |
| 6 | other | `ユーザーコード保持の回帰防止` | user |
| 7 | other | `ファイル全体ユーザーコード（ マーカー）` | marker / user |
| 8 | other | `関数単位ユーザーコード（ ）` | function / user |
| 9 | other | `ファイル末尾ユーザーコード（ ）` | user |
| 10 | other | `の完全サイクル` |  |
| 11 | other | `の複数ファイル処理` |  |
| 13 | other | `対象` |  |
| 24 | comment | `ヘルパー` |  |
| 58 | comment | `ファイル全体ユーザーコード` | user |
| 95 | comment | `関数単位ユーザーコード` | function / user |
| 119 | string | `パターンも抽出できる` |  |
| 144 | comment | `マーカーが無い場合は変更されない（新規挿入しない）` | marker |
| 155 | comment | `ファイル末尾ユーザーコード` | user |
| 184 | comment | `完全サイクル` |  |
| 229 | string | `種類のユーザーコードが同時に保持される` | user |
| 263 | comment | `プレースホルダは残らない` |  |
| 277 | comment | `既存ファイル配置` |  |
| 298 | comment | `は既存なし そのまま` |  |
| 302 | string | `使用時 生成キーと既存パスが異なる` |  |
| 312 | comment | `生成キーは` |  |
| 313 | comment | `実際の既存パスは` |  |
| 323 | comment | `層サフィックスを付与` | layer |
| 339 | comment | `サマリー取得` |  |
| 366 | comment | `エッジケース` |  |
| 372 | string | `空のユーザーコードブロックは正常に処理される` | user / normal |

### `tests\test_enum_generator.py` （23 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `のユニットテスト` |  |
| 5 | other | `目的` |  |
| 6 | other | `コード生成（ 部分）の回帰防止` |  |
| 7 | other | `状態 イベント フラグの 生成` | state / event / flag |
| 8 | other | `層名プレフィックス（ 修正の回帰防止）` | layer |
| 9 | other | `空名イベントの除外（ 修正の回帰防止）` | event |
| 10 | other | `値（完了イベント）の自動挿入` | event / completed |
| 12 | other | `対象` |  |
| 23 | comment | `ヘルパー` |  |
| 39 | comment | `状態` | state |
| 58 | comment | `が含まれる` |  |
| 69 | string | `層名が 名にプレフィックスされる` | layer |
| 78 | string | `層名なしの場合はプレフィックスなし` | layer |
| 87 | comment | `イベント` | event |
| 97 | string | `が必ず挿入される` |  |
| 105 | other | `修正 空名イベントは本処理から除外される` | event |
| 106 | other | `（ と二重定義になるため）` | definition |
| 111 | comment | `は 回だけ（ ）` |  |
| 130 | comment | `フラグ` | flag |
| 147 | string | `フラグは層名プレフィックスなし（共通型）` | flag / type / layer |
| 151 | comment | `フラグには層名が付かない` | flag / layer |
| 183 | comment | `フラグなし` | flag |
| 187 | comment | `ビットマスク` |  |

### `tests\test_event_queue_generator.py` （23 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `のユニットテスト` |  |
| 5 | other | `目的` |  |
| 6 | other | `イベントキュー生成の回帰防止` | event / queue |
| 7 | other | `を含む` |  |
| 8 | other | `満杯チェック エンキュー` | queue |
| 9 | other | `空チェック デキュー` | queue |
| 10 | other | `種を連結` |  |
| 11 | other | `複数キュー対応` | queue |
| 13 | other | `対象` |  |
| 23 | comment | `ヘルパー` |  |
| 28 | string | `メインキュー` | queue |
| 55 | comment | `メンバ` |  |
| 65 | comment | `の実装次第だが 化` |  |
| 76 | string | `テストキュー` | queue |
| 78 | string | `テストキュー` | queue |
| 114 | comment | `満杯チェック` |  |
| 157 | comment | `ポインタ チェック` | pointer |
| 159 | comment | `読み出し` |  |
| 187 | comment | `複数キュー` | queue |
| 217 | comment | `全て含まれる` |  |
| 230 | comment | `エッジケース` |  |
| 248 | string | `名前空でもエラーにならない` | error |
| 251 | comment | `クラッシュしないこと` |  |

### `tests\test_gui_roundtrip.py` （56 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `自動テスト（ ）` |  |
| 5 | other | `を実際にインスタンス化し` |  |
| 6 | other | `の一連の流れを自動実行して` | execute |
| 7 | other | `がどう変化するかを検証する` |  |
| 9 | other | `での実行` | execute |
| 13 | other | `での実行` | execute |
| 17 | comment | `配下の全` |  |
| 20 | other | `環境変数` | variable |
| 21 | other | `が自動設定される（ヘッドレス実行）` | execute / settings |
| 31 | comment | `を モードで起動（ 表示なし）` | start |
| 34 | comment | `プロジェクトルート解決（ から 階層上）` | layer |
| 42 | comment | `正規化（差分比較用）` |  |
| 54 | string | `つの の差分を要約` |  |
| 71 | string | `の差分を詳細分析` |  |
| 110 | comment | `実行` | execute |
| 115 | other | `を 経由で する` |  |
| 117 | other | `をモンキーパッチして 以下を自動実行` | execute |
| 118 | other | `インスタンス化` |  |
| 119 | other | `自動補完` |  |
| 132 | comment | `のインポートと 準備` | ready |
| 144 | comment | `のインポート` |  |
| 153 | comment | `出力先一時ファイル` |  |
| 164 | comment | `をモンキーパッチ` |  |
| 180 | comment | `がブロックしないよう無効化` |  |
| 195 | comment | `生成` |  |
| 207 | comment | `比較` |  |
| 219 | string | `経由でも完全一致` |  |
| 232 | string | `経由で自動補完` |  |
| 239 | string | `自動補完以外の差分あり 要調査` |  |
| 249 | comment | `モンキーパッチを復元` |  |
| ... | ... | （他 26 行）| |

### `tests\test_interrupt_generator.py` （38 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `のユニットテスト` |  |
| 5 | other | `目的` |  |
| 6 | other | `生成の回帰防止` |  |
| 7 | other | `アクション解析（ そのまま）` | action |
| 8 | other | `使用ロール関数・変数の自動抽出` | role function / variable / function |
| 9 | other | `関数の完全生成` | function |
| 10 | other | `層名による名前空間変換` | namespace / layer |
| 11 | other | `マーカー名生成` | marker |
| 13 | other | `対象` |  |
| 23 | comment | `ヘルパー` |  |
| 35 | comment | `名前生成` |  |
| 48 | comment | `変換でアンダースコアが除去される想定` |  |
| 59 | comment | `アクション解析` | action |
| 86 | string | `層なし` | layer |
| 92 | string | `キーワードはそのまま` |  |
| 99 | string | `既に で始まる場合はそのまま` |  |
| 105 | string | `その他の 文はそのまま` |  |
| 123 | comment | `アクション 条件` | condition / action |
| 144 | comment | `使用シンボル抽出` |  |
| 198 | comment | `完全生成` |  |
| 252 | comment | `空ハンドラ` |  |
| 259 | other | `アクションが空の場合の 生成` | action |
| 261 | other | `実装仕様` |  |
| 262 | other | `が空なら は空リストを返す` |  |
| 263 | other | `アクション部分はセクションごと出力されない` | action |
| 264 | other | `アクション未定義 コメントは が非空だが` | definition / action |
| 265 | other | `全アクションがパース失敗した場合にのみ出力される` | failure / action |
| 270 | comment | `基本構造は生成される` |  |
| 273 | comment | `アクションが空 アクションセクションが出力されない` | action |
| 274 | string | `アクション（自動生成）` | action |
| ... | ... | （他 8 行）| |

### `tests\test_mermaid_gen.py` （44 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `のユニットテスト` |  |
| 5 | other | `目的` |  |
| 6 | other | `ラベルサニタイズの回帰防止` |  |
| 7 | other | `タイトル イベント名 条件式に含まれる特殊文字でパースエラーが出ないこと` | event / error / title / condition |
| 9 | other | `背景` |  |
| 10 | string | `で のようにタイトルに が` | title |
| 11 | other | `含まれると がパースエラーを起こす問題を修正` | error |
| 12 | other | `で全角に置換して回避` |  |
| 22 | comment | `ヘルパー` |  |
| 28 | other | `遷移を持つ を構築` | transition |
| 30 | other | `修正 イベントを に事前登録する` | event |
| 31 | other | `（ は が登録済みであることを要求）` |  |
| 50 | string | `特定の遷移行を抽出` | transition |
| 58 | comment | `のユニットテスト（全て 済）` |  |
| 64 | string | `コロンが全角に置換される` |  |
| 65 | string | `：` |  |
| 68 | string | `角括弧が全角に置換される` |  |
| 69 | string | `［` |  |
| 70 | string | `］` |  |
| 73 | string | `ダブルクォートがシングルに置換される` |  |
| 77 | string | `改行が空白に置換される` |  |
| 81 | string | `空文字列はそのまま空` |  |
| 85 | string | `を渡してもエラーにならない` | error |
| 89 | string | `連続空白が つに正規化される` |  |
| 94 | comment | `の統合テスト（修正済）` |  |
| 100 | string | `基本構造が出力される` |  |
| 101 | string | `起動` | start |
| 108 | string | `タイトル内の がパースエラーを起こさない（本件の再発防止）` | error / title |
| 115 | comment | `区切りの は 個のみ（タイトル内は全角に置換済）` | title |
| 117 | string | `：` |  |
| ... | ... | （他 14 行）| |

### `tests\test_role_function_generator.py` （54 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `のユニットテスト` |  |
| 5 | other | `目的` |  |
| 6 | other | `ロール関数生成の回帰防止` | role function / function |
| 7 | other | `命名規則（ ）` |  |
| 8 | other | `参照正規化（ 識別子検証）` |  |
| 9 | other | `条件式からの関数抽出` | condition / function |
| 10 | other | `呼び出しサイト収集（ ）` |  |
| 11 | other | `層フィルタ（ ）` | layer |
| 12 | other | `宣言生成 実装生成` |  |
| 13 | other | `一括生成` |  |
| 14 | other | `マーカー名生成` | marker |
| 15 | other | `ガード` | guard |
| 17 | other | `対象` |  |
| 32 | comment | `ヘルパー` |  |
| 61 | comment | `命名規則` |  |
| 78 | string | `未設定時は を採用` | settings |
| 129 | comment | `参照正規化（ 識別子検証）` |  |
| 161 | comment | `識別子検証` |  |
| 163 | string | `演算子混入を拒否` |  |
| 193 | comment | `条件式からの関数抽出` | condition / function |
| 216 | string | `予約語は抽出されない` |  |
| 222 | string | `式中の 識別子を検出` |  |
| 240 | comment | `呼び出しサイト収集` |  |
| 297 | string | `不正な識別子（ ）は収集されない` |  |
| 312 | comment | `呼び出しサイト取得` |  |
| 333 | comment | `層フィルタ` | layer |
| 339 | string | `自層の関数は出力` | function / layer |
| 346 | string | `他層の関数で呼び出し元なし スキップ` | function / layer |
| 353 | string | `他層の関数でも呼び出し元あり 出力` | function / layer |
| 364 | string | `なしの呼び出しでマッチ` |  |
| ... | ... | （他 24 行）| |

### `tests\test_state_machine.py` （42 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `のユニットテスト` |  |
| 5 | other | `目的` |  |
| 6 | other | `コアロジックの回帰防止` |  |
| 7 | other | `状態 イベント 遷移 ロール関数の追加・削除` | state / event / transition / role function / function |
| 8 | other | `整合性チェック（未定義参照の拒否）` | definition |
| 9 | other | `遷移削除の連鎖（ で関連遷移も削除）` | transition |
| 10 | other | `セル単位 イベント単位の遷移取得` | event / transition |
| 11 | other | `の値等価性（ ）` |  |
| 13 | other | `対象` |  |
| 23 | comment | `ヘルパー` |  |
| 27 | string | `状態 イベント 遷移` | state / event / transition |
| 37 | comment | `状態` | state |
| 62 | comment | `イベント` | event |
| 85 | string | `存在しないイベントの削除は無視される（例外なし）` | event / ignore |
| 87 | other | `例外が出ないこと` |  |
| 91 | string | `イベント削除で関連遷移も削除される` | event / transition |
| 109 | comment | `遷移` | transition |
| 140 | string | `が空（内部遷移）でも登録可能` | transition |
| 148 | string | `が空（完了遷移）でも登録可能` | transition / completed |
| 163 | other | `値が異なる遷移を渡しても 何も削除されない` | transition |
| 165 | other | `注 は のため` |  |
| 166 | other | `値が等しい つのインスタンスは で等価と見なされる` |  |
| 167 | other | `よって 存在しない を検証するには` |  |
| 168 | other | `値が異なる遷移を渡す必要がある` | transition |
| 171 | comment | `値が異なる遷移（ が違う）` | transition |
| 173 | other | `例外なし` |  |
| 178 | other | `値が等しい遷移を渡すと 既存の遷移が削除される` | transition |
| 180 | other | `（ の意図的な動作）` |  |
| 183 | comment | `値が同じ別インスタンス` |  |
| 189 | string | `同じセルに複数遷移を登録可能（条件分岐）` | transition / condition |
| ... | ... | （他 12 行）| |

### `tests\test_struct_generator.py` （19 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `のユニットテスト` |  |
| 5 | other | `目的` |  |
| 6 | other | `コード生成（ 部分）の回帰防止` |  |
| 7 | other | `の生成` |  |
| 8 | other | `の追加（ ）` |  |
| 9 | other | `共通 と層別 の分離` | layer |
| 10 | other | `マクロ（ ）` |  |
| 11 | other | `カスタム型 ビットフィールド 配列メンバー` | type |
| 13 | other | `対象` |  |
| 26 | comment | `ヘルパー` |  |
| 56 | string | `カウンタ` | counter |
| 110 | string | `が追加される` |  |
| 127 | comment | `共通` |  |
| 142 | comment | `層別` | layer |
| 163 | comment | `マクロ` |  |
| 184 | comment | `カスタム型` | type |
| 194 | comment | `の実装により などになる想定` |  |
| 252 | comment | `形式` |  |
| 277 | comment | `後方互換` |  |

### `tests\test_timer_generator.py` （24 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `のユニットテスト` |  |
| 5 | other | `目的` |  |
| 6 | other | `タイマ生成ロジックの回帰防止` | timer |
| 7 | other | `以降は空を返す（ 廃止）` |  |
| 8 | other | `の生成` |  |
| 9 | other | `派生タイマ計算` | timer |
| 10 | other | `チェック` |  |
| 11 | other | `の取り扱い` |  |
| 13 | other | `対象` |  |
| 25 | comment | `ヘルパー` |  |
| 29 | string | `基本タイマ（ ）を持つ` | timer |
| 40 | string | `基本 派生タイマ（ ）` | timer |
| 52 | comment | `（ 空を返す）` |  |
| 58 | string | `廃止 空文字を返す` |  |
| 70 | comment | `タイマ一覧取得` | timer |
| 149 | string | `派生タイマ` | timer |
| 158 | string | `派生なしの場合は計算行が出力されない` |  |
| 162 | comment | `基本構造のみ（計算行なし）` |  |
| 192 | comment | `は空なので含まれない` |  |
| 194 | comment | `は含まれる` |  |
| 200 | comment | `エッジケース` |  |
| 206 | string | `空の でもエラーにならない` | error |
| 219 | string | `の場合は除算を出力しない（ゼロ除算回避）` |  |
| 229 | comment | `の除算行は出力されない` |  |

### `tests\test_transition_generator.py` （31 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `のユニットテスト` |  |
| 5 | other | `目的` |  |
| 6 | other | `遷移生成ロジックの回帰防止` | transition |
| 7 | other | `セル単位の遷移関数（前方宣言 実装）` | transition / function |
| 8 | other | `遷移テーブル（ ）` | transition |
| 9 | other | `関数ディクショナリ` | function |
| 10 | other | `関数` | function |
| 11 | other | `関数` | function |
| 12 | other | `層名プレフィックス命名規則` | layer |
| 13 | other | `短縮セル関数名（ ）` | function |
| 15 | other | `対象` |  |
| 26 | comment | `ヘルパー` |  |
| 30 | string | `基本構造の を生成` |  |
| 39 | string | `起動` | start |
| 41 | string | `停止` | stop |
| 46 | comment | `命名規則` |  |
| 98 | comment | `セル単位の遷移関数` | transition / function |
| 113 | comment | `などが生成される` |  |
| 143 | comment | `が含まれる` |  |
| 148 | comment | `遷移テーブル` | transition |
| 179 | comment | `未実装の でも にフォールバック` |  |
| 193 | comment | `関数ディクショナリ` | function |
| 217 | comment | `関数` | function |
| 251 | comment | `関数` | function |
| 274 | comment | `形式` |  |
| 300 | comment | `後方互換` |  |
| 309 | comment | `前方宣言 テーブル 実装 が含まれる` |  |
| 316 | comment | `エッジケース` |  |
| 325 | comment | `空でも例外が出ない` |  |
| 334 | string | `内部` |  |
| ... | ... | （他 1 行）| |

### `tests\test_variable_generator.py` （25 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `のユニットテスト` |  |
| 5 | other | `目的` |  |
| 6 | other | `コード生成（変数マクロ・初期化関数）の回帰防止` | initialization / variable / function |
| 7 | other | `（フィールド名 ）` |  |
| 8 | other | `カスタム型の 初期化（ 修正）` | initialization / type |
| 9 | other | `配列変数の 初期化` | initialization / variable |
| 10 | other | `フラグアクセスマクロ` | flag |
| 11 | other | `関数の構造` | function |
| 13 | other | `対象` |  |
| 25 | comment | `ヘルパー` |  |
| 38 | comment | `データアクセスマクロ（ 修正の回帰防止）` |  |
| 44 | string | `マクロ名は` |  |
| 52 | other | `修正 フィールド名は のまま` |  |
| 53 | other | `（旧バグ ）` |  |
| 62 | string | `キャメルケースの変数 マクロ フィールドは` | variable |
| 67 | comment | `の実装次第だが フィールドは 系` |  |
| 127 | comment | `初期化コード生成` | initialization |
| 140 | string | `修正 カスタム型は で初期化` | initialization / type |
| 169 | comment | `関数` | function |
| 178 | comment | `が含まれる` |  |
| 180 | other | `チェック` |  |
| 181 | other | `初期化` | initialization |
| 200 | string | `の初期化` | initialization |
| 209 | comment | `形式` |  |
| 229 | comment | `後方互換` |  |

### `tests\test_xml_io.py` （46 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `のユニットテスト` |  |
| 5 | other | `目的` |  |
| 6 | other | `保存 読込のエッジケースと回帰防止` |  |
| 7 | other | `空プロジェクトの` |  |
| 8 | other | `特殊文字 を含む文字列の` |  |
| 9 | other | `レガシー （ 未設定）の自動移行` | settings |
| 10 | other | `の 文字分解救済` |  |
| 11 | other | `共有ライブラリ（ ）の` |  |
| 12 | other | `プロジェクト設定（ ）の` | settings |
| 13 | other | `グローバル定義（変数・フラグ・割り込み・タイマ）の` | definition / variable / flag / interrupt / timer |
| 15 | other | `対象` |  |
| 35 | comment | `ヘルパー` |  |
| 40 | string | `保存 読込の往復` |  |
| 53 | string | `ファイルを正規化して比較しやすくする` |  |
| 80 | string | `文字ずつに分解された旧データを結合` |  |
| 92 | comment | `空プロジェクトの` |  |
| 98 | string | `状態・イベント・遷移なしの が往復する` | state / event / transition |
| 113 | comment | `特殊文字 の` |  |
| 120 | string | `待機` | idle |
| 121 | string | `動作中` | running |
| 127 | string | `待機 動作中` | idle / running |
| 130 | string | `タイトル内の が で保持される` | title |
| 147 | string | `を含む文字列が エスケープで保持される` |  |
| 154 | string | `同時` |  |
| 160 | string | `同時` |  |
| 164 | comment | `レガシー 自動移行` |  |
| 171 | string | `未設定` | settings |
| 173 | comment | `レガシー を直接生成` |  |
| 182 | string | `初期化` | initialization |
| 200 | string | `移行後の再保存 再読込で安定（冪等）` |  |
| ... | ... | （他 16 行）| |

### `tests\timer_generator.py` （16 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `タイマ変数生成モジュール（完全データ駆動版）` | variable / timer |
| 5 | other | `修正` |  |
| 6 | other | `を廃止` |  |
| 7 | other | `タイマ変数は 内に 経由で` | variable / timer |
| 8 | other | `既に展開されているため 未使用の を出力しない` |  |
| 33 | string | `タイマ変数生成クラス（完全データ駆動）` | variable / timer |
| 117 | string | `タイマ変数構造体 システム全体で使用するタイマ変数を管理` | variable / timer / system |
| 149 | string | `タイマ変数初期化` | initialization / variable / timer |
| 150 | string | `システムコンテキストポインタ` | system / context / pointer |
| 204 | string | `タイマ更新処理` | timer |
| 205 | string | `システムコンテキストポインタ` | system / context / pointer |
| 232 | other | `タイマ変数構造体生成` | variable / timer |
| 234 | other | `変更` |  |
| 235 | other | `タイマ変数は 内に既に展開されており` | variable / timer |
| 236 | other | `は使用されていなかった（ ）` |  |
| 237 | other | `後方互換のため関数自体は残すが 空文字列を返すように変更` | function |

## カテゴリ H: その他

### `statable\__init__.py` （9 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `データモデル層` | layer |
| 5 | other | `主要クラスを再エクスポートし 外部からの利用を簡便にする` |  |
| 7 | other | `追加` |  |
| 8 | other | `循環インポート回避のため 依存の軽いモジュールのみ再エクスポート` |  |
| 9 | other | `は意図的に除外` |  |
| 10 | other | `（これらは重い依存を持ち 循環参照の原因になるため）` |  |
| 13 | comment | `（依存なし） 最初にロードすべき` |  |
| 25 | comment | `（ に依存）` |  |
| 28 | comment | `（依存なし）` |  |

### `statable\global_defs.py` （43 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 1 | string | `グローバル変数・イベントフラグ・割り込み処理・デバイスリソース・タイマ設定・ユーザー定義型のデータモデル` | event / settings / definition / variable / flag / interrupt  |
| 9 | string | `構造体メンバ定義` | definition |
| 24 | string | `メンバ` |  |
| 29 | string | `ユーザー定義型（構造体など）` | definition / type / user |
| 37 | string | `型` | type |
| 42 | string | `システム全体で共有するグローバル変数` | variable / system |
| 57 | string | `変数` | variable |
| 62 | string | `ビットフィールドで扱うイベントフラグ` | event / flag |
| 72 | string | `フラグ` | flag |
| 83 | string | `割り込み処理内の条件付きアクション` | interrupt / condition / action |
| 90 | other | `割り込み処理定義` | definition / interrupt |
| 92 | other | `使用ロール関数の リスト（自動抽出）` | role function / function |
| 93 | other | `例` |  |
| 94 | other | `の 保存時に更新` |  |
| 95 | other | `生成コードのコメントにも使用` |  |
| 97 | other | `使用グローバル変数名のリスト（自動抽出）` | variable |
| 98 | other | `例` |  |
| 106 | comment | `追加 使用記録` |  |
| 112 | string | `割り込み` | interrupt |
| 117 | string | `デバイスリソース仮定義` | definition |
| 124 | string | `デバイス` |  |
| 129 | string | `派生タイマ変数定義` | definition / variable / timer |
| 138 | string | `タイマ` | timer |
| 143 | string | `タイマ刻み変数定義` | definition / variable / timer |
| 153 | string | `タイマ基準` | timer |
| 158 | string | `イベントキュー定義` | event / definition / queue |
| 171 | string | `キュー` | queue |
| 175 | string | `グローバル変数・イベントフラグ・割り込み処理・デバイスリソース・タイマ設定・イベントキュー・ユーザー定義型の管理クラス` | event / settings / definition / variable / flag / interrupt  |
| 188 | other | `タイマ基準変数・派生タイマ変数をグローバル変数として登録する` | variable / timer |
| 190 | other | `既存変数（ 読込 編集済）は を保持` | variable |
| ... | ... | （他 13 行）| |

### `statable\mermaid_gen.py` （37 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 5 | comment | `ラベル用サニタイズ（ 追加）` |  |
| 8 | comment | `のラベルで問題になる文字と代替` |  |
| 10 | comment | `状態遷移ラベルの区切り文字と誤認される` | state / transition |
| 11 | comment | `例` |  |
| 12 | comment | `タイトル内の でパースエラー` | error / title |
| 15 | comment | `条件ブロック記法と競合する可能性` | condition |
| 16 | comment | `二重の が混ざるとパース失敗` | failure |
| 18 | comment | `引用符がラベル全体の終端と誤認される` |  |
| 20 | comment | `ラベルは 行のみ有効 空白に正規化` |  |
| 22 | comment | `コードブロックと誤認される可能性` |  |
| 25 | string | `： コロン 全角コロン` |  |
| 26 | string | `［ 開き角括弧 全角` |  |
| 27 | string | `］ 閉じ角括弧 全角` |  |
| 28 | other | `ダブルクォート シングル` |  |
| 29 | other | `バッククォート シングル` |  |
| 30 | other | `改行 空白` |  |
| 37 | other | `のラベル文字列を安全化する` |  |
| 39 | other | `ユーザー入力のタイトル・イベント名・条件式に` | event / title / condition / user |
| 40 | other | `のメタ文字が含まれていても パースエラーを` | error |
| 41 | other | `起こさないように置換する` |  |
| 43 | other | `例` |  |
| 45 | string | `：` |  |
| 51 | comment | `連続空白を単一に正規化` |  |
| 57 | string | `長い状態遷移条件を省略表示する（改行は先頭行のみ）` | state / transition / condition |
| 61 | comment | `改行がある場合は先頭行だけ使用` |  |
| 69 | comment | `行目以降があれば省略記号を付与` |  |
| 77 | other | `から 形式の文字列を生成する` |  |
| 79 | other | `ラベル（タイトル イベント名 条件式）はすべて` | event / title / condition |
| 80 | other | `で正規化してパースエラーを防止する` | error |
| 90 | comment | `タイトル（無題遷移以外）` | transition / title |
| ... | ... | （他 7 行）| |

### `statable\model.py` （49 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 24 | string | `イベントの配送方法` | event |
| 31 | string | `イベントの発生源レイヤ` | event / layer |
| 49 | string | `状態遷移イベント（ドライバ層・ミドル層から通知される）` | state / event / transition / layer / driver |
| 64 | string | `イベント イベント （完了）` | event / completed |
| 70 | other | `状態遷移定義` | state / transition / definition |
| 72 | other | `変更 化` |  |
| 73 | other | `位置引数によるフィールド順序ずれ事故（ ）を` | argument |
| 74 | other | `構造的に防止するため 引数のみ受け付ける` | argument |
| 76 | other | `旧 位置引数（危険）` | argument |
| 77 | other | `新 のみ` |  |
| 79 | other | `で` |  |
| 80 | other | `の全 箇所が 済みであることを 監査で確認済み` |  |
| 82 | other | `既知の制約 は予約フィールド` |  |
| 83 | other | `通常遷移（既定値 実装済み）` | transition |
| 84 | other | `状態を出ず のみ実行（ 未実装・予約 ）` | state / execute |
| 85 | other | `自己遷移（ 未実装・予約 ）` | transition |
| 87 | other | `時点で は未実装 生成コード` |  |
| 88 | other | `（ ）は を参照せず` |  |
| 89 | other | `常に 相当（ へ遷移）として扱う` | transition |
| 91 | other | `影響` |  |
| 92 | other | `（ ）に遷移種別列は表示されない` | transition |
| 93 | other | `生成コードで 呼び分けは行われない` |  |
| 94 | other | `保存 読込では値が保持される（ は維持）` |  |
| 96 | other | `予約理由` |  |
| 97 | other | `呼び出し制御は` |  |
| 98 | other | `（ テンプレート群）に広く影響するため` |  |
| 99 | other | `では仕様を凍結し で段階的に実装する` |  |
| 101 | other | `参照 （一貫性チェック検出）` |  |
| 105 | other | `条件式（シンボル名で保持）` | condition |
| 106 | other | `遷移直前処理` | transition |
| ... | ... | （他 19 行）| |

### `statable\parser.py` （39 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `パーサー（未実装スタブ）` |  |
| 6 | other | `現状は未実装のスタブ` |  |
| 7 | other | `の入出力は が担当している` |  |
| 9 | other | `将来実装予定` |  |
| 10 | other | `読み込み` |  |
| 11 | other | `等を使用して状態遷移表を取り込む` | state / transition |
| 12 | other | `読み込み` |  |
| 13 | other | `状態 イベントのマトリクス形式を想定` | state / event |
| 14 | other | `読み込み` |  |
| 15 | other | `外部ツール連携用の汎用フォーマット` |  |
| 17 | other | `注意` |  |
| 18 | other | `このモジュールは現時点で呼び出し元が存在しない` |  |
| 19 | other | `実装する際は の` |  |
| 20 | other | `に変換すること` |  |
| 21 | other | `既存の と同じインターフェース` |  |
| 22 | other | `（ 相当）を目指すのが望ましい` |  |
| 24 | other | `実装しない場合` |  |
| 25 | other | `このファイル自体を削除しても問題ない` |  |
| 26 | other | `呼び出し元がないため 削除しても影響はない` |  |
| 30 | comment | `未実装マーカー` | marker |
| 32 | comment | `以下は将来実装する予定のプレースホルダ` |  |
| 33 | comment | `実装するまでは呼び出さないこと` |  |
| 35 | other | `公開 なし（未実装のため）` |  |
| 39 | string | `の機能が未実装であることを示す例外` |  |
| 45 | other | `ファイルから状態遷移データを読み込む（未実装）` | state / transition |
| 48 | other | `読み込む ファイルパス` |  |
| 51 | other | `常に送出（未実装のため）` |  |
| 54 | string | `は未実装です` |  |
| 55 | string | `現状は を使用してください` |  |
| 61 | other | `ファイルから状態遷移データを読み込む（未実装）` | state / transition |
| ... | ... | （他 9 行）| |

### `statable\state_machine.py` （4 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 14 | comment | `レイヤ設定` | settings / layer |
| 15 | other | `実行優先度（ ）` | execute / priority |
| 16 | other | `層の説明（任意）` | description / layer |
| 17 | string | `層名（例 ）` | layer |

### `statable\xml_io.py` （42 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `入出力（プロジェクト設定・レイヤ優先度・層名・名前空間対応版）` | settings / namespace / layer / priority / layer |
| 4 | other | `プロジェクト保存 読込で共有ライブラリを保存` |  |
| 5 | other | `の も保存` |  |
| 6 | other | `文字列 リスト正規化 文字分解の自動結合` |  |
| 7 | other | `レイヤ優先度・説明・層名（ ）・プロジェクト名の保存 復元` | description / layer / priority / layer |
| 8 | other | `の 保存 復元` |  |
| 9 | other | `の 保存 復元` |  |
| 10 | other | `レガシー （ 無し）の自動移行` |  |
| 31 | comment | `共有ライブラリ（インポート失敗時は ）` | failure |
| 40 | comment | `ヘルパー 文字列 リストの正規化` |  |
| 44 | other | `を必ず に正規化する` |  |
| 48 | other | `文字リスト 旧バージョンの壊れたデータ救済` |  |
| 56 | comment | `文字ずつに分解された古いデータを検出して結合` |  |
| 61 | comment | `通常のリスト` |  |
| 79 | comment | `レイヤ設定` | settings / layer |
| 117 | comment | `に 属性を追加` |  |
| 135 | comment | `正規化 文字列や分解済みリストを必ず正しいリストに変換` |  |
| 169 | comment | `レイヤ設定` | settings / layer |
| 218 | comment | `読込 レガシー移行` |  |
| 225 | comment | `レガシー移行 未設定 が層名プレフィックス付き` | settings / layer |
| 255 | comment | `生のリストを取得` |  |
| 259 | comment | `正規化（ 文字分解されていれば結合）` |  |
| 375 | comment | `対応` |  |
| 389 | comment | `使用ロール関数・変数を記録` | role function / variable / function |
| 484 | comment | `復元` |  |
| 494 | comment | `使用ロール関数・変数を復元` | role function / variable / function |
| 559 | comment | `共有ライブラリ` |  |
| 584 | other | `は のみ受け付けるため` |  |
| 585 | other | `それ以外の属性は で確認してから する` |  |
| 595 | comment | `が受け付ける引数のみで生成` | argument |
| ... | ... | （他 12 行）| |

### `tools\check_all_specs.py` （7 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `配下の全 で 一貫性チェックを実行` | execute |
| 5 | other | `使い方` |  |
| 17 | string | `対象 件` |  |
| 36 | comment | `標準エラー（ ログ）を表示` | error |
| 41 | comment | `レポートから 結果を抽出` |  |
| 54 | string | `レポート未生成` |  |
| 56 | string | `サマリ` |  |

### `tools\consistency_check.py` （85 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `一貫性チェックツール 完全版` |  |
| 5 | other | `検査内容` |  |
| 7 | other | `方式（ 本実装）` |  |
| 8 | other | `方式（汎用フォールバック）` |  |
| 9 | other | `データクラスフィールド突き合わせ モデル定義 各層の出現箇所` | definition / layer |
| 10 | other | `フィールドは 予約 として明示（ 扱いしない）` |  |
| 11 | other | `使用箇所 の メンバーが他ファイルで使われているか` |  |
| 12 | other | `メンバーは 予約 として明示` |  |
| 13 | other | `生成 コード整合性` |  |
| 14 | other | `の有無` |  |
| 15 | other | `が を しているか` |  |
| 16 | other | `全層横断でプロトタイプの定義が存在するか` | definition / layer |
| 17 | other | `所有層（ ）の に定義があるか` | definition / layer |
| 19 | other | `使い方` |  |
| 20 | comment | `全検査（デフォルト引数で動作）` | argument |
| 23 | comment | `のみ` |  |
| 26 | comment | `生成 コード検査をスキップ` |  |
| 29 | other | `終了コード` |  |
| 30 | other | `全 （ 含む）` |  |
| 31 | other | `つ以上` |  |
| 33 | other | `変更履歴` |  |
| 34 | other | `対応 フィールド導入` |  |
| 35 | other | `生成 検査を全層横断方式に修正（ 案 対応）` | layer |
| 51 | comment | `予約フィールド 予約 メンバー定義（ 由来）` | definition |
| 54 | comment | `クラス名 フィールド名` |  |
| 56 | other | `未実装` |  |
| 57 | other | `旧互換用` |  |
| 60 | comment | `名 メンバー名` |  |
| 62 | comment | `拡張状態（将来実装予定）` | state |
| 67 | comment | `以外のイベント種別（将来実装予定）` | event |
| ... | ... | （他 55 行）| |

### `tools\consistency_checks.py` （16 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 2 | string | `一貫性チェック コアロジック（ 非依存）` |  |
| 63 | string | `一貫性チェック本体 各 メソッドが を返す` |  |
| 118 | string | `正規化後 完全一致` |  |
| 121 | string | `差分あり` |  |
| 131 | comment | `フィールドマトリクス` |  |
| 157 | string | `対象クラス未検出` |  |
| 182 | string | `クラス フィールド 未参照` |  |
| 185 | comment | `使用箇所` |  |
| 216 | string | `未検出` |  |
| 242 | string | `メンバー 未参照` |  |
| 245 | comment | `生成 コード整合性` |  |
| 258 | string | `なし` |  |
| 265 | string | `未` |  |
| 280 | string | `定義なしプロトタイプ` | definition |
| 283 | string | `検出 件` |  |
| 287 | comment | `全実行` | execute |

### `tools\purge_unused_files.py` （83 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `未使用ファイル削除ツール（ 前提・物理削除版）` |  |
| 5 | other | `前提 プロジェクトが 管理下にあり が であること` |  |
| 7 | other | `使い方` |  |
| 8 | other | `ドキュメント` |  |
| 10 | comment | `調査のみ` |  |
| 13 | comment | `物理削除（ は使わず ファイル削除のみ）` |  |
| 16 | comment | `削除後に で復元する場合` |  |
| 17 | comment | `削除前にコミット済みなら` |  |
| 18 | other | `個別` |  |
| 19 | other | `全部` |  |
| 21 | other | `設計` |  |
| 22 | other | `入口` |  |
| 23 | other | `追跡 で 解析 再帰探索` |  |
| 24 | other | `削除 で物理削除` |  |
| 25 | other | `削除前に 状態をチェック` | state |
| 38 | comment | `設定` | settings |
| 41 | other | `リポジトリルート（要調整）` |  |
| 61 | comment | `動的 で使われるモジュール（誤削除防止）` |  |
| 95 | comment | `状態チェック` | state |
| 98 | string | `リポジトリの状態をチェック` | state |
| 99 | string | `状態チェック` | state |
| 101 | comment | `リポジトリかどうか` |  |
| 109 | string | `リポジトリではありません` |  |
| 110 | string | `場所` |  |
| 113 | string | `コマンドが見つかりません` |  |
| 116 | string | `実行エラー` | error / execute |
| 119 | comment | `が か` |  |
| 127 | string | `失敗` | failure |
| 132 | string | `は です` |  |
| 136 | string | `未コミットの変更が 件あります` |  |
| ... | ... | （他 53 行）| |

### `tools\remove_libcntrl_tryexcept.py` （45 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `移行支援ツール 一括削除` |  |
| 5 | other | `用途` |  |
| 8 | other | `パターンを検出し を削除して` |  |
| 9 | other | `に統一` |  |
| 10 | other | `なしの も` |  |
| 11 | other | `に置換` |  |
| 13 | other | `修正` |  |
| 14 | other | `削除 本体を （正しい）` |  |
| 15 | other | `維持（ しない）` |  |
| 16 | other | `直下の最初のコード行が の場合のみ処理` |  |
| 17 | other | `（外側の を誤検出しない）` |  |
| 19 | other | `使い方` |  |
| 57 | comment | `ヘルパー` |  |
| 81 | string | `コメント・空行を除いた最初のコード行を返す` |  |
| 93 | comment | `ブロック検出` |  |
| 140 | comment | `変換ロジック` |  |
| 186 | comment | `直下の最初のコード行が か` |  |
| 201 | comment | `を削除し 本体を して残す` |  |
| 222 | comment | `構造は維持 本体の のみ置換` |  |
| 223 | comment | `はしない！` |  |
| 241 | comment | `でない 外側の 何もせず素通り` |  |
| 242 | comment | `（次の行から入れ子の を個別に処理）` |  |
| 244 | comment | `単独の を置換` |  |
| 268 | comment | `ファイル走査` |  |
| 325 | comment | `レポート出力` |  |
| 333 | string | `削除レポート` |  |
| 335 | string | `スキャン対象ファイル数` |  |
| 336 | string | `修正対象ファイル数` |  |
| 338 | string | `エラー` | error |
| 343 | string | `要修正` |  |
| ... | ... | （他 15 行）| |

### `tools\scan_japanese.py` （180 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `日本語テキスト調査ツール` |  |
| 5 | other | `目的` |  |
| 6 | other | `リリース用に日本語 英語へ変換するため` |  |
| 7 | other | `どのファイルにどの日本語が含まれているかを調査する` |  |
| 9 | other | `スキャン対象` |  |
| 10 | other | `データモデル層` | layer |
| 11 | other | `層` | layer |
| 12 | other | `コード生成層` | layer |
| 13 | other | `開発支援ツール` |  |
| 14 | other | `テスト` |  |
| 16 | other | `カテゴリ分類` |  |
| 17 | other | `生成 コードコメント（最優先）` |  |
| 18 | other | `表示文言（最優先）` |  |
| 19 | other | `ログメッセージ` |  |
| 20 | other | `エラー・警告メッセージ` | error / warning |
| 21 | other | `コメント` |  |
| 22 | other | `サンプルデータ` |  |
| 23 | other | `テスト期待値` |  |
| 24 | other | `その他` |  |
| 26 | other | `使い方` |  |
| 27 | comment | `全スキャン` |  |
| 30 | comment | `特定カテゴリのみ` |  |
| 33 | comment | `特定ディレクトリのみ` |  |
| 36 | comment | `除外パターン` |  |
| 49 | comment | `定数` |  |
| 62 | comment | `日本語文字の 範囲` |  |
| 64 | other | `ひらがな` |  |
| 65 | other | `カタカナ` |  |
| 66 | other | `漢字（ 統合漢字）` |  |
| 67 | other | `全角記号` |  |
| ... | ... | （他 150 行）| |

### `tools\transition_audit.py` （37 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `移行支援ツール 化 監査ツール` |  |
| 5 | other | `用途` |  |
| 6 | other | `の全構築箇所を ベースで検出` |  |
| 7 | other | `位置引数 キーワード引数の分類` | argument |
| 8 | other | `化した際に になる箇所を事前に洗い出し` |  |
| 9 | other | `（任意） で位置引数をキーワード引数に自動変換` | argument |
| 11 | other | `使い方` |  |
| 33 | comment | `仕様書準拠 のフィールド順` |  |
| 109 | string | `展開あり（手動確認推奨）` |  |
| 111 | string | `位置引数 個 化で` | argument |
| 147 | comment | `ファイル走査` |  |
| 181 | comment | `位置引数 キーワード引数 変換` | argument |
| 243 | comment | `レポート出力` |  |
| 254 | string | `構築箇所 監査レポート` |  |
| 256 | string | `スキャン対象ファイル数` |  |
| 257 | string | `検出数` |  |
| 258 | string | `修正必要（位置引数あり）` | argument |
| 259 | string | `修正必要ファイル数` |  |
| 261 | string | `パースエラー` | error |
| 266 | string | `要修正 位置引数で構築されている箇所` | argument |
| 274 | string | `位置引数` | argument |
| 288 | string | `既に のみで構築されている箇所` |  |
| 298 | string | `パースエラー` | error |
| 306 | string | `位置引数構築はありません を 化できます` | argument |
| 308 | string | `箇所を に変換してから 化してください` |  |
| 317 | string | `化 移行支援ツール 用` |  |
| 319 | string | `スキャンするルートディレクトリ` |  |
| 321 | string | `対象クラス名（デフォルト ）` |  |
| 323 | string | `フィールド順（カンマ区切り） 時に使用` |  |
| 324 | string | `問題なしの箇所も表示` |  |
| ... | ... | （他 7 行）| |

### `tools\upgrade_specs.py` （25 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `配下の を新形式に一括変換` |  |
| 5 | other | `動作` |  |
| 6 | other | `各 を で読込` |  |
| 7 | other | `で新形式として保存` |  |
| 8 | other | `元ファイルは として退避` |  |
| 10 | other | `使い方` |  |
| 11 | comment | `ドライラン（変更内容を確認のみ ファイル書き換えなし）` |  |
| 14 | comment | `本実行（バックアップ作成 書き換え）` | execute |
| 17 | comment | `特定ファイルのみ` |  |
| 33 | string | `ファイルを新形式に変換` |  |
| 45 | comment | `読込` |  |
| 54 | comment | `ドライラン 一時ファイルに書き出して差分サイズのみ確認` |  |
| 69 | string | `変更内容を確認（ファイル未変更）` |  |
| 71 | comment | `本実行 バックアップ 上書き保存` | execute |
| 84 | string | `バックアップ` |  |
| 96 | string | `配下の を新形式に変換` |  |
| 100 | string | `個別ファイル指定（複数可） 未指定なら すべて` |  |
| 102 | string | `ファイルを書き換えず サイズ差分のみ確認` |  |
| 111 | string | `対象 が見つかりません` |  |
| 114 | string | `対象 件` |  |
| 116 | string | `ドライラン ファイルは書き換えません` |  |
| 142 | comment | `サマリ` |  |
| 143 | string | `サマリ` |  |
| 159 | string | `ドライラン完了 件` | completed |
| 161 | string | `変換完了 件 エラー 件` | error / completed |

### `tools\write_isr_test_xml.py` （89 行）

| 行 | 種別 | 日本語 | 英語ヒント |
|---|---|---|---|
| 3 | other | `を に書き出すスクリプト` |  |
| 5 | other | `使い方` |  |
| 6 | other | `ドキュメント` |  |
| 14 | comment | `出力先（ と つ上の の両方に書く）` |  |
| 45 | string | `汎用カウンタ カウンタ` | counter |
| 46 | string | `エラーコード エラーコード` | error / error code |
| 47 | string | `リトライ回数 リトライ回数` | retry |
| 48 | string | `準備完了 準備` | completed / ready |
| 49 | string | `受信データ データ` |  |
| 50 | string | `タイマ基準 システムタイマ` | timer / system |
| 51 | string | `派生タイマ タイマ` | timer |
| 55 | string | `初期化完了 初期化完了` | initialization / completed |
| 56 | string | `エラー発生 エラー` | error |
| 60 | string | `周期タイマ タイマ 割り込み` | interrupt / timer |
| 64 | string | `周期タイマ タイマ 割り込み` | interrupt / timer |
| 70 | string | `受信割り込み 受信割り込み` | interrupt |
| 76 | string | `割り込み 割り込み` | interrupt |
| 81 | string | `ドライバ補助割り込み ドライバ補助割り込み` | interrupt / driver |
| 90 | string | `システムタイマ基準` | timer / system |
| 91 | string | `タイマ` | timer |
| 103 | string | `ドライバ層` | layer / driver |
| 105 | string | `待機` | idle |
| 106 | string | `初期化中` | initialization |
| 107 | string | `準備完了` | completed / ready |
| 108 | string | `エラー` | error |
| 111 | string | `初期化要求 初期化` | initialization |
| 112 | string | `準備完了 準備完了` | completed / ready |
| 113 | string | `失敗通知 失敗` | failure |
| 114 | string | `リセット リセット` |  |
| 117 | string | `ドライバ初期化 ドライバ初期化` | initialization / driver |
| ... | ... | （他 59 行）| |
