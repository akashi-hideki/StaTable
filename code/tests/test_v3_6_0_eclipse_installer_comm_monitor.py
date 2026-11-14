"""v3.6.0 Eclipse Installer: XML generation with Tri-state comm_monitor."""
import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent
_CODE_DIR = _TESTS_DIR.parent
for _p in (str(_CODE_DIR), str(_TESTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from eclipse_installer.core import (
    InstallOptions, install, generate_from_xml, _resolve_comm_monitor,
)


SAMPLE_XML = _CODE_DIR / "tests" / "data" / "v22_features_test3.xml"
COMM_FILES = [
    "statable_comm_config.h",
    "statable_comm_monitor.c",
    "statable_comm_monitor.h",
    "statable_comm_registry.c",
    "statable_comm_registry.h",
    "statable_comm_ring.c",
    "statable_comm_ring.h",
]


def _comm_count(d):
    return sum(1 for n in COMM_FILES if (Path(d) / n).exists())


@pytest.mark.parametrize("xml_settings,override,expected", [
    ({"comm_monitor_enabled": True},  None,  True),
    ({"comm_monitor_enabled": False}, None,  False),
    ({},                              None,  False),
    ({"comm_monitor_enabled": False}, True,  True),
    ({"comm_monitor_enabled": True},  False, False),
])
def test_resolve_comm_monitor(xml_settings, override, expected):
    assert _resolve_comm_monitor(xml_settings, override) is expected


def test_generate_auto_xml_off(tmp_path):
    enabled = generate_from_xml(SAMPLE_XML, tmp_path, with_comm_monitor=None)
    assert enabled is False
    assert _comm_count(tmp_path) == 0


def test_generate_force_on(tmp_path):
    enabled = generate_from_xml(SAMPLE_XML, tmp_path, with_comm_monitor=True)
    assert enabled is True
    assert _comm_count(tmp_path) == 7


def test_generate_force_off(tmp_path):
    enabled = generate_from_xml(SAMPLE_XML, tmp_path, with_comm_monitor=False)
    assert enabled is False
    assert _comm_count(tmp_path) == 0


def test_generate_auto_xml_on(tmp_path):
    """Full XML (with GlobalDefinitions) + comm_monitor_enabled="true".

    The resolver should return True and the generator should emit all
    7 comm_monitor files, without any CLI override.
    """
    import re

    src = SAMPLE_XML.read_text(encoding="utf-8")
    # Inject comm_monitor_enabled="true" into the existing <CodeGeneration ... />
    modified, n = re.subn(
        r"(<CodeGeneration\b[^/]*?)(\s*/>)",
        r'\1 comm_monitor_enabled="true"\2',
        src,
        count=1,
    )
    assert n == 1, "failed to inject comm_monitor_enabled into sample XML"

    xml = tmp_path / "on.xml"
    xml.write_text(modified, encoding="utf-8")
    out = tmp_path / "out"
    enabled = generate_from_xml(xml, out, with_comm_monitor=None)
    assert enabled is True
    assert _comm_count(out) == 7


def test_install_xml_force_on_copies_comm(tmp_path):
    proj = tmp_path / "proj"; proj.mkdir()
    out = tmp_path / "gen"
    opts = InstallOptions(
        project_root=proj, output_dir=out,
        xml_path=SAMPLE_XML, with_comm_monitor=True,
    )
    res = install(opts)
    assert not res.errors, res.errors
    dst = proj / opts.generated_subdir
    assert _comm_count(dst) == 7


def test_install_no_xml_with_flag_warns(tmp_path):
    proj = tmp_path / "proj"; proj.mkdir()
    out = tmp_path / "out"; out.mkdir()
    (out / "dummy.c").write_text("/* */", encoding="utf-8")
    res = install(InstallOptions(
        project_root=proj, output_dir=out, with_comm_monitor=True))
    assert not res.errors
    assert any("xml_path" in w for w in res.warnings)
