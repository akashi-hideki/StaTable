"""v3.6.0 comm_monitor response/XML tests (spec §9.5)."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_CODE_DIR = _TESTS_DIR.parent
for _p in (str(_CODE_DIR), str(_TESTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from statable_monitor import frame_to_xml, data_line_to_xml


def _parse(xml):
    return ET.fromstring(xml)


# ----------------------------------------------------------------------
# frame_to_xml basics
# ----------------------------------------------------------------------

def test_ack_standard():
    xml = frame_to_xml(
        'ACK ret=0 id=1 name=oven_current_temp value=25', 100)
    root = _parse(xml)
    assert root.tag == 'sample'
    assert root.attrib['t'] == '100'
    assert root.attrib['kind'] == 'ACK'
    assert root.attrib['status'] == 'ret=0'
    var = root.find('var')
    assert var is not None
    assert var.attrib['id'] == '1'
    assert var.attrib['name'] == 'oven_current_temp'
    assert var.attrib['value'] == '25'


def test_ping_response():
    xml = frame_to_xml(
        'ACK ret=0 fw=3.6.0 crc=8A3F21C7 vars=30', 0)
    root = _parse(xml)
    assert root.attrib['kind'] == 'ACK'
    var = root.find('var')
    assert var.attrib['fw'] == '3.6.0'
    assert var.attrib['crc'] == '8A3F21C7'
    assert var.attrib['vars'] == '30'


def test_nak_response():
    xml = frame_to_xml('NAK ret=2 id=99 reason=idx', 200)
    root = _parse(xml)
    assert root.attrib['kind'] == 'NAK'
    var = root.find('var')
    assert var.attrib['id'] == '99'
    assert var.attrib['reason'] == 'idx'


def test_compact_multi_ids():
    xml = frame_to_xml('ACK ret=0 3=25 7=100 15=31', 0)
    root = _parse(xml)
    vars_ = root.findall('var')
    assert len(vars_) == 3
    assert vars_[0].attrib == {'id': '3', 'value': '25'}
    assert vars_[1].attrib == {'id': '7', 'value': '100'}
    assert vars_[2].attrib == {'id': '15', 'value': '31'}


def test_compact_single_id():
    xml = frame_to_xml('ACK ret=0 3=25', 0)
    root = _parse(xml)
    var = root.find('var')
    assert var.attrib['id'] == '3'
    assert var.attrib['value'] == '25'


def test_empty_input():
    xml = frame_to_xml('', 0)
    root = _parse(xml)
    assert root.tag == 'sample'
    assert root.attrib['kind'] == 'EMPTY'


def test_single_token():
    xml = frame_to_xml('ACK', 0)
    root = _parse(xml)
    assert root.attrib['kind'] == 'ACK'
    assert root.find('var') is None


# ----------------------------------------------------------------------
# XML escaping
# ----------------------------------------------------------------------

def test_escape_lt_gt():
    xml = frame_to_xml('ACK ret=0 name=<value>', 0)
    root = _parse(xml)
    var = root.find('var')
    assert var.attrib['name'] == '<value>'


def test_escape_amp():
    xml = frame_to_xml('ACK ret=0 name=a&b', 0)
    root = _parse(xml)
    var = root.find('var')
    assert var.attrib['name'] == 'a&b'


def test_escape_quotes():
    xml = frame_to_xml(
        'ACK ret=0 name="double" title=\'single\'', 0)
    root = _parse(xml)
    var = root.find('var')
    assert var.attrib['name'] == '"double"'
    assert var.attrib['title'] == "'single'"


# ----------------------------------------------------------------------
# data_line_to_xml
# ----------------------------------------------------------------------

def test_data_line_basic():
    xml = data_line_to_xml('@200 oven_temp=25 heater=100')
    root = _parse(xml)
    assert root.attrib['t'] == '200'
    assert root.attrib['kind'] == 'DATA'
    var = root.find('var')
    assert var.attrib['oven_temp'] == '25'
    assert var.attrib['heater'] == '100'


def test_data_line_invalid():
    assert data_line_to_xml('not a data line') == ''
    assert data_line_to_xml('@') == ''
    assert data_line_to_xml('@abc k=v') == ''
