"""In-process StaTable comm_monitor simulator.

Emulates PING / LIST / GET / HELP over a pyserial-compatible wrapper
so that StaTableMonitor can talk to it without hardware.

Values are time-varying (triangle wave) so the generated psblog
contains meaningful samples for PowerSimBuilder.
"""
import threading
import time

STX = 0x02
CR = 0x0D
ETX = 0x03


class SimulatedDevice:
    VARS = [
        # name, type, unit, group, description, wave-spec
        ('g_system_tick',     'uint32_t', '1ms',  'Timer',
         'System tick',          'tick'),
        ('oven_current_temp', 'uint16_t', 'degC', 'Hardware',
         'Current oven temp',    'triangle:25,200'),
        ('oven_target_temp',  'uint16_t', 'degC', 'Hardware',
         'Target oven temp',     'const:200'),
        ('heater_top_duty',   'uint8_t',  '%',    'Hardware',
         'Top heater PWM duty',  'triangle:0,100'),
        ('error_code',        'uint8_t',  '-',    'System',
         'Error code',           'const:0'),
    ]
    FW = '3.6.0'
    CRC = 0x00000000  # Simulator: fixed CRC; skipped by GUI when no XML

    def __init__(self):
        self.t0 = time.monotonic()

    def value_at(self, var_id, t_ms):
        _n, _t, _u, _g, _d, wave = self.VARS[var_id]
        if wave == 'tick':
            return t_ms
        if wave.startswith('const:'):
            return int(wave.split(':', 1)[1])
        if wave.startswith('triangle:'):
            lo, hi = map(int, wave.split(':', 1)[1].split(','))
            period_ms = 4000
            phase = (t_ms % period_ms) / period_ms
            if phase < 0.5:
                v = lo + (hi - lo) * (phase / 0.5)
            else:
                v = hi - (hi - lo) * ((phase - 0.5) / 0.5)
            return int(round(v))
        return 0

    def handle_frame(self, body):
        t_ms = int((time.monotonic() - self.t0) * 1000)
        parts = body.strip().split()
        if not parts:
            return None
        cmd = parts[0].upper()
        args = parts[1:]
        if cmd == 'PING':
            return (f'ACK ret=0 fw={self.FW} '
                    f'crc={self.CRC:08X} vars={len(self.VARS)}')
        if cmd == 'LIST':
            lines = [f'ACK ret=0 vars={len(self.VARS)}']
            for i, (name, type_, unit, group, _desc, _w) in enumerate(self.VARS):
                lines.append(
                    f'ACK ret=0 id={i} name={name} '
                    f'type={type_} unit={unit} group={group}')
            return '\n'.join(lines)
        if cmd == 'HELP':
            return 'ACK ret=0 cmds=PING,LIST,GET,HELP'
        if cmd == 'GET':
            if not args:
                return 'NAK ret=7 reason=args'
            compact = False
            if args and args[-1] == 'compact':
                compact = True
                args = args[:-1]
            tokens = ','.join(args).split(',')
            vals = []
            for tok in tokens:
                tok = tok.strip()
                if not tok or not tok.isdigit():
                    return 'NAK ret=1 reason=parse'
                v_id = int(tok)
                if v_id >= len(self.VARS):
                    return 'NAK ret=2 reason=idx'
                vals.append((v_id, self.value_at(v_id, t_ms)))
            if compact:
                return 'ACK ret=0 ' + ' '.join(f'{i}={v}' for i, v in vals)
            return 'ACK ret=0 ' + ' '.join(
                f'id={i} name={self.VARS[i][0]} value={v}'
                for i, v in vals)
        return 'NAK ret=5 reason=cmd'


class SimulatedSerial:
    """pyserial-compatible wrapper around SimulatedDevice."""
    def __init__(self, device=None, timeout=0.1, **_ignored):
        self.device = device or SimulatedDevice()
        self.timeout = timeout
        self._rx = bytearray()
        self._tx = bytearray()
        self._lock = threading.Lock()

    def write(self, data):
        with self._lock:
            self._rx.extend(data)
            self._process()

    def _process(self):
        while True:
            if STX not in self._rx:
                self._rx.clear()
                return
            si = self._rx.index(STX)
            del self._rx[:si]
            try:
                ei = self._rx.index(CR)
            except ValueError:
                return
            if len(self._rx) < ei + 2 or self._rx[ei + 1] != ETX:
                del self._rx[:1]
                continue
            body = bytes(self._rx[1:ei]).decode('ascii', 'replace')
            del self._rx[:ei + 2]
            resp = self.device.handle_frame(body)
            if resp:
                for line in resp.split('\n'):
                    self._tx.append(STX)
                    self._tx.extend(line.encode('ascii', 'replace'))
                    self._tx.append(CR)
                    self._tx.append(ETX)

    def read(self, n=1):
        deadline = time.monotonic() + self.timeout
        while True:
            with self._lock:
                if self._tx:
                    out = bytes(self._tx[:n])
                    del self._tx[:n]
                    return out
            if time.monotonic() >= deadline:
                return b''
            time.sleep(0.003)

    def close(self):
        pass

    @property
    def in_waiting(self):
        with self._lock:
            return len(self._tx)
