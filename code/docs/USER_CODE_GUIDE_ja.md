# StaTable ユーザーコード作成ガイド



本ガイドは、StaTable が生成する C コードに対して

**ユーザーが独自のロジック・インクルード・ヘルパー関数を追加する方法**を

体系的にまとめたものです。



- 対象バージョン: **StaTable v3.3.0 以降**

- 想定読者: 組込みエンジニア（C99 / MISRA C:2012 の基礎知識がある方）

- 関連ドキュメント:

&#x20; - TUTORIAL_ja.md — チュートリアル全般

&#x20; - SPEC_SDK_API_ja.md — SDK / 公開 API

&#x20; - SPEC_AUDIT_ja.md — マーカー契約の詳細

&#x20; - SPEC_CODEGEN_v3.md — コード生成の内部仕様

&#x20; - OSAL_PORTING_GUIDE_ja.md — RTOS 移植



---



## 1. ユーザーコード保護の全体像



### 1.1 なぜマーカーが必要か



StaTable は State Machine 設計から C コードを自動生成します。

設計変更のたびにコードを再生成すると、ユーザーが手で書いた実装が消えてしまう

という問題が発生します。



これを防ぐため、StaTable は生成コード内にマーカーを埋め込みます。



&#x20;   /* [[STABLE_USER_CODE_START:Driver_ReadCoinSensor]] */

&#x20;   /* ユーザーがここに実装を書く */

&#x20;   /* [[STABLE_USER_CODE_END:Driver_ReadCoinSensor]] */



再生成時、StaTable は:



1\. 既存ファイルから マーカー間の内容を抽出

2\. 新しい生成コードの 対応するマーカー間に再挿入



これにより、設計変更 → 再生成 → ユーザーコード保持 が自動化されます。



### 1.2 3 種のマーカー



| マーカー種別 | 用途 | 配置 |

|---|---|---|

| 関数レベル | ロール関数 / ISR の実装 | 各関数の内部 |

| ファイルレベル | #include 追加、ファイル全体で使う宣言 | include セクション直後 |

| ファイル末尾 | ヘルパー関数、静的データ | ファイル末尾 |



---



## 2. マーカー一覧



| # | マーカー | 用途 |

|---|---|---|

| 1 | STABLE_USER_CODE_START / END | ファイルレベル |

| 2 | STABLE_USER_CODE_START:<name> / END:<name> | 関数レベル |

| 3 | STABLE_USER_CODE_TAIL_START / END | ファイル末尾 |



name の形式:



- ロール関数: Layer_FunctionName （例: Driver_ReadCoinSensor）

- ISR: InterruptName （例: TIMER0）

- 状態アクション: Layer_Kind_State_custom （例: Driver_Do_Waiting_custom）



---



## 3. 関数レベル: ロール関数の実装



### 3.1 生成される雛形



StaTable は各ロール関数を次の形で生成します。



&#x20;   int RoleFunc_Driver_ReadCoinSensor(

&#x20;       const TransitionContext_Driver_t *transition,

&#x20;       SystemContext_t *ctx)

&#x20;   {

&#x20;       STATE_Driver_t from_state = STATE_Driver_MAX;

&#x20;       EVENT_Driver_t event = EVENT_Driver_NONE;

&#x20;       if (transition != NULL) {

&#x20;           from_state = transition->from_state;

&#x20;           event = transition->event;

&#x20;       }



&#x20;       const uint16_t transition_id = Transition_GetId(

&#x20;           transition, call_sites_ReadCoinSensor, ...);



&#x20;       uint32_t *const balance = \&ctx->data.balance;

&#x20;       uint32_t *const price = \&ctx->data.price;

&#x20;       /* ... 他の変数 ... */



&#x20;       int ret = 0;



&#x20;       /* [[STABLE_USER_CODE_START:Driver_ReadCoinSensor]] */

&#x20;       (void)from_state;

&#x20;       (void)event;

&#x20;       (void)transition_id;

&#x20;       (void)balance;

&#x20;       /* ... 未使用変数の抑制 ... */



&#x20;       /* Write user implementation code here */

&#x20;       /* [[STABLE_USER_CODE_END:Driver_ReadCoinSensor]] */



&#x20;       return ret;

&#x20;   }



### 3.2 ローカル変数の宣言（C99）



C99 準拠なので、ブロック内の任意の位置で変数宣言が可能です。



推奨: ネストブロックを使う



&#x20;   /* [[STABLE_USER_CODE_START:Driver_ReadCoinSensor]] */

&#x20;   (void)from_state;

&#x20;   (void)event;

&#x20;   /* 使わない変数の (void) は残す */

&#x20;   (void)stock;

&#x20;   (void)item_id;

&#x20;   (void)error_code;

&#x20;   (void)g_system_tick;



