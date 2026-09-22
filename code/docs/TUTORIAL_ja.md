# StaTable チュートリアル — 完全版

```markdown
# StaTable チュートリアル — 部品を定義してプログラムを組み立てる

Version: 1.0
Date: 2026-09-22
対象: StaTable を初めて使う設計者
前提: StaTable v2.4.1 以降

---

## 目次

### 序章
1. このツールの考え方
2. 題材: 自動販売機の制御プログラム

### 本編 — 骨組みを作る
3. 手順1: プロジェクトを作る
4. 手順2: 骨組みを作る（状態 + イベント）

### 本編 — マトリクスを埋める
5. 手順3: 遷移を組む（Driver 層から）
6. 手順4: セルを仕上げる（Role 関数の初回登録）
7. 手順5: 状態を仕上げる
8. 手順6: 他の層も同様に完成させる

### 本編 — 完成させる
9. 手順7: 図で確認する
10. 手順8: C コードを生成する
11. 手順9: 組み込みに統合する
12. 手順10: プロジェクトを保存する

### 応用編
13. 既存プロジェクトを流用する
14. 反復開発

### まとめ
15. 作業 × 機能 対応表
16. よくある質問（FAQ）
17. 次のステップ

### 付録
A. マーカーリファレンス
B. 用語対応表
C. 用語集
D. 変更履歴

---

# 序章

---

## 1. このツールの考え方

### 1.1 StaTable は何をするツールか

StaTable は、**プログラムの部品を定義し、それを状態遷移マトリクスに
組み込んで、動くプログラムを組み立てるツール**です。

- **部品** = Role 関数（システムができること）
- **組み立て** = 状態遷移（いつ、どの部品を使うか）
- **完成品** = 状態機械（C コードとして出力）

特に、以下のようなプログラムに適しています:

| 適したプログラム | 例 |
|----------------|-----|
| 状態遷移が明確なもの | 自動販売機、洗濯機、エレベーター |
| イベント駆動のもの | 割り込み処理、通信プロトコル |
| 組み込みシステム | MCU ファームウェア全般 |
| MISRA C:2012 準拠が必要なもの | 車載、医療、産業機器 |

### 1.2 「部品」と「組み立て」の比喩

電子回路基板の製作に似ています。

```
┌───────────────────────────────────────────────┐
│  StaTable = ブレッドボード                     │
│                                               │
│  ┌─────────────┐    ┌─────────────┐          │
│  │ 部品箱      │    │ 配線盤      │          │
│  │ (Role 関数) │    │ (状態遷移   │          │
│  │             │    │  マトリクス) │          │
│  │ ・コイン判定 │    │             │          │
│  │ ・商品排出   │    │ 待機│選択│支払│        │
│  │ ・釣銭計算   │    │ ────┼────┼────┤        │
│  │ ・エラー表示 │    │選択 │ ○  │    │        │
│  │ ・モータ駆動 │    │投入 │    │ ○  │        │
│  └─────────────┘    └─────────────┘          │
└───────────────────────────────────────────────┘
```

1. まず **部品箱に部品を揃える**（機能を定義する）
2. 次に **配線盤に部品を配置する**（遷移マトリクスを埋める）
3. 回路図（状態機械）が組み上がる

### 1.3 全体の作業手順（骨組み → 埋める）

**StaTable の特性を活かした、推奨の作業手順**は次のとおりです。

```
手順1: プロジェクトを作る
       ↓
手順2: 骨組みを作る（状態 + イベント）
       → 遷移マトリクスの枠が自動的に現れる
       ↓
手順3: 遷移を埋める（セルごとに）
       → 必要になったら Role 関数をその場で追加
       ↓
手順4: セルを仕上げる（アクション・関係）
       ↓
手順5: 状態を仕上げる（entry / exit）
       ↓
手順6: 完成させる（確認 → C コード生成 → 統合）
```

#### なぜ「骨組み → 埋める」なのか

| # | 理由 |
|---|------|
| 1 | 状態とイベントを登録すると、**マトリクスの枠が自動生成**される |
| 2 | **設計図を常に見ながら**作業できる（発見的設計に強い） |
| 3 | **必要になった時点で Role 関数を追加**できる（不要な部品を作らない） |
| 4 | 机上検討が不完全でも始められる |

### 1.4 用語の整理（Role 関数 = 部品）

本チュートリアルでは、StaTable の用語を以下のように扱います。

| StaTable 用語 | 本チュートリアルでの呼称 | 意味 |
|--------------|----------------------|------|
| **Role 関数** | **部品（機能）** | システムができること |
| **State** | **状態** | 動作モード |
| **Event** | **きっかけ** | 状態を変える信号 |
| **Transition** | **遷移** | 「A 状態で X イベントが来たら B 状態へ」 |
| **Layer** | **層** | 役割ごとの分類（Driver / Middleware / Application） |
| **Namespace** | **Namespace** | 部品が属する層を明示 |

#### Role 関数 = 部品 の例（自動販売機）

| 抽象度 | 表現 | 例 |
|-------|------|-----|
| 高 | 機能 | 「コインを判定する」 |
| 中 | 動作 | `ValidateCoin()` |
| 低 | C 関数 | `int RoleFunc_Middleware_ValidateCoin(...)` |

チュートリアルでは **「機能」レベルから入り、徐々に具体化** します。

#### 用語の関係図

```
       Layer（層）
          │
          │ に属する
          ▼
    Role 関数（部品）
          │
          │ を使う
          ▼
    Transition（遷移）  ←  State × Event
          │
          │ が集まって
          ▼
    State Machine（状態機械）
```

---

## 2. 題材: 自動販売機の制御プログラム

### 2.1 何を作るか（製品概要）

**自動販売機の制御プログラム** を作ります。

#### 製品の基本動作

1. 顧客が商品を選ぶ
2. コインを投入する
3. 金額が足りれば商品を排出
4. 釣銭があれば返却
5. 完了後、待機状態に戻る

#### エラー処理

- 商品詰まり
- 釣銭切れ
- 電源断
- 不正コイン

#### なぜ自動販売機を題材にするのか

| # | 理由 |
|---|------|
| 1 | **状態遷移が具体的** — 待機 → 選択 → 支払 → 排出 → 完了 |
| 2 | **イベントが多彩** — ボタン、コイン、タイムアウト、エラー |
| 3 | **機能が「部品」として明確** — コイン判定、商品排出、釣銭計算 |
| 4 | **机上スケッチが描きやすい** — 誰でも動作を想像できる |
| 5 | **エラー処理が自然** — 詰まり、釣銭切れ、電源断 |

### 2.2 3層構成の全体像

自動販売機は、**3つの層**で構成します。各層は**自己完結**しており、
層をまたぐ Role 関数の共有は行いません。

```
┌─────────────────────────────────────────────────────┐
│  Application 層（販売ロジック）                       │
│    顧客とのやり取り、販売フロー全体の制御              │
│                                                       │
│    状態: Idle / ProductSelected / AwaitingPayment /  │
│          Dispensing / ReturningChange / Error         │
│    機能: SelectProduct, ConfirmPurchase, ...         │
├─────────────────────────────────────────────────────┤
│  Middleware 層（デバイス処理）                        │
│    コイン判定、商品排出、釣銭計算                     │
│                                                       │
│    状態: MwIdle / CoinAccepting / Dispensing / ...   │
│    機能: ValidateCoin, DispenseProduct, ...          │
├─────────────────────────────────────────────────────┤
│  Driver 層（ハードウェア制御）                        │
│    モータ、センサ、LCD、キーパッド                    │
│                                                       │
│    状態: HwIdle / HwActive / HwError                 │
│    機能: MotorStart, MotorStop, LcdWrite, ...        │
└─────────────────────────────────────────────────────┘
```

#### 各層の責務

| 層 | 責務 | 主な機能 |
|---|------|---------|
| **Application** | 販売フローの制御 | 商品選択受付、購入確定、釣銭処理指示 |
| **Middleware** | デバイスの抽象化 | コイン判定、商品排出制御、釣銭計算 |
| **Driver** | ハードウェア制御 | モータ駆動、センサ読取、LCD 書込、キー読取 |

#### 層の独立性（重要）

各層の Role 関数は、**その層の中だけで使われます**。

```
✅ 良い設計（層の独立性）
   Application 層: Application 内の Role 関数のみ使用
   Middleware 層:  Middleware 内の Role 関数のみ使用
   Driver 層:      Driver 内の Role 関数のみ使用

❌ 避けるべき設計（層間の依存）
   Application 層: Driver 層の Role 関数を直接呼ぶ
