#!/usr/bin/env python3
"""patch_v3_6_0_comm_monitor_p3a.py

Patch 3a: CommMonitorGenerator.render() + CodeGenerationConfig 統合。

- codegen/comm_monitor/generator.py に render() を追加（ディスク書込なし）
- codegen/config.py に comm_monitor フィールドを追加（enabled=False 既定）
- tests/test_v3_6_0_comm_monitor_generator.py に 4 件追加
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
CODE = REPO if (REPO / "pyproject.toml").exists() else REPO / "code"


def backup_and_write(rel, content):
    p = CODE / rel
    if p.exists():
        bak = p.with_suffix(p.suffix + ".bak_p3a")
        bak.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"  [backup] {bak.name}")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  [write ] {rel}")


GENERATOR_PY = '''"""CommMonitor C code generator (v3.6.0 p3a / render+generate)."""
from pathlib import Path
from .config import CommMonitorConfig
from .registry import VarMeta, registry_crc32
from . import templates


class CommMonitorGenerator:
    def __init__(self, config: CommMonitorConfig, variables: list[VarMeta]):
        config.validate()
        self.config = config
        self.vars = variables

    def render(self) -> dict[str, str]:
        """生成ファイルを filename -> content の dict で返す（書込なし）。"""
        crc = registry_crc32(self.vars)
        entries = "\\n".join(
            f"    {{ &g_ctx.data.{v.name}, {v.size} }}," for v in self.vars
        )
        names = "\\n".join(f'    "{v.name}",' for v in self.vars)
        return {
            "statable_comm_config.h": templates.CONFIG_H.substitute(
                enabled=int(self.config.enabled),
                body_max=self.config.ascii_body_max,
                rx_ring=self.config.rx_ring_size,
                tx_ring=self.config.tx_ring_size,
                idle_ms=self.config.idle_ms,
                ack_unit=int(self.config.ack_unit),
                ack_name=int(self.config.ack_name),
                version="3.6.0",
                crc32=f"{crc:08X}",
                var_count=len(self.vars),
            ),
            "statable_comm_registry.h": templates.REGISTRY_H.substitute(),
            "statable_comm_registry.c": templates.REGISTRY_C.substitute(
                entries=entries, names=names,
            ),
            "statable_comm_ring.h": templates.RING_H.substitute(),
            "statable_comm_ring.c": templates.RING_C.substitute(),
            "statable_comm_monitor.h": templates.MONITOR_H.substitute(),
            "statable_comm_monitor.c": templates.MONITOR_C.substitute(),
        }

    def generate(self, out_dir: Path) -> list[Path]:
        out_dir.mkdir(parents=True, exist_ok=True)
        written: list[Path] = []
        for name, body in self.render().items():
            p = out_dir / name
            p.write_text(body, encoding="utf-8")
            written.append(p)
        return written
'''


NEW_TESTS = '''

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
'''


def patch_config_py() -> bool:
    p = CODE / "codegen" / "config.py"
    text = p.read_text(encoding="utf-8")

    if "CommMonitorConfig" in text:
        print("  [skip ] config.py already has CommMonitorConfig")
        return True

    old_import = "from typing import Dict, List, Optional"
    if old_import not in text:
        print("  [error] typing import pattern not found in config.py")
        return False

    new_import = (
        "from typing import Dict, List, Optional\n"
        "\n"
        "try:\n"
        "    from .comm_monitor.config import CommMonitorConfig\n"
        "except ImportError:\n"
        "    from comm_monitor.config import CommMonitorConfig"
    )
    text = text.replace(old_import, new_import, 1)

    old_field = "    max_consecutive_pending_events: int = 16"
    if old_field not in text:
        print("  [error] max_consecutive_pending_events not found")
        return False

    new_field = (
        "    max_consecutive_pending_events: int = 16\n"
        "\n"
        "    # ===== Communication monitor (v3.6.0) =====\n"
        "    comm_monitor: CommMonitorConfig = field(\n"
        "        default_factory=CommMonitorConfig\n"
        "    )"
    )
    text = text.replace(old_field, new_field, 1)

    bak = p.with_suffix(p.suffix + ".bak_p3a")
    bak.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    p.write_text(text, encoding="utf-8")
    print("  [write ] codegen/config.py (import + field added)")
    return True


def main() -> int:
    print("=== patch_v3_6_0_comm_monitor_p3a ===")
    print(f"repo: {REPO}")

    backup_and_write("codegen/comm_monitor/generator.py", GENERATOR_PY)

    if not patch_config_py():
        return 1

    test_path = CODE / "tests" / "test_v3_6_0_comm_monitor_generator.py"
    current = test_path.read_text(encoding="utf-8")
    if "test_render_returns_dict_without_writing" in current:
        print("  [skip ] tests already contain render tests")
    else:
        test_path.write_text(current + NEW_TESTS, encoding="utf-8")
        print("  [append] tests/test_v3_6_0_comm_monitor_generator.py")

    print("=== done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())