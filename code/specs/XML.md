コード生成バリエーション網羅を目的に、**Application 単層サンプルで XML 仕様書を確定**できます。model.py / global_defs.py / state_machine.py で全情報が揃ったので、以下をドラフトとして提示します。

---

# XML 仕様書 v2.2.5 — コード生成バリエーション網羅（Application 単層）

## 1. 確定情報サマリ（コードから抽出済）

### 1.1 Enum 全値確定

| Enum | 値（XML 文字列） | 数 |
|---|---|---|
| `StateType` | `normal` / `concurrent` / `region` / `initial` / `final` / `choice` / `junction` | 7 |
| `EventKind` | `signal` / `call` / `time` / `change` | 4 |
| `EventDeliveryType` | `direct` / `queue` / `double` | 3 |
| `EventSourceLayer` | `driver` / `middleware` | 2 |

### 1.2 cell キーの順序保証

```python
get_cell_keys() → sorted(set(actions.keys()) | set(relations.keys()))
```
- キーは `(source, event)` のタプル、**辞書順ソート**
- Action リストは **挿入順保持**（`list(actions)`）
- Relation リストも **挿入順保持**

→ round-trip の Level 1 canonical 比較（属性順・要素順ソート）と整合。

### 1.3 `add_timer_variables()` の副作用（round-trip 注意点）

- `variables` に Timer 系を**自動追加**する
- 既存変数の `type`/`unit` は **timer 定義が上書き**
- `description`/`title` は **既存値優先**（空のときのみデフォルト補完）

→ テスト XML 作成時、`TimerBase` で宣言した変数は `SystemVariables` に**重複記載しても上書きされる**点に注意。

---

## 2. コード生成バリエーション網羅マトリクス

Application 単層サンプルで網羅すべき variation を 6 カテゴリに整理：

### A. State 種別（7 種）

| # | StateType | 検証ポイント |
|---|---|---|
| A1 | `initial` | 初期状態として `set_initial` と一致 |
| A2 | `normal` | 基本遷移 |
| A3 | `final` | 終端（遷移なし） |
| A4 | `concurrent` | 並列リージョン生成 |
| A5 | `region` | サブリージョン |
| A6 | `choice` | 条件分岐ノード |
| A7 | `junction` | マージノード |

### B. Event 属性（4 × 3 × 2 + 拡張）

| 軸 | 値 | 組み合わせ |
|---|---|---|
| kind | signal / call / time / change | 4 |
| delivery_type | direct / queue / double | 3 |
| source_layer | driver / middleware | 2 |
| priority | 0 / 1 / 2 | 3 水準 |
| data_type + data_name | あり / なし | 2 |
| params | あり / なし | 2 |

→ **代表 6 パターン**で全軸カバー可能。

### C. Transition 属性

| 軸 | 値 | 検証 |
|---|---|---|
| has_else | true / false | else 分岐生成 |
| else_target | "" / 状態名 | 空なら self 扱い |
| early_return | true (Commit) / false (Tentative) | `_handled` 制御 |
| condition | "" / 式 | if ガード生成 |
| pre_actions | 0 / 1 / 複数 | 順次呼出 |
| else_actions | 0 / 1 / 複数 | else 側呼出 |
| label | "" / "T1" | Relation 参照 |
| transition_type | external / internal（要確認） | 遷移コード |

### D. Cell metadata

| 軸 | 値 |
|---|---|
| Actions trigger | before_transitions / after_transitions / 両方 / 複数 |
| Relations kind | sequential / exclusive / group |
| Relation ネスト | 0 / 1 / 2+ 階層 |
| shared_condition | "" / 式 |

### E. RoleFunction

| 軸 | 値 |
|---|---|
| namespace | "" / "App" / "Driver"（不一致テスト） |
| return_type | void / int / 独自型 |
| args | 0 / 1 / 2 個 |

### F. Layer 設定

| 軸 | 値 |
|---|---|
| layer_priority | 1 / 5 |
| layer_name | "Application" |
| layer_description | "" / 文字列 |

