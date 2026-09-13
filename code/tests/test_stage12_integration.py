# tests/test_stage12_integration.py
"""
Stage 1 + Stage 2 包括検証テスト（1 ファイル完結版）

Stage 1: データモデル層
  - model.RoleFunction.namespace / qualified_name / from_legacy_name
  - libcntrl.RoleFunction.namespace / to_dict / from_dict
  - RoleFunctionLibrary の namespace キー化
  - InterruptHandlerDef.used_role_functions / used_variables
  - xml_io の namespace / used_* 保存・復元
  - レガシー XML の自動移行

Stage 2: 生成器層
  - role_function_generator: NULL transition ガード
  - Transition_GetId: transition / table NULL チェック
  - namespace 優先ロジック（func.namespace > layer_name）
  - code_merger: RoleFunc_ / ISR_ 両マーカー対応

実行方法:
    cd C:\\Users\\user\\OneDrive\\ドキュメント\\GitHub\\StaTable\\code
    python -m tests.test_stage12_integration
    python tests/test_stage12_integration.py          (直接実行も可)
    python tests/test_stage12_integration.py --dump   (成果物ダンプ付き)

Exit code: 0 = 全合格, 1 = 失敗あり
"""

import sys
import os
import re
import tempfile
import traceback
from typing import Callable, List, Tuple, Optional

# ============================================================
# パス設定
# ============================================================
_THIS_DIR    = os.path.dirname(os.path.abspath(__file__))
_CODE_DIR    = os.path.dirname(_THIS_DIR)
_CODEGEN_DIR = os.path.join(_CODE_DIR, 'codegen')
_GUI_DIR     = os.path.join(_CODE_DIR, 'statable_gui')