```

**なぜ層の独立性が重要か**:

| # | 理由 |
|---|------|
| 1 | **各層を独立してテストできる** |
| 2 | **他製品への流用が容易** |
| 3 | **保守範囲が明確** |
| 4 | **MISRA C:2012 の複雑度を抑えられる** |

### 2.3 どんな状態があるか

各層の状態を机上で検討します。

#### Application 層の状態

| # | 状態 | 説明 |
|---|------|------|
| 1 | `Idle` | 待機中（顧客待ち） |
| 2 | `ProductSelected` | 商品選択済み |
| 3 | `AwaitingPayment` | 入金待ち |
| 4 | `Dispensing` | 商品排出中 |
| 5 | `ReturningChange` | 釣銭返却中 |
| 6 | `Error` | エラー状態 |

#### Middleware 層の状態

| # | 状態 | 説明 |
|---|------|------|
| 1 | `MwIdle` | 待機中 |
| 2 | `CoinAccepting` | コイン受付中 |
| 3 | `Dispensing` | 商品排出制御中 |
| 4 | `ChangeCalculating` | 釣銭計算中 |

#### Driver 層の状態

| # | 状態 | 説明 |
|---|------|------|
| 1 | `HwIdle` | ハードウェア待機中 |
| 2 | `HwActive` | ハードウェア動作中 |
| 3 | `HwError` | ハードウェアエラー |

### 2.4 何が状態を変えるか（イベント）

各層のイベントを机上で検討します。

#### Application 層のイベント

| # | イベント | 説明 |
|---|---------|------|
| 1 | `SELECT` | 商品選択ボタン押下 |
| 2 | `COIN_IN` | コイン投入検知 |
| 3 | `CONFIRM` | 購入確定 |
| 4 | `DISPENSE_DONE` | 商品排出完了 |
| 5 | `CHANGE_DONE` | 釣銭返却完了 |
| 6 | `CANCEL` | キャンセル |
| 7 | `ERROR` | エラー発生 |
| 8 | `RESET` | エラーリセット |

#### Middleware 層のイベント

| # | イベント | 説明 |
|---|---------|------|
| 1 | `MW_START_COIN` | コイン受付開始指示 |
| 2 | `MW_COIN_VALID` | 有効コイン検知 |
| 3 | `MW_COIN_INVALID` | 不正コイン検知 |
| 4 | `MW_START_DISPENSE` | 商品排出開始指示 |
| 5 | `MW_DISPENSE_DONE` | 商品排出完了 |
| 6 | `MW_START_CHANGE` | 釣銭返却開始指示 |
| 7 | `MW_CHANGE_DONE` | 釣銭返却完了 |

#### Driver 層のイベント

| # | イベント | 説明 |
|---|---------|------|
| 1 | `HW_ENABLE` | ハードウェア有効化 |
| 2 | `HW_DISABLE` | ハードウェア無効化 |
| 3 | `HW_MOTOR_START` | モータ起動 |
| 4 | `HW_MOTOR_STOP` | モータ停止 |
| 5 | `HW_ERROR` | ハードウェアエラー検知 |

### 2.5 どんな機能（部品）が必要か

各層で必要な機能を机上で列挙します。

#### Application 層の機能

| # | 機能 | 説明 |
|---|------|------|
| 1 | `ShowProductList` | 商品一覧を表示 |
| 2 | `HighlightProduct` | 選択商品を強調表示 |
| 3 | `CalculateTotal` | 合計金額を計算 |
| 4 | `CheckSufficientFunds` | 金額が足りるか判定 |
| 5 | `RequestDispense` | 商品排出を要求 |
| 6 | `RequestChange` | 釣銭返却を要求 |
| 7 | `ShowError` | エラー表示 |
| 8 | `ResetSystem` | システムリセット |

#### Middleware 層の機能

| # | 機能 | 説明 |
|---|------|------|
| 1 | `ValidateCoin` | コインを判定 |
| 2 | `AccumulateCoin` | 投入金額を累積 |
| 3 | `DispenseProduct` | 商品排出制御 |
| 4 | `StopDispense` | 商品排出停止 |
| 5 | `CalculateChange` | 釣銭を計算 |
| 6 | `DispenseChange` | 釣銭を返却 |

#### Driver 層の機能

| # | 機能 | 説明 |
|---|------|------|
| 1 | `InitHardware` | ハードウェア初期化 |
| 2 | `ReadCoinSensor` | コインセンサ読取 |
| 3 | `DriveMotor` | モータ駆動 |
| 4 | `StopMotor` | モータ停止 |
| 5 | `WriteLcd` | LCD に書込 |
| 6 | `ReadKeypad` | キーパッド読取 |

### 2.6 完成イメージ（机上スケッチ）

#### Application 層の状態遷移図

```
                         [SELECT]
                             ↓
    ┌──────────┐         ┌──────────────┐
    │   Idle   │ ──────→ │ProductSelected│
    └──────────┘         └──────────────┘
         ↑                     │
         │ [RESET]             │ [COIN_IN]
         │                     ↓
    ┌──────────┐         ┌──────────────┐
    │  Error   │ ←─────  │AwaitingPayment│
    └──────────┘ [ERROR] └──────────────┘
         ↑                     │
         │                     │ [CONFIRM]
         │                     ↓
         │               ┌──────────────┐
         │               │  Dispensing  │
         │               └──────────────┘
         │                     │
         │                     │ [DISPENSE_DONE]
         │                     ↓
         │               ┌──────────────┐
         │               │ReturningChange│
         │               └──────────────┘
         │                     │
         │                     │ [CHANGE_DONE]
         │                     ↓
         └───────────────── Idle に戻る
```

#### 3層の関係（実行順序）

```
1. Driver 層が最優先（ハードウェア制御）
       ↓
2. Middleware 層（デバイス処理）
       ↓
3. Application 層（販売ロジック）
```

この順序は **Layer Settings** で設定します（手順7 で説明）。

---

# 本編 — 骨組みを作る

---

## 3. 手順1: プロジェクトを作る

### 3.1 StaTable を起動する

#### 操作

ターミナル（またはコマンドプロンプト）で以下を実行します:

```bash
cd StaTable/code
python -m statable
```

#### 結果

**サンプルプロジェクト**（Application タブ）が表示されます。

- 4つの状態（Idle / Active / Error / Halt）
- 5つのイベント（START / STOP / ERROR / TIMER0_OVERFLOW / 完了）
- 6つの遷移
- 9つの Role 関数

これらは**チュートリアルでは使いません**ので、次の手順で消します。

### 3.2 新規プロジェクトを開始する

#### 操作

1. メニュー **File → New Project...** を選択（または **Ctrl+N**）
2. **未保存確認ダイアログ**が表示されます:

   ```
   ┌─────────────────────────────────────────────────┐
   │  ⚠  Unsaved Changes                             │
   │                                                 │
   │  The current project has unsaved changes.       │
   │  Do you want to save them before continuing?    │
   │                                                 │
   │       [ Save ]  [ Discard ]  [ Cancel ]         │
   └─────────────────────────────────────────────────┘
   ```

   | ボタン | 動作 |
   |-------|------|
   | **Save** | 現在のプロジェクトを保存してから実行 |
   | **Discard** | 保存せずに実行（サンプルが不要な場合はこちら） |
   | **Cancel** | 中止して元の画面に戻る |

   > **注意**: 起動直後はサンプルプロジェクトが読み込まれた状態のため、
   > `windowModified` が `True` になっています。サンプルが不要な場合は
   > **Discard** を選択してください。

3. **Discard** を選択

#### 結果

| 項目 | 変化 |
|------|------|
| タブ | `Application` タブ 1個のみ（空） |
| 状態 / イベント / 遷移 | すべて空（0件） |
| 共有ライブラリ | 空 |
| グローバル定義 | 空 |
| コード生成設定 | デフォルト |
| ウィンドウタイトル | `Untitled[*] - StaTable` |
| ステータスバー | `New project created` を 3 秒表示 |

**まっさらな状態になりました。**

### 3.3 3つのタブ（層）を準備する

#### 3.3.1 タブ名 = 層名 という仕組み

**StaTable では、タブ名がそのまま「層名」になります。**

| タブ名 | 自動設定される `layer_name` |
|-------|--------------------------|
| `Application` | `"Application"` |
| `Driver` | `"Driver"` |
| `Middleware` | `"Middleware"` |

#### なぜ重要か

| # | 理由 |
|---|------|
| 1 | **Role 関数の Namespace 候補になる** — Role function ダイアログのコンボボックスに全タブ名が表示される |
| 2 | **生成 C コードのファイル名に使われる** — `statable_transitions_Driver.c` など |
| 3 | **層の優先度設定の対象になる** — Layer Settings で層ごとに実行順を設定 |

#### 命名の推奨

- 短く、意味が明確な名前
- 例: `Application`, `Driver`, `Middleware`
- 例: `App`, `Drv`, `Mw`（略称も可、ただし統一する）

#### 3.3.2 現在のタブを確認

既に `Application` タブが作られています（新規プロジェクトで自動生成）。
これは **`layer_name = "Application"`** に自動設定されています。

#### 3.3.3 Driver タブを追加

**操作**:

1. メニュー **File → New State Machine**（またはツールバーの **New tab** ボタン）
2. タブ名を入力: `Driver`
3. OK をクリック
4. 新しいタブ **Driver** が追加される

**自動設定される項目**:
- `layer_name`: `Driver`（タブ名から自動設定）
- `layer_priority`: `5`（デフォルト。後で変更します）

#### 3.3.4 Middleware タブを追加

同様に:

1. メニュー **File → New State Machine**
2. タブ名: `Middleware`
3. OK

#### 結果

```
┌──────────┬──────────┬────────────────┐
│ Driver   │Middleware│ Application    │
└──────────┴──────────┴────────────────┘
```

3つのタブが並びました。

### 3.4 何が空になるか確認する

各タブを切り替えて、**すべて空**であることを確認します。

#### 確認項目

| 項目 | 期待値 |
|------|--------|
| State list タブ | 0件 |
| Role function タブ | 0件 |
| 遷移マトリクス | 空（列 = 0、行 = 0） |
| Mermaid 図 | `[*]` のみ（初期状態なし） |

#### マトリクスの見え方（例: Application タブ）

```
（列なし、行なし）
```

状態とイベントが登録されていないため、**マトリクスは空**です。

**これで手順1が完了です。次は骨組みを作ります。**

---

## 4. 手順2: 骨組みを作る（状態 + イベント）

### 4.1 なぜ状態とイベントから始めるのか

StaTable の**遷移マトリクスは自動生成**されます:

```
遷移マトリクス
├── 列 = State list の状態
└── 行 = Event definitions のイベント
```

つまり、**状態とイベントを登録するだけで、マトリクスの枠が現れます**。

#### 骨組みを先に作る利点

| # | 利点 |
|---|------|
| 1 | **全体像が見える** — どのセルに遷移があるべきか、目で確認できる |
| 2 | **設計の見通しが立つ** — 状態数 × イベント数の規模が分かる |
| 3 | **Role 関数は後回しにできる** — 必要になった時点で追加 |
| 4 | **セルを眺めながら設計できる** — 発見的設計に強い |

#### 作業順序

各層（Driver / Middleware / Application）ごとに、以下を繰り返します:

```
1. 状態を登録する     → マトリクスの「列」ができる
2. イベントを登録する → マトリクスの「行」ができる
3. マトリクスを眺める → 全体像を確認
```

### 4.2 なぜ Driver 層から作るのか

3つの層を作る順序には、**自動販売機の動作そのもの**に基づく理由があります。

#### 自動販売機の動作を分解すると

「商品を排出する」という1つの動作も、層ごとに分解できます。

```
【Application 層】
  顧客が「購入確定」を押した
       ↓ 「商品を出して」
