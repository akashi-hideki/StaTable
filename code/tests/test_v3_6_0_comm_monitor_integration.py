"""v3.6.0 comm_monitor integration tests."""
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
