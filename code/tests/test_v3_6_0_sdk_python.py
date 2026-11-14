"""v3.6.0 SDK Python tests (pyserial mock)."""
import time
from pathlib import Path

import pytest

import sys as _sys
from pathlib import Path as _Path
_CODE_DIR = _Path(__file__).resolve().parent.parent
if str(_CODE_DIR) not in _sys.path:
    _sys.path.insert(0, str(_CODE_DIR))

from statable_monitor import StaTableMonitor, ConnectionError
from statable_monitor.registry import VariableInfo, RegistryInfo


def _frame(body):
    return b"\x02" + body.encode("ascii") + b"\x0d\x03"


class FakeSerial:
    def __init__(self, script):
        self._script = [
            (pattern, [_frame(b) for b in bodies])
            for pattern, bodies in script
        ]
        self._buffer = b''
        self.port = 'COM_TEST'
        self.written = b''

    def write(self, data):
        self.written += data
        if data.startswith(b'\x02') and data.endswith(b'\x0d\x03'):
            body = data[1:-2].decode('ascii')
            for pattern, frames in self._script:
                if body.startswith(pattern):
                    self._buffer += b''.join(frames)
                    break
        return len(data)

    def read(self, n=1):
        if not self._buffer:
            return b''
        chunk = self._buffer[:n]
        self._buffer = self._buffer[n:]
        return chunk

    def close(self):
        pass


def _make_monitor(script):
    fake = FakeSerial(script)
    m = StaTableMonitor(serial_factory=lambda **kw: fake)
    m.connect('COM_TEST')
    return m, fake


def _set_registry(m):
    m._registry = RegistryInfo(
        variables=[
            VariableInfo(0, 'g_system_tick', 'uint32_t',
                         unit='1ms', group='Timer'),
            VariableInfo(1, 'oven_current_temp', 'uint16_t',
                         unit='degC', group='Hardware'),
            VariableInfo(2, 'oven_target_temp', 'uint16_t',
                         unit='degC', group='Hardware'),
        ],
        crc32=0,
    )


def test_connect_opens_serial():
    m, fake = _make_monitor([
        ('PING', ['ACK ret=0 fw=3.6.0 crc=0 vars=3']),
    ])
    assert m._ser is fake


def test_ping_returns_ack():
    m, _ = _make_monitor([
        ('PING', ['ACK ret=0 fw=3.6.0 crc=8A3F21C7 vars=30']),
    ])
    resp = m.ping()
    assert resp['kind'] == 'ACK'
    assert resp['fw'] == '3.6.0'
    assert resp['crc'] == '8A3F21C7'


def test_connect_xml_crc_mismatch(tmp_path):
    xml = tmp_path / 'test.xml'
    xml.write_text(
        '<root><variable name="a" type="uint8_t"/></root>')
    m, _ = _make_monitor([
        ('PING', ['ACK ret=0 fw=3.6.0 crc=DEADBEEF vars=1']),
    ])
    with pytest.raises(ConnectionError, match='CRC mismatch'):
        m.connect('COM_TEST', xml_path=str(xml))


def test_list_variables():
    m, _ = _make_monitor([
        ('LIST', [
            'ACK ret=0 vars=2',
            'ACK ret=0 id=0 name=g_system_tick type=uint32_t',
            'ACK ret=0 id=1 name=oven_current_temp type=uint16_t',
        ]),
    ])
    reg = m.list_variables()
    assert len(reg.variables) == 2
    assert reg.variables[0].name == 'g_system_tick'
    assert reg.variables[1].c_type == 'uint16_t'


def test_get_by_name():
    m, _ = _make_monitor([
        ('GET 1', ['ACK ret=0 id=1 name=oven_current_temp value=25']),
    ])
    _set_registry(m)
    assert m.get('oven_current_temp') == 25


def test_get_by_id():
    m, _ = _make_monitor([
        ('GET 0', ['ACK ret=0 id=0 name=g_system_tick value=1000']),
    ])
    _set_registry(m)
    assert m.get(0) == 1000


def test_get_many():
    m, _ = _make_monitor([
        ('GET 0,1 compact', ['ACK ret=0 0=1000 1=25']),
    ])
    _set_registry(m)
    result = m.get_many(['g_system_tick', 'oven_current_temp'])
    assert result[0] == 1000
    assert result[1] == 25


def test_polling_below_100ms_raises():
    m, _ = _make_monitor([])
    _set_registry(m)
    with pytest.raises(ValueError, match='100'):
        m.start_polling(['g_system_tick'], period_ms=50)


def test_start_stop_polling():
    m, _ = _make_monitor([
        ('GET 0 compact', ['ACK ret=0 0=100']),
    ])
    _set_registry(m)
    samples = []
    m.start_polling(
        ['g_system_tick'], period_ms=100,
        on_sample=lambda n, v, t: samples.append((n, v)))
    time.sleep(0.35)
    m.stop_polling()
    assert len(samples) >= 2
    assert all(v == 100 for _, v in samples)


def test_create_logger_writes_file(tmp_path):
    m, _ = _make_monitor([
        ('PING', ['ACK ret=0 fw=3.6.0 crc=0 vars=1']),
    ])
    _set_registry(m)
    log_path = tmp_path / 'session.psblog'
    logger = m.create_logger(log_path)
    logger.start()
    logger.write('oven_current_temp', 42, 0.1)
    logger.write('oven_current_temp', 43, 0.2)
    logger.stop()
    text = log_path.read_text(encoding='utf-8')
    assert '@schema       psblog/v1' in text
    assert '@var oven_current_temp uint16_t degC Hardware' in text
    assert '@100 oven_current_temp=42' in text
    assert '@200 oven_current_temp=43' in text
    assert '@samples  2' in text