【Middleware 層】
  在庫を1つ減らして、商品排出機構に指示
       ↓ 「モータを回して」
【Driver 層】
  モータを指定角度だけ回転させ、センサで完了を検知
```

**上位層の動作は、下位層の動作の組み合わせでできています。**

#### 具体例：「商品を排出する」

| 層 | やること | Role 関数の例 |
|---|---------|--------------|
| Application | 購入確定を受けて、排出を要求 | `RequestDispense` |
| Middleware | 在庫確認 → 排出制御 → 完了通知 | `DispenseProduct` |
| Driver | モータ回転 → センサ読取 → 停止 | `DriveMotor`, `ReadSensor` |

**下位層（Driver）の機能が決まらないと、上位層（Middleware / Application）の
機能は作れません。**

#### Driver 層は「機械が何をできるか」の定義

Driver 層は、**この機械が物理的に何をできるか**を定義する層です。

| 層 | 定義するもの | 自動販売機での例 |
|---|-------------|----------------|
| **Driver** | 機械の物理能力 | モータを回す、センサを読む、LCD に書く |
| **Middleware** | デバイス操作 | コインを判定、商品を排出、釣銭を計算 |
| **Application** | 業務ロジック | 商品選択、購入確定、釣銭返却 |

**比喩**:

```
Driver 層     = 「この機械は、モータが回せる、センサが読める」
                （＝機械の能力のカタログ）
       ↓ 組み合わせ
Middleware 層 = 「だから、コインを判定できる、商品を出せる」
       ↓ 組み合わせ
Application 層= 「だから、商品を販売できる」
```

**つまり**:
- Driver 層は**ハードウェア仕様書**に近い（物理に密着）
- Middleware 層は**デバイス操作マニュアル**（機能の組み合わせ）
- Application 層は**業務フロー**（製品としての振る舞い）

**Driver 層から作る = 機械の能力を最初に確定させる** ことになります。
これが決まれば、上位層は「この能力をどう組み合わせるか」に集中できます。

#### 逆に、Application 層から作ると…

```
【Application 層】「購入確定で商品を出したい」
       ↓ でも…
【Middleware 層】「商品を出すって、具体的に何をするの？」
       ↓ でも…
【Driver 層】「モータをどう回すか、まだ決めてない」
       ↑ ここが未確定
```

**「商品を出す」の実装方法が未確定のまま、上位層の設計を進めることになり、
後で大幅な手戻りが発生します。**

#### 自動販売機での設計順序と根拠

| 順序 | 層 | 何を決めるか | 決まると… |
|------|-----|-------------|----------|
| 1 | **Driver** | モータ・センサ・LCD の制御方法 | Middleware が「モータを回す」を呼べる |
| 2 | **Middleware** | コイン判定・商品排出・釣銭計算 | Application が「商品を出して」を呼べる |
| 3 | **Application** | 顧客とのやり取り・販売フロー | プログラム全体が完成する |

#### 各段階で「動くもの」ができる

Driver 層から作ると、**各段階で動作確認**できます。

| 段階 | 確認できること |
|------|--------------|
| Driver 完了時 | モータが回る、LCD に文字が出る、キーが読める |
| Middleware 完了時 | コインを入れると判定される、商品が1つ出る |
| Application 完了時 | 実際の販売フローが動く |

**Application 層から作ると、最後まで「動くもの」ができません。**

#### チーム開発での利点

自動販売機開発を複数人で進める場合：

| 担当 | 期間 | 内容 |
|------|------|------|
| Driver 担当 | 前半 | ハードウェア制御を完成させる |
| Middleware 担当 | 中盤 | Driver の完成を待って着手 |
| Application 担当 | 後半 | Middleware の完成を待って着手 |

**Driver 担当が先に動き出せば、他は待ち時間なく並行作業できます。**

#### 層の独立性との関係

この設計順序は、序章で述べた「層の独立性」とも整合します。

- Driver 層は、Application 層の存在を知らない
- Middleware 層は、Application 層の存在を知らない
- Application 層は、Driver / Middleware 層の詳細を知らない

**「下位から作る」= 「依存されない側から作る」** ことで、
自然と層の独立性が保たれます。

### 4.3 Driver 層の状態とイベントを登録

まず最下層（Driver）から作ります。

#### 4.3.1 Driver タブを開く

**操作**: タブバーの **Driver** をクリック

#### 4.3.2 Driver 層の状態を登録

**使う機能**: SettingsPanel → **State list** タブ → **Add** ボタン

**登録する状態（3個）**:

| # | Name | Description | entry function | exit function | Type |
|---|------|-------------|---------------|---------------|------|
| 1 | `HwIdle` | ハードウェア待機中 | （空） | （空） | `normal` |
| 2 | `HwActive` | ハードウェア動作中 | （空） | （空） | `normal` |
| 3 | `HwError` | ハードウェアエラー | （空） | （空） | `normal` |

**手順**:

1. **Add** ボタンをクリック
2. 行が追加される
3. **Name** 列をクリックして `HwIdle` と入力
4. **Description** 列に `ハードウェア待機中` と入力
5. **Type** 列は `normal` のまま（デフォルト）
6. 同様に `HwActive`, `HwError` を追加

> **ポイント**: entry / exit は**この段階では空**にしておきます。
> 後の手順5で、必要になった時点で Role 関数を追加します。

#### 4.3.3 Driver 層のイベントを登録

**使う機能**: SettingsPanel → **Role function** タブ内の
**Event definitions...** ボタン

**登録するイベント（5個）**:

| # | Event name | Delivery type | Description |
|---|-----------|--------------|-------------|
| 1 | `HW_ENABLE` | `DIRECT` | ハードウェア有効化 |
| 2 | `HW_DISABLE` | `DIRECT` | ハードウェア無効化 |
| 3 | `HW_MOTOR_START` | `DIRECT` | モータ起動 |
| 4 | `HW_MOTOR_STOP` | `DIRECT` | モータ停止 |
| 5 | `HW_ERROR` | `QUEUE` | ハードウェアエラー検知 |

**手順**:

1. **Event definitions...** ボタンをクリック
2. EventDefinitionDialog が開く
3. **Add** で上記5個を追加
4. OK をクリック

> **Delivery type の選び方**:
> - `DIRECT`: 割り込みから直接処理（応答性重視）
> - `QUEUE`: キュー経由（優先度制御可能）
> - `DOUBLE`: 両方
>
> Driver 層は応答性重視のため `DIRECT` を基本、エラー通知は `QUEUE` に。

#### 4.3.4 Driver 層のマトリクスを確認

**操作**: SettingsPanel を閉じる（またはマトリクスをクリック）

**結果**:

```
          │ HwIdle │ HwActive │ HwError
──────────┼────────┼──────────┼─────────
HW_ENABLE │        │          │
HW_DISABLE│        │          │
HW_MOTOR_ │        │          │
  START   │        │          │
HW_MOTOR_ │        │          │
  STOP    │        │          │
