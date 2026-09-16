# tests/test_xml_io.py
"""
xml_io のユニットテスト

【目的】
  XML 保存/読込のエッジケースと回帰防止:
    - 空プロジェクトの round-trip
    - 特殊文字 / Unicode を含む文字列の round-trip
    - レガシー XML（namespace 未設定）の自動移行
    - _normalize_actions の 1 文字分解救済
    - 共有ライブラリ（RoleFunction / Condition / Literal）の round-trip
    - プロジェクト設定（CodeGeneration）の round-trip
    - グローバル定義（変数・フラグ・割り込み・タイマ）の round-trip

【対象】
  statable/xml_io.py
"""
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from statable.model import State, Event, Transition, StateType, EventKind, RoleFunction
from statable.state_machine import StateMachine
from statable.global_defs import (
    GlobalDefinitions, SystemVariable, EventFlag,
    InterruptHandlerDef, InterruptAction,
)
from statable.xml_io import (
    project_to_xml, project_from_xml, _normalize_actions,
)


# ============================================================
# ヘルパー
# ============================================================

def _save_and_load(tmp_path, tabs, gd, settings=None,
                   role_lib=None, cond_lib=None, lit_lib=None):
    """保存 → 読込の往復"""
    path = tmp_path / "test.xml"
    project_to_xml(
        tabs, gd, str(path),
        role_function_library=role_lib,
        condition_library=cond_lib,
        literal_library=lit_lib,
        project_settings=settings,
    )
    return project_from_xml(str(path))


def _xml_bytes(path: Path) -> str:
    """XML ファイルを正規化して比較しやすくする"""
    text = path.read_text(encoding="utf-8")
    return ET.canonicalize(text, strip_text=True)


# ============================================================
# _normalize_actions
# ============================================================

class TestNormalizeActions:

    def test_none_returns_empty(self):
        assert _normalize_actions(None) == []

    def test_empty_string_returns_empty(self):
        assert _normalize_actions("") == []

    def test_whitespace_only_returns_empty(self):
        assert _normalize_actions("   ") == []

    def test_single_string(self):
        assert _normalize_actions("init()") == ["init()"]

    def test_normal_list(self):
        assert _normalize_actions(["init()", "reset()"]) == ["init()", "reset()"]

    def test_one_char_list_joined(self):
        """1 文字ずつに分解された旧データを結合"""
        assert _normalize_actions(["i", "n", "i", "t", "(", ")"]) == ["init()"]

    def test_empty_items_filtered(self):
        assert _normalize_actions(["a", "", "  ", "b"]) == ["a", "b"]

    def test_non_string_converted(self):
        result = _normalize_actions(42)
        assert result == ["42"]


# ============================================================
# 空プロジェクトの round-trip
# ============================================================

class TestEmptyProject:

    def test_empty_state_machine_roundtrip(self, tmp_path):
        """状態・イベント・遷移なしの StateMachine が往復する"""
        sm = StateMachine()
        tabs = [("Main", sm)]
        gd = GlobalDefinitions()

        loaded_tabs, loaded_gd, *_ = _save_and_load(tmp_path, tabs, gd)

        assert len(loaded_tabs) == 1
        assert loaded_tabs[0][0] == "Main"
        assert len(loaded_tabs[0][1].states) == 0
        assert len(loaded_tabs[0][1].events) == 0
        assert len(loaded_tabs[0][1].transitions) == 0


# ============================================================
# 特殊文字 / Unicode の round-trip
# ============================================================

class TestSpecialCharacters:

    def test_unicode_in_state_name(self, tmp_path):
        sm = StateMachine()
        sm.add_state(State(name="待機"))
        sm.add_state(State(name="動作中"))
        tabs = [("Main", sm)]
        gd = GlobalDefinitions()

        loaded_tabs, *_ = _save_and_load(tmp_path, tabs, gd)
        names = set(loaded_tabs[0][1].states.keys())
        assert names == {"待機", "動作中"}

    def test_colon_in_transition_title(self, tmp_path):
        """タイトル内の ':' が XML で保持される"""
        sm = StateMachine()
        sm.add_state(State(name="A"))
        sm.add_state(State(name="B"))
        sm.add_event(Event(name="GO"))
        sm.add_transition(Transition(
            source="A", event="GO", target="B",
            title="RETRY: battery_voltage >600",
        ))
        tabs = [("Main", sm)]
        gd = GlobalDefinitions()

        loaded_tabs, *_ = _save_and_load(tmp_path, tabs, gd)
        loaded_trans = loaded_tabs[0][1].transitions[0]
        assert loaded_trans.title == "RETRY: battery_voltage >600"

    def test_ampersand_in_title(self, tmp_path):
        """'&' を含む文字列が XML エスケープで保持される"""
        sm = StateMachine()
        sm.add_state(State(name="A"))
        sm.add_state(State(name="B"))
        sm.add_event(Event(name="GO"))
        sm.add_transition(Transition(
            source="A", event="GO", target="B",
            title="A & B 同時",
        ))
        tabs = [("Main", sm)]
        gd = GlobalDefinitions()

        loaded_tabs, *_ = _save_and_load(tmp_path, tabs, gd)
        assert loaded_tabs[0][1].transitions[0].title == "A & B 同時"


