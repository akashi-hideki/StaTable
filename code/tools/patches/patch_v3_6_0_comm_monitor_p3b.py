#!/usr/bin/env python3
"""patch_v3_6_0_comm_monitor_p3b.py

Patch 3b: generate_all 系メソッドに CommMonitor 生成物を統合する。

- c_code_generator.py に _collect_comm_monitor_variables / _merge_comm_monitor_files を追加
- generate_all / generate_all_layers / _generate_all_by_layer の返り値直前に統合呼び出しを挿入
- tests/test_v3_6_0_comm_monitor_integration.py を新規作成（3 件）

enabled=False 既定のため、既存挙動は変化しない。
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
CODE = REPO if (REPO / "pyproject.toml").exists() else REPO / "code"


def patch_c_code_generator() -> bool:
    p = CODE / "codegen" / "c_code_generator.py"
    text = p.read_text(encoding="utf-8")

    if "_merge_comm_monitor_files" in text:
        print("  [skip ] c_code_generator.py already patched")
        return True

    # ---- 1. import 追加 ----
    old_import = (
        "    from .config import CodeGenerationConfig, ConfigManager"
    )
    if old_import not in text:
        print("  [error] config import not found")
        return False
    new_import = (
        old_import + "\n"
        "    from .comm_monitor.generator import CommMonitorGenerator\n"
        "    from .comm_monitor.registry import build_registry"
    )
    text = text.replace(old_import, new_import, 1)

    # ---- 2. ヘルパメソッドを generate_all の直前に挿入 ----
    anchor = "    def generate_all(self, state_machine, global_defs,"
    if anchor not in text:
        print("  [error] generate_all anchor not found")
        return False

    helpers = (
        "    def _collect_comm_monitor_variables(self, global_defs):\n"
        "        \"\"\"GlobalDefinitions.variables を build_registry 用 dict に変換。\"\"\"\n"
        "        result = []\n"
        "        variables = getattr(global_defs, 'variables', None) or []\n"
        "        for v in variables:\n"
        "            ctype = getattr(v, 'type', None)\n"
        "            if not ctype:\n"
        "                continue\n"
        "            if getattr(v, 'array_size', 0) > 0:\n"
        "                continue  # 配列は v3.6.0 では非対応\n"
        "            result.append({\n"
        "                'name': getattr(v, 'name', ''),\n"
        "                'type': str(ctype),\n"
        "                'unit': getattr(v, 'unit', '') or '-',\n"
        "                'group': getattr(v, 'group', '') or '-',\n"
        "                'description': getattr(v, 'description', '') or '',\n"
        "            })\n"
        "        return result\n"
        "\n"
        "    def _merge_comm_monitor_files(self, generated_files,\n"
        "                                  state_machine, global_defs):\n"
        "        \"\"\"comm_monitor.enabled なら生成物を dict に追加して返す。\"\"\"\n"
        "        cfg = getattr(self.config, 'comm_monitor', None)\n"
        "        if cfg is None or not cfg.enabled:\n"
        "            return generated_files\n"
        "        var_dicts = self._collect_comm_monitor_variables(global_defs)\n"
        "        if not var_dicts:\n"
        "            logger.warning(\n"
        "                'comm_monitor enabled but no variables; skipping')\n"
        "            return generated_files\n"
        "        try:\n"
        "            registry = build_registry(var_dicts)\n"
        "            gen = CommMonitorGenerator(cfg, registry)\n"
        "            rendered = gen.render()\n"
        "        except ValueError as e:\n"
        "            logger.warning(f'comm_monitor: {e}; skipping')\n"
        "            return generated_files\n"
        "        for name, content in rendered.items():\n"
        "            generated_files[name] = content\n"
        "        logger.info(\n"
        "            f'comm_monitor: {len(rendered)} files merged '\n"
        "            f'({len(var_dicts)} vars)')\n"
        "        return generated_files\n"
        "\n"
    )
    text = text.replace(anchor, helpers + anchor, 1)

    # ---- 3. 3 メソッドの return 直前に統合呼び出しを挿入 ----
    def insert_merge(text, method_name):
        """def <method_name>(...) 〜 次の def までを切り出し、
        最初の 'return generated_files' を統合呼び出しに置換。"""
        start = text.find(f"    def {method_name}(")
        if start == -1:
            print(f"  [warn ] def {method_name} not found")
            return text
        next_def = text.find("\n    def ", start + 1)
        if next_def == -1:
            segment = text[start:]
        else:
            segment = text[start:next_def]

        ret_pattern = "return generated_files"
        if ret_pattern not in segment:
            print(f"  [warn ] return generated_files not found in {method_name}")
            return text

        idx = segment.find(ret_pattern)
        # 行頭の空白を取得
        line_start = segment.rfind("\n", 0, idx) + 1
        indent = segment[line_start:idx]
        replacement = (
            f"{indent}generated_files = self._merge_comm_monitor_files(\n"
            f"{indent}    generated_files, state_machine, global_defs)\n"
            f"{indent}return generated_files"
        )
        new_segment = (
            segment[:line_start]
            + replacement
            + segment[idx + len(ret_pattern):]
        )
        if next_def == -1:
            return text[:start] + new_segment
        return text[:start] + new_segment + text[next_def:]

    for method in ("generate_all", "generate_all_layers",
                   "_generate_all_by_layer"):
        text = insert_merge(text, method)

    bak = p.with_suffix(p.suffix + ".bak_p3b")
    bak.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    p.write_text(text, encoding="utf-8")
    print("  [write ] codegen/c_code_generator.py")
    return True


INTEGRATION_TEST = '''"""v3.6.0 comm_monitor integration tests."""
from pathlib import Path
from codegen.c_code_generator import CCodeGenerator
from codegen.comm_monitor.config import CommMonitorConfig
from codegen.config import CodeGenerationConfig
from statable.global_defs import GlobalDefinitions, SystemVariable


def _make_gd(with_vars=True):
    gd = GlobalDefinitions()
    if with_vars:
        gd.variables.append(SystemVariable(
            name="g_system_tick", type="volatile uint32_t",
            unit="1ms", group="Timer", description="System tick"))
        gd.variables.append(SystemVariable(
            name="oven_current_temp", type="uint16_t",
            unit="degC", group="Hardware",
            description="Current oven temperature"))
    return gd


def test_merge_disabled_returns_unchanged():
    cfg = CodeGenerationConfig(
        comm_monitor=CommMonitorConfig(enabled=False))
    gen = CCodeGenerator(config=cfg)
    gd = _make_gd()
    base = {"statable_types_common.h": "/* types */"}
    result = gen._merge_comm_monitor_files(base, None, gd)
    assert result == base
    assert "statable_comm_config.h" not in result


def test_merge_enabled_adds_comm_files():
    cfg = CodeGenerationConfig(
        comm_monitor=CommMonitorConfig(enabled=True))
    gen = CCodeGenerator(config=cfg)
    gd = _make_gd()
    base = {"statable_types_common.h": "/* types */"}
    result = gen._merge_comm_monitor_files(base, None, gd)
    assert "statable_comm_config.h" in result
    assert "statable_comm_monitor.c" in result
    assert "statable_comm_ring.c" in result
    assert "statable_comm_registry.c" in result
    assert "statable_types_common.h" in result


def test_merge_enabled_no_vars_returns_unchanged():
    cfg = CodeGenerationConfig(
        comm_monitor=CommMonitorConfig(enabled=True))
    gen = CCodeGenerator(config=cfg)
    gd = _make_gd(with_vars=False)
    base = {"statable_types_common.h": "/* types */"}
    result = gen._merge_comm_monitor_files(base, None, gd)
    assert result == base
'''


def write_integration_test():
    p = CODE / "tests" / "test_v3_6_0_comm_monitor_integration.py"
    if p.exists():
        print("  [skip ] integration test exists")
        return
    p.write_text(INTEGRATION_TEST, encoding="utf-8")
    print("  [new  ] tests/test_v3_6_0_comm_monitor_integration.py")


def main() -> int:
    print("=== patch_v3_6_0_comm_monitor_p3b ===")
    print(f"repo: {REPO}")

    if not patch_c_code_generator():
        return 1
    write_integration_test()

    print("=== done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())