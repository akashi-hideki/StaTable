# tests/test_c_code_generator.py
"""
c_code_generator.CCodeGenerator のユニットテスト

【目的】
  コード生成統括クラスの回帰防止:
    - 単層 generate_all
    - 複数層 generate_all_layers（by_layer / by_type / flat）
    - by_layer の層サフィックス付与（v1.6 §9.7 #91）
    - statable_types_common.h の生成（v1.6 §9.8 #92）
    - include guard / include の層別展開
    - 出力パス解決
    - 保存（マージなし / マージあり）

【対象】
  codegen/c_code_generator.py
"""
import os
import pytest
from pathlib import Path

from statable.model import State, Event, Transition
from statable.state_machine import StateMachine
from statable.global_defs import (
    GlobalDefinitions, SystemVariable, EventFlag,
)
from codegen.c_code_generator import CCodeGenerator
from codegen.config import CodeGenerationConfig


# ============================================================
# ヘルパー
# ============================================================

def _make_sm(layer_name="Driver", with_initial=True):
    sm = StateMachine()
    sm.layer_name = layer_name
    sm.layer_priority = 1
    sm.add_state(State(name="Idle"))
    sm.add_state(State(name="Active"))
    sm.add_event(Event(name="START"))
    sm.add_transition(Transition(
        source="Idle", event="START", target="Active",
        title="起動",
    ))
    if with_initial:
        sm.set_initial("Idle")
    return sm


def _make_gd():
    gd = GlobalDefinitions()
    gd.variables.append(SystemVariable(
        name="counter", type="uint32_t",
        description="カウンタ", title="カウンタ"))
    gd.flags.append(EventFlag(
        name="EVT_INIT", min_value=0, max_value=1,
        description="初期化", title="初期化"))
    return gd


def _make_config(folder_structure="flat", project_name="TestProject"):
    cfg = CodeGenerationConfig()
    cfg.project_name = project_name
    cfg.folder_structure = folder_structure
    cfg.generate_super_include = True
    cfg.table_type = "array"
    cfg.generation_style = "table_driven"
    cfg.os_type = "non_rtos"
    return cfg


# ============================================================
# 初期化
# ============================================================

class TestInit:

    def test_basic_init(self):
        gen = CCodeGenerator()
        assert gen.config is not None
        assert gen.generation_date is not None

    def test_config_override(self):
        cfg = _make_config(project_name="MyProject")
        gen = CCodeGenerator(config=cfg)
        assert gen.config.project_name == "MyProject"

    def test_get_generated_file_list(self):
        gen = CCodeGenerator()
        files = gen.get_generated_file_list()
        assert isinstance(files, list)
        assert "statable_types_common.h" in files
        assert "statable_types.h" in files
        assert "statable_transitions.c" in files
        assert "statable_role_functions.c" in files
        assert "statable_all.h" in files


# ============================================================
# 単層 generate_all
# ============================================================

class TestGenerateAllSingleLayer:

    def test_returns_dict(self):
        gen = CCodeGenerator(config=_make_config("flat"))
        sm = _make_sm()
        gd = _make_gd()
        result = gen.generate_all(sm, gd)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_required_files_present(self):
        gen = CCodeGenerator(config=_make_config("flat"))
        sm = _make_sm()
        gd = _make_gd()
        result = gen.generate_all(sm, gd)
        # 主要ファイル
        assert "statable_types_common.h" in result
        assert "statable_types.h" in result
        assert "statable_transitions.c" in result
        assert "statable_role_functions.c" in result

    def test_types_common_content(self):
        """statable_types_common.h に共通型が含まれる"""
        gen = CCodeGenerator(config=_make_config("flat"))
        sm = _make_sm()
        gd = _make_gd()
        result = gen.generate_all(sm, gd)
        content = result["statable_types_common.h"]
        assert "SystemData_t" in content
        assert "EventFlags_t" in content
        assert "SystemContext_t" in content
        # 共通型なので state enum は含まれない（層固有側）
        assert "STATE_t" not in content or "STATE_Driver_t" not in content

    def test_types_header_contains_enums(self):
        """statable_types.h（層固有）に enum が含まれる"""
        gen = CCodeGenerator(config=_make_config("flat"))
        sm = _make_sm()
        gd = _make_gd()
        result = gen.generate_all(sm, gd)
        content = result["statable_types.h"]
        # enum のみ
        assert "STATE_Driver_t" in content or "STATE_t" in content
        assert "typedef enum" in content

    def test_super_include_skipped_when_disabled(self):
        cfg = _make_config("flat")
        cfg.generate_super_include = False
        gen = CCodeGenerator(config=cfg)
        sm = _make_sm()
        gd = _make_gd()
        result = gen.generate_all(sm, gd)
        assert "statable_all.h" not in result