---

## 3. XML リファレンス（作成用属性表）

### 3.1 ルート

```xml
<?xml version='1.0' encoding='utf-8'?>
<Project name="...">
```

### 3.2 全要素・全属性（テスト作成時に参照）

| 要素 | 属性（型 / デフォルト） |
|---|---|
| `State` | `name`* / `type`="normal" / `parent`="" / `do`="" / `description`="" |
| `State/Entry/Action` | `name`* |
| `State/Exit/Action` | `name`* |
| `Event` | `name`* / `id`="" / `kind`="signal" / `params`="" / `priority`="0" / `description`="" / `delivery_type`="direct" / `source_layer`="driver" / `data_type`="" / `data_name`="" / `title`="" |
| `RoleFunction` | `name`* / `namespace`="" / `description`="" / `return_type`="int"※ / `arg1_type`="" / `arg1_name`="" / `arg2_type`="" / `arg2_name`="" / `title`="" |
| `Transition` | `source`* / `event`* / `condition`="" / `action`="" / `target`="" / `transition_type`="external" / `title`="" / `has_else`="true" / `else_target`="" / `early_return`="false" / `label`="" |
| `Transition/PreAction` | `action`* |
| `Transition/ElseAction` | `action`* |
| `Cell` | `source`* / `event`* |
| `Cell/Action` | `role_function`* / `trigger`="before_transitions" / `title`="" |
| `Relation` | `kind`="sequential" / `members`="," 区切り / `shared_condition`="" / `note`="" |
| `Relation/Children/Relation` | 再帰 |

※ `RoleFunction` の `return_type` は XML ローダが `"int"` をデフォルトにしていますが、モデル側デフォルトは `"void"`。**XML 作成時は明示推奨**。

### 3.3 canonical 形で無視される差分

- 属性の記述順
- 要素の兄弟順（`canon()` が `sorted()` するため）
- 空白 / インデント

→ **テスト XML を書くときに順序を気にしなくて良い**（ただし意味比較 Level 2 では別途順序考慮あり）。

---

## 4. Application サンプル設計方針

### 4.1 1 ファイルで全 variation を踏む構成

```
Application 単層
├── States (7) : Idle/initial, Running/normal, Paused/normal,
│                Done/final, Choice1/choice, Join1/junction,
│                Parallel/concurrent(+Region1/region)
├── Events (6) : START, STOP, TICK, STATE_CHANGED, API_CALL, ERROR(with data)
├── RoleFunctions (~12)
├── Transitions (~15)
│   ├── has_else=true/false
│   ├── early_return=true/false
│   ├── pre_actions 0/1/2
│   ├── else_actions 0/1
│   └── condition "" / 式
└── Cells (~8)
    ├── actions (before only / after only / both)
    ├── relations (sequential / exclusive / group)
    └── nested group (2 階層)
```

### 4.2 網羅マトリクス（対応表）

| Variation | 対応 State/Event/Transition |
|---|---|
| A1 initial | Idle |
| A2 normal | Running, Paused |
| A3 final | Done |
| A4 concurrent | Parallel |
| A5 region | Region1（Parallel 配下） |
| A6 choice | Choice1 |
| A7 junction | Join1 |
| B kind=signal | START, STOP, ERROR |
| B kind=call | API_CALL |
| B kind=time | TICK |
| B kind=change | STATE_CHANGED |
| B delivery=direct | START, TICK, API_CALL |
| B delivery=queue | STOP, ERROR |
| B delivery=double | （要追加: DUAL） |
| B source=driver | TICK, STATE_CHANGED, ERROR |
| B source=middleware | START, STOP, API_CALL |
| B data あり | ERROR |
| C has_else=true | Idle+START |
| C has_else=false | 多数 |
| C early_return=true | 多数 |
| C early_return=false | Paused+STOP の 1 本 |
| C pre_actions=2 | Running entry 相当 |
| C else_actions=1 | Idle+START |
| D actions before only | Cell(Running, API_CALL) |
| D actions after only | Cell(Paused, TICK) |
| D actions both | Cell(Idle, START) |
| D relations seq | Cell(Running, PAUSE) |
| D relations excl | Cell(Error, RESET) |
| D relations group | Cell(Running, STOP) |
| D nested group | Cell(Running, STOP) 2 階層 |
| E namespace="" | （1 つ入れる: GlobalFunc） |
| E return_type=void | （1 つ入れる） |
| E args=2 | （1 つ入れる: SetMode(int, int)） |
| F layer_priority | 5 |
| F layer_name | "Application" |