HW_ERROR  │        │          │
```

**空のマトリクス（3列 × 5行）** が現れました。これが骨組みです。

### 4.4 Middleware 層の状態とイベントを登録

Middleware 層も Driver 層と同じ手順で登録します。
詳細な操作手順は **4.3 を参照** してください。

#### 登録する状態（4個）

| # | Name | Description | Type |
|---|------|-------------|------|
| 1 | `MwIdle` | 待機中 | `normal` |
| 2 | `CoinAccepting` | コイン受付中 | `normal` |
| 3 | `Dispensing` | 商品排出制御中 | `normal` |
| 4 | `ChangeCalculating` | 釣銭計算中 | `normal` |

#### 登録するイベント（7個）

| # | Event name | Delivery type | Description |
|---|-----------|--------------|-------------|
| 1 | `MW_START_COIN` | `DIRECT` | コイン受付開始指示 |
| 2 | `MW_COIN_VALID` | `DIRECT` | 有効コイン検知 |
| 3 | `MW_COIN_INVALID` | `DIRECT` | 不正コイン検知 |
| 4 | `MW_START_DISPENSE` | `DIRECT` | 商品排出開始指示 |
| 5 | `MW_DISPENSE_DONE` | `DIRECT` | 商品排出完了 |
| 6 | `MW_START_CHANGE` | `DIRECT` | 釣銭返却開始指示 |
| 7 | `MW_CHANGE_DONE` | `DIRECT` | 釣銭返却完了 |

#### マトリクスを確認

登録後、**4列 × 7行** の空マトリクスが現れます。

### 4.5 Application 層の状態とイベントを登録

Application 層も同様に登録します。
詳細な操作手順は **4.3 を参照** してください。

#### 登録する状態（6個）

| # | Name | Description | Type |
|---|------|-------------|------|
| 1 | `Idle` | 待機中（顧客待ち） | `normal` |
| 2 | `ProductSelected` | 商品選択済み | `normal` |
| 3 | `AwaitingPayment` | 入金待ち | `normal` |
| 4 | `Dispensing` | 商品排出中 | `normal` |
| 5 | `ReturningChange` | 釣銭返却中 | `normal` |
| 6 | `Error` | エラー状態 | `normal` |

#### 登録するイベント（8個）

| # | Event name | Delivery type | Description |
|---|-----------|--------------|-------------|
| 1 | `SELECT` | `DIRECT` | 商品選択ボタン押下 |
| 2 | `COIN_IN` | `DIRECT` | コイン投入検知 |
| 3 | `CONFIRM` | `DIRECT` | 購入確定 |
| 4 | `DISPENSE_DONE` | `DIRECT` | 商品排出完了 |
| 5 | `CHANGE_DONE` | `DIRECT` | 釣銭返却完了 |
| 6 | `CANCEL` | `DIRECT` | キャンセル |
| 7 | `ERROR` | `QUEUE` | エラー発生 |
| 8 | `RESET` | `DIRECT` | エラーリセット |

#### マトリクスを確認

登録後、**6列 × 8行** の空マトリクスが現れます。

### 4.6 各層のマトリクスを確認

3つのタブを切り替えて、**骨組みが揃っているか**確認します。

#### 確認表

| 層 | 状態数 | イベント数 | マトリクス |
|---|-------|-----------|-----------|
| Driver | 3 | 5 | 3 × 5 |
| Middleware | 4 | 7 | 4 × 7 |
| Application | 6 | 8 | 6 × 8 |
| **合計** | **13** | **20** | – |

#### 骨組み完成のチェック

- [ ] Driver タブ: 3状態 + 5イベントが登録されている
- [ ] Middleware タブ: 4状態 + 7イベントが登録されている
- [ ] Application タブ: 6状態 + 8イベントが登録されている
- [ ] 各タブでマトリクスの枠が見える
- [ ] Mermaid 図は各タブで「状態のみ」表示されている

#### 現時点でまだやっていないこと

| 項目 | やる場所 |
|------|---------|
| 遷移の追加 | 手順3（第5章） |
| セルアクション | 手順4（第6章） |
| entry / exit | 手順5（第7章） |
| Role 関数の登録 | 手順4以降（必要になった時点で） |
| 層の優先度設定 | 手順7（第9章） |

**骨組みが完成しました。次はマトリクスを埋めていきます。**

---

# 本編 — マトリクスを埋める

---

## 5. 手順3: 遷移を組む（Driver 層から）

### 5.1 マトリクスの見方

**MatrixTableWidget** を確認します:

```
          │ HwIdle │ HwActive │ HwError
──────────┼────────┼──────────┼─────────
HW_ENABLE │        │          │
HW_DISABLE│        │          │
HW_MOTOR_ │        │          │
  START   │        │          │
HW_MOTOR_ │        │          │
  STOP    │        │          │
HW_ERROR  │        │          │
```

- **列** = 状態（State list から自動生成）
- **行** = イベント（Event definitions から自動生成）
- **セル** = その (状態, イベント) で何が起きるか（＝遷移）

### 5.2 セルに遷移を追加する

#### Driver 層に追加する遷移

| # | 状態 | イベント | 遷移先 | 条件 | モード |
|---|------|---------|--------|------|--------|
| 1 | HwIdle | HW_ENABLE | HwActive | （なし） | Commit |
| 2 | HwActive | HW_DISABLE | HwIdle | （なし） | Commit |
| 3 | HwActive | HW_ERROR | HwError | （なし） | Commit |
| 4 | HwError | HW_DISABLE | HwIdle | （なし） | Commit |

> **注意**: `HW_MOTOR_START` / `HW_MOTOR_STOP` は**状態を変えない**ため、
> 遷移としては追加しません。これらは「セルアクション」として扱います（手順4で説明）。

### 5.3 遷移のモード（Commit / Tentative）

遷移には2種類のモードがあります。

| モード | 意味 | 使う場面 |
|-------|------|---------|
| **Commit** | この遷移が成立したら、同セル内の後続遷移を評価しない | 通常の遷移（デフォルト） |
| **Tentative** | 後続遷移で上書き可能 | 例外的な遷移 |

**自動販売機では**:
- すべて **Commit** で OK
- 同じセルに複数の遷移がある場合のみ、慎重に検討（今回は該当なし）

### 5.4 遷移の条件式

遷移には**条件式**を設定できます。条件式が `true` の時のみ遷移します。

| 例 | 意味 |
|----|------|
| （空） | 無条件（必ず遷移） |
| `current_speed >= target_speed` | 速度が目標値以上 |
| `coin_total >= price` | 投入金額が価格以上 |
| `retry_count < 3` | リトライ回数が3未満 |

**Driver 層では**:
- 今回は条件式なし（無条件遷移のみ）
- 上位層（Application）で条件式を使います

### 5.5 遷移のラベル（T1, T2, ...）

同じセルに複数の遷移がある場合、**ラベル**で識別します。

| ラベル | 用途 |
|-------|------|
| `T1` | 1番目の遷移 |
| `T2` | 2番目の遷移 |

**Driver 層では**:
- 各セルに1つずつなので、ラベルは `T1` のみ

### 5.6 具体的な操作手順

#### セル (HwIdle, HW_ENABLE) の編集

1. **HwIdle** 列 × **HW_ENABLE** 行のセルをダブルクリック
2. **ActionEditorDialog** が開く（5タブ）
3. **Transitions** タブを選択
4. **Add** ボタンをクリック
5. 以下の値を入力:

   | フィールド | 値 |
   |-----------|-----|
   | Source | `HwIdle` |
   | Event | `HW_ENABLE` |
   | Target | `HwActive` |
   | Condition | （空） |
   | Mode | `Commit` |
   | Title | `HW 有効化` |
   | Label | `T1` |

6. OK をクリック
7. マトリクスのセルに `HW 有効化 (HW_ENABLE) [Commit] <T1>` が表示される

#### 残り3つの遷移も同様に追加

- (HwActive, HW_DISABLE) → HwIdle
- (HwActive, HW_ERROR) → HwError
- (HwError, HW_DISABLE) → HwIdle

### 5.7 Driver 層のマトリクス完成を確認

```
          │ HwIdle              │ HwActive             │ HwError
──────────┼─────────────────────┼──────────────────────┼─────────────────────
HW_ENABLE │ HW 有効化 (HW_ENABLE)│                     │
          │ [Commit] <T1>       │                     │
HW_DISABLE│                     │ HW 無効化 [Commit]   │ HW 復帰 [Commit]
          │                     │ <T1>                 │ <T1>
HW_MOTOR_ │                     │ （セルアクション）    │
  START   │                     │                      │
HW_MOTOR_ │                     │ （セルアクション）    │
  STOP    │                     │                      │
HW_ERROR  │                     │ HW エラー [Commit]   │
          │                     │ <T1>                 │