for _p in (_CODEGEN_DIR, _CODE_DIR, _GUI_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ============================================================
# 依存モジュール
# ============================================================
from statable.model import (
    State, Event, Transition, RoleFunction,
)
from statable.state_machine import StateMachine
from statable.global_defs import (
    GlobalDefinitions, InterruptHandlerDef, InterruptAction,
)
from statable import xml_io

from role_function_generator import RoleFunctionGenerator, RoleFuncCallSite
from code_merger import CodeMerger


# libcntrl のインポート（パスバリエーション対応）
try:
    from libcntrl.role_function_library import (
        RoleFunctionLibrary, RoleFunction as LibRoleFunction,
    )
    _LIB_OK = True
    _LIB_ERR = ''
except ImportError as _e1:
    try:
        from statable_gui.libcntrl.role_function_library import (
            RoleFunctionLibrary, RoleFunction as LibRoleFunction,
        )
        _LIB_OK = True
        _LIB_ERR = ''
    except ImportError as _e2:
        _LIB_OK = False
        _LIB_ERR = f"{_e1} / {_e2}"
        RoleFunctionLibrary = None
        LibRoleFunction = None


# ============================================================
# レポーター
# ============================================================
class StageReporter:
    """テスト結果を 1 ページに集約するレポーター"""

    COL_OK    = "  [OK]"
    COL_NG    = "  [NG]"
    COL_SKIP  = "  [--]"

    def __init__(self):
        self.results: List[Tuple[str, str, bool, str]] = []
        self.sections: List[str] = []
        self._current_section: str = ''
        self._section_counts = {}

    # ---- セクション管理 ----
    def section(self, title: str):
        self._current_section = title
        self.sections.append(title)
        self._section_counts[title] = [0, 0]  # [pass, fail]
        bar = "=" * 72
        print(f"\n{bar}")
        print(f"  {title}")
        print(bar)

    # ---- チェック実行 ----
    def check(self, name: str, func: Callable):
        try:
            func()
            ok = True
            err = ''
            self._section_counts[self._current_section][0] += 1
        except AssertionError as e:
            ok = False
            err = str(e) or "AssertionError"
            self._section_counts[self._current_section][1] += 1
        except Exception as e:
            ok = False
            err = f"{type(e).__name__}: {e}"
            self._section_counts[self._current_section][1] += 1

        self.results.append(
            (self._current_section, name, ok, err)
        )
        mark = self.COL_OK if ok else self.COL_NG
        print(f"{mark}  {name}")
        if not ok:
            print(f"         └─ {err}")

    def skip(self, name: str, reason: str):
        self.results.append(
            (self._current_section, name, None, reason)  # type: ignore
        )
        self._section_counts[self._current_section][0] += 0
        print(f"{self.COL_SKIP}  {name}   ({reason})")

    # ---- サマリ ----
    def summary(self) -> bool:
        bar = "=" * 72
        print(f"\n{bar}")
        print("  サマリ")
        print(bar)

        total_pass = total_fail = total_skip = 0
        for sec in self.sections:
            p, f = self._section_counts[sec]
            s = sum(1 for r in self.results
                    if r[0] == sec and r[2] is None)
            total_pass += p
            total_fail += f
            total_skip += s
            mark = "✓" if f == 0 else "✗"
            print(f"  {mark}  {sec:<40}  pass={p:>3}  fail={f:>2}  skip={s:>2}")

        print("-" * 72)
        print(f"  合計: pass={total_pass}  fail={total_fail}  skip={total_skip}")
        print(bar)

        if total_fail == 0:
            print("\n  ★ 全テスト合格 ★  Stage 1 / Stage 2 は健全です。\n")
            return True
        else:
            print(f"\n  ⚠  {total_fail} 件の失敗があります。\n")
            return False


R = StageReporter()


# ============================================================
# ヘルパー
# ============================================================
def make_model_rf(name, namespace='', **kw):
    return RoleFunction(name=name, namespace=namespace, **kw)


def make_sm_with_layer(layer='Driver'):
    sm = StateMachine()
    sm.layer_name = layer
    sm.add_state(State(name='Idle'))
    sm.add_state(State(name='Active'))
    sm.add_event(Event(name='START'))
    sm.add_event(Event(name='STOP'))
    return sm


def make_gen_with_layer(layer='Driver'):
    g = RoleFunctionGenerator()
    g.set_layer(layer)
    return g


# ============================================================
# Section 1: Model Layer
# ============================================================
def section_model():
    R.section("1. Model Layer — statable.model.RoleFunction")

    def t_default_ns():
        rf = make_model_rf("Init")
        assert rf.namespace == "", f"expected '', got {rf.namespace!r}"

    def t_qualified_with_ns():
        rf = make_model_rf("Init", namespace="Driver")
        assert rf.qualified_name == "Driver.Init", rf.qualified_name

    def t_qualified_without_ns():
        rf = make_model_rf("Init")
        assert rf.qualified_name == "Init", rf.qualified_name

    def t_title_uses_qualified():
        rf = make_model_rf("Init", namespace="Driver")
        assert rf.title == "ロール関数: Driver.Init", rf.title

    def t_explicit_title_kept():
        rf = make_model_rf("Init", namespace="Driver", title="独自")
        assert rf.title == "独自", rf.title

    def t_legacy_with_layer():
        rf = RoleFunction.from_legacy_name(
            "Driver_Init", layer_names=["Driver", "Application"],
        )
        assert rf.namespace == "Driver", rf.namespace
        assert rf.name == "Init", rf.name

    def t_legacy_no_match():
        rf = RoleFunction.from_legacy_name(
            "Init", layer_names=["Driver"],
        )
        assert rf.namespace == "", rf.namespace
        assert rf.name == "Init", rf.name

    def t_legacy_empty():
        rf = RoleFunction.from_legacy_name("", layer_names=["Driver"])
        assert rf.name == "" and rf.namespace == ""

    def t_legacy_no_list():
        rf = RoleFunction.from_legacy_name("Driver_Init", layer_names=None)
        assert rf.namespace == "", rf.namespace
        assert rf.name == "Driver_Init", rf.name

    R.check("namespace デフォルト = ''", t_default_ns)
    R.check("qualified_name = 'Driver.Init'", t_qualified_with_ns)
    R.check("qualified_name (ns なし) = 'Init'", t_qualified_without_ns)
    R.check("title 自動生成 = 'ロール関数: Driver.Init'", t_title_uses_qualified)
    R.check("明示 title 保持", t_explicit_title_kept)
    R.check("from_legacy_name: 層プレフィックス分解", t_legacy_with_layer)
    R.check("from_legacy_name: 不一致時はそのまま", t_legacy_no_match)
    R.check("from_legacy_name: 空入力", t_legacy_empty)
    R.check("from_legacy_name: layer_names=None", t_legacy_no_list)


# ============================================================
# Section 2: Library Layer
# ============================================================
def section_library():
    R.section("2. Library Layer — libcntrl.role_function_library")

    if not _LIB_OK:
        R.skip("libcntrl インポート", _LIB_ERR)
        return

    def t_default_ns():
        rf = LibRoleFunction(name="Init")
        assert rf.namespace == "", rf.namespace

    def t_qualified():
        rf = LibRoleFunction(name="Init", namespace="Driver")
        assert rf.qualified_name == "Driver.Init"

    def t_to_dict():
        rf = LibRoleFunction(name="Init", namespace="Driver")
        d = rf.to_dict()
        assert d.get('namespace') == "Driver", d
        assert d.get('name') == "Init", d

    def t_from_dict():
        rf = LibRoleFunction.from_dict({
            'name': "Init", 'namespace': "Driver",
        })
        assert rf.namespace == "Driver", rf.namespace
        assert rf.name == "Init", rf.name

    def t_from_dict_legacy():
        rf = LibRoleFunction.from_dict({'name': "Init"})
        assert rf.namespace == "", rf.namespace

    def t_lib_add_get_qname():
        lib = RoleFunctionLibrary()
        lib.add(LibRoleFunction(name="Init", namespace="Driver"))
        rf = lib.get("Driver.Init")
        assert rf is not None
        assert rf.namespace == "Driver"

    def t_lib_add_get_bare():
        lib = RoleFunctionLibrary()
        lib.add(LibRoleFunction(name="Init", namespace="Driver"))
        rf = lib.get("Init")
        assert rf is not None
        assert rf.namespace == "Driver"

    def t_lib_ns_collision_ok():
        lib = RoleFunctionLibrary()
        lib.add(LibRoleFunction(name="Init", namespace="Driver"))
        lib.add(LibRoleFunction(name="Init", namespace="Application"))
        assert len(lib.list_all()) == 2

    def t_lib_dup_raises():
        lib = RoleFunctionLibrary()
        lib.add(LibRoleFunction(name="Init", namespace="Driver"))
        try:
            lib.add(LibRoleFunction(name="Init", namespace="Driver"))
        except ValueError:
            return
        raise AssertionError("重複追加で ValueError が発生しなかった")

    def t_lib_dict_roundtrip():
        lib = RoleFunctionLibrary()
        lib.add(LibRoleFunction(name="Init", namespace="Driver",
                                description="初期化"))
        lib2 = RoleFunctionLibrary.from_dict(lib.to_dict())
        rf = lib2.get("Driver.Init")
        assert rf is not None
        assert rf.description == "初期化", rf.description

    R.check("namespace デフォルト = ''", t_default_ns)
    R.check("qualified_name = 'Driver.Init'", t_qualified)
    R.check("to_dict に namespace 含む", t_to_dict)
    R.check("from_dict で namespace 復元", t_from_dict)
    R.check("from_dict (旧形式, namespace なし)", t_from_dict_legacy)
    R.check("Library.get('Driver.Init')", t_lib_add_get_qname)
    R.check("Library.get('Init') = bare name 検索", t_lib_add_get_bare)
    R.check("Library: namespace 違いは共存可", t_lib_ns_collision_ok)
    R.check("Library: 重複で ValueError", t_lib_dup_raises)
    R.check("Library: to_dict / from_dict 往復", t_lib_dict_roundtrip)


# ============================================================
# Section 3: GlobalDefs Layer
# ============================================================
def section_global_defs():
    R.section("3. GlobalDefs Layer — InterruptHandlerDef.used_*")

    def t_default_used_rfs():
        h = InterruptHandlerDef(name="TIMER0")
        assert h.used_role_functions == [], h.used_role_functions

    def t_default_used_vars():
        h = InterruptHandlerDef(name="TIMER0")
        assert h.used_variables == [], h.used_variables

    def t_explicit_used():
        h = InterruptHandlerDef(
            name="TIMER0",
            used_role_functions=["Driver.Init"],
            used_variables=["counter"],
        )
        assert h.used_role_functions == ["Driver.Init"]
        assert h.used_variables == ["counter"]

    R.check("used_role_functions デフォルト = []", t_default_used_rfs)
    R.check("used_variables デフォルト = []", t_default_used_vars)
    R.check("明示設定の保持", t_explicit_used)


# ============================================================
# Section 4: XML Round-trip
# ============================================================
def section_xml_roundtrip():
    R.section("4. XML Round-trip — xml_io 保存/復元")

    def t_ns_saved():
        sm = make_sm_with_layer("Driver")
        sm.add_role_function(make_model_rf("Init", namespace="Driver"))
        sm.add_role_function(make_model_rf("Shared", namespace=""))
        elem = xml_io.state_machine_to_element(sm)
        roles = elem.find("RoleFunctions")
        items = roles.findall("RoleFunction")
        by_name = {r.get("name"): r for r in items}
        assert by_name["Init"].get("namespace") == "Driver"
        assert by_name["Shared"].get("namespace") == ""

    def t_ns_restored():
        sm = make_sm_with_layer("Driver")
        sm.add_role_function(make_model_rf("Init", namespace="Driver"))
        elem = xml_io.state_machine_to_element(sm)
        sm2 = xml_io.state_machine_from_element(elem)
        rf = sm2.role_functions.get("Init")
        assert rf is not None
        assert rf.namespace == "Driver", rf.namespace

    def t_used_rfs_saved():
        gd = GlobalDefinitions()
        gd.interrupts.append(InterruptHandlerDef(
            name="TIMER0",
            actions=[InterruptAction(condition="", action="Driver.Init")],
            used_role_functions=["Driver.Init", "App.Tick"],
            used_variables=["counter"],
        ))
        elem = xml_io.global_defs_to_element(gd)
        child = elem.find("Interrupts").find("Interrupt")
        refs = [r.get("ref") for r in child.findall("UsedRoleFunction")]
        vars_ = [v.get("name") for v in child.findall("UsedVariable")]
        assert refs == ["Driver.Init", "App.Tick"], refs
        assert vars_ == ["counter"], vars_

    def t_used_rfs_restored():
        gd = GlobalDefinitions()
        gd.interrupts.append(InterruptHandlerDef(
            name="TIMER0",
            used_role_functions=["Driver.Init"],
            used_variables=["counter"],
        ))
        elem = xml_io.global_defs_to_element(gd)
        gd2 = xml_io.global_defs_from_element(elem)
        h = gd2.interrupts[0]
        assert h.used_role_functions == ["Driver.Init"], h.used_role_functions
        assert h.used_variables == ["counter"], h.used_variables

    def t_used_empty_no_children():
        gd = GlobalDefinitions()
        gd.interrupts.append(InterruptHandlerDef(name="TIMER0"))
        elem = xml_io.global_defs_to_element(gd)
        child = elem.find("Interrupts").find("Interrupt")
        assert child.findall("UsedRoleFunction") == []
        assert child.findall("UsedVariable") == []

    def t_full_project_roundtrip():
        sm = make_sm_with_layer("Driver")
        sm.add_role_function(make_model_rf("Init", namespace="Driver"))

        gd = GlobalDefinitions()
        gd.interrupts.append(InterruptHandlerDef(
            name="TIMER0",
            used_role_functions=["Driver.Init"],
        ))

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "project.xml")
            xml_io.project_to_xml([("Driver", sm)], gd, path)
            (tabs, gd2, rl, cl, ll, ps) = xml_io.project_from_xml(path)

        assert len(tabs) == 1
        _, sm2 = tabs[0]
        rf = sm2.role_functions.get("Init")
        assert rf is not None and rf.namespace == "Driver"
        assert gd2.interrupts[0].used_role_functions == ["Driver.Init"]

    R.check("RoleFunction の namespace 属性が保存される", t_ns_saved)
    R.check("RoleFunction の namespace が復元される", t_ns_restored)
    R.check("InterruptHandlerDef の used_* が保存される", t_used_rfs_saved)
    R.check("InterruptHandlerDef の used_* が復元される", t_used_rfs_restored)
    R.check("空 used_* では子要素なし", t_used_empty_no_children)
    R.check("プロジェクト全体 round-trip", t_full_project_roundtrip)


