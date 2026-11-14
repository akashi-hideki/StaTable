"""psblog/v1 ライター（PC 側専用）。"""
from datetime import datetime, timezone
from pathlib import Path


class PStaBlogLogger:
    def __init__(self, path, source, firmware, period_ms, variables):
        self.path = Path(path)
        self.source = source
        self.firmware = firmware
        self.period_ms = period_ms
        self.variables = list(variables)
        self._f = None
        self._samples = 0
        self._dropped = 0

    def start(self):
        self._f = self.path.open("w", encoding="utf-8", newline="\n")
        t0 = datetime.now(timezone.utc).astimezone()
        self._f.write("# PStaTable UART Monitor Log\n")
        self._f.write("@schema       psblog/v1\n")
        self._f.write(
            f"@captured_at  {t0.isoformat(timespec='milliseconds')}\n")
        self._f.write(f"@source       uart:{self.source}\n")
        self._f.write(f"@firmware     {self.firmware}\n")
        self._f.write("@protocol     pstable-uart/v1\n")
        self._f.write(f"@period_ms    {self.period_ms}\n")
        for v in self.variables:
            desc = v.get("description", "")
            desc_q = f'"{desc}"' if desc else ""
            self._f.write(
                f"@var {v['name']} {v['type']} {v.get('unit', '-')} "
                f"{v.get('group', '-')} {desc_q}\n")

    def write(self, name, value, host_ts):
        if self._f is None:
            return
        t_ms = int(round(host_ts * 1000))
        self._f.write(f"@{t_ms} {name}={value}\n")
        self._samples += 1

    def stop(self):
        if self._f is None:
            return
        end = datetime.now(timezone.utc).astimezone()
        self._f.write(
            f"@end      {end.isoformat(timespec='milliseconds')}\n")
        self._f.write(f"@samples  {self._samples}\n")
        self._f.write(f"@dropped  {self._dropped}\n")
        self._f.close()
        self._f = None