```

**Driver 層の遷移が完成しました。**

---

## 6. 手順4: セルを仕上げる（Role 関数の初回登録）

### 6.1 セルアクションとは

**セルアクション** = 遷移とは独立して実行される処理です。

| 種類 | 実行タイミング |
|------|--------------|
| `before_transitions` | そのセルの遷移評価の**前** |
| `after_transitions` | そのセルの遷移評価の**後** |

#### 遷移とセルアクションの違い

| 項目 | 遷移 | セルアクション |
|------|------|--------------|
| 目的 | 状態を変える | 付随的な処理 |
| 例 | HwIdle → HwActive | モータ回転、ログ出力 |
| 条件 | 条件式で制御可能 | 常に実行 |
| 効果 | 次状態を決定 | 副作用のみ |

### 6.2 セルアクションを追加する

#### Driver 層に追加するセルアクション

| # | セル | タイミング | 機能 |
|---|------|-----------|------|
| 1 | (HwActive, HW_MOTOR_START) | before | `DriveMotor` |
| 2 | (HwActive, HW_MOTOR_STOP) | before | `StopMotor` |
| 3 | (HwError, HW_ERROR) | after | `WriteLcd` |

### 6.3 Role 関数をその場で追加する

**ここが重要**: セルアクションを追加する際に、**Role 関数が未登録**なら、その場で追加します。

#### 操作手順

1. セル (HwActive, HW_MOTOR_START) をダブルクリック
2. **ActionEditorDialog** → **Pre / Post Actions** タブ
3. **Add (Pre)** ボタンをクリック
4. Role 関数選択ダイアログが開く
5. **`DriveMotor`** を探す → **見つからない**
6. **Cancel** で閉じる
7. **ActionEditorDialog** も一旦 Cancel
8. **SettingsPanel → Role function** タブ
9. **Add** ボタンで Role 関数を追加:

   | フィールド | 値 |
   |-----------|-----|
   | Function name | `DriveMotor` |
   | Namespace | `Driver` |
   | Display name | モータを駆動 |
   | Description | モータを指定角度だけ回転 |

10. OK
11. 再びセルをダブルクリック → Role 関数選択で `DriveMotor` を選択

> **ポイント**: 「必要になったら追加する」を実践します。
> 先に全部の Role 関数を作る必要はありません。

#### Driver 層で必要な Role 関数（5個）

| # | Function name | Namespace | Display name |
|---|--------------|-----------|--------------|
| 1 | `InitHardware` | `Driver` | ハードウェア初期化 |
| 2 | `DriveMotor` | `Driver` | モータ駆動 |
| 3 | `StopMotor` | `Driver` | モータ停止 |
| 4 | `WriteLcd` | `Driver` | LCD 書込 |
| 5 | `ReadKeypad` | `Driver` | キーパッド読取 |

#### Namespace の役割

Role 関数には **Namespace** を設定します。これは**部品が属する層**を明示します。

| 設定 | 効果 |
|------|------|
| Namespace = `Driver` | `Driver.DriveMotor` として扱われる |
| Namespace = （空） | `DriveMotor` として扱われる |

**Namespace コンボボックスには、全タブのレイヤ名が候補として表示されます。**
これにより、どの層に属するかを明示的に選択できます。

### 6.4 セル関係を追加する

**セル関係** = 1つのセルに複数の遷移がある場合の関係性。

| 種類 | 意味 |
|------|------|
| `sequential` | 順番に評価（デフォルト） |
| `exclusive` | 最大1つだけ発火 |
| `group` | グループ化、共有条件を外側に |

**Driver 層では**:
- 各セルに1つずつなので、**関係は不要**

**Application 層では**:
- 複数遷移があるセルで使用（後述）

---

## 7. 手順5: 状態を仕上げる

### 7.1 entry / exit アクションとは

状態には、**entry** と **exit** アクションを設定できます。

| アクション | タイミング |
|-----------|-----------|
| **entry** | その状態に**入った**時 |
| **exit** | その状態を**出る**時 |

#### 遷移との違い

| 項目 | 遷移 | entry / exit |
|------|------|-------------|
| 実行タイミング | 状態をまたぐ時 | 状態の入退出時 |
| 実行順序 | 遷移評価 → 実行 | exit → 遷移 → entry |

### 7.2 entry / exit を設定する

#### Driver 層の entry / exit

| # | 状態 | entry | exit |
|---|------|-------|------|
| 1 | HwIdle | `InitHardware` | （なし） |
| 2 | HwActive | （なし） | `StopMotor` |
| 3 | HwError | `WriteLcd` | （なし） |

#### 操作手順

1. **SettingsPanel → State list** タブ
2. `HwIdle` 行の **entry function** 列をダブルクリック
3. **ActionEditDialog** が開く
4. `InitHardware` を選択
5. OK

同様に他の entry / exit も設定します。

### 7.3 Role 関数を追加する

セルアクションと同様、必要になった時点で Role 関数を追加します。

**Driver 層では**:
- `InitHardware`, `WriteLcd`, `StopMotor` は既に登録済み
- 追加不要

### 7.4 Driver 層の完成を確認

#### チェックリスト

- [ ] 状態 3 個（HwIdle / HwActive / HwError）
- [ ] イベント 5 個（HW_ENABLE / HW_DISABLE / HW_MOTOR_START / HW_MOTOR_STOP / HW_ERROR）
- [ ] 遷移 4 個
- [ ] セルアクション 3 個
- [ ] entry / exit 3 個
- [ ] Role 関数 5 個

**Driver 層が完成しました。次は Middleware 層です。**

---

## 8. 手順6: 他の層も同様に完成させる

### 8.1 Middleware 層の遷移を追加

#### Middleware 層に追加する遷移

| # | 状態 | イベント | 遷移先 | 条件 | モード |
|---|------|---------|--------|------|--------|
| 1 | MwIdle | MW_START_COIN | CoinAccepting | （なし） | Commit |
| 2 | CoinAccepting | MW_COIN_VALID | MwIdle | （なし） | Commit |
| 3 | CoinAccepting | MW_COIN_INVALID | MwIdle | （なし） | Commit |
| 4 | MwIdle | MW_START_DISPENSE | Dispensing | （なし） | Commit |
| 5 | Dispensing | MW_DISPENSE_DONE | MwIdle | （なし） | Commit |
| 6 | MwIdle | MW_START_CHANGE | ChangeCalculating | （なし） | Commit |
| 7 | ChangeCalculating | MW_CHANGE_DONE | MwIdle | （なし） | Commit |

#### セルアクション

| # | セル | タイミング | 機能 |
|---|------|-----------|------|
| 1 | (CoinAccepting, MW_COIN_VALID) | before | `AccumulateCoin` |
| 2 | (Dispensing, MW_DISPENSE_DONE) | before | `StopDispense` |
| 3 | (ChangeCalculating, MW_CHANGE_DONE) | before | `DispenseChange` |

#### entry / exit

| # | 状態 | entry | exit |
|---|------|-------|------|
| 1 | CoinAccepting | `ValidateCoin` | （なし） |
| 2 | Dispensing | `DispenseProduct` | （なし） |
| 3 | ChangeCalculating | `CalculateChange` | （なし） |

#### Middleware 層で必要な Role 関数（6個）

| # | Function name | Namespace |
|---|--------------|-----------|
| 1 | `ValidateCoin` | `Middleware` |
| 2 | `AccumulateCoin` | `Middleware` |
| 3 | `DispenseProduct` | `Middleware` |
| 4 | `StopDispense` | `Middleware` |
| 5 | `CalculateChange` | `Middleware` |
| 6 | `DispenseChange` | `Middleware` |

### 8.2 Application 層の遷移を追加

#### Application 層に追加する遷移

| # | 状態 | イベント | 遷移先 | 条件 | モード |
|---|------|---------|--------|------|--------|
| 1 | Idle | SELECT | ProductSelected | （なし） | Commit |
| 2 | ProductSelected | COIN_IN | AwaitingPayment | （なし） | Commit |
| 3 | AwaitingPayment | CONFIRM | Dispensing | （なし） | Commit |
| 4 | Dispensing | DISPENSE_DONE | ReturningChange | `change_amount > 0` | Commit |
| 5 | Dispensing | DISPENSE_DONE | Idle | `change_amount == 0` | Commit |
| 6 | ReturningChange | CHANGE_DONE | Idle | （なし） | Commit |
| 7 | *（任意の状態） | ERROR | Error | （なし） | Commit |
| 8 | Error | RESET | Idle | （なし） | Commit |

### 8.3 セル関係を追加する（Application 層）

#### 8.3.1 セル関係とは

**セル関係** = 同じセル内の複数の遷移の関係性を定義します。

| 種類 | 意味 |
|------|------|
| `sequential` | 順番に評価（デフォルト） |
| `exclusive` | 最大1つだけ発火 |
| `group` | グループ化、共有条件を外側に |

#### 8.3.2 なぜ Application 層で必要か

Driver / Middleware 層では**各セルに1つの遷移**なので、関係は不要でした。

Application 層では、以下のように**複数の遷移を持つセル**があります:

```
セル (Dispensing, DISPENSE_DONE):
  T1: → ReturningChange （条件: change_amount > 0）
  T2: → Idle            （条件: change_amount == 0）
