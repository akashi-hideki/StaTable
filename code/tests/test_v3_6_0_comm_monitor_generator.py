"""v3.6.0 通信モニター生成器のテスト。"""
from pathlib import Path
import pytest
from codegen.comm_monitor.config import CommMonitorConfig
from codegen.comm_monitor.registry import build_registry, registry_crc32
from codegen.comm_monitor.generator import CommMonitorGenerator

VARS = [
    {"name": "g_system_tick", "type": "volatile uint32_t",
     "unit": "1ms", "group": "Timer"},
    {"name": "oven_current_temp", "type": "uint16_t",
     "unit": "degC", "group": "Hardware"},
    {"name": "heater_top_duty", "type": "uint8_t",
     "unit": "%", "group": "Hardware"},
]


def test_registry_ids_are_sequential():
    reg = build_registry(VARS)
    assert [v.id for v in reg] == [0, 1, 2]
    assert reg[0].size == 4
    assert reg[1].size == 2
    assert reg[2].size == 1


def test_registry_crc_is_stable():
    reg = build_registry(VARS)
    assert registry_crc32(reg) == registry_crc32(build_registry(VARS))


def test_generator_writes_all_files(tmp_path: Path):
    reg = build_registry(VARS)
    gen = CommMonitorGenerator(CommMonitorConfig(enabled=True), reg)
    written = gen.generate(tmp_path)
    names = {p.name for p in written}
    assert "statable_comm_config.h" in names
    assert "statable_comm_registry.c" in names
    assert "statable_comm_monitor.c" in names


def test_generated_config_has_var_count(tmp_path: Path):
    reg = build_registry(VARS)
    gen = CommMonitorGenerator(CommMonitorConfig(enabled=True), reg)
    gen.generate(tmp_path)
    text = (tmp_path / "statable_comm_config.h").read_text()
    assert "COMM_MONITOR_VAR_COUNT      3u" in text


def test_period_validation_rejects_below_100():
    with pytest.raises(ValueError):
        CommMonitorConfig(period_ms=50).validate()


def test_generator_writes_ring_files(tmp_path: Path):
    reg = build_registry(VARS)
    gen = CommMonitorGenerator(CommMonitorConfig(enabled=True), reg)
    written = gen.generate(tmp_path)
    names = {p.name for p in written}
    assert "statable_comm_ring.h" in names
    assert "statable_comm_ring.c" in names


def test_monitor_c_uses_ring(tmp_path: Path):
    reg = build_registry(VARS)
    gen = CommMonitorGenerator(CommMonitorConfig(enabled=True), reg)
    gen.generate(tmp_path)
    text = (tmp_path / "statable_comm_monitor.c").read_text(encoding="utf-8")
    assert "comm_ring_push" in text
    assert "comm_ring_pop" in text
    assert "process_byte" in text
    assert "g_rx_ring" in text


def test_render_returns_dict_without_writing(tmp_path: Path):
    reg = build_registry(VARS)
    gen = CommMonitorGenerator(CommMonitorConfig(enabled=True), reg)
    result = gen.render()
    assert isinstance(result, dict)
    assert "statable_comm_config.h" in result
    assert "statable_comm_monitor.c" in result
    assert "statable_comm_ring.c" in result
    # no files written to tmp_path
    assert not list(tmp_path.iterdir())


def test_render_matches_generate(tmp_path: Path):
    reg = build_registry(VARS)
    gen = CommMonitorGenerator(CommMonitorConfig(enabled=True), reg)
    rendered = gen.render()
    gen.generate(tmp_path)
    for name, content in rendered.items():
        on_disk = (tmp_path / name).read_text(encoding="utf-8")
        assert on_disk == content


def test_config_has_comm_monitor_field():
    from codegen.config import CodeGenerationConfig
    cfg = CodeGenerationConfig()
    assert hasattr(cfg, "comm_monitor")
    assert cfg.comm_monitor.enabled is False


def test_config_comm_monitor_can_be_enabled():
    from codegen.config import CodeGenerationConfig
    from codegen.comm_monitor.config import CommMonitorConfig
    cfg = CodeGenerationConfig(
        comm_monitor=CommMonitorConfig(enabled=True))
    assert cfg.comm_monitor.enabled is True