# ============================================================
# 複数層 generate_all_layers (by_layer)
# ============================================================

class TestGenerateAllLayersByLayer:

    def test_layer_specific_files_named(self):
        """層固有ファイルに _{layer} サフィックス"""
        cfg = _make_config("by_layer")
        gen = CCodeGenerator(config=cfg)

        layers = [
            ("Driver", _make_sm("Driver")),
            ("Application", _make_sm("Application")),
        ]
        gd = _make_gd()
        result = gen.generate_all_layers(layers, gd)

        # キーに "Driver/statable_role_functions_Driver.c" が含まれる
        keys = list(result.keys())
        assert any("Driver/statable_role_functions_Driver.c" in k
                   for k in keys), f"keys={keys}"
        assert any("Application/statable_role_functions_Application.c" in k
                   for k in keys)

    def test_layer_specific_types_enum_only(self):
        """層固有 types.h は enum のみ（共通型は含まない）"""
        cfg = _make_config("by_layer")
        gen = CCodeGenerator(config=cfg)

        layers = [("Driver", _make_sm("Driver"))]
        gd = _make_gd()
        result = gen.generate_all_layers(layers, gd)

        # 層固有 types
        types_key = "Driver/statable_types_Driver.h"
        assert types_key in result
        content = result[types_key]
        # enum は含む
        assert "STATE_Driver" in content or "typedef enum" in content
        # 共通型は含まない
        assert "SystemData_t" not in content

    def test_layer_types_includes_common(self):
        """層固有 types.h は common.h を include"""
        cfg = _make_config("by_layer")
        gen = CCodeGenerator(config=cfg)

        layers = [("Driver", _make_sm("Driver"))]
        gd = _make_gd()
        result = gen.generate_all_layers(layers, gd)

        content = result["Driver/statable_types_Driver.h"]
        assert "statable_types_common.h" in content

    def test_common_files_at_root(self):
        """共通ファイルは層フォルダ外（ルート）"""
        cfg = _make_config("by_layer")
        gen = CCodeGenerator(config=cfg)

        layers = [("Driver", _make_sm("Driver"))]
        gd = _make_gd()
        result = gen.generate_all_layers(layers, gd)

        keys = list(result.keys())
        assert "statable_types_common.h" in keys
        assert "statable_init.c" in keys
        assert "statable_interrupt.c" in keys

    def test_guard_has_layer_suffix(self):
        """層固有ヘッダの include guard に層サフィックス"""
        cfg = _make_config("by_layer")
        gen = CCodeGenerator(config=cfg)

        layers = [("Driver", _make_sm("Driver"))]
        gd = _make_gd()
        result = gen.generate_all_layers(layers, gd)

        content = result["Driver/statable_types_Driver.h"]
        # 層サフィックス付き guard
        assert "STATABLE_TYPES_H_DRIVER" in content

    def test_multiple_layers_priority_sorted(self):
        """優先度昇順に処理される"""
        cfg = _make_config("by_layer")
        gen = CCodeGenerator(config=cfg)

        sm1 = _make_sm("Driver")
        sm1.layer_priority = 3
        sm2 = _make_sm("Application")
        sm2.layer_priority = 1

        layers = [("Driver", sm1), ("Application", sm2)]
        gd = _make_gd()
        result = gen.generate_all_layers(layers, gd)

        # スーパーループ内の順序で確認
        super_loop_key = f"{cfg.project_name}_run.c"
        assert super_loop_key in result
        content = result[super_loop_key]
        # Application（優先度1）が Driver（優先度3）より前に
        idx_app = content.find("Application")
        idx_drv = content.find("Driver")
        assert idx_app < idx_drv or idx_drv == -1