```

この2つの遷移は**排他的**（同時に成立しない）なので、`exclusive` を設定します。

#### 8.3.3 実践: (Dispensing, DISPENSE_DONE) の exclusive 設定

**操作手順**:

1. セル (Dispensing, DISPENSE_DONE) をダブルクリック
2. **Transitions タブ**で**2つの遷移**を追加:

   | フィールド | T1 | T2 |
   |-----------|-----|-----|
   | Target | `ReturningChange` | `Idle` |
   | Condition | `change_amount > 0` | `change_amount == 0` |
   | Mode | `Commit` | `Commit` |
   | Title | 釣銭あり | 釣銭なし |
   | Label | `T1` | `T2` |

3. **Relations タブ**に切り替え
4. **Add** で以下を設定:

   | フィールド | 値 |
   |-----------|-----|
   | Kind | `exclusive` |
   | Members | `T1, T2` |
   | Note | 釣銭の有無で排他的に分岐 |

5. OK

#### 8.3.4 他のセルでも使う場面

| セル | 使う関係 | 理由 |
|------|---------|------|
| (Idle, SELECT) | `sequential` | 商品選択は1つだけ |
| (AwaitingPayment, CONFIRM) | `sequential` | 確定は1つ |
| (Dispensing, DISPENSE_DONE) | **`exclusive`** | 釣銭の有無で排他 |
| (Error, RESET) | `sequential` | リセットは1つ |

**`group`** は、複数の遷移が同じ条件を共有する場合に使います（今回は使用しません）。

### 8.4 Application 層で必要な Role 関数（8個）

| # | Function name | Namespace |
|---|--------------|-----------|
| 1 | `ShowProductList` | `Application` |
| 2 | `HighlightProduct` | `Application` |
| 3 | `CalculateTotal` | `Application` |
| 4 | `CheckSufficientFunds` | `Application` |
| 5 | `RequestDispense` | `Application` |
| 6 | `RequestChange` | `Application` |
| 7 | `ShowError` | `Application` |
| 8 | `ResetSystem` | `Application` |

### 8.5 セルアクション / entry / exit（Application 層）

#### セルアクション

| # | セル | タイミング | 機能 |
|---|------|-----------|------|
| 1 | (Idle, SELECT) | before | `ShowProductList` |
| 2 | (ProductSelected, COIN_IN) | after | `HighlightProduct` |
| 3 | (AwaitingPayment, CONFIRM) | before | `CheckSufficientFunds` |
| 4 | (Error, RESET) | before | `ResetSystem` |

#### entry / exit

| # | 状態 | entry | exit |
|---|------|-------|------|
| 1 | ProductSelected | `HighlightProduct` | （なし） |
| 2 | Dispensing | `RequestDispense` | （なし） |
| 3 | ReturningChange | `RequestChange` | （なし） |
| 4 | Error | `ShowError` | （なし） |

### 8.6 3層すべての完成を確認

| 層 | 状態 | イベント | 遷移 | セルアクション | entry/exit | Role 関数 |
|---|-----|---------|------|--------------|-----------|----------|
| Driver | 3 | 5 | 4 | 3 | 3 | 5 |
| Middleware | 4 | 7 | 7 | 3 | 3 | 6 |
| Application | 6 | 8 | 8 | 4 | 4 | 8 |
| **合計** | **13** | **20** | **19** | **10** | **10** | **19** |

**3層すべての組み立てが完成しました。**

---

# 本編 — 完成させる

---

## 9. 手順7: 図で確認する

### 9.1 Mermaid 図の見方

#### 9.1.1 横型レイアウト（direction LR）

StaTable の状態遷移図は、**左から右へ流れる横型** で表示されます。

```
┌──────┐   START    ┌──────┐   TIMER   ┌──────┐
│ Idle │ ─────────→ │Blink │ ────────→ │Off   │
└──────┘            └──────┘           └──────┘
```

#### 9.1.2 なぜ横型か

| # | 理由 |
|---|------|
| 1 | **進行方向が直感的** — 時間の流れを左→右で表現 |
| 2 | **画面の横幅を活用** — モニタは横長 |
| 3 | **状態の並びが見やすい** — 同列の状態を比較しやすい |
| 4 | **マトリクスとの対応** — マトリクスの列（状態）と同じ順序 |

#### 9.1.3 縦型との比較

| 項目 | 横型（StaTable） | 縦型 |
|------|----------------|------|
| 進行方向 | 左 → 右 | 上 → 下 |
| 画面利用 | 横長モニタに最適 | 縦長 |
| 状態の並び | 横一列で比較可能 | 縦一列 |
| マトリクスとの対応 | 列 = 状態と一致 | 一致しない |

#### 9.1.4 実際の表示

Mermaid の `direction LR` で描画されます:

```
stateDiagram-v2
    direction LR
    [*] --> Idle
    Idle --> ProductSelected : SELECT
    ProductSelected --> AwaitingPayment : COIN_IN
    AwaitingPayment --> Dispensing : CONFIRM
```

### 9.2 各層の図を確認

3つのタブを切り替えて、**机上スケッチと一致するか**確認します。

#### 確認項目

| # | 確認内容 |
|---|---------|
| 1 | すべての状態が到達可能か |
| 2 | 終端状態（抜けられない状態）がないか |
| 3 | 意図した遷移がすべて描かれているか |
| 4 | 条件式が正しく表示されているか |
| 5 | entry / exit は図に表示されない（メタデータのみ） |

### 9.3 層の優先度を設定する

実行時の層の実行順序を決めます。

#### 操作手順

1. メニュー **Edit → Layer Settings...**
2. LayerSettingsDialog が開く
3. 各層の優先度を設定:

   | 層 | 優先度 | 意味 |
   |---|-------|------|
   | Driver | `1` | 最優先（ハードウェア制御） |
   | Middleware | `5` | 中位 |
   | Application | `9` | 最下位（販売ロジック） |

   > **優先度の意味**: 数値が小さいほど優先される（1〜9）

4. OK

#### 実行順序

```
1. Driver 層の状態機械を処理
       ↓
2. Middleware 層の状態機械を処理
       ↓
3. Application 層の状態機械を処理
```

### 9.4 問題があった場合の修正

| 問題 | 原因 | 対処 |
|------|------|------|
| 図に遷移が出ない | セルが空 | セルをダブルクリックして遷移を追加 |
| 孤立した状態がある | 遷移未定義 | その状態への遷移を追加 |
| 条件式が表示されない | 条件式が空 | 遷移編集で条件式を入力 |
| ラベルが重複している | 同じラベルを複数使用 | ラベルを `T1`, `T2`, ... と振り直す |

---

## 10. 手順8: C コードを生成する

### 10.1 出力先を設定する

1. メニュー **Code generation → Generation settings...**（**Ctrl+Shift+G**）
2. CodeGenerationSettingsDialog が開く
3. **Output settings** タブ
4. 以下を設定:

   | 項目 | 値 |
   |------|-----|
   | Output directory | （例: `C:\projects\vending_machine\output`） |
   | Folder structure | `by_layer`（推奨） |
   | Save with merge | ✅ チェック |

5. OK

### 10.2 生成する

1. メニュー **Code generation → Code generation...**（**Ctrl+G**）
2. CodeGenerationDialog が開く
3. **Generate** ボタンをクリック
4. 生成完了のメッセージを確認

### 10.3 生成ファイルを確認する

#### `by_layer` 構成の場合

```
output/
├── Driver/
│   ├── statable_types_Driver.h
│   ├── statable_transitions_Driver.c
│   ├── statable_transitions_Driver.h
│   ├── statable_role_functions_Driver.c
│   └── statable_role_functions_Driver.h
├── Middleware/
│   └── （同様の5ファイル）
├── Application/
│   └── （同様の5ファイル）
├── include/
│   └── statable_types_common.h
├── src/
│   ├── statable_init.c
│   ├── statable_event_queue.c
│   ├── statable_interrupt.c
│   ├── statable_timer.c
│   └── Untitled_run.c
└── common/
    ├── osal.h
    ├── osal.c
    └── statable_all.h
```

> **注**: 層別ファイル（15個）+ 共通ファイル（10個）= **合計25ファイル**。
> 層ごとにファイルが分かれるため、`by_type` より多くなります。

### 10.4 層別ファイルと共通ファイル

| 種類 | ファイル | 数 |
|------|---------|---|
| **層別** | `statable_types_<Layer>.h` など 5ファイル × 3層 | 15 |
| **共通** | `statable_types_common.h` | 1 |
| **共通** | `statable_init.c` など | 6 |
| **共通** | `osal.h` / `osal.c` | 2 |
| **共通** | `statable_all.h` | 1 |
| **合計** | | **25** |

#### セル関数の例

`statable_transitions_Driver.c` より:

```c
static STATE_Driver_t t_HwIdle_HW_ENABLE(
    const Transition_t* transition,
    TransitionContext_Driver_t* ctx)
{
    STATE_Driver_t next_state = STATE_Driver_HwIdle;

    if (1) {
        next_state = STATE_Driver_HwActive;  /* [Commit] */
    }

    return next_state;
}
```

#### Role 関数のユーザコード領域

`statable_role_functions_Driver.c` より:

```c
int RoleFunc_Driver_DriveMotor(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx)
{
    (void)ctx;

    /* [[STABLE_USER_CODE_START:Driver_DriveMotor]] */
    /* Write user implementation code here */
    /* [[STABLE_USER_CODE_END:Driver_DriveMotor]] */

    return 0;
}
```

> **重要**: ユーザコードは `[[STABLE_USER_CODE_START:...]]` と
> `[[STABLE_USER_CODE_END:...]]` の間に書きます。
> **マーカーを削除・改名しないでください** — 再生成時にコードが失われます。

---

## 11. 手順9: 組み込みに統合する

### 11.1 統合の全体像

```
1. main.c で SystemContext_Init を呼ぶ
2. メインループで各層を優先度順に処理
3. Role 関数のマーカー内にユーザコードを書く
```

### 11.2 main.c の最小構成

```c
#include "statable_all.h"
#include "board.h"

