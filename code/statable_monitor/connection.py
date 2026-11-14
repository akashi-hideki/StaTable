"""StaTable monitor SDK - connection & commands (ASCII mode)."""
import time

STX = 0x02
ETX = 0x03
CR = 0x0D


class ConnectionError(Exception):
    pass


class StaTableMonitor:
    def __init__(self, serial_factory=None):
        self._factory = serial_factory
        self._ser = None
        self._timeout = 1.0
        self._registry = None
        self._polling = None

    def connect(self, port, baudrate=115200, xml_path=None):
        if self._factory:
            self._ser = self._factory(port=port, baudrate=baudrate,
                                       timeout=self._timeout)
        else:
            import serial
            self._ser = serial.Serial(port, baudrate, timeout=self._timeout)
        self._registry = None
        if xml_path:
            from .registry import load_xml
            self._registry = load_xml(xml_path)
            pong = self.ping()
            expected = '{:08X}'.format(self._registry.crc32)
            device_crc = pong.get('crc', '')
            if device_crc != expected:
                self._ser.close()
                raise ConnectionError(
                    'XML CRC mismatch: xml={} device={}'.format(
                        expected, device_crc))

    def close(self):
        self.stop_polling()
        if self._ser:
            self._ser.close()
            self._ser = None

    def ping(self):
        return self._command('PING')

    def list_variables(self):
        self._ser.write(bytes([STX]) + b'LIST' + bytes([CR, ETX]))
        first = self._parse(self._read_frame())
        if first['kind'] != 'ACK':
            raise ConnectionError('LIST failed: {}'.format(first))
        n = int(first['vars'])
        from .registry import VariableInfo, RegistryInfo
        import zlib
        variables = []
        for _ in range(n):
            f = self._parse(self._read_frame())
            variables.append(VariableInfo(
                id=int(f['id']),
                name=f['name'],
                c_type=f.get('type', 'uint32_t'),
                unit=f.get('unit', '-'),
                group=f.get('group', '-'),
            ))
        payload = '\n'.join(
            '{}:{}'.format(v.name, v.c_type) for v in variables
        ).encode('utf-8')
        return RegistryInfo(variables, zlib.crc32(payload) & 0xFFFFFFFF)

    def _ensure_registry(self):
        if self._registry is None:
            self._registry = self.list_variables()

    def _resolve(self, name_or_id):
        if isinstance(name_or_id, int):
            return name_or_id
        for v in self._registry.variables:
            if v.name == name_or_id:
                return v.id
        raise KeyError('unknown variable: {}'.format(name_or_id))

    def get(self, name_or_id):
        self._ensure_registry()
        idx = self._resolve(name_or_id)
        resp = self._command('GET {}'.format(idx))
        if resp['kind'] != 'ACK':
            raise ConnectionError('GET failed: {}'.format(resp))
        return int(resp['value'])

    def get_many(self, names_or_ids):
        self._ensure_registry()
        ids = [self._resolve(n) for n in names_or_ids]
        ids_str = ','.join(str(i) for i in ids)
        resp = self._command('GET {} compact'.format(ids_str))
        if resp['kind'] != 'ACK':
            raise ConnectionError('GET failed: {}'.format(resp))
        result = {}
        for i in ids:
            key = str(i)
            if key in resp:
                result[i] = int(resp[key])
        return result

    def start_polling(self, names_or_ids, period_ms=200, on_sample=None):
        from .polling import PollingController
        if self._polling is not None:
            raise RuntimeError('polling already running')
        self._ensure_registry()
        ids = [self._resolve(n) for n in names_or_ids]

        def _fetch(fetch_ids):
            ids_str = ','.join(str(i) for i in fetch_ids)
            resp = self._command('GET {} compact'.format(ids_str))
            if resp['kind'] != 'ACK':
                raise TimeoutError('poll failed: {}'.format(resp))
            return {
                i: int(resp[str(i)])
                for i in fetch_ids if str(i) in resp
            }

        self._polling = PollingController(_fetch)
        self._polling.start(ids, period_ms=period_ms, on_sample=on_sample)

    def stop_polling(self):
        if self._polling is not None:
            self._polling.stop()
            self._polling = None

    def create_logger(self, path, variables=None):
        from .psblog_logger import PStaBlogLogger, LogOptions
        self._ensure_registry()
        if variables is None:
            variables = [
                {'name': v.name, 'type': v.c_type,
                 'unit': v.unit, 'group': v.group,
                 'description': v.description}
                for v in self._registry.variables
            ]
        fw = self.ping().get('fw', 'unknown')
        source = getattr(self._ser, 'port', 'uart')
        return PStaBlogLogger(
            path=path,
            source=source,
            firmware='StaTable v{}'.format(fw),
            period_ms=200,
            variables=variables,
            options=LogOptions(),
        )

    def _command(self, body):
        frame = bytes([STX]) + body.encode('ascii') + bytes([CR, ETX])
        self._ser.write(frame)
        return self._parse(self._read_frame())

    def _read_frame(self):
        buf = bytearray()
        deadline = time.monotonic() + self._timeout
        while time.monotonic() < deadline:
            b = self._ser.read(1)
            if not b:
                continue
            if b[0] == STX:
                buf.clear()
                continue
            if b[0] == CR:
                nxt = self._ser.read(1)
                if nxt and nxt[0] == ETX:
                    return buf.decode('ascii', 'replace')
                continue
            buf.append(b[0])
        raise TimeoutError('no response')

    @staticmethod
    def _parse(line):
        parts = line.split()
        out = {'kind': parts[0] if parts else '', 'ret': -1}
        for p in parts[1:]:
            if '=' in p:
                k, v = p.split('=', 1)
                out[k] = v
        if 'ret' in out:
            try:
                out['ret'] = int(out['ret'])
            except ValueError:
                pass
        return out

