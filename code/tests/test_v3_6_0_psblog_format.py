"""v3.6.0 psblog/v1 byte-level format tests (spec §10)."""
import re as _re
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
    {'name': 'heater_top_duty', 'type': 'uint8_t',
     'unit': '%', 'group': 'Hardware',
     'description': 'Top heater PWM duty'},
]


def _make_logger(tmp_path, **overrides):
    kwargs = dict(
        path=tmp_path / 'session.psblog',
        source='COM3',
        firmware='StaTable v3.6.0',
        period_ms=200,
        variables=VARS,
    )
    kwargs.update(overrides)
    return PStaBlogLogger(**kwargs)


def test_no_bom(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start(); logger.stop()
    data = (tmp_path / 'session.psblog').read_bytes()
    assert data[:3] != b'\xef\xbb\xbf'


def test_lf_only(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start(); logger.stop()
    data = (tmp_path / 'session.psblog').read_bytes()
    assert b'\r\n' not in data
    assert b'\n' in data


def test_utf8_decodable(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start(); logger.stop()
    data = (tmp_path / 'session.psblog').read_bytes()
    data.decode('utf-8')


def test_trailing_newline(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start(); logger.stop()
    data = (tmp_path / 'session.psblog').read_bytes()
    assert data.endswith(b'\n')


def test_section_order(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start()
    logger.write('oven_current_temp', 25, host_ts=0)
    logger.stop()
    text = (tmp_path / 'session.psblog').read_text(encoding='utf-8')
    assert text.index('@schema') < text.index('@var ')
    assert text.index('@var ') < text.index('@0 oven_current_temp=25')
    assert text.index('@0 oven_current_temp=25') < text.index('@end')


def test_header_schema_literal(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start(); logger.stop()
    text = (tmp_path / 'session.psblog').read_text(encoding='utf-8')
    assert '@schema       psblog/v1\n' in text


def test_header_protocol_literal(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start(); logger.stop()
    text = (tmp_path / 'session.psblog').read_text(encoding='utf-8')
    assert '@protocol     pstable-uart/v1\n' in text


def test_header_source_uart_prefix(tmp_path):
    logger = _make_logger(tmp_path, source='COM7')
    logger.start(); logger.stop()
    doc = parse(tmp_path / 'session.psblog')
    assert doc.header['@source'] == 'uart:COM7'


def test_header_captured_at_iso8601(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start(); logger.stop()
    doc = parse(tmp_path / 'session.psblog')
    ts = doc.header['@captured_at']
    pat = _re.compile(
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2}$')
    assert pat.match(ts), f'captured_at not ISO 8601: {ts!r}'


def test_header_firmware_string(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start(); logger.stop()
    doc = parse(tmp_path / 'session.psblog')
    assert doc.header['@firmware'] == 'StaTable v3.6.0'
    assert not doc.header['@firmware'].startswith('PStaTable')


def test_header_comment_line(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start(); logger.stop()
    first = (tmp_path / 'session.psblog').read_text(
        encoding='utf-8').split('\n')[0]
    assert 'PStaTable' not in first
    assert 'StaTable' in first


def test_vartable_line_regex(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start(); logger.stop()
    text = (tmp_path / 'session.psblog').read_text(encoding='utf-8')
    var_lines = [l for l in text.split('\n') if l.startswith('@var ')]
    assert len(var_lines) == len(VARS)
    pat = _re.compile(r'^@var\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(".*")$')
    for line in var_lines:
        assert pat.match(line), f'@var format wrong: {line!r}'


def test_data_line_regex(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start()
    logger.write('oven_current_temp', 25, host_ts=0)
    logger.write('heater_top_duty', 100, host_ts=0.2)
    logger.stop()
    text = (tmp_path / 'session.psblog').read_text(encoding='utf-8')
    data_lines = [
        l for l in text.split('\n')
        if _re.match(r'^@\d+\s+\S+=', l)]
    assert len(data_lines) == 2
    pat = _re.compile(r'^@\d+\s+\S+=\S+(\s+\S+=\S+)*$')
    for line in data_lines:
        assert pat.match(line), f'data line wrong: {line!r}'


def test_data_t_ms_is_integer_millis(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start()
    logger.write('oven_current_temp', 25, host_ts=0.123)
    logger.stop()
    text = (tmp_path / 'session.psblog').read_text(encoding='utf-8')
    m = _re.search(r'^@(\d+)\s+oven_current_temp=25$', text, _re.MULTILINE)
    assert m, 'data line not found'
    assert int(m.group(1)) == 123


def test_footer_samples_dropped(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start()
    for i in range(3):
        logger.write('oven_current_temp', i, host_ts=i)
    logger.stop()
    doc = parse(tmp_path / 'session.psblog')
    assert doc.footer['@samples'] == '3'
    assert doc.footer['@dropped'] == '0'


def test_empty_log_has_no_data_lines(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start(); logger.stop()
    text = (tmp_path / 'session.psblog').read_text(encoding='utf-8')
    data_lines = [l for l in text.split('\n') if _re.match(r'^@\d+\s', l)]
    assert data_lines == []


def test_roundtrip_via_reference_parser(tmp_path):
    logger = _make_logger(tmp_path)
    logger.start()
    logger.write('oven_current_temp', 25, host_ts=0)
    logger.write('heater_top_duty', 100, host_ts=0.2)
    logger.stop()
    doc = parse(tmp_path / 'session.psblog')
    assert len(doc.samples) == 2
    t0, vals0 = doc.samples[0]
    assert t0 == 0
    assert vals0['oven_current_temp'] == '25'
