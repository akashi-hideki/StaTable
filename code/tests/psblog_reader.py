"""psblog/v1 reference parser (test helper)."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class VarDef:
    name: str
    type: str
    unit: str
    group: str
    description: str = ''


@dataclass
class PsblogDoc:
    header: Dict[str, str] = field(default_factory=dict)
    vars: List[VarDef] = field(default_factory=list)
    samples: List[Tuple[int, Dict[str, str]]] = field(default_factory=list)
    footer: Dict[str, str] = field(default_factory=dict)


HEADER_KEYS = {
    '@schema', '@captured_at', '@source',
    '@firmware', '@protocol', '@baud', '@period_ms',
}
FOOTER_KEYS = {'@end', '@samples', '@dropped'}


def parse(path):
    path = Path(path)
    doc = PsblogDoc()
    with path.open('r', encoding='utf-8') as f:
        for raw_line in f:
            line = raw_line.rstrip('\n')
            if not line or line.startswith('#'):
                continue
            if line.startswith('@var '):
                _parse_var(line, doc)
            elif _is_data_line(line):
                _parse_data(line, doc)
            elif line.startswith('@'):
                _parse_meta(line, doc)
    return doc


def _parse_var(line, doc):
    parts = line.split(maxsplit=5)
    if len(parts) < 5:
        return
    name, type_, unit, group = parts[1], parts[2], parts[3], parts[4]
    desc = parts[5] if len(parts) > 5 else ''
    if desc.startswith('"') and desc.endswith('"'):
        desc = desc[1:-1]
    doc.vars.append(VarDef(name, type_, unit, group, desc))


def _is_data_line(line):
    if not line.startswith('@'):
        return False
    rest = line[1:]
    if not rest:
        return False
    first = rest.split(' ', 1)[0]
    return first.isdigit()


def _parse_data(line, doc):
    parts = line.split()
    t_ms = int(parts[0][1:])
    sample = {}
    for token in parts[1:]:
        if '=' in token:
            k, v = token.split('=', 1)
            sample[k] = v
    doc.samples.append((t_ms, sample))


def _parse_meta(line, doc):
    parts = line.split(maxsplit=1)
    key = parts[0]
    val = parts[1] if len(parts) > 1 else ''
    if key in HEADER_KEYS:
        doc.header[key] = val
    elif key in FOOTER_KEYS:
        doc.footer[key] = val

