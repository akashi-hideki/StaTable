"""v3.6.0 XML persistence: comm_monitor_enabled attribute."""
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_CODE_DIR = _TESTS_DIR.parent
for _p in (str(_CODE_DIR), str(_TESTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from statable.xml_io import (
    project_from_xml,
    _project_settings_to_element, _project_settings_from_element,
)


def test_write_enabled_has_attribute():
    elem = _project_settings_to_element({'comm_monitor_enabled': True})
    cg = elem.find('CodeGeneration')
    assert cg is not None
    assert cg.get('comm_monitor_enabled') == 'true'


def test_write_disabled_no_attribute():
    elem = _project_settings_to_element({'comm_monitor_enabled': False})
    cg = elem.find('CodeGeneration')
    assert cg is not None
    assert cg.get('comm_monitor_enabled') is None


def test_read_present_true():
    from xml.etree import ElementTree as ET
    root = ET.Element('ProjectSettings')
    ET.SubElement(root, 'CodeGeneration', comm_monitor_enabled='true')
    s = _project_settings_from_element(root)
    assert s['comm_monitor_enabled'] is True


def test_read_absent_false():
    from xml.etree import ElementTree as ET
    root = ET.Element('ProjectSettings')
    ET.SubElement(root, 'CodeGeneration')
    s = _project_settings_from_element(root)
    assert s['comm_monitor_enabled'] is False


def test_round_trip_via_xml_file(tmp_path):
    xml = tmp_path / 'p.xml'
    xml.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<Project name="T"><ProjectSettings>'
        '<CodeGeneration comm_monitor_enabled="true"/>'
        '</ProjectSettings></Project>\n',
        encoding='utf-8')
    tabs, gd, *_rest, settings = project_from_xml(str(xml))
    assert settings['comm_monitor_enabled'] is True


def test_legacy_xml_reads_false(tmp_path):
    xml = tmp_path / 'legacy.xml'
    xml.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<Project name="T"><ProjectSettings>'
        '<CodeGeneration project_name="T"/>'
        '</ProjectSettings></Project>\n',
        encoding='utf-8')
    tabs, gd, *_rest, settings = project_from_xml(str(xml))
    assert settings['comm_monitor_enabled'] is False