# ============================================================
# by_type / flat
# ============================================================

class TestFolderStructures:

    def test_flat_structure(self):
        cfg = _make_config("flat")
        gen = CCodeGenerator(config=cfg)
        sm = _make_sm()
        gd = _make_gd()
        result = gen.generate_all(sm, gd)
        # ルート直下
        assert "statable_types_common.h" in result
        assert "statable_init.c" in result

    def test_by_type_structure(self):
        cfg = _make_config("by_type")
        gen = CCodeGenerator(config=cfg)
        sm = _make_sm()
        gd = _make_gd()
        result = gen.generate_all(sm, gd)
        # by_type でも generate_all のキーは同じ（パス解決は保存時）
        assert isinstance(result, dict)
        assert len(result) > 0


# ============================================================
# パス解決
# ============================================================

class TestPathResolution:

    def test_layer_filename_with_layer(self):
        gen = CCodeGenerator()
        result = gen._layer_filename(
            "statable_role_functions.c", "Driver")
        assert result == "statable_role_functions_Driver.c"

    def test_layer_filename_without_layer(self):
        gen = CCodeGenerator()
        result = gen._layer_filename(
            "statable_role_functions.c", "")
        assert result == "statable_role_functions.c"

    def test_layer_filename_common_file_unchanged(self):
        """共通ファイル（LAYER_SPECIFIC_FILES 外）は変更なし"""
        gen = CCodeGenerator()
        result = gen._layer_filename("statable_init.c", "Driver")
        assert result == "statable_init.c"

    def test_layer_suffix_with_layer(self):
        gen = CCodeGenerator()
        assert gen._layer_suffix("Driver") == "_Driver"

    def test_layer_suffix_without_layer(self):
        gen = CCodeGenerator()
        assert gen._layer_suffix("") == ""

    def test_resolve_path_flat(self):
        cfg = _make_config("flat")
        gen = CCodeGenerator(config=cfg)
        result = gen._resolve_path_flat("statable_init.c")
        assert result == "statable_init.c"

    def test_resolve_path_by_type(self):
        cfg = _make_config("by_type")
        gen = CCodeGenerator(config=cfg)
        result = gen._resolve_path_by_type("statable_init.c")
        # src フォルダに
        assert "statable_init.c" in result

    def test_resolve_output_path_by_layer_with_folder(self):
        cfg = _make_config("by_layer")
        gen = CCodeGenerator(config=cfg)
        result = gen._resolve_output_path(
            "Driver/statable_types_Driver.h", "Driver")
        # 既にパス形式なら変更なし
        assert result == "Driver/statable_types_Driver.h"


# ============================================================
# 保存
# ============================================================

class TestSave:

    def test_save_without_merge(self, tmp_path):
        cfg = _make_config("flat")
        gen = CCodeGenerator(config=cfg)
        sm = _make_sm()
        gd = _make_gd()
        generated = gen.generate_all(sm, gd)

        output_dir = tmp_path / "output"
        saved = gen.save_generated_code(generated, str(output_dir))

        assert len(saved) > 0
        assert (output_dir / "statable_types_common.h").exists()
        assert (output_dir / "statable_init.c").exists()

    def test_save_by_layer_structure(self, tmp_path):
        cfg = _make_config("by_layer")
        gen = CCodeGenerator(config=cfg)
        layers = [("Driver", _make_sm("Driver"))]
        gd = _make_gd()
        generated = gen.generate_all_layers(layers, gd)

        output_dir = tmp_path / "output"
        gen.save_generated_code(generated, str(output_dir))

        # 層フォルダが作成される
        assert (output_dir / "Driver").is_dir()
        assert (output_dir / "Driver" / "statable_types_Driver.h").exists()
        # 共通ファイルはルート
        assert (output_dir / "statable_types_common.h").exists()

    def test_save_with_merge_preserves_user_code(self, tmp_path):
        cfg = _make_config("flat")
        gen = CCodeGenerator(config=cfg)
        sm = _make_sm()
        gd = _make_gd()
        generated = gen.generate_all(sm, gd)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # 事前に既存ファイルを配置（ユーザーコード入り）
        types_path = output_dir / "statable_types_common.h"
        types_path.write_text(
            "#ifndef X\n"
            "#define X\n"
            "/* [[STABLE_USER_CODE_START]] */\n"
            "int user_custom(void);\n"
            "/* [[STABLE_USER_CODE_END]] */\n"
            "#endif\n",
            encoding="utf-8",
        )

        merged = gen.save_generated_code_with_merge(
            generated, str(output_dir))

        # ユーザーコードが保持される
        content = types_path.read_text(encoding="utf-8")
        assert "int user_custom(void);" in content


