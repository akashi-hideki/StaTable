"""CommMonitor の設定値（v3.6.0 / GET 専用 / ASCII のみ）。"""
from dataclasses import dataclass

MIN_POLL_PERIOD_MS = 100
DEFAULT_POLL_PERIOD_MS = 200
MAX_POLL_PERIOD_MS = 60_000


@dataclass
class CommMonitorConfig:
    enabled: bool = False
    ascii_body_max: int = 256
    rx_ring_size: int = 64
    tx_ring_size: int = 64
    idle_ms: int = 100
    ack_unit: bool = True
    ack_name: bool = True
    period_ms: int = DEFAULT_POLL_PERIOD_MS

    def validate(self) -> None:
        if self.rx_ring_size & (self.rx_ring_size - 1):
            raise ValueError("rx_ring_size must be power of two")
        if self.tx_ring_size & (self.tx_ring_size - 1):
            raise ValueError("tx_ring_size must be power of two")
        if not (MIN_POLL_PERIOD_MS <= self.period_ms <= MAX_POLL_PERIOD_MS):
            raise ValueError(
                f"period_ms must be {MIN_POLL_PERIOD_MS}..{MAX_POLL_PERIOD_MS}"
            )