# ============================================================
# Section 5: Legacy Migration
# ============================================================
def section_legacy_migration():
    R.section("5. Legacy Migration — 旧形式 XML の自動移行")

    def t_legacy_migrated():
        """旧 name='Driver_Init' → namespace='Driver', name='Init'"""
        sm = StateMachine()
        sm.layer_name = "Driver"
        sm.add_state(State(name="Idle"))
        sm.add_event(Event(name="START"))
        sm.add_role_function(make_model_rf("Driver_Init", namespace=""))

        elem = xml_io.state_machine_to_element(sm)
        sm2 = xml_io.state_machine_from_element(elem)
        assert "Init" in sm2.role_functions, list(sm2.role_functions)
        rf = sm2.role_functions["Init"]
        assert rf.namespace == "Driver", rf.namespace

    def t_no_layer_no_migration():
        sm = StateMachine()
        sm.layer_name = ""
        sm.add_state(State(name="Idle"))
        sm.add_event(Event(name="START"))
        sm.add_role_function(make_model_rf("Driver_Init", namespace=""))

        elem = xml_io.state_machine_to_element(sm)
        sm2 = xml_io.state_machine_from_element(elem)
        assert "Driver_Init" in sm2.role_functions
        rf = sm2.role_functions["Driver_Init"]
        assert rf.namespace == "", rf.namespace

    def t_different_prefix_no_migration():
        sm = StateMachine()
        sm.layer_name = "Application"
        sm.add_state(State(name="Idle"))
        sm.add_event(Event(name="START"))
        sm.add_role_function(make_model_rf("Driver_Init", namespace=""))

        elem = xml_io.state_machine_to_element(sm)
        sm2 = xml_io.state_machine_from_element(elem)
        assert "Driver_Init" in sm2.role_functions
        rf = sm2.role_functions["Driver_Init"]
        assert rf.namespace == "", rf.namespace

    R.check("旧 'Driver_Init' → namespace='Driver' / name='Init'", t_legacy_migrated)
    R.check("layer_name 空なら移行しない", t_no_layer_no_migration)
    R.check("別 layer のプレフィックスなら移行しない", t_different_prefix_no_migration)