# ============================================================
# レガシー XML 自動移行
# ============================================================

class TestLegacyMigration:

    def test_legacy_role_function_migrated(self, tmp_path):
        """
        'Driver_Init' (namespace 未設定) → namespace='Driver', name='Init'
        """
        # レガシー XML を直接生成
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
<Project name="LegacyTest">
  <GlobalDefinitions></GlobalDefinitions>
  <Tab name="Driver">
    <StateMachine initial="" layer_name="Driver">
      <States><State name="Idle" type="normal" parent="" entry="" exit="" do="" description=""/></States>
      <Events></Events>
      <RoleFunctions>
        <RoleFunction name="Driver_Init" description="初期化" return_type="int"
                      arg1_type="" arg1_name="" arg2_type="" arg2_name="" title=""/>
      </RoleFunctions>
      <Transitions></Transitions>
    </StateMachine>
  </Tab>
</Project>"""
        path = tmp_path / "legacy.xml"
        path.write_text(xml_content, encoding="utf-8")

        tabs, *_ = project_from_xml(str(path))
        sm = tabs[0][1]
        rfs = list(sm.role_functions.values())
        assert len(rfs) == 1
        assert rfs[0].name == "Init"
        assert rfs[0].namespace == "Driver"

    def test_legacy_role_function_roundtrip_preserves_migration(self, tmp_path):
        """移行後の再保存 → 再読込で安定（冪等）"""
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
<Project name="LegacyTest">
  <GlobalDefinitions></GlobalDefinitions>
  <Tab name="Driver">
    <StateMachine initial="" layer_name="Driver">
      <States><State name="Idle" type="normal" parent="" entry="" exit="" do="" description=""/></States>
      <Events></Events>
      <RoleFunctions>
        <RoleFunction name="Driver_Init" description="初期化" return_type="int"
                      arg1_type="" arg1_name="" arg2_type="" arg2_name="" title=""/>
      </RoleFunctions>
      <Transitions></Transitions>
    </StateMachine>
  </Tab>
</Project>"""
        path = tmp_path / "legacy.xml"
        path.write_text(xml_content, encoding="utf-8")

        # 1 回目の読込
        tabs, gd, *_ = project_from_xml(str(path))

        # 新形式で保存
        out_path = tmp_path / "upgraded.xml"
        project_to_xml(tabs, gd, str(out_path))

        # 2 回目の読込（冪等性確認）
        tabs2, *_ = project_from_xml(str(out_path))
        rfs = list(tabs2[0][1].role_functions.values())
        assert rfs[0].name == "Init"
        assert rfs[0].namespace == "Driver"


# ============================================================
# プロジェクト設定の round-trip
# ============================================================

class TestProjectSettings:

    def test_settings_roundtrip(self, tmp_path):
        sm = StateMachine()
        tabs = [("Main", sm)]
        gd = GlobalDefinitions()
        settings = {
            "project_name": "MyProj",
            "table_type": "array",
            "generation_style": "table_driven",
            "os_type": "non_rtos",
            "folder_structure": "by_layer",
            "include_dir_name": "include",
            "source_dir_name": "src",
            "common_dir_name": "common",
            "project_dir_name": "project",
            "generate_super_include": True,
            "super_include_file": "statable_all.h",
            "max_consecutive_pending_events": 16,
            "external_includes": [],
            "external_includes_in_super": True,
            "external_includes_in_role": True,
            "external_includes_in_transitions": False,
            "external_includes_in_common": False,
        }

        _, _, _, _, _, loaded_settings = _save_and_load(
            tmp_path, tabs, gd, settings=settings)

        for key, value in settings.items():
            assert loaded_settings[key] == value, f"{key}: {loaded_settings[key]} != {value}"

    def test_external_includes_list(self, tmp_path):
        sm = StateMachine()
        tabs = [("Main", sm)]
        gd = GlobalDefinitions()
        settings = {
            "project_name": "P",
            "external_includes": ["stdio.h", "stdint.h"],
        }

        _, _, _, _, _, loaded = _save_and_load(
            tmp_path, tabs, gd, settings=settings)
        assert loaded["external_includes"] == ["stdio.h", "stdint.h"]


# ============================================================
# グローバル定義の round-trip
# ============================================================