&#x20;   /* ネストブロックで変数宣言 */

&#x20;   {

&#x20;       uint32_t coin_in = 100;

&#x20;       *coin_value = coin_in;

&#x20;       *balance += coin_in;

&#x20;       if (*balance >= *price) {

&#x20;           ret = 1;

&#x20;       }

&#x20;   }

&#x20;   /* [[STABLE_USER_CODE_END:Driver_ReadCoinSensor]] */



利点: C89 でも合法、変数スコープが狭く可読性向上、再生成の影響を受けない。



代替: C99 の途中宣言



&#x20;   (void)g_system_tick;



&#x20;   uint32_t coin_in = 100;   /* C99 で合法 */



プロジェクトが C89 準拠を要求する場合はネストブロック必須。



### 3.3 (void) 抑制行の扱い



生成コードには未使用変数の警告を抑制する行が含まれます。



&#x20;   (void)from_state;   /* suppress unused warning */



使い始めた変数の (void) 行は削除してください。残しても無害ですが、

可読性のため削除推奨です。



| 操作 | 結果 |

|---|---|

| (void)balance; を残したまま *balance を使う | 動作するが冗長 |

| (void)balance; を削除して *balance を使う | 推奨 |

| 未使用のまま (void) を削除 | -Wunused-variable 警告 |



### 3.4 実例: 硬貨センサー読み取り



&#x20;   /* [[STABLE_USER_CODE_START:Driver_ReadCoinSensor]] */

&#x20;   (void)from_state;

&#x20;   (void)event;

&#x20;   (void)transition_id;

&#x20;   (void)stock;

&#x20;   (void)item_id;

&#x20;   (void)error_code;

&#x20;   (void)g_system_tick;



&#x20;   {

&#x20;       /* ハードウェアレジスタ（ユーザー定義）から硬貨種別を取得 */

&#x20;       uint32_t coin_in = Hw_CoinAcceptor_ReadValue();

&#x20;       if (coin_in > 0) {

&#x20;           *coin_value = coin_in;

&#x20;           *balance += coin_in;

&#x20;           ret = 1;   /* 遷移を許可 */

&#x20;       }

&#x20;   }

&#x20;   /* [[STABLE_USER_CODE_END:Driver_ReadCoinSensor]] */



---



## 4. ファイルレベル: include の追加（v3.3.0 新機能）



### 4.1 背景



関数レベルマーカー内で #include を書くと、その関数内でのみ有効です。

ファイル内の全関数から使える include を追加したい場合は、

ファイルレベルマーカーを使用します。



### 4.2 生成される雛形（v3.3.0 以降）



.c ファイルの include セクション直後に、空のファイルレベルマーカーが出力されます。



&#x20;   /*==============================================================

&#x20;    *  Include files

&#x20;    *==============================================================*/



&#x20;   #include "statable_role_functions_Driver.h"

&#x20;   #include "Middleware/statable_role_functions_Middleware.h"

&#x20;   #include "Application/statable_role_functions_Application.h"



&#x20;   /* [[STABLE_USER_CODE_START]] */

&#x20;   /* [[STABLE_USER_CODE_END]] */



&#x20;   /*==============================================================

&#x20;    *  Role function implementations

&#x20;    *==============================================================*/



### 4.3 手書きでの include 追加



&#x20;   /* [[STABLE_USER_CODE_START]] */

&#x20;   #include "my_hardware.h"

&#x20;   #include "custom_types.h"

&#x20;   /* [[STABLE_USER_CODE_END]] */



これで my_hardware.h の内容が、同ファイル内のすべての RoleFunc から参照可能になります。



### 4.4 再生成時の保持



ファイルレベルマーカー内の内容は、再生成時に自動保護されます。



&#x20;   初回生成 → 空のマーカー

&#x20;     ↓

&#x20;   ユーザーが #include 追加

&#x20;     ↓

&#x20;   設計変更 → 再生成

&#x20;     ↓

&#x20;   マーカー内の #include が保持される ✅



### 4.5 検証方法



StaTable には、この動作を機械検証する公式テストがあります。



&#x20;   cd code

&#x20;   python tools\\test_user_code_roundtrip.py



このコマンドは:



1\. XML から C コードを生成

2\. ファイルレベルマーカーに #include "user_roundtrip_test.h" を注入

3\. 再生成（マージ）を実行

4\. include が保持されているか確認

5\. gcc コンパイル + ARM リンク



を自動実行します。Exit code 0 で全て PASS。



---



## 5. ファイル末尾: ヘルパー関数



### 5.1 TAIL マーカー



生成ファイルの末尾に、ユーザー専用の領域があります。



&#x20;   /* [[STABLE_USER_CODE_TAIL_START]] */

&#x20;   /* Write user-added code here (helper functions, etc.) */

