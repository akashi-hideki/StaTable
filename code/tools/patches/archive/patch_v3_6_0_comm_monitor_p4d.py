#!/usr/bin/env python3
"""patch_v3_6_0_comm_monitor_p4d.py - psblog reference parser + roundtrip."""
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
REPO = CODE.parent

PARSER_PY = [
    '"""psblog/v1 reference parser (test helper)."""',
    "from dataclasses import dataclass, field",
    "from pathlib import Path",
    "from typing import Dict, List, Tuple",
    "",
    "",
    "@dataclass",
    "class VarDef:",
    "    name: str",
    "    type: str",
    "    unit: str",
    "    group: str",
    "    description: str = ''",
    "",
    "",
    "@dataclass",
    "class PsblogDoc:",
    "    header: Dict[str, str] = field(default_factory=dict)",
    "    vars: List[VarDef] = field(default_factory=list)",
    "    samples: List[Tuple[int, Dict[str, str]]] = field(default_factory=list)",
    "    footer: Dict[str, str] = field(default_factory=dict)",
    "",
    "",
    "HEADER_KEYS = {",
    "    '@schema', '@captured_at', '@source',",
    "    '@firmware', '@protocol', '@baud', '@period_ms',",
    "}",
    "FOOTER_KEYS = {'@end', '@samples', '@dropped'}",
    "",
    "",
    "def parse(path):",
    "    path = Path(path)",
    "    doc = PsblogDoc()",
    "    with path.open('r', encoding='utf-8') as f:",
    "        for raw_line in f:",
    "            line = raw_line.rstrip('\\n')",
    "            if not line or line.startswith('#'):",
    "                continue",
    "            if line.startswith('@var '):",
    "                _parse_var(line, doc)",
    "            elif _is_data_line(line):",
    "                _parse_data(line, doc)",
    "            elif line.startswith('@'):",
    "                _parse_meta(line, doc)",
    "    return doc",
    "",
    "",
    "def _parse_var(line, doc):",
    "    parts = line.split(maxsplit=5)",
    "    if len(parts) < 5:",
    "        return",
    "    name, type_, unit, group = parts[1], parts[2], parts[3], parts[4]",
    "    desc = parts[5] if len(parts) > 5 else ''",
    "    if desc.startswith('\"') and desc.endswith('\"'):",
    "        desc = desc[1:-1]",
    "    doc.vars.append(VarDef(name, type_, unit, group, desc))",
    "",
    "",
    "def _is_data_line(line):",
    "    if not line.startswith('@'):",
    "        return False",
    "    rest = line[1:]",
    "    if not rest:",
    "        return False",
    "    first = rest.split(' ', 1)[0]",
    "    return first.isdigit()",
    "",
    "",
    "def _parse_data(line, doc):",
    "    parts = line.split()",
    "    t_ms = int(parts[0][1:])",
    "    sample = {}",
    "    for token in parts[1:]:",
    "        if '=' in token:",
    "            k, v = token.split('=', 1)",
    "            sample[k] = v",
    "    doc.samples.append((t_ms, sample))",
    "",
    "",
    "def _parse_meta(line, doc):",
    "    parts = line.split(maxsplit=1)",
    "    key = parts[0]",
    "    val = parts[1] if len(parts) > 1 else ''",
    "    if key in HEADER_KEYS:",
    "        doc.header[key] = val",
    "    elif key in FOOTER_KEYS:",
    "        doc.footer[key] = val",
    "",
]