# ============================================================
# Section 6: NULL Guard
# ============================================================
def section_null_guard():
    R.section("6. NULL Guard — role_function_generator")

    def t_null_guard_header():
        g = make_gen_with_layer("Driver")
        impl = g.generate_implementation(
            make_model_rf("Init"), include_transition_id=False,
        )
        assert "transition NULL ガード" in impl
        assert "ISR からの呼び出し対応" in impl

    def t_from_state_default():
        g = make_gen_with_layer("Driver")
        impl = g.generate_implementation(
            make_model_rf("Init"), include_transition_id=False,
        )
        assert "STATE_Driver_t from_state = STATE_Driver_MAX;" in impl

    def t_event_default():
        g = make_gen_with_layer("Driver")
        impl = g.generate_implementation(
            make_model_rf("Init"), include_transition_id=False,
        )
        assert "EVENT_Driver_t event = EVENT_Driver_NONE;" in impl

    def t_null_check():
        g = make_gen_with_layer("Driver")
        impl = g.generate_implementation(
            make_model_rf("Init"), include_transition_id=False,
        )
        assert "if (transition != NULL) {" in impl

    def t_assignments():
        g = make_gen_with_layer("Driver")
        impl = g.generate_implementation(
            make_model_rf("Init"), include_transition_id=False,
        )
        assert "from_state = transition->from_state;" in impl
        assert "event = transition->event;" in impl

    def t_void_suppress():
        g = make_gen_with_layer("Driver")
        impl = g.generate_implementation(
            make_model_rf("Init"), include_transition_id=False,
        )
        assert "(void)from_state;" in impl
        assert "(void)event;" in impl

    def t_no_layer():
        g = RoleFunctionGenerator()  # no layer
        impl = g.generate_implementation(
            make_model_rf("Init"), include_transition_id=False,
        )
        assert "STATE_t from_state = STATE_MAX;" in impl
        assert "EVENT_t event = EVENT_NONE;" in impl

    def t_no_void_transition():
        g = make_gen_with_layer("Driver")
        impl = g.generate_implementation(
            make_model_rf("Init"), include_transition_id=False,
        )
        # (void)transition は NULL ガードで参照されるので不要
        assert "(void)transition;" not in impl

    R.check("NULL ガードセクションのヘッダコメント", t_null_guard_header)
    R.check("from_state デフォルト値 = STATE_MAX", t_from_state_default)
    R.check("event デフォルト値 = EVENT_NONE", t_event_default)
    R.check("if (transition != NULL) チェック", t_null_check)
    R.check("transition メンバー代入", t_assignments)
    R.check("(void) 警告抑制", t_void_suppress)
    R.check("層なし版 NULL ガード", t_no_layer)
    R.check("(void)transition; が出力されない", t_no_void_transition)


