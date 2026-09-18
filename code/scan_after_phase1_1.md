# StaTable 日本語テキスト調査レポート

## サマリ

- スキャンファイル数: 44
- 日本語を含むファイル数: 43
- 日本語を含む行数: 1222

## カテゴリ別集計

| カテゴリ | 説明 | 行数 | ファイル数 |
|---|---|---|---|
| A | 生成 C コードコメント（最優先） | 720 | 11 |
| C | コード生成層のログ等 | 502 | 32 |

## ファイル別集計（行数の多い順）

| ファイル | カテゴリ | 行数 |
|---|---|---|
| `codegen\c_code_generator.py` | A | 174 |
| `codegen\code_templates.py` | A | 143 |
| `codegen\struct_generator.py` | A | 108 |
| `codegen\role_function_generator.py` | A | 103 |
| `codegen\code_merger.py` | C | 78 |
| `codegen\validate\validation_dialog.py` | C | 72 |
| `codegen\variable_generator.py` | A | 60 |
| `codegen\validate\data\validation_rules.py` | C | 55 |
| `codegen\sample_data.py` | C | 50 |
| `codegen\validate\data\action_definitions.py` | C | 49 |
| `codegen\interrupt_generator.py` | A | 47 |
| `codegen\validate\change_applier.py` | C | 43 |
| `codegen\config.py` | C | 36 |
| `codegen\event_queue_generator.py` | A | 26 |
| `codegen\validate\data\prompt_templates.py` | C | 23 |
| `codegen\validate\data\keywords.py` | C | 21 |
| `codegen\enum_generator.py` | A | 20 |
| `codegen\timer_generator.py` | A | 16 |
| `codegen\validate\prompt_generator.py` | A | 12 |
| `codegen\osal_generator.py` | A | 11 |
| `codegen\validate\models.py` | C | 11 |
| `codegen\__init__.py` | C | 9 |
| `codegen\validate\logger.py` | C | 5 |
| `codegen\validate\validator.py` | C | 5 |
| `codegen\validate\items\event_validator.py` | C | 5 |
| `codegen\validate\items\transition_validator.py` | C | 5 |
| `codegen\naming_convention.py` | C | 4 |
| `codegen\validate\change_actions.py` | C | 3 |
| `codegen\validate\response_parser.py` | C | 3 |
| `codegen\type_mapper.py` | C | 2 |
| `codegen\validate\clipboard_manager.py` | C | 2 |
| `codegen\validate\items\base_validator.py` | C | 2 |
| `codegen\validate\items\custom_type_validator.py` | C | 2 |
| `codegen\validate\items\flag_validator.py` | C | 2 |
| `codegen\validate\items\interrupt_validator.py` | C | 2 |
| `codegen\validate\items\queue_validator.py` | C | 2 |
| `codegen\validate\items\role_function_validator.py` | C | 2 |
| `codegen\validate\items\state_validator.py` | C | 2 |
| `codegen\validate\items\timer_validator.py` | C | 2 |
| `codegen\validate\items\variable_validator.py` | C | 2 |
| `codegen\validate\__init__.py` | C | 1 |
| `codegen\validate\data\__init__.py` | C | 1 |
| `codegen\validate\items\__init__.py` | C | 1 |

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
