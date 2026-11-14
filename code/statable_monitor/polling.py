"""PC 側ポーリング制御（最小 100 ms）。"""
import threading
import time


class PollingController:
    MIN_MS = 100
    MAX_MS = 60_000

    def __init__(self, send_get):
        self._send_get = send_get
        self._thread = None
        self._stop = threading.Event()

    def start(self, ids, period_ms=200, on_sample=None):
        if not (self.MIN_MS <= period_ms <= self.MAX_MS):
            raise ValueError(
                f"period_ms must be {self.MIN_MS}..{self.MAX_MS}")
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop,
            args=(list(ids), period_ms, on_sample),
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _loop(self, ids, period_ms, on_sample):
        interval = period_ms / 1000.0
        next_t = time.monotonic()
        while not self._stop.is_set():
            try:
                values = self._send_get(ids)
                ts = time.monotonic()
                if on_sample:
                    for idx, val in values.items():
                        on_sample(idx, val, ts)
            except TimeoutError:
                pass
            next_t += interval
            sleep = next_t - time.monotonic()
            if sleep > 0:
                self._stop.wait(sleep)
            else:
                next_t = time.monotonic()