---

## 5. Application サンプル XML（骨子・コピペ可）

以下は**完全な 1 ファイル**として使えるドラフトです。プロジェクト名は `VariationCoverage`、単一 Tab = Application。

```xml
<?xml version='1.0' encoding='utf-8'?>
<Project name="VariationCoverage">
    <ProjectSettings>
        <CodeGeneration project_name="VariationCoverage"
                        table_type="array"
                        generation_style="table_driven"
                        os_type="non_rtos"
                        folder_structure="by_layer"
                        include_dir_name="include"
                        source_dir_name="src"
                        common_dir_name="common"
                        project_dir_name="project"
                        generate_super_include="true"
                        super_include_file="statable_all.h"
                        max_consecutive_pending_events="16"
                        external_includes_in_super="true"
                        external_includes_in_role="true"
                        external_includes_in_transitions="false"
                        external_includes_in_common="false" />
    </ProjectSettings>
    <GlobalDefinitions>
        <SystemVariables>
            <Variable name="counter" type="uint32_t" unit="" default_value="0" group="System" description="Counter" title="Counter" array_size="0" />
            <Variable name="mode" type="uint8_t" unit="" default_value="0" group="System" description="Mode" title="Mode" array_size="0" />
            <Variable name="err_code" type="uint8_t" unit="" default_value="0" group="System" description="Error code" title="Error code" array_size="0" />
            <Variable name="g_system_tick" type="volatile uint32_t" unit="1ms" default_value="0" group="Timer" description="Timer base" title="System tick" array_size="0" />
        </SystemVariables>
        <EventFlags>
            <Flag name="EVT_READY" min_value="0" max_value="1" group="System" description="Ready" title="Ready" />
        </EventFlags>
        <Interrupts>
            <Interrupt name="TIMER0" description="1ms" event_names="" is_timer="true" title="Timer0">
                <Action condition="" action="ctx-&gt;data.g_system_tick++" />
                <UsedVariable name="g_system_tick" />
            </Interrupt>
        </Interrupts>
        <TimerBase>
            <Timer variable_name="g_system_tick" unit="1ms" data_type="volatile uint32_t" title="System tick" interrupt_name="TIMER0" />
        </TimerBase>
    </GlobalDefinitions>
    <SharedLibraries>
        <RoleFunctionLibrary />
        <ConditionLibrary />
        <LiteralLibrary />
    </SharedLibraries>
    <Tab name="Application">
        <StateMachine initial="Idle" layer_priority="5"
                      layer_description="Application layer (variation coverage)"
                      layer_name="Application">
            <States>
                <!-- A1 initial + Entry/Exit -->
                <State name="Idle" type="initial" parent="" do="" description="Idle">
                    <Entry><Action name="App.IdleEntry" /></Entry>
                    <Exit><Action name="App.IdleExit" /></Exit>
                </State>
                <!-- A2 normal + 複数 Entry -->
                <State name="Running" type="normal" parent="" do="" description="Running">
                    <Entry>
                        <Action name="App.RunEntry1" />
                        <Action name="App.RunEntry2" />
                    </Entry>
                </State>
                <State name="Paused" type="normal" parent="" do="" description="Paused">
                    <Entry><Action name="App.PauseEntry" /></Entry>
                    <Exit><Action name="App.PauseExit" /></Exit>
                </State>
                <!-- A3 final -->
                <State name="Done" type="final" parent="" do="" description="Done" />
                <!-- A6 choice -->
                <State name="Choice1" type="choice" parent="" do="" description="Decision node" />
                <!-- A7 junction -->
                <State name="Join1" type="junction" parent="" do="" description="Merge node" />
                <!-- A4 concurrent + A5 region -->
                <State name="Parallel" type="concurrent" parent="" do="" description="Parallel region" />
                <State name="Region1" type="region" parent="Parallel" do="" description="Sub region" />
            </States>
            <Events>
                <!-- B: signal/direct/middleware -->
                <Event name="START" id="1" kind="signal" params="" priority="0" description="Start" delivery_type="direct" source_layer="middleware" data_type="" data_name="" title="Start" />
                <!-- B: signal/queue/middleware -->
                <Event name="STOP" id="2" kind="signal" params="" priority="1" description="Stop" delivery_type="queue" source_layer="middleware" data_type="" data_name="" title="Stop" />
                <!-- B: time/direct/driver -->
                <Event name="TICK" id="3" kind="time" params="" priority="0" description="Tick" delivery_type="direct" source_layer="driver" data_type="" data_name="" title="Tick" />
                <!-- B: change/direct/driver -->
                <Event name="STATE_CHANGED" id="4" kind="change" params="" priority="0" description="State changed" delivery_type="direct" source_layer="driver" data_type="" data_name="" title="StateChanged" />
                <!-- B: call/direct/middleware -->
                <Event name="API_CALL" id="5" kind="call" params="arg1,arg2" priority="0" description="API call" delivery_type="direct" source_layer="middleware" data_type="" data_name="" title="ApiCall" />
                <!-- B: signal/queue/driver + data -->
                <Event name="ERROR" id="6" kind="signal" params="" priority="2" description="Error" delivery_type="queue" source_layer="driver" data_type="uint8_t" data_name="err_code" title="Error" />
                <!-- B: double delivery -->
                <Event name="DUAL" id="7" kind="signal" params="" priority="0" description="Dual delivery" delivery_type="double" source_layer="middleware" data_type="" data_name="" title="Dual" />
            </Events>
            <RoleFunctions>
                <RoleFunction name="IdleEntry" namespace="App" description="" return_type="int" arg1_type="" arg1_name="" arg2_type="" arg2_name="" title="Idle entry" />
                <RoleFunction name="IdleExit" namespace="App" description="" return_type="int" arg1_type="" arg1_name="" arg2_type="" arg2_name="" title="Idle exit" />
                <RoleFunction name="RunEntry1" namespace="App" description="" return_type="int" arg1_type="" arg1_name="" arg2_type="" arg2_name="" title="Run entry 1" />
                <RoleFunction name="RunEntry2" namespace="App" description="" return_type="int" arg1_type="" arg1_name="" arg2_type="" arg2_name="" title="Run entry 2" />
                <RoleFunction name="PauseEntry" namespace="App" description="" return_type="int" arg1_type="" arg1_name="" arg2_type="" arg2_name="" title="Pause entry" />
                <RoleFunction name="PauseExit" namespace="App" description="" return_type="int" arg1_type="" arg1_name="" arg2_type="" arg2_name="" title="Pause exit" />
                <RoleFunction name="Start" namespace="App" description="" return_type="int" arg1_type="" arg1_name="" arg2_type="" arg2_name="" title="Start" />
                <RoleFunction name="Stop" namespace="App" description="" return_type="int" arg1_type="" arg1_name="" arg2_type="" arg2_name="" title="Stop" />
                <RoleFunction name="OnTick" namespace="App" description="" return_type="int" arg1_type="" arg1_name="" arg2_type="" arg2_name="" title="On tick" />
                <RoleFunction name="OnChange" namespace="App" description="" return_type="int" arg1_type="" arg1_name="" arg2_type="" arg2_name="" title="On change" />
                <RoleFunction name="OnApi" namespace="App" description="" return_type="int" arg1_type="" arg1_name="" arg2_type="" arg2_name="" title="On API" />
                <RoleFunction name="LogError" namespace="App" description="" return_type="int" arg1_type="" arg1_name="" arg2_type="" arg2_name="" title="Log error" />
                <RoleFunction name="Cleanup" namespace="App" description="" return_type="int" arg1_type="" arg1_name="" arg2_type="" arg2_name="" title="Cleanup" />
                <RoleFunction name="PreCheck" namespace="App" description="" return_type="int" arg1_type="" arg1_name="" arg2_type="" arg2_name="" title="Pre-check" />
                <!-- E: namespace なし -->
                <RoleFunction name="GlobalFunc" namespace="" description="" return_type="void" arg1_type="" arg1_name="" arg2_type="" arg2_name="" title="Global (no namespace)" />
                <!-- E: 引数 2 個 -->
                <RoleFunction name="SetMode" namespace="App" description="" return_type="int" arg1_type="uint8_t" arg1_name="new_mode" arg2_type="uint8_t" arg2_name="flags" title="Set mode" />
            </RoleFunctions>
            <Transitions>
                <!-- C: has_else=true + else_actions + early_return=true -->
                <Transition source="Idle" event="START"
                            condition="counter &gt; 0"
                            action="" target="Running"
                            transition_type="external"
                            title="Start"
                            has_else="true" else_target="Done"
                            early_return="true" label="T1">
                    <PreAction action="App.Start" />
                    <ElseAction action="App.LogError" />
                </Transition>

                <!-- C: early_return=false (Tentative) -->
                <Transition source="Running" event="PAUSE"
                            condition="mode == 0"
                            action="" target="Paused"
                            transition_type="external"
                            title="Pause tentative"
                            has_else="false" else_target=""
                            early_return="false" label="T1">
                    <PreAction action="App.PauseEntry" />
                </Transition>
                <Transition source="Running" event="PAUSE"
                            condition="mode != 0"
                            action="" target="Running"
                            transition_type="external"
                            title="Pause ignored"
                            has_else="false" else_target=""
                            early_return="false" label="T2" />

                <!-- C: pre_actions 0 -->
                <Transition source="Paused" event="START"
                            condition=""
                            action="" target="Running"
                            transition_type="external"
                            title="Resume"
                            has_else="false" else_target=""
                            early_return="true" label="T1" />

                <!-- B time event 使用 -->
                <Transition source="Running" event="TICK"
                            condition="g_system_tick &gt; 100"
                            action="" target="Join1"
                            transition_type="external"
                            title="On tick"
                            has_else="false" else_target=""
                            early_return="true" label="T1">
                    <PreAction action="App.OnTick" />
                </Transition>

                <!-- B change event 使用 -->
                <Transition source="Running" event="STATE_CHANGED"
                            condition=""
                            action="" target="Choice1"
                            transition_type="external"
                            title="On change"
                            has_else="false" else_target=""
                            early_return="true" label="T1">
                    <PreAction action="App.OnChange" />
                </Transition>

                <!-- Choice -> 分岐 -->
                <Transition source="Choice1" event="API_CALL"
                            condition="counter &gt; 10"
                            action="" target="Paused"
                            transition_type="external"
                            title="Choice paused"
                            has_else="true" else_target="Running"
                            early_return="true" label="T1">
                    <PreAction action="App.OnApi" />
                </Transition>

                <!-- B: ERROR with data + queue -->
                <Transition source="Running" event="ERROR"
                            condition="err_code == 1"
                            action="" target="Done"
                            transition_type="external"
                            title="Fatal error"
                            has_else="false" else_target=""
                            early_return="true" label="T1">
                    <PreAction action="App.LogError" />
                </Transition>
                <Transition source="Running" event="ERROR"
                            condition="err_code != 1"
                            action="" target="Paused"
                            transition_type="external"
                            title="Recoverable"
                            has_else="false" else_target=""
                            early_return="false" label="T2" />

                <!-- Junction -> concurrent -->
                <Transition source="Join1" event="DUAL"
                            condition=""
                            action="" target="Parallel"
                            transition_type="external"
                            title="To parallel"
                            has_else="false" else_target=""
                            early_return="true" label="T1" />

                <!-- STOP + 引数付き RF -->
                <Transition source="Paused" event="STOP"
                            condition=""
                            action="" target="Done"
                            transition_type="external"
                            title="Stop"
                            has_else="false" else_target=""
                            early_return="true" label="T1">
                    <PreAction action="App.Stop" />
                    <PreAction action="App.SetMode" />
                </Transition>
            </Transitions>
            <Cells>
                <!-- D: actions before + after -->
                <Cell source="Idle" event="START">
                    <Actions>
                        <Action role_function="App.PreCheck" trigger="before_transitions" title="Pre-check" />
                        <Action role_function="App.Cleanup" trigger="after_transitions" title="Cleanup" />
                    </Actions>
                </Cell>
                <!-- D: relations sequential -->
                <Cell source="Running" event="PAUSE">
                    <Relations>
                        <Relation kind="sequential" members="T1,T2" shared_condition="" note="T1 then T2" />
                    </Relations>
                </Cell>
                <!-- D: actions after only -->
                <Cell source="Running" event="TICK">
                    <Actions>
                        <Action role_function="App.Cleanup" trigger="after_transitions" title="Cleanup" />
                    </Actions>
                </Cell>
                <!-- D: actions before only + relations group -->
                <Cell source="Running" event="ERROR">
                    <Actions>
                        <Action role_function="App.PreCheck" trigger="before_transitions" title="Pre-check" />
                    </Actions>
                    <Relations>
                        <Relation kind="group" members="T1,T2"
                                  shared_condition="counter &gt; 0"
                                  note="Gate on counter" />
                    </Relations>
                </Cell>
                <!-- D: nested group (2 階層) -->
                <Cell source="Paused" event="START">
                    <Relations>
                        <Relation kind="group" members="T1"
                                  shared_condition="counter &gt; 0"
                                  note="Parent group">
                            <Children>
                                <Relation kind="exclusive" members="T1"
                                          shared_condition=""
                                          note="Child: exclusive" />
                            </Children>
                        </Relation>
                    </Relations>
                </Cell>
                <!-- D: relations exclusive -->
                <Cell source="Paused" event="STOP">
                    <Relations>
                        <Relation kind="exclusive" members="T1"
                                  shared_condition=""
                                  note="At most one" />
                    </Relations>
                </Cell>
            </Cells>
        </StateMachine>
    </Tab>
</Project>
```