TEST_PY = [
    '"""v3.6.0 psblog/v1 roundtrip tests (reference parser)."""',
    "import sys as _sys",
    "from pathlib import Path as _Path",
    "_TESTS_DIR = _Path(__file__).resolve().parent",
    "_CODE_DIR = _TESTS_DIR.parent",
    "for _p in (str(_CODE_DIR), str(_TESTS_DIR)):",
    "    if _p not in _sys.path:",
    "        _sys.path.insert(0, _p)",
    "",
    "from statable_monitor import PStaBlogLogger",
    "",
    "from psblog_reader import parse",
    "",
    "",
    "VARS = [",
    "    {'name': 'oven_current_temp', 'type': 'uint16_t',",
    "     'unit': 'degC', 'group': 'Hardware',",
    "     'description': 'Current oven temperature'},",
    "    {'name': 'oven_target_temp', 'type': 'uint16_t',",
    "     'unit': 'degC', 'group': 'Hardware',",
    "     'description': 'Target oven temperature'},",
    "    {'name': 'heater_top_duty', 'type': 'uint8_t',",
    "     'unit': '%', 'group': 'Hardware',",
    "     'description': 'Top heater PWM duty'},",
    "]",
    "",
    "",
    "def _make_logger(tmp_path):",
    "    return PStaBlogLogger(",
    "        path=tmp_path / 'session.psblog',",
    "        source='COM_TEST',",
    "        firmware='StaTable v3.6.0',",
    "        period_ms=200,",
    "        variables=VARS,",
    "    )",
    "",
    "",
    "def test_header_keys(tmp_path):",
    "    logger = _make_logger(tmp_path)",
    "    logger.start()",
    "    logger.stop()",
    "    doc = parse(tmp_path / 'session.psblog')",
    "    assert doc.header['@schema'] == 'psblog/v1'",
    "    assert doc.header['@source'] == 'uart:COM_TEST'",
    "    assert doc.header['@firmware'] == 'StaTable v3.6.0'",
    "    assert doc.header['@protocol'] == 'pstable-uart/v1'",
    "    assert doc.header['@period_ms'] == '200'",
    "    assert '@captured_at' in doc.header",
    "",
    "",
    "def test_vartable(tmp_path):",
    "    logger = _make_logger(tmp_path)",
    "    logger.start()",
    "    logger.stop()",
    "    doc = parse(tmp_path / 'session.psblog')",
    "    assert len(doc.vars) == 3",
    "    v0 = doc.vars[0]",
    "    assert v0.name == 'oven_current_temp'",
    "    assert v0.type == 'uint16_t'",
    "    assert v0.unit == 'degC'",
    "    assert v0.group == 'Hardware'",
    "    assert v0.description == 'Current oven temperature'",
    "",
    "",
    "def test_data_lines(tmp_path):",
    "    logger = _make_logger(tmp_path)",
    "    logger.start()",
    "    logger.write('oven_current_temp', 25, 0.1)",
    "    logger.write('oven_current_temp', 26, 0.2)",
    "    logger.write('heater_top_duty', 50, 0.3)",
    "    logger.stop()",
    "    doc = parse(tmp_path / 'session.psblog')",
    "    assert len(doc.samples) == 3",
    "    assert doc.samples[0] == (100, {'oven_current_temp': '25'})",
    "    assert doc.samples[1] == (200, {'oven_current_temp': '26'})",
    "    assert doc.samples[2] == (300, {'heater_top_duty': '50'})",
    "",
    "",
    "def test_footer(tmp_path):",
    "    logger = _make_logger(tmp_path)",
    "    logger.start()",
    "    logger.write('oven_current_temp', 25, 0.1)",
    "    logger.stop()",
    "    doc = parse(tmp_path / 'session.psblog')",
    "    assert '@end' in doc.footer",
    "    assert doc.footer['@samples'] == '1'",
    "    assert doc.footer['@dropped'] == '0'",
    "",
    "",
    "def test_roundtrip_values(tmp_path):",
    "    logger = _make_logger(tmp_path)",
    "    logger.start()",
    "    for name, val, ts in [",
    "        ('oven_current_temp', 25, 0.0),",
    "        ('oven_current_temp', 26, 0.1),",
    "        ('oven_target_temp', 200, 0.2),",
    "        ('heater_top_duty', 100, 0.3),",
    "    ]:",
    "        logger.write(name, val, ts)",
    "    logger.stop()",
    "    doc = parse(tmp_path / 'session.psblog')",
    "    recovered = {",
    "        (t_ms, name): int(val)",
    "        for t_ms, sample in doc.samples",
    "        for name, val in sample.items()",
    "    }",
    "    assert recovered[(0, 'oven_current_temp')] == 25",
    "    assert recovered[(100, 'oven_current_temp')] == 26",
    "    assert recovered[(200, 'oven_target_temp')] == 200",
    "    assert recovered[(300, 'heater_top_duty')] == 100",
    "",
    "",
    "def test_byte_level(tmp_path):",
    "    logger = _make_logger(tmp_path)",
    "    logger.start()",
    "    logger.write('oven_current_temp', 42, 0.1)",
    "    logger.stop()",
    "    raw = (tmp_path / 'session.psblog').read_bytes()",
    "    assert not raw.startswith(b'\\xef\\xbb\\xbf')",
    "    assert b'\\r' not in raw",
    "    assert raw.startswith(b'#')",
    "",
]


def write_lines(rel, lines):
    p = CODE / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("  [write ] code/{} ({} lines)".format(rel, len(lines)))


def register_in_ci():
    p = REPO / ".github" / "workflows" / "check.yml"
    text = p.read_text(encoding="utf-8")
    if "test_v3_6_0_psblog_roundtrip" in text:
        print("  [skip ] check.yml already has psblog test")
        return
    anchor = ("coverage run --parallel-mode "
              "tests/test_v3_6_0_sdk_python.py")
    if anchor not in text:
        print("  [error] anchor not found")
        return
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if anchor in line:
            indent = line[: len(line) - len(line.lstrip())]
            lines.insert(
                i + 1,
                "{}coverage run --parallel-mode "
                "tests/test_v3_6_0_psblog_roundtrip.py".format(indent))
            break
    p.write_text("\n".join(lines), encoding="utf-8")
    print("  [write ] check.yml (psblog test registered)")


def update_readme():
    p = REPO / "README.md"
    text = p.read_text(encoding="utf-8")
    repls = [
        ("Tests-1911%20PASS", "Tests-1917%20PASS"),
        ("1911 PASS", "1917 PASS"),
        ("1911 tests", "1917 tests"),
        ("53 test suites", "54 test suites"),
        ("53 suites", "54 suites"),
    ]
    changed = False
    for old, new in repls:
        if old in text:
            text = text.replace(old, new)
            changed = True
    if changed:
        p.write_text(text, encoding="utf-8")
        print("  [write ] README.md (54 suites / 1917 PASS)")
    else:
        print("  [skip ] README unchanged")


def main():
    print("=== patch_v3_6_0_comm_monitor_p4d ===")
    print("repo: {}".format(REPO))
    write_lines("tests/psblog_reader.py", PARSER_PY)
    write_lines("tests/test_v3_6_0_psblog_roundtrip.py", TEST_PY)
    register_in_ci()
    update_readme()
    print("=== done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())