# ============================================================
# Section 7: Transition_GetId
# ============================================================
def section_transition_getid():
    R.section("7. Transition_GetId — NULL チェック")

    def t_prototype():
        g = make_gen_with_layer("Driver")
        code = g.generate_transition_id_prototype()
        assert "static uint16_t Transition_GetId(" in code
        assert "const TransitionContext_Driver_t *transition," in code
        assert "const RoleFuncCallSiteEntry_Driver_t *table," in code
        assert "uint16_t table_size);" in code

    def t_null_check_both():
        g = make_gen_with_layer("Driver")
        code = g.generate_transition_id_function()
        assert "if (transition == NULL || table == NULL)" in code

    def t_returns_none():
        g = make_gen_with_layer("Driver")
        code = g.generate_transition_id_function()
        assert "return TRANSITION_ID_NONE;" in code

    def t_linear_search():
        g = make_gen_with_layer("Driver")
        code = g.generate_transition_id_function()
        assert "for (i = 0; i < table_size; i++)" in code
        assert "table[i].from_state == transition->from_state" in code
        assert "table[i].event      == transition->event" in code

    def t_no_layer():
        g = RoleFunctionGenerator()
        code = g.generate_transition_id_function()
        assert "const TransitionContext_t *transition," in code
        assert "const RoleFuncCallSiteEntry_t *table," in code

    def t_none_define():
        g = make_gen_with_layer("Driver")
        code = g.generate_none_define()
        assert "#define TRANSITION_ID_NONE" in code
        assert "((uint16_t)0xFFFF)" in code

    R.check("プロトタイプ宣言", t_prototype)
    R.check("transition/table 両方 NULL チェック", t_null_check_both)
    R.check("NULL 時に TRANSITION_ID_NONE を返す", t_returns_none)
    R.check("線形探索のロジック", t_linear_search)
    R.check("層なし版の型名", t_no_layer)
    R.check("TRANSITION_ID_NONE 定義", t_none_define)