&#x20;   /* [[STABLE_USER_CODE_TAIL_END]] */



### 5.2 用途



- static ヘルパー関数

- ファイルスコープの定数テーブル

- マクロ定義



&#x20;   /* [[STABLE_USER_CODE_TAIL_START]] */



&#x20;   /* 内部用: 硬貨種別を判定 */

&#x20;   static uint8_t classify_coin(uint32_t value)

&#x20;   {

&#x20;       if (value == 10)  return 1;

&#x20;       if (value == 50)  return 2;

&#x20;       if (value == 100) return 3;

&#x20;       return 0;

&#x20;   }



&#x20;   /* [[STABLE_USER_CODE_TAIL_END]] */



### 5.3 注意点



- TAIL はファイル末尾にあるため、その前の関数からは参照できません

&#x20; （宣言を先に書けば可能だが、複雑になる）

- ロール関数から使いたいヘルパーは、プロトタイプ宣言をファイルレベルマーカーに、

&#x20; 本体を TAIL に置くのが定石



&#x20;   /* [[STABLE_USER_CODE_START]] */

&#x20;   #include "my_hardware.h"

&#x20;   /* プロトタイプ宣言 */

&#x20;   static uint8_t classify_coin(uint32_t value);

&#x20;   /* [[STABLE_USER_CODE_END]] */



&#x20;   /* ... ロール関数群 ... */



&#x20;   /* [[STABLE_USER_CODE_TAIL_START]] */

&#x20;   static uint8_t classify_coin(uint32_t value) { /* ... */ }

&#x20;   /* [[STABLE_USER_CODE_TAIL_END]] */



---



## 6. コンパイル・リンク検証



### 6.1 構文検証



&#x20;   cd code

&#x20;   python tools\\verify_c_syntax.py --root output --compiler gcc --std c99 --strict



### 6.2 ARM リンク検証



&#x20;   python tools\\verify_arm_link.py --root output



Cortex-M 用リンカスクリプトで実リンクまで検証。未解決シンボルを検出。



### 6.3 統合テスト



&#x20;   python tools\\test_user_code_roundtrip.py



以下を一括実行:



1\. 生成

2\. ユーザーコード注入

3\. 再生成（マージ）

4\. 保持確認

5\. gcc コンパイル

6\. ARM リンク



---



## 7. トラブルシューティング



### Q1. ユーザーコードが再生成で消えた



チェック:



1\. マーカーのスペルミス（STABLE_USER_CODE_START 等）

2\. マーカーの入れ子（START 内に START を書いていないか）

3\. code_merger.py のログで Replaced file user code が出ているか



### Q2. ローカル変数宣言で警告が出る



症状: -Wdeclaration-after-statement 警告



原因: C89 モードでビルドしている



対処: ネストブロック { ... } で囲む、または -std=c99 以上を指定



### Q3. ファイルレベルマーカーに追加した include が見つからない



症状: fatal error: my_hardware.h: No such file or directory



原因: インクルードパスが通っていない



対処: -I オプション追加、または CMakeLists / Makefile でパス指定



### Q4. 関数レベルマーカーが複数ある



症状: 同じ name のマーカーが複数箇所に



対処: name は一意である必要あり。同じロール関数が複数セルから

呼ばれる場合、生成側で 1 つに統合される（はず）。



### Q5. TAIL マーカー内の関数がロール関数から見えない



原因: C の宣言順序（TAIL はファイル末尾）



対処: プロトタイプ宣言をファイルレベルマーカーに置く（5.3 参照）



---



## 8. FAQ



### Q. ユーザーコードに MISRA 違反があっても生成側で検出されますか？



A. StaTable の MISRA チェックは生成コードを対象としています。

ユーザーコードも同じファイル内なので、cppcheck の走査範囲に含まれますが、

MISRA 適合はユーザー責任です。



### Q. マーカー自体を削除してしまったら？



A. 次回生成時にマーカーが復活し、内容は失われます。

マーカーは削除せず、内部のコードのみ編集してください。



### Q. 手動でファイル全体を書き換えたい



A. 非推奨です。次回生成で大部分が上書きされます。

どうしても必要な場合は、生成先ディレクトリを Git 管理外に置き、

手動マージしてください。



### Q. マーカー間で別のマーカーを使いたい（ネスト）



A. 未サポートです。フラットな構造を保ってください。



### Q. (void) 行を全部削除してもいい？



A. 未使用変数に対する警告が出ます。使う変数の (void) のみ削除してください。



---



## 変更履歴



| バージョン | 日付 | 内容 |

|---|---|---|

| v3.3.0 | 2026-10-04 | ファイルレベルマーカーの説明を追加 |

| v1.0 | 2026-10-04 | 初版作成 |



---



*このガイドは StaTable v3.3.0 のリリースに合わせて作成されました。*



