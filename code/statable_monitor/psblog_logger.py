"""psblog/v1 writer (PC side only)."""
from datetime import datetime, timezone
from pathlib import Path


class LogOptions:
    def __init__(self, max_file_size_bytes=10 * 1024 * 1024,
                 rotate_suffix='.{index}'):
        self.max_file_size_bytes = max_file_size_bytes
        self.rotate_suffix = rotate_suffix


class PStaBlogLogger:
    def __init__(self, path, source, firmware, period_ms, variables,
                 options=None):
        self.path = Path(path)
        self.source = source
        self.firmware = firmware
        self.period_ms = period_ms
        self.variables = list(variables)
        self.options = options or LogOptions()
        self._f = None
        self._samples = 0
        self._dropped = 0

    def start(self):
        self._f = self.path.open('w', encoding='utf-8', newline='\n')
        t0 = datetime.now(timezone.utc).astimezone()
        self._f.write('# StaTable UART Monitor Log\n')
        self._f.write('@schema       psblog/v1\n')
        ts = t0.isoformat(timespec='milliseconds')
        self._f.write('@captured_at  {}\n'.format(ts))
        self._f.write('@source       uart:{}\n'.format(self.source))
        self._f.write('@firmware     {}\n'.format(self.firmware))
        self._f.write('@protocol     pstable-uart/v1\n')
        self._f.write('@period_ms    {}\n'.format(self.period_ms))
        for v in self.variables:
            desc = v.get('description', '')
            # Always emit quoted description (spec §10.3)
            desc_q = '"{}"'.format(desc)
            line = '@var {} {} {} {} {}\n'.format(
                v['name'], v['type'],
                v.get('unit', '-'), v.get('group', '-'), desc_q)
            self._f.write(line)

    def write(self, name, value, host_ts):
        if self._f is None:
            return
        t_ms = int(round(host_ts * 1000))
        self._f.write('@{} {}={}\n'.format(t_ms, name, value))
        self._samples += 1

    def write_many(self, name_values, host_ts):
        """Write multiple name=value pairs on one Data line (spec §8).

        One call = one sample. The sample counter increments once.
        """
        if self._f is None:
            return
        if not name_values:
            return
        t_ms = int(round(host_ts * 1000))
        pairs = ' '.join('{}={}'.format(k, v) for k, v in name_values.items())
        self._f.write('@{} {}\n'.format(t_ms, pairs))
        self._samples += 1

    def stop(self):
        if self._f is None:
            return
        end = datetime.now(timezone.utc).astimezone()
        ts = end.isoformat(timespec='milliseconds')
        self._f.write('@end      {}\n'.format(ts))
        self._f.write('@samples  {}\n'.format(self._samples))
        self._f.write('@dropped  {}\n'.format(self._dropped))
        self._f.close()
        self._f = None