# ============================================================
# generate_file（単一ファイル）
# ============================================================

class TestGenerateFile:

    def test_specific_file(self):
        cfg = _make_config("flat")
        gen = CCodeGenerator(config=cfg)
        sm = _make_sm()
        gd = _make_gd()
        result = gen.generate_file(
            "statable_types_common.h", sm, gd)
        assert "SystemData_t" in result

    def test_unknown_file_raises(self):
        cfg = _make_config("flat")
        gen = CCodeGenerator(config=cfg)
        sm = _make_sm()
        gd = _make_gd()
        with pytest.raises(ValueError, match="Unknown file"):
            gen.generate_file("not_exist.h", sm, gd)


# ============================================================
# エッジケース
# ============================================================

class TestEdgeCases:

    def test_empty_sm(self):
        cfg = _make_config("flat")
        gen = CCodeGenerator(config=cfg)
        sm = StateMachine()
        sm.layer_name = "Empty"
        gd = GlobalDefinitions()
        # クラッシュしないこと
        result = gen.generate_all(sm, gd)
        assert isinstance(result, dict)

    def test_empty_gd(self):
        cfg = _make_config("flat")
        gen = CCodeGenerator(config=cfg)
        sm = _make_sm()
        gd = GlobalDefinitions()
        result = gen.generate_all(sm, gd)
        assert "statable_types_common.h" in result

    def test_normalize_layers_single_sm(self):
        gen = CCodeGenerator()
        sm = _make_sm("Driver")
        result = gen._normalize_layers(sm)
        assert len(result) == 1
        assert result[0][1] is sm

    def test_normalize_layers_tuple_list(self):
        gen = CCodeGenerator()
        layers = [
            ("Driver", _make_sm("Driver")),
            ("App", _make_sm("App")),
        ]
        result = gen._normalize_layers(layers)
        assert len(result) == 2

    def test_normalize_layers_sorted_by_priority(self):
        gen = CCodeGenerator()
        sm1 = _make_sm("A")
        sm1.layer_priority = 5
        sm2 = _make_sm("B")
        sm2.layer_priority = 1
        result = gen._normalize_layers([("A", sm1), ("B", sm2)])
        assert result[0][0] == "B"  # 優先度1が先
        assert result[1][0] == "A"

    def test_normalize_layers_empty(self):
        gen = CCodeGenerator()
        assert gen._normalize_layers(None) == []
        assert gen._normalize_layers([]) == []

    def test_get_layer_name(self):
        gen = CCodeGenerator()
        sm = _make_sm("Driver")
        assert gen._get_layer_name(sm) == "Driver"

    def test_get_layer_name_empty(self):
        gen = CCodeGenerator()
        sm = StateMachine()
        assert gen._get_layer_name(sm) == ""

    def test_get_initial_state(self):
        gen = CCodeGenerator()
        sm = _make_sm()
        assert gen._get_initial_state(sm) == "Idle"

    def test_get_initial_state_fallback(self):
        """initial_state 未設定なら 'Idle'"""
        gen = CCodeGenerator()
        sm = StateMachine()
        assert gen._get_initial_state(sm) == "Idle"