# ============================================================
# Section 8: namespace 優先ロジック
# ============================================================
def section_namespace_priority():
    R.section("8. namespace 優先ロジック — role_function_generator")

    def t_func_name_with_ns():
        g = make_gen_with_layer("Application")
        name = g._generate_function_name(
            make_model_rf("Init", namespace="Driver")
        )
        # func.namespace が layer_name より優先
        assert name == "RoleFunc_Driver_Init", name

    def t_func_name_fallback_to_layer():
        g = make_gen_with_layer("Application")
        name = g._generate_function_name(make_model_rf("Init"))
        assert name == "RoleFunc_Application_Init", name

    def t_func_name_no_layer():
        g = RoleFunctionGenerator()
        name = g._generate_function_name(make_model_rf("Init"))
        assert name == "RoleFunc_Init", name

    def t_marker_with_ns():
        g = make_gen_with_layer("Application")
        marker = g._get_marker_name(
            make_model_rf("Init", namespace="Driver")
        )
        assert marker == "Driver_Init", marker

    def t_marker_fallback():
        g = make_gen_with_layer("Application")
        marker = g._get_marker_name(make_model_rf("Init"))
        assert marker == "Application_Init", marker

    def t_dedupe_by_ns_name():
        g = RoleFunctionGenerator()
        funcs = [
            make_model_rf("Init", namespace="Driver"),
            make_model_rf("Init", namespace="Application"),
            make_model_rf("Init", namespace="Driver"),  # 重複
        ]
        result = g._dedupe_by_name(funcs)
        assert len(result) == 2, len(result)

    def t_marker_matches_code_merger():
        """生成マーカーが CodeMerger の抽出パターンと一致"""
        g = make_gen_with_layer("Driver")
        impl = g.generate_implementation(
            make_model_rf("Init", namespace="Driver"),
            include_transition_id=False,
        )
        m = re.search(r'RoleFunc_(\w+)\s*\(', impl)
        assert m is not None
        extracted = m.group(1)
        assert extracted == "Driver_Init", extracted
        assert f"START:{extracted}" in impl
        assert f"END:{extracted}" in impl

    R.check("func.namespace > layer_name", t_func_name_with_ns)
    R.check("layer_name にフォールバック", t_func_name_fallback_to_layer)
    R.check("両方空なら RoleFunc_Init", t_func_name_no_layer)
    R.check("マーカー名も namespace 優先", t_marker_with_ns)
    R.check("マーカー名 layer_name fallback", t_marker_fallback)
    R.check("dedupe は namespace.name で一意化", t_dedupe_by_ns_name)
    R.check("生成マーカーが CodeMerger と整合", t_marker_matches_code_merger)


