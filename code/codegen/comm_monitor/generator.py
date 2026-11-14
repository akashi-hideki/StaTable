"""CommMonitor C code generator (v3.6.0 p2 / ring buffer)."""
from pathlib import Path
from .config import CommMonitorConfig
from .registry import VarMeta, registry_crc32
from . import templates


class CommMonitorGenerator:
    def __init__(self, config: CommMonitorConfig, variables: list[VarMeta]):
        config.validate()
        self.config = config
        self.vars = variables

    def generate(self, out_dir: Path) -> list[Path]:
        out_dir.mkdir(parents=True, exist_ok=True)
        crc = registry_crc32(self.vars)

        entries = "\n".join(
            f"    {{ &g_ctx.data.{v.name}, {v.size} }}," for v in self.vars
        )
        names = "\n".join(
            f'    "{v.name}",' for v in self.vars
        )

        rendered = {
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

        written: list[Path] = []
        for name, body in rendered.items():
            p = out_dir / name
            p.write_text(body, encoding="utf-8")
            written.append(p)
        return written
