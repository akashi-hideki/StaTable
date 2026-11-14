"""v3.6.0 psblog/v1 roundtrip tests (reference parser)."""
import sys as _sys
from pathlib import Path as _Path
_TESTS_DIR = _Path(__file__).resolve().parent
_CODE_DIR = _TESTS_DIR.parent
for _p in (str(_CODE_DIR), str(_TESTS_DIR)):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from statable_monitor import PStaBlogLogger

from psblog_reader import parse


VARS = [
    {'name': 'oven_current_temp', 'type': 'uint16_t',
     'unit': 'degC', 'group': 'Hardware',
     'description': 'Current oven temperature'},
    {'name': 'oven_target_temp', 'type': 'uint16_t',
     'unit': 'degC', 'group': 'Hardware',
     'description': 'Target oven temperature'},
    {'name': 'heater_top_duty', 'type': 'uint8_t',
     'unit': '%', 'group': 'Hardware',
     'description': 'Top heater PWM duty'},
]


def _make_logger(tmp_path):
    return PStaBlogLogger(
        path=tmp_path / 'session.psblog',
        source='COM_TEST',
        firmware='PStaTable v3.6.0',
        period_ms=200,
        variables=VARS,
    )


def test_header_keys(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start()
    logger.stop()
    doc = parse(tmp_path / 'session.psblog')
    assert doc.header['@schema'] == 'psblog/v1'
    assert doc.header['@source'] == 'uart:COM_TEST'
    assert doc.header['@firmware'] == 'PStaTable v3.6.0'
    assert doc.header['@protocol'] == 'pstable-uart/v1'
    assert doc.header['@period_ms'] == '200'
    assert '@captured_at' in doc.header


def test_vartable(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start()
    logger.stop()
    doc = parse(tmp_path / 'session.psblog')
    assert len(doc.vars) == 3
    v0 = doc.vars[0]
    assert v0.name == 'oven_current_temp'
    assert v0.type == 'uint16_t'
    assert v0.unit == 'degC'
    assert v0.group == 'Hardware'
    assert v0.description == 'Current oven temperature'


def test_data_lines(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start()
    logger.write('oven_current_temp', 25, 0.1)
    logger.write('oven_current_temp', 26, 0.2)
    logger.write('heater_top_duty', 50, 0.3)
    logger.stop()
    doc = parse(tmp_path / 'session.psblog')
    assert len(doc.samples) == 3
    assert doc.samples[0] == (100, {'oven_current_temp': '25'})
    assert doc.samples[1] == (200, {'oven_current_temp': '26'})
    assert doc.samples[2] == (300, {'heater_top_duty': '50'})


def test_footer(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start()
    logger.write('oven_current_temp', 25, 0.1)
    logger.stop()
    doc = parse(tmp_path / 'session.psblog')
    assert '@end' in doc.footer
    assert doc.footer['@samples'] == '1'
    assert doc.footer['@dropped'] == '0'


def test_roundtrip_values(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start()
    for name, val, ts in [
        ('oven_current_temp', 25, 0.0),
        ('oven_current_temp', 26, 0.1),
        ('oven_target_temp', 200, 0.2),
        ('heater_top_duty', 100, 0.3),
    ]:
        logger.write(name, val, ts)
    logger.stop()
    doc = parse(tmp_path / 'session.psblog')
    recovered = {
        (t_ms, name): int(val)
        for t_ms, sample in doc.samples
        for name, val in sample.items()
    }
    assert recovered[(0, 'oven_current_temp')] == 25
    assert recovered[(100, 'oven_current_temp')] == 26
    assert recovered[(200, 'oven_target_temp')] == 200
    assert recovered[(300, 'heater_top_duty')] == 100


def test_byte_level(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start()
    logger.write('oven_current_temp', 42, 0.1)
    logger.stop()
    raw = (tmp_path / 'session.psblog').read_bytes()
    assert not raw.startswith(b'\xef\xbb\xbf')
    assert b'\r' not in raw
    assert raw.startswith(b'#')