# ============================================================
# Section 9: Code Merger ISR Support
# ============================================================
def section_merger_isr():
    R.section("9. Code Merger — ISR マーカー対応")

    def t_extract_isr():
        m = CodeMerger()
        content = (
            "void ISR_TIMER0(void)\n"
            "{\n"
            "    /* [[STABLE_USER_CODE_START:TIMER0]] */\n"
            "    counter++;\n"
            "    /* [[STABLE_USER_CODE_END:TIMER0]] */\n"
            "}\n"
        )
        code = m.extract_func_user_code(content, "TIMER0")
        assert "counter++" in code, repr(code)

    def t_extract_all_includes_isr():
        m = CodeMerger()
        content = (
            "int RoleFunc_Driver_Init(...)\n"
            "{\n"
            "    /* [[STABLE_USER_CODE_START:Driver_Init]] */\n"
            "    init_body();\n"
            "    /* [[STABLE_USER_CODE_END:Driver_Init]] */\n"
            "}\n"
            "void ISR_TIMER0(void)\n"
            "{\n"
            "    /* [[STABLE_USER_CODE_START:TIMER0]] */\n"
            "    isr_body();\n"
            "    /* [[STABLE_USER_CODE_END:TIMER0]] */\n"
            "}\n"
        )
        codes = m.extract_all_func_user_codes(content)
        assert "Driver_Init" in codes, codes.keys()
        assert "TIMER0" in codes, codes.keys()
        assert "init_body" in codes["Driver_Init"]
        assert "isr_body" in codes["TIMER0"]

    def t_extract_multiple_isrs():
        m = CodeMerger()
        content = (
            "void ISR_TIMER0(void) {\n"
            "    /* [[STABLE_USER_CODE_START:TIMER0]] */\n"
            "    t0_body();\n"
            "    /* [[STABLE_USER_CODE_END:TIMER0]] */\n"
            "}\n"
            "void ISR_UARTRX(void) {\n"
            "    /* [[STABLE_USER_CODE_START:UARTRX]] */\n"
            "    rx_body();\n"
            "    /* [[STABLE_USER_CODE_END:UARTRX]] */\n"
            "}\n"
        )
        codes = m.extract_all_func_user_codes(content)
        assert len(codes) == 2, len(codes)
        assert "TIMER0" in codes
        assert "UARTRX" in codes

    def t_inject_isr():
        m = CodeMerger()
        generated = (
            "void ISR_TIMER0(void)\n"
            "{\n"
            "    /* [[STABLE_USER_CODE_START:TIMER0]] */\n"
            "    /* ユーザー実装コードをここに記述 */\n"
            "    /* [[STABLE_USER_CODE_END:TIMER0]] */\n"
            "}\n"
        )
        result = m.inject_func_user_code(
            generated, "TIMER0", "my_code();"
        )
        assert "my_code();" in result
        assert "/* ユーザー実装コードをここに記述 */" not in result

    def t_merge_preserves_isr():
        m = CodeMerger()
        generated = (
            "#include \"x.h\"\n"
            "void ISR_TIMER0(void)\n"
            "{\n"
            "    /* [[STABLE_USER_CODE_START:TIMER0]] */\n"
            "    /* ユーザー実装コードをここに記述 */\n"
            "    /* [[STABLE_USER_CODE_END:TIMER0]] */\n"
            "}\n"
        )
        existing = (
            "#include \"x.h\"\n"
            "void ISR_TIMER0(void)\n"
            "{\n"
            "    /* [[STABLE_USER_CODE_START:TIMER0]] */\n"
            "    counter++;\n"
            "    /* [[STABLE_USER_CODE_END:TIMER0]] */\n"
            "}\n"
        )
        merged = m.merge_file(generated, existing)
        assert "counter++;" in merged
        assert "/* ユーザー実装コードをここに記述 */" not in merged

    def t_merge_rolefunc_and_isr():
        m = CodeMerger()
        gen_content = (
            "int RoleFunc_Driver_Init(...)\n"
            "{\n"
            "    /* [[STABLE_USER_CODE_START:Driver_Init]] */\n"
            "    /* ユーザー */\n"
            "    /* [[STABLE_USER_CODE_END:Driver_Init]] */\n"
            "}\n"
            "void ISR_TIMER0(void)\n"
            "{\n"
            "    /* [[STABLE_USER_CODE_START:TIMER0]] */\n"
            "    /* ユーザー */\n"
            "    /* [[STABLE_USER_CODE_END:TIMER0]] */\n"
            "}\n"
        )
        existing = (
            "int RoleFunc_Driver_Init(...)\n"
            "{\n"
            "    /* [[STABLE_USER_CODE_START:Driver_Init]] */\n"
            "    init_body();\n"
            "    /* [[STABLE_USER_CODE_END:Driver_Init]] */\n"
            "}\n"
            "void ISR_TIMER0(void)\n"
            "{\n"
            "    /* [[STABLE_USER_CODE_START:TIMER0]] */\n"
            "    isr_body();\n"
            "    /* [[STABLE_USER_CODE_END:TIMER0]] */\n"
            "}\n"
        )
        merged = m.merge_file(gen_content, existing)
        assert "init_body();" in merged
        assert "isr_body();" in merged

    def t_summary_counts_isr():
        m = CodeMerger()
        content = (
            "int RoleFunc_Driver_Init(...)\n"
            "{\n"
            "    /* [[STABLE_USER_CODE_START:Driver_Init]] */\n"
            "    x();\n"
            "    /* [[STABLE_USER_CODE_END:Driver_Init]] */\n"
            "}\n"
            "void ISR_TIMER0(void)\n"
            "{\n"
            "    /* [[STABLE_USER_CODE_START:TIMER0]] */\n"
            "    y();\n"
            "    /* [[STABLE_USER_CODE_END:TIMER0]] */\n"
            "}\n"
        )
        s = m.get_user_code_summary(content)
        assert s['func_user_codes'] == 2, s

    R.check("ISR マーカー抽出", t_extract_isr)
    R.check("extract_all に ISR 含む", t_extract_all_includes_isr)
    R.check("複数 ISR の同時抽出", t_extract_multiple_isrs)
    R.check("ISR マーカー注入", t_inject_isr)
    R.check("merge_file で ISR ユーザーコード保持", t_merge_preserves_isr)
    R.check("RoleFunc + ISR 共存マージ", t_merge_rolefunc_and_isr)
    R.check("get_user_code_summary に ISR カウント", t_summary_counts_isr)