---

## 6. このサンプルで網羅できていない項目（必要なら追加）

| # | 未網羅 | 追加案 |
|---|---|---|
| 1 | `Event.params` 付き transition | `API_CALL` は params 付きだが、これを遷移条件に使うサンプル未 |
| 2 | `RoleFunction` の `arg1`/`arg2` の型バリエーション | 1 種類のみ |
| 3 | `Transition.transition_type` の `internal` | external のみ |
| 4 | `State.parent` の実効性 | `Region1.parent="Parallel"` のみ |
| 5 | `CustomTypes` / `EventQueues` / `ExtraTimers` | 未使用（GlobalDefinitions 側） |
| 6 | 自己遷移（target == source） | 明示していない（`Paused+START→Running` は別状態） |

---

## 7. 確認したいこと

1. **`transition_type` の許容値** — `external` 以外に `internal` は実在しますか？（`c_code_generator.py` を見ないと確定できない）
2. **`State.parent` の扱い** — `concurrent` / `region` の親子関係はコード生成にどう反映されますか？
3. **`Event.params` の実効性** — 生成コードの関数引数になりますか、コメントのみですか？
4. 上記 §5 サンプルを **テスト fixture として確定**して良いですか？ あるいは追加 variation を入れますか？

回答をいただければ、この XML を仕様書本体に組み込み、`tests/data/variation_coverage.xml` として配置できる形に整えます。