int main(void)
{
    SystemContext_t ctx;

    board_init();
    SystemContext_Init(&ctx);

    __enable_irq();

    while (1) {
        /* Driver 層（最優先） */
        EVENT_Driver_t drv_ev =
            StateMachine_GetNextEvent_Driver(&ctx);
        if (drv_ev != EVENT_Driver_NONE) {
            (void)StateMachine_Process_Driver(drv_ev, &ctx);
        }

        /* Middleware 層 */
        EVENT_Middleware_t mw_ev =
            StateMachine_GetNextEvent_Middleware(&ctx);
        if (mw_ev != EVENT_Middleware_NONE) {
            (void)StateMachine_Process_Middleware(mw_ev, &ctx);
        }

        /* Application 層 */
        EVENT_Application_t app_ev =
            StateMachine_GetNextEvent_Application(&ctx);
        if (app_ev != EVENT_Application_NONE) {
            (void)StateMachine_Process_Application(app_ev, &ctx);
        }

        /* その他のタスク */
        board_background_task();
    }
}
```

### 11.3 ISR とタイマーの設定概要

#### 11.3.1 割り込みが必要な理由

自動販売機は、以下の割り込み駆動で動作します:

| 割り込み源 | 用途 |
|-----------|------|
| コイン投入 | コインセンサのエッジ検出 |
| 商品排出完了 | モーター位置センサ |
| タイマー | タイムアウト検知 |

#### 11.3.2 コイン投入 ISR（例）

```c
void COIN_IRQHandler(void)
{
    /* 割り込みフラグクリア */
    COIN_SENSOR->SR = 0;

    /* イベントをキューに投入 */
    StateMachine_EnqueueEvent(
        &g_system_ctx,
        EVENT_Application_COIN_IN
    );
}
```

#### 11.3.3 タイマー ISR（タイムアウト検知）

```c
void SysTick_Handler(void)
{
    g_system_tick++;

    /* 1秒ごとにタイムアウトチェック */
    if ((g_system_tick % 1000) == 0) {
        StateMachine_EnqueueEvent(
            &g_system_ctx,
            EVENT_Application_TIMEOUT
        );
    }
}
```

#### 11.3.4 イベントのキュー投入

ISR から `StateMachine_EnqueueEvent` を呼ぶことで、
メインループで安全に処理できます。

### 11.4 Role 関数のユーザコード実装

生成された `statable_role_functions_Driver.c` のマーカー内に実装します。

```c
int RoleFunc_Driver_DriveMotor(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx)
{
    (void)ctx;

    /* [[STABLE_USER_CODE_START:Driver_DriveMotor]] */
    /* モータを指定角度だけ回転 */
    Motor_SetDirection(MOTOR_FORWARD);
    Motor_SetSpeed(200);
    Motor_Start();
    /* [[STABLE_USER_CODE_END:Driver_DriveMotor]] */

    return 0;
}
```

### 11.5 詳細は INTEGRATION_GUIDE_ja.md へ

統合の詳細（NonRTOS / FreeRTOS / ISR 設定など）は
`INTEGRATION_GUIDE_ja.md` を参照してください。

---

## 12. 手順10: プロジェクトを保存する

### 12.1 保存する

1. メニュー **File → Save Project...**
2. 保存先を指定（例: `VendingMachine.xml`）
3. 保存

### 12.2 何が保存されるか

| 保存対象 | 内容 |
|---------|------|
| 全タブの状態機械 | 状態 / イベント / 遷移 / Role 関数 |
| グローバル定義 | 変数 / フラグ / 割り込み / タイマー |
| 共有ライブラリ | Role 関数 / 条件 / リテラル |
| プロジェクト設定 | コード生成設定 |

### 12.3 ユーザコードの扱い

**重要**: ユーザコード（マーカー内）は **XML ではなく C ファイル**に保存されます。

```
VendingMachine.xml        ← 設計情報（StaTable で読み書き）
output/                   ← 生成 C コード（ユーザコード含む）
  └── Driver/
      └── statable_role_functions_Driver.c  ← ユーザコード
```

**XML には設計情報のみ。ユーザコードは C ファイルに残ります。**

---

# 応用編

---

## 13. 既存プロジェクトを流用する

### 13.1 流用設計のシナリオ

**シナリオ**: 飲料の自動販売機を開発した後、
**同じ Driver / Middleware を流用してコーヒー自販機を開発する**。

#### 製品の違い

| 項目 | 飲料自販機（既存） | コーヒー自販機（新規） |
|------|-----------------|---------------------|
| 商品 | 缶飲料 | コーヒー（カップ） |
| 選択方法 | ボタン（商品ごと） | ボタン（種類選択） |
| 提供方法 | 商品シュート | カップ + 抽出機構 |
| 追加機能 | なし | お湯、ミルク、砂糖の選択 |
| Application 層 | 飲料販売ロジック | コーヒー抽出ロジック |

#### なぜ「コーヒー自販機」を題材にするか

| # | 理由 |
|---|------|
| 1 | **Driver / Middleware が完全流用できる** — モータ、コイン処理、LCD が同じ |
| 2 | **差分が Application 層に集中** — 層の独立性の利点が明確 |
| 3 | **製品として現実的** — 実在する製品構成 |
| 4 | **学習効果が最大化** — 「どこを変えて、どこを変えないか」が一目で分かる |

### 13.2 流用できるもの / できないもの

| 層 | 流用可否 | 理由 |
|---|---------|------|
| **Driver 層** | ✅ **完全流用** | モータ、コイン、LCD は同じ |
| **Middleware 層** | ✅ **完全流用** | 商品排出、釣銭計算は同じ |
| **Application 層** | ❌ **新規作成** | コーヒー抽出ロジックが異なる |

#### 開発期間の短縮効果

| 層 | 新規開発 | 流用 |
|---|---------|------|
| Driver | 0% | **100%** |
| Middleware | 0% | **100%** |
| Application | 100% | 0% |
| **全体** | **約 33%** | **約 67%** |

**これが流用設計の最大の利点です。**
**2/3 の開発を省略できます。**

### 13.3 既存プロジェクトを開く

1. メニュー **File → Open Project...**
2. `VendingMachine.xml` を選択
3. 読み込み完了

**結果**: 3層すべてが復元されます。

### 13.4 Application 層だけを差し替える

#### 操作手順

1. **Application** タブを選択
2. 状態・イベント・遷移を編集
3. Role 関数も Application 層のものだけを編集
4. Driver / Middleware タブは**触らない**

#### 変更例

| 項目 | 変更前 | 変更後 |
|------|-------|-------|
| 状態 | `Idle` / `ProductSelected` / ... | `Idle` / `DrinkSelected` / ... |
| イベント | `SELECT` | `SELECT_DRINK` |
| Role 関数 | `ShowProductList` | `ShowDrinkList` |

### 13.5 層の独立性がもたらす利点

| # | 利点 |
|---|------|
| 1 | **Driver / Middleware を変更せずに済む** |
| 2 | **Application 層のテストだけを書き直せばよい** |
| 3 | **ハードウェア制御の実績をそのまま使える** |
| 4 | **開発期間を大幅に短縮できる** |

### 13.6 共有ライブラリの活用（任意）

プロジェクト全体で使う汎用関数は、共有ライブラリに登録します。

| # | 例 | 用途 |
|---|---|------|
| 1 | `Log` | ログ出力 |
| 2 | `Delay` | 待機 |
| 3 | `CheckSum` | チェックサム計算 |

#### 共有ライブラリへの登録

1. **File → Open Project** で XML を開く際、共有ライブラリも復元
2. 新規タブ追加時、共有ライブラリの関数が候補として表示される
3. namespace を分けることで衝突を回避

---

## 14. 反復開発

### 14.1 設計変更 → 再生成の流れ

```
1. 設計を変更（機能追加 / 遷移修正）
       ↓
2. 再生成（Save Generated Code）
       ↓
3. code_merger.py が自動マージ
       ↓