# ============================================================
# Section 10: End-to-End Integration
# ============================================================
def section_e2e():
    R.section("10. End-to-End Integration")

    def t_model_to_generation_to_merge():
        """model → generator → merger の一気通貫"""
        # 1. モデル構築
        sm = make_sm_with_layer("Driver")
        sm.add_transition(Transition(
            source="Idle", event="START", target="Active",
            condition="Driver.StartOk",
        ))
        sm.add_role_function(make_model_rf(
            "StartOk", namespace="Driver",
            description="開始条件チェック",
        ))

        # 2. 生成
        g = make_gen_with_layer("Driver")
        impl = g.generate_all_implementations(
            list(sm.role_functions.values()),
            state_machine=sm,
        )
        assert "RoleFunc_Driver_StartOk" in impl
        assert "if (transition != NULL)" in impl

        # 3. ユーザー編集
        edited = impl.replace(
            "    /* ユーザー実装コードをここに記述 */",
            "    ret = 1;",
        )
        # 4. 再生成 → マージ
        regen = g.generate_all_implementations(
            list(sm.role_functions.values()),
            state_machine=sm,
        )
        merged = CodeMerger().merge_file(regen, edited)
        assert "ret = 1;" in merged

    def t_xml_to_generation():
        """model → XML → 復元 → 生成"""
        sm = make_sm_with_layer("Driver")
        sm.add_role_function(make_model_rf(
            "Init", namespace="Driver",
        ))

        # XML round-trip
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "p.xml")
            xml_io.project_to_xml([("Driver", sm)], GlobalDefinitions(), path)
            tabs, _, _, _, _, _ = xml_io.project_from_xml(path)

        _, sm2 = tabs[0]
        g = make_gen_with_layer("Driver")
        impl = g.generate_all_implementations(
            list(sm2.role_functions.values()),
        )
        assert "RoleFunc_Driver_Init" in impl
        assert "[[STABLE_USER_CODE_START:Driver_Init]]" in impl

    def t_library_merge_with_sm():
        """SM の role_functions と Library のロール関数を統合"""
        sm = make_sm_with_layer("Driver")
        sm.add_role_function(make_model_rf("Init", namespace="Driver"))

        # Library 側に別の関数
        if not _LIB_OK:
            return  # スキップ
        lib = RoleFunctionLibrary()
        lib.add(LibRoleFunction(name="HandleTick", namespace="Application"))

        # SM 側 + Library 側を統合（c_code_generator のロジックを再現）
        funcs = dict(sm.role_functions)
        for rf in lib.list_all():
            name = getattr(rf, 'name', None)
            if name and name not in funcs:
                funcs[name] = rf

        all_funcs = list(funcs.values())
        g = make_gen_with_layer("Driver")
        impl = g.generate_all_implementations(all_funcs)
        assert "RoleFunc_Driver_Init" in impl
        assert "RoleFunc_Application_HandleTick" in impl

    R.check("model → generator → merger 一気通貫", t_model_to_generation_to_merge)
    R.check("model → XML → 復元 → 生成", t_xml_to_generation)
    R.check("SM + Library 統合で両方の関数を生成", t_library_merge_with_sm)


# ============================================================
# ダンプ（--dump オプション）
# ============================================================
def dump_artifacts():
    out_dir = os.path.join(_THIS_DIR, "_generated", "stage12")
    os.makedirs(out_dir, exist_ok=True)
    print(f"\n[ダンプ] {out_dir}")

    # 1. Stage 1: XML 保存例
    sm = make_sm_with_layer("Driver")
    sm.add_role_function(make_model_rf("Init", namespace="Driver"))
    sm.add_role_function(make_model_rf("Shared"))

    gd = GlobalDefinitions()
    gd.interrupts.append(InterruptHandlerDef(
        name="TIMER0",
        actions=[InterruptAction(condition="", action="Driver.Init")],
        used_role_functions=["Driver.Init"],
        used_variables=["counter"],
    ))
    xml_path = os.path.join(out_dir, "stage1_project.xml")
    xml_io.project_to_xml([("Driver", sm)], gd, xml_path)
    print(f"  - {os.path.basename(xml_path)}")

    # 2. Stage 2: ロール関数実装
    sm2 = make_sm_with_layer("Driver")
    sm2.add_transition(Transition(
        source="Idle", event="START", target="Active",
        condition="Driver.StartOk",
    ))
    sm2.add_role_function(make_model_rf(
        "StartOk", namespace="Driver", description="開始条件チェック",
    ))

    g = make_gen_with_layer("Driver")
    impl = g.generate_all_implementations(
        list(sm2.role_functions.values()), state_machine=sm2,
    )
    impl_path = os.path.join(out_dir, "stage2_role_functions.c")
    with open(impl_path, 'w', encoding='utf-8') as f:
        f.write(impl)
    print(f"  - {os.path.basename(impl_path)}")

    # 3. Stage 2: ISR マージ例
    isr_sample = (
        "void ISR_TIMER0(void)\n"
        "{\n"
        "    /* [[STABLE_USER_CODE_START:TIMER0]] */\n"
        "    counter++;\n"
        "    /* [[STABLE_USER_CODE_END:TIMER0]] */\n"
        "}\n"
    )
    m = CodeMerger()
    extracted = m.extract_all_func_user_codes(isr_sample)
    dump_path = os.path.join(out_dir, "stage2_isr_extracted.txt")
    with open(dump_path, 'w', encoding='utf-8') as f:
        for k, v in extracted.items():
            f.write(f"--- {k} ---\n{v}\n")
    print(f"  - {os.path.basename(dump_path)}")


# ============================================================
# メイン
# ============================================================
def main():
    print("\n" + "=" * 72)
    print("  Stage 1 + Stage 2 包括検証テスト")
    print("=" * 72)
    print(f"  Python:  {sys.version.split()[0]}")
    print(f"  libcntrl: {'OK' if _LIB_OK else 'NG (' + _LIB_ERR + ')'}")

    section_model()
    section_library()
    section_global_defs()
    section_xml_roundtrip()
    section_legacy_migration()
    section_null_guard()
    section_transition_getid()
    section_namespace_priority()
    section_merger_isr()
    section_e2e()

    ok = R.summary()

    if '--dump' in sys.argv:
        try:
            dump_artifacts()
        except Exception as e:
            print(f"\n[ダンプ失敗] {e}")
            traceback.print_exc()

    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())