class TestGlobalDefinitions:

    def test_variables_roundtrip(self, tmp_path):
        sm = StateMachine()
        gd = GlobalDefinitions()
        gd.variables.append(SystemVariable(
            name="counter", type="uint32_t",
            description="カウンタ", title="カウンタ"))
        gd.variables.append(SystemVariable(
            name="rx_data", type="uint8_t",
            default_value="0", group="System",
            description="RX データ", title="RX"))

        _, loaded_gd, *_ = _save_and_load(tmp_path, [("Main", sm)], gd)
        names = {v.name for v in loaded_gd.variables if v.group != "Timer"}
        assert "counter" in names
        assert "rx_data" in names

    def test_flags_roundtrip(self, tmp_path):
        sm = StateMachine()
        gd = GlobalDefinitions()
        gd.flags.append(EventFlag(
            name="EVT_INIT", min_value=0, max_value=1,
            description="初期化", title="初期化"))

        _, loaded_gd, *_ = _save_and_load(tmp_path, [("Main", sm)], gd)
        assert len(loaded_gd.flags) == 1
        assert loaded_gd.flags[0].name == "EVT_INIT"

    def test_interrupt_with_used_roles(self, tmp_path):
        sm = StateMachine()
        gd = GlobalDefinitions()
        gd.interrupts.append(InterruptHandlerDef(
            name="TIMER0",
            description="タイマ割り込み",
            actions=[InterruptAction(action="ctx->counter++")],
            used_role_functions=["Application.HandleTick"],
            used_variables=["counter"],
            title="タイマ",
        ))

        _, loaded_gd, *_ = _save_and_load(tmp_path, [("Main", sm)], gd)
        assert len(loaded_gd.interrupts) == 1
        intr = loaded_gd.interrupts[0]
        assert intr.name == "TIMER0"
        assert "Application.HandleTick" in intr.used_role_functions
        assert "counter" in intr.used_variables


# ============================================================
# 複数タブの round-trip
# ============================================================

class TestMultipleTabs:

    def test_three_layers(self, tmp_path):
        """3 層（Driver / Middleware / Application）"""
        tabs = []
        for name in ["Driver", "Middleware", "Application"]:
            sm = StateMachine()
            sm.layer_name = name
            sm.add_state(State(name="Idle"))
            sm.add_event(Event(name="START"))
            sm.add_state(State(name="Active"))
            sm.add_transition(Transition(
                source="Idle", event="START", target="Active"))
            tabs.append((name, sm))

        loaded_tabs, *_ = _save_and_load(tmp_path, tabs, GlobalDefinitions())

        assert len(loaded_tabs) == 3
        names = [n for n, _ in loaded_tabs]
        assert names == ["Driver", "Middleware", "Application"]

    def test_tab_layer_name_preserved(self, tmp_path):
        sm = StateMachine()
        sm.layer_name = "Driver"
        sm.layer_priority = 1
        sm.layer_description = "ドライバ層"
        tabs = [("Driver", sm)]

        loaded_tabs, *_ = _save_and_load(tmp_path, tabs, GlobalDefinitions())
        sm2 = loaded_tabs[0][1]
        assert sm2.layer_name == "Driver"
        assert sm2.layer_priority == 1
        assert sm2.layer_description == "ドライバ層"


# ============================================================
# 遷移のプリ/エルスアクション round-trip
# ============================================================

class TestTransitionActions:

    def test_pre_actions_list_roundtrip(self, tmp_path):
        sm = StateMachine()
        sm.add_state(State(name="A"))
        sm.add_state(State(name="B"))
        sm.add_event(Event(name="GO"))
        sm.add_transition(Transition(
            source="A", event="GO", target="B",
            pre_actions=["Driver.Init", "Driver.Check"],
        ))
        tabs = [("Main", sm)]

        loaded_tabs, *_ = _save_and_load(tmp_path, tabs, GlobalDefinitions())
        trans = loaded_tabs[0][1].transitions[0]
        assert trans.pre_actions == ["Driver.Init", "Driver.Check"]

    def test_else_actions_roundtrip(self, tmp_path):
        sm = StateMachine()
        sm.add_state(State(name="A"))
        sm.add_state(State(name="B"))
        sm.add_event(Event(name="GO"))
        sm.add_transition(Transition(
            source="A", event="GO", target="B",
            else_target="B",
            else_actions=["Log.Error"],
        ))
        tabs = [("Main", sm)]

        loaded_tabs, *_ = _save_and_load(tmp_path, tabs, GlobalDefinitions())
        trans = loaded_tabs[0][1].transitions[0]
        assert trans.else_actions == ["Log.Error"]
        assert trans.else_target == "B"

    def test_has_else_false(self, tmp_path):
        sm = StateMachine()
        sm.add_state(State(name="A"))
        sm.add_state(State(name="B"))
        sm.add_event(Event(name="GO"))
        sm.add_transition(Transition(
            source="A", event="GO", target="B", has_else=False))
        tabs = [("Main", sm)]

        loaded_tabs, *_ = _save_and_load(tmp_path, tabs, GlobalDefinitions())
        assert loaded_tabs[0][1].transitions[0].has_else is False