4. ユーザコードは保持される
```

### 14.2 ユーザコード保護（マージ）

#### マーカーの仕組み

```c
/* [[STABLE_USER_CODE_START:Driver_DriveMotor]] */
Motor_SetSpeed(200);   ← ユーザが書いた実装
/* [[STABLE_USER_CODE_END:Driver_DriveMotor]] */
```

再生成時、マーカー間のコードは**保持**されます。

#### マーカーの種類

| マーカー | 用途 |
|---------|------|
| `[[STABLE_USER_CODE_START]]` / `END` | ファイルレベル |
| `[[STABLE_USER_CODE_START:<name>]]` / `END:<name>` | 関数レベル |
| `[[STABLE_USER_CODE_TAIL_START]]` / `END` | ファイル末尾 |

### 14.3 冪等性の保証

**同じ設計で何度再生成しても、ファイルサイズは増えません。**

検証済み: `tests/test_v2_4_p1_merge.py` Test [3]

### 14.4 検証・AI 診断の活用

#### 検証機能

1. メニュー **Validate → Validation / AI diagnosis...**（**Ctrl+Shift+V**）
2. ValidationDialog が開く
3. **Validate** ボタンで検証実行

#### 検証される項目（35ルール）

| カテゴリ | ルール数 |
|---------|---------|
| state | 4 |
| event | 2 |
| transition | 5 |
| role_function | 3 |
| variable | 3 |
| flag | 2 |
| queue | 2 |
| interrupt | 2 |
| timer | 2 |
| custom_type | 2 |
| cell | 8 |
| **合計** | **35** |

---

# まとめ

---

## 15. 作業 × 機能 対応表

### 15.1 手順一覧

| # | 手順 | 章 |
|---|------|-----|
| 1 | プロジェクトを作る | 3 |
| 2 | 骨組みを作る（状態 + イベント） | 4 |
| 3 | 遷移を組む | 5 |
| 4 | セルを仕上げる | 6 |
| 5 | 状態を仕上げる | 7 |
| 6 | 他の層も完成させる | 8 |
| 7 | 図で確認する | 9 |
| 8 | C コードを生成する | 10 |
| 9 | 組み込みに統合する | 11 |
| 10 | プロジェクトを保存する | 12 |

### 15.2 機能一覧

| 作業 | 使う機能 |
|------|---------|
| プロジェクトを新規作成 | File → New Project |
| プロジェクトを開く | File → Open Project |
| プロジェクトを保存 | File → Save Project |
| 新しい層（タブ）を追加 | File → New State Machine |
| 状態を定義 | SettingsPanel → State list |
| イベントを定義 | SettingsPanel → Event definitions |
| Role 関数を定義 | SettingsPanel → Role function |
| 変数を定義 | Edit → Global Definitions |
| 遷移を追加 | MatrixTable → セルをダブルクリック |
| セルアクションを追加 | ActionEditorDialog → Pre/Post Actions |
| セル関係を追加 | ActionEditorDialog → Relations |
| entry / exit を設定 | State list → セルをダブルクリック |
| 図で確認 | MermaidWidget（自動更新） |
| C コード生成 | Code generation → Generate |
| 層の優先度を設定 | Edit → Layer Settings |
| 検証 | Validate → Validation |

### 15.3 ショートカット一覧

| ショートカット | 機能 |
|--------------|------|
| `Ctrl+N` | New Project |
| `Ctrl+G` | Code generation |
| `Ctrl+Shift+G` | Generation settings |
| `Ctrl+Shift+S` | Save generated code |
| `Ctrl+Shift+V` | Validation / AI diagnosis |

---

## 16. よくある質問（FAQ）

**Q1. なぜ最初に状態とイベントを全部登録するのか？**
A. 状態とイベントを登録すると、遷移マトリクスの枠が自動生成されます。
設計図を常に見ながら作業できるため、発見的設計に強い手法です。

**Q2. なぜ Driver 層から作るのか？**
A. 依存関係の方向と一致するためです。Driver 層は Application 層の
存在を知らないので、下位から作れば手戻りが少なくなります。
また、Driver 層は「機械が何をできるか」の定義であり、
これが最初に確定することで上位層の設計がスムーズになります。

**Q3. Role 関数はいつ登録するのか？**
A. 必要になった時点で登録します。事前に全部作る必要はありません。

**Q4. 複数の状態機械を 1 つのプロジェクトに含められる？**
A. はい。タブごとに独立した StateMachine を持てます。

**Q5. 層間で Role 関数を共有すべき？**
A. 共有は推奨しません。各層の独立性を保つため、層ごとに関数を
定義してください。

**Q6. 図が横型なのはなぜ？**
A. 時間の流れを左→右で表現し、横長モニタを活用するためです。
マトリクスの列（状態）と同じ順序で並ぶため、対応関係も見やすいです。

---

## 17. 次のステップ

### 17.1 学習パス

```
本チュートリアル（完了）
       ↓
INTEGRATION_GUIDE_ja.md（組み込み統合）
       ↓
SPEC_OVERVIEW_ja.md（詳細仕様）
```

### 17.2 参照ドキュメント

| # | 目的 | 参照ドキュメント |
|---|------|-----------------|
| 1 | 生成コードを組み込みに統合 | `INTEGRATION_GUIDE_ja.md` |
| 2 | 検証ルールの詳細 | `SPEC_OVERVIEW_ja.md` §7.5 |
| 3 | MISRA 対応 | `SPEC_OVERVIEW_ja.md` §7.4 |
| 4 | GUI 画面の詳細 | `SPEC_SCREENS_ja.md` |
| 5 | SDK として利用 | `SPEC_SDK_API_en.md` |

---

# 付録

---

## A. マーカーリファレンス

| マーカー | 用途 |
|---------|------|
| `[[STABLE_USER_CODE_START]]` / `END` | ファイルレベルのユーザコード領域 |
| `[[STABLE_USER_CODE_START:<name>]]` / `END:<name>` | 関数レベルのユーザコード領域 |
| `[[STABLE_USER_CODE_TAIL_START]]` / `END` | ファイル末尾のユーザコード領域 |

---

## B. 用語対応表

| StaTable 用語 | 一般的な呼称 | 本チュートリアルでの呼称 |
|--------------|-------------|----------------------|
| Role 関数 | 関数 / メソッド | **部品（機能）** |
| State | 状態 | 状態 |
| Event | イベント / 信号 | きっかけ |
| Transition | 遷移 | 遷移 |
| Layer | 層 | 層 |
| Namespace | 名前空間 | Namespace |
| Cell | セル | セル |

---

## C. 用語集

### C.1 基本用語

| 用語 | 説明 | 登場章 |
|------|------|-------|
| Layer（層） | タブごとの状態機械群 | 2.2 |
| State（状態） | 動作モード | 2.3 |
| Event（イベント） | 状態を変えるきっかけ | 2.4 |
| Transition（遷移） | 「A 状態で X イベントが来たら B 状態へ」 | 5.2 |
| Cell（セル） | (状態, イベント) の組 | 5.1 |

### C.2 Role 関数関連

| 用語 | 説明 | 登場章 |
|------|------|-------|
| Role 関数 | 条件評価とアクション用の関数（部品） | 1.4 |
| namespace | Role 関数の所属層 | 6.3 |
| qualified_name | `namespace.name` 形式 | 6.3 |
| 部品 | 本チュートリアルでの Role 関数の呼称 | 1.4 |

### C.3 遷移関連

| 用語 | 説明 | 登場章 |
|------|------|-------|
| Commit | `early_return=True`（後続遷移を停止） | 5.3 |
| Tentative | `early_return=False`（後続が上書き可能） | 5.3 |
| 条件式 | 遷移が成立する条件 | 5.4 |
| ラベル（T1, T2, ...） | セル内での遷移の識別子 | 5.5 |

### C.4 セル関連

| 用語 | 説明 | 登場章 |
|------|------|-------|
| セルアクション | 遷移非依存の付随処理 | 6.1 |
| before_transitions | 遷移評価の前 | 6.1 |
| after_transitions | 遷移評価の後 | 6.1 |
| セル関係 | セル内遷移間の関係 | 8.3 |
| sequential | 順番に評価 | 8.3 |
| exclusive | 最大1つだけ発火 | 8.3 |
| group | グループ化、共有条件を外側に | 8.3 |

### C.5 状態アクション

| 用語 | 説明 | 登場章 |
|------|------|-------|
| entry | 状態に入った時のアクション | 7.1 |
| exit | 状態を出る時のアクション | 7.1 |
| do | 状態にいる間のアクション（予約） | 7.1 |

### C.6 コード生成関連

| 用語 | 説明 | 登場章 |
|------|------|-------|
| マーカー | ユーザコード保持用コメント | 10.4 |
| マージ | 生成コードと既存コードの統合 | 14.2 |
| 冪等性 | 何度実行しても結果が同じ | 14.3 |
| セル関数 | 1つのセルを処理する static 関数 | 10.4 |

### C.7 描画関連

| 用語 | 説明 | 登場章 |
|------|------|-------|
| Mermaid | 状態遷移図の生成エンジン | 9.1 |
| 横型（LR） | 左→右に流れる状態遷移図 | 9.1 |
| 縦型（TD） | 上→下に流れる状態遷移図（未使用） | 9.1 |

### C.8 規格関連

| 用語 | 説明 | 登場章 |
|------|------|-------|
| MISRA C:2012 | 車載向け C 言語規格 | 14.4 |
| cppcheck | 静的解析ツール | 14.4 |
| 抑制 | 意図的な規格逸脱 | 14.4 |

### C.9 その他

| 用語 | 説明 | 登場章 |
|------|------|-------|
| Tab（タブ） | 層を表す UI 要素 | 3.3 |
| Matrix（マトリクス） | 遷移マトリクス（状態 × イベント） | 4.1 |
| SettingsPanel | 右側の設定パネル | 3.3 |
| MermaidWidget | 下部の図表示ウィジェット | 9.1 |
| ISR | 割り込みサービスルーチン | 11.3 |
| OSAL | OS 抽象化層 | 10.4 |

---

## D. 変更履歴

| バージョン | 日付 | 内容 |
|-----------|------|------|
| 1.0 | 2026-09-22 | 初版。自動販売機を題材に、骨組み → マトリクス → 完成の手順で構成 |

---

以上、`TUTORIAL_ja.md` v1.0 の完全版です。
```

---

## 保存手順

### 1. Notepad で新規ファイルを作成

```powershell
cd C:\Users\user\OneDrive\ドキュメント\GitHub\StaTable\code
notepad docs\TUTORIAL_ja.md
```

### 2. 全文を貼り付け

- 上記のコードブロック内を**全選択してコピー**
- Notepad に貼り付け
- **Ctrl+S** で保存

### 3. 確認

```powershell
# 行数
(Get-Content docs\TUTORIAL_ja.md).Count

# 章立て
Select-String -Path docs\TUTORIAL_ja.md -Pattern "^## "
```

**期待**：
- 行数：約 1,800〜2,000 行
- 章立て：17章 + 付録4